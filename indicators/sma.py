import pandas as pd

def calcular_sma(data: pd.DataFrame, period: int = 20, price_col: str = "Close") -> pd.Series:
    """
    Calcula la Media Móvil Simple (SMA).

    :param data: DataFrame que contiene la columna especificada en price_col
    :param period: Número de periodos para la media móvil
    :param price_col: Columna de precios a usar (ej. 'Close' o 'Adj Close')
    :return: Serie de SMA
    """
    if price_col not in data.columns:
        raise ValueError(f"El DataFrame debe contener la columna '{price_col}'")
    return data[price_col].rolling(window=period).mean()