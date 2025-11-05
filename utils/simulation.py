from utils.backtest import simulate_signals, simulate_signals_v2

def run_basic_simulation(df):
    return simulate_signals(df)

def run_advanced_simulation(df):
    return simulate_signals_v2(df)
