# src/utils/okx_native.py
from __future__ import annotations
import os, time, json, hmac, hashlib, base64, requests
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

STABLES = {"USD", "USDT", "USDC"}

def utc_iso() -> str:
    # OKX expects ISO timestamp with 3-digit milliseconds (not 6-digit microseconds)
    dt = datetime.now(timezone.utc)
    # Get milliseconds (3 digits) instead of microseconds (6 digits)
    milliseconds = int(dt.microsecond / 1000)
    return dt.strftime('%Y-%m-%dT%H:%M:%S') + f'.{milliseconds:03d}Z'

@dataclass
class OKXCreds:
    api_key: str
    secret_key: str
    passphrase: str
    hostname: str = "www.okx.com"

    @classmethod
    def from_env(cls) -> "OKXCreds":
        # Always use production OKX hostname for live trading
        return cls(
            api_key=os.getenv("OKX_API_KEY", ""),
            secret_key=os.getenv("OKX_SECRET_KEY", ""),
            passphrase=os.getenv("OKX_PASSPHRASE", ""),
            hostname="www.okx.com",  # Force production hostname
        )

class OKXNative:
    def __init__(self, creds: OKXCreds, timeout: int = 10):
        if not (creds.api_key and creds.secret_key and creds.passphrase):
            raise RuntimeError("OKX API credentials required")
        self.creds = creds
        self.base_url = f"https://{creds.hostname}"
        self.session = requests.Session()
        self.timeout = timeout

    # --- low-level helpers ---
    def _sign(self, ts: str, method: str, path: str, body: str = "") -> str:
        msg = f"{ts}{method}{path}{body}"
        mac = hmac.new(self.creds.secret_key.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256)
        return base64.b64encode(mac.digest()).decode("utf-8")

    def _headers(self, ts: str, sig: str) -> Dict[str, str]:
        return {
            "OK-ACCESS-KEY": self.creds.api_key,
            "OK-ACCESS-SIGN": sig,
            "OK-ACCESS-TIMESTAMP": ts,
            "OK-ACCESS-PASSPHRASE": self.creds.passphrase,
            "Content-Type": "application/json",
        }

    def _request(self, path: str, method: str = "GET", body: Optional[Dict[str, Any]] = None, timeout: Optional[int] = None) -> Dict[str, Any]:
        from app import with_throttle, logger
        tmo = timeout or self.timeout
        ts = utc_iso()
        body_str = json.dumps(body) if (body and method != "GET") else ""
        sig = self._sign(ts, method, path, body_str)
        headers = self._headers(ts, sig)
        url = self.base_url + path
        
        # Debug authentication for trade/account endpoints
        if "/trade/" in path or "/account/" in path:
            logger.info(f"OKX Authentication Debug for {path}:")
            logger.info(f"  Timestamp: {ts}")
            logger.info(f"  Method: {method}")
            logger.info(f"  Path: {path}")
            logger.info(f"  Body: '{body_str}'")
            logger.info(f"  Signature Input: '{ts}{method}{path}{body_str}'")
            logger.info(f"  API Key: {self.creds.api_key[:8]}...")
            logger.info(f"  Passphrase: {self.creds.passphrase}")
            logger.info(f"  Headers: {headers}")
        
        if method == "GET":
            resp = with_throttle(self.session.get, url, headers=headers, timeout=tmo)
        else:
            resp = with_throttle(self.session.post, url, headers=headers, data=body_str, timeout=tmo)
        resp.raise_for_status()
        return resp.json()

    # --- public API ---
    @classmethod
    def from_env(cls) -> "OKXNative":
        return cls(OKXCreds.from_env())

    def ticker(self, inst_id: str) -> Dict[str, float]:
        """Return comprehensive ticker data with caching."""
        try:
            # Try cache first
            from app import cache_get_price, cache_put_price
            cached_ticker = cache_get_price(f"ticker_{inst_id}")
            if cached_ticker is not None:
                return cached_ticker
        except ImportError:
            pass
            
        data = self._request(f"/api/v5/market/ticker?instId={inst_id}")
        if data.get("code") == "0" and data.get("data"):
            t = data["data"][0]
            last = float(t.get("last") or 0)
            open24h = float(t.get("open24h") or 0)
            high24h = float(t.get("high24h") or 0)
            low24h = float(t.get("low24h") or 0)
            vol24h = float(t.get("vol24h") or 0)
            bidPx = float(t.get("bidPx") or 0)
            askPx = float(t.get("askPx") or 0)
            pct_24h = ((last - open24h) / open24h * 100) if open24h > 0 else 0.0
            
            ticker_data = {
                "last": last, 
                "open24h": open24h, 
                "high24h": high24h,
                "low24h": low24h,
                "vol24h": vol24h, 
                "bidPx": bidPx,
                "askPx": askPx,
                "pct_24h": pct_24h
            }
            
            # Cache the result
            try:
                from app import cache_put_price
                cache_put_price(f"ticker_{inst_id}", ticker_data)
            except ImportError:
                pass
                
            return ticker_data
        return {"last": 0.0, "open24h": 0.0, "high24h": 0.0, "low24h": 0.0, "vol24h": 0.0, "bidPx": 0.0, "askPx": 0.0, "pct_24h": 0.0}

    def candles(self, inst_id: str, bar: str = "1D", limit: int = 7, before_ms: Optional[int] = None) -> List[List[str]]:
        path = f"/api/v5/market/candles?instId={inst_id}&bar={bar}&limit={limit}"
        if before_ms:
            path += f"&before={before_ms}"
        data = self._request(path)
        return data.get("data", []) if data.get("code") == "0" else []

    def fills(self, begin_ms: Optional[int] = None, end_ms: Optional[int] = None, limit: int = 100) -> List[Dict[str, Any]]:
        q = f"/api/v5/trade/fills?limit={limit}"
        if begin_ms: q += f"&begin={begin_ms}"
        if end_ms:   q += f"&end={end_ms}"
        try:
            data = self._request(q)
            if data.get("code") == "0":
                from app import logger
                logger.info(f"OKX fills API success: Retrieved {len(data.get('data', []))} fills")
                return data.get("data", [])
            else:
                # Log the error details for debugging
                from app import logger
                logger.error(f"OKX fills API error: {data.get('msg', 'Unknown error')} (code: {data.get('code', 'N/A')})")
                return []
        except Exception as e:
            from app import logger
            logger.error(f"OKX fills API request failed: {e}")
            return []

    def bills(self, begin_ms: int, end_ms: int, limit: int = 100) -> List[Dict[str, Any]]:
        q = f"/api/v5/account/bills?begin={begin_ms}&end={end_ms}&limit={limit}"
        data = self._request(q)
        return data.get("data", []) if data.get("code") == "0" else []

    def balance(self) -> Dict[str, Any]:
        """Return enhanced balance data with totalEq and detailed currency info."""
        data = self._request("/api/v5/account/balance")
        if data.get("code") == "0" and data.get("data"):
            balance_data = data["data"][0]
            # Extract totalEq from top level for portfolio total value
            total_eq = float(balance_data.get("totalEq") or 0)
            
            # Process details array to include eq field for each currency
            details = balance_data.get("details", [])
            enhanced_details = []
            for detail in details:
                enhanced_detail = {
                    "ccy": detail.get("ccy", ""),
                    "bal": detail.get("bal", "0"),
                    "availBal": detail.get("availBal", "0"),
                    "eq": float(detail.get("eq") or 0),  # Individual currency equity
                    "eqUsd": float(detail.get("eqUsd") or 0),  # USD equivalent
                }
                enhanced_details.append(enhanced_detail)
            
            return {
                "totalEq": total_eq,
                "details": enhanced_details,
                # Preserve original structure for compatibility
                **balance_data
            }
        return {"totalEq": 0.0, "details": []}

    def price(self, inst_id: str) -> float:
        return self.ticker(inst_id).get("last", 0.0)

    def place_order(self, inst_id: str, side: str, ord_type: str, sz: str, px: Optional[str] = None) -> Dict[str, Any]:
        """Place an order on OKX.
        
        Args:
            inst_id: Trading pair (e.g., BTC-USDT)
            side: 'buy' or 'sell'
            ord_type: 'market' or 'limit'
            sz: Order size (for market buy: amount in quote currency, for market sell: amount in base currency)
            px: Price (only for limit orders)
        
        Returns:
            OKX API response
        """
        body = {
            "instId": inst_id,
            "tdMode": "cash",  # Cash trading mode (spot)
            "side": side.lower(),
            "ordType": ord_type.lower(),
            "sz": str(sz)
        }
        
        if ord_type.lower() == "limit" and px:
            body["px"] = str(px)
        
        return self._request("/api/v5/trade/order", "POST", body)

    def get_order(self, inst_id: str, ord_id: str) -> Dict[str, Any]:
        """Get order details by order ID."""
        return self._request(f"/api/v5/trade/order?instId={inst_id}&ordId={ord_id}", "GET")