def init_logger() -> None
def log_trade_csv(path: str, trade: dict) -> None
def save_state(path: str, state: dict) -> None
def load_state(path: str) -> dict
def start_healthcheck(port: int = 8000) -> None  # tiny HTTP server returning "ok" for uptime checks
def heartbeat(path: str = "heartbeat.txt") -> None
