"""
Master Portfolio Assets List - Hardcoded Cryptocurrency Universe
===============================================================

This module contains the definitive list of 103 cryptocurrencies that comprise
the complete trading portfolio. This hardcoded list ensures consistent data
loading and eliminates API mapping uncertainties.

Each asset represents a $10 initial investment when trading begins.
"""

# Master list of 103 cryptocurrency assets for the portfolio
MASTER_PORTFOLIO_ASSETS = [
    # Top 25 by Market Cap & Liquidity
    "BTC", "ETH", "SOL", "XRP", "DOGE", "ADA", "AVAX", "LINK", "UNI", "BNB",
    "DOT", "MATIC", "LTC", "ATOM", "ICP", "NEAR", "APT", "STX", "IMX", "HBAR",
    "BCH", "FIL", "VET", "THETA", "ALGO",
    
    # DeFi Ecosystem (15 assets)
    "AAVE", "SUSHI", "COMP", "YFI", "SNX", "CRV", "BAL", "ALPHA", "CREAM", "BADGER",
    "MKR", "LEND", "RUNE", "CAKE", "BAKE",
    
    # Gaming & NFT (15 assets)
    "AXS", "MANA", "SAND", "ENJ", "CHZ", "FLOW", "WAX", "GALA", "ILV", "AUDIO",
    "REVV", "TLM", "SLP", "GHST", "ALICE",
    
    # Layer 2 & Infrastructure (12 assets)
    "ARB", "OP", "EGLD", "FTM", "LUNA", "XTZ", "ZIL", "ONE", "CELO", "KAVA",
    "SCRT", "ROSE",
    
    # Meme & Community (10 assets)
    "SHIB", "PEPE", "FLOKI", "BABYDOGE", "ELON", "DOGO", "AKITA", "KISHU", "SAITAMA", "LEASH",
    
    # Exchange Tokens (8 assets)
    "FTT", "KCS", "HT", "OKB", "LEO", "CRO", "GT", "BGB",
    
    # Privacy & Security (8 assets)
    "XMR", "ZEC", "DASH", "ZCASH", "BEAM", "GRIN", "FIRO", "ARRR",
    
    # Enterprise & Business (10 assets)
    "XLM", "XDC", "IOTA", "NANO", "RVN", "DGB", "SYS", "VTC", "MONA", "QNT"
]

# Verify we have exactly 103 assets
assert len(MASTER_PORTFOLIO_ASSETS) == 103, f"Expected 103 assets, got {len(MASTER_PORTFOLIO_ASSETS)}"

# Remove duplicates while preserving order
seen = set()
MASTER_PORTFOLIO_ASSETS = [x for x in MASTER_PORTFOLIO_ASSETS if not (x in seen or seen.add(x))]

# Final verification
assert len(MASTER_PORTFOLIO_ASSETS) == 103, f"After deduplication: Expected 103 assets, got {len(MASTER_PORTFOLIO_ASSETS)}"

def get_portfolio_assets():
    """
    Returns the complete list of 103 cryptocurrency assets for portfolio initialization.
    
    Returns:
        List[str]: List of 103 cryptocurrency symbols
    """
    return MASTER_PORTFOLIO_ASSETS.copy()

def get_portfolio_size():
    """
    Returns the total number of assets in the master portfolio.
    
    Returns:
        int: Number of cryptocurrency assets (103)
    """
    return len(MASTER_PORTFOLIO_ASSETS)

def is_valid_asset(symbol: str) -> bool:
    """
    Check if a cryptocurrency symbol is part of the master portfolio.
    
    Args:
        symbol (str): Cryptocurrency symbol to check
        
    Returns:
        bool: True if symbol is in the master portfolio
    """
    return symbol.upper() in MASTER_PORTFOLIO_ASSETS

def get_asset_categories():
    """
    Returns categorized breakdown of the portfolio assets.
    
    Returns:
        dict: Dictionary mapping categories to asset lists
    """
    return {
        "top_market_cap": MASTER_PORTFOLIO_ASSETS[0:25],
        "defi_ecosystem": MASTER_PORTFOLIO_ASSETS[25:40], 
        "gaming_nft": MASTER_PORTFOLIO_ASSETS[40:55],
        "layer2_infrastructure": MASTER_PORTFOLIO_ASSETS[55:67],
        "meme_community": MASTER_PORTFOLIO_ASSETS[67:77],
        "exchange_tokens": MASTER_PORTFOLIO_ASSETS[77:85],
        "privacy_security": MASTER_PORTFOLIO_ASSETS[85:93],
        "enterprise_business": MASTER_PORTFOLIO_ASSETS[93:103]
    }

# Asset validation and statistics
if __name__ == "__main__":
    print(f"Master Portfolio Assets: {len(MASTER_PORTFOLIO_ASSETS)} cryptocurrencies")
    print(f"Categories: {len(get_asset_categories())} asset categories")
    print("\nCategory Breakdown:")
    for category, assets in get_asset_categories().items():
        print(f"  {category}: {len(assets)} assets")
    print(f"\nFirst 10 assets: {MASTER_PORTFOLIO_ASSETS[:10]}")
    print(f"Last 10 assets: {MASTER_PORTFOLIO_ASSETS[-10:]}")