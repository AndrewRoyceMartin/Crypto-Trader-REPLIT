"""
Multi-Currency Enhanced Trading System
Supports automatic trading across multiple cryptocurrencies with universal rebuy mechanism.
"""

import logging
import threading
import time

from ..config import Config
from ..exchanges.base import BaseExchange
from .confidence_trader import get_confidence_trader
from .enhanced_trader import EnhancedTrader


class MultiCurrencyTrader:
    """Enhanced trader that supports multiple cryptocurrencies with universal rebuy."""

    def __init__(self, config: Config, exchange: BaseExchange):
        self.config = config
        self.exchange = exchange
        self.logger = logging.getLogger(__name__)

        # Get dynamic trading pairs from available positions
        self.trading_pairs = self._get_available_trading_pairs()

        # Fallback to core pairs if API fails
        if not self.trading_pairs:
            self.trading_pairs = [
                'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'ADA/USDT',
                'DOGE/USDT', 'XRP/USDT', 'AVAX/USDT', 'PEPE/USDT'
            ]
            self.logger.warning("Using fallback trading pairs due to API error")

        # Individual traders for each pair
        self.traders: dict[str, EnhancedTrader] = {}
        self.running = False
        self.threads: list[threading.Thread] = []

        # Initialize confidence-based trader for hybrid approach
        self.confidence_trader = get_confidence_trader(config)
        self.confidence_scan_interval = 300  # 5 minutes between confidence scans

        # Initialize traders for each pair
        for pair in self.trading_pairs:
            trader = EnhancedTrader(config, exchange)
            # Ensure rebuy mechanism applies universally
            trader.strategy.rebuy_max_usd = config.get_float('strategy', 'rebuy_max_usd', 100.0)
            self.traders[pair] = trader

        self.logger.info(f"Multi-currency trader initialized for {len(self.trading_pairs)} pairs: {', '.join(self.trading_pairs)}")
        self.logger.info(f"Universal rebuy limit: ${config.get_float('strategy', 'rebuy_max_usd', 100.0):.2f}")
        self.logger.info("🤖 HYBRID SYSTEM: Enhanced Bollinger Bands + Confidence-Based Auto-Purchasing ENABLED")

    def _get_available_trading_pairs(self) -> list[str]:
        """Get trading pairs dynamically from available positions with tradeable assets."""
        try:
            # Import here to avoid circular imports
            from ..services.portfolio_service import PortfolioService

            # Create portfolio service to get available assets
            PortfolioService(self.exchange)

            # Get all available cryptocurrencies (excluding fiat/stablecoins)
            available_pairs = []

            # Major cryptocurrencies that are typically tradeable on OKX
            crypto_assets = [
                'BTC', 'ETH', 'SOL', 'ADA', 'DOT', 'AVAX', 'MATIC', 'LINK', 'UNI', 'LTC',
                'BCH', 'XLM', 'ALGO', 'ATOM', 'ICP', 'FTM', 'NEAR', 'SAND', 'MANA', 'CRO',
                'APE', 'GALA', 'TRX', 'PEPE', 'SHIB', 'DOGE', 'XRP', 'BNB', 'FTT', 'AXS',
                'ENJ', 'CHZ', 'BAT', 'ZEC', 'ETC', 'DASH', 'THETA', 'VET', 'HOT', 'OMG',
                'ZIL', 'ICX', 'REP', 'KNC', 'REN', 'LRC', 'STORJ', 'GRT', 'COMP', 'MKR',
                'YFI', 'SUSHI', 'SNX', 'AAVE', 'CRV', 'BAL', '1INCH', 'RUNE', 'ALPHA',
                'PERP', 'DYDX', 'IMX', 'API3', 'AUDIO', 'CTX'
            ]

            # Create trading pairs for available cryptocurrencies
            for asset in crypto_assets:
                pair = f"{asset}/USDT"
                try:
                    # Verify pair exists on exchange and has recent trading volume
                    if self.exchange and hasattr(self.exchange, 'exchange'):
                        markets = self.exchange.exchange.load_markets()
                        if pair in markets:
                            market_info = markets[pair]
                            # Check if market is active and has reasonable volume
                            if market_info.get('active', True):
                                available_pairs.append(pair)
                except Exception as pair_error:
                    self.logger.debug(f"Skipping {pair}: {pair_error}")
                    continue

            # Prioritize major coins first, then others
            major_coins = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'ADA/USDT', 'DOGE/USDT', 'XRP/USDT', 'AVAX/USDT', 'PEPE/USDT']
            prioritized_pairs = []

            # Add major coins first
            for major in major_coins:
                if major in available_pairs:
                    prioritized_pairs.append(major)

            # Add remaining pairs
            for pair in available_pairs:
                if pair not in prioritized_pairs:
                    prioritized_pairs.append(pair)

            # Limit to reasonable number for performance
            max_pairs = self.config.get_int('trading', 'max_trading_pairs', 20)
            final_pairs = prioritized_pairs[:max_pairs]

            self.logger.info(f"Dynamically found {len(final_pairs)} trading pairs from {len(crypto_assets)} possible assets")
            return final_pairs

        except Exception as e:
            self.logger.error(f"Error getting dynamic trading pairs: {e}")
            return []  # Return empty list to trigger fallback

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

        # Start confidence-based trading thread (hybrid approach)
        confidence_thread = threading.Thread(
            target=self._run_confidence_scanner,
            name="ConfidenceScanner"
        )
        confidence_thread.daemon = True
        confidence_thread.start()
        self.threads.append(confidence_thread)

        self.logger.info(f"Started {len(self.threads)} trading threads (including confidence scanner)")
        self.logger.critical("🚀 HYBRID TRADING SYSTEM ACTIVE: Bollinger Bands + Confidence Auto-Purchasing")

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

    def get_status(self) -> dict:
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

    def get_rebuy_opportunities(self) -> list[dict]:
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

    def _run_confidence_scanner(self) -> None:
        """Run confidence-based scanning for automatic purchases in background."""
        self.logger.info("🔍 Confidence scanner thread started - scanning for CAUTIOUS_BUY/STRONG_BUY signals")
        last_scan_time = time.time()

        while self.running:
            try:
                current_time = time.time()

                # Run confidence scan every scan interval (5 minutes)
                if current_time - last_scan_time >= self.confidence_scan_interval:
                    self.logger.info("🎯 Running confidence-based opportunity scan...")

                    opportunities_found, purchases_executed = self.confidence_trader.run_confidence_scan_cycle()

                    if opportunities_found > 0:
                        self.logger.info(
                            "📈 CONFIDENCE SCAN RESULTS: %d opportunities found, %d purchases executed",
                            opportunities_found, purchases_executed
                        )

                    last_scan_time = current_time

                # Sleep for 30 seconds before checking again
                time.sleep(30)

            except Exception as e:
                self.logger.error("Error in confidence scanner: %s", e)
                # Wait longer on error to avoid spam
                time.sleep(60)

        self.logger.info("🔍 Confidence scanner thread stopped")
