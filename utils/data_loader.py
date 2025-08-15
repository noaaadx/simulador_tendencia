import yfinance as yf
import pandas as pd
import os

def download_data(ticker: str, period: str = "1y", interval: str = "1d", save_path: str = "data/raw") -> pd.DataFrame:
    """
    Descarga datos históricos de Yahoo Finance y los guarda en CSV.

    :param ticker: símbolo de la empresa, ej: 'AAPL'
    :param period: período de tiempo, ej: '1y', '6mo', '3mo'
    :param interval: intervalo de los datos, ej: '1d' para diario
    :param save_path: carpeta donde guardar CSV
    :return: DataFrame con datos históricos
    """
    try:
        df = yf.download(ticker, period=period, interval=interval, auto_adjust=False)
        if df.empty:
            raise ValueError(f"No se encontraron datos para el ticker {ticker}")
        os.makedirs(save_path, exist_ok=True)
        file_path = os.path.join(save_path, f"{ticker}_{interval}.csv")
        df.to_csv(file_path)
        print(f"[INFO] Datos de {ticker} ({interval}) guardados en {file_path}")
        return df
    except Exception as e:
        print(f"[ERROR] Fallo al descargar datos: {e}")
        return pd.DataFrame()