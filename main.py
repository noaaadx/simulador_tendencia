# main.py
from utils.data_loader import download_data
from indicators.sma import calcular_sma
from indicators.ema import calcular_ema
from indicators.rsi import calculate_rsi
from indicators.macd import calculate_macd
from indicators.bollinger import calculate_bollinger
from utils.plotter import plot_indicators
from utils.analysis import generate_historical_analysis
from utils.strategies import run_backtest
from utils.simulation import run_basic_simulation, run_advanced_simulation  # <-- nuevas funciones

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
    
    interval_map = {"diario": "1d", "mensual": "1mo", "bimestral": "2mo"}
    df = download_data(ticker, period, interval=interval_map[interval])
    
    if df.empty:
        print(f"[ERROR] No se encontraron datos para el ticker {ticker}")
        return
    
    df.index = pd.to_datetime(df.index, utc=True)
    
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]
    df.columns = [col.capitalize() for col in df.columns]
    
    if interval in ["mensual", "bimestral"]:
        resample_rule = 'M' if interval == "mensual" else '2M'
        available_columns = [col for col in ['Open', 'High', 'Low', 'Close', 'Adj close', 'Volume'] if col in df.columns]
        if not available_columns:
            print(f"[ERROR] No se encontraron columnas válidas en el DataFrame: {df.columns.tolist()}")
            return
        agg_dict = {col: 'last' for col in available_columns}
        agg_dict.update({'Open': 'first', 'High': 'max', 'Low': 'min', 'Volume': 'sum'})
        df = df[available_columns].resample(resample_rule).agg(agg_dict).dropna(how='all')
    
    price_col = "Adj Close" if "Adj Close" in df.columns else "Close"
    
    # Configuración de indicadores
    sma_period = 20 if interval == "diario" else 5
    ema_period = 20 if interval == "diario" else 5
    rsi_period = 14 if interval == "diario" else 5
    macd_fast, macd_slow, macd_signal = (12, 26, 9) if interval == "diario" else (5, 10, 5)
    bollinger_period = 20 if interval == "diario" else 3
    
    # Calcular indicadores
    df[f"SMA_{sma_period}"] = calcular_sma(df, sma_period, price_col=price_col)
    df[f"EMA_{ema_period}"] = calcular_ema(df, ema_period, price_col=price_col)
    df = calculate_rsi(df, period=rsi_period, price_col=price_col)
    df = calculate_macd(df, price_col=price_col, fast=macd_fast, slow=macd_slow, signal=macd_signal)
    df = calculate_bollinger(df, period=bollinger_period, price_col=price_col, num_std=2)
    
    # --- 1️⃣ Análisis histórico ---
    analysis_report = generate_historical_analysis(df)
    print("\n--- Análisis Histórico ---")
    print(analysis_report)
    
    # --- 2️⃣ Simulación normal ---
    print("\n--- Simulación de Señales ---")
    basic_report = run_basic_simulation(df)
    print(basic_report)
    
    # --- 3️⃣ Simulación avanzada ---
    print("\n=== Simulación Avanzada (SMA+EMA+MACD+RSI+Bollinger) ===")
    advanced_report = run_advanced_simulation(df)
    print(advanced_report)
    
    # --- 4️⃣ Estrategias ---
    indicator_cols = {
        'sma_col': f"SMA_{sma_period}",
        'ema_col': f"EMA_{ema_period}",
        'rsi_col': f"RSI_{rsi_period}",
        'macd_col': 'MACD',
        'macd_signal_col': 'MACD_signal',
        'bollinger_upper_col': 'Bollinger_Upper',
        'bollinger_lower_col': 'Bollinger_Lower'
    }
    strategy_reports = run_backtest(df, indicator_cols)
    print("\n--- Resultados Backtest Estrategias ---")
    for name, report in strategy_reports.items():
        print(report)
    
    # --- Guardar reportes ---
    processed_path = os.path.join("data", "processed")
    os.makedirs(processed_path, exist_ok=True)
    
    report_path = os.path.join(processed_path, f"{ticker}_{interval}_report.txt")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("--- Análisis Histórico ---\n" + analysis_report + "\n\n")
        f.write("--- Simulación Normal ---\n" + basic_report + "\n\n")
        f.write("--- Simulación Avanzada ---\n" + advanced_report + "\n\n")
        f.write("--- Resultados Backtest Estrategias ---\n")
        for name, report in strategy_reports.items():
            f.write(report + "\n\n")
    print(f"Reporte guardado en: {report_path}")
    
    output_file = os.path.join(processed_path, f"{ticker}_{interval}_processed.csv")
    df.reset_index().to_csv(output_file, index=False)
    
    print(f"\nPrimeras filas con indicadores ({interval}):")
    print(df.head())
    print(f"\nArchivo guardado en: {output_file}")
    
    plot_indicators(df, ticker, price_col=price_col)

if __name__ == "__main__":
    main()
