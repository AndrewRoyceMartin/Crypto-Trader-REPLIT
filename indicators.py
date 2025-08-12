def bollinger(close: "pd.Series", window: int = 20, k: float = 2.0) -> tuple  # (mid, up, lo)
def atr(df: "pd.DataFrame", window: int = 14) -> "pd.Series"  # optional for ATR stops/takes
