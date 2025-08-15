# tests/test_indicators.py
import pandas as pd
from indicators.sma import calcular_sma
from indicators.ema import calcular_ema
from indicators.rsi import calculate_rsi
from indicators.macd import calculate_macd
from indicators.bollinger import calculate_bollinger
import pytest

@pytest.fixture
def sample_df():
    data = {
        'Close': [100, 105, 110, 115, 120, 125]
    }
    df = pd.DataFrame(data)
    return df

def test_calcular_sma(sample_df):
    sma = calcular_sma(sample_df, period=3, price_col='Close')
    assert len(sma) == len(sample_df)
    assert pd.isna(sma.iloc[1])  # NaN en las primeras filas
    assert sma.iloc[-1] == (115 + 120 + 125) / 3

def test_calcular_ema(sample_df):
    ema = calcular_ema(sample_df, period=3, price_col='Close')
    assert len(ema) == len(sample_df)
    assert ema.iloc[-1] > 120  # EMA ponderada hacia los últimos valores

def test_calculate_rsi(sample_df):
    df_rsi = calculate_rsi(sample_df, period=3, price_col='Close')
    assert 'RSI_3' in df_rsi.columns
    assert df_rsi['RSI_3'].iloc[-1] == 100  # Con datos crecientes, RSI tiende a 100

def test_calculate_macd(sample_df):
    df_macd = calculate_macd(sample_df, price_col='Close', fast=2, slow=4, signal=1)
    assert 'MACD' in df_macd.columns
    assert 'MACD_signal' in df_macd.columns
    assert 'MACD_hist' in df_macd.columns
    assert df_macd['MACD_hist'].iloc[-1] > 0  # Con tendencia alcista

def test_calculate_bollinger(sample_df):
    df_boll = calculate_bollinger(sample_df, period=3, price_col='Close', num_std=2)
    assert 'Bollinger_Upper' in df_boll.columns
    assert 'Bollinger_Lower' in df_boll.columns
    assert df_boll['Bollinger_Upper'].iloc[-1] > df_boll['Close'].iloc[-1]