def backtest_bbands(df: "pd.DataFrame", params: dict) -> dict
# returns: {"metrics": {...}, "equity": pd.DataFrame, "trades": list}

def walk_forward_optimize(df: "pd.DataFrame",
                          param_grid: dict,
                          train_bars: int,
                          test_bars: int) -> dict  # optional (later)
