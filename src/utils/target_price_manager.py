#!/usr/bin/env python3
"""
Target Price Manager - Locks target buy prices to prevent exponential recalculation.
Now uses intelligent 3-day momentum analysis instead of simple discounts.
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import os
from src.utils.entry_confidence import EntryConfidenceAnalyzer

logger = logging.getLogger(__name__)

class TargetPriceManager:
    """
    Manages locked target buy prices to prevent constant recalculation.
    
    Features:
    - Locks target prices for 24 hours once calculated
    - Allows updates only if market drops significantly (>5%) 
    - Provides manual reset capability
    - Persistent storage in SQLite
    """
    
    def __init__(self, db_path: str = "trading.db"):
        self.db_path = db_path
        self.confidence_analyzer = EntryConfidenceAnalyzer()  # INTEGRATION: Use 3-day algorithm
        self._init_database()
    
    def _init_database(self):
        """Initialize target prices table."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS target_prices (
                    symbol TEXT PRIMARY KEY,
                    target_price REAL NOT NULL,
                    original_market_price REAL NOT NULL,
                    calculated_at TIMESTAMP NOT NULL,
                    locked_until TIMESTAMP NOT NULL,
                    tier TEXT DEFAULT 'altcoin',
                    discount_percent REAL DEFAULT 8.0
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Target prices database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize target prices database: {e}")
    
    def get_locked_target_price(self, symbol: str, current_market_price: float) -> Tuple[float, bool]:
        """
        Get locked target price for a symbol. Returns (target_price, is_locked).
        
        Args:
            symbol: Cryptocurrency symbol
            current_market_price: Current market price
            
        Returns:
            tuple: (target_price, is_locked) where is_locked indicates if price is locked
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT target_price, original_market_price, calculated_at, locked_until, discount_percent
                FROM target_prices 
                WHERE symbol = ?
            ''', (symbol,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                target_price, original_price, calculated_at, locked_until, discount_percent = result
                locked_until_dt = datetime.fromisoformat(locked_until)
                
                # Check if lock is still valid
                if datetime.now() < locked_until_dt:
                    # Check if market has dropped significantly (>5% from original)
                    price_drop_percent = ((original_price - current_market_price) / original_price) * 100
                    
                    if price_drop_percent > 5.0:
                        logger.info(f"{symbol}: Market dropped {price_drop_percent:.1f}%, recalculating target")
                        return self._calculate_new_target(symbol, current_market_price)
                    
                    logger.debug(f"{symbol}: Using locked target ${target_price:.8f} (locked until {locked_until})")
                    return target_price, True
                else:
                    logger.info(f"{symbol}: Target price lock expired, recalculating")
                    return self._calculate_new_target(symbol, current_market_price)
            else:
                logger.info(f"{symbol}: No existing target price, calculating new one")
                return self._calculate_new_target(symbol, current_market_price)
                
        except Exception as e:
            logger.error(f"Error getting locked target price for {symbol}: {e}")
            return self._calculate_new_target(symbol, current_market_price)
    
    def _calculate_new_target(self, symbol: str, current_price: float) -> Tuple[float, bool]:
        """Calculate and lock a new target price using INTELLIGENT 3-DAY ALGORITHM."""
        try:
            # 🎯 REVOLUTIONARY CHANGE: Use confidence analyzer's 3-day momentum algorithm!
            confidence_data = self.confidence_analyzer.calculate_confidence(
                symbol=symbol, 
                current_price=current_price
            )
            
            # Get intelligent target price from sophisticated analysis
            target_price = confidence_data.get('suggested_target_price', current_price * 0.98)
            confidence_score = confidence_data.get('confidence_score', 50)
            
            # Asset tier classification (for database tracking)
            if symbol in ['BTC', 'ETH']:
                tier = 'large_cap'
            elif symbol in ['SOL', 'ADA', 'DOT', 'MATIC', 'AVAX', 'LINK']:
                tier = 'mid_cap'
            elif symbol in ['GALA', 'SAND', 'MANA', 'CHZ', 'ENJ']:
                tier = 'gaming'
            elif symbol in ['PEPE', 'SHIB', 'DOGE']:
                tier = 'meme'
            elif current_price < 0.01:
                tier = 'micro_cap'
            else:
                tier = 'altcoin'
            
            # Calculate actual discount achieved
            discount_percent = ((current_price - target_price) / current_price) * 100
            
            # Lock for 24 hours
            lock_duration = timedelta(hours=24)
            locked_until = datetime.now() + lock_duration
            
            # Save to database
            self._save_target_price(symbol, target_price, current_price, locked_until, tier, discount_percent)
            
            logger.info(f"🎯 {symbol}: INTELLIGENT TARGET ${target_price:.8f} ({discount_percent:.1f}% discount, "
                       f"confidence: {confidence_score:.1f}), locked until {locked_until.strftime('%H:%M %d/%m')}")
            return target_price, True
            
        except Exception as e:
            logger.error(f"Error calculating intelligent target for {symbol}: {e}")
            # Fallback: conservative 2% discount, no lock
            return current_price * 0.98, False
    
    def _save_target_price(self, symbol: str, target_price: float, original_price: float, 
                          locked_until: datetime, tier: str, discount_percent: float):
        """Save target price to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO target_prices 
                (symbol, target_price, original_market_price, calculated_at, locked_until, tier, discount_percent)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (symbol, target_price, original_price, datetime.now().isoformat(), 
                  locked_until.isoformat(), tier, discount_percent))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving target price for {symbol}: {e}")
    
    def reset_all_target_prices(self):
        """Clear ALL target prices to force recalculation with INTELLIGENT 3-DAY ALGORITHM."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get count first
            cursor.execute('SELECT COUNT(*) FROM target_prices')
            count = cursor.fetchone()[0]
            
            cursor.execute('DELETE FROM target_prices')
            conn.commit()
            conn.close()
            logger.info(f"🎯 ALGORITHM UPGRADE: Cleared {count} old targets - will now use intelligent 3-day momentum analysis!")
        except Exception as e:
            logger.error(f"Error clearing all target prices: {e}")
    
    def reset_target_price(self, symbol: str):
        """Manually reset a target price (force recalculation on next request)."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM target_prices WHERE symbol = ?', (symbol,))
            conn.commit()
            conn.close()
            
            logger.info(f"Reset target price for {symbol}")
            
        except Exception as e:
            logger.error(f"Error resetting target price for {symbol}: {e}")
    
    def get_all_locked_targets(self) -> Dict[str, Dict]:
        """Get all currently locked target prices."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT symbol, target_price, original_market_price, calculated_at, 
                       locked_until, tier, discount_percent
                FROM target_prices 
                WHERE locked_until > datetime('now')
                ORDER BY symbol
            ''')
            
            results = cursor.fetchall()
            conn.close()
            
            locked_targets = {}
            for row in results:
                symbol, target_price, original_price, calculated_at, locked_until, tier, discount = row
                locked_targets[symbol] = {
                    'target_price': target_price,
                    'original_market_price': original_price,
                    'calculated_at': calculated_at,
                    'locked_until': locked_until,
                    'tier': tier,
                    'discount_percent': discount
                }
            
            return locked_targets
            
        except Exception as e:
            logger.error(f"Error getting all locked targets: {e}")
            return {}
    
    def cleanup_expired_targets(self):
        """Remove expired target prices from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM target_prices WHERE locked_until < datetime('now')")
            deleted_count = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired target prices")
                
        except Exception as e:
            logger.error(f"Error cleaning up expired targets: {e}")

# Global instance
_target_manager = None

def get_target_price_manager() -> TargetPriceManager:
    """Get singleton target price manager instance."""
    global _target_manager
    if _target_manager is None:
        _target_manager = TargetPriceManager()
    return _target_manager