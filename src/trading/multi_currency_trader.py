"""
Multi-Currency Enhanced Trading System
Supports automatic trading across multiple cryptocurrencies with universal rebuy mechanism.
"""

import logging
import time
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

from .enhanced_trader import EnhancedTrader
from ..config import Config
from ..exchanges.base import BaseExchange


class MultiCurrencyTrader:
    """Enhanced trader that supports multiple cryptocurrencies with universal rebuy."""
    
    def __init__(self, config: Config, exchange: BaseExchange):
        self.config = config
        self.exchange = exchange
        self.logger = logging.getLogger(__name__)
        
        # Supported trading pairs
        self.trading_pairs = [
            'BTC/USDT', 'PEPE/USDT', 'ETH/USDT', 'DOGE/USDT', 
            'ADA/USDT', 'SOL/USDT', 'XRP/USDT', 'AVAX/USDT'
        ]
        
        # Individual traders for each pair
        self.traders: Dict[str, EnhancedTrader] = {}
        self.running = False
        self.threads: List[threading.Thread] = []
        
        # Initialize traders for each pair
        for pair in self.trading_pairs:
            trader = EnhancedTrader(config, exchange)
            # Ensure rebuy mechanism applies universally
            trader.strategy.rebuy_max_usd = config.get_float('strategy', 'rebuy_max_usd', 100.0)
            self.traders[pair] = trader
            
        self.logger.info(f"Multi-currency trader initialized for {len(self.trading_pairs)} pairs")
        self.logger.info(f"Universal rebuy limit: ${config.get_float('strategy', 'rebuy_max_usd', 100.0):.2f}")
    
    def start_trading(self, timeframe: str = '1h') -> None:
        """Start trading across all supported cryptocurrencies."""
        if self.running:
            self.logger.warning("Multi-currency trading already running")
            return
            
        self.running = True
        self.logger.info("Starting multi-currency trading with universal rebuy mechanism")
        
        # Start a thread for each trading pair with staggered delays to prevent OKX rate limiting
        for i, pair in enumerate(self.trading_pairs):
            thread = threading.Thread(
                target=self._trade_pair,
                args=(pair, timeframe, i * 2),  # Add delay parameter 
                name=f"Trader-{pair.replace('/', '-')}"
            )
            thread.daemon = True
            thread.start()
            self.threads.append(thread)
            
        self.logger.info(f"Started {len(self.threads)} trading threads")
    
    def _trade_pair(self, pair: str, timeframe: str, delay: int = 0) -> None:
        """Trade a specific cryptocurrency pair."""
        if delay > 0:
            self.logger.info(f"Delaying {pair} startup by {delay} seconds to prevent API rate limiting")
            time.sleep(delay)
            
        trader = self.traders[pair]
        try:
            self.logger.info(f"Starting trading for {pair}")
            trader.start_trading(pair, timeframe)
        except Exception as e:
            self.logger.error(f"Error trading {pair}: {e}")
        finally:
            self.logger.info(f"Stopped trading for {pair}")
    
    def stop_trading(self) -> None:
        """Stop all trading activity."""
        if not self.running:
            return
            
        self.logger.info("Stopping multi-currency trading")
        self.running = False
        
        # Stop all individual traders
        for pair, trader in self.traders.items():
            try:
                trader.stop_trading()
                self.logger.info(f"Stopped trader for {pair}")
            except Exception as e:
                self.logger.error(f"Error stopping trader for {pair}: {e}")
        
        # Wait for threads to finish
        for thread in self.threads:
            thread.join(timeout=10)
        
        self.threads.clear()
        self.logger.info("Multi-currency trading stopped")
    
    def get_status(self) -> Dict:
        """Get status of all trading pairs."""
        status = {
            'running': self.running,
            'pairs': {},
            'rebuy_armed_count': 0,
            'active_positions': 0
        }
        
        for pair, trader in self.traders.items():
            pair_status = {
                'running': trader.running,
                'rebuy_armed': False,
                'position_qty': 0.0,
                'last_update': None
            }
            
            if hasattr(trader.strategy, 'position_state'):
                state = trader.strategy.position_state
                pair_status.update({
                    'rebuy_armed': state.get('rebuy_armed', False),
                    'position_qty': state.get('position_qty', 0.0),
                    'rebuy_price': state.get('rebuy_price', 0.0)
                })
                
                if state.get('rebuy_armed', False):
                    status['rebuy_armed_count'] += 1
                
                if state.get('position_qty', 0.0) > 0:
                    status['active_positions'] += 1
            
            if trader.last_update_time:
                pair_status['last_update'] = trader.last_update_time.isoformat()
            
            status['pairs'][pair] = pair_status
        
        return status
    
    def get_rebuy_opportunities(self) -> List[Dict]:
        """Get list of cryptocurrencies with armed rebuy mechanisms."""
        opportunities = []
        
        for pair, trader in self.traders.items():
            if hasattr(trader.strategy, 'position_state'):
                state = trader.strategy.position_state
                if state.get('rebuy_armed', False):
                    opportunities.append({
                        'pair': pair,
                        'rebuy_price': state.get('rebuy_price', 0.0),
                        'max_purchase': trader.strategy.rebuy_max_usd,
                        'ready_at': state.get('rebuy_ready_at'),
                        'mode': trader.strategy.rebuy_mode
                    })
        
        return opportunities