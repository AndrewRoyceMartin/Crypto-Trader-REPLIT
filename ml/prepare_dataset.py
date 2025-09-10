# ml/prepare_dataset.py

import pandas as pd

def load_signal_data(path="signals_log.csv") -> pd.DataFrame:
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")

    # drop incomplete
    df = df.dropna(subset=["confidence_score", "current_price", "rsi", "volatility"])
    return df

def label_profitability(df: pd.DataFrame, horizon: int = 3) -> pd.DataFrame:
    """
    Adds a binary label: 1 if price increased in next N rows, else 0
    """
    df = df.copy()
    df["future_price"] = df["current_price"].shift(-horizon)
    df["price_change_pct"] = (df["future_price"] - df["current_price"]) / df["current_price"] * 100
    df["profitable"] = (df["price_change_pct"] > 1.0).astype(int)  # > +1%
    return df.dropna()