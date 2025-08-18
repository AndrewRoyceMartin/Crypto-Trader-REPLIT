# -*- coding: utf-8 -*-
"""
Master Portfolio Assets List - Hardcoded Cryptocurrency Universe
===============================================================

This module contains the definitive list of 103 cryptocurrencies that comprise
the complete trading portfolio. This hardcoded list ensures consistent data
loading and eliminates API mapping uncertainties.

Each asset represents a $10 initial investment when trading begins.
"""

from __future__ import annotations

from typing import List, Dict

# Base list (intentionally ordered)
_MASTER_ASSETS_RAW: List[str] = [
    # Top 25 by Market Cap & Liquidity (25)
    "BTC", "ETH", "SOL", "XRP", "DOGE", "ADA", "AVAX", "LINK", "UNI", "BNB",
    "DOT", "MATIC", "LTC", "ATOM", "ICP", "NEAR", "APT", "STX", "IMX", "HBAR",
    "BCH", "FIL", "VET", "THETA", "ALGO",

    # DeFi Ecosystem (15)  -> 40
    "AAVE", "SUSHI", "COMP", "YFI", "SNX", "CRV", "BAL", "ALPHA", "CREAM", "BADGER",
    "MKR", "LEND", "RUNE", "CAKE", "BAKE",

    # Gaming & NFT (15)    -> 55
    "AXS", "MANA", "SAND", "ENJ", "CHZ", "FLOW", "WAX", "GALA", "ILV", "AUDIO",
    "REVV", "TLM", "SLP", "GHST", "ALICE",

    # Layer 2 & Infrastructure (12) -> 67
    "ARB", "OP", "EGLD", "FTM", "LUNA", "XTZ", "ZIL", "ONE", "CELO", "KAVA",
    "SCRT", "ROSE",

    # Meme & Community (10) -> 77
    "SHIB", "PEPE", "FLOKI", "BABYDOGE", "ELON", "DOGO", "AKITA", "KISHU", "SAITAMA", "LEASH",

    # Exchange Tokens (8)   -> 85
    "FTT", "KCS", "HT", "OKB", "LEO", "CRO", "GT", "BGB",

    # Privacy & Security (8) -> 93
    "XMR", "ZEC", "DASH", "ZCASH", "BEAM", "GRIN", "FIRO", "ARRR",

    # Enterprise & Business (10) -> 103
    "XLM", "XDC", "IOTA", "NANO", "RVN", "DGB", "SYS", "VTC", "MONA", "QNT",
]

# Deduplicate while preserving order (defensive)
_seen = set()
MASTER_PORTFOLIO_ASSETS: List[str] = []
for sym in _MASTER_ASSETS_RAW:
    up = sym.upper()
    if up not in _seen:
        _seen.add(up)
        MASTER_PORTFOLIO_ASSETS.append(up)

# Final verification (fail fast with a clear error message)
EXPECTED_COUNT = 103
if len(MASTER_PORTFOLIO_ASSETS) != EXPECTED_COUNT:
    raise ValueError(
        f"MASTER_PORTFOLIO_ASSETS must contain {EXPECTED_COUNT} unique symbols; "
        f"found {len(MASTER_PORTFOLIO_ASSETS)}"
    )

# Category index boundaries (keep in sync with the counts above)
_IDX: Dict[str, tuple[int, int]] = {
    "top_market_cap": (0, 25),
    "defi_ecosystem": (25, 40),
    "gaming_nft": (40, 55),
    "layer2_infrastructure": (55, 67),
    "meme_community": (67, 77),
    "exchange_tokens": (77, 85),
    "privacy_security": (85, 93),
    "enterprise_business": (93, 103),
}

def get_portfolio_assets() -> List[str]:
    """Return a copy of the complete asset list."""
    return list(MASTER_PORTFOLIO_ASSETS)

def get_portfolio_size() -> int:
    """Return the total number of assets."""
    return len(MASTER_PORTFOLIO_ASSETS)

def is_valid_asset(symbol: str) -> bool:
    """Check if a symbol is part of the master portfolio."""
    return symbol.upper() in MASTER_PORTFOLIO_ASSETS

def get_asset_categories() -> Dict[str, List[str]]:
    """Return categorized breakdown of the portfolio assets."""
    return {
        name: MASTER_PORTFOLIO_ASSETS[start:end]
        for name, (start, end) in _IDX.items()
    }

if __name__ == "__main__":
    print(f"Master Portfolio Assets: {len(MASTER_PORTFOLIO_ASSETS)} cryptocurrencies")
    cats = get_asset_categories()
    print(f"Categories: {len(cats)} asset categories\n")
    print("Category Breakdown:")
    for cat, assets in cats.items():
        print(f"  {cat}: {len(assets)} assets")
    print(f"\nFirst 10 assets: {MASTER_PORTFOLIO_ASSETS[:10]}")
    print(f"Last 10 assets: {MASTER_PORTFOLIO_ASSETS[-10:]}")
