import pandas as pd

def generate_historical_analysis(df):
    """
    Genera un reporte textual de análisis histórico basado en los indicadores.
    """
    if df.empty:
        return "No hay datos suficientes para el análisis."

    analysis = ""

    # Tendencia general
    first_close = df['Close'].iloc[0]
    last_close = df['Close'].iloc[-1]
    trend = "alcista" if last_close > first_close else "bajista" if last_close < first_close else "lateral"
    change_pct = ((last_close - first_close) / first_close) * 100
    analysis += f"Tendencia general en el período: {trend}. Cambio total: {change_pct:.2f}% (desde {df.index[0].strftime('%Y-%m')} hasta {df.index[-1].strftime('%Y-%m')}).\n\n"

    # Análisis de SMA/EMA
    sma_col = next((col for col in df.columns if col.startswith("SMA_")), None)
    ema_col = next((col for col in df.columns if col.startswith("EMA_")), None)
    if sma_col and ema_col:
        bullish_cross = df[(df[sma_col].shift(1) < df[ema_col].shift(1)) & (df[sma_col] > df[ema_col])].index
        bearish_cross = df[(df[sma_col].shift(1) > df[ema_col].shift(1)) & (df[sma_col] < df[ema_col])].index
        if not bullish_cross.empty:
            analysis += f"Cruces alcistas de SMA/EMA (señal de compra potencial): {', '.join(bullish_cross.strftime('%Y-%m'))}.\n"
        else:
            analysis += "No se detectaron cruces alcistas de SMA/EMA.\n"
        if not bearish_cross.empty:
            analysis += f"Cruces bajistas de SMA/EMA (señal de venta potencial): {', '.join(bearish_cross.strftime('%Y-%m'))}.\n"
        else:
            analysis += "No se detectaron cruces bajistas de SMA/EMA.\n"
        analysis += "\n"

    # Análisis de RSI
    rsi_col = next((col for col in df.columns if col.startswith("RSI_")), None)
    if rsi_col:
        overbought = df[df[rsi_col] > 70].index
        oversold = df[df[rsi_col] < 30].index
        if not overbought.empty:
            analysis += f"Períodos de sobrecompra (RSI > 70, posible corrección bajista): {', '.join(overbought.strftime('%Y-%m'))}.\n"
        else:
            analysis += "No se detectaron períodos de sobrecompra (RSI > 70).\n"
        if not oversold.empty:
            analysis += f"Períodos de sobreventa (RSI < 30, posible recuperación alcista): {', '.join(oversold.strftime('%Y-%m'))}.\n"
        else:
            analysis += "No se detectaron períodos de sobreventa (RSI < 30).\n"
        analysis += "\n"

    # Análisis de MACD
    if "MACD" in df.columns and "MACD_signal" in df.columns:
        bullish_macd = df[(df['MACD'].shift(1) < df['MACD_signal'].shift(1)) & (df['MACD'] > df['MACD_signal'])].index
        bearish_macd = df[(df['MACD'].shift(1) > df['MACD_signal'].shift(1)) & (df['MACD'] < df['MACD_signal'])].index
        if not bullish_macd.empty:
            analysis += f"Cruces alcistas de MACD (señal de momentum alcista): {', '.join(bullish_macd.strftime('%Y-%m'))}.\n"
        else:
            analysis += "No se detectaron cruces alcistas de MACD.\n"
        if not bearish_macd.empty:
            analysis += f"Cruces bajistas de MACD (señal de momentum bajista): {', '.join(bearish_macd.strftime('%Y-%m'))}.\n"
        else:
            analysis += "No se detectaron cruces bajistas de MACD.\n"
        analysis += "\n"

    # Análisis de Bollinger Bands
    if "Bollinger_Upper" in df.columns and "Bollinger_Lower" in df.columns:
        touch_upper = df[df['Close'] > df['Bollinger_Upper']].index
        touch_lower = df[df['Close'] < df['Bollinger_Lower']].index
        if not touch_upper.empty:
            analysis += f"Toques a banda superior de Bollinger (potencial corrección bajista): {', '.join(touch_upper.strftime('%Y-%m'))}.\n"
        else:
            analysis += "No se detectaron toques a la banda superior de Bollinger.\n"
        if not touch_lower.empty:
            analysis += f"Toques a banda inferior de Bollinger (potencial recuperación alcista): {', '.join(touch_lower.strftime('%Y-%m'))}.\n"
        else:
            analysis += "No se detectaron toques a la banda inferior de Bollinger.\n"
        analysis += "\n"

    return analysis