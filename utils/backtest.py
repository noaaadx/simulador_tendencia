import pandas as pd

def simulate_signals(df):
    """
    Simula señales de compra/venta y calcula retornos hipotéticos basados en indicadores.
    """
    if df.empty:
        return "No hay datos suficientes para la simulación."

    # Inicializar columnas para señales
    df['Signal'] = 0
    df['Position'] = 0
    df['Returns'] = 0.0

    rsi_col = next((col for col in df.columns if col.startswith("RSI_")), None)
    if "MACD" in df.columns and "MACD_signal" in df.columns and rsi_col:
        # Señales de compra: MACD cruza arriba de señal o RSI < 40
        df.loc[(df['MACD'].shift(1) < df['MACD_signal'].shift(1)) & (df['MACD'] > df['MACD_signal']) | (df[rsi_col] < 40), 'Signal'] = 1
        
        # Señales de venta: RSI > 70 o MACD cruza abajo de señal
        df.loc[((df[rsi_col] > 70) | ((df['MACD'].shift(1) > df['MACD_signal'].shift(1)) & (df['MACD'] < df['MACD_signal']))) & (df['Signal'] != 1), 'Signal'] = -1

        # Simular posiciones (1 = comprado, 0 = sin posición)
        position = 0
        for i in range(len(df)):
            if df['Signal'].iloc[i] == 1:
                position = 1
            elif df['Signal'].iloc[i] == -1:
                position = 0
            df['Position'].iloc[i] = position

        # Calcular retornos (porcentaje de cambio cuando está en posición)
        df['Returns'] = df['Close'].pct_change() * df['Position'].shift(1).fillna(0)
        total_returns = df['Returns'].sum() * 100
        num_trades = df['Signal'].abs().sum()
        winning_trades = (df['Returns'] > 0).sum()

        report = f"Simulación de señales en el período:\n"
        report += f"Número de operaciones: {num_trades}\n"
        report += f"Operaciones ganadoras: {winning_trades}\n"
        report += f"Retorno hipotético total: {total_returns:.2f}%\n\n"
        report += f"Señales de compra: {', '.join(df[df['Signal'] == 1].index.strftime('%Y-%m'))}\n"
        report += f"Señales de venta: {', '.join(df[df['Signal'] == -1].index.strftime('%Y-%m'))}\n"

        return report
    else:
        return "No hay suficientes indicadores para la simulación."