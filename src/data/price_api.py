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
        self.cache_duration = 60  # Cache for 60 seconds
        self.last_request_time = 0
        self.request_delay = 1.1  # Rate limit: 1 request per second
        
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
            "HOT": "holo",
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
            "ONT": "ontology"
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
        """Check if cached data is still valid."""
        if cache_key not in self.cache:
            return False
        
        cache_time = self.cache[cache_key].get('timestamp', 0)
        return (time.time() - cache_time) < self.cache_duration
    
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
    
    def get_multiple_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Get current prices for multiple cryptocurrencies in a single request."""
        cache_key = f"multi_price_{'_'.join(sorted(symbols))}"
        
        # Check cache for all symbols
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['prices']
        
        # Map symbols to coin IDs
        coin_ids = []
        symbol_mapping = {}
        
        for symbol in symbols:
            coin_id = self.coin_mapping.get(symbol)
            if coin_id:
                coin_ids.append(coin_id)
                symbol_mapping[coin_id] = symbol
        
        if not coin_ids:
            return {}
        
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
            prices = {}
            
            for coin_id, price_data in data.items():
                symbol = symbol_mapping.get(coin_id)
                price = price_data.get('usd')
                
                if symbol and price is not None:
                    prices[symbol] = price
            
            # Cache the results
            self.cache[cache_key] = {
                'prices': prices,
                'timestamp': time.time()
            }
            
            self.logger.info(f"Retrieved live prices for {len(prices)} cryptocurrencies")
            return prices
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed for multiple prices: {e}")
        except Exception as e:
            self.logger.error(f"Error getting multiple prices: {e}")
        
        return {}
    
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