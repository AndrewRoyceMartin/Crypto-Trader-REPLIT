"""
Portfolio Service - Integrates app with Simulated OKX Exchange
Provides a unified interface for portfolio data from the exchange.
"""

import logging
import time
from typing import Dict, List, Optional
from datetime import datetime
from src.exchanges.simulated_okx import SimulatedOKX
from src.data.portfolio_assets import MASTER_PORTFOLIO_ASSETS as PORTFOLIO_ASSETS
from src.utils.bot_pricing import BotPricingCalculator, BotParams


class PortfolioService:
    """Service that manages portfolio data through Simulated OKX exchange."""
    
    def __init__(self):
        """Initialize portfolio service with OKX exchange."""
        self.logger = logging.getLogger(__name__)
        
        # Initialize simulated OKX exchange
        config = {
            'sandbox': True,
            'apiKey': 'simulated_key',
            'secret': 'simulated_secret',
            'password': 'simulated_passphrase'
        }
        
        self.exchange = SimulatedOKX(config)
        self._initialize_exchange()
        
        # Track initialization state - always initialized for simulation
        self.is_initialized = True
        self._last_sync = datetime.now()
        
    def _initialize_exchange(self):
        """Initialize and connect to the simulated exchange."""
        try:
            success = self.exchange.connect()
            if success:
                self.logger.info("Successfully connected to Simulated OKX Exchange")
                self._populate_initial_portfolio()
            else:
                raise Exception("Failed to connect to exchange")
                
        except Exception as e:
            self.logger.error(f"Exchange initialization failed: {str(e)}")
            raise
    
    def _populate_initial_portfolio(self):
        """Populate the exchange with initial $10 positions for each crypto."""
        try:
            self.logger.info("Populating initial portfolio positions...")
            
            # Create initial positions for each asset ($10 each)
            successful_positions = 0
            failed_positions = []
            
            for symbol in PORTFOLIO_ASSETS:
                try:
                    # Calculate quantity for $10 position
                    current_price = self.exchange._get_current_price(f"{symbol}/USDT")
                    if current_price and current_price > 0:
                        quantity = 10.0 / current_price
                        
                        # Place buy order to establish position
                        order_result = self.exchange.place_order(
                            symbol=f"{symbol}/USDT",
                            side='buy',
                            amount=quantity,
                            order_type='market'
                        )
                        
                        if order_result.get('code') == '0':
                            successful_positions += 1
                            self.logger.debug(f"Created position: {symbol} - {quantity:.8f} @ ${current_price:.6f}")
                        else:
                            failed_positions.append(symbol)
                            
                    else:
                        failed_positions.append(symbol)
                        self.logger.warning(f"Could not get price for {symbol}")
                        
                except Exception as e:
                    failed_positions.append(symbol)
                    self.logger.warning(f"Failed to create position for {symbol}: {str(e)}")
            
            self.logger.info(f"Portfolio initialization complete: {successful_positions} positions created")
            if failed_positions:
                self.logger.warning(f"Failed to create positions for: {', '.join(failed_positions)}")
            
            # Generate some initial trade history for demonstration
            self._generate_initial_trade_history()
            
            self.is_initialized = True
            self._last_sync = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Portfolio population failed: {str(e)}")
            raise
    
    def _generate_initial_trade_history(self):
        """Generate some initial trade history for the portfolio."""
        try:
            from datetime import timedelta
            import random
            
            # Generate trades for last 30 days
            base_time = datetime.now() - timedelta(days=30)
            
            # Get top 20 assets for generating trade history
            top_assets = PORTFOLIO_ASSETS[:20]
            
            trades_generated = 0
            for i, symbol in enumerate(top_assets):
                
                # Generate 2-5 trades per asset over the past month
                num_trades = random.randint(2, 5)
                
                for j in range(num_trades):
                    # Random time in the past 30 days
                    days_ago = random.randint(1, 30)
                    hours_ago = random.randint(0, 23)
                    trade_time = base_time + timedelta(days=days_ago, hours=hours_ago)
                    
                    # Random trade details
                    side = 'buy' if random.random() > 0.6 else 'sell'  # More buys than sells
                    base_price = self.exchange._get_current_price(f"{symbol}/USDT") or 1.0
                    # Vary price by ±20% from current
                    price_variation = random.uniform(0.8, 1.2)
                    trade_price = base_price * price_variation
                    
                    # Random quantity (smaller for expensive coins)
                    if base_price > 1000:  # BTC, ETH
                        quantity = random.uniform(0.001, 0.01)
                    elif base_price > 100:  # SOL, etc
                        quantity = random.uniform(0.1, 1.0)
                    elif base_price > 1:  # Most altcoins
                        quantity = random.uniform(1, 50)
                    else:  # Cheap coins
                        quantity = random.uniform(100, 10000)
                    
                    # Create simulated trade in exchange
                    trade_data = {
                        'ordId': f'simulated_{trades_generated + 1}',
                        'clOrdId': f'client_{trades_generated + 1}',
                        'instId': f'{symbol}-USDT-SWAP',
                        'side': side,
                        'sz': str(quantity),
                        'px': str(trade_price),
                        'fillSz': str(quantity),
                        'fillPx': str(trade_price),
                        'ts': str(int(trade_time.timestamp() * 1000)),
                        'state': 'filled',
                        'fee': str(quantity * trade_price * 0.001),  # 0.1% fee
                        'feeCcy': 'USDT'
                    }
                    
                    # Add to exchange's trade history
                    if not hasattr(self.exchange, 'trade_history'):
                        self.exchange.trade_history = []
                    self.exchange.trade_history.append(trade_data)
                    
                    trades_generated += 1
            
            self.logger.info(f"Generated {trades_generated} initial trades for portfolio demonstration")
            
        except Exception as e:
            self.logger.error(f"Error generating initial trade history: {str(e)}")
            # Don't raise - this is optional demonstration data
    
    def get_portfolio_data(self) -> Dict:
        """Get complete portfolio data from OKX simulation for all 103 cryptocurrencies."""
        try:
            # Use ONLY OKX simulation - no external API calls
            holdings = []
            total_value = 0
            total_initial_value = 0
            
            # Get actual positions from the exchange
            positions_response = self.exchange.get_positions()
            actual_positions = {pos['instId'].replace('-USDT-SWAP', ''): pos 
                             for pos in positions_response.get('data', [])}
            
            for rank, symbol in enumerate(PORTFOLIO_ASSETS, 1):
                try:
                    # Get current price from OKX simulation only
                    current_price = self.exchange._get_current_price(f"{symbol}/USDT")
                    
                    if current_price and current_price > 0:
                        initial_investment = 10.0  # $10 per crypto
                        
                        # Check if we have an actual position from trades
                        if symbol in actual_positions:
                            actual_position = actual_positions[symbol]
                            quantity = float(actual_position['pos'])
                            avg_price = float(actual_position['avgPx'])
                            current_value = quantity * current_price
                            cost_basis = quantity * avg_price
                            pnl = current_value - cost_basis
                            pnl_percent = (pnl / cost_basis) * 100 if cost_basis > 0 else 0
                            
                            # Mark as live position
                            has_position = True
                            
                        else:
                            # Check if this position has been fully sold (has trading history but no current position)
                            has_trading_history = any(
                                trade.get('instId', '').replace('-USDT-SWAP', '') == symbol 
                                for trade in self.exchange.trades
                            )
                            
                            if has_trading_history:
                                # Position was sold - show zero holdings
                                quantity = 0.0
                                current_value = 0.0
                                pnl = -initial_investment  # Show full loss if position sold
                                pnl_percent = -100.0
                                has_position = False
                                
                            else:
                                # Use simulated historical purchase price for assets without real positions
                                price_variation = (hash(symbol) % 20 - 10) / 100.0  # -10% to +10% variation
                                historical_purchase_price = current_price * (1 - price_variation)
                                
                                # Calculate quantity based on historical purchase price
                                quantity = initial_investment / historical_purchase_price
                                current_value = quantity * current_price
                                
                                # Calculate P&L based on price movement from purchase to now
                                pnl = current_value - initial_investment
                                pnl_percent = (pnl / initial_investment) * 100
                                has_position = True
                        
                        holdings.append({
                            "rank": rank,
                            "symbol": symbol,
                            "name": symbol,
                            "quantity": round(quantity, 8),
                            "current_price": current_price,
                            "value": current_value,
                            "current_value": current_value,
                            "pnl": pnl,
                            "pnl_percent": pnl_percent,
                            "is_live": True,  # All OKX prices are simulated "live"
                            "has_position": has_position  # Track real vs simulated positions
                        })
                        
                        total_value += current_value
                        total_initial_value += initial_investment
                    else:
                        # Fallback price if OKX simulation doesn't have this symbol
                        current_price = 1.0
                        initial_investment = 10.0
                        quantity = initial_investment / current_price
                        current_value = quantity * current_price
                        
                        holdings.append({
                            "rank": rank,
                            "symbol": symbol,
                            "name": symbol,
                            "quantity": round(quantity, 8),
                            "current_price": current_price,
                            "value": current_value,
                            "current_value": current_value,
                            "pnl": 0.0,
                            "pnl_percent": 0.0,
                            "is_live": False
                        })
                        
                        total_value += current_value
                        total_initial_value += initial_investment
                        
                except Exception as e:
                    self.logger.warning(f"Failed to get price for {symbol} from OKX: {str(e)}")
                    # Use fallback
                    holdings.append({
                        "rank": rank,
                        "symbol": symbol,
                        "name": symbol,
                        "quantity": 10.0,
                        "current_price": 1.0,
                        "value": 10.0,
                        "current_value": 10.0,
                        "pnl": 0.0,
                        "pnl_percent": 0.0,
                        "is_live": False
                    })
                    total_value += 10.0
                    total_initial_value += 10.0
            
            total_pnl = total_value - total_initial_value
            total_pnl_percent = (total_pnl / total_initial_value) * 100 if total_initial_value > 0 else 0
            
            # Additional portfolio metadata
            cash_balance = 100000 - total_initial_value  # Start with $100k, subtract investments
            
            return {
                "holdings": holdings,
                "total_current_value": total_value,
                "total_pnl": total_pnl,
                "total_pnl_percent": total_pnl_percent,
                "cash_balance": cash_balance,
                "last_update": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"OKX Portfolio data error: {str(e)}")
            return {
                "holdings": [],
                "total_current_value": 1030.0,  # 103 * $10 fallback
                "total_pnl": 0,
                "total_pnl_percent": 0,
                "cash_balance": 98970.0,  # $100k - $1030
                "last_update": datetime.now().isoformat()
            }
    
    def _convert_to_app_format(self, positions: List[Dict]) -> List[Dict]:
        """Convert OKX position format to app format."""
        holdings = []
        
        # Create holdings list from positions
        for position in positions:
            try:
                symbol = position['instId'].replace('-USDT-SWAP', '')
                quantity = float(position['pos'])
                avg_price = float(position['avgPx'])
                current_price = float(position['markPx'])
                
                # Calculate values
                current_value = quantity * current_price
                cost_basis = quantity * avg_price
                pnl = current_value - cost_basis
                pnl_percent = (pnl / cost_basis) * 100 if cost_basis > 0 else 0
                
                # Find asset info
                asset_info = next((a for a in PORTFOLIO_ASSETS if a['symbol'] == symbol), None)
                asset_name = asset_info['name'] if asset_info else symbol
                asset_rank = asset_info['rank'] if asset_info else 999
                
                holding = {
                    'symbol': symbol,
                    'name': asset_name,
                    'rank': asset_rank,
                    'quantity': quantity,
                    'current_price': current_price,
                    'avg_price': avg_price,
                    'current_value': current_value,
                    'value': cost_basis,  # Initial investment value
                    'pnl': pnl,
                    'pnl_percent': pnl_percent,
                    'is_live': True,
                    'exchange_position': position  # Include raw OKX data
                }
                
                holdings.append(holding)
                
            except Exception as e:
                self.logger.error(f"Error converting position {position}: {str(e)}")
                continue
        
        # Sort by rank
        holdings.sort(key=lambda x: x['rank'])
        
        return holdings
    
    def _calculate_total_pnl_percent(self, holdings: List[Dict]) -> float:
        """Calculate total P&L percentage across all holdings."""
        total_cost = sum(h.get('value', 0) for h in holdings)
        total_pnl = sum(h.get('pnl', 0) for h in holdings)
        
        return (total_pnl / total_cost) * 100 if total_cost > 0 else 0
    
    def place_trade(self, symbol: str, side: str, amount: float, order_type: str = 'market') -> Dict:
        """Place a trade through the exchange."""
        if not self.exchange.is_connected():
            raise Exception("Exchange not connected")
        
        try:
            # Format symbol for OKX
            trading_pair = f"{symbol}/USDT"
            
            # Place order
            result = self.exchange.place_order(
                symbol=trading_pair,
                side=side,
                amount=amount,
                order_type=order_type
            )
            
            self.logger.info(f"Trade executed: {side} {amount} {symbol}")
            return result
            
        except Exception as e:
            self.logger.error(f"Trade execution failed: {str(e)}")
            raise
    
    def get_trade_history(self, symbol: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get trade history from the exchange."""
        if not self.exchange.is_connected():
            raise Exception("Exchange not connected")
        
        try:
            # Get trades from exchange
            if hasattr(self.exchange, 'trade_history') and self.exchange.trade_history:
                trades = self.exchange.trade_history
                
                # Filter by symbol if provided
                if symbol:
                    symbol_filter = f"{symbol}-USDT-SWAP"
                    trades = [t for t in trades if t['instId'] == symbol_filter]
                
                # Sort by timestamp (newest first) and limit
                trades = sorted(trades, key=lambda x: int(x['ts']), reverse=True)[:limit]
                
                # Convert to app format
                formatted_trades = []
                for trade in trades:
                    formatted_trade = {
                        'id': trade['ordId'],
                        'symbol': trade['instId'].replace('-USDT-SWAP', ''),
                        'side': trade['side'].upper(),
                        'quantity': float(trade['fillSz']),
                        'price': float(trade['fillPx']),
                        'timestamp': datetime.fromtimestamp(int(trade['ts']) / 1000).isoformat(),
                        'fee': float(trade.get('fee', 0)),
                        'fee_currency': trade.get('feeCcy', 'USDT'),
                        'total_value': float(trade['fillSz']) * float(trade['fillPx']),
                        'exchange_data': trade
                    }
                    formatted_trades.append(formatted_trade)
                
                return formatted_trades
            else:
                return []
            
        except Exception as e:
            self.logger.error(f"Error getting trade history: {str(e)}")
            return []
    
    def get_exchange_status(self) -> Dict:
        """Get exchange connection and status information."""
        return {
            'connected': self.exchange.is_connected(),
            'initialized': self.is_initialized,
            'last_sync': self._last_sync.isoformat() if self._last_sync else None,
            'exchange_type': 'Simulated OKX',
            'market_open': getattr(self.exchange, 'market_open', True),
            'balance_summary': self._get_balance_summary()
        }
    
    def _get_balance_summary(self) -> Dict:
        """Get simplified balance summary."""
        try:
            if self.exchange.is_connected():
                balance = self.exchange.get_balance()
                portfolio = self.exchange.get_portfolio_summary()
                
                return {
                    'cash_balance': float(balance['data'][0]['availBal']),
                    'total_equity': float(portfolio['data']['totalEq']),
                    'currency': 'USDT'
                }
            else:
                return {'error': 'Exchange not connected'}
                
        except Exception as e:
            return {'error': str(e)}
    
    def reset_portfolio(self) -> bool:
        """Reset portfolio to initial state (useful for testing)."""
        try:
            self.logger.info("Resetting portfolio to initial state...")
            
            # Reinitialize exchange
            self.exchange = SimulatedOKX(self.exchange.config)
            self._initialize_exchange()
            
            self.logger.info("Portfolio reset successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Portfolio reset failed: {str(e)}")
            return False


# Global portfolio service instance
_portfolio_service = None

def get_portfolio_service() -> PortfolioService:
    """Get the global portfolio service instance."""
    global _portfolio_service
    if _portfolio_service is None:
        _portfolio_service = PortfolioService()
    return _portfolio_service