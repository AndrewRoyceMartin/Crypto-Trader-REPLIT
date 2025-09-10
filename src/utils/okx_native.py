# src/utils/okx_native.py
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import random
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import requests

STABLES = {"USD", "USDT", "USDC"}

def utc_iso() -> str:
    # OKX requires ISO 8601 timestamps with only 3-digit milliseconds
    now = datetime.now(UTC)
    # Format with 3-digit milliseconds
    return now.strftime('%Y-%m-%dT%H:%M:%S.') + f"{int(now.microsecond / 1000):03d}Z"

@dataclass
class OKXCreds:
    api_key: str
    secret_key: str
    passphrase: str
    hostname: str = "www.okx.com"

    @classmethod
    def from_env(cls) -> OKXCreds:
        # Always use production OKX hostname for live trading
        return cls(
            api_key=os.getenv("OKX_API_KEY", ""),
            secret_key=os.getenv("OKX_SECRET_KEY", ""),
            passphrase=os.getenv("OKX_PASSPHRASE", ""),
            hostname="www.okx.com",  # Force production hostname
        )

class OKXNative:
    # Class-level rate limiting
    _rate_limiter = threading.Lock()
    _last_request_time = 0
    _min_request_interval = 0.2  # 200ms between requests (5 req/sec max)

    def __init__(self, creds: OKXCreds, timeout: int = 10):
        if not (creds.api_key and creds.secret_key and creds.passphrase):
            raise RuntimeError("OKX API credentials required")
        self.creds = creds
        self.base_url = f"https://{creds.hostname}"
        self.session = requests.Session()
        self.timeout = timeout
        self.request_stats = {
            "total_requests": 0,
            "failed_401": 0,
            "rate_limited": 0,
            "retries_used": 0
        }

    # --- low-level helpers ---
    def _sign(self, ts: str, method: str, path: str, body: str = "") -> str:
        msg = f"{ts}{method}{path}{body}"
        mac = hmac.new(self.creds.secret_key.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256)
        return base64.b64encode(mac.digest()).decode("utf-8")

    def _headers(self, ts: str, sig: str) -> dict[str, str]:
        return {
            "OK-ACCESS-KEY": self.creds.api_key,
            "OK-ACCESS-SIGN": sig,
            "OK-ACCESS-TIMESTAMP": ts,
            "OK-ACCESS-PASSPHRASE": self.creds.passphrase,
            "Content-Type": "application/json",
        }

    def _rate_limit(self):
        """Apply rate limiting to avoid hitting OKX throttle caps."""
        with self._rate_limiter:
            current_time = time.time()
            time_since_last = current_time - self._last_request_time
            if time_since_last < self._min_request_interval:
                sleep_time = self._min_request_interval - time_since_last
                time.sleep(sleep_time)
            self._last_request_time = time.time()

    def _request_with_retry(self, path: str, method: str = "GET", body: dict[str, Any] | None = None, timeout: int | None = None, max_retries: int = 3) -> dict[str, Any]:
        """Make request with exponential backoff retry logic for transient 401s."""
        from app import logger, with_throttle

        self.request_stats["total_requests"] += 1
        tmo = timeout or self.timeout

        for attempt in range(max_retries + 1):
            try:
                # Apply rate limiting
                self._rate_limit()

                # Generate fresh timestamp for each attempt
                ts = utc_iso()
                body_str = json.dumps(body) if (body and method != "GET") else ""
                sig = self._sign(ts, method, path, body_str)
                headers = self._headers(ts, sig)
                url = self.base_url + path

                # Debug authentication for trade/account endpoints on first attempt
                if attempt == 0 and ("/trade/" in path or "/account/" in path):
                    logger.info(f"OKX API Request [{attempt + 1}/{max_retries + 1}] for {path}:")
                    logger.info(f"  Timestamp: {ts}")
                    logger.info(f"  Method: {method}")
                    logger.info(f"  Signature Input: '{ts}{method}{path}{body_str}'")

                if method == "GET":
                    resp = with_throttle(self.session.get, url, headers=headers, timeout=tmo)
                else:
                    resp = with_throttle(self.session.post, url, headers=headers, data=body_str, timeout=tmo)

                resp.raise_for_status()

                # Log success after retries
                if attempt > 0:
                    logger.info(f"✅ OKX API success on attempt {attempt + 1} for {path}")

                return resp.json()

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    self.request_stats["failed_401"] += 1

                    # Log 401 patterns for analysis
                    logger.warning(f"🔐 401 Unauthorized attempt {attempt + 1}/{max_retries + 1} for {path}")
                    logger.warning(f"   Request stats: {self.request_stats}")

                    if attempt < max_retries:
                        # Exponential backoff: 1s, 2s, 4s
                        backoff_time = (2 ** attempt) + random.uniform(0, 1)
                        logger.info(f"⏳ Retrying in {backoff_time:.1f}s (exponential backoff)")
                        time.sleep(backoff_time)
                        self.request_stats["retries_used"] += 1
                        continue
                    else:
                        logger.error(f"❌ All {max_retries + 1} attempts failed with 401 for {path}")
                        raise

                elif "busy" in str(e).lower() or "too many" in str(e).lower():
                    self.request_stats["rate_limited"] += 1
                    logger.warning(f"⚠️ Rate limit hit on attempt {attempt + 1} for {path}")

                    if attempt < max_retries:
                        # Longer backoff for rate limiting: 5s, 10s, 20s
                        backoff_time = 5 * (2 ** attempt) + random.uniform(0, 2)
                        logger.info(f"⏳ Rate limit backoff: {backoff_time:.1f}s")
                        time.sleep(backoff_time)
                        self.request_stats["retries_used"] += 1
                        continue
                    else:
                        raise
                else:
                    # Other HTTP errors, don't retry
                    logger.error(f"❌ HTTP {e.response.status_code} error for {path}: {e}")
                    raise

            except Exception as e:
                # Network/timeout errors
                if attempt < max_retries:
                    backoff_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"🌐 Network error attempt {attempt + 1}, retrying in {backoff_time:.1f}s: {e}")
                    time.sleep(backoff_time)
                    self.request_stats["retries_used"] += 1
                    continue
                else:
                    logger.error(f"❌ Network error after {max_retries + 1} attempts for {path}: {e}")
                    raise

        # This should never be reached
        raise RuntimeError(f"Unexpected end of retry loop for {path}")

    def _request(self, path: str, method: str = "GET", body: dict[str, Any] | None = None, timeout: int | None = None) -> dict[str, Any]:
        """Legacy wrapper for backward compatibility."""
        return self._request_with_retry(path, method, body, timeout)

    # --- public API ---
    @classmethod
    def from_env(cls) -> OKXNative:
        return cls(OKXCreds.from_env())

    def ticker(self, inst_id: str) -> dict[str, float]:
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

    def candles(self, inst_id: str, bar: str = "1D", limit: int = 7, before_ms: int | None = None) -> list[list[str]]:
        path = f"/api/v5/market/candles?instId={inst_id}&bar={bar}&limit={limit}"
        if before_ms:
            path += f"&before={before_ms}"
        data = self._request(path)
        return data.get("data", []) if data.get("code") == "0" else []

    def fills(self, begin_ms: int | None = None, end_ms: int | None = None, limit: int = 100) -> list[dict[str, Any]]:
        q = f"/api/v5/trade/fills?limit={limit}"
        if begin_ms: q += f"&begin={begin_ms}"
        if end_ms:   q += f"&end={end_ms}"
        try:
            # Use retry logic for fills endpoint
            data = self._request_with_retry(q, max_retries=3)
            if data.get("code") == "0":
                from app import logger
                fills_count = len(data.get('data', []))
                logger.info(f"✅ OKX fills API success: Retrieved {fills_count} fills (stats: {self.request_stats})")
                return data.get("data", [])
            else:
                # Log the error details for debugging
                from app import logger
                logger.error(f"❌ OKX fills API error: {data.get('msg', 'Unknown error')} (code: {data.get('code', 'N/A')})")
                return []
        except Exception as e:
            from app import logger
            logger.error(f"❌ OKX fills API request failed after retries: {e} (stats: {self.request_stats})")
            return []

    def get_request_stats(self) -> dict[str, Any]:
        """Get request statistics for monitoring."""
        return {
            **self.request_stats,
            "success_rate": (self.request_stats["total_requests"] - self.request_stats["failed_401"] - self.request_stats["rate_limited"]) / max(1, self.request_stats["total_requests"]) * 100
        }

    def bills(self, begin_ms: int, end_ms: int, limit: int = 100) -> list[dict[str, Any]]:
        q = f"/api/v5/account/bills?begin={begin_ms}&end={end_ms}&limit={limit}"
        data = self._request(q)
        return data.get("data", []) if data.get("code") == "0" else []

    def balance(self) -> dict[str, Any]:
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

    def place_order(self, inst_id: str, side: str, ord_type: str, sz: str, px: str | None = None) -> dict[str, Any]:
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

    def get_order(self, inst_id: str, ord_id: str) -> dict[str, Any]:
        """Get order details by order ID."""
        return self._request(f"/api/v5/trade/order?instId={inst_id}&ordId={ord_id}", "GET")
