"""
Trading Business Service
Handles trading operations, bot management, and position analysis
"""
from typing import Dict, Any, List, Optional
import logging
import threading
import time
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class TradingBusinessService:
    """Business logic for trading operations and bot management."""
    
    def __init__(self):
        self.logger = logger
        self._state_lock = threading.RLock()
    
    def calculate_entry_confidence(self, symbol: str, current_price: float, 
                                 bb_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate entry confidence score and timing signal."""
        try:
            # Base confidence score
            confidence_score = 50.0  # Neutral starting point
            timing_signal = "WAIT"
            confidence_level = "FAIR"
            
            # Bollinger Bands analysis influence
            bb_signal = bb_analysis.get("signal", "NO DATA")
            bb_distance = bb_analysis.get("distance_percent", 0)
            
            if bb_signal == "STRONG":
                confidence_score += 25  # Strong buy signal
                timing_signal = "BUY_NOW"
            elif bb_signal == "MODERATE":
                confidence_score += 15  # Moderate buy signal
                timing_signal = "CAUTIOUS_BUY"
            elif bb_signal == "WEAK":
                confidence_score += 5   # Weak buy signal
                timing_signal = "WAIT"
            
            # Distance from lower band adjustment
            if bb_distance <= 2:  # Very close to lower band
                confidence_score += 10
            elif bb_distance <= 5:  # Close to lower band
                confidence_score += 5
            elif bb_distance > 15:  # Far from lower band
                confidence_score -= 10
            
            # Asset-specific adjustments
            if symbol in ['BTC', 'ETH']:  # Blue chip assets
                confidence_score += 5
            elif symbol in ['DOGE', 'SHIB', 'PEPE']:  # Meme coins (higher risk)
                confidence_score -= 10
            
            # Determine confidence level
            if confidence_score >= 75:
                confidence_level = "STRONG"
            elif confidence_score >= 60:
                confidence_level = "GOOD"
            elif confidence_score >= 40:
                confidence_level = "FAIR"
            elif confidence_score >= 25:
                confidence_level = "WEAK"
            else:
                confidence_level = "POOR"
                timing_signal = "AVOID"
            
            # Cap score at 100
            confidence_score = min(100, max(0, confidence_score))
            
            return {
                "level": confidence_level,
                "score": round(confidence_score, 1),
                "timing_signal": timing_signal
            }
            
        except Exception as e:
            self.logger.debug(f"Entry confidence calculation failed for {symbol}: {e}")
            return {
                "level": "FAIR",
                "score": 50.0,
                "timing_signal": "WAIT"
            }
    
    def analyze_position_type(self, symbol: str, current_balance: float, 
                            target_price: float, current_price: float) -> Dict[str, Any]:
        """Analyze position type and trading signals."""
        try:
            # Determine position type
            if current_balance > 0:
                position_type = "current_holding"
                buy_signal = "CURRENT HOLDING"
            else:
                position_type = "available_position"
                
                # Determine buy signal based on price analysis
                if target_price > 0 and current_price > 0:
                    price_diff_percent = ((current_price - target_price) / target_price) * 100
                    
                    if price_diff_percent <= -5:  # Price is 5%+ below target
                        buy_signal = "STRONG BUY"
                    elif price_diff_percent <= -2:  # Price is 2-5% below target
                        buy_signal = "BUY"
                    elif price_diff_percent <= 2:   # Price within 2% of target
                        buy_signal = "NEAR TARGET"
                    else:  # Price above target
                        buy_signal = "WAIT"
                else:
                    buy_signal = "MONITOR"
            
            # Calculate price metrics
            price_difference = current_price - target_price if target_price > 0 else 0
            price_diff_percent = ((current_price - target_price) / target_price * 100) if target_price > 0 else 0
            
            return {
                "position_type": position_type,
                "buy_signal": buy_signal,
                "price_difference": round(price_difference, 8),
                "price_diff_percent": round(price_diff_percent, 2)
            }
            
        except Exception as e:
            self.logger.debug(f"Position analysis failed for {symbol}: {e}")
            return {
                "position_type": "unknown",
                "buy_signal": "ERROR",
                "price_difference": 0,
                "price_diff_percent": 0
            }
    
    def create_initial_purchase_trades(self, mode: str, trade_type: str) -> List[Dict[str, Any]]:
        """Create trade records using real OKX cost basis instead of simulations."""
        try:
            from src.services.portfolio_service import get_portfolio_service
            portfolio_service = get_portfolio_service()
            okx_portfolio: Dict[str, Any] = portfolio_service.get_portfolio_data()
            
            initial_trades = []
            trade_counter = 1
            
            for holding in okx_portfolio.get('holdings', []):
                # Type hint: holding is a dict from portfolio service
                holding: Dict[str, Any]
                symbol = holding['symbol']
                current_price = holding['current_price']
                quantity = holding['quantity']
                cost_basis = holding.get('cost_basis', 0)  # Use real cost basis from OKX
                
                if current_price and current_price > 0:
                    trade_record = {
                        "trade_id": trade_counter,
                        "symbol": f"{symbol}/USDT",
                        "side": "BUY",
                        "quantity": quantity,
                        "price": holding.get('avg_entry_price', current_price),  # Real entry from OKX
                        "total_value": cost_basis,  # Real cost basis from OKX
                        "type": "INITIAL_PURCHASE",
                        "mode": mode,
                        "timestamp": self._iso_utc(),
                        "status": "completed"
                    }
                    initial_trades.append(trade_record)
                    trade_counter += 1
            
            self.logger.info("Created %d initial purchase trades for portfolio setup", len(initial_trades))
            return initial_trades
            
        except (KeyError, AttributeError, ValueError) as e:
            self.logger.error(f"Data error creating initial purchase trades: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error creating initial purchase trades: {e}")
            return []
    
    def filter_trades_by_timeframe(self, trades: List[Dict[str, Any]], timeframe: str) -> List[Dict[str, Any]]:
        """Filter trades based on timeframe specification."""
        if not trades:
            return []
        
        try:
            # Parse timeframe
            timeframe_map = {
                '1h': 1/24,
                '6h': 6/24, 
                '12h': 12/24,
                '24h': 1,
                '1d': 1,
                '3d': 3,
                '7d': 7,
                '14d': 14,
                '30d': 30,
                '90d': 90
            }
            
            days = timeframe_map.get(timeframe, 7)  # Default to 7 days
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)
            
            filtered_trades = []
            for trade in trades:
                try:
                    trade_time_str = trade.get('timestamp', '')
                    if trade_time_str:
                        # Handle ISO format with Z suffix
                        if trade_time_str.endswith('Z'):
                            trade_time_str = trade_time_str[:-1] + '+00:00'
                        
                        trade_time = datetime.fromisoformat(trade_time_str)
                        if trade_time.tzinfo is None:
                            trade_time = trade_time.replace(tzinfo=timezone.utc)
                        
                        if trade_time >= cutoff_time:
                            filtered_trades.append(trade)
                            
                except (ValueError, TypeError) as e:
                    self.logger.debug(f"Error parsing trade timestamp: {e}")
                    continue
            
            return filtered_trades
            
        except Exception as e:
            self.logger.error(f"Error filtering trades by timeframe: {e}")
            return trades  # Return original list on error
    
    def _iso_utc(self, dt: Optional[datetime] = None) -> str:
        """Convert datetime to ISO UTC string."""
        if dt is None:
            dt = datetime.now(timezone.utc)
        return dt.isoformat().replace('+00:00', 'Z')
    
    def get_bot_runtime_stats(self, bot_state: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate bot runtime statistics."""
        bot_running = bool(bot_state.get("running", False))
        runtime_sec = 0
        
        if bot_running and bot_state.get("started_at"):
            try:
                ts = str(bot_state["started_at"]).replace('Z', '+00:00')
                dt = datetime.fromisoformat(ts)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                runtime_sec = max(0, int((datetime.now(dt.tzinfo) - dt).total_seconds()))
            except (ValueError, TypeError, KeyError) as e:
                self.logger.debug(f"Error parsing bot start time: {e}")
                runtime_sec = 0
        
        return {
            "runtime_seconds": runtime_sec,
            "runtime_human": self._humanize_seconds(runtime_sec),
            "running": bot_running
        }
    
    def _humanize_seconds(self, seconds: int) -> str:
        """Convert seconds to human readable format."""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m {seconds % 60}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"