def entry_signal(px: float, bb_lo: float) -> bool                      # buy when px <= lower band
def exit_signal(px: float, bb_up: float, entry: float, tp: float, sl: float, low: float) -> bool
def position_size_risk(equity: float, price: float, stop_loss_pct: float, risk_pct: float) -> float
