from utils.data_loader import download_data
from indicators.sma import calcular_sma
from indicators.ema import calcular_ema
from indicators.rsi import calculate_rsi
from indicators.macd import calculate_macd
from indicators.bollinger import calculate_bollinger
from utils.plotter import plot_indicators
from utils.analysis import generate_historical_analysis
from utils.backtest import simulate_signals
import pandas as pd
import os

def main():
    print("=== Simulador de Tendencia Histórica + Técnica ===")
    
    ticker = input("Ingrese el ticker de la empresa (ej. AAPL, NVDA, AHCO): ").upper()
    period = input("Ingrese el período (ej. 1y, 6mo, 3mo): ")
    interval = input("Ingrese el intervalo (diario, mensual, bimestral): ").lower().strip()
    
    valid_intervals = ["diario", "mensual", "bimestral"]
    if interval not in valid_intervals:
        print(f"[ERROR] Intervalo inválido. Use uno de: {', '.join(valid_intervals)}")
        return
    
    df = download_data(ticker, period, interval="1d")
    
    if df.empty:
        print(f"[ERROR] No se encontraron datos para el ticker {ticker}")
        return
    
    print(f"[DEBUG] Columnas del DataFrame original: {df.columns.tolist()}")
    
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]
    
    df.columns = [col.capitalize() for col in df.columns]
    
    print(f"[DEBUG] Columnas normalizadas: {df.columns.tolist()}")
    
    if interval in ["mensual", "bimestral"]:
        resample_rule = 'M' if interval == "mensual" else '2M'
        available_columns = [col for col in ['Open', 'High', 'Low', 'Close', 'Adj close', 'Volume'] if col in df.columns]
        if not available_columns:
            print(f"[ERROR] No se encontraron columnas válidas en el DataFrame: {df.columns.tolist()}")
            return
        agg_dict = {col: 'last' for col in available_columns}
        agg_dict.update({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Volume': 'sum'
        })
        df = df[available_columns].resample(resample_rule).agg(agg_dict).dropna(how='all')
    
    price_col = "Adj Close" if "Adj Close" in df.columns else "Close"
    
    sma_period = 3 if interval in ["mensual", "bimestral"] else 20
    ema_period = 3 if interval in ["mensual", "bimestral"] else 20
    rsi_period = 3 if interval in ["mensual", "bimestral"] else 14
    macd_fast = 2 if interval in ["mensual", "bimestral"] else 12
    macd_slow = 4 if interval in ["mensual", "bimestral"] else 26
    macd_signal = 1 if interval in ["mensual", "bimestral"] else 9
    bollinger_period = 3 if interval in ["mensual", "bimestral"] else 20
    
    df[f"SMA_{sma_period}"] = calcular_sma(df, sma_period, price_col=price_col)
    df[f"EMA_{ema_period}"] = calcular_ema(df, ema_period, price_col=price_col)
    df = calculate_rsi(df, period=rsi_period, price_col=price_col)
    df = calculate_macd(df, price_col=price_col, fast=macd_fast, slow=macd_slow, signal=macd_signal)
    df = calculate_bollinger(df, period=bollinger_period, price_col=price_col, num_std=2)
    
    analysis_report = generate_historical_analysis(df)
    print("\n--- Análisis Histórico ---")
    print(analysis_report)
    
    simulation_report = simulate_signals(df)
    print("\n--- Simulación de Señales ---")
    print(simulation_report)
    
    report_path = os.path.join("data", "processed", f"{ticker}_{interval}_report.txt")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("--- Análisis Histórico ---\n" + analysis_report + "\n\n--- Simulación de Señales ---\n" + simulation_report)
    print(f"Reporte guardado en: {report_path}")
    
    processed_path = os.path.join("data", "processed")
    os.makedirs(processed_path, exist_ok=True)
    
    output_file = os.path.join(processed_path, f"{ticker}_{interval}_processed.csv")
    df_with_date = df.reset_index()
    df_with_date.to_csv(output_file, index=False)
    
    print(f"\nPrimeras filas con indicadores ({interval}):")
    print(df.head())
    print(f"\nArchivo guardado en: {output_file}")
    
    plot_indicators(df, ticker, price_col=price_col)

if __name__ == "__main__":
    main()