import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

def plot_indicators(df, ticker, price_col="Close"):
    """
    Grafica SMA, EMA, RSI, MACD y Bollinger Bands en dos figuras separadas, con señales de compra/venta.
    """
    plt.style.use("seaborn-darkgrid")

    # Verificar si hay suficientes datos para graficar
    if len(df) < 3:
        print(f"[ADVERTENCIA] El DataFrame tiene solo {len(df)} filas, algunos indicadores pueden no mostrarse correctamente.")
    
    # Figura 1: Precio + SMA/EMA y Bollinger Bands
    fig1, axes1 = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
    for ax in axes1:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.grid(True, linestyle='--', alpha=0.7)

    # Subgráfico 1: Precio + SMA + EMA + Señales
    axes1[0].plot(df.index, df[price_col], label="Precio Cierre", color="blue", linewidth=1.5)
    sma_col = next((col for col in df.columns if col.startswith("SMA_")), None)
    ema_col = next((col for col in df.columns if col.startswith("EMA_")), None)
    if sma_col and df[sma_col].notna().any():
        axes1[0].plot(df.index, df[sma_col], label=sma_col, color="orange", linewidth=1)
    if ema_col and df[ema_col].notna().any():
        axes1[0].plot(df.index, df[ema_col], label=ema_col, color="green", linewidth=1)
    
    # Marcar señales de compra/venta
    if 'Signal' in df.columns:
        buy_signals = df[df['Signal'] == 1]
        sell_signals = df[df['Signal'] == -1]
        axes1[0].plot(buy_signals.index, buy_signals[price_col], '^', markersize=10, color='green', label='Compra')
        axes1[0].plot(sell_signals.index, sell_signals[price_col], 'v', markersize=10, color='red', label='Venta')
    
    # Etiquetas para máximo y mínimo precio
    valid_prices = df[price_col].dropna()
    if not valid_prices.empty:
        max_price_idx = valid_prices.idxmax()
        min_price_idx = valid_prices.idxmin()
        axes1[0].annotate(f'Máx: ${valid_prices[max_price_idx]:.2f}', 
                          xy=(max_price_idx, valid_prices[max_price_idx]), 
                          xytext=(10, 10), textcoords='offset points', 
                          color='red', fontsize=10, weight='bold',
                          bbox=dict(facecolor='white', alpha=0.8))
        axes1[0].annotate(f'Mín: ${valid_prices[min_price_idx]:.2f}', 
                          xy=(min_price_idx, valid_prices[min_price_idx]), 
                          xytext=(10, -20), textcoords='offset points', 
                          color='green', fontsize=10, weight='bold',
                          bbox=dict(facecolor='white', alpha=0.8))
    
    axes1[0].set_title(f"{ticker} - Precio y Medias")
    axes1[0].set_ylabel("Precio ($)")
    axes1[0].legend()

    # Subgráfico 2: Bollinger Bands
    if "Bollinger_Upper" in df.columns and "Bollinger_Lower" in df.columns and df["Bollinger_Upper"].notna().any():
        axes1[1].plot(df.index, df[price_col], label="Precio Cierre", color="blue")
        axes1[1].plot(df.index, df["Bollinger_Upper"], label="Banda Superior", color="red", linestyle="--")
        axes1[1].plot(df.index, df["Bollinger_Lower"], label="Banda Inferior", color="green", linestyle="--")
        
        # Etiquetas para las bandas en el último punto válido
        last_valid_idx = df["Bollinger_Upper"].last_valid_index()
        if last_valid_idx:
            last_upper = df["Bollinger_Upper"].loc[last_valid_idx]
            last_lower = df["Bollinger_Lower"].loc[last_valid_idx]
            axes1[1].annotate(f'Sup: ${last_upper:.2f}', 
                              xy=(last_valid_idx, last_upper), 
                              xytext=(10, 10), textcoords='offset points', 
                              color='red', fontsize=10, weight='bold',
                              bbox=dict(facecolor='white', alpha=0.8))
            axes1[1].annotate(f'Inf: ${last_lower:.2f}', 
                              xy=(last_valid_idx, last_lower), 
                              xytext=(10, -20), textcoords='offset points', 
                              color='green', fontsize=10, weight='bold',
                              bbox=dict(facecolor='white', alpha=0.8))
        
        axes1[1].set_title("Bollinger Bands")
        axes1[1].set_ylabel("Precio ($)")
        axes1[1].legend()
    else:
        axes1[1].text(0.5, 0.5, "Datos insuficientes para Bollinger Bands", 
                      horizontalalignment='center', verticalalignment='center', 
                      fontsize=12, color='red')
        axes1[1].set_title("Bollinger Bands")
        axes1[1].set_ylabel("Precio ($)")

    fig1.tight_layout()
    plt.setp(axes1[-1].get_xticklabels(), rotation=45)
    fig1.suptitle(f"{ticker} - Análisis de Precio", fontsize=16, y=1.02)

    # Figura 2: RSI y MACD
    fig2, axes2 = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
    for ax in axes2:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.grid(True, linestyle='--', alpha=0.7)

    # Subgráfico 1: RSI
    rsi_col = next((col for col in df.columns if col.startswith("RSI_")), None)
    if rsi_col and df[rsi_col].notna().any():
        axes2[0].plot(df.index, df[rsi_col], label=rsi_col, color="purple")
        axes2[0].axhline(70, color="red", linestyle="--", label="Sobrecompra (70)")
        axes2[0].axhline(30, color="green", linestyle="--", label="Sobreventa (30)")
        
        # Etiqueta para el último valor válido de RSI
        last_valid_rsi_idx = df[rsi_col].last_valid_index()
        if last_valid_rsi_idx:
            last_rsi = df[rsi_col].loc[last_valid_rsi_idx]
            axes2[0].annotate(f'RSI: {last_rsi:.2f}', 
                              xy=(last_valid_rsi_idx, last_rsi), 
                              xytext=(10, 0), textcoords='offset points', 
                              color='purple', fontsize=10, weight='bold',
                              bbox=dict(facecolor='white', alpha=0.8))
        
        axes2[0].set_title("RSI")
        axes2[0].set_ylabel("RSI")
        axes2[0].legend()
    else:
        axes2[0].text(0.5, 0.5, "Datos insuficientes para RSI", 
                      horizontalalignment='center', verticalalignment='center', 
                      fontsize=12, color='red')
        axes2[0].set_title("RSI")
        axes2[0].set_ylabel("RSI")

    # Subgráfico 2: MACD
    if "MACD" in df.columns and "MACD_signal" in df.columns and df["MACD"].notna().any():
        axes2[1].plot(df.index, df["MACD"], label="MACD", color="blue")
        axes2[1].plot(df.index, df["MACD_signal"], label="Señal", color="red")
        axes2[1].bar(df.index, df["MACD_hist"], label="Histograma", color="gray", alpha=0.3)
        
        # Etiqueta para el último valor válido de MACD
        last_valid_macd_idx = df["MACD"].last_valid_index()
        if last_valid_macd_idx:
            last_macd = df["MACD"].loc[last_valid_macd_idx]
            axes2[1].annotate(f'MACD: {last_macd:.2f}', 
                              xy=(last_valid_macd_idx, last_macd), 
                              xytext=(10, 0), textcoords='offset points', 
                              color='blue', fontsize=10, weight='bold',
                              bbox=dict(facecolor='white', alpha=0.8))
        
        axes2[1].set_title("MACD")
        axes2[1].set_ylabel("MACD")
        axes2[1].legend()
    else:
        axes2[1].text(0.5, 0.5, "Datos insuficientes para MACD", 
                      horizontalalignment='center', verticalalignment='center', 
                      fontsize=12, color='red')
        axes2[1].set_title("MACD")
        axes2[1].set_ylabel("MACD")

    fig2.tight_layout()
    plt.setp(axes2[-1].get_xticklabels(), rotation=45)
    fig2.suptitle(f"{ticker} - Indicadores Técnicos", fontsize=16, y=1.02)

    # Mostrar ambas figuras
    plt.show()

    # Mostrar tabla de valores clave
    print("\nTabla de valores clave:")
    key_dates = df.index[::len(df)//3] if len(df) > 3 else df.index  # Mostrar ~3 fechas representativas
    table_columns = [col for col in [price_col, sma_col, ema_col, rsi_col, "MACD", "Bollinger_Upper", "Bollinger_Lower"] if col and col in df.columns]
    table_data = df.loc[key_dates, table_columns].dropna(how='all')
    print(table_data.to_string())