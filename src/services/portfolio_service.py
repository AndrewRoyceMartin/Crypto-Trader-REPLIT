"""
Portfolio Service - Integrates app with Simulated OKX Exchange
Provides a unified interface for portfolio data from the exchange.
"""

import logging
import time
from typing import Dict, List, Optional
from datetime import datetime
from src.exchanges.simulated_okx import SimulatedOKX
from src.data.portfolio_assets import PORTFOLIO_ASSETS


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
        
        # Track initialization state
        self.is_initialized = False
        self._last_sync = None
        
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
            
            for asset in PORTFOLIO_ASSETS:
                symbol = asset['symbol']
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
            
            self.is_initialized = True
            self._last_sync = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Portfolio population failed: {str(e)}")
            raise
    
    def get_portfolio_data(self) -> Dict:
        """Get complete portfolio data from the exchange."""
        if not self.exchange.is_connected():
            raise Exception("Exchange not connected")
        
        try:
            # Get account summary
            portfolio_summary = self.exchange.get_portfolio_summary()
            
            # Get all positions
            positions_response = self.exchange.get_positions()
            
            # Get balance
            balance_response = self.exchange.get_balance()
            
            # Update mark prices
            self.exchange.simulate_market_movement()
            
            # Convert to app format
            holdings = self._convert_to_app_format(positions_response['data'])
            
            return {
                'holdings': holdings,
                'total_current_value': float(portfolio_summary['data']['totalEq']),
                'cash_balance': float(balance_response['data'][0]['availBal']),
                'total_pnl': sum(h.get('pnl', 0) for h in holdings),
                'total_pnl_percent': self._calculate_total_pnl_percent(holdings),
                'last_update': datetime.now().isoformat(),
                'exchange_data': {
                    'balance': balance_response,
                    'positions': positions_response,
                    'summary': portfolio_summary
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting portfolio data: {str(e)}")
            raise
    
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
            # Format symbol for OKX if provided
            trading_pair = f"{symbol}/USDT" if symbol else None
            
            trades_response = self.exchange.get_trades(trading_pair, limit)
            return trades_response['data']
            
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