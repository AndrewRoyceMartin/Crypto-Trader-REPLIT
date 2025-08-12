def make_exchange(name: str) -> "ccxt.Exchange"
def set_okx_demo_headers(ex: "ccxt.Exchange", demo: bool) -> None
def load_markets_safe(ex: "ccxt.Exchange") -> None
def price_to_precision(ex: "ccxt.Exchange", symbol: str, price: float) -> float
def amount_to_precision(ex: "ccxt.Exchange", symbol: str, amount: float) -> float
def fetch_ohlcv(ex: "ccxt.Exchange", symbol: str, timeframe: str, limit: int) -> list
def create_order_limit_ioc(ex: "ccxt.Exchange", symbol: str, side: str, qty: float, price: float) -> dict
def create_order_market(ex: "ccxt.Exchange", symbol: str, side: str, qty: float) -> dict  # rarely used; we prefer LMT+IOC
def fetch_balance(ex: "ccxt.Exchange") -> dict
