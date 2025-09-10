"""
Portfolio Business Service
Handles portfolio calculations, P&L analysis, and asset allocation logic
"""
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timezone
import time

logger = logging.getLogger(__name__)

class PortfolioBusinessService:
    """Business logic for portfolio management and calculations."""
    
    def __init__(self):
        self.logger = logger
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
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
            self.logger.info(f"Portfolio summary unavailable: {e}")
            return {
                "total_value": 0.0,
                "daily_pnl": 0.0,
                "daily_pnl_percent": 0.0,
                "error": "Portfolio data unavailable"
            }
    
    def calculate_portfolio_overview(self, portfolio_data: Dict[str, Any], 
                                   currency: str = "USD") -> Dict[str, Any]:
        """Calculate comprehensive portfolio overview with analytics."""
        holdings_list = portfolio_data.get('holdings', [])
        
        overview = {
            "currency": currency,
            "total_value": float(portfolio_data.get('total_current_value', 0)),
            "cash_balance": float(portfolio_data.get('cash_balance', 0)),
            "aud_balance": float(portfolio_data.get('aud_balance', 0.0)),
            "total_pnl": float(portfolio_data.get('total_pnl', 0)),
            "total_pnl_percent": float(portfolio_data.get('total_pnl_percent', 0)),
            "daily_pnl": float(portfolio_data.get('daily_pnl', 0.0)),
            "daily_pnl_percent": float(portfolio_data.get('daily_pnl_percent', 0.0)),
            "total_assets": len(holdings_list),
            "profitable_positions": sum(1 for h in holdings_list if float(h.get('pnl_percent', 0) or 0) > 0),
            "losing_positions": sum(1 for h in holdings_list if float(h.get('pnl_percent', 0) or 0) < 0),
            "breakeven_positions": max(
                0,
                len(holdings_list) - sum(
                    1 for h in holdings_list if float(h.get('pnl_percent', 0) or 0) != 0
                )
            ),
            "last_update": portfolio_data.get('last_update'),
            "is_live": True,
            "connected": True
        }
        
        return overview
    
    def calculate_asset_allocation(self, holdings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate asset allocation percentages and data."""
        total_value = sum(float(pos.get('market_value', 0) or pos.get('current_value', 0)) for pos in holdings)
        
        allocation_data = []
        for position in holdings:
            market_value = float(position.get('market_value', 0) or position.get('current_value', 0))
            if market_value > 0:
                allocation_percent = (market_value / total_value) * 100 if total_value > 0 else 0
                allocation_data.append({
                    "symbol": position.get('symbol', 'Unknown'),
                    "market_value": market_value,
                    "allocation_percent": round(allocation_percent, 2),
                    "quantity": float(position.get('quantity', 0)),
                    "current_price": float(position.get('current_price', 0))
                })
        
        # Sort by allocation percentage descending
        allocation_data.sort(key=lambda x: x['allocation_percent'], reverse=True)
        return allocation_data
    
    def analyze_performance_metrics(self, holdings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze portfolio performance metrics."""
        if not holdings:
            return {
                "best_performer": None,
                "worst_performer": None,
                "win_rate": 0.0,
                "concentration_risk": 0.0,
                "profitable_count": 0,
                "losing_count": 0
            }
        
        # Find best and worst performers
        profitable = [h for h in holdings if float(h.get('pnl_percent', 0) or 0) > 0]
        losing = [h for h in holdings if float(h.get('pnl_percent', 0) or 0) < 0]
        
        best_performer = max(holdings, key=lambda x: float(x.get('pnl_percent', 0) or 0)) if holdings else None
        worst_performer = min(holdings, key=lambda x: float(x.get('pnl_percent', 0) or 0)) if holdings else None
        
        # Calculate concentration risk (top 3 holdings percentage)
        sorted_holdings = sorted(holdings, key=lambda x: x.get('allocation_percent', 0), reverse=True)
        concentration_risk = sum(h.get('allocation_percent', 0) for h in sorted_holdings[:3])
        
        return {
            "best_performer": {
                'symbol': best_performer.get('symbol', 'N/A'),
                'name': best_performer.get('name', 'N/A'),
                'pnl_percent': round(best_performer.get('pnl_percent', 0), 2)
            } if best_performer else None,
            "worst_performer": {
                'symbol': worst_performer.get('symbol', 'N/A'),
                'name': worst_performer.get('name', 'N/A'),
                'pnl_percent': round(worst_performer.get('pnl_percent', 0), 2)
            } if worst_performer else None,
            "win_rate": round((len(profitable) / len(holdings) * 100), 2),
            "concentration_risk": round(concentration_risk, 2),
            "profitable_count": len(profitable),
            "losing_count": len(losing)
        }
    
    def format_portfolio_response(self, portfolio_data: Dict[str, Any], 
                                overview: Dict[str, Any], 
                                currency: str = "USD") -> Dict[str, Any]:
        """Format complete portfolio response payload."""
        holdings_list = portfolio_data.get('holdings', [])
        
        payload = {
            "holdings": holdings_list,
            "summary": {
                "total_cryptos": len(holdings_list),
                "total_current_value": overview["total_value"],
                "total_estimated_value": float(
                    portfolio_data.get('total_estimated_value', overview["total_value"])
                ),
                "total_pnl": overview["total_pnl"],
                "total_pnl_percent": overview["total_pnl_percent"],
                "cash_balance": overview["cash_balance"],
                "aud_balance": overview["aud_balance"],
                "currency": currency
            },
            "total_pnl": overview["total_pnl"],
            "total_pnl_percent": overview["total_pnl_percent"],
            "total_current_value": overview["total_value"],
            "total_estimated_value": float(
                portfolio_data.get('total_estimated_value', overview["total_value"])
            ),
            "cash_balance": overview["cash_balance"],
            "currency": currency,
            "overview": overview
        }
        
        # Add refresh timing
        import os
        refresh_seconds = int(os.getenv("UI_REFRESH_MS", "6000")) // 1000
        payload["overview"]["next_refresh_in_seconds"] = refresh_seconds
        payload["next_refresh_in_seconds"] = refresh_seconds
        
        return payload