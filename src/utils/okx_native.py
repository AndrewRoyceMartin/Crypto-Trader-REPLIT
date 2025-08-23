# src/utils/okx_native.py
from __future__ import annotations
import os, time, json, hmac, hashlib, base64, requests
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

STABLES = {"USD", "USDT", "USDC"}

def utc_iso() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

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
        tmo = timeout or self.timeout
        ts = utc_iso()
        body_str = json.dumps(body) if (body and method != "GET") else ""
        sig = self._sign(ts, method, path, body_str)
        headers = self._headers(ts, sig)
        url = self.base_url + path
        if method == "GET":
            resp = self.session.get(url, headers=headers, timeout=tmo)
        else:
            resp = self.session.post(url, headers=headers, data=body_str, timeout=tmo)
        resp.raise_for_status()
        return resp.json()

    # --- public API ---
    @classmethod
    def from_env(cls) -> "OKXNative":
        return cls(OKXCreds.from_env())

    def ticker(self, inst_id: str) -> Dict[str, float]:
        """Return last, open24h, vol24h, pct_24h with caching."""
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
            vol24h = float(t.get("vol24h") or 0)
            pct_24h = ((last - open24h) / open24h * 100) if open24h > 0 else 0.0
            ticker_data = {"last": last, "open24h": open24h, "vol24h": vol24h, "pct_24h": pct_24h}
            
            # Cache the result
            try:
                from app import cache_put_price
                cache_put_price(f"ticker_{inst_id}", ticker_data)
            except ImportError:
                pass
                
            return ticker_data
        return {"last": 0.0, "open24h": 0.0, "vol24h": 0.0, "pct_24h": 0.0}

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
        data = self._request(q)
        return data.get("data", []) if data.get("code") == "0" else []

    def bills(self, begin_ms: int, end_ms: int, limit: int = 100) -> List[Dict[str, Any]]:
        q = f"/api/v5/account/bills?begin={begin_ms}&end={end_ms}&limit={limit}"
        data = self._request(q)
        return data.get("data", []) if data.get("code") == "0" else []

    def balance(self) -> Dict[str, Any]:
        data = self._request("/api/v5/account/balance")
        return data["data"][0] if data.get("code") == "0" and data.get("data") else {}

    def price(self, inst_id: str) -> float:
        return self.ticker(inst_id).get("last", 0.0)