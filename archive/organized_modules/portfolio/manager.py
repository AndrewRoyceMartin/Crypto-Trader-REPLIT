"""
Portfolio Management Module
Handles portfolio data, calculations, and management using business services
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Initialize portfolio business service
_portfolio_business_service = None

def get_portfolio_business_service():
    """Get portfolio business service instance."""
    global _portfolio_business_service
    if _portfolio_business_service is None:
        from services.portfolio_business_service import PortfolioBusinessService
        _portfolio_business_service = PortfolioBusinessService()
    return _portfolio_business_service

def get_portfolio_summary() -> dict[str, Any]:
    """Get portfolio summary for status endpoint using business service."""
    try:
        business_service = get_portfolio_business_service()
        return business_service.get_portfolio_summary()
    except Exception as e:
        logger.info(f"Portfolio summary unavailable: {e}")
        return {
            "total_value": 0.0,
            "daily_pnl": 0.0,
            "daily_pnl_percent": 0.0,
            "error": "Portfolio data unavailable"
        }

def calculate_portfolio_overview(portfolio_data: dict[str, Any], currency: str = "USD") -> dict[str, Any]:
    """Calculate portfolio overview using business service."""
    try:
        business_service = get_portfolio_business_service()
        return business_service.calculate_portfolio_overview(portfolio_data, currency)
    except Exception as e:
        logger.error(f"Portfolio overview calculation failed: {e}")
        return {
            "currency": currency,
            "total_value": 0.0,
            "error": "Calculation failed"
        }

def calculate_asset_allocation(holdings: list) -> list:
    """Calculate asset allocation using business service."""
    try:
        business_service = get_portfolio_business_service()
        return business_service.calculate_asset_allocation(holdings)
    except Exception as e:
        logger.error(f"Asset allocation calculation failed: {e}")
        return []

def get_portfolio_service():
    """Get the global PortfolioService singleton from the service module."""
    try:
        from src.services.portfolio_service import get_portfolio_service as _get_ps
        return _get_ps()
    except ImportError as e:
        logger.error(f"Could not import portfolio service: {e}")
        return None
