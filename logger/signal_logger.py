# logger/signal_logger.py

import csv
import os
from datetime import datetime

CSV_FILE = "signals_log.csv"
CSV_HEADERS = [
    "timestamp", "symbol", "current_price", "confidence_score",
    "timing_signal", "rsi", "volatility", "volume_ratio",
    "momentum_signal", "support_signal", "bollinger_signal"
]

def log_signal(symbol: str, current_price: float, confidence_data: dict):
    """
    Log signal prediction to CSV file (append if exists).
    """
    timestamp = datetime.utcnow().isoformat()

    indicators = confidence_data.get("indicators", {})

    row = {
        "timestamp": timestamp,
        "symbol": symbol,
        "current_price": current_price,
        "confidence_score": confidence_data.get("confidence_score"),
        "timing_signal": confidence_data.get("timing_signal"),
        "rsi": indicators.get("rsi"),
        "volatility": indicators.get("volatility"),
        "volume_ratio": indicators.get("volume_signal"),  # True/False
        "momentum_signal": indicators.get("momentum_signal"),
        "support_signal": indicators.get("support_signal"),
        "bollinger_signal": indicators.get("bollinger_signal"),
    }

    file_exists = os.path.isfile(CSV_FILE)

    with open(CSV_FILE, mode="a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)