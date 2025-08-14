# main.py
from utils.data_loader import download_data
import pandas as pd

def main():
    print("=== Simulador de Tendencia Histórica + Técnica ===")
    
    # Pedir ticker y período
    ticker = input("Ingrese el ticker de la empresa (ej. AAPL, NVDA, AHCO): ").upper()
    period = input("Ingrese el período (ej. 1y, 6mo, 3mo): ")
    
    # Descargar datos
    df = download_data(ticker, period)
    
    # Mostrar primeras filas
    print("\nPrimeras filas del DataFrame:")
    print(df.head())

if __name__ == "__main__":
    main()
