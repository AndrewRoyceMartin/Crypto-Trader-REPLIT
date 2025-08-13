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
        """Get list of top 100 cryptocurrencies with their details."""
        return [
            {"symbol": "BTC", "name": "Bitcoin", "rank": 1},
            {"symbol": "ETH", "name": "Ethereum", "rank": 2},
            {"symbol": "USDT", "name": "Tether", "rank": 3},
            {"symbol": "BNB", "name": "BNB", "rank": 4},
            {"symbol": "SOL", "name": "Solana", "rank": 5},
            {"symbol": "USDC", "name": "USD Coin", "rank": 6},
            {"symbol": "XRP", "name": "XRP", "rank": 7},
            {"symbol": "DOGE", "name": "Dogecoin", "rank": 8},
            {"symbol": "TON", "name": "Toncoin", "rank": 9},
            {"symbol": "ADA", "name": "Cardano", "rank": 10},
            {"symbol": "AVAX", "name": "Avalanche", "rank": 11},
            {"symbol": "SHIB", "name": "Shiba Inu", "rank": 12},
            {"symbol": "DOT", "name": "Polkadot", "rank": 13},
            {"symbol": "TRX", "name": "TRON", "rank": 14},
            {"symbol": "LINK", "name": "Chainlink", "rank": 15},
            {"symbol": "MATIC", "name": "Polygon", "rank": 16},
            {"symbol": "ICP", "name": "Internet Computer", "rank": 17},
            {"symbol": "LTC", "name": "Litecoin", "rank": 18},
            {"symbol": "BCH", "name": "Bitcoin Cash", "rank": 19},
            {"symbol": "UNI", "name": "Uniswap", "rank": 20},
            {"symbol": "ATOM", "name": "Cosmos", "rank": 21},
            {"symbol": "ETC", "name": "Ethereum Classic", "rank": 22},
            {"symbol": "HBAR", "name": "Hedera", "rank": 23},
            {"symbol": "FIL", "name": "Filecoin", "rank": 24},
            {"symbol": "APT", "name": "Aptos", "rank": 25},
            {"symbol": "XLM", "name": "Stellar", "rank": 26},
            {"symbol": "VET", "name": "VeChain", "rank": 27},
            {"symbol": "ALGO", "name": "Algorand", "rank": 28},
            {"symbol": "SAND", "name": "The Sandbox", "rank": 29},
            {"symbol": "MANA", "name": "Decentraland", "rank": 30},
            {"symbol": "THETA", "name": "Theta Network", "rank": 31},
            {"symbol": "FTM", "name": "Fantom", "rank": 32},
            {"symbol": "EGLD", "name": "MultiversX", "rank": 33},
            {"symbol": "AXS", "name": "Axie Infinity", "rank": 34},
            {"symbol": "FLOW", "name": "Flow", "rank": 35},
            {"symbol": "XTZ", "name": "Tezos", "rank": 36},
            {"symbol": "AAVE", "name": "Aave", "rank": 37},
            {"symbol": "KCS", "name": "KuCoin Shares", "rank": 38},
            {"symbol": "CHZ", "name": "Chiliz", "rank": 39},
            {"symbol": "ENJ", "name": "Enjin Coin", "rank": 40},
            {"symbol": "MINA", "name": "Mina", "rank": 41},
            {"symbol": "ZEC", "name": "Zcash", "rank": 42},
            {"symbol": "DASH", "name": "Dash", "rank": 43},
            {"symbol": "COMP", "name": "Compound", "rank": 44},
            {"symbol": "YFI", "name": "yearn.finance", "rank": 45},
            {"symbol": "BAT", "name": "Basic Attention Token", "rank": 46},
            {"symbol": "ZIL", "name": "Zilliqa", "rank": 47},
            {"symbol": "WAVES", "name": "Waves", "rank": 48},
            {"symbol": "OMG", "name": "OMG Network", "rank": 49},
            {"symbol": "QTUM", "name": "Qtum", "rank": 50},
            {"symbol": "ICX", "name": "ICON", "rank": 51},
            {"symbol": "ZRX", "name": "0x", "rank": 52},
            {"symbol": "ONT", "name": "Ontology", "rank": 53},
            {"symbol": "LSK", "name": "Lisk", "rank": 54},
            {"symbol": "DCR", "name": "Decred", "rank": 55},
            {"symbol": "NANO", "name": "Nano", "rank": 56},
            {"symbol": "RVN", "name": "Ravencoin", "rank": 57},
            {"symbol": "DGB", "name": "DigiByte", "rank": 58},
            {"symbol": "SC", "name": "Siacoin", "rank": 59},
            {"symbol": "HOT", "name": "Holo", "rank": 60},
            {"symbol": "IOST", "name": "IOST", "rank": 61},
            {"symbol": "CRV", "name": "Curve DAO Token", "rank": 62},
            {"symbol": "SNX", "name": "Synthetix", "rank": 63},
            {"symbol": "SUSHI", "name": "SushiSwap", "rank": 64},
            {"symbol": "1INCH", "name": "1inch", "rank": 65},
            {"symbol": "ALPHA", "name": "Alpha Finance Lab", "rank": 66},
            {"symbol": "BAND", "name": "Band Protocol", "rank": 67},
            {"symbol": "OCEAN", "name": "Ocean Protocol", "rank": 68},
            {"symbol": "RSR", "name": "Reserve Rights", "rank": 69},
            {"symbol": "REN", "name": "Ren", "rank": 70},
            {"symbol": "KNC", "name": "Kyber Network", "rank": 71},
            {"symbol": "LRC", "name": "Loopring", "rank": 72},
            {"symbol": "STORJ", "name": "Storj", "rank": 73},
            {"symbol": "NMR", "name": "Numeraire", "rank": 74},
            {"symbol": "UMA", "name": "UMA", "rank": 75},
            {"symbol": "BNT", "name": "Bancor", "rank": 76},
            {"symbol": "REP", "name": "Augur", "rank": 77},
            {"symbol": "MLN", "name": "Melon", "rank": 78},
            {"symbol": "GNT", "name": "Golem", "rank": 79},
            {"symbol": "BAL", "name": "Balancer", "rank": 80},
            {"symbol": "MKR", "name": "Maker", "rank": 81},
            {"symbol": "GRT", "name": "The Graph", "rank": 82},
            {"symbol": "FET", "name": "Fetch.ai", "rank": 83},
            {"symbol": "CELR", "name": "Celer Network", "rank": 84},
            {"symbol": "ANKR", "name": "Ankr", "rank": 85},
            {"symbol": "CTSI", "name": "Cartesi", "rank": 86},
            {"symbol": "SKL", "name": "SKALE Network", "rank": 87},
            {"symbol": "NKN", "name": "NKN", "rank": 88},
            {"symbol": "COTI", "name": "COTI", "rank": 89},
            {"symbol": "POLY", "name": "Polymath", "rank": 90},
            {"symbol": "KAVA", "name": "Kava", "rank": 91},
            {"symbol": "OGN", "name": "Origin Protocol", "rank": 92},
            {"symbol": "DUSK", "name": "Dusk Network", "rank": 93},
            {"symbol": "HARD", "name": "Kava Lend", "rank": 94},
            {"symbol": "SXP", "name": "Swipe", "rank": 95},
            {"symbol": "WIN", "name": "WINkLink", "rank": 96},
            {"symbol": "TWT", "name": "Trust Wallet Token", "rank": 97},
            {"symbol": "JST", "name": "JUST", "rank": 98},
            {"symbol": "SUN", "name": "Sun", "rank": 99},
            {"symbol": "BTT", "name": "BitTorrent", "rank": 100}
        ]
    
    def _initialize_portfolio(self) -> Dict:
        """Initialize portfolio with starting values for each cryptocurrency."""
        portfolio = {}
        
        for crypto in self.crypto_list:
            symbol = crypto["symbol"]
            # Simulate realistic starting prices based on rank
            base_price = self._generate_realistic_price(crypto["rank"])
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
                "pnl_percent": 0.0
            }
            
        return portfolio
    
    def _generate_realistic_price(self, rank: int) -> float:
        """Generate realistic cryptocurrency prices based on market cap rank."""
        if rank <= 5:  # Top 5 cryptos
            return np.random.uniform(20000, 70000)  # BTC-like prices
        elif rank <= 10:  # Top 10
            return np.random.uniform(1000, 5000)    # ETH-like prices
        elif rank <= 20:  # Top 20
            return np.random.uniform(50, 1000)      # Major alts
        elif rank <= 50:  # Top 50
            return np.random.uniform(1, 100)       # Mid-cap alts
        else:  # Rest
            return np.random.uniform(0.01, 10)     # Small-cap alts
    
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
        """Get appropriate volatility based on cryptocurrency rank."""
        if rank <= 5:
            return 0.015   # 1.5% volatility for top cryptos
        elif rank <= 10:
            return 0.025   # 2.5% for top 10
        elif rank <= 20:
            return 0.035   # 3.5% for top 20
        elif rank <= 50:
            return 0.05    # 5% for top 50
        else:
            return 0.08    # 8% for smaller caps
    
    def get_portfolio_summary(self) -> Dict:
        """Get complete portfolio summary statistics."""
        total_initial_value = sum(crypto["initial_value"] for crypto in self.portfolio_data.values())
        total_current_value = sum(crypto["current_value"] for crypto in self.portfolio_data.values())
        total_pnl = total_current_value - total_initial_value
        total_pnl_percent = (total_pnl / total_initial_value) * 100
        
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