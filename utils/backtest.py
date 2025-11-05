import pandas as pd
import numpy as np
import locale
import math

# Localización para meses en español (usado en los reportes)
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_TIME, '')


def simulate_signals(df, initial_capital=100000, stop_loss_pct=0.05, take_profit_pct=0.15):
    """
    Versión original (simple) - Cruces SMA/EMA + RSI + MACD + Bollinger.
    """
    if df is None or df.empty:
        return "No hay datos suficientes para la simulación."

    df = df.copy()
    price_col = 'Close'
    rsi_col = next((c for c in df.columns if c.upper().startswith("RSI_")), None)
    sma_col = next((c for c in df.columns if c.upper().startswith("SMA_")), None)
    ema_col = next((c for c in df.columns if c.upper().startswith("EMA_")), None)

    if not (sma_col and ema_col and rsi_col and 'MACD' in df.columns and 'MACD_signal' in df.columns):
        return "No hay suficientes indicadores para la simulación."

    df['Signal'] = 0
    df['Equity'] = np.nan

    positions = []
    closed_trades = []
    equity = initial_capital
    equity_series = []

    for i in range(1, len(df)):
        prev_sma, prev_ema = df[sma_col].iloc[i - 1], df[ema_col].iloc[i - 1]
        sma, ema = df[sma_col].iloc[i], df[ema_col].iloc[i]
        close = df[price_col].iloc[i]
        rsi = df[rsi_col].iloc[i]
        macd = df['MACD'].iloc[i]
        macd_sig = df['MACD_signal'].iloc[i]

        # --- Compra ---
        if (prev_sma < prev_ema) and (sma >= ema):
            if (rsi < 70) and (macd > macd_sig):
                df.at[df.index[i], 'Signal'] = 1
                allocation = equity * 0.25
                if allocation > 0:
                    qty = allocation / close
                    positions.append({
                        'entry_date': df.index[i],
                        'entry_price': close,
                        'qty': qty,
                        'allocation': allocation,
                        'peak_price': close
                    })
                    equity -= allocation

        # --- Venta por cruce bajista ---
        elif (prev_sma > prev_ema) and (sma <= ema):
            if (rsi > 30) or (macd < macd_sig):
                df.at[df.index[i], 'Signal'] = -1
                for pos in positions:
                    exit_price = close
                    ret_pct = (exit_price - pos['entry_price']) / pos['entry_price'] * 100
                    pnl = pos['qty'] * exit_price
                    closed_trades.append({
                        'entry': pos['entry_date'],
                        'exit': df.index[i],
                        'entry_price': pos['entry_price'],
                        'exit_price': exit_price,
                        'return_%': ret_pct
                    })
                    equity += pnl
                positions = []

        # --- SL / TP individuales ---
        still_open = []
        for pos in positions:
            current_price = close
            pos['peak_price'] = max(pos['peak_price'], current_price)

            if current_price <= pos['entry_price'] * (1 - stop_loss_pct) or \
               current_price >= pos['entry_price'] * (1 + take_profit_pct):
                exit_price = current_price
                ret_pct = (exit_price - pos['entry_price']) / pos['entry_price'] * 100
                pnl = pos['qty'] * exit_price
                closed_trades.append({
                    'entry': pos['entry_date'],
                    'exit': df.index[i],
                    'entry_price': pos['entry_price'],
                    'exit_price': exit_price,
                    'return_%': ret_pct
                })
                equity += pnl
            else:
                still_open.append(pos)
        positions = still_open

        open_value = sum([p['qty'] * close for p in positions])
        total_equity = equity + open_value
        df.at[df.index[i], 'Equity'] = total_equity
        equity_series.append(total_equity)

    if positions:
        last_price = df[price_col].iloc[-1]
        for pos in positions:
            exit_price = last_price
            ret_pct = (exit_price - pos['entry_price']) / pos['entry_price'] * 100
            pnl = pos['qty'] * exit_price
            closed_trades.append({
                'entry': pos['entry_date'],
                'exit': df.index[-1],
                'entry_price': pos['entry_price'],
                'exit_price': exit_price,
                'return_%': ret_pct
            })
            equity += pnl
        positions = []

    final_equity = equity_series[-1] if equity_series else initial_capital
    total_return_pct = (final_equity - initial_capital) / initial_capital * 100
    equity_s = pd.Series(equity_series, index=df.index[1:len(equity_series)+1])
    running_max = equity_s.cummax()
    drawdowns_equity = (running_max - equity_s) / running_max * 100
    max_drawdown_global = drawdowns_equity.max() if not drawdowns_equity.empty else 0.0

    num_trades = len(closed_trades)
    winners = sum(1 for t in closed_trades if t['return_%'] > 0)

    report_lines = []
    report_lines.append("=== Simulación Original (SMA/EMA) ===")
    report_lines.append(f"Número de operaciones cerradas: {num_trades}")
    report_lines.append(f"Operaciones ganadoras: {winners}")
    report_lines.append(f"Retorno total: {total_return_pct:.2f}%")
    report_lines.append(f"Máx. drawdown global: {max_drawdown_global:.2f}%")
    report_lines.append("")
    if closed_trades:
        report_lines.append("Detalle de operaciones:")
        for i, t in enumerate(closed_trades, 1):
            entry_str = t['entry'].strftime('%B-%Y')
            exit_str = t['exit'].strftime('%B-%Y')
            report_lines.append(f"  {i}. {entry_str} → {exit_str}: {t['return_%']:.2f}%")

    return "\n".join(report_lines)


def simulate_signals_v2(df, initial_capital=100000, stop_loss_pct=0.05, take_profit_pct=0.15):
    """
    Estrategia combinada SMA + EMA + MACD + RSI + Bollinger.
    Versión corregida: condiciones más realistas y señales desfasadas.
    """
    if df is None or df.empty:
        return "No hay datos suficientes para la simulación."

    df = df.copy()
    price_col = 'Close'
    sma_col = next((c for c in df.columns if c.upper().startswith("SMA_")), None)
    ema_col = next((c for c in df.columns if c.upper().startswith("EMA_")), None)
    rsi_col = next((c for c in df.columns if c.upper().startswith("RSI_")), None)

    if not (sma_col and ema_col and rsi_col and 'MACD' in df.columns and 'MACD_signal' in df.columns):
        return "No hay suficientes indicadores para la estrategia avanzada."

    df['Signal'] = 0
    df['Equity'] = np.nan

    positions = []
    closed_trades = []
    equity = initial_capital
    equity_series = []

    for i in range(1, len(df)):
        close = df[price_col].iloc[i]
        sma = df[sma_col].iloc[i]
        ema = df[ema_col].iloc[i]
        prev_sma = df[sma_col].iloc[i - 1]
        prev_ema = df[ema_col].iloc[i - 1]
        rsi = df[rsi_col].iloc[i]
        macd = df['MACD'].iloc[i]
        macd_sig = df['MACD_signal'].iloc[i]
        upper_bb = df['Bollinger_Upper'].iloc[i] if 'Bollinger_Upper' in df.columns else np.nan
        lower_bb = df['Bollinger_Lower'].iloc[i] if 'Bollinger_Lower' in df.columns else np.nan

        # --- Señal de Compra ---
        buy_condition = (
            (sma > ema) and                          # tendencia técnica alcista
            (macd > macd_sig) and                    # momentum alcista
            (45 < rsi < 70) and                      # RSI saludable
            (not np.isnan(lower_bb)) and (close > lower_bb)  # no está en la banda baja
        )

        # --- Señal de Venta ---
        sell_condition = (
            (sma < ema) or
            (macd < macd_sig) or
            (rsi > 80) or (rsi < 35)
        )

        # --- Entrada ---
        if buy_condition and equity > 0:
            df.at[df.index[i], 'Signal'] = 1
            allocation = equity * 0.25
            qty = allocation / close
            positions.append({
                'entry_date': df.index[i],
                'entry_price': close,
                'qty': qty,
                'allocation': allocation,
                'peak_price': close
            })
            equity -= allocation

        # --- Salida ---
        elif sell_condition and positions:
            df.at[df.index[i], 'Signal'] = -1
            for pos in positions:
                exit_price = close
                ret_pct = (exit_price - pos['entry_price']) / pos['entry_price'] * 100
                pnl = pos['qty'] * exit_price
                closed_trades.append({
                    'entry': pos['entry_date'],
                    'exit': df.index[i],
                    'entry_price': pos['entry_price'],
                    'exit_price': exit_price,
                    'return_%': ret_pct
                })
                equity += pnl
            positions = []

        # --- Stop loss / Take profit individual ---
        still_open = []
        for pos in positions:
            current_price = close
            pos['peak_price'] = max(pos['peak_price'], current_price)

            if current_price <= pos['entry_price'] * (1 - stop_loss_pct) or \
               current_price >= pos['entry_price'] * (1 + take_profit_pct):
                exit_price = current_price
                ret_pct = (exit_price - pos['entry_price']) / pos['entry_price'] * 100
                pnl = pos['qty'] * exit_price
                closed_trades.append({
                    'entry': pos['entry_date'],
                    'exit': df.index[i],
                    'entry_price': pos['entry_price'],
                    'exit_price': exit_price,
                    'return_%': ret_pct
                })
                equity += pnl
            else:
                still_open.append(pos)
        positions = still_open

        open_value = sum([p['qty'] * close for p in positions])
        total_equity = equity + open_value
        df.at[df.index[i], 'Equity'] = total_equity
        equity_series.append(total_equity)

    # --- Cierre final ---
    if positions:
        last_price = df[price_col].iloc[-1]
        for pos in positions:
            exit_price = last_price
            ret_pct = (exit_price - pos['entry_price']) / pos['entry_price'] * 100
            pnl = pos['qty'] * exit_price
            closed_trades.append({
                'entry': pos['entry_date'],
                'exit': df.index[-1],
                'entry_price': pos['entry_price'],
                'exit_price': exit_price,
                'return_%': ret_pct
            })
            equity += pnl
        positions = []

    # --- Métricas Avanzadas ---
    final_equity = equity_series[-1] if equity_series else initial_capital
    total_return_pct = (final_equity - initial_capital) / initial_capital * 100

    equity_s = pd.Series(equity_series, index=df.index[1:len(equity_series)+1])
    running_max = equity_s.cummax()
    drawdowns_equity = (running_max - equity_s) / running_max * 100
    max_drawdown_global = drawdowns_equity.max() if not drawdowns_equity.empty else 0.0

    years = (df.index[-1] - df.index[0]).days / 365
    cagr = ((final_equity / initial_capital) ** (1 / years) - 1) * 100 if years > 0 else 0

    daily_returns = equity_s.pct_change().dropna()
    sharpe_ratio = 0
    if not daily_returns.empty and daily_returns.std() != 0:
        sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * math.sqrt(252)

    gains = [t['return_%'] for t in closed_trades if t['return_%'] > 0]
    losses = [abs(t['return_%']) for t in closed_trades if t['return_%'] < 0]
    profit_factor = (sum(gains) / sum(losses)) if losses else float('inf')

    num_trades = len(closed_trades)
    winners = sum(1 for t in closed_trades if t['return_%'] > 0)

    report_lines = []
    report_lines.append("=== Simulación Avanzada (SMA+EMA+MACD+RSI+Bollinger) ===")
    report_lines.append(f"Número de operaciones cerradas: {num_trades}")
    report_lines.append(f"Operaciones ganadoras: {winners}")
    report_lines.append(f"Winrate: {(winners/num_trades*100) if num_trades else 0:.2f}%")
    report_lines.append(f"Retorno total: {total_return_pct:.2f}%")
    report_lines.append(f"CAGR: {cagr:.2f}%")
    report_lines.append(f"Sharpe ratio: {sharpe_ratio:.2f}")
    report_lines.append(f"Profit factor: {profit_factor:.2f}")
    report_lines.append(f"Máx. drawdown global: {max_drawdown_global:.2f}%")
    report_lines.append("")
    if closed_trades:
        report_lines.append("Detalle de operaciones:")
        for i, t in enumerate(closed_trades, 1):
            entry_str = t['entry'].strftime('%B-%Y')
            exit_str = t['exit'].strftime('%B-%Y')
            report_lines.append(f"  {i}. {entry_str} → {exit_str}: {t['return_%']:.2f}%")

    return "\n".join(report_lines)
