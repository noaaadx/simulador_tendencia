# utils/data_loader.py
import yfinance as yf
import pandas as pd
import os

def download_data(ticker: str, period: str = "1y", save_path: str = "data/raw") -> pd.DataFrame:
    """
    Descarga datos históricos de Yahoo Finance y los guarda en CSV.

    :param ticker: símbolo de la empresa, ej: 'AAPL'
    :param period: período de tiempo, ej: '1y', '6mo', '3mo'
    :param save_path: carpeta donde guardar CSV
    :return: DataFrame con datos históricos
    """
    # Descargar datos
    df = yf.download(ticker, period=period)
    
    # Crear carpeta si no existe
    os.makedirs(save_path, exist_ok=True)
    
    # Guardar CSV
    file_path = os.path.join(save_path, f"{ticker}.csv")
    df.to_csv(file_path)
    
    print(f"[INFO] Datos de {ticker} guardados en {file_path}")
    return df
