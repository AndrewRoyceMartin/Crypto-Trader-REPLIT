"""
Simulated OKX Exchange for realistic paper trading.
Uses exact OKX API v5 field naming conventions and response structure.
"""

import time
import random
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from .base import BaseExchange


class SimulatedOKX(BaseExchange):
    """Simulated OKX exchange for realistic paper trading."""
    
    def __init__(self, config: Dict):
        """Initialize simulated OKX exchange with proper API v5 structure."""
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        
        # Connection state
        self._is_connected = False
        
        # OKX API v5 Balance Structure
        self.balance_data = [
            {
                "ccy": "USDT",           # Currency
                "bal": "100000.0",       # Total balance  
                "frozenBal": "0",        # Frozen balance
                "availBal": "100000.0"   # Available balance
            }
        ]
        
        # OKX API v5 Position Structure
        self.position_data = []  # Array of position objects
        
        # Order tracking with OKX format
        self.orders = {}
        self.trades = []
        self.order_id_counter = 312269865356374016  # OKX-style order ID
        
        # Market simulation parameters
        self.spread_percentage = 0.001  # 0.1% spread
        self.slippage_percentage = 0.0005  # 0.05% slippage
        self.latency_ms = random.randint(10, 50)  # Realistic latency
        
        # Market hours (24/7 for crypto)
        self.market_open = True
        
        # Realistic simulated prices (based on real market prices as of August 2025)
        self.simulated_base_prices = {
            'BTC': 67500.00,
            'ETH': 3850.00,
            'SOL': 185.50,
            'XRP': 0.65,
            'DOGE': 0.14,
            'ADA': 0.55,
            'AVAX': 32.80,
            'LINK': 18.20,
            'DOT': 7.85,
            'UNI': 12.40,
            'NEAR': 8.90,
            'ATOM': 9.75,
            'FTM': 0.85,
            'ALGO': 0.28,
            'VET': 0.038,
            'ICP': 12.60,
            'AAVE': 165.00,
            'MKR': 2850.00,
            'COMP': 78.50,
            'CRV': 0.42,
            'UMA': 3.20,
            'BAL': 4.80,
            'YFI': 8900.00,
            'SUSHI': 1.25,
            'SNX': 3.40,
            'LDO': 2.10,
            'APT': 11.80,
            'SUI': 1.95,
            'ARB': 0.88,
            'OP': 2.85,
            'MATIC': 0.78,
            'IMX': 1.65,
            'LRC': 0.32,
            'MANA': 0.52,
            'SAND': 0.58,
            'AXS': 8.90,
            'ENJ': 0.45,
            'GALA': 0.038,
            'CHZ': 0.095,
            'FLOW': 1.20,
            'THETA': 1.85,
            'REVV': 0.028,
            'TLM': 0.024,
            'SLP': 0.0045,
            'ALPHA': 0.18,
            'GHST': 2.80,
            'ALICE': 1.95,
            'CREAM': 28.50,
            'CELO': 0.95,
            'KAVA': 0.58,
            'SCRT': 0.85,
            'ROSE': 0.085,
            'SHIB': 0.000028,
            'PEPE': 0.000018,
            'FLOKI': 0.00025,
            'BABYDOGE': 0.0000048,
            'ELON': 0.00000058,
            'DOGO': 0.000012,
            'AKITA': 0.0000018,
            'KISHU': 0.00000000085,
            'SAITAMA': 0.0000000065,
            'LEASH': 580.00,
            'FTT': 2.85,
            'KCS': 12.40,
            'HT': 6.80,
            'OKB': 58.50,
            'LEO': 6.95,
            'CRO': 0.125,
            'GT': 8.20,
            'BGB': 1.85,
            'XMR': 185.00,
            'ZEC': 48.50,
            'DASH': 38.20,
            'ZCASH': 48.50,
            'BEAM': 0.085,
            'GRIN': 0.048,
            'FIRO': 2.40,
            'ARRR': 0.58,
            'XLM': 0.125,
            'XDC': 0.048,
            'IOTA': 0.285,
            'NANO': 1.85,
            'RVN': 0.028,
            'DGB': 0.018,
            'SYS': 0.185,
            'VTC': 0.058,
            'MONA': 0.185,
            'QNT': 125.00,
            'BNB': 685.00,
            'RNDR': 8.90,
            'FIL': 8.20,
            'HBAR': 0.085,
            'LTC': 95.50,
            'BCH': 485.00,
            'ETC': 28.50,
            'XTZ': 1.20,
            'EGLD': 48.50,
            'NEO': 18.50,
            'WAVES': 2.85,
            'KSM': 38.50,
            'ONE': 0.018,
            'HOT': 0.0028,
            'IOST': 0.012,
            'ZIL': 0.028,
            'ICX': 0.28,
            'ONT': 0.38,
            'REN': 0.085,
            'ZRX': 0.58,
            'STORJ': 0.85,
            'GRT': 0.28
        }
        
        # Price volatility simulation
        self.price_last_update = {}
        self.price_trends = {}  # Track price movement trends
        
    def connect(self) -> bool:
        """Connect to simulated OKX exchange."""
        try:
            self.logger.info("Connecting to Simulated OKX Exchange...")
            
            # Simulate connection delay
            time.sleep(0.1)
            
            # Initialize market data
            self._initialize_markets()
            
            self._is_connected = True
            self.logger.info("Successfully connected to Simulated OKX Exchange")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Simulated OKX: {str(e)}")
            return False
    
    def is_connected(self) -> bool:
        """Check connection status."""
        return self._is_connected
    
    def _initialize_markets(self):
        """Initialize available trading pairs and market data."""
        # Common crypto pairs available on OKX
        self.markets = {
            'BTC/USDT': {'min_amount': 0.00001, 'precision': 8},
            'ETH/USDT': {'min_amount': 0.0001, 'precision': 6},
            'SOL/USDT': {'min_amount': 0.01, 'precision': 4},
            'XRP/USDT': {'min_amount': 1.0, 'precision': 4},
            'DOGE/USDT': {'min_amount': 10.0, 'precision': 6},
            'ADA/USDT': {'min_amount': 1.0, 'precision': 6},
            'AVAX/USDT': {'min_amount': 0.01, 'precision': 4},
            'LINK/USDT': {'min_amount': 0.1, 'precision': 4},
            'DOT/USDT': {'min_amount': 0.1, 'precision': 4},
            'UNI/USDT': {'min_amount': 0.1, 'precision': 4},
        }
        
        self.logger.info(f"Initialized {len(self.markets)} trading pairs")
    
    def get_balance(self) -> Dict:
        """Get account balance in OKX API v5 format."""
        if not self._is_connected:
            raise Exception("Not connected to exchange")
        
        # Return OKX API v5 structure
        return {
            "code": "0",
            "msg": "",
            "data": self.balance_data.copy()
        }
    
    def get_ticker(self, symbol: str) -> Dict:
        """Get ticker data in OKX API v5 format."""
        if not self._is_connected:
            raise Exception("Not connected to exchange")
        
        price = self._get_current_price(symbol)
        if not price:
            raise Exception(f"Symbol {symbol} not found")
        
        # OKX uses string values for precision
        spread = price * self.spread_percentage
        
        return {
            "code": "0",
            "msg": "",
            "data": [{
                "instId": symbol,        # Instrument ID
                "last": str(price),      # Last price
                "lastSz": "0.1",         # Last size
                "askPx": str(price + spread/2),  # Ask price
                "askSz": "1.0",          # Ask size  
                "bidPx": str(price - spread/2),  # Bid price
                "bidSz": "1.0",          # Bid size
                "open24h": str(price * 0.98),    # 24h open
                "high24h": str(price * 1.02),    # 24h high
                "low24h": str(price * 0.98),     # 24h low
                "vol24h": str(random.uniform(1000, 10000)),  # 24h volume
                "ts": str(int(datetime.now().timestamp() * 1000))  # Timestamp
            }]
        }
    
    def place_order(self, symbol: str, side: str, amount: float, 
                   order_type: str = 'market', price: Optional[float] = None) -> Dict:
        """Place order using OKX API v5 format."""
        if not self._is_connected:
            raise Exception("Not connected to exchange")
        
        if not self.market_open:
            raise Exception("Market is closed")
        
        # Validate symbol
        if symbol not in self.markets:
            return {
                "code": "1",
                "msg": "",
                "data": [{
                    "clOrdId": "",
                    "ordId": "",
                    "sCode": "51000",
                    "sMsg": f"Instrument {symbol} does not exist",
                    "tag": ""
                }]
            }
        
        # Generate OKX-style order ID
        order_id = str(self.order_id_counter)
        self.order_id_counter += 1
        
        # Get current price
        current_price = self._get_current_price(symbol)
        if not current_price:
            return {
                "code": "1", 
                "msg": "",
                "data": [{
                    "clOrdId": "",
                    "ordId": "",
                    "sCode": "51001",
                    "sMsg": "Unable to get price",
                    "tag": ""
                }]
            }
        
        # Calculate execution price
        if order_type == 'market':
            if side == 'buy':
                execution_price = current_price * (1 + self.slippage_percentage)
            else:
                execution_price = current_price * (1 - self.slippage_percentage)
        else:
            execution_price = price or current_price
        
        # Execute order logic
        try:
            self._execute_order_internal(symbol, side, amount, execution_price)
            
            # Record trade in OKX format
            trade = {
                "tradeId": order_id + "T",
                "instId": symbol,
                "ordId": order_id,
                "side": side,
                "sz": str(amount),
                "px": str(execution_price),
                "fee": str(amount * execution_price * 0.001),
                "ts": str(int(datetime.now().timestamp() * 1000))
            }
            
            self.trades.append(trade)
            
            # Return OKX API v5 successful response
            return {
                "code": "0",
                "msg": "",
                "data": [{
                    "ordId": order_id,
                    "clOrdId": f"client_{order_id}",
                    "tag": "",
                    "sCode": "0",
                    "sMsg": "",
                    "reqId": ""
                }]
            }
            
        except Exception as e:
            return {
                "code": "1",
                "msg": "",
                "data": [{
                    "clOrdId": "",
                    "ordId": "",
                    "sCode": "51008",
                    "sMsg": str(e),
                    "tag": ""
                }]
            }
    
    def get_trades(self, symbol: Optional[str] = None, limit: int = 100) -> Dict:
        """Get trade history in OKX API v5 format."""
        if not self._is_connected:
            raise Exception("Not connected to exchange")
        
        trades = self.trades.copy()
        
        if symbol:
            trades = [t for t in trades if t.get('instId') == symbol]
        
        # Return most recent trades first
        trades.reverse()
        
        return {
            "code": "0",
            "msg": "",
            "data": trades[:limit]
        }
    
    def get_ohlcv(self, symbol: str, timeframe: str, limit: int = 100) -> pd.DataFrame:
        """Get OHLCV data (simulated with live price base)."""
        if not self._is_connected:
            raise Exception("Not connected to exchange")
        
        if symbol not in self.markets:
            raise Exception(f"Symbol {symbol} not supported")
        
        # Get current price as base
        current_price = self._get_current_price(symbol)
        if not current_price:
            raise Exception(f"Unable to get price for {symbol}")
        
        # Generate simulated OHLCV data
        data = []
        now = datetime.now()
        
        # Convert timeframe to minutes
        timeframe_minutes = self._timeframe_to_minutes(timeframe)
        
        for i in range(limit):
            timestamp = now - timedelta(minutes=timeframe_minutes * (limit - i))
            
            # Simulate price movement (random walk)
            volatility = 0.02  # 2% volatility
            change = random.gauss(0, volatility)
            base_price = current_price * (1 + change * 0.1)
            
            # Generate OHLCV
            open_price = base_price * random.uniform(0.99, 1.01)
            high_price = open_price * random.uniform(1.0, 1.03)
            low_price = open_price * random.uniform(0.97, 1.0)
            close_price = open_price * random.uniform(0.98, 1.02)
            volume = random.uniform(10000, 100000)
            
            data.append([
                int(timestamp.timestamp() * 1000),
                open_price,
                high_price,
                low_price,
                close_price,
                volume
            ])
        
        # Create DataFrame with correct columns parameter
        df = pd.DataFrame(data)
        df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        return df
    
    def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current simulated price for trading pair."""
        try:
            # Extract base symbol from trading pair (e.g., 'BTC/USDT' -> 'BTC')
            base_symbol = symbol.split('/')[0]
            
            # Check if we have a simulated price for this symbol
            if base_symbol not in self.simulated_base_prices:
                self.logger.warning(f"No simulated price data for {base_symbol}")
                return None
            
            # Get base price
            base_price = self.simulated_base_prices[base_symbol]
            
            # Apply realistic price simulation with small volatility
            current_time = time.time()
            last_update = self.price_last_update.get(base_symbol, current_time - 60)
            
            # Only update price if enough time has passed (simulate real market movement)
            if current_time - last_update > 30:  # Update every 30 seconds
                # Generate small random price movement (±2% max)
                price_change_percent = random.uniform(-0.02, 0.02)
                
                # Apply trend continuity for more realistic movement
                if base_symbol in self.price_trends:
                    # 70% chance to continue existing trend
                    if random.random() < 0.7:
                        trend = self.price_trends[base_symbol]
                        price_change_percent = abs(price_change_percent) * trend
                
                # Update base price with volatility
                new_price = base_price * (1 + price_change_percent)
                self.simulated_base_prices[base_symbol] = new_price
                self.price_last_update[base_symbol] = current_time
                
                # Set trend for next update
                self.price_trends[base_symbol] = 1 if price_change_percent > 0 else -1
                
                self.logger.debug(f"Updated {base_symbol} price: ${base_price:.6f} -> ${new_price:.6f} ({price_change_percent*100:.3f}%)")
            
            return self.simulated_base_prices[base_symbol]
            
        except Exception as e:
            self.logger.error(f"Error getting simulated price for {symbol}: {str(e)}")
            return None
    
    def _execute_order_internal(self, symbol: str, side: str, amount: float, execution_price: float):
        """Internal order execution with balance management."""
        if side == 'buy':
            cost = amount * execution_price
            
            # Check USDT balance
            usdt_bal = float(self.balance_data[0]['availBal'])
            if cost > usdt_bal:
                raise Exception("Insufficient USDT balance")
            
            # Update USDT balance
            new_usdt_bal = usdt_bal - cost
            self.balance_data[0]['bal'] = str(new_usdt_bal)
            self.balance_data[0]['availBal'] = str(new_usdt_bal)
            
            # Update or create position
            base_symbol = symbol.split('/')[0]
            self._update_position(base_symbol, amount, execution_price, 'buy')
            
        else:  # sell
            base_symbol = symbol.split('/')[0]
            position = self._find_position(base_symbol)
            
            if not position or float(position['pos']) < amount:
                raise Exception(f"Insufficient {base_symbol} balance")
            
            # Calculate proceeds
            proceeds = amount * execution_price
            
            # Update USDT balance
            usdt_bal = float(self.balance_data[0]['availBal'])
            new_usdt_bal = usdt_bal + proceeds
            self.balance_data[0]['bal'] = str(new_usdt_bal)
            self.balance_data[0]['availBal'] = str(new_usdt_bal)
            
            # Update position
            self._update_position(base_symbol, amount, execution_price, 'sell')
    
    def _update_position(self, base_symbol: str, amount: float, price: float, side: str):
        """Update position using OKX API v5 format."""
        position = self._find_position(base_symbol)
        
        if not position:
            if side == 'buy':
                # Create new position
                new_position = {
                    "instId": f"{base_symbol}-USDT-SWAP",
                    "posId": f"pos_{base_symbol}_{int(time.time())}",
                    "posSide": "net",
                    "pos": str(amount),
                    "ccy": "USDT",
                    "avgPx": str(price),
                    "upl": "0",
                    "margin": str(amount * price * 0.1),  # 10% margin
                    "mgnMode": "isolated",
                    "lever": "1",
                    "markPx": str(price),
                    "notionalUsd": str(amount * price),
                    "uTime": str(int(datetime.now().timestamp() * 1000))
                }
                self.position_data.append(new_position)
        else:
            # Update existing position
            old_pos = float(position['pos'])
            old_avg = float(position['avgPx'])
            
            if side == 'buy':
                # Weighted average price calculation
                new_pos = old_pos + amount
                new_avg = ((old_pos * old_avg) + (amount * price)) / new_pos
                position['pos'] = str(new_pos)
                position['avgPx'] = str(new_avg)
            else:  # sell
                new_pos = old_pos - amount
                if new_pos <= 0:
                    # Remove position if fully closed
                    self.position_data.remove(position)
                else:
                    position['pos'] = str(new_pos)
            
            if position in self.position_data:
                position['uTime'] = str(int(datetime.now().timestamp() * 1000))
    
    def _find_position(self, base_symbol: str) -> Optional[Dict]:
        """Find position by base symbol."""
        for position in self.position_data:
            if position['instId'].startswith(base_symbol):
                return position
        return None
    
    def _timeframe_to_minutes(self, timeframe: str) -> int:
        """Convert timeframe string to minutes."""
        timeframe_map = {
            '1m': 1,
            '5m': 5,
            '15m': 15,
            '30m': 30,
            '1h': 60,
            '4h': 240,
            '1d': 1440
        }
        return timeframe_map.get(timeframe, 60)
    
    def get_positions(self) -> Dict:
        """Get positions in OKX API v5 format."""
        if not self._is_connected:
            raise Exception("Not connected to exchange")
        
        return {
            "code": "0",
            "msg": "",
            "data": self.position_data.copy()
        }
    
    def get_portfolio_summary(self) -> Dict:
        """Get comprehensive portfolio summary in OKX format."""
        if not self._is_connected:
            raise Exception("Not connected to exchange")
        
        balance_response = self.get_balance()
        positions_response = self.get_positions()
        
        usdt_balance = float(self.balance_data[0]['availBal'])
        total_position_value = 0
        
        # Calculate total position value
        for position in positions_response['data']:
            current_price = self._get_current_price(position['instId'].replace('-USDT-SWAP', '/USDT'))
            if current_price:
                pos_value = float(position['pos']) * current_price
                total_position_value += pos_value
        
        return {
            "code": "0",
            "msg": "",
            "data": {
                "totalEq": str(usdt_balance + total_position_value),  # Total equity
                "isoEq": str(total_position_value),  # Isolated margin equity
                "adjEq": str(usdt_balance + total_position_value * 0.9),  # Adjusted equity
                "ordFroz": "0",  # Margin frozen for open orders
                "imr": str(total_position_value * 0.1),  # Initial margin requirement
                "mmr": str(total_position_value * 0.05),  # Maintenance margin requirement
                "mgnRatio": "999" if total_position_value == 0 else str((usdt_balance + total_position_value) / (total_position_value * 0.05)),
                "notionalUsd": str(total_position_value),
                "uTime": str(int(datetime.now().timestamp() * 1000)),
                "details": balance_response['data']
            }
        }
    
    def simulate_market_movement(self):
        """Simulate market movement for testing."""
        if not self._is_connected:
            return
        
        # Update position mark prices and unrealized P&L
        for position in self.position_data:
            symbol = position['instId'].replace('-USDT-SWAP', '/USDT')
            current_price = self._get_current_price(symbol)
            
            if current_price:
                position['markPx'] = str(current_price)
                
                # Calculate unrealized P&L
                pos_size = float(position['pos'])
                avg_price = float(position['avgPx'])
                upl = (current_price - avg_price) * pos_size
                position['upl'] = str(upl)
                position['uplRatio'] = str(upl / (avg_price * pos_size) if pos_size > 0 else 0)
                position['uTime'] = str(int(datetime.now().timestamp() * 1000))
        
        self.logger.debug("Market simulation tick - positions updated")

    def cancel_order(self, order_id: str, symbol: str) -> Dict:
        """Cancel an order - required abstract method."""
        if order_id in self.orders:
            self.orders[order_id]['state'] = 'canceled'
            return {
                "code": "0",
                "msg": "",
                "data": [{
                    "ordId": order_id,
                    "clOrdId": self.orders[order_id].get('clOrdId', ''),
                    "sCode": "0",
                    "sMsg": ""
                }]
            }
        return {
            "code": "1",
            "msg": "",
            "data": [{
                "ordId": order_id,
                "clOrdId": "",
                "sCode": "51000",
                "sMsg": "Order not found"
            }]
        }

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get open orders - required abstract method."""
        open_orders = [order for order in self.orders.values() 
                      if order['state'] in ['live', 'partially_filled']]
        if symbol:
            target_inst = f'{symbol}-USDT-SWAP'
            open_orders = [order for order in open_orders if order['instId'] == target_inst]
        return {
            "code": "0",
            "msg": "",
            "data": open_orders
        }