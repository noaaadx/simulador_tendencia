import pandas as pd
import locale
import numpy as np

# Configurar localización para meses en español
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_TIME, '')

def simulate_signals(df):
    """
    Simula señales de compra/venta y calcula retornos hipotéticos basados en indicadores.
    """
    if df.empty:
        return "No hay datos suficientes para la simulación."

    # Crear una copia del DataFrame
    df = df.copy()

    # Inicializar columnas
    df['Signal'] = 0
    df['Position'] = 0
    df['Returns'] = 0.0

    rsi_col = next((col for col in df.columns if col.startswith("RSI_")), None)
    sma_col = next((col for col in df.columns if col.startswith("SMA_")), None)
    ema_col = next((col for col in df.columns if col.startswith("EMA_")), None)

    if "MACD" in df.columns and "MACD_signal" in df.columns and rsi_col and sma_col and ema_col:
        # Señales de compra: Confirmación de RSI < 30 y MACD cruza arriba, o precio toca banda inferior
        df.loc[((df[rsi_col] < 30) & (df['MACD'].shift(1) < df['MACD_signal'].shift(1)) & (df['MACD'] > df['MACD_signal'])) | 
               (df['Close'] < df['Bollinger_Lower']), 'Signal'] = 1
        
        # Señales de venta: Confirmación de RSI > 70 y MACD cruza abajo, o precio toca banda superior
        df.loc[((df[rsi_col] > 70) & (df['MACD'].shift(1) > df['MACD_signal'].shift(1)) & (df['MACD'] < df['MACD_signal'])) | 
               (df['Close'] > df['Bollinger_Upper']) | 
               ((df[sma_col].shift(1) > df[ema_col].shift(1)) & (df[sma_col] < df[ema_col])), 'Signal'] = -1

        # Simular posiciones
        position = 0
        for i, idx in enumerate(df.index):
            if df['Signal'].iloc[i] == 1:
                position = 1
            elif df['Signal'].iloc[i] == -1:
                position = 0
            df.loc[idx, 'Position'] = position

        # Calcular retornos
        df['Returns'] = df['Close'].pct_change() * df['Position'].shift(1).fillna(0)
        total_returns = df['Returns'].sum() * 100
        num_trades = df['Signal'].abs().sum()
        winning_trades = (df['Returns'] > 0).sum()

        # Calcular máximo drawdown
        cumulative_returns = (1 + df['Returns']).cumprod()
        peak = cumulative_returns.cummax()
        drawdown = (cumulative_returns - peak) / peak
        max_drawdown = np.min(drawdown) * 100 if not drawdown.empty and not np.all(np.isnan(drawdown)) else 0.0

        # Resumir fechas por mes
        buy_signals = df[df['Signal'] == 1].index.strftime('%B-%Y')
        sell_signals = df[df['Signal'] == -1].index.strftime('%B-%Y')
        buy_dates = sorted(set(buy_signals))
        sell_dates = sorted(set(sell_signals))

        report = f"Simulación de señales en el período:\n"
        report += f"Número de operaciones: {num_trades}\n"
        report += f"Operaciones ganadoras: {winning_trades}\n"
        report += f"Retorno hipotético total: {total_returns:.2f}%\n"
        report += f"Máximo drawdown: {max_drawdown:.2f}%\n\n"
        report += f"Señales de compra: {', '.join(buy_dates)} ({len(buy_signals)} días).\n"
        report += f"Señales de venta: {', '.join(sell_dates)} ({len(sell_signals)} días).\n"

        return report
    else:
        return "No hay suficientes indicadores para la simulación."