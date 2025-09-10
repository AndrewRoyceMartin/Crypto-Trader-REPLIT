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
    Adds continuous P&L percentage target for regression instead of binary classification.
    Returns actual P&L% that can be predicted by regression model.
    """
    df = df.copy()
    df["future_price"] = df["current_price"].shift(-horizon)
    df["pnl_pct"] = (df["future_price"] - df["current_price"]) / df["current_price"] * 100
    
    # Keep legacy binary label for compatibility (but use pnl_pct as main target)
    df["profitable"] = (df["pnl_pct"] > 1.0).astype(int)  # > +1%
    
    return df.dropna()