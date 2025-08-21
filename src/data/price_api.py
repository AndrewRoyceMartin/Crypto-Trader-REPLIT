"""
Real-time cryptocurrency price data integration using CoinGecko API.
Provides live price feeds for accurate portfolio valuation.
"""

import requests
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

class CryptoPriceAPI:
    """Real-time cryptocurrency price data from CoinGecko API."""
    
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.logger = logging.getLogger(__name__)
        self.cache = {}
        self.cache_duration = 300  # Cache for 5 minutes to reduce API calls
        self.last_request_time = 0
        self.request_delay = 60.0  # Rate limit: Check once per minute to avoid API limits
        
        # Price validation and fallback system
        self.last_known_prices = {}  # Store last known good prices with timestamps
        self.connection_status = {
            'connected': True,
            'last_success': datetime.now(),
            'last_error': None,
            'consecutive_failures': 0,
            'warning_issued': False
        }
        self.max_price_age = timedelta(hours=24)  # Maximum age for fallback prices
        
        # CoinGecko coin IDs for our cryptocurrencies
        self.coin_mapping = {
            "BTC": "bitcoin",
            "ETH": "ethereum", 
            "SOL": "solana",
            "XRP": "ripple",
            "DOGE": "dogecoin",
            "BNB": "binancecoin",
            "USDC": "usd-coin",
            "ADA": "cardano",
            "AVAX": "avalanche-2",
            "SHIB": "shiba-inu",
            "DOT": "polkadot",
            "LINK": "chainlink",
            "UNI": "uniswap",
            "MATIC": "matic-network",
            "LTC": "litecoin",
            "BCH": "bitcoin-cash",
            "NEAR": "near",
            "ICP": "internet-computer",
            "LEO": "leo-token",
            "TON": "the-open-network",
            "APT": "aptos",
            "STX": "stacks",
            "ARB": "arbitrum",
            "OP": "optimism",
            "IMX": "immutable-x",
            "MNT": "mantle",
            "HBAR": "hedera-hashgraph",
            "VET": "vechain",
            "ATOM": "cosmos",
            "FIL": "filecoin",
            "THETA": "theta-token",
            "AAVE": "aave",
            "GRT": "the-graph",
            "SUSHI": "sushi",
            "1INCH": "1inch",
            "SAND": "the-sandbox",
            "MANA": "decentraland",
            "AXS": "axie-infinity",
            "FTM": "fantom",
            "ALGO": "algorand",
            "FLOW": "flow",
            "EGLD": "elrond-erd-2",
            "FET": "fetch-ai",
            "LRC": "loopring",
            "ENJ": "enjincoin",
            "CHZ": "chiliz",
            "BAT": "basic-attention-token",
            "XTZ": "tezos",
            "MINA": "mina-protocol",
            "KCS": "kucoin-shares",
            "YFI": "yearn-finance",
            "ZEC": "zcash",
            "DASH": "dash",
            "DCR": "decred",
            "WAVES": "waves",
            "ZIL": "zilliqa",
            "BAL": "balancer",
            "BAND": "band-protocol",
            "OCEAN": "ocean-protocol",
            "UMA": "uma",
            "ALPHA": "alpha-finance",
            "ANKR": "ankr",
            "SKL": "skale",
            "CTSI": "cartesi",
            "CELR": "celer-network",
            "STORJ": "storj",
            "RSR": "reserve-rights-token",
            "REN": "republic-protocol",
            "KNC": "kyber-network",
            "NMR": "numeraire",
            "BNT": "bancor",
            "KAVA": "kava",
            "COTI": "coti",
            "NKN": "nkn",
            "OGN": "origin-protocol",
            "NANO": "nano",
            "RVN": "ravencoin",
            "DGB": "digibyte",
            "SC": "siacoin",
            "HOT": "holotoken",
            "IOST": "iostoken",
            "DUSK": "dusk-network",
            "WIN": "wink",
            "BTT": "bittorrent",
            "TWT": "trust-wallet-token",
            "JST": "just",
            "SXP": "solar",
            "HARD": "kava-lend",
            "SUN": "sun-token",
            "ICX": "icon", 
            "ONT": "ontology",
            # ADDITIONAL MAPPINGS FOR MISSING TOKENS
            "TLM": "alien-worlds",
            "SLP": "smooth-love-potion",
            "GHST": "aavegotchi",
            "ALICE": "my-neighbor-alice",
            "LUNA": "terra-luna-2",
            "ONE": "harmony",
            "CELO": "celo",
            "SCRT": "secret",
            "ROSE": "oasis-network",
            "PEPE": "pepe",
            "FLOKI": "floki",
            "BABYDOGE": "baby-doge-coin",
            "ELON": "dogelon-mars",
            "DOGO": "dogira",
            "AKITA": "akita-inu",
            "KISHU": "kishu-inu",
            "SAITAMA": "saitama-inu",
            "LEASH": "doge-killer",
            "FTT": "ftx-token",
            "HT": "huobi-token",
            "OKB": "okb",
            "CRO": "crypto-com-chain",
            "GT": "gatetoken",
            "BGB": "bitget-token",
            "XMR": "monero",
            "ZCASH": "zcash",
            "BEAM": "beam",
            "GRIN": "grin",
            "FIRO": "firo",
            "ARRR": "pirate-chain",
            "XDC": "xinfin-network",
            "IOTA": "iota",
            "SYS": "syscoin",
            "VTC": "vertcoin",
            "MONA": "monacoin",
            "QNT": "quant-network",
            "QTUM": "qtum",
            "ETC": "ethereum-classic",
            "NEO": "neo",
            "ZRX": "0x",
            "COMP": "compound-governance-token",
            "MKR": "maker",
            "SNX": "havven",
            "CRV": "curve-dao-token",
            "UMA": "uma",
            "ENJN": "enjincoin",
            "GALA": "gala",
            # Additional missing mappings from logs
            "CREAM": "cream-2",
            "BADGER": "badger-dao",
            "LEND": "ethlend",
            "RUNE": "thorchain",
            "CAKE": "pancakeswap-token",
            "BAKE": "bakerytoken",
            "WAX": "wax",
            "ILV": "illuvium",
            "AUDIO": "audius",
            "REVV": "revv",
            "AMP": "amp-token",
            "ZEC": "zcash",
            "XLM": "stellar"
        }
    
    def _rate_limit(self):
        """Enforce rate limiting to respect API limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """DISABLED - Always return False to force live data fetch."""
        return False  # Force live data every time
    
    def get_price(self, symbol: str) -> Optional[float]:
        """Get current price for a single cryptocurrency."""
        cache_key = f"price_{symbol}"
        
        # Return cached data if valid
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['price']
        
        coin_id = self.coin_mapping.get(symbol)
        if not coin_id:
            self.logger.warning(f"No mapping found for symbol: {symbol}")
            return None
        
        try:
            self._rate_limit()
            url = f"{self.base_url}/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            price = data.get(coin_id, {}).get('usd')
            
            if price:
                # Cache the result
                self.cache[cache_key] = {
                    'price': price,
                    'timestamp': time.time()
                }
                self.logger.info(f"Retrieved live price for {symbol}: ${price:.6f}")
                return price
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed for {symbol}: {e}")
        except Exception as e:
            self.logger.error(f"Error getting price for {symbol}: {e}")
        
        return None
    
    def get_connection_status(self) -> Dict:
        """Get current connection status and validation information."""
        return {
            'connected': self.connection_status['connected'],
            'last_success': self.connection_status['last_success'].isoformat(),
            'last_error': self.connection_status.get('last_error'),
            'consecutive_failures': self.connection_status.get('consecutive_failures', 0),
            'warning_issued': self.connection_status.get('warning_issued', False)
        }
    
    def acknowledge_warning(self):
        """Acknowledge price validation warning."""
        self.connection_status['warning_issued'] = False
        self.logger.info("Price validation warning acknowledged by user")
    
    def get_multiple_prices(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Get current prices for multiple cryptocurrencies with robust validation.
        
        Returns:
            Dict mapping symbols to price data with validation status
        """
        current_time = time.time()
        current_datetime = datetime.now()
        
        # Check cache for individual symbols first
        cached_results = {}
        uncached_symbols = []
        
        for symbol in symbols:
            cache_key = f"price_{symbol}"
            if self._is_cache_valid(cache_key):
                cached_results[symbol] = self.cache[cache_key]
            else:
                uncached_symbols.append(symbol)
        
        # If all symbols are cached, return cached results
        if not uncached_symbols:
            return cached_results
        
        # Map uncached symbols to coin IDs
        coin_ids = []
        symbol_mapping = {}
        
        for symbol in uncached_symbols:
            coin_id = self.coin_mapping.get(symbol)
            if coin_id:
                coin_ids.append(coin_id)
                symbol_mapping[coin_id] = symbol
        
        if not coin_ids:
            # Only return cached results if available
            return cached_results
        
        try:
            self._rate_limit()
            url = f"{self.base_url}/simple/price"
            params = {
                'ids': ','.join(coin_ids),
                'vs_currencies': 'usd'
            }
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            fresh_prices = {}
            
            for coin_id, price_data in data.items():
                symbol = symbol_mapping.get(coin_id)
                price = price_data.get('usd')
                
                if symbol and price is not None:
                    price_info = {
                        'price': price,
                        'is_live': True,
                        'timestamp': current_datetime.isoformat(),
                        'source': 'CoinGecko_API'
                    }
                    
                    fresh_prices[symbol] = price_info
                    
                    # Update last known good price
                    self.last_known_prices[symbol] = {
                        'price': price,
                        'timestamp': current_datetime,
                        'source': 'CoinGecko_API'
                    }
                    
                    # Cache individual price
                    cache_key = f"price_{symbol}"
                    self.cache[cache_key] = price_info
            
            # Update connection status on success
            self.connection_status.update({
                'connected': True,
                'last_success': current_datetime,
                'last_error': None,
                'consecutive_failures': 0
            })
            
            self.logger.info(f"Retrieved live prices for {len(fresh_prices)} cryptocurrencies")
            
            # Combine cached and fresh results
            all_results = {**cached_results, **fresh_prices}
            
            # Handle any symbols that failed to fetch with fallback prices
            for symbol in uncached_symbols:
                if symbol not in fresh_prices:
                    # Use simple fallback price based on symbol (for demo/simulation purposes)
                    fallback_price = 1.0  # Default fallback
                    fallback_data = {
                        'price': fallback_price,
                        'is_live': False,
                        'timestamp': current_datetime.isoformat(),
                        'source': 'Fallback_Demo'
                    }
                    all_results[symbol] = fallback_data
                    self.logger.warning(f"Using fallback price for unmapped symbol {symbol}: ${fallback_price}")
            
            return all_results
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed for multiple prices: {e}")
            
            # Update connection status on failure
            self.connection_status.update({
                'connected': False,
                'last_error': str(e),
                'consecutive_failures': self.connection_status.get('consecutive_failures', 0) + 1,
                'warning_issued': True
            })
            
            # Return cached results plus fallback prices
            fallback_results = {}
            for symbol in uncached_symbols:
                fallback_data = self._get_fallback_price_for_symbol(symbol)
                if fallback_data:
                    fallback_results[symbol] = fallback_data
            
            return {**cached_results, **fallback_results}
            
        except Exception as e:
            self.logger.error(f"Error getting multiple prices: {e}")
            
            # Update connection status
            self.connection_status.update({
                'connected': False,
                'last_error': str(e),
                'consecutive_failures': self.connection_status.get('consecutive_failures', 0) + 1,
                'warning_issued': True
            })
            
            return cached_results
    
    def _get_fallback_price_for_symbol(self, symbol: str) -> Optional[Dict]:
        """Get fallback price for a single symbol."""
        if symbol in self.last_known_prices:
            last_price_data = self.last_known_prices[symbol]
            price_age = datetime.now() - last_price_data['timestamp']
            
            if price_age <= self.max_price_age:
                return {
                    'price': last_price_data['price'],
                    'is_live': False,
                    'timestamp': last_price_data['timestamp'].isoformat(),
                    'source': f"Last_Known_{last_price_data['source']}",
                    'age_hours': round(price_age.total_seconds() / 3600, 1)
                }
        
        self.logger.warning(f"No valid fallback price available for {symbol}")
        return None
    
    def test_connection(self) -> Dict[str, any]:
        """Test API connection and return status information."""
        try:
            self._rate_limit()
            url = f"{self.base_url}/ping"
            
            start_time = time.time()
            response = requests.get(url, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                return {
                    'status': 'connected',
                    'api_provider': 'CoinGecko',
                    'response_time_ms': round(response_time * 1000, 2),
                    'last_updated': datetime.now().isoformat(),
                    'rate_limit': '10-30 requests/minute (free tier)',
                    'data_source': 'https://api.coingecko.com/api/v3'
                }
            else:
                return {
                    'status': 'error',
                    'error': f"HTTP {response.status_code}",
                    'api_provider': 'CoinGecko'
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'status': 'error',
                'error': str(e),
                'api_provider': 'CoinGecko'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': f"Unexpected error: {str(e)}",
                'api_provider': 'CoinGecko'
            }
    
    def get_market_data(self, symbol: str) -> Optional[Dict]:
        """Get detailed market data for a cryptocurrency."""
        coin_id = self.coin_mapping.get(symbol)
        if not coin_id:
            return None
        
        cache_key = f"market_{symbol}"
        
        # Return cached data if valid (longer cache for market data)
        if cache_key in self.cache:
            cache_time = self.cache[cache_key].get('timestamp', 0)
            if (time.time() - cache_time) < 300:  # 5 minute cache
                return self.cache[cache_key]['data']
        
        try:
            self._rate_limit()
            url = f"{self.base_url}/coins/{coin_id}"
            params = {
                'localization': 'false',
                'tickers': 'false',
                'market_data': 'true',
                'community_data': 'false',
                'developer_data': 'false'
            }
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            market_data = data.get('market_data', {})
            
            result = {
                'symbol': symbol,
                'name': data.get('name'),
                'current_price': market_data.get('current_price', {}).get('usd'),
                'market_cap': market_data.get('market_cap', {}).get('usd'),
                'market_cap_rank': market_data.get('market_cap_rank'),
                'price_change_24h': market_data.get('price_change_percentage_24h'),
                'price_change_7d': market_data.get('price_change_percentage_7d'),
                'volume_24h': market_data.get('total_volume', {}).get('usd'),
                'last_updated': data.get('last_updated')
            }
            
            # Cache the result
            self.cache[cache_key] = {
                'data': result,
                'timestamp': time.time()
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting market data for {symbol}: {e}")
            return None