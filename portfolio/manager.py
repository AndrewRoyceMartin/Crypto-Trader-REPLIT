"""
Portfolio Management Module
Handles portfolio data, calculations, and management
"""
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

def get_portfolio_summary() -> Dict[str, Any]:
    """Get portfolio summary for status endpoint."""
    try:
        from src.services.portfolio_service import get_portfolio_service as _get_ps
        
        portfolio_service = _get_ps()
        if not portfolio_service:
            return {
                "total_value": 0.0,
                "daily_pnl": 0.0,
                "daily_pnl_percent": 0.0,
                "error": "Service not available"
            }

        portfolio_data: Dict[str, Any] = portfolio_service.get_portfolio_data()
        return {
            "total_value": portfolio_data.get('total_current_value', 0.0),
            "daily_pnl": portfolio_data.get('total_pnl', 0.0),
            "daily_pnl_percent": portfolio_data.get('total_pnl_percent', 0.0),
            "cash_balance": portfolio_data.get('cash_balance', 0.0),
            "status": "connected"
        }
    except Exception as e:
        logger.info(f"Portfolio summary unavailable: {e}")
        return {
            "total_value": 0.0,
            "daily_pnl": 0.0,
            "daily_pnl_percent": 0.0,
            "error": "Portfolio data unavailable"
        }

def get_portfolio_service():
    """Get the global PortfolioService singleton from the service module."""
    try:
        from src.services.portfolio_service import get_portfolio_service as _get_ps
        return _get_ps()
    except ImportError as e:
        logger.error(f"Could not import portfolio service: {e}")
        return None