def within_daily_loss_cap(equity: float, peak_equity: float, cap_pct: float) -> bool
def notional_ok(symbol_info: dict, price: float, qty: float, min_notional: float) -> bool
def slippage_model(price: float, slip_pct: float, side: str) -> float
def fee_model(entry: float, exit: float, qty: float, fee_rate: float) -> float
