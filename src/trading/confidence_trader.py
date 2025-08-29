"""
Confidence-based trader that automatically executes purchases based on UI confidence signals.
This creates a hybrid approach using both confidence analysis AND Enhanced Bollinger Bands strategy.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from ..utils.entry_confidence import get_confidence_analyzer
from ..services.portfolio_service import get_portfolio_service
from ..utils.okx_native import OKXNative
from ..config import Config


class ConfidenceBasedTrader:
    """
    Hybrid trader that combines confidence analysis with traditional trading signals.
    Automatically executes purchases when assets show strong confidence signals.
    """

    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.confidence_analyzer = get_confidence_analyzer()
        self.okx_client = OKXNative.from_env()
        
        # Trading parameters respecting $100 rebuy limit from replit.md
        self.max_purchase_amount = 100.0  # Universal $100 maximum as per user preferences
        self.min_confidence_for_cautious = 60.0  # CAUTIOUS_BUY threshold
        self.min_confidence_for_strong = 85.0    # STRONG_BUY threshold
        
        # Cooldown to prevent rapid repeated purchases
        self.purchase_cooldown_minutes = 30
        self.last_purchase_times: Dict[str, datetime] = {}
        
        self.logger.info("Confidence-based trader initialized with $%.2f purchase limit", self.max_purchase_amount)

    def scan_for_confidence_opportunities(self) -> List[Dict[str, Any]]:
        """
        Scan all available assets for confidence-based buying opportunities.
        Returns list of assets meeting confidence criteria.
        """
        try:
            portfolio_service = get_portfolio_service()
            
            # Get current portfolio to avoid buying assets we already own
            portfolio_data = portfolio_service.get_portfolio_data()
            current_holdings = {h.get('symbol', '') for h in portfolio_data.get('holdings', [])}
            
            # Get available positions data (similar to UI endpoint logic)
            exchange = portfolio_service.exchange
            if not exchange or not exchange.is_connected():
                self.logger.warning("Exchange not connected, cannot scan for opportunities")
                return []
            
            # Safely access exchange balance data
            try:
                balance_data = exchange.exchange.fetch_balance() if exchange.exchange else {}
            except Exception as e:
                self.logger.error("Error fetching balance data: %s", e)
                return []
            
            # Comprehensive list of major cryptocurrencies (same as available-positions endpoint)
            major_crypto_assets = [
                'BTC', 'ETH', 'SOL', 'ADA', 'AVAX', 'LINK', 'UNI', 'LTC', 'XRP',
                'DOGE', 'MATIC', 'ATOM', 'DOT', 'NEAR', 'SHIB', 'BNB', 'BCH', 
                'XLM', 'ALGO', 'ICP', 'SAND', 'MANA', 'CRO', 'APE', 'AXS', 
                'CHZ', 'THETA', 'GRT', 'COMP', 'MKR', 'YFI', 'SUSHI', 'AAVE', 
                'CRV', 'TON', 'FIL', 'OP', 'ARB', 'LDO', 'FET', 'INJ'
            ]
            
            opportunities = []
            
            for symbol in major_crypto_assets:
                try:
                    # Skip if we already hold this asset
                    if symbol in current_holdings:
                        self.logger.debug("Skipping %s - already owned", symbol)
                        continue
                    
                    # Skip stablecoins and fiat
                    if symbol in ['USDT', 'USDC', 'DAI', 'BUSD', 'AUD', 'USD', 'EUR', 'GBP']:
                        continue
                    
                    # Check if we're in cooldown for this asset
                    if self._is_in_cooldown(symbol):
                        continue
                    
                    # Get current balance (should be zero for available positions)
                    balance_info = balance_data.get(symbol, {'total': 0})
                    current_balance = float(balance_info.get('total', 0) or 0)
                    
                    if current_balance > 0:
                        continue  # Skip if we have existing balance
                    
                    # Get current price
                    current_price = portfolio_service._get_live_okx_price(symbol)
                    if not current_price or current_price <= 0:
                        continue
                    
                    # Calculate confidence score
                    confidence_data = self.confidence_analyzer.calculate_confidence(symbol, current_price)
                    confidence_score = confidence_data['confidence_score']
                    timing_signal = confidence_data['timing_signal']
                    
                    # Check if confidence meets our criteria
                    if timing_signal in ['CAUTIOUS_BUY', 'STRONG_BUY', 'BUY']:
                        opportunity = {
                            'symbol': symbol,
                            'current_price': current_price,
                            'confidence_score': confidence_score,
                            'timing_signal': timing_signal,
                            'confidence_data': confidence_data,
                            'recommended_amount': self._calculate_purchase_amount(confidence_score, timing_signal)
                        }
                        opportunities.append(opportunity)
                        
                        self.logger.info(
                            "🎯 CONFIDENCE OPPORTUNITY: %s at $%.4f - %s (Score: %.1f)",
                            symbol, current_price, timing_signal, confidence_score
                        )
                
                except Exception as asset_error:
                    self.logger.debug("Error analyzing %s: %s", symbol, asset_error)
                    continue
            
            return opportunities
            
        except Exception as e:
            self.logger.error("Error scanning for confidence opportunities: %s", e)
            return []

    def _calculate_purchase_amount(self, confidence_score: float, timing_signal: str) -> float:
        """
        Calculate recommended purchase amount based on confidence level.
        Always respects the $100 maximum limit.
        """
        base_amount = self.max_purchase_amount
        
        # Adjust amount based on confidence level
        if timing_signal == 'STRONG_BUY':
            # Use full amount for strong signals
            return base_amount
        elif timing_signal == 'BUY':
            # Use 75% for regular buy signals
            return base_amount * 0.75
        elif timing_signal == 'CAUTIOUS_BUY':
            # Use 50% for cautious signals
            return base_amount * 0.50
        else:
            # Default to minimal amount
            return base_amount * 0.25

    def _is_in_cooldown(self, symbol: str) -> bool:
        """Check if symbol is in purchase cooldown period."""
        if symbol not in self.last_purchase_times:
            return False
        
        last_purchase = self.last_purchase_times[symbol]
        cooldown_end = last_purchase.replace(tzinfo=timezone.utc) + timedelta(minutes=self.purchase_cooldown_minutes)
        
        return datetime.now(timezone.utc) < cooldown_end

    def execute_confidence_purchase(self, symbol: str, amount_usd: float, confidence_data: Dict[str, Any]) -> bool:
        """
        Execute a purchase based on confidence signal.
        Returns True if successful, False otherwise.
        """
        try:
            # CRITICAL SAFETY CHECKS - Respect $100 universal limit from replit.md
            if amount_usd > self.max_purchase_amount:
                self.logger.warning(
                    "🚨 PURCHASE LIMIT ENFORCED: Amount $%.2f exceeds universal limit $%.2f for %s", 
                    amount_usd, self.max_purchase_amount, symbol
                )
                amount_usd = self.max_purchase_amount
            
            if amount_usd < 5.0:  # Minimum order size check
                self.logger.warning("🚨 MINIMUM ORDER SIZE: Purchase amount $%.2f too small for %s (min $5.00)", amount_usd, symbol)
                return False
            
            # Check available USDT balance for purchase
            try:
                portfolio_service = get_portfolio_service()
                exchange = portfolio_service.exchange
                if exchange and exchange.is_connected() and exchange.exchange:
                    balance_data = exchange.exchange.fetch_balance()
                    usdt_balance = float(balance_data.get('USDT', {}).get('free', 0) or 0)
                    
                    if usdt_balance < amount_usd:
                        self.logger.warning(
                            "🚨 INSUFFICIENT FUNDS: USDT balance $%.2f insufficient for %s purchase $%.2f",
                            usdt_balance, symbol, amount_usd
                        )
                        return False
                    
                    # Ensure we leave some buffer (minimum $10 USDT)
                    if usdt_balance - amount_usd < 10.0:
                        available_amount = max(5.0, usdt_balance - 10.0)
                        if available_amount >= 5.0:
                            self.logger.info(
                                "💰 BALANCE OPTIMIZATION: Adjusting purchase from $%.2f to $%.2f to maintain $10 USDT buffer",
                                amount_usd, available_amount
                            )
                            amount_usd = available_amount
                        else:
                            self.logger.warning("🚨 INSUFFICIENT BUFFER: Not enough USDT to maintain minimum balance")
                            return False
                            
            except Exception as balance_error:
                self.logger.error("Error checking USDT balance: %s", balance_error)
                # Continue with purchase anyway - let OKX reject if insufficient funds
                pass
            
            # Get current price and calculate quantity
            current_price = confidence_data.get('current_price', 0)
            if not current_price:
                # Refresh price
                portfolio_service = get_portfolio_service()
                current_price = portfolio_service._get_live_okx_price(symbol)
                
            if not current_price or current_price <= 0:
                self.logger.error("Cannot get valid price for %s", symbol)
                return False
            
            quantity = amount_usd / current_price
            
            # Execute purchase via exchange adapter (same method as enhanced trader)
            trading_symbol = f"{symbol}/USDT"
            
            self.logger.info(
                "🚀 EXECUTING CONFIDENCE PURCHASE: %.6f %s at $%.4f (Total: $%.2f) - %s",
                quantity, symbol, current_price, amount_usd, confidence_data['timing_signal']
            )
            
            # Get the exchange adapter from portfolio service for proper authentication
            portfolio_service = get_portfolio_service()
            live_exchange = portfolio_service.exchange
            
            if not live_exchange:
                self.logger.error("Cannot get exchange adapter for trading")
                return False
            
            # Place market buy order using simple place_order method (same as enhanced trader)
            order_response = live_exchange.place_order(trading_symbol, 'buy', quantity, 'market')
            
            if order_response and order_response.get('id'):
                order_id = order_response['id']
                
                # Record purchase time for cooldown
                self.last_purchase_times[symbol] = datetime.now(timezone.utc)
                
                self.logger.critical(
                    "✅ CONFIDENCE PURCHASE EXECUTED: %s - Order ID: %s - Amount: $%.2f - Signal: %s",
                    symbol, order_id, amount_usd, confidence_data['timing_signal']
                )
                
                return True
            else:
                error_msg = order_response.get('msg', 'Unknown error') if order_response else 'No response'
                self.logger.error("❌ CONFIDENCE PURCHASE FAILED: %s - %s", symbol, error_msg)
                return False
                
        except Exception as e:
            self.logger.error("Error executing confidence purchase for %s: %s", symbol, e)
            return False

    def run_confidence_scan_cycle(self) -> Tuple[int, int]:
        """
        Run one cycle of confidence-based scanning and purchasing.
        Returns (opportunities_found, purchases_executed).
        """
        try:
            self.logger.info("🔍 Starting confidence-based opportunity scan...")
            
            opportunities = self.scan_for_confidence_opportunities()
            opportunities_found = len(opportunities)
            purchases_executed = 0
            
            if not opportunities:
                self.logger.debug("No confidence opportunities found this cycle")
                return 0, 0
            
            # Sort opportunities by confidence score (highest first)
            opportunities.sort(key=lambda x: x['confidence_score'], reverse=True)
            
            # Execute purchases for top opportunities
            max_purchases_per_cycle = 3  # Limit to prevent too many simultaneous purchases
            
            for i, opportunity in enumerate(opportunities[:max_purchases_per_cycle]):
                symbol = opportunity['symbol']
                amount = opportunity['recommended_amount']
                
                self.logger.info(
                    "📊 OPPORTUNITY %d/%d: %s - Score: %.1f - Signal: %s - Amount: $%.2f",
                    i + 1, min(len(opportunities), max_purchases_per_cycle),
                    symbol, opportunity['confidence_score'], 
                    opportunity['timing_signal'], amount
                )
                
                # Execute purchase
                if self.execute_confidence_purchase(symbol, amount, opportunity):
                    purchases_executed += 1
                    # Small delay between purchases to avoid overwhelming the exchange
                    time.sleep(2)
                else:
                    self.logger.warning("Failed to execute purchase for %s", symbol)
            
            self.logger.info(
                "🎯 CONFIDENCE SCAN COMPLETE: %d opportunities found, %d purchases executed",
                opportunities_found, purchases_executed
            )
            
            return opportunities_found, purchases_executed
            
        except Exception as e:
            self.logger.error("Error in confidence scan cycle: %s", e)
            return 0, 0


# Global instance for integration with existing system
_confidence_trader = None

def get_confidence_trader(config: Optional[Config] = None) -> ConfidenceBasedTrader:
    """Get singleton confidence trader instance."""
    global _confidence_trader
    if _confidence_trader is None:
        if config is None:
            # Import here to avoid circular imports
            from ..config import Config
            config = Config()
        _confidence_trader = ConfidenceBasedTrader(config)
    return _confidence_trader