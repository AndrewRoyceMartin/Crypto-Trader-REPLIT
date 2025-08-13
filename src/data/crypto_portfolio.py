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

class CryptoPortfolioManager:
    """Manages a portfolio of 100 different cryptocurrencies."""
    
    def __init__(self, initial_value_per_crypto: float = 100.0):
        """
        Initialize the crypto portfolio manager.
        
        Args:
            initial_value_per_crypto: Starting USD value for each cryptocurrency
        """
        self.initial_value = initial_value_per_crypto
        self.logger = logging.getLogger(__name__)
        self.crypto_list = self._get_top_100_cryptos()
        self.portfolio_data = self._initialize_portfolio()
        self.price_history = {}
        
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
            
            # High-Growth Winners - Top performers from research
            {"symbol": "SAROS", "name": "Saros Finance", "rank": 11},  # +1,379%
            {"symbol": "XCN", "name": "Onyxcoin", "rank": 12},  # +551%
            {"symbol": "ZBCN", "name": "Zebec Network", "rank": 13},  # +298%
            {"symbol": "SYRUP", "name": "Maple Finance", "rank": 14},  # +288%
            {"symbol": "TOSHI", "name": "Toshi", "rank": 15},  # +284%
            {"symbol": "VENOM", "name": "Venom", "rank": 16},  # +255%
            {"symbol": "EUL", "name": "Euler", "rank": 17},  # +120%
            {"symbol": "WBT", "name": "WhiteBIT Coin", "rank": 18},  # +90%
            {"symbol": "HYPE", "name": "Hyperliquid", "rank": 19},  # +65%
            {"symbol": "XMR", "name": "Monero", "rank": 20},  # +62%
            
            # Strong Altcoin Performers
            {"symbol": "SUI", "name": "Sui Network", "rank": 21},  # +371%
            {"symbol": "RNDR", "name": "Render Token", "rank": 22},
            {"symbol": "PEPE", "name": "Pepe", "rank": 23},
            {"symbol": "TON", "name": "Toncoin", "rank": 24},
            {"symbol": "LTC", "name": "Litecoin", "rank": 25},
            {"symbol": "SHIB", "name": "Shiba Inu", "rank": 26},
            {"symbol": "DOT", "name": "Polkadot", "rank": 27},
            {"symbol": "TRX", "name": "TRON", "rank": 28},
            {"symbol": "MATIC", "name": "Polygon", "rank": 29},
            {"symbol": "APT", "name": "Aptos", "rank": 30},
            
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
            
            # Infrastructure & Layer-1s
            {"symbol": "ATOM", "name": "Cosmos", "rank": 41},
            {"symbol": "FTM", "name": "Fantom", "rank": 42},
            {"symbol": "ALGO", "name": "Algorand", "rank": 43},
            {"symbol": "FLOW", "name": "Flow", "rank": 44},
            {"symbol": "ICP", "name": "Internet Computer", "rank": 45},
            {"symbol": "THETA", "name": "Theta Network", "rank": 46},
            {"symbol": "FIL", "name": "Filecoin", "rank": 47},
            {"symbol": "VET", "name": "VeChain", "rank": 48},
            {"symbol": "HBAR", "name": "Hedera", "rank": 49},
            {"symbol": "EGLD", "name": "MultiversX", "rank": 50},
            
            # High Potential Mid-Caps
            {"symbol": "GRT", "name": "The Graph", "rank": 51},
            {"symbol": "FET", "name": "Fetch.ai", "rank": 52},
            {"symbol": "LRC", "name": "Loopring", "rank": 53},
            {"symbol": "ENJ", "name": "Enjin Coin", "rank": 54},
            {"symbol": "CHZ", "name": "Chiliz", "rank": 55},
            {"symbol": "BAT", "name": "Basic Attention Token", "rank": 56},
            {"symbol": "XTZ", "name": "Tezos", "rank": 57},
            {"symbol": "MINA", "name": "Mina Protocol", "rank": 58},
            {"symbol": "KCS", "name": "KuCoin Shares", "rank": 59},
            {"symbol": "YFI", "name": "yearn.finance", "rank": 60},
            
            # Privacy & Security
            {"symbol": "ZEC", "name": "Zcash", "rank": 61},
            {"symbol": "DASH", "name": "Dash", "rank": 62},
            {"symbol": "DCR", "name": "Decred", "rank": 63},
            {"symbol": "WAVES", "name": "Waves", "rank": 64},
            {"symbol": "ZIL", "name": "Zilliqa", "rank": 65},
            
            # Emerging DeFi & Layer-2
            {"symbol": "BAL", "name": "Balancer", "rank": 66},
            {"symbol": "BAND", "name": "Band Protocol", "rank": 67},
            {"symbol": "OCEAN", "name": "Ocean Protocol", "rank": 68},
            {"symbol": "UMA", "name": "UMA Protocol", "rank": 69},
            {"symbol": "ALPHA", "name": "Alpha Finance", "rank": 70},
            {"symbol": "ANKR", "name": "Ankr", "rank": 71},
            {"symbol": "SKL", "name": "SKALE Network", "rank": 72},
            {"symbol": "CTSI", "name": "Cartesi", "rank": 73},
            {"symbol": "CELR", "name": "Celer Network", "rank": 74},
            {"symbol": "STORJ", "name": "Storj", "rank": 75},
            
            # High-Volatility Opportunities
            {"symbol": "RSR", "name": "Reserve Rights", "rank": 76},
            {"symbol": "REN", "name": "Ren Protocol", "rank": 77},
            {"symbol": "KNC", "name": "Kyber Network", "rank": 78},
            {"symbol": "NMR", "name": "Numeraire", "rank": 79},
            {"symbol": "BNT", "name": "Bancor", "rank": 80},
            {"symbol": "KAVA", "name": "Kava", "rank": 81},
            {"symbol": "COTI", "name": "COTI", "rank": 82},
            {"symbol": "NKN", "name": "NKN", "rank": 83},
            {"symbol": "OGN", "name": "Origin Protocol", "rank": 84},
            {"symbol": "NANO", "name": "Nano", "rank": 85},
            
            # Micro-Cap Moonshots
            {"symbol": "RVN", "name": "Ravencoin", "rank": 86},
            {"symbol": "DGB", "name": "DigiByte", "rank": 87},
            {"symbol": "SC", "name": "Siacoin", "rank": 88},
            {"symbol": "HOT", "name": "Holo", "rank": 89},
            {"symbol": "IOST", "name": "IOST", "rank": 90},
            {"symbol": "DUSK", "name": "Dusk Network", "rank": 91},
            {"symbol": "WIN", "name": "WINkLink", "rank": 92},
            {"symbol": "BTT", "name": "BitTorrent", "rank": 93},
            {"symbol": "TWT", "name": "Trust Wallet Token", "rank": 94},
            {"symbol": "JST", "name": "JUST", "rank": 95},
            
            # Specialized Tokens
            {"symbol": "SXP", "name": "Solar", "rank": 96},
            {"symbol": "HARD", "name": "Kava Lend", "rank": 97},
            {"symbol": "SUN", "name": "Sun Token", "rank": 98},
            {"symbol": "ICX", "name": "ICON", "rank": 99},
            {"symbol": "ONT", "name": "Ontology", "rank": 100}
        ]
    
    def _initialize_portfolio(self) -> Dict:
        """Initialize portfolio with starting values for each cryptocurrency."""
        portfolio = {}
        
        for crypto in self.crypto_list:
            symbol = crypto["symbol"]
            # Simulate realistic starting prices based on rank
            base_price = self._generate_realistic_price(crypto["rank"])
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
                "projected_sell_pnl": self._calculate_target_sell_price(base_price, crypto["rank"]) * quantity - self.initial_value
            }
            
        return portfolio
    
    def _generate_realistic_price(self, rank: int) -> float:
        """Generate realistic cryptocurrency prices based on market cap rank and performance potential."""
        if rank == 1:  # BTC
            return np.random.uniform(65000, 75000)  # Bitcoin range
        elif rank == 2:  # ETH
            return np.random.uniform(3000, 4000)    # Ethereum range
        elif rank <= 5:  # Top 3-5 (SOL, XRP, DOGE)
            return np.random.uniform(50, 250)      # Major alts
        elif rank <= 10:  # Top 6-10
            return np.random.uniform(10, 100)      # Established alts
        elif rank <= 20:  # High-growth winners (SAROS, XCN, etc.)
            return np.random.uniform(1, 50)        # Mid-range alts
        elif rank <= 40:  # Strong altcoins
            return np.random.uniform(0.50, 20)     # Mid-cap range
        elif rank <= 60:  # DeFi leaders
            return np.random.uniform(0.20, 10)     # Established DeFi
        elif rank <= 80:  # Infrastructure tokens
            return np.random.uniform(0.05, 5)      # Growing projects
        else:  # Micro-cap moonshots
            return np.random.uniform(0.001, 2)     # Small caps
    
    def simulate_price_movements(self, hours_elapsed: int = 1) -> None:
        """Simulate realistic price movements for all cryptocurrencies."""
        timestamp = datetime.now()
        
        for symbol in self.portfolio_data:
            crypto = self.portfolio_data[symbol]
            current_price = crypto["current_price"]
            
            # Generate realistic volatility based on market cap rank
            volatility = self._get_volatility_by_rank(crypto["rank"])
            
            # Generate price change with some correlation to Bitcoin
            btc_change = np.random.normal(0, 0.02)  # Bitcoin baseline volatility
            individual_change = np.random.normal(0, volatility)
            
            # Combine BTC correlation (30%) with individual movement (70%)
            total_change = 0.3 * btc_change + 0.7 * individual_change
            
            # Apply the price change
            new_price = current_price * (1 + total_change)
            new_price = max(new_price, current_price * 0.5)  # Prevent more than 50% crash
            
            # Update portfolio data
            crypto["current_price"] = new_price
            crypto["current_value"] = crypto["quantity"] * new_price
            crypto["pnl"] = crypto["current_value"] - crypto["initial_value"]
            crypto["pnl_percent"] = (crypto["pnl"] / crypto["initial_value"]) * 100
            
            # Update projected sell P&L
            if crypto.get("target_sell_price"):
                sell_value = crypto["target_sell_price"] * crypto["quantity"]
                crypto["projected_sell_pnl"] = sell_value - crypto["initial_value"]
            
            # Update target prices based on current price
            crypto["target_sell_price"] = self._calculate_target_sell_price(new_price, crypto["rank"])
            crypto["target_buy_price"] = self._calculate_target_buy_price(new_price, crypto["rank"])
            
            # Store price history
            if symbol not in self.price_history:
                self.price_history[symbol] = []
            
            self.price_history[symbol].append({
                "timestamp": timestamp,
                "price": new_price,
                "volume": np.random.uniform(100000, 10000000)  # Simulated volume
            })
            
            # Keep only last 100 data points per crypto
            if len(self.price_history[symbol]) > 100:
                self.price_history[symbol] = self.price_history[symbol][-100:]
    
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