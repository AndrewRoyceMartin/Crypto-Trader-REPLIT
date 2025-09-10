# okx/trade_history.py

import requests
import pandas as pd
import time
import hmac
import hashlib
import base64
import os
from datetime import datetime
from typing import Dict, Optional

class OKXTradeHistory:
    def __init__(self):
        self.base_url = "https://www.okx.com"
        self.creds = self._load_creds()

    def _load_creds(self) -> Dict:
        return {
            "api_key": os.getenv("OKX_API_KEY", ""),
            "secret_key": os.getenv("OKX_SECRET_KEY", ""),
            "passphrase": os.getenv("OKX_PASSPHRASE", "")
        }

    def _headers(self, method: str, path: str, body: str = "") -> Dict:
        ts = datetime.utcnow().isoformat(timespec='milliseconds') + "Z"
        msg = f"{ts}{method}{path}{body}"
        sign = base64.b64encode(hmac.new(
            self.creds["secret_key"].encode("utf-8"),
            msg.encode("utf-8"),
            hashlib.sha256
        ).digest()).decode()

        return {
            "OK-ACCESS-KEY": self.creds["api_key"],
            "OK-ACCESS-SIGN": sign,
            "OK-ACCESS-TIMESTAMP": ts,
            "OK-ACCESS-PASSPHRASE": self.creds["passphrase"],
            "Content-Type": "application/json"
        }

    def get_trade_fills(self, instType: str = "SPOT", limit: int = 100) -> pd.DataFrame:
        """
        Pull recent executed trades (fills) from OKX account.
        instType: SPOT / MARGIN / SWAP / FUTURES
        """
        path = "/api/v5/trade/fills"
        url = self.base_url + path
        headers = self._headers("GET", path)
        params = {
            "instType": instType,
            "limit": limit
        }

        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        if not data.get("data"):
            print("No trade fills found.")
            return pd.DataFrame()

        records = data["data"]
        df = pd.DataFrame(records)

        # Format/clean columns
        df["price"] = df["fillPx"].astype(float)
        df["size"] = df["fillSz"].astype(float)
        df["side"] = df["side"].str.upper()
        df["timestamp"] = pd.to_datetime(df["ts"].astype(int), unit='ms')

        return df[["timestamp", "instId", "side", "price", "size", "tradeId", "ordId"]]

    def save_trades_to_csv(self, filename: str = "okx_trade_history.csv") -> None:
        """Save trade history to CSV file"""
        df = self.get_trade_fills()
        if not df.empty:
            df.to_csv(filename, index=False)
            print(f"✅ Saved {len(df)} trades to {filename}")
        else:
            print("⚠️ No trades to save.")

    def get_trade_summary(self) -> Dict:
        """Get summary statistics of recent trades"""
        df = self.get_trade_fills()
        if df.empty:
            return {"total_trades": 0}
        
        summary = {
            "total_trades": len(df),
            "buy_trades": len(df[df["side"] == "BUY"]),
            "sell_trades": len(df[df["side"] == "SELL"]),
            "unique_instruments": df["instId"].nunique(),
            "date_range": {
                "from": df["timestamp"].min().isoformat(),
                "to": df["timestamp"].max().isoformat()
            },
            "total_volume": df["size"].sum(),
            "avg_trade_size": df["size"].mean()
        }
        
        return summary