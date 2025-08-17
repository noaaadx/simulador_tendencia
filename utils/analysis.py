import pandas as pd
import locale

# Configurar localización para meses en español
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_TIME, '')

def group_consecutive_dates(dates):
    """
    Agrupa fechas consecutivas en rangos (e.g., 'mayo-2025 a julio-2025').
    """
    if not dates:
        return ""
    dates = sorted(set(dates))
    ranges = []
    start = dates[0]
    prev = dates[0]
    for date in dates[1:]:
        if date == prev + pd.offsets.MonthEnd(1):
            prev = date
        else:
            ranges.append(f"{start.strftime('%B-%Y')} a {prev.strftime('%B-%Y')}" if start != prev else start.strftime('%B-%Y'))
            start = date
            prev = date
    ranges.append(f"{start.strftime('%B-%Y')} a {prev.strftime('%B-%Y')}" if start != prev else start.strftime('%B-%Y'))
    return ', '.join(ranges)

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
    analysis += f"Tendencia general en el período: {trend}. Cambio total: {change_pct:.2f}% (desde {df.index[0].strftime('%B-%Y')} hasta {df.index[-1].strftime('%B-%Y')}).\n"
    analysis += f"Precio inicial: ${first_close:.2f}, Precio final: ${last_close:.2f}\n\n"

    # Análisis de volumen
    if 'Volume' in df.columns:
        avg_volume = df['Volume'].mean()
        high_volume = df[df['Volume'] > avg_volume * 1.5]
        if not high_volume.empty:
            high_volume_dates = sorted(set(high_volume.index))
            high_volume_range = group_consecutive_dates(high_volume_dates)
            high_volume_values = [f"{row['Volume']:.0f}" for _, row in high_volume.iterrows()][:3]  # Limitar a 3 valores
            analysis += f"Días con volumen alto (>1.5x promedio): {high_volume_range} (Volumen: {', '.join(high_volume_values)}{', ...' if len(high_volume_values) > 3 else ''}).\n"
        else:
            analysis += "No se detectaron días con volumen alto.\n"
        analysis += "\n"

    # Análisis de SMA/EMA
    sma_col = next((col for col in df.columns if col.startswith("SMA_")), None)
    ema_col = next((col for col in df.columns if col.startswith("EMA_")), None)
    if sma_col and ema_col:
        # Precio vs SMA
        bullish_trend = df[df['Close'] > df[sma_col]]
        bearish_trend = df[df['Close'] < df[sma_col]]
        if not bullish_trend.empty:
            bullish_dates = sorted(set(bullish_trend.index))
            bullish_range = group_consecutive_dates(bullish_dates)
            analysis += f"Períodos con precio > SMA (tendencia alcista): {bullish_range} ({len(bullish_trend)} días).\n"
        else:
            analysis += "No se detectaron períodos con precio > SMA (tendencia alcista).\n"
        if not bearish_trend.empty:
            bearish_dates = sorted(set(bearish_trend.index))
            bearish_range = group_consecutive_dates(bearish_dates)
            analysis += f"Períodos con precio < SMA (tendencia bajista): {bearish_range} ({len(bearish_trend)} días).\n"
        else:
            analysis += "No se detectaron períodos con precio < SMA (tendencia bajista).\n"
        
        # Cruces SMA/EMA
        bullish_cross = df[(df[sma_col].shift(1) < df[ema_col].shift(1)) & (df[sma_col] > df[ema_col])]
        bearish_cross = df[(df[sma_col].shift(1) > df[ema_col].shift(1)) & (df[sma_col] < df[ema_col])]
        if not bullish_cross.empty:
            bullish_cross_info = [f"{date.strftime('%B-%Y')} (SMA={row[sma_col]:.2f}, EMA={row[ema_col]:.2f})" 
                                 for date, row in bullish_cross.iterrows()][:3]  # Limitar a 3
            analysis += f"Cruces alcistas de SMA/EMA (señal de compra potencial): {', '.join(bullish_cross_info)}{', ...' if len(bullish_cross) > 3 else ''}.\n"
        else:
            analysis += "No se detectaron cruces alcistas de SMA/EMA.\n"
        if not bearish_cross.empty:
            bearish_cross_info = [f"{date.strftime('%B-%Y')} (SMA={row[sma_col]:.2f}, EMA={row[ema_col]:.2f})" 
                                  for date, row in bearish_cross.iterrows()][:3]  # Limitar a 3
            analysis += f"Cruces bajistas de SMA/EMA (señal de venta potencial): {', '.join(bearish_cross_info)}{', ...' if len(bearish_cross) > 3 else ''}.\n"
        else:
            analysis += "No se detectaron cruces bajistas de SMA/EMA.\n"
        analysis += "\n"

    # Análisis de RSI
    rsi_col = next((col for col in df.columns if col.startswith("RSI_")), None)
    if rsi_col:
        overbought = df[df[rsi_col] > 70]
        oversold = df[df[rsi_col] < 30]
        if not overbought.empty:
            overbought_dates = sorted(set(overbought.index))
            overbought_range = group_consecutive_dates(overbought_dates)
            overbought_values = [f"{row[rsi_col]:.2f}" for _, row in overbought.iterrows()][:3]  # Limitar a 3
            analysis += f"Períodos de sobrecompra (RSI > 70, posible corrección bajista): {overbought_range} (RSI: {', '.join(overbought_values)}{', ...' if len(overbought) > 3 else ''}).\n"
        else:
            analysis += "No se detectaron períodos de sobrecompra (RSI > 70).\n"
        if not oversold.empty:
            oversold_dates = sorted(set(oversold.index))
            oversold_range = group_consecutive_dates(oversold_dates)
            oversold_values = [f"{row[rsi_col]:.2f}" for _, row in oversold.iterrows()][:3]  # Limitar a 3
            analysis += f"Períodos de sobreventa (RSI < 30, posible recuperación alcista): {oversold_range} (RSI: {', '.join(oversold_values)}{', ...' if len(oversold) > 3 else ''}).\n"
        else:
            analysis += "No se detectaron períodos de sobreventa (RSI < 30).\n"
        analysis += "\n"

    # Análisis de MACD
    if "MACD" in df.columns and "MACD_signal" in df.columns:
        bullish_macd = df[(df['MACD'].shift(1) < df['MACD_signal'].shift(1)) & (df['MACD'] > df['MACD_signal'])]
        bearish_macd = df[(df['MACD'].shift(1) > df['MACD_signal'].shift(1)) & (df['MACD'] < df['MACD_signal'])]
        if not bullish_macd.empty:
            bullish_macd_info = [f"{date.strftime('%B-%Y')} (MACD={row['MACD']:.2f}, Signal={row['MACD_signal']:.2f})" 
                                for date, row in bullish_macd.iterrows()][:3]  # Limitar a 3
            analysis += f"Cruces alcistas de MACD (señal de momentum alcista): {', '.join(bullish_macd_info)}{', ...' if len(bullish_macd) > 3 else ''}.\n"
        else:
            analysis += "No se detectaron cruces alcistas de MACD.\n"
        if not bearish_macd.empty:
            bearish_macd_info = [f"{date.strftime('%B-%Y')} (MACD={row['MACD']:.2f}, Signal={row['MACD_signal']:.2f})" 
                                 for date, row in bearish_macd.iterrows()][:3]  # Limitar a 3
            analysis += f"Cruces bajistas de MACD (señal de momentum bajista): {', '.join(bearish_macd_info)}{', ...' if len(bearish_macd) > 3 else ''}.\n"
        else:
            analysis += "No se detectaron cruces bajistas de MACD.\n"
        analysis += "\n"

    # Análisis de Bollinger Bands
    if "Bollinger_Upper" in df.columns and "Bollinger_Lower" in df.columns:
        touch_upper = df[df['Close'] > df['Bollinger_Upper']]
        touch_lower = df[df['Close'] < df['Bollinger_Lower']]
        if not touch_upper.empty:
            touch_upper_info = [f"{date.strftime('%B-%Y')} (Precio={row['Close']:.2f})" 
                                for date, row in touch_upper.iterrows()][:3]  # Limitar a 3
            analysis += f"Toques a banda superior de Bollinger (potencial corrección bajista): {', '.join(touch_upper_info)}{', ...' if len(touch_upper) > 3 else ''}.\n"
        else:
            analysis += "No se detectaron toques a la banda superior de Bollinger.\n"
        if not touch_lower.empty:
            touch_lower_info = [f"{date.strftime('%B-%Y')} (Precio={row['Close']:.2f})" 
                                for date, row in touch_lower.iterrows()][:3]  # Limitar a 3
            analysis += f"Toques a banda inferior de Bollinger (potencial recuperación alcista): {', '.join(touch_lower_info)}{', ...' if len(touch_lower) > 3 else ''}.\n"
        else:
            analysis += "No se detectaron toques a la banda inferior de Bollinger.\n"
        analysis += "\n"

    return analysis