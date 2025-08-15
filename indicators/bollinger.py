# indicators/bollinger.py
import pandas as pd

def calculate_bollinger(df, period=20, price_col="Close", num_std=2):
    df[f"SMA_{period}"] = df[price_col].rolling(window=period).mean()
    df[f"STD_{period}"] = df[price_col].rolling(window=period).std()
    df[f"Bollinger_Upper"] = df[f"SMA_{period}"] + (df[f"STD_{period}"] * num_std)
    df[f"Bollinger_Lower"] = df[f"SMA_{period}"] - (df[f"STD_{period}"] * num_std)
    return df
