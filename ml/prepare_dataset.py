# ml/prepare_dataset.py

import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

class SignalDatasetPreparer:
    def __init__(self):
        self.base_url = "https://api.binance.com/api/v3"  # Using Binance for price data (public API)
        
    def load_signals(self, csv_path: str = "signals_log.csv") -> pd.DataFrame:
        """Load signal data from CSV"""
        try:
            df = pd.read_csv(csv_path)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            print(f"✅ Loaded {len(df)} signals from {csv_path}")
            return df
        except FileNotFoundError:
            print(f"❌ Signal file {csv_path} not found")
            return pd.DataFrame()
    
    def get_future_price(self, symbol: str, timestamp: datetime, hours_ahead: int = 24) -> float:
        """
        Get the price of a crypto X hours after the signal timestamp.
        Uses Binance historical klines for accurate pricing.
        """
        # Convert symbol format (ETH -> ETHUSDT)
        binance_symbol = f"{symbol}USDT" if not symbol.endswith("USDT") else symbol
        
        # Calculate future timestamp (milliseconds)
        future_time = timestamp + timedelta(hours=hours_ahead)
        start_time = int(future_time.timestamp() * 1000)
        end_time = start_time + (60 * 1000)  # 1 minute window
        
        try:
            # Get historical kline data from Binance
            url = f"{self.base_url}/klines"
            params = {
                "symbol": binance_symbol,
                "interval": "1m",
                "startTime": start_time,
                "endTime": end_time,
                "limit": 1
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data and len(data) > 0:
                # Kline format: [timestamp, open, high, low, close, volume, ...]
                close_price = float(data[0][4])  # Close price
                return close_price
            else:
                return None
                
        except Exception as e:
            print(f"   ⚠️ Error fetching future price for {symbol}: {e}")
            return None
    
    def create_labels(self, df: pd.DataFrame, profit_threshold: float = 0.02, hours_ahead: int = 24) -> pd.DataFrame:
        """
        Create profit labels for each signal.
        
        Args:
            df: DataFrame with signals
            profit_threshold: Minimum profit % to consider successful (default 2%)
            hours_ahead: Hours to look ahead for profit calculation (default 24)
        """
        print(f"🔄 Creating profit labels ({profit_threshold*100}% threshold, {hours_ahead}h ahead)...")
        
        labeled_data = []
        
        for idx, row in df.iterrows():
            signal_data = {
                'signal_id': idx,
                'timestamp': row['timestamp'],
                'symbol': row['symbol'],
                'current_price': row['current_price'],
                'confidence_score': row['confidence_score'],
                'timing_signal': row['timing_signal'],
                'rsi': row['rsi'],
                'volatility': row['volatility'],
                'volume_ratio': row['volume_ratio'],
                'momentum_signal': row['momentum_signal'],
                'support_signal': row['support_signal'],
                'bollinger_signal': row['bollinger_signal']
            }
            
            # Get future price
            future_price = self.get_future_price(row['symbol'], row['timestamp'], hours_ahead)
            
            if future_price is not None:
                # Calculate profit percentage
                profit_pct = (future_price - row['current_price']) / row['current_price']
                
                # Create binary label: 1 if profitable, 0 if not
                is_profitable = 1 if profit_pct >= profit_threshold else 0
                
                signal_data.update({
                    'future_price': future_price,
                    'profit_pct': profit_pct,
                    'is_profitable': is_profitable,
                    'hours_ahead': hours_ahead
                })
                
                labeled_data.append(signal_data)
                
                print(f"   📊 {row['symbol']}: {row['current_price']:.4f} → {future_price:.4f} ({profit_pct:.2%}) {'✅' if is_profitable else '❌'}")
            else:
                print(f"   ⚠️ {row['symbol']}: Could not fetch future price")
            
            # Rate limiting
            time.sleep(0.1)
        
        labeled_df = pd.DataFrame(labeled_data)
        print(f"✅ Created {len(labeled_df)} labeled samples")
        
        if len(labeled_df) > 0:
            profitable_count = labeled_df['is_profitable'].sum()
            success_rate = profitable_count / len(labeled_df)
            print(f"📈 Success rate: {profitable_count}/{len(labeled_df)} ({success_rate:.1%})")
        
        return labeled_df
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create additional features for ML training.
        """
        print("🔧 Engineering additional features...")
        
        # Create feature combinations
        df['confidence_x_rsi'] = df['confidence_score'] * df['rsi']
        df['volatility_normalized'] = df['volatility'] / df['volatility'].mean()
        
        # Boolean feature encoding
        df['volume_signal_int'] = df['volume_ratio'].astype(int)
        df['momentum_signal_int'] = df['momentum_signal'].astype(int)
        df['support_signal_int'] = df['support_signal'].astype(int)
        df['bollinger_signal_int'] = df['bollinger_signal'].astype(int)
        
        # Technical signal strength
        df['signal_strength'] = (
            df['volume_signal_int'] + 
            df['momentum_signal_int'] + 
            df['support_signal_int'] + 
            df['bollinger_signal_int']
        )
        
        # RSI zones
        df['rsi_oversold'] = (df['rsi'] < 30).astype(int)
        df['rsi_overbought'] = (df['rsi'] > 70).astype(int)
        df['rsi_neutral'] = ((df['rsi'] >= 30) & (df['rsi'] <= 70)).astype(int)
        
        print(f"✅ Feature engineering complete. Total features: {len(df.columns)}")
        return df
    
    def prepare_ml_dataset(self, csv_path: str = "signals_log.csv", output_path: str = "ml/training_dataset.csv") -> pd.DataFrame:
        """
        Complete pipeline: load signals → create labels → engineer features → save dataset
        """
        print("🚀 Starting ML dataset preparation...")
        
        # Load signal data
        signals_df = self.load_signals(csv_path)
        if signals_df.empty:
            return pd.DataFrame()
        
        # Create profit labels
        labeled_df = self.create_labels(signals_df)
        if labeled_df.empty:
            return pd.DataFrame()
        
        # Engineer features
        final_df = self.engineer_features(labeled_df)
        
        # Save processed dataset
        final_df.to_csv(output_path, index=False)
        print(f"✅ Saved ML dataset to {output_path}")
        
        return final_df

if __name__ == "__main__":
    preparer = SignalDatasetPreparer()
    dataset = preparer.prepare_ml_dataset()
    
    if not dataset.empty:
        print("\n📊 Dataset Summary:")
        print(f"   Samples: {len(dataset)}")
        print(f"   Features: {len(dataset.columns) - 5}")  # Exclude metadata columns
        print(f"   Profitable signals: {dataset['is_profitable'].sum()}")
        print(f"   Success rate: {dataset['is_profitable'].mean():.1%}")