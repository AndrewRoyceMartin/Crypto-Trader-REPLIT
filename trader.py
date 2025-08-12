class Runner:
    def __init__(self, ex, symbol: str, timeframe: str, params: dict, io: "IO"):
        ...

    def step_once(self) -> None
    # pulls last N candles -> computes BB -> checks signals -> sizes -> places LMT+IOC -> logs

    def place(self, side: str, qty: float, px: float, taker: bool = True) -> dict

def align_to_timeframe(timeframe: str) -> float  # seconds to sleep until next bar boundary
