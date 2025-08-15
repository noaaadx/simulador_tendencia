# indicators/macd.py
import pandas as pd

def calculate_macd(df, price_col="Close", fast=12, slow=26, signal=9):
    df["EMA_fast"] = df[price_col].ewm(span=fast, adjust=False).mean()
    df["EMA_slow"] = df[price_col].ewm(span=slow, adjust=False).mean()
    df["MACD"] = df["EMA_fast"] - df["EMA_slow"]
    df["MACD_signal"] = df["MACD"].ewm(span=signal, adjust=False).mean()
    df["MACD_hist"] = df["MACD"] - df["MACD_signal"]
    return df
