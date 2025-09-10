"""
Version configuration for the trading system.
"""

# Application version - update this for each deployment
APP_VERSION = "2.2.0"

# Version history:
# 2.2.0 - 2025-08-27: Enhanced testing framework with real-time progress monitoring, comprehensive null safety, button functionality validation, and dual-tier test system
# 2.1.3 - 2025-08-26: Fixed console warnings/errors, removed invalid OKB symbol, enhanced API rate limiting and error handling
# 2.1.2 - 2025-08-25: Comprehensive static analysis review and code quality improvements
# 2.1.1 - 2025-08-22: Enhanced trade history to use OKX trading history (executed trades) instead of order history
# 2.1.0 - 2025-08-14: Reduced CoinGecko API polling to once per minute, improved rate limiting
# 2.0.0 - 2025-08-14: Server-side connection monitoring, CoinGecko-specific labels
# 1.0.0 - 2025-08-13: Initial deployment with crypto portfolio system

def get_version():
    """Get the current application version."""
    return APP_VERSION

def get_version_info():
    """Get detailed version information."""
    return {
        'version': APP_VERSION,
        'release_date': '2025-08-27',
        'build_type': 'Production'
    }