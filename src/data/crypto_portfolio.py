# -*- coding: utf-8 -*-
"""
Cryptocurrency Portfolio Management System
Lightweight, self-contained portfolio manager (no external price APIs).
- Seeds a fixed $10 allocation per asset
- Maintains quantities and recalculates values from current prices
- Pyright/pandas-friendly (no pandas/numpy)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class CryptoPortfolioManager:
    """Manages a portfolio of cryptocurrencies with a fixed $ allocation per asset."""

    def __init__(
        self,
        initial_value_per_crypto: float = 10.0,
        assets: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """
        Args:
            initial_value_per_crypto: starting USD value for each cryptocurrency
            assets: optional list of dicts [{'symbol','name','rank'}]; if None, a small default set is used
        """
        self.logger = logging.getLogger(__name__)
        self.initial_value: float = float(initial_value_per_crypto)

        # Asset universe (symbol/name/rank)
        self.crypto_list: List[Dict[str, Any]] = (
            assets if assets is not None else self._default_assets()
        )

        # Core state
        self.portfolio_data: Dict[str, Dict[str, Any]] = {}
        self.price_history: Dict[str, List[Dict[str, Any]]] = {}
        self.cash_balance: float = 0.0  # available cash outside positions

        # Seed portfolio at $10 per asset
        self._seed_portfolio()
        self.logger.info(
            "Initialized lightweight portfolio manager with %d assets at $%.2f each",
            len(self.crypto_list),
            self.initial_value,
        )

    # -------------------------
    # Setup / Seeding
    # -------------------------
    def _default_assets(self) -> List[Dict[str, Any]]:
        """Minimal default list; replace with your full universe if desired."""
        base = [
            {"symbol": "BTC", "name": "Bitcoin", "rank": 1},
            {"symbol": "ETH", "name": "Ethereum", "rank": 2},
            {"symbol": "SOL", "name": "Solana", "rank": 3},
            {"symbol": "XRP", "name": "XRP", "rank": 4},
            {"symbol": "DOGE", "name": "Dogecoin", "rank": 5},
            {"symbol": "BNB", "name": "BNB", "rank": 6},
            {"symbol": "ADA", "name": "Cardano", "rank": 7},
            {"symbol": "AVAX", "name": "Avalanche", "rank": 8},
            {"symbol": "LINK", "name": "Chainlink", "rank": 9},
            {"symbol": "UNI", "name": "Uniswap", "rank": 10},
        ]
        return base

    def _fallback_price(self, rank: int) -> float:
        """Deterministic fallback price by rank (keeps data realistic without external calls)."""
        if rank <= 2:
            return 30000.0 if rank == 1 else 2000.0
        if rank <= 10:
            return max(0.05, 0.5 * (11 - rank))  # simple decreasing scale
        if rank <= 50:
            return 1.0
        return 0.1

    def _seed_portfolio(self) -> None:
        """Seed the portfolio with $10 per asset, computing quantity from a fallback price."""
        for a in self.crypto_list:
            symbol = a["symbol"]
            name = a.get("name", symbol)
            rank = int(a.get("rank", 999))

            base_price = float(self._fallback_price(rank))
            # Prevent div/0; ensure positive
            if base_price <= 0.0:
                base_price = 0.000001

            qty = self.initial_value / base_price
            current_value = qty * base_price

            self.portfolio_data[symbol] = {
                "name": name,
                "rank": rank,
                "quantity": qty,  # fixed units
                "initial_price": base_price,
                "current_price": base_price,
                "initial_value": self.initial_value,  # $10
                "current_value": current_value,       # qty * current_price
                "pnl": current_value - self.initial_value,
                "pnl_percent": ((current_value - self.initial_value) / self.initial_value) * 100.0,
                "initial_investment_date": datetime.now(timezone.utc).isoformat(),
                "total_invested": self.initial_value,
                "total_realized_pnl": 0.0,
                "trade_count": 0,
            }

    # -------------------------
    # Summaries / Data
    # -------------------------
    def get_portfolio_data(self) -> Dict[str, Dict[str, Any]]:
        """Return the raw portfolio data mapping symbol -> fields."""
        return self.portfolio_data

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Aggregate summary across all assets."""
        total_initial = sum(v.get("initial_value", 0.0) for v in self.portfolio_data.values())
        total_current = sum(v.get("current_value", 0.0) for v in self.portfolio_data.values())
        total_pnl = total_current - total_initial
        total_pnl_pct = (total_pnl / total_initial * 100.0) if total_initial > 0 else 0.0

        # Top gainers/losers by pnl_percent
        items = list(self.portfolio_data.items())
        items.sort(key=lambda kv: kv[1].get("pnl_percent", 0.0), reverse=True)
        top_gainers = items[:5]
        top_losers = items[-5:]

        # Largest positions by current_value
        items_val = list(self.portfolio_data.items())
        items_val.sort(key=lambda kv: kv[1].get("current_value", 0.0), reverse=True)
        largest_positions = items_val[:10]

        return {
            "total_initial_value": total_initial,
            "total_current_value": total_current,
            "total_pnl": total_pnl,
            "total_pnl_percent": total_pnl_pct,
            "number_of_cryptos": len(self.portfolio_data),
            "top_gainers": [(s, d.get("name", s), d.get("pnl_percent", 0.0)) for s, d in top_gainers],
            "top_losers": [(s, d.get("name", s), d.get("pnl_percent", 0.0)) for s, d in top_losers],
            "largest_positions": [(s, d.get("name", s), d.get("current_value", 0.0)) for s, d in largest_positions],
        }

    def get_portfolio_performance(self) -> List[Dict[str, Any]]:
        """Per-asset performance rows, sorted by accumulated P&L% descending."""
        rows: List[Dict[str, Any]] = []
        now = datetime.now(timezone.utc)

        for symbol, c in self.portfolio_data.items():
            # Parse initial timestamp
            init_ts_raw = c.get("initial_investment_date")
            if isinstance(init_ts_raw, str):
                try:
                    init_ts = datetime.fromisoformat(init_ts_raw)
                except Exception:
                    init_ts = now
            else:
                init_ts = now

            days_invested = max(0, (now - init_ts).days)

            realized = float(c.get("total_realized_pnl", 0.0))
            unrealized = float(c.get("pnl", 0.0))
            total_accumulated_pnl = realized + unrealized

            total_invested = float(c.get("total_invested", c.get("initial_value", self.initial_value)))
            acc_pct = (total_accumulated_pnl / total_invested * 100.0) if total_invested > 0 else 0.0
            daily_ret = (acc_pct / days_invested) if days_invested > 0 else 0.0

            qty = float(c.get("quantity", 0.0))
            init_price = (total_invested / qty) if qty > 0 else 0.0

            rows.append(
                {
                    "symbol": symbol,
                    "name": c.get("name", symbol),
                    "rank": int(c.get("rank", 999)),
                    "days_invested": days_invested,
                    "total_invested": total_invested,
                    "current_value": float(c.get("current_value", 0.0)),
                    "total_accumulated_pnl": total_accumulated_pnl,
                    "accumulated_pnl_percent": acc_pct,
                    "daily_return_percent": daily_ret,
                    "current_price": float(c.get("current_price", 0.0)),
                    "quantity": qty,
                    "initial_price": init_price,
                    "best_performer": acc_pct > 50.0,
                    "status": "winning" if acc_pct > 0.0 else "losing",
                }
            )

        rows.sort(key=lambda r: r.get("accumulated_pnl_percent", 0.0), reverse=True)
        return rows

    def get_current_positions(self) -> List[Dict[str, Any]]:
        """
        Current positions with derived targets.
        NOTE (Option A): includes 'target_buy_price' so 'target_buy' is used (no Pyright warning).
        """
        positions: List[Dict[str, Any]] = []
        total_val = sum(float(v.get("current_value", 0.0)) for v in self.portfolio_data.values())
        total_val = total_val if total_val > 0 else 1.0  # avoid /0

        now_iso = datetime.now(timezone.utc).isoformat()

        for s, h in self.portfolio_data.items():
            qty = float(h.get("quantity", 0.0))
            if qty <= 0.0:
                continue

            cur_px = float(h.get("current_price", 0.0))
            cur_val = qty * cur_px
            pnl_pct = float(h.get("pnl_percent", 0.0))

            # Simple status bucketing
            if pnl_pct > 20.0:
                status = "strong_gain"
            elif pnl_pct > 5.0:
                status = "moderate_gain"
            elif pnl_pct > -5.0:
                status = "stable"
            elif pnl_pct > -20.0:
                status = "moderate_loss"
            else:
                status = "significant_loss"

            # Targets
            target_buy = cur_px * 0.95 if cur_px > 0 else 0.0
            target_sell = cur_px * 1.10 if cur_px > 0 else 0.0
            potential_sell_value = qty * target_sell if target_sell > 0 else 0.0
            potential_profit = potential_sell_value - float(h.get("initial_value", self.initial_value))

            initial_price = (
                float(h.get("initial_value", self.initial_value)) / qty if qty > 0 else 0.0
            )

            positions.append(
                {
                    "symbol": h.get("symbol", s),
                    "name": h.get("name", s),
                    "quantity": qty,
                    "current_price": cur_px,
                    "current_value": cur_val,
                    "position_percent": (cur_val / total_val) * 100.0,
                    "unrealized_pnl": float(h.get("pnl", 0.0)),
                    "pnl_percent": pnl_pct,
                    "status": status,
                    "target_buy_price": target_buy,   # <-- Option A: included
                    "target_sell_price": target_sell,
                    "potential_sell_value": potential_sell_value,
                    "potential_profit": potential_profit,
                    "avg_buy_price": initial_price,
                    "last_updated": now_iso,
                }
            )

        positions.sort(key=lambda x: x.get("current_value", 0.0), reverse=True)
        return positions

    # -------------------------
    # Persistence
    # -------------------------
    def save_portfolio_state(self, filepath: str = "crypto_portfolio_state.json") -> None:
        """Save current portfolio state to a JSON file."""
        state = {
            "portfolio_data": self.portfolio_data,
            "price_history": {
                sym: [
                    {
                        "timestamp": pt["timestamp"],
                        "price": float(pt.get("price", 0.0)),
                        "volume": float(pt.get("volume", 0.0)),
                    }
                    for pt in hist
                ]
                for sym, hist in self.price_history.items()
            },
            "cash_balance": self.cash_balance,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        self.logger.info("Portfolio state saved to %s", filepath)

    def load_portfolio_state(self, filepath: str = "crypto_portfolio_state.json") -> bool:
        """
        Load portfolio state from file.
        Return False if file missing or invalid (keeps current state).
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                state = json.load(f)
            p = state.get("portfolio_data")
            if isinstance(p, dict):
                self.portfolio_data = p
            self.price_history = state.get("price_history", {})
            self.cash_balance = float(state.get("cash_balance", 0.0))
            self.logger.info("Loaded portfolio state from %s", filepath)
            return True
        except Exception as e:
            self.logger.warning("Could not load portfolio state: %s", e)
            return False
