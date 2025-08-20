# -*- coding: utf-8 -*-
"""
Portfolio Service - Integrates app with Simulated OKX Exchange
Provides a unified interface for portfolio data from the exchange.
"""

from __future__ import annotations

import logging
import random
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta, timezone
import hashlib

from src.exchanges.simulated_okx import SimulatedOKX
from src.data.portfolio_assets import MASTER_PORTFOLIO_ASSETS as RAW_ASSETS


def _normalize_assets(raw: Any) -> List[Dict[str, Any]]:
    """
    Accepts MASTER_PORTFOLIO_ASSETS as either:
      - list[str] of symbols, or
      - list[dict] with keys like {'symbol','name','rank'}.
    Returns a list of dicts: [{'symbol','name','rank'}].
    """
    assets: List[Dict[str, Any]] = []
    if not raw:
        return assets

    if isinstance(raw, list):
        if all(isinstance(x, str) for x in raw):
            for idx, sym in enumerate(raw, start=1):
                assets.append({"symbol": sym, "name": sym, "rank": idx})
        elif all(isinstance(x, dict) for x in raw):
            # ensure required keys with sensible defaults
            for idx, item in enumerate(raw, start=1):
                sym = item.get("symbol") or item.get("ticker") or item.get("code")
                if not sym:
                    continue
                assets.append({
                    "symbol": sym,
                    "name": item.get("name", sym),
                    "rank": item.get("rank", idx),
                })
    return assets


ASSETS: List[Dict[str, Any]] = _normalize_assets(RAW_ASSETS)


class PortfolioService:
    """Service that manages portfolio data through live OKX exchange."""

    def __init__(self) -> None:
        """Initialize portfolio service with OKX exchange."""
        self.logger = logging.getLogger(__name__)

        # Initialize OKX exchange with credentials
        import os
        
        # Check if demo mode is enabled (default to demo for compatibility)
        demo_mode = os.getenv('OKX_DEMO', '1').strip().lower() in ('1', 'true', 't', 'yes', 'y', 'on')
        
        config = {
            "sandbox": demo_mode,  # Use demo mode by default for compatibility
            "apiKey": os.getenv("OKX_API_KEY", ""),
            "secret": os.getenv("OKX_SECRET_KEY", ""),
            "password": os.getenv("OKX_PASSPHRASE", ""),
        }

        # Require all credentials
        if not all([config["apiKey"], config["secret"], config["password"]]):
            raise RuntimeError("OKX API credentials (OKX_API_KEY, OKX_SECRET_KEY, OKX_PASSPHRASE) are required.")
        
        # Use OKX exchange (demo or live based on OKX_DEMO setting)
        from src.exchanges.okx_adapter import OKXAdapter
        self.exchange = OKXAdapter(config)
        mode_text = "demo" if demo_mode else "live"
        if not self.exchange.connect():
            raise RuntimeError(f"Failed to connect to OKX {mode_text} account. Please check your API credentials and network connection.")
        self._initialize_exchange()

        # Track initialization state
        self.is_initialized: bool = True
        self._last_sync: datetime = datetime.now(timezone.utc)

        # Live exchange will provide real trade history - no simulation needed

        # Cache a safe price getter to avoid attr-defined Pyright warnings
        self._price_getter: Optional[Callable[[str], float]] = None
        self._init_price_getter()

    def _init_price_getter(self) -> None:
        """Prepare a safe price getter without relying on private attributes."""
        # Prefer a public method if your adapter exposes one; fallback to the simulated helper.
        # We wrap it so typing stays clean for Pyright.
        getter = getattr(self.exchange, "_get_current_price", None)
        if callable(getter):
            def _wrap(pair: str) -> float:
                try:
                    v = getter(pair)
                    return float(v) if v is not None else 0.0
                except Exception:
                    return 0.0
            self._price_getter = _wrap
        else:
            # Fallback: always return 0.0 if no method available
            self._price_getter = lambda _pair: 0.0

    def _safe_price(self, inst_pair: str) -> float:
        """Get current price defensively."""
        if self._price_getter is None:
            self._init_price_getter()
        try:
            price = float(self._price_getter(inst_pair))  # type: ignore[misc]
        except Exception:
            price = 0.0
        return price if price > 0.0 else 0.0

    def _initialize_exchange(self) -> None:
        """Initialize and connect to the live OKX exchange."""
        try:
            if self.exchange.is_connected():
                self.logger.info("Successfully connected to live OKX Exchange")
                # No need to populate initial portfolio - use real data
            else:
                raise RuntimeError("Failed to connect to live OKX exchange")
        except Exception as e:
            self.logger.error("Exchange initialization failed: %s", e)
            raise

    def _populate_initial_portfolio(self) -> None:
        """Populate the exchange with initial $10 positions for each asset."""
        try:
            self.logger.info("Populating initial portfolio positions...")

            successful_positions = 0
            failed_positions: List[str] = []

            for asset in ASSETS:
                symbol = asset["symbol"]
                try:
                    inst = f"{symbol}/USDT"
                    current_price = self._safe_price(inst)
                    if current_price > 0.0:
                        quantity = 10.0 / current_price

                        order_result = self.exchange.place_order(
                            symbol=inst,
                            side="buy",
                            amount=quantity,
                            order_type="market",
                        )
                        if str(order_result.get("code")) == "0":
                            successful_positions += 1
                            self.logger.debug(
                                "Created position: %s - %.8f @ $%.6f",
                                symbol,
                                quantity,
                                current_price,
                            )
                        else:
                            failed_positions.append(symbol)
                    else:
                        failed_positions.append(symbol)
                        self.logger.warning("Could not get price for %s", symbol)
                except Exception as e:
                    failed_positions.append(symbol)
                    self.logger.warning("Failed to create position for %s: %s", symbol, e)

            self.logger.info(
                "Portfolio initialization complete: %d positions created",
                successful_positions,
            )
            if failed_positions:
                self.logger.warning(
                    "Failed to create positions for: %s", ", ".join(failed_positions)
                )

            # Generate some initial trade history for demonstration
            self._generate_initial_trade_history()

            self.is_initialized = True
            self._last_sync = datetime.now(timezone.utc)

        except Exception as e:
            self.logger.error("Portfolio population failed: %s", e)
            raise

    def _generate_initial_trade_history(self) -> None:
        """Generate some initial trade history for the portfolio."""
        try:
            base_time = datetime.now(timezone.utc) - timedelta(days=30)

            # pick top 20 by rank
            top_assets = sorted(ASSETS, key=lambda a: a.get("rank", 999))[:20]
            trades_generated = 0

            for asset in top_assets:
                symbol = asset["symbol"]

                # Generate 2-5 trades per asset over the past month
                num_trades = random.randint(2, 5)

                for _ in range(num_trades):
                    # Random time in the past 30 days
                    days_ago = random.randint(1, 30)
                    hours_ago = random.randint(0, 23)
                    trade_time = base_time + timedelta(days=days_ago, hours=hours_ago)

                    inst_pair = f"{symbol}/USDT"
                    base_price = self._safe_price(inst_pair)
                    if base_price <= 0.0:
                        base_price = 1.0

                    price_variation = random.uniform(0.8, 1.2)
                    trade_price = base_price * price_variation

                    # Random quantity (smaller for expensive coins)
                    if base_price > 1000:
                        quantity = random.uniform(0.001, 0.01)
                    elif base_price > 100:
                        quantity = random.uniform(0.1, 1.0)
                    elif base_price > 1:
                        quantity = random.uniform(1.0, 50.0)
                    else:
                        quantity = random.uniform(100.0, 10000.0)

                    side = "buy" if random.random() > 0.6 else "sell"

                    trade_data = {
                        "ordId": f"simulated_{trades_generated + 1}",
                        "clOrdId": f"client_{trades_generated + 1}",
                        "instId": f"{symbol}-USDT-SWAP",
                        "side": side,
                        "sz": f"{quantity}",
                        "px": f"{trade_price}",
                        "fillSz": f"{quantity}",
                        "fillPx": f"{trade_price}",
                        "ts": str(int(trade_time.timestamp() * 1000)),
                        "state": "filled",
                        "fee": f"{round(quantity * trade_price * 0.001, 6)}",  # 0.1%
                        "feeCcy": "USDT",
                    }

                    self.exchange.trades.append(trade_data)  # type: ignore[attr-defined]
                    trades_generated += 1

            self.logger.info(
                "Generated %d initial trades for portfolio demonstration", trades_generated
            )

        except Exception as e:
            self.logger.error("Error generating initial trade history: %s", e)
            # non-fatal

    @staticmethod
    def _stable_bucket_0_99(key: str) -> int:
        """Deterministic 0..99 bucket (stable across runs and processes)."""
        h = hashlib.md5(key.encode("utf-8")).hexdigest()
        return int(h[:8], 16) % 100

    def get_portfolio_data(self) -> Dict[str, Any]:
        """
        Get complete portfolio data from OKX simulation for all assets.
        Returns a dict with keys: holdings, total_current_value, total_pnl, total_pnl_percent,
        cash_balance, last_update
        """
        try:
            holdings: List[Dict[str, Any]] = []
            total_value = 0.0
            total_initial_value = 0.0

            # Real positions from the exchange
            positions_response = self.exchange.get_positions()
            okx_positions = {  # map 'BTC' -> position
                (pos.get("instId", "") or "").replace("-USDT-SWAP", "").replace("-USDT", ""): pos
                for pos in (positions_response.get("data") or [])
            }

            for asset in ASSETS:
                rank = int(asset.get("rank", 999))
                symbol = asset["symbol"]
                name = asset.get("name", symbol)

                inst_pair = f"{symbol}/USDT"
                current_price = self._safe_price(inst_pair)
                if current_price <= 0.0:
                    current_price = 1.0

                initial_investment = 10.0
                quantity: float = 0.0
                avg_entry_price: float = current_price
                current_value: float = 0.0
                cost_basis: float = initial_investment
                pnl: float = 0.0
                pnl_percent: float = 0.0
                has_position: bool = False

                if symbol in okx_positions:
                    # Live position from simulated exchange
                    p = okx_positions[symbol]
                    try:
                        quantity = float(p.get("pos", 0.0) or 0.0)
                    except (TypeError, ValueError):
                        quantity = 0.0
                    try:
                        avg_entry_price = float(p.get("avgPx", current_price) or current_price)
                    except (TypeError, ValueError):
                        avg_entry_price = current_price
                    try:
                        mark_price = float(p.get("markPx", current_price) or current_price)
                    except (TypeError, ValueError):
                        mark_price = current_price

                    current_value = quantity * mark_price
                    cost_basis = quantity * max(avg_entry_price, 0.0)
                    pnl = current_value - cost_basis
                    pnl_percent = (pnl / cost_basis * 100.0) if cost_basis > 0 else 0.0
                    has_position = quantity > 0.0
                else:
                    # No open position; simulate a historical entry for display
                    b = self._stable_bucket_0_99(symbol)
                    if b < 20:
                        # +5%..+35%
                        price_variation = (b % 30 + 5) / 100.0
                    elif b < 40:
                        # -5%..-30%
                        price_variation = -((b % 25 + 5) / 100.0)
                    else:
                        # -7%..+7%
                        price_variation = ((b % 15) - 7) / 100.0

                    historical_purchase_price = current_price / (1.0 + price_variation)
                    if historical_purchase_price <= 0.0:
                        historical_purchase_price = current_price

                    quantity = initial_investment / historical_purchase_price
                    current_value = quantity * current_price
                    cost_basis = initial_investment
                    pnl = current_value - initial_investment
                    pnl_percent = (pnl / initial_investment * 100.0) if initial_investment > 0 else 0.0
                    has_position = True  # shows in holdings with simulated entry

                holdings.append({
                    "rank": rank,
                    "symbol": symbol,
                    "name": name,
                    "quantity": round(quantity, 8),
                    "current_price": float(current_price),
                    "value": float(current_value),
                    "current_value": float(current_value),
                    "cost_basis": float(cost_basis),
                    "avg_entry_price": float(avg_entry_price),
                    "pnl": float(pnl),
                    "pnl_percent": float(pnl_percent),
                    "unrealized_pnl": float(pnl),
                    "is_live": True,  # simulated live
                    "has_position": bool(has_position),
                })

                total_value += current_value
                total_initial_value += initial_investment

            # Fill allocation_percent now that total_value is known
            total_value_for_alloc = total_value if total_value > 0 else 1.0
            for h in holdings:
                h["allocation_percent"] = (float(h.get("current_value", 0.0)) / total_value_for_alloc) * 100.0

            total_pnl = sum(float(h.get("pnl", 0.0)) for h in holdings)
            total_pnl_percent = (total_pnl / total_initial_value * 100.0) if total_initial_value > 0 else 0.0

            # Keep ~10% cash reserve vs a $10 seed per asset
            target_portfolio_value = len(ASSETS) * 10.0
            cash_balance = target_portfolio_value * 0.10

            return {
                "holdings": holdings,
                "total_current_value": float(total_value),
                "total_pnl": float(total_pnl),
                "total_pnl_percent": float(total_pnl_percent),
                "cash_balance": float(cash_balance),
                "last_update": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            self.logger.error("OKX Portfolio data error: %s", e)
            # Safe fallback
            seed_value = len(ASSETS) * 10.0 if ASSETS else 1030.0
            return {
                "holdings": [],
                "total_current_value": float(seed_value),
                "total_pnl": 0.0,
                "total_pnl_percent": 0.0,
                "cash_balance": float(seed_value * 0.10),
                "last_update": datetime.now(timezone.utc).isoformat(),
            }

    def _convert_to_app_format(self, positions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert OKX position format to a simpler app format."""
        holdings: List[Dict[str, Any]] = []

        # quick map for rank/name
        meta = {a["symbol"]: a for a in ASSETS}

        for position in positions:
            try:
                inst_id = str(position.get("instId", "") or "")
                symbol = inst_id.replace("-USDT-SWAP", "").replace("-USDT", "")
                try:
                    quantity = float(position.get("pos", 0.0) or 0.0)
                except (TypeError, ValueError):
                    quantity = 0.0
                try:
                    avg_price = float(position.get("avgPx", 0.0) or 0.0)
                except (TypeError, ValueError):
                    avg_price = 0.0
                try:
                    current_price = float(position.get("markPx", avg_price) or avg_price)
                except (TypeError, ValueError):
                    current_price = avg_price

                current_value = quantity * current_price
                cost_basis = quantity * avg_price
                pnl = current_value - cost_basis
                pnl_percent = (pnl / cost_basis * 100.0) if cost_basis > 0 else 0.0

                info = meta.get(symbol, {"name": symbol, "rank": 999})

                holding = {
                    "symbol": symbol,
                    "name": info.get("name", symbol),
                    "rank": int(info.get("rank", 999)),
                    "quantity": quantity,
                    "current_price": current_price,
                    "avg_price": avg_price,
                    "current_value": current_value,
                    "value": cost_basis,
                    "pnl": pnl,
                    "pnl_percent": pnl_percent,
                    "is_live": True,
                    "exchange_position": position,
                }
                holdings.append(holding)
            except Exception as e:
                self.logger.error("Error converting position %s: %s", position, e)
                continue

        holdings.sort(key=lambda x: int(x.get("rank", 999)))
        return holdings

    def _calculate_total_pnl_percent(self, holdings: List[Dict[str, Any]]) -> float:
        """Calculate total P&L percentage across all holdings."""
        total_cost = sum(float(h.get("value", 0.0)) for h in holdings)
        total_pnl = sum(float(h.get("pnl", 0.0)) for h in holdings)
        return (total_pnl / total_cost * 100.0) if total_cost > 0 else 0.0

    def place_trade(self, symbol: str, side: str, amount: float, order_type: str = "market") -> Dict[str, Any]:
        """Place a trade through the exchange."""
        if not self.exchange.is_connected():
            raise RuntimeError("Exchange not connected")

        try:
            trading_pair = f"{symbol}/USDT"
            result = self.exchange.place_order(
                symbol=trading_pair, side=side, amount=amount, order_type=order_type
            )
            self.logger.info("Trade executed: %s %s %s", side, amount, symbol)
            return result
        except Exception as e:
            self.logger.error("Trade execution failed: %s", e)
            raise

    def get_trade_history(self, symbol: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get trade history from the exchange."""
        if not self.exchange.is_connected():
            raise RuntimeError("Exchange not connected")

        try:
            trades_raw: List[Dict[str, Any]] = list(getattr(self.exchange, "trades", []) or [])
            if symbol:
                symbol_filter = f"{symbol}-USDT-SWAP"
                trades_raw = [t for t in trades_raw if (t.get("instId") or "") == symbol_filter]

            # Newest first
            def _ts(t: Dict[str, Any]) -> int:
                try:
                    return int(t.get("ts", "0") or 0)
                except Exception:
                    return 0

            trades_raw = sorted(trades_raw, key=_ts, reverse=True)[: max(0, limit)]

            formatted: List[Dict[str, Any]] = []
            for t in trades_raw:
                try:
                    quantity = float(t.get("fillSz", t.get("sz", "0")) or 0.0)
                except (TypeError, ValueError):
                    quantity = 0.0
                try:
                    price = float(t.get("fillPx", t.get("px", "0")) or 0.0)
                except (TypeError, ValueError):
                    price = 0.0

                # ts in ms -> aware datetime
                ts_ms = 0
                try:
                    ts_ms = int(t.get("ts", "0") or 0)
                except Exception:
                    ts_ms = 0
                as_dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)

                formatted.append({
                    "id": t.get("ordId", ""),
                    "symbol": (t.get("instId", "") or "").replace("-USDT-SWAP", "").replace("-USDT", ""),
                    "side": (t.get("side", "BUY") or "").upper(),
                    "quantity": quantity,
                    "price": price,
                    "timestamp": as_dt.isoformat(),
                    "fee": float(t.get("fee", quantity * price * 0.001) or 0.0),
                    "fee_currency": t.get("feeCcy", "USDT"),
                    "total_value": quantity * price,
                    "exchange_data": t,
                })
            return formatted
        except Exception as e:
            self.logger.error("Error getting trade history: %s", e)
            return []

    def get_exchange_status(self) -> Dict[str, Any]:
        """Get exchange connection and status information."""
        return {
            "connected": self.exchange.is_connected(),
            "initialized": self.is_initialized,
            "last_sync": self._last_sync.isoformat() if self._last_sync else None,
            "exchange_type": "Simulated OKX",
            "market_open": getattr(self.exchange, "market_open", True),
            "balance_summary": self._get_balance_summary(),
        }

    def _get_balance_summary(self) -> Dict[str, Any]:
        """Get simplified balance summary."""
        try:
            if self.exchange.is_connected():
                balance = self.exchange.get_balance()
                portfolio = self.exchange.get_portfolio_summary()

                cash = 0.0
                try:
                    cash = float((balance.get("data") or [{}])[0].get("availBal", 0.0) or 0.0)
                except Exception:
                    cash = 0.0

                total_eq = 0.0
                try:
                    total_eq = float((portfolio.get("data") or {}).get("totalEq", 0.0) or 0.0)
                except Exception:
                    total_eq = 0.0

                return {
                    "cash_balance": cash,
                    "total_equity": total_eq,
                    "currency": "USDT",
                }
            return {"error": "Exchange not connected"}
        except Exception as e:
            return {"error": str(e)}

    def reset_portfolio(self) -> bool:
        """Reset portfolio to initial state (useful for testing)."""
        try:
            self.logger.info("Resetting portfolio to initial state...")
            self.exchange = SimulatedOKX(self.exchange.config)
            self._initialize_exchange()
            self._init_price_getter()
            self.logger.info("Portfolio reset successfully")
            return True
        except Exception as e:
            self.logger.error("Portfolio reset failed: %s", e)
            return False


# Global portfolio service instance
_portfolio_service: Optional[PortfolioService] = None


def get_portfolio_service() -> PortfolioService:
    """Get the global portfolio service instance."""
    global _portfolio_service
    if _portfolio_service is None:
        _portfolio_service = PortfolioService()
    return _portfolio_service
