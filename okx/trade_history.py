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

    def get_trade_fills(self, instType: str = "SPOT", limit: int = 100, 
                       begin: Optional[str] = None, end: Optional[str] = None) -> pd.DataFrame:
        """
        Pull executed trades (fills) from OKX account.
        
        Args:
            instType: SPOT / MARGIN / SWAP / FUTURES
            limit: Number of trades to retrieve (max 100)
            begin: Start timestamp (milliseconds) - optional
            end: End timestamp (milliseconds) - optional
        """
        path = "/api/v5/trade/fills"
        url = self.base_url + path
        headers = self._headers("GET", path)
        params = {
            "instType": instType,
            "limit": limit
        }
        
        # Add date range if specified
        if begin:
            params["begin"] = begin
        if end:
            params["end"] = end

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data.get("data") or len(data["data"]) == 0:
                print(f"No trade fills found for {instType}")
                return pd.DataFrame()

            records = data["data"]
            df = pd.DataFrame(records)

            # Format/clean columns with proper data types
            df["price"] = df["fillPx"].astype(float)
            df["size"] = df["fillSz"].astype(float)
            df["value_usd"] = df["price"] * df["size"]  # Calculate trade value
            df["side"] = df["side"].str.upper()
            df["timestamp"] = pd.to_datetime(df["ts"].astype(int), unit='ms')
            df["fee"] = df["fee"].astype(float)
            df["feeCcy"] = df["feeCcy"]
            
            # Sort by timestamp (newest first)
            df = df.sort_values("timestamp", ascending=False)

            return df[["timestamp", "instId", "side", "price", "size", "value_usd", "fee", "feeCcy", "tradeId", "ordId"]]
            
        except Exception as e:
            print(f"Error fetching trade fills: {e}")
            return pd.DataFrame()

    def save_trades_to_csv(self, filename: str = "okx_trade_history.csv") -> None:
        """Save trade history to CSV file"""
        df = self.get_trade_fills()
        if not df.empty:
            df.to_csv(filename, index=False)
            print(f"✅ Saved {len(df)} trades to {filename}")
        else:
            print("⚠️ No trades to save.")

    def get_comprehensive_trades(self, days_back: int = 30) -> pd.DataFrame:
        """
        Get comprehensive trade history across all instrument types.
        
        Args:
            days_back: Number of days to look back for trades
        """
        from datetime import datetime, timedelta
        
        # Calculate timestamp range (OKX uses milliseconds)
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days_back)
        begin_ms = str(int(start_time.timestamp() * 1000))
        end_ms = str(int(end_time.timestamp() * 1000))
        
        all_trades = []
        instrument_types = ["SPOT", "MARGIN", "SWAP", "FUTURES"]
        
        print(f"🔍 Searching for trades in the last {days_back} days...")
        
        for inst_type in instrument_types:
            print(f"   Checking {inst_type}...")
            df = self.get_trade_fills(inst_type, limit=100, begin=begin_ms, end=end_ms)
            if not df.empty:
                df["inst_type"] = inst_type
                all_trades.append(df)
                print(f"   ✅ Found {len(df)} {inst_type} trades")
            else:
                print(f"   ⚪ No {inst_type} trades")
        
        if all_trades:
            combined_df = pd.concat(all_trades, ignore_index=True)
            return combined_df.sort_values("timestamp", ascending=False)
        else:
            return pd.DataFrame()

    def get_trade_summary(self, days_back: int = 30) -> Dict:
        """Get comprehensive summary statistics of trades"""
        df = self.get_comprehensive_trades(days_back)
        
        if df.empty:
            return {
                "total_trades": 0,
                "message": f"No trades found in the last {days_back} days"
            }
        
        # Calculate P&L for pairs
        pnl_by_pair = {}
        for pair in df["instId"].unique():
            pair_trades = df[df["instId"] == pair].copy()
            if len(pair_trades) >= 2:  # Need at least buy and sell
                # Calculate basic P&L (simplified)
                buys = pair_trades[pair_trades["side"] == "BUY"]
                sells = pair_trades[pair_trades["side"] == "SELL"]
                
                if not buys.empty and not sells.empty:
                    avg_buy_price = (buys["price"] * buys["size"]).sum() / buys["size"].sum()
                    avg_sell_price = (sells["price"] * sells["size"]).sum() / sells["size"].sum()
                    pnl_by_pair[pair] = {
                        "avg_buy": avg_buy_price,
                        "avg_sell": avg_sell_price,
                        "pnl_percent": ((avg_sell_price - avg_buy_price) / avg_buy_price) * 100
                    }
        
        summary = {
            "total_trades": len(df),
            "buy_trades": len(df[df["side"] == "BUY"]),
            "sell_trades": len(df[df["side"] == "SELL"]),
            "unique_instruments": df["instId"].nunique(),
            "instrument_types": df.groupby("inst_type").size().to_dict(),
            "date_range": {
                "from": df["timestamp"].min().isoformat(),
                "to": df["timestamp"].max().isoformat()
            },
            "total_volume_usd": df["value_usd"].sum(),
            "avg_trade_size_usd": df["value_usd"].mean(),
            "total_fees": df["fee"].sum(),
            "most_traded_pairs": df["instId"].value_counts().head(5).to_dict(),
            "estimated_pnl": pnl_by_pair
        }
        
        return summary

    def analyze_trading_performance(self, days_back: int = 30) -> Dict:
        """
        Analyze trading performance with detailed metrics.
        This is the audit-proof alternative to signal logging.
        """
        df = self.get_comprehensive_trades(days_back)
        
        if df.empty:
            return {"error": f"No trades found in the last {days_back} days for analysis"}
        
        analysis = {
            "period": f"Last {days_back} days",
            "total_trades": len(df),
            "trading_frequency": len(df) / days_back,
            "instruments_traded": df["instId"].nunique(),
            "most_active_pairs": df["instId"].value_counts().head(3).to_dict(),
            "trading_patterns": {
                "buy_ratio": len(df[df["side"] == "BUY"]) / len(df),
                "sell_ratio": len(df[df["side"] == "SELL"]) / len(df),
                "avg_trade_size": df["value_usd"].mean(),
                "largest_trade": df["value_usd"].max(),
                "smallest_trade": df["value_usd"].min()
            },
            "fees_analysis": {
                "total_fees": df["fee"].sum(),
                "avg_fee_per_trade": df["fee"].mean(),
                "fee_as_percent_of_volume": (df["fee"].sum() / df["value_usd"].sum()) * 100
            }
        }
        
        return analysis