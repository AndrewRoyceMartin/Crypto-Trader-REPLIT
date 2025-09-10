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

    def get_all_trade_fills(self, instType: str = "SPOT", max_pages: int = 20, delay_sec: float = 0.3) -> pd.DataFrame:
        """
        Pull full trade history using pagination.
        OKX limit = 100 trades per request.
        """
        path = "/api/v5/trade/fills"
        url = self.base_url + path
        headers = self._headers("GET", path)

        all_records = []
        before_id = None
        page = 0

        print(f"🔄 Fetching historical {instType} trades (max {max_pages} pages)...")

        while page < max_pages:
            params = {
                "instType": instType,
                "limit": 100
            }
            if before_id:
                params["before"] = before_id

            try:
                response = requests.get(url, headers=headers, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                if not data.get("data") or len(data["data"]) == 0:
                    print(f"   📋 Page {page + 1}: No more data - stopping pagination")
                    break

                records = data["data"]
                all_records.extend(records)
                
                print(f"   📋 Page {page + 1}: Fetched {len(records)} trades (total: {len(all_records)})")

                last_trade_id = records[-1].get("tradeId")
                if not last_trade_id:
                    print(f"   ⚠️ No tradeId found - stopping pagination")
                    break

                before_id = last_trade_id
                page += 1
                
                if page < max_pages:  # Don't delay after the last request
                    time.sleep(delay_sec)  # Rate limit protection
                    
            except Exception as e:
                print(f"   ❌ Error on page {page + 1}: {e}")
                break

        if not all_records:
            print(f"⚠️ No historical {instType} trade data found.")
            return pd.DataFrame()

        print(f"✅ Total {instType} trades retrieved: {len(all_records)}")
        
        df = pd.DataFrame(all_records)

        # Format columns with enhanced data
        df["price"] = df["fillPx"].astype(float)
        df["size"] = df["fillSz"].astype(float)
        df["value_usd"] = df["price"] * df["size"]  # Calculate trade value
        df["timestamp"] = pd.to_datetime(df["ts"].astype(int), unit="ms")
        df["side"] = df["side"].str.upper()
        df["fee"] = df["fee"].astype(float)
        df["feeCcy"] = df["feeCcy"]
        
        # Sort by timestamp (newest first)
        df = df.sort_values("timestamp", ascending=False)

        selected_df = df[["timestamp", "instId", "side", "price", "size", "value_usd", "fee", "feeCcy", "tradeId", "ordId"]]
        return selected_df

    def save_all_trades_to_csv(self, filename: str = "okx_trade_history_full.csv", **kwargs) -> None:
        """Save complete trade history to CSV file using pagination"""
        df = self.get_all_trade_fills(**kwargs)
        if not df.empty:
            df.to_csv(filename, index=False)
            print(f"✅ Saved {len(df)} historical trades to {filename}")
        else:
            print("⚠️ No historical trades to save.")

    def get_comprehensive_historical_trades(self, max_pages: int = 10) -> pd.DataFrame:
        """
        Get comprehensive historical trade data across all instrument types using pagination.
        
        Args:
            max_pages: Maximum pages per instrument type (100 trades per page)
        """
        all_trades = []
        instrument_types = ["SPOT", "MARGIN", "SWAP", "FUTURES"]
        
        print(f"🔍 Fetching comprehensive historical trades ({max_pages} pages max per type)...")
        
        for inst_type in instrument_types:
            print(f"\n📊 Processing {inst_type} trades:")
            df = self.get_all_trade_fills(inst_type, max_pages=max_pages, delay_sec=0.3)
            if not df.empty:
                df["inst_type"] = inst_type
                all_trades.append(df)
                print(f"   ✅ {inst_type}: {len(df)} trades added")
            else:
                print(f"   ⚪ {inst_type}: No trades found")
        
        if all_trades:
            combined_df = pd.concat(all_trades, ignore_index=True)
            combined_df = combined_df.sort_values("timestamp", ascending=False)
            print(f"\n🎯 Total historical trades: {len(combined_df)}")
            return combined_df
        else:
            print("\n⚠️ No historical trades found across all instrument types")
            return pd.DataFrame()

    def get_historical_trade_summary(self, max_pages: int = 10) -> Dict:
        """Get comprehensive summary of historical trades with pagination"""
        df = self.get_comprehensive_historical_trades(max_pages)
        
        if df.empty:
            return {
                "total_trades": 0,
                "message": "No historical trades found"
            }
        
        # Enhanced analytics with historical data
        summary = {
            "total_historical_trades": len(df),
            "buy_trades": len(df[df["side"] == "BUY"]),
            "sell_trades": len(df[df["side"] == "SELL"]),
            "unique_instruments": df["instId"].nunique(),
            "instrument_breakdown": df.groupby("inst_type").size().to_dict(),
            "date_range": {
                "earliest_trade": df["timestamp"].min().isoformat(),
                "latest_trade": df["timestamp"].max().isoformat(),
                "trading_days": (df["timestamp"].max() - df["timestamp"].min()).days
            },
            "volume_analysis": {
                "total_volume_usd": df["value_usd"].sum(),
                "avg_trade_size_usd": df["value_usd"].mean(),
                "largest_trade_usd": df["value_usd"].max(),
                "smallest_trade_usd": df["value_usd"].min()
            },
            "fee_analysis": {
                "total_fees": df["fee"].sum(),
                "avg_fee_per_trade": df["fee"].mean(),
                "fee_as_percent_of_volume": (df["fee"].sum() / df["value_usd"].sum()) * 100 if df["value_usd"].sum() > 0 else 0
            },
            "most_traded_pairs": df["instId"].value_counts().head(10).to_dict(),
            "trading_frequency": {
                "trades_per_day": len(df) / max(1, (df["timestamp"].max() - df["timestamp"].min()).days),
                "most_active_day": df["timestamp"].dt.date.value_counts().head(1).to_dict()
            }
        }
        
        return summary

    def analyze_historical_performance(self, max_pages: int = 10) -> Dict:
        """
        Comprehensive historical trading performance analysis.
        This provides audit-proof analysis of all historical trades.
        """
        df = self.get_comprehensive_historical_trades(max_pages)
        
        if df.empty:
            return {"error": "No historical trades found for analysis"}
        
        # Calculate trading patterns by pair
        pair_analysis = {}
        for pair in df["instId"].unique():
            pair_trades = df[df["instId"] == pair].copy()
            buys = pair_trades[pair_trades["side"] == "BUY"]
            sells = pair_trades[pair_trades["side"] == "SELL"]
            
            pair_analysis[pair] = {
                "total_trades": len(pair_trades),
                "buy_count": len(buys),
                "sell_count": len(sells),
                "total_volume": pair_trades["value_usd"].sum(),
                "avg_buy_price": buys["price"].mean() if len(buys) > 0 else 0,
                "avg_sell_price": sells["price"].mean() if len(sells) > 0 else 0
            }
        
        analysis = {
            "analysis_period": {
                "from": df["timestamp"].min().isoformat(),
                "to": df["timestamp"].max().isoformat(),
                "total_days": (df["timestamp"].max() - df["timestamp"].min()).days
            },
            "trading_overview": {
                "total_trades": len(df),
                "trading_frequency_per_day": len(df) / max(1, (df["timestamp"].max() - df["timestamp"].min()).days),
                "instruments_traded": df["instId"].nunique(),
                "instrument_types": df["inst_type"].unique().tolist()
            },
            "volume_metrics": {
                "total_volume_usd": df["value_usd"].sum(),
                "avg_trade_size": df["value_usd"].mean(),
                "median_trade_size": df["value_usd"].median(),
                "largest_trade": df["value_usd"].max(),
                "volume_by_type": df.groupby("inst_type")["value_usd"].sum().to_dict()
            },
            "trading_patterns": {
                "buy_sell_ratio": len(df[df["side"] == "BUY"]) / len(df[df["side"] == "SELL"]) if len(df[df["side"] == "SELL"]) > 0 else float('inf'),
                "most_active_pairs": df["instId"].value_counts().head(5).to_dict(),
                "trading_hours": df["timestamp"].dt.hour.value_counts().head(5).to_dict()
            },
            "cost_analysis": {
                "total_fees_paid": df["fee"].sum(),
                "avg_fee_per_trade": df["fee"].mean(),
                "fee_percentage_of_volume": (df["fee"].sum() / df["value_usd"].sum()) * 100 if df["value_usd"].sum() > 0 else 0,
                "fees_by_currency": df.groupby("feeCcy")["fee"].sum().to_dict()
            },
            "pair_breakdown": pair_analysis
        }
        
        return analysis

    # Legacy methods for backward compatibility
    def get_trade_fills(self, instType: str = "SPOT", limit: int = 100, 
                       begin: Optional[str] = None, end: Optional[str] = None) -> pd.DataFrame:
        """Legacy method - use get_all_trade_fills() for complete history"""
        full_df = self.get_all_trade_fills(instType, max_pages=1)
        return full_df.head(limit) if not full_df.empty else full_df

    def save_trades_to_csv(self, filename: str = "okx_trade_history.csv") -> None:
        """Legacy method - use save_all_trades_to_csv() for complete history"""
        self.save_all_trades_to_csv(filename, max_pages=1)