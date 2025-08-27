"""
Market Data Service
Handles price fetching, market analysis, and technical indicators
"""
from typing import Dict, Any, Optional, Tuple
import logging
import os

logger = logging.getLogger(__name__)

class MarketDataService:
    """Business logic for market data and price operations."""
    
    def __init__(self):
        self.logger = logger
    
    def get_live_price(self, symbol: str, base_currency: str = "USDT") -> float:
        """Get live price for a trading pair using multiple fallback methods."""
        pair = f"{symbol}/{base_currency}"
        
        try:
            # Try OKX native client first
            from src.utils.okx_native import OKXNative
            client = OKXNative.from_env()
            
            # Convert to OKX format
            okx_pair = f"{symbol}-{base_currency}"
            ticker_data = client.ticker(okx_pair)
            
            if ticker_data and 'last' in ticker_data:
                price = float(ticker_data['last'])
                if price > 0:
                    return price
                    
        except Exception as e:
            self.logger.debug(f"OKX native price fetch failed for {pair}: {e}")
        
        # Fallback to portfolio service exchange
        try:
            from src.services.portfolio_service import get_portfolio_service
            service = get_portfolio_service()
            
            if (service and hasattr(service, 'exchange') 
                    and hasattr(service.exchange, 'exchange')
                    and service.exchange.exchange):
                service.exchange.exchange.timeout = 8000
                ticker: Dict[str, Any] = service.exchange.exchange.fetch_ticker(pair)
                price = float(ticker.get('last') or 0)
                if price > 0:
                    return price
                    
        except Exception as e:
            self.logger.debug(f"CCXT price fetch failed for {pair}: {e}")
        
        return 0.0
    
    def calculate_bollinger_bands_analysis(self, symbol: str, current_price: float) -> Dict[str, Any]:
        """Calculate Bollinger Bands analysis for entry opportunity assessment."""
        try:
            from src.utils.okx_native import OKXNative
            okx_client = OKXNative.from_env()
            
            # Get 100 daily candles for BB calculation
            symbol_pair = f"{symbol}-USDT"
            candles = okx_client.candles(symbol_pair, bar="1D", limit=100)
            
            if candles and len(candles) >= 50:
                import pandas as pd
                from src.indicators.technical import TechnicalIndicators
                
                # Convert to DataFrame
                if not candles or len(candles[0]) < 5:
                    raise ValueError("Invalid candle data structure")
                
                price_data = [[candle[0], candle[1], candle[2], candle[3], candle[4]] for candle in candles]
                df = pd.DataFrame(price_data, columns=['timestamp', 'open', 'high', 'low', 'close'])
                df['close'] = pd.to_numeric(df['close'], errors='coerce')
                
                if df['close'].isna().all():
                    raise ValueError("No valid close price data")
                
                # Calculate Bollinger Bands (20-period, 2.0 std dev)
                indicators = TechnicalIndicators()
                upper_band, middle_band, lower_band = indicators.bollinger_bands(df['close'], period=20, std_dev=2.0)
                
                if len(lower_band) > 0 and not pd.isna(lower_band.iloc[-1]):
                    lower_band_price = float(lower_band.iloc[-1])
                else:
                    raise ValueError("No valid Bollinger Band data calculated")
                
                if lower_band_price > 0:
                    # Calculate distance from current price to lower band
                    bb_distance_percent = ((current_price - lower_band_price) / current_price) * 100
                    
                    # Enhanced signal logic
                    if current_price <= lower_band_price * 1.005:  # Within 0.5% of lower band
                        bb_signal = "STRONG"
                        bb_strategy = self._get_bb_strategy_type(symbol)
                    elif current_price <= lower_band_price * 1.03:  # Within 3% of lower band
                        bb_signal = "MODERATE"
                        bb_strategy = "Conservative"
                    elif current_price <= lower_band_price * 1.08:  # Within 8% of lower band
                        bb_signal = "WEAK"
                        bb_strategy = "Conservative"
                    else:
                        bb_signal = "NO SIGNAL"
                        bb_strategy = "N/A"
                    
                    return {
                        "signal": bb_signal,
                        "strategy": bb_strategy,
                        "lower_band_price": round(lower_band_price, 6),
                        "distance_percent": round(bb_distance_percent, 2)
                    }
                    
        except Exception as e:
            self.logger.debug(f"Bollinger Bands calculation failed for {symbol}: {e}")
        
        return {
            "signal": "NO DATA",
            "strategy": "N/A",
            "lower_band_price": 0,
            "distance_percent": 0
        }
    
    def _get_bb_strategy_type(self, symbol: str) -> str:
        """Determine the BB strategy variant based on asset characteristics."""
        # Large cap assets (conservative approach)
        if symbol in ['BTC', 'ETH', 'BNB', 'XRP', 'ADA', 'SOL', 'DOT', 'LTC']:
            return 'Conservative'
        
        # Meme coins (higher volatility strategy)
        elif symbol in ['DOGE', 'SHIB', 'PEPE', 'BONK', 'WIF', 'FLOKI']:
            return 'Aggressive'
        
        # Stablecoins and fiat (not applicable)
        elif symbol in ['USDT', 'USDC', 'DAI', 'BUSD', 'AUD', 'USD', 'EUR', 'GBP']:
            return 'N/A'
        
        # All other tokens (standard approach)
        else:
            return 'Standard'
    
    def get_target_buy_price(self, symbol: str, current_price: float) -> float:
        """Get a stable, locked target buy price using TargetPriceManager."""
        try:
            if current_price <= 0:
                return current_price
            
            from src.utils.target_price_manager import TargetPriceManager
            target_manager = TargetPriceManager()
            
            # Get or calculate stable target price
            target_price = target_manager.get_target_price(symbol, current_price)
            
            # Ensure target is below current price (buy opportunity)
            if target_price >= current_price:
                # Apply default discount based on asset type
                discount = self._get_default_discount(symbol)
                target_price = current_price * (1 - discount)
                target_manager.set_target_price(symbol, target_price, current_price)
            
            return round(target_price, 8)
            
        except Exception as e:
            self.logger.debug(f"Target price calculation failed for {symbol}: {e}")
            # Fallback to simple discount
            discount = self._get_default_discount(symbol)
            return round(current_price * (1 - discount), 8)
    
    def _get_default_discount(self, symbol: str) -> float:
        """Get default discount percentage based on asset type."""
        # Large cap: 3-8%
        if symbol in ['BTC', 'ETH', 'BNB', 'XRP', 'ADA', 'SOL', 'DOT', 'LTC']:
            return 0.05  # 5%
        
        # Mid cap: 5-12%
        elif symbol in ['AVAX', 'LINK', 'MATIC', 'UNI', 'ATOM', 'FTM']:
            return 0.08  # 8%
        
        # Gaming/Meta: 8-15%
        elif symbol in ['GALA', 'SAND', 'MANA', 'ENJ', 'AXS']:
            return 0.12  # 12%
        
        # Meme coins: 10-20%
        elif symbol in ['DOGE', 'SHIB', 'PEPE', 'BONK', 'WIF', 'FLOKI']:
            return 0.15  # 15%
        
        # Default: 8%
        else:
            return 0.08
    
    def check_exchange_connectivity(self) -> Dict[str, Any]:
        """Check OKX exchange connectivity and status."""
        try:
            okx_api_key = os.getenv("OKX_API_KEY", "")
            okx_secret = os.getenv("OKX_SECRET_KEY", "")
            okx_pass = os.getenv("OKX_PASSPHRASE", "")
            
            if not (okx_api_key and okx_secret and okx_pass):
                return {
                    "status": "error",
                    "api_provider": "OKX_Live_Exchange",
                    "exchange_type": "Live",
                    "error": "OKX API credentials not configured"
                }
            
            from src.exchanges.okx_adapter import OKXAdapter
            config = {
                "sandbox": False,
                "apiKey": okx_api_key,
                "secret": okx_secret,
                "password": okx_pass,
            }
            
            exchange = OKXAdapter(config)
            is_connected = exchange.connect()
            
            return {
                "status": "connected" if is_connected else "disconnected",
                "api_provider": "OKX_Live_Exchange",
                "exchange_type": "Live",
                "symbols_loaded": []  # Could be populated from warmup state
            }
            
        except Exception as e:
            self.logger.error(f"OKX status check error: {e}")
            return {
                "status": "error",
                "api_provider": "OKX_Live_Exchange",
                "error": str(e)
            }