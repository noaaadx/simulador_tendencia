import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from pandas.plotting import register_matplotlib_converters

# Registrar convertidores 
register_matplotlib_converters()

def plot_indicators(df, ticker, price_col="Close"):
    """
    Genera dos figuras: una con precio, SMA, EMA, Bollinger y detalles numéricos; otra con RSI y MACD.
    """
    # Asegurar que el índice sea datetime con tz
    df = df.copy()
    df.index = pd.to_datetime(df.index, utc=True)

    sns.set(style="whitegrid")
    
    # Filtrar señales únicas por mes
    if 'Signal' in df.columns:
        df['YearMonth'] = df.index.strftime('%Y-%m')
        buy_signals = df[df['Signal'] == 1].groupby('YearMonth').first()
        sell_signals = df[df['Signal'] == -1].groupby('YearMonth').first()
        df = df.drop(columns=['YearMonth'])
    
    # Primera figura: Precio, SMA, EMA, Bollinger
    fig1, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    
    # Precio, SMA, EMA
    ax1.plot(df.index, df[price_col], label='Precio', color='blue')
    sma_col = next((col for col in df.columns if col.startswith("SMA_")), None)
    ema_col = next((col for col in df.columns if col.startswith("EMA_")), None)
    if sma_col:
        ax1.plot(df.index, df[sma_col], label=sma_col, color='orange')
    if ema_col:
        ax1.plot(df.index, df[ema_col], label=ema_col, color='green')
    
    # Señales de compra/venta con precios
    if 'Signal' in df.columns:
        for idx, row in buy_signals.iterrows():
            ax1.plot(idx, row[price_col], '^', markersize=10, color='green', label='Compra' if idx == buy_signals.index[0] else "")
            ax1.annotate(f"${row[price_col]:.2f}", (idx, row[price_col]), xytext=(0, 10), textcoords='offset points', ha='center', fontsize=8, bbox=dict(facecolor='white', alpha=0.8))
        for idx, row in sell_signals.iterrows():
            ax1.plot(idx, row[price_col], 'v', markersize=10, color='red', label='Venta' if idx == sell_signals.index[0] else "")
            ax1.annotate(f"${row[price_col]:.2f}", (idx, row[price_col]), xytext=(0, -15), textcoords='offset points', ha='center', fontsize=8, bbox=dict(facecolor='white', alpha=0.8))
    
    # Máximos y mínimos
    max_price = df[price_col].max()
    min_price = df[price_col].min()
    max_idx = df[price_col].idxmax()
    min_idx = df[price_col].idxmin()
    ax1.axhline(max_price, color='red', linestyle='--', alpha=0.5, label=f'Máximo: ${max_price:.2f}')
    ax1.axhline(min_price, color='green', linestyle='--', alpha=0.5, label=f'Mínimo: ${min_price:.2f}')
    ax1.annotate(f"${max_price:.2f}", (max_idx, max_price), xytext=(10, 10), textcoords='offset points', color='red', fontsize=8, weight='bold', bbox=dict(facecolor='white', alpha=0.8))
    ax1.annotate(f"${min_price:.2f}", (min_idx, min_price), xytext=(10, -20), textcoords='offset points', color='green', fontsize=8, weight='bold', bbox=dict(facecolor='white', alpha=0.8))
    
    # Precio de cierre
    last_close = df[price_col].iloc[-1]
    ax1.set_title(f'{ticker} - Precio, SMA, EMA (Cierre: ${last_close:.2f})')
    ax1.set_ylabel('Precio')
    ax1.legend()
    
    # Bandas de Bollinger
    if 'Bollinger_Upper' in df.columns and 'Bollinger_Lower' in df.columns:
        ax2.plot(df.index, df['Bollinger_Upper'], label='Banda Superior', color='purple', linestyle='--')
        ax2.plot(df.index, df[price_col], label='Precio', color='blue')
        ax2.plot(df.index, df['Bollinger_Lower'], label='Banda Inferior', color='purple', linestyle='--')
        ax2.fill_between(df.index, df['Bollinger_Upper'], df['Bollinger_Lower'], color='purple', alpha=0.1)
        # Etiquetas en toques a bandas
        touch_upper = df[df[price_col] > df['Bollinger_Upper']]
        touch_lower = df[df[price_col] < df['Bollinger_Lower']]
        for idx, row in touch_upper.iterrows():
            ax2.annotate(f"${row[price_col]:.2f}", (idx, row[price_col]), xytext=(0, 10), textcoords='offset points', ha='center', fontsize=8, bbox=dict(facecolor='white', alpha=0.8))
        for idx, row in touch_lower.iterrows():
            ax2.annotate(f"${row[price_col]:.2f}", (idx, row[price_col]), xytext=(0, -15), textcoords='offset points', ha='center', fontsize=8, bbox=dict(facecolor='white', alpha=0.8))
    ax2.set_title('Bandas de Bollinger')
    ax2.set_ylabel('Precio')
    ax2.legend()
    
    plt.tight_layout()
    
    # Segunda figura: RSI y MACD
    fig2, (ax3, ax4) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    
    # RSI
    rsi_col = next((col for col in df.columns if col.startswith("RSI_")), None)
    if rsi_col:
        ax3.plot(df.index, df[rsi_col], label=rsi_col, color='blue')
        ax3.axhline(70, color='red', linestyle='--', label='Sobrecompra (70)')
        ax3.axhline(30, color='green', linestyle='--', label='Sobreventa (30)')
        # Etiquetas en sobrecompra/sobreventa
        overbought = df[df[rsi_col] > 70]
        oversold = df[df[rsi_col] < 30]
        for idx, row in overbought.iterrows():
            ax3.annotate(f"{row[rsi_col]:.2f}", (idx, row[rsi_col]), xytext=(0, 10), textcoords='offset points', ha='center', fontsize=8, bbox=dict(facecolor='white', alpha=0.8))
        for idx, row in oversold.iterrows():
            ax3.annotate(f"{row[rsi_col]:.2f}", (idx, row[rsi_col]), xytext=(0, -15), textcoords='offset points', ha='center', fontsize=8, bbox=dict(facecolor='white', alpha=0.8))
        ax3.set_title(f'{ticker} - RSI')
        ax3.set_ylabel('RSI')
        ax3.legend()
    
    # MACD
    if 'MACD' in df.columns and 'MACD_signal' in df.columns:
        ax4.plot(df.index, df['MACD'], label='MACD', color='blue')
        ax4.plot(df.index, df['MACD_signal'], label='Señal', color='orange')
        ax4.bar(df.index, df['MACD_hist'], label='Histograma', color='gray')
        # Etiquetas en cruces MACD
        bullish_macd = df[(df['MACD'].shift(1) < df['MACD_signal'].shift(1)) & (df['MACD'] > df['MACD_signal'])]
        bearish_macd = df[(df['MACD'].shift(1) > df['MACD_signal'].shift(1)) & (df['MACD'] < df['MACD_signal'])]
        for idx, row in bullish_macd.iterrows():
            ax4.annotate(f"{row['MACD']:.2f}", (idx, row['MACD']), xytext=(0, 10), textcoords='offset points', ha='center', fontsize=8, bbox=dict(facecolor='white', alpha=0.8))
        for idx, row in bearish_macd.iterrows():
            ax4.annotate(f"{row['MACD']:.2f}", (idx, row['MACD']), xytext=(0, -15), textcoords='offset points', ha='center', fontsize=8, bbox=dict(facecolor='white', alpha=0.8))
        ax4.set_title('MACD')
        ax4.set_ylabel('MACD')
        ax4.legend()
    
    plt.tight_layout()
    plt.show()