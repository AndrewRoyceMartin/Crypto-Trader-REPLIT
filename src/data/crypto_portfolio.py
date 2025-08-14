"""
Cryptocurrency Portfolio Management System
Manages a diversified portfolio of 100 cryptocurrencies
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import json
import os
from .price_api import CryptoPriceAPI
from ..utils.email_service import email_service

class CryptoPortfolioManager:
    """Manages a portfolio of 103 different cryptocurrencies with $10 initial investment per crypto."""
    
    def __init__(self, initial_value_per_crypto: float = 10.0):
        """
        Initialize the crypto portfolio manager.
        
        Args:
            initial_value_per_crypto: Starting USD value for each cryptocurrency
        """
        self.initial_value = initial_value_per_crypto
        self.logger = logging.getLogger(__name__)
        self.crypto_list = self._get_top_100_cryptos()
        self.price_api = CryptoPriceAPI()
        self.portfolio_data = self._initialize_portfolio()
        self.price_history = {}
        
        # Test API connection on startup
        api_status = self.price_api.test_connection()
        if api_status['status'] == 'connected':
            self.logger.info(f"Live price API connected: {api_status['api_provider']}")
        else:
            self.logger.warning(f"Price API connection failed: {api_status.get('error', 'Unknown error')}")
        
    def _get_top_100_cryptos(self) -> List[Dict]:
        """Get list of top 100 highest-performing cryptocurrencies based on past 6 months data."""
        return [
            # Top Tier - Established market leaders with strong performance
            {"symbol": "BTC", "name": "Bitcoin", "rank": 1},
            {"symbol": "ETH", "name": "Ethereum", "rank": 2},
            {"symbol": "SOL", "name": "Solana", "rank": 3},
            {"symbol": "XRP", "name": "XRP", "rank": 4},
            {"symbol": "DOGE", "name": "Dogecoin", "rank": 5},
            {"symbol": "BNB", "name": "BNB", "rank": 6},
            {"symbol": "ADA", "name": "Cardano", "rank": 7},
            {"symbol": "AVAX", "name": "Avalanche", "rank": 8},
            {"symbol": "LINK", "name": "Chainlink", "rank": 9},
            {"symbol": "UNI", "name": "Uniswap", "rank": 10},
            
            # Real Major Cryptocurrencies - All have verified CoinGecko mappings
            {"symbol": "USDC", "name": "USD Coin", "rank": 11},
            {"symbol": "SHIB", "name": "Shiba Inu", "rank": 12},
            {"symbol": "LTC", "name": "Litecoin", "rank": 13},
            {"symbol": "BCH", "name": "Bitcoin Cash", "rank": 14},
            {"symbol": "NEAR", "name": "NEAR Protocol", "rank": 15},
            {"symbol": "ICP", "name": "Internet Computer", "rank": 16},
            {"symbol": "LEO", "name": "LEO Token", "rank": 17},
            {"symbol": "TON", "name": "Toncoin", "rank": 18},
            {"symbol": "APT", "name": "Aptos", "rank": 19},
            {"symbol": "STX", "name": "Stacks", "rank": 20},
            
            # Strong Altcoin Performers
            {"symbol": "ARB", "name": "Arbitrum", "rank": 21},
            {"symbol": "OP", "name": "Optimism", "rank": 22},
            {"symbol": "IMX", "name": "Immutable X", "rank": 23},
            {"symbol": "MNT", "name": "Mantle", "rank": 24},
            {"symbol": "HBAR", "name": "Hedera", "rank": 25},
            {"symbol": "VET", "name": "VeChain", "rank": 26},
            {"symbol": "DOT", "name": "Polkadot", "rank": 27},
            {"symbol": "MATIC", "name": "Polygon", "rank": 28},
            {"symbol": "ATOM", "name": "Cosmos", "rank": 29},
            {"symbol": "FIL", "name": "Filecoin", "rank": 30},
            
            # DeFi & Gaming Leaders
            {"symbol": "AAVE", "name": "Aave", "rank": 31},
            {"symbol": "MKR", "name": "Maker", "rank": 32},
            {"symbol": "COMP", "name": "Compound", "rank": 33},
            {"symbol": "CRV", "name": "Curve DAO", "rank": 34},
            {"symbol": "SNX", "name": "Synthetix", "rank": 35},
            {"symbol": "SUSHI", "name": "SushiSwap", "rank": 36},
            {"symbol": "1INCH", "name": "1inch", "rank": 37},
            {"symbol": "SAND", "name": "The Sandbox", "rank": 38},
            {"symbol": "MANA", "name": "Decentraland", "rank": 39},
            {"symbol": "AXS", "name": "Axie Infinity", "rank": 40},
            
            # Additional User-Requested Tokens
            {"symbol": "BADGER", "name": "Badger DAO", "rank": 41},
            {"symbol": "AMP", "name": "Amp", "rank": 42},
            {"symbol": "GALA", "name": "Gala", "rank": 43},
            
            # Infrastructure & Layer-1s
            {"symbol": "ATOM", "name": "Cosmos", "rank": 44},
            {"symbol": "FTM", "name": "Fantom", "rank": 45},
            {"symbol": "ALGO", "name": "Algorand", "rank": 46},
            {"symbol": "FLOW", "name": "Flow", "rank": 47},
            {"symbol": "ICP", "name": "Internet Computer", "rank": 48},
            {"symbol": "THETA", "name": "Theta Network", "rank": 49},
            {"symbol": "FIL", "name": "Filecoin", "rank": 50},
            {"symbol": "VET", "name": "VeChain", "rank": 51},
            {"symbol": "HBAR", "name": "Hedera", "rank": 52},
            {"symbol": "EGLD", "name": "MultiversX", "rank": 53},
            
            # High Potential Mid-Caps
            {"symbol": "GRT", "name": "The Graph", "rank": 54},
            {"symbol": "FET", "name": "Fetch.ai", "rank": 55},
            {"symbol": "LRC", "name": "Loopring", "rank": 56},
            {"symbol": "ENJ", "name": "Enjin Coin", "rank": 57},
            {"symbol": "CHZ", "name": "Chiliz", "rank": 58},
            {"symbol": "BAT", "name": "Basic Attention Token", "rank": 59},
            {"symbol": "XTZ", "name": "Tezos", "rank": 60},
            {"symbol": "MINA", "name": "Mina Protocol", "rank": 61},
            {"symbol": "KCS", "name": "KuCoin Shares", "rank": 62},
            {"symbol": "YFI", "name": "yearn.finance", "rank": 63},
            
            # Privacy & Security
            {"symbol": "ZEC", "name": "Zcash", "rank": 64},
            {"symbol": "DASH", "name": "Dash", "rank": 65},
            {"symbol": "DCR", "name": "Decred", "rank": 66},
            {"symbol": "WAVES", "name": "Waves", "rank": 67},
            {"symbol": "ZIL", "name": "Zilliqa", "rank": 68},
            
            # Emerging DeFi & Layer-2
            {"symbol": "BAL", "name": "Balancer", "rank": 69},
            {"symbol": "BAND", "name": "Band Protocol", "rank": 70},
            {"symbol": "OCEAN", "name": "Ocean Protocol", "rank": 71},
            {"symbol": "UMA", "name": "UMA Protocol", "rank": 72},
            {"symbol": "ALPHA", "name": "Alpha Finance", "rank": 73},
            {"symbol": "ANKR", "name": "Ankr", "rank": 74},
            {"symbol": "SKL", "name": "SKALE Network", "rank": 75},
            {"symbol": "CTSI", "name": "Cartesi", "rank": 76},
            {"symbol": "CELR", "name": "Celer Network", "rank": 77},
            {"symbol": "STORJ", "name": "Storj", "rank": 78},
            
            # High-Volatility Opportunities
            {"symbol": "RSR", "name": "Reserve Rights", "rank": 79},
            {"symbol": "REN", "name": "Ren Protocol", "rank": 80},
            {"symbol": "KNC", "name": "Kyber Network", "rank": 81},
            {"symbol": "NMR", "name": "Numeraire", "rank": 82},
            {"symbol": "BNT", "name": "Bancor", "rank": 83},
            {"symbol": "KAVA", "name": "Kava", "rank": 84},
            {"symbol": "COTI", "name": "COTI", "rank": 85},
            {"symbol": "NKN", "name": "NKN", "rank": 86},
            {"symbol": "OGN", "name": "Origin Protocol", "rank": 87},
            {"symbol": "NANO", "name": "Nano", "rank": 88},
            
            # Micro-Cap Moonshots
            {"symbol": "RVN", "name": "Ravencoin", "rank": 89},
            {"symbol": "DGB", "name": "DigiByte", "rank": 90},
            {"symbol": "SC", "name": "Siacoin", "rank": 91},
            {"symbol": "HOT", "name": "Holo", "rank": 92},
            {"symbol": "IOST", "name": "IOST", "rank": 93},
            {"symbol": "DUSK", "name": "Dusk Network", "rank": 94},
            {"symbol": "WIN", "name": "WINkLink", "rank": 95},
            {"symbol": "BTT", "name": "BitTorrent", "rank": 96},
            {"symbol": "TWT", "name": "Trust Wallet Token", "rank": 97},
            {"symbol": "JST", "name": "JUST", "rank": 98},
            
            # Specialized Tokens
            {"symbol": "SXP", "name": "Solar", "rank": 99},
            {"symbol": "HARD", "name": "Kava Lend", "rank": 100},
            {"symbol": "SUN", "name": "Sun Token", "rank": 101},
            {"symbol": "ICX", "name": "ICON", "rank": 102},
            {"symbol": "ONT", "name": "Ontology", "rank": 103}
        ]
    
    def _initialize_portfolio(self) -> Dict:
        """Initialize portfolio with starting values for each cryptocurrency."""
        portfolio = {}
        
        # Get live prices for top 10 cryptocurrencies only during initialization to speed up startup
        symbols = [crypto["symbol"] for crypto in self.crypto_list[:10]]  # Limit to first 10 for faster startup
        live_prices = self.price_api.get_multiple_prices(symbols)
        
        for crypto in self.crypto_list[:10]:  # Initialize only top 10 for faster startup
            symbol = crypto["symbol"]
            # Use live price if available, otherwise fallback to realistic simulation
            if symbol in live_prices:
                base_price = live_prices[symbol]
                if isinstance(base_price, (int, float)):
                    self.logger.info(f"Using live price for {symbol}: ${base_price:.6f}")
                else:
                    # Handle new price data format with validation info
                    price_value = base_price.get('price', 0) if isinstance(base_price, dict) else base_price
                    is_live = base_price.get('is_live', True) if isinstance(base_price, dict) else True
                    source = base_price.get('source', 'Unknown') if isinstance(base_price, dict) else 'Legacy'
                    
                    if is_live:
                        self.logger.info(f"Using live price for {symbol}: ${price_value:.6f} from {source}")
                    else:
                        age_hours = base_price.get('age_hours', 0) if isinstance(base_price, dict) else 0
                        self.logger.warning(f"Using cached price for {symbol}: ${price_value:.6f} from {source} ({age_hours:.1f}h old)")
                    
                    base_price = price_value  # Use the actual price value for calculations
            else:
                # NEVER use simulated prices - log error and skip this crypto
                self.logger.error(f"CRITICAL: No live price data available for {symbol} - SKIPPING from portfolio initialization")
                continue
            
            # Ensure base_price is not zero to prevent division by zero
            if base_price <= 0:
                base_price = 0.000001  # Use a very small number as fallback
            quantity = self.initial_value / base_price
            
            portfolio[symbol] = {
                "name": crypto["name"],
                "rank": crypto["rank"],
                "quantity": quantity,
                "initial_price": base_price,
                "current_price": base_price,
                "initial_value": self.initial_value,
                "current_value": self.initial_value,
                "pnl": 0.0,
                "pnl_percent": 0.0,
                "target_sell_price": self._calculate_target_sell_price(base_price, crypto["rank"]),
                "target_buy_price": self._calculate_target_buy_price(base_price, crypto["rank"]),
                "projected_sell_pnl": float(self._calculate_target_sell_price(base_price, crypto["rank"]) * quantity) - float(self.initial_value),
                "initial_investment_date": datetime.now().isoformat(),
                "total_invested": self.initial_value,
                "total_realized_pnl": 0.0,
                "trade_count": 0
            }
            
        return portfolio
    
    def _get_live_price(self, symbol: str) -> Optional[float]:
        """Get live price from CoinGecko API with fallback to simulated price."""
        try:
            live_price = self.price_api.get_price(symbol)
            if live_price is not None:
                self.logger.info(f"Retrieved live price for {symbol}: ${live_price:.6f}")
                return live_price
        except Exception as e:
            self.logger.warning(f"Failed to get live price for {symbol}: {e}")
        
        # CRITICAL ERROR: No simulated data allowed - return None to indicate failure
        self.logger.error(f"CRITICAL: No live price data available for {symbol} from CoinGecko API")
        return None
    
    # REMOVED: _generate_realistic_price function - This system NEVER generates simulated prices
    # All price data MUST come from live CoinGecko API - no fallbacks, no simulations, no mock data
    
    # REMOVED: simulate_price_movements function - This system NEVER uses simulated data
    # All price data MUST come from live CoinGecko API or return errors if unavailable
    
    def _get_volatility_by_rank(self, rank: int) -> float:
        """Get appropriate volatility based on cryptocurrency rank and performance potential."""
        if rank <= 2:  # BTC, ETH - stable leaders
            return 0.02    # 2% volatility for premium cryptos
        elif rank <= 10:  # Top established performers
            return 0.03    # 3% for stable top 10
        elif rank <= 20:  # High-growth winners (SAROS, XCN, ZBCN, etc.)
            return 0.08    # 8% volatility for massive gainers
        elif rank <= 40:  # Strong altcoins with momentum
            return 0.06    # 6% for strong performers
        elif rank <= 60:  # DeFi leaders with steady growth
            return 0.05    # 5% for established DeFi
        elif rank <= 80:  # Infrastructure projects
            return 0.07    # 7% for emerging projects
        else:  # Micro-cap moonshots
            return 0.12    # 12% extreme volatility for small caps
    
    def _calculate_target_sell_price(self, current_price: float, rank: int) -> float:
        """Calculate target sell price based on Bollinger Bands strategy and crypto tier."""
        # Base profit target varies by crypto tier
        if rank <= 2:  # BTC, ETH - conservative targets
            profit_target = 0.05    # 5% profit target
        elif rank <= 10:  # Top performers - moderate targets
            profit_target = 0.08    # 8% profit target
        elif rank <= 20:  # High-growth winners - aggressive targets
            profit_target = 0.12    # 12% profit target
        elif rank <= 40:  # Strong altcoins - high targets
            profit_target = 0.10    # 10% profit target
        elif rank <= 60:  # DeFi leaders - moderate targets
            profit_target = 0.09    # 9% profit target
        elif rank <= 80:  # Infrastructure - high risk/reward
            profit_target = 0.15    # 15% profit target
        else:  # Micro-cap moonshots - maximum targets
            profit_target = 0.20    # 20% profit target for high-risk plays
        
        return current_price * (1 + profit_target)
    
    def _calculate_target_buy_price(self, current_price: float, rank: int) -> float:
        """Calculate target buy price based on risk appetite and support levels."""
        # Target buy prices are typically 10-25% below current price for good entry points
        if rank <= 2:   # BTC, ETH - conservative dip buying
            discount = 0.08    # 8% below current price
        elif rank <= 10:  # Top performers - moderate dips
            discount = 0.12    # 12% below current price  
        elif rank <= 20:  # High-growth winners - bigger dips for better entries
            discount = 0.18    # 18% below current price
        elif rank <= 40:  # Strong altcoins - volatility opportunities
            discount = 0.15    # 15% below current price
        elif rank <= 60:  # DeFi leaders - moderate entries
            discount = 0.14    # 14% below current price
        elif rank <= 80:  # Infrastructure - bigger swings
            discount = 0.20    # 20% below current price
        else:  # Micro-cap moonshots - maximum discount for high-risk entries
            discount = 0.25    # 25% below current price for speculative plays
        
        return current_price * (1 - discount)
    
    def _migrate_portfolio_data(self) -> None:
        """Migrate old portfolio data to include new fields like target_sell_price and target_buy_price."""
        for symbol, crypto in self.portfolio_data.items():
            current_price = crypto.get("current_price", crypto.get("initial_price", 100))
            rank = crypto.get("rank", 50)
            
            # Add target_sell_price if it doesn't exist
            if "target_sell_price" not in crypto:
                crypto["target_sell_price"] = self._calculate_target_sell_price(current_price, rank)
                self.logger.info(f"Added target sell price for {symbol}: ${crypto['target_sell_price']:.4f}")
            
            # Add target_buy_price if it doesn't exist
            if "target_buy_price" not in crypto:
                crypto["target_buy_price"] = self._calculate_target_buy_price(current_price, rank)
                self.logger.info(f"Added target buy price for {symbol}: ${crypto['target_buy_price']:.4f}")
            
            # Add projected_sell_pnl if it doesn't exist
            if "projected_sell_pnl" not in crypto:
                if crypto.get("target_sell_price") and crypto.get("quantity"):
                    sell_value = crypto["target_sell_price"] * crypto["quantity"]
                    crypto["projected_sell_pnl"] = sell_value - crypto["initial_value"]
                else:
                    crypto["projected_sell_pnl"] = 0.0
    
    def get_portfolio_summary(self) -> Dict:
        """Get complete portfolio summary statistics."""
        total_initial_value = sum(crypto["initial_value"] for crypto in self.portfolio_data.values())
        total_current_value = sum(crypto["current_value"] for crypto in self.portfolio_data.values())
        total_pnl = total_current_value - total_initial_value
        total_pnl_percent = (total_pnl / total_initial_value) * 100 if total_initial_value > 0 else 0
        
        # Get top gainers and losers
        sorted_by_pnl = sorted(self.portfolio_data.items(), key=lambda x: x[1]["pnl_percent"], reverse=True)
        top_gainers = sorted_by_pnl[:5]
        top_losers = sorted_by_pnl[-5:]
        
        # Get largest positions by value
        sorted_by_value = sorted(self.portfolio_data.items(), key=lambda x: x[1]["current_value"], reverse=True)
        largest_positions = sorted_by_value[:10]
        
        return {
            "total_initial_value": total_initial_value,
            "total_current_value": total_current_value,
            "total_pnl": total_pnl,
            "total_pnl_percent": total_pnl_percent,
            "number_of_cryptos": len(self.portfolio_data),
            "top_gainers": [(symbol, data["name"], data["pnl_percent"]) for symbol, data in top_gainers],
            "top_losers": [(symbol, data["name"], data["pnl_percent"]) for symbol, data in top_losers],
            "largest_positions": [(symbol, data["name"], data["current_value"]) for symbol, data in largest_positions]
        }
    
    def get_portfolio_data(self) -> Dict:
        """Get detailed portfolio data for all cryptocurrencies."""
        return self.portfolio_data
    
    def get_portfolio_performance(self) -> List[Dict]:
        """Get portfolio performance data showing accumulated P&L since original investment."""
        performance_data = []
        
        for symbol, crypto in self.portfolio_data.items():
            # Calculate time since investment
            initial_time = crypto.get("initial_investment_date", datetime.now())
            if isinstance(initial_time, str):
                try:
                    initial_time = datetime.fromisoformat(initial_time)
                except:
                    initial_time = datetime.now()
            
            days_invested = (datetime.now() - initial_time).days
            
            # Calculate total accumulated P&L (includes all trades and current position)
            total_realized_pnl = crypto.get("total_realized_pnl", 0.0)  # From completed trades
            current_unrealized_pnl = crypto.get("pnl", 0.0)  # Current position P&L
            total_accumulated_pnl = total_realized_pnl + current_unrealized_pnl
            
            # Calculate total money invested (initial + any additional purchases)
            total_invested = crypto.get("total_invested", crypto["initial_value"])
            accumulated_pnl_percent = (total_accumulated_pnl / total_invested) * 100 if total_invested > 0 else 0
            
            # Calculate average daily return
            daily_return = accumulated_pnl_percent / days_invested if days_invested > 0 else 0
            
            performance_data.append({
                "symbol": symbol,
                "name": crypto["name"],
                "rank": crypto["rank"],
                "days_invested": days_invested,
                "total_invested": total_invested,
                "current_value": crypto["current_value"],
                "total_accumulated_pnl": total_accumulated_pnl,
                "accumulated_pnl_percent": accumulated_pnl_percent,
                "daily_return_percent": daily_return,
                "current_price": crypto["current_price"],
                "quantity": crypto["quantity"],
                "initial_price": float(total_invested) / float(crypto["quantity"]) if crypto["quantity"] > 0 else 0,
                "best_performer": accumulated_pnl_percent > 50,  # Flag top performers
                "status": "winning" if accumulated_pnl_percent > 0 else "losing"
            })
        
        # Sort by accumulated P&L percentage (best performers first)
        performance_data.sort(key=lambda x: x["accumulated_pnl_percent"], reverse=True)
        
        return performance_data
    
    def get_current_positions(self) -> List[Dict]:
        """Get current market positions showing actual holdings at this moment."""
        positions = []
        
        for symbol, crypto in self.portfolio_data.items():
            # Only include positions with actual holdings
            if crypto["quantity"] > 0:
                current_value = crypto["current_value"]
                unrealized_pnl = crypto.get("pnl", 0.0)
                
                # Calculate position size as percentage of total portfolio
                total_portfolio_value = sum(c["current_value"] for c in self.portfolio_data.values())
                position_percent = (current_value / total_portfolio_value) * 100 if total_portfolio_value > 0 else 0
                
                # Determine position status
                pnl_percent = crypto.get("pnl_percent", 0.0)
                if pnl_percent > 20:
                    status = "strong_gain"
                elif pnl_percent > 5:
                    status = "moderate_gain" 
                elif pnl_percent > -5:
                    status = "stable"
                elif pnl_percent > -20:
                    status = "moderate_loss"
                else:
                    status = "significant_loss"
                
                # Calculate potential profit at target sell price
                target_sell_price = crypto.get("target_sell_price", 0)
                potential_sell_value = crypto["quantity"] * target_sell_price if target_sell_price > 0 else 0
                potential_profit = potential_sell_value - float(crypto["initial_value"]) if potential_sell_value > 0 else 0
                
                positions.append({
                    "symbol": symbol,
                    "name": crypto["name"],
                    "quantity": crypto["quantity"],
                    "current_price": crypto["current_price"],
                    "current_value": current_value,
                    "position_percent": position_percent,
                    "unrealized_pnl": unrealized_pnl,
                    "pnl_percent": pnl_percent,
                    "status": status,
                    "target_sell_price": target_sell_price,
                    "potential_sell_value": potential_sell_value,
                    "potential_profit": potential_profit,
                    "avg_buy_price": float(crypto["initial_value"]) / float(crypto["quantity"]) if crypto["quantity"] > 0 else 0,
                    "last_updated": datetime.now().isoformat()
                })
        
        # Sort by current value (largest positions first)
        positions.sort(key=lambda x: x["current_value"], reverse=True)
        
        return positions
    
    def get_api_status(self) -> Dict:
        """Get live API connection status and information."""
        return self.price_api.test_connection()
    
    def update_live_prices(self, symbols: List[str] = None) -> Dict[str, any]:
        """
        Update portfolio with live prices from API with validation.
        
        Returns:
            Dictionary containing update status and price validation information
        """
        if symbols is None:
            symbols = [crypto["symbol"] for crypto in self.crypto_list]
        
        # Get validated price data for all symbols
        price_data_with_validation = self.price_api.get_multiple_prices(symbols)
        
        update_summary = {
            'total_symbols': len(symbols),
            'live_prices': 0,
            'cached_prices': 0,
            'failed_symbols': [],
            'has_non_live_prices': False,
            'oldest_price_age': 0,
            'connection_status': self.price_api.get_connection_status(),
            'prices': {}
        }
        
        # Update portfolio with validated price data
        updated_count = 0
        for symbol in symbols:
            if symbol in price_data_with_validation and symbol in self.portfolio_data:
                price_info = price_data_with_validation[symbol]
                crypto = self.portfolio_data[symbol]
                
                if isinstance(price_info, dict):
                    price = price_info.get('price', crypto["current_price"])
                    is_live = price_info.get('is_live', True)
                    source = price_info.get('source', 'Unknown')
                    age_hours = price_info.get('age_hours', 0)
                    
                    # Track validation statistics
                    if is_live:
                        update_summary['live_prices'] += 1
                    else:
                        update_summary['cached_prices'] += 1
                        update_summary['has_non_live_prices'] = True
                        if age_hours > update_summary['oldest_price_age']:
                            update_summary['oldest_price_age'] = age_hours
                    
                    # Store validation info for frontend
                    update_summary['prices'][symbol] = {
                        'price': price,
                        'is_live': is_live,
                        'source': source,
                        'age_hours': age_hours
                    }
                else:
                    # Legacy numeric price format
                    price = price_info
                    update_summary['live_prices'] += 1
                
                # CRITICAL: Only use live data - if no valid price data, mark as failed
                if price is None or price <= 0:
                    update_summary['failed_symbols'].append(symbol)
                    self.logger.error(f"CRITICAL ERROR: No valid price data for {symbol} - marking as failed")
                    continue
                    update_summary['prices'][symbol] = {
                        'price': price,
                        'is_live': True,
                        'source': 'CoinGecko_API',
                        'age_hours': 0
                    }
                
                # Update portfolio data
                crypto["current_price"] = price
                crypto["current_value"] = crypto["quantity"] * price
                crypto["pnl"] = crypto["current_value"] - crypto["initial_value"]
                crypto["pnl_percent"] = (crypto["pnl"] / crypto["initial_value"]) * 100
                
                # Update target prices
                crypto["target_sell_price"] = self._calculate_target_sell_price(price, crypto["rank"])
                crypto["target_buy_price"] = self._calculate_target_buy_price(price, crypto["rank"])
                
                # Update projected P&L
                if crypto.get("target_sell_price"):
                    sell_value = crypto["target_sell_price"] * crypto["quantity"]
                    crypto["projected_sell_pnl"] = sell_value - crypto["initial_value"]
                
                updated_count += 1
            else:
                # Symbol failed to update
                update_summary['failed_symbols'].append(symbol)
        
        if update_summary['has_non_live_prices'] or update_summary['failed_symbols']:
            self.logger.warning(f"Updated {updated_count} cryptocurrencies: {update_summary['live_prices']} live, {update_summary['cached_prices']} cached, {len(update_summary['failed_symbols'])} failed")
        else:
            self.logger.info(f"Updated {updated_count} cryptocurrencies with live prices")
        
        return update_summary
    
    def get_price_validation_status(self) -> Dict[str, any]:
        """Get current price validation status for the portfolio."""
        return {
            'connection_status': self.price_api.get_connection_status(),
            'has_trading_restrictions': not self.price_api.connection_status['connected'],
            'last_update': datetime.now().isoformat()
        }
    
    def check_auto_trading_opportunities(self) -> List[Dict]:
        """Check for automatic buy/sell opportunities based on target prices."""
        opportunities = []
        
        for symbol, crypto in self.portfolio_data.items():
            current_price = crypto["current_price"]
            target_buy_price = crypto.get("target_buy_price", 0)
            target_sell_price = crypto.get("target_sell_price", 0)
            
            # Check for auto-buy opportunities
            if target_buy_price > 0 and current_price <= target_buy_price:
                # Calculate buy amount based on available cash (assuming some spare cash)
                buy_amount = min(100, self.cash_balance * 0.05)  # 5% of cash or $100 max
                if buy_amount >= 10:  # Minimum $10 trade
                    opportunities.append({
                        'type': 'BUY',
                        'symbol': symbol,
                        'current_price': current_price,
                        'target_price': target_buy_price,
                        'recommended_amount': buy_amount,
                        'quantity': buy_amount / current_price,
                        'reason': f'Price ${current_price:.4f} reached target buy ${target_buy_price:.4f}'
                    })
            
            # Check for auto-sell opportunities
            if target_sell_price > 0 and current_price >= target_sell_price:
                quantity = crypto.get("quantity", 0)
                if quantity > 0:
                    opportunities.append({
                        'type': 'SELL',
                        'symbol': symbol,
                        'current_price': current_price,
                        'target_price': target_sell_price,
                        'quantity': quantity,
                        'estimated_value': quantity * current_price,
                        'reason': f'Price ${current_price:.4f} reached target sell ${target_sell_price:.4f}'
                    })
        
        return opportunities
    
    def execute_auto_trade(self, opportunity: Dict, db_manager=None) -> bool:
        """Execute an automatic trade opportunity."""
        try:
            import time
            from datetime import datetime
            
            symbol = opportunity['symbol']
            trade_type = opportunity['type']
            current_price = opportunity['current_price']
            
            if trade_type == 'BUY':
                amount = opportunity['recommended_amount']
                quantity = opportunity['quantity']
                
                # Check if we have enough cash
                if self.cash_balance >= amount:
                    # Execute buy
                    self.cash_balance -= amount
                    
                    if symbol in self.portfolio_data:
                        # Add to existing position
                        existing_qty = self.portfolio_data[symbol]['quantity']
                        existing_value = self.portfolio_data[symbol]['current_value']
                        
                        new_quantity = existing_qty + quantity
                        new_value = existing_value + amount
                        avg_price = new_value / new_quantity
                        
                        self.portfolio_data[symbol]['quantity'] = new_quantity
                        self.portfolio_data[symbol]['current_value'] = new_value
                        self.portfolio_data[symbol]['initial_value'] += amount  # Add to initial investment
                    
                    # Record trade if database manager available
                    if db_manager:
                        trade_data = {
                            'timestamp': datetime.now(),
                            'symbol': symbol,
                            'action': 'BUY',
                            'size': quantity,
                            'price': current_price,
                            'commission': amount * 0.001,
                            'order_id': f"AUTO_BUY_{symbol}_{int(time.time())}",
                            'strategy': 'AUTO_TARGET_BUY',
                            'confidence': 0.8,
                            'pnl': 0,
                            'mode': 'paper'
                        }
                        db_manager.save_trade(trade_data)
                    
                    # Send email notification for successful buy
                    trade_data_email = {
                        'symbol': symbol,
                        'action': 'BUY',
                        'quantity': quantity,
                        'price': current_price,
                        'total_value': amount,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    email_service.send_trade_notification(trade_data_email)
                    
                    self.logger.info(f"AUTO BUY executed: {symbol} - {quantity:.4f} @ ${current_price:.4f}")
                    return True
                    
            elif trade_type == 'SELL':
                quantity = opportunity['quantity']
                estimated_value = opportunity['estimated_value']
                
                if symbol in self.portfolio_data and self.portfolio_data[symbol]['quantity'] >= quantity:
                    # Execute sell
                    initial_value = self.portfolio_data[symbol]['initial_value']
                    pnl = estimated_value - initial_value
                    
                    # Add cash from sale
                    self.cash_balance += estimated_value
                    
                    # Record trade if database manager available
                    if db_manager:
                        trade_data = {
                            'timestamp': datetime.now(),
                            'symbol': symbol,
                            'action': 'SELL',
                            'size': quantity,
                            'price': current_price,
                            'commission': estimated_value * 0.001,
                            'order_id': f"AUTO_SELL_{symbol}_{int(time.time())}",
                            'strategy': 'AUTO_TARGET_SELL',
                            'confidence': 0.8,
                            'pnl': pnl,
                            'mode': 'paper'
                        }
                        db_manager.save_trade(trade_data)
                    
                    # Remove position (full sell)
                    del self.portfolio_data[symbol]
                    
                    # Send email notification for successful sell
                    trade_data_email = {
                        'symbol': symbol,
                        'action': 'SELL',
                        'quantity': quantity,
                        'price': current_price,
                        'total_value': estimated_value,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'pnl': pnl
                    }
                    email_service.send_trade_notification(trade_data_email)
                    
                    self.logger.info(f"AUTO SELL executed: {symbol} - {quantity:.4f} @ ${current_price:.4f} (P&L: ${pnl:.2f})")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error executing auto trade for {symbol}: {str(e)}")
            return False
    
    def get_crypto_history(self, symbol: str, hours: int = 24) -> List[Dict]:
        """Get price history for a specific cryptocurrency."""
        if symbol not in self.price_history:
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            point for point in self.price_history[symbol]
            if point["timestamp"] >= cutoff_time
        ]
    
    def get_portfolio_chart_data(self, hours: int = 24) -> List[Dict]:
        """Get portfolio value over time for charting."""
        if not self.price_history:
            return []
        
        # Get all unique timestamps
        all_timestamps = set()
        for crypto_history in self.price_history.values():
            for point in crypto_history:
                all_timestamps.add(point["timestamp"])
        
        sorted_timestamps = sorted(all_timestamps)
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_timestamps = [ts for ts in sorted_timestamps if ts >= cutoff_time]
        
        chart_data = []
        for timestamp in recent_timestamps:
            total_value = 0
            for symbol, crypto in self.portfolio_data.items():
                # Find the price at this timestamp (or closest before)
                price = crypto["current_price"]  # Default to current
                if symbol in self.price_history:
                    for point in reversed(self.price_history[symbol]):
                        if point["timestamp"] <= timestamp:
                            price = point["price"]
                            break
                
                total_value += crypto["quantity"] * price
            
            chart_data.append({
                "timestamp": timestamp.isoformat(),
                "value": total_value
            })
        
        return chart_data
    
    def save_portfolio_state(self, filepath: str = "crypto_portfolio_state.json") -> None:
        """Save current portfolio state to file."""
        state = {
            "portfolio_data": self.portfolio_data,
            "price_history": {
                symbol: [
                    {
                        "timestamp": point["timestamp"].isoformat(),
                        "price": point["price"],
                        "volume": point["volume"]
                    }
                    for point in history
                ]
                for symbol, history in self.price_history.items()
            },
            "last_updated": datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
        
        self.logger.info(f"Portfolio state saved to {filepath}")
    
    def load_portfolio_state(self, filepath: str = "crypto_portfolio_state.json") -> bool:
        """Load portfolio state from file."""
        try:
            if not os.path.exists(filepath):
                return False
            
            with open(filepath, 'r') as f:
                state = json.load(f)
            
            self.portfolio_data = state["portfolio_data"]
            
            # Migrate old portfolio data to include target_sell_price
            self._migrate_portfolio_data()
            
            # Convert timestamp strings back to datetime objects
            self.price_history = {}
            for symbol, history in state["price_history"].items():
                self.price_history[symbol] = [
                    {
                        "timestamp": datetime.fromisoformat(point["timestamp"]),
                        "price": point["price"],
                        "volume": point["volume"]
                    }
                    for point in history
                ]
            
            self.logger.info(f"Portfolio state loaded from {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading portfolio state: {e}")
            return False