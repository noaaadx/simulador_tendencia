import pandas as pd
import numpy as np
import locale
import math

# Configuración de localización
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_TIME, '')

class TradingStrategy:
    """Clase base para estrategias de trading."""
    def __init__(self, stop_loss_pct=0.05, take_profit_pct=0.15, initial_capital=100000, indicator_cols=None):
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.initial_capital = initial_capital
        self.closed_trades = []
        self.equity_series = []
        self.indicator_cols = indicator_cols or {
            'sma_col': 'SMA_',
            'ema_col': 'EMA_',
            'rsi_col': 'RSI_',
            'macd_col': 'MACD',
            'macd_signal_col': 'MACD_signal',
            'bollinger_upper_col': 'Bollinger_Upper',
            'bollinger_lower_col': 'Bollinger_Lower'
        }

    def generate_signals(self, df):
        """Genera señales de compra/venta. Debe ser sobrescrito por subclases."""
        raise NotImplementedError("Método generate_signals debe ser implementado.")

    def simulate(self, df):
        """Simula la estrategia y calcula métricas."""
        if df is None or df.empty:
            return "No hay datos suficientes para la simulación."

        df = df.copy()
        price_col = 'Close'
        sma_col = self.indicator_cols['sma_col']
        ema_col = self.indicator_cols['ema_col']
        rsi_col = self.indicator_cols['rsi_col']

        if not (sma_col in df.columns and ema_col in df.columns and rsi_col in df.columns and
                'MACD' in df.columns and 'MACD_signal' in df.columns):
            return "No hay suficientes indicadores para la simulación."

        df['Signal'] = 0
        df['Equity'] = np.nan
        equity = self.initial_capital
        positions = []

        # Generar señales específicas de la estrategia
        self.generate_signals(df)

        for i in range(1, len(df)):
            close = df[price_col].iloc[i]
            signal = df['Signal'].iloc[i]

            # Gestión de posiciones
            if signal == 1 and not positions:
                allocation = equity * 0.25
                if allocation > 0:
                    qty = allocation / close
                    positions.append({
                        'entry_date': df.index[i],
                        'entry_price': close,
                        'qty': qty,
                        'peak_price': close
                    })
                    equity -= allocation

            elif signal == -1 or (positions and self.check_exit(close, positions[0])):
                if positions:
                    exit_price = close
                    ret_pct = (exit_price - positions[0]['entry_price']) / positions[0]['entry_price'] * 100
                    pnl = positions[0]['qty'] * exit_price
                    self.closed_trades.append({
                        'entry': positions[0]['entry_date'],
                        'exit': df.index[i],
                        'return_%': ret_pct
                    })
                    equity += pnl
                    positions = []

            # Stop-loss y Take-profit
            still_open = []
            for pos in positions:
                current_price = close
                pos['peak_price'] = max(pos['peak_price'], current_price)
                if current_price <= pos['entry_price'] * (1 - self.stop_loss_pct) or \
                   current_price >= pos['entry_price'] * (1 + self.take_profit_pct):
                    exit_price = current_price
                    ret_pct = (exit_price - pos['entry_price']) / pos['entry_price'] * 100
                    pnl = pos['qty'] * exit_price
                    self.closed_trades.append({
                        'entry': pos['entry_date'],
                        'exit': df.index[i],
                        'return_%': ret_pct
                    })
                    equity += pnl
                else:
                    still_open.append(pos)
            positions = still_open

            open_value = sum([p['qty'] * close for p in positions])
            total_equity = equity + open_value
            df.at[df.index[i], 'Equity'] = total_equity
            self.equity_series.append(total_equity)

        # Cierre final
        if positions:
            last_price = df[price_col].iloc[-1]
            for pos in positions:
                exit_price = last_price
                ret_pct = (exit_price - pos['entry_price']) / pos['entry_price'] * 100
                pnl = pos['qty'] * exit_price
                self.closed_trades.append({
                    'entry': pos['entry_date'],
                    'exit': df.index[-1],
                    'return_%': ret_pct
                })
                equity += pnl

        return self._generate_report(df)

    def check_exit(self, current_price, position):
        """Verifica condiciones de salida (stop-loss/take-profit)."""
        return current_price <= position['entry_price'] * (1 - self.stop_loss_pct) or \
               current_price >= position['entry_price'] * (1 + self.take_profit_pct)

    def _generate_report(self, df):
        """Genera reporte con métricas."""
        final_equity = self.equity_series[-1] if self.equity_series else self.initial_capital
        total_return_pct = (final_equity - self.initial_capital) / self.initial_capital * 100

        equity_s = pd.Series(self.equity_series, index=df.index[1:len(self.equity_series)+1])
        running_max = equity_s.cummax()
        drawdowns_equity = (running_max - equity_s) / running_max * 100
        max_drawdown_global = drawdowns_equity.max() if not drawdowns_equity.empty else 0.0

        days = (df.index[-1] - df.index[0]).days
        cagr = ((final_equity / self.initial_capital) ** (1 / (days / 365.25)) - 1) * 100 if days > 0 else 0

        daily_returns = equity_s.pct_change().dropna()
        sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * math.sqrt(252) if not daily_returns.empty and daily_returns.std() != 0 else 0

        gains = [t['return_%'] for t in self.closed_trades if t['return_%'] > 0]
        losses = [abs(t['return_%']) for t in self.closed_trades if t['return_%'] < 0]
        profit_factor = (sum(gains) / sum(losses)) if losses else float('inf') if gains else 0

        num_trades = len(self.closed_trades)
        winners = sum(1 for t in self.closed_trades if t['return_%'] > 0)

        report_lines = []
        report_lines.append(f"=== {self.__class__.__name__} ===")
        report_lines.append(f"Número de operaciones cerradas: {num_trades}")
        report_lines.append(f"Operaciones ganadoras: {winners}")
        report_lines.append(f"Winrate: {(winners/num_trades*100) if num_trades else 0:.2f}%")
        report_lines.append(f"Retorno total: {total_return_pct:.2f}%")
        report_lines.append(f"CAGR: {cagr:.2f}%")
        report_lines.append(f"Sharpe ratio: {sharpe_ratio:.2f}")
        report_lines.append(f"Profit factor: {profit_factor:.2f}")
        report_lines.append(f"Máx. drawdown global: {max_drawdown_global:.2f}%")
        report_lines.append("")
        if self.closed_trades:
            report_lines.append("Detalle de operaciones:")
            for i, t in enumerate(self.closed_trades, 1):
                entry_str = t['entry'].strftime('%B-%Y')
                exit_str = t['exit'].strftime('%B-%Y')
                report_lines.append(f"  {i}. {entry_str} → {exit_str}: {t['return_%']:.2f}%")

        return "\n".join(report_lines)

class TrendFollowingStrategy(TradingStrategy):
    """Estrategia de seguimiento de tendencias."""
    def __init__(self, stop_loss_pct=0.05, take_profit_pct=0.15, initial_capital=100000, indicator_cols=None):
        super().__init__(stop_loss_pct, take_profit_pct, initial_capital, indicator_cols)
        self.sma_col = self.indicator_cols.get('sma_col', 'SMA_')
        self.ema_col = self.indicator_cols.get('ema_col', 'EMA_')
        self.macd_col = self.indicator_cols.get('macd_col', 'MACD')
        self.macd_signal_col = self.indicator_cols.get('macd_signal_col', 'MACD_signal')

    def generate_signals(self, df):
        for i in range(1, len(df)):
            prev_sma, prev_ema = df[self.sma_col].iloc[i - 1], df[self.ema_col].iloc[i - 1]
            sma, ema = df[self.sma_col].iloc[i], df[self.ema_col].iloc[i]
            macd, macd_sig = df[self.macd_col].iloc[i], df[self.macd_signal_col].iloc[i]
            if (prev_sma < prev_ema and sma >= ema) and (macd > macd_sig):
                df.at[df.index[i], 'Signal'] = 1
            elif (prev_sma > prev_ema and sma <= ema) and (macd < macd_sig):
                df.at[df.index[i], 'Signal'] = -1

class SwingStrategy(TradingStrategy):
    """Estrategia de swing trading."""
    def __init__(self, stop_loss_pct=0.05, take_profit_pct=0.15, initial_capital=100000, indicator_cols=None):
        super().__init__(stop_loss_pct, take_profit_pct, initial_capital, indicator_cols)
        self.rsi_col = self.indicator_cols.get('rsi_col', 'RSI_')
        self.sma_col = self.indicator_cols.get('sma_col', 'SMA_')

    def generate_signals(self, df):
        for i in range(1, len(df)):
            rsi = df[self.rsi_col].iloc[i]
            sma = df[self.sma_col].iloc[i]
            close = df['Close'].iloc[i]
            prev_close = df['Close'].iloc[i - 1]
            if rsi < 30 and close > sma and prev_close <= sma:
                df.at[df.index[i], 'Signal'] = 1
            elif rsi > 70 or (close < sma and prev_close >= sma):
                df.at[df.index[i], 'Signal'] = -1

class ContrarianStrategy(TradingStrategy):
    """Estrategia contrarian/reversión a la media."""
    def __init__(self, stop_loss_pct=0.05, take_profit_pct=0.15, initial_capital=100000, indicator_cols=None):
        super().__init__(stop_loss_pct, take_profit_pct, initial_capital, indicator_cols)
        self.rsi_col = self.indicator_cols.get('rsi_col', 'RSI_')
        self.bollinger_lower_col = self.indicator_cols.get('bollinger_lower_col', 'Bollinger_Lower')

    def generate_signals(self, df):
        for i in range(1, len(df)):
            rsi = df[self.rsi_col].iloc[i]
            close = df['Close'].iloc[i]
            lower_bb = df[self.bollinger_lower_col].iloc[i] if self.bollinger_lower_col in df.columns else np.nan
            if rsi < 25 and close < lower_bb:
                df.at[df.index[i], 'Signal'] = 1
            elif rsi > 75:
                df.at[df.index[i], 'Signal'] = -1

# Función principal para ejecutar todas las estrategias
def run_backtest(df, indicator_cols=None):
    if indicator_cols is None:
        indicator_cols = {
            'sma_col': 'SMA_',
            'ema_col': 'EMA_',
            'rsi_col': 'RSI_',
            'macd_col': 'MACD',
            'macd_signal_col': 'MACD_signal',
            'bollinger_upper_col': 'Bollinger_Upper',
            'bollinger_lower_col': 'Bollinger_Lower'
        }
    strategies = [
        TrendFollowingStrategy(indicator_cols=indicator_cols),
        SwingStrategy(indicator_cols=indicator_cols),
        ContrarianStrategy(indicator_cols=indicator_cols)
    ]
    reports = {}
    for strategy in strategies:
        reports[strategy.__class__.__name__] = strategy.simulate(df)
    return reports

# Ejemplo de uso
if __name__ == "__main__":
    # Simulación con datos de ejemplo (debes cargar tu DataFrame aquí)
    df = pd.read_csv("data/processed/NVDA_diario_processed.csv", index_col=0, parse_dates=True)
    results = run_backtest(df)
    for name, report in results.items():
        print(report)