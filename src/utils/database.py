"""
Database utilities for storing trading data and state.
"""

import sqlite3
import pandas as pd
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import os
from contextlib import contextmanager


class DatabaseManager:
    """Database manager for trading system data storage."""
    
    def __init__(self, db_path: str = 'trading.db'):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Create database directory if needed
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Trades table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS trades (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TIMESTAMP NOT NULL,
                        symbol TEXT NOT NULL,
                        action TEXT NOT NULL,
                        size REAL NOT NULL,
                        price REAL NOT NULL,
                        commission REAL DEFAULT 0,
                        order_id TEXT,
                        strategy TEXT,
                        confidence REAL,
                        pnl REAL,
                        mode TEXT DEFAULT 'paper',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Positions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS positions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        size REAL NOT NULL,
                        avg_price REAL NOT NULL,
                        entry_time TIMESTAMP NOT NULL,
                        stop_loss REAL,
                        take_profit REAL,
                        unrealized_pnl REAL DEFAULT 0,
                        status TEXT DEFAULT 'open',
                        mode TEXT DEFAULT 'paper',
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Portfolio snapshots table with real OKX data fields
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TIMESTAMP NOT NULL,
                        total_value REAL NOT NULL,
                        cash REAL NOT NULL,
                        positions_value REAL NOT NULL,
                        daily_pnl REAL DEFAULT 0,
                        total_return REAL DEFAULT 0,
                        cost_basis REAL DEFAULT 0,  -- Real cost basis from OKX
                        okx_symbol TEXT,  -- OKX symbol for tracking
                        okx_quantity REAL DEFAULT 0,  -- Real quantity from OKX
                        mode TEXT DEFAULT 'live',  -- Default to live mode with real OKX data
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Signals table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS signals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TIMESTAMP NOT NULL,
                        symbol TEXT NOT NULL,
                        action TEXT NOT NULL,
                        price REAL NOT NULL,
                        confidence REAL NOT NULL,
                        strategy TEXT,
                        executed BOOLEAN DEFAULT FALSE,
                        mode TEXT DEFAULT 'paper',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Strategy performance table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS strategy_performance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        strategy_name TEXT NOT NULL,
                        symbol TEXT NOT NULL,
                        start_date DATE NOT NULL,
                        end_date DATE NOT NULL,
                        total_return REAL NOT NULL,
                        sharpe_ratio REAL,
                        max_drawdown REAL,
                        total_trades INTEGER DEFAULT 0,
                        win_rate REAL DEFAULT 0,
                        mode TEXT DEFAULT 'backtest',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # System state table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_state (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON signals(timestamp)')
                
                conn.commit()
                self.logger.info("Database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Error initializing database: {str(e)}")
            raise
    
    @contextmanager
    def get_connection(self):
        """
        Get database connection with automatic cleanup.
        
        Yields:
            SQLite connection object
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database error: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
    
    def save_trade(self, trade_data: Dict) -> int:
        """
        Save trade to database.
        
        Args:
            trade_data: Trade data dictionary
            
        Returns:
            Trade ID
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO trades 
                    (timestamp, symbol, action, size, price, commission, order_id, 
                     strategy, confidence, pnl, mode)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trade_data.get('timestamp', datetime.now()),
                    trade_data['symbol'],
                    trade_data['action'],
                    trade_data['size'],
                    trade_data['price'],
                    trade_data.get('commission', 0),
                    trade_data.get('order_id'),
                    trade_data.get('strategy'),
                    trade_data.get('confidence'),
                    trade_data.get('pnl'),
                    trade_data.get('mode', 'paper')
                ))
                
                trade_id = cursor.lastrowid
                conn.commit()
                
                self.logger.debug(f"Trade saved with ID: {trade_id}")
                return trade_id or 0
                
        except Exception as e:
            self.logger.error(f"Error saving trade: {str(e)}")
            raise
    
    def get_trades(self, symbol: str = None, start_date: datetime = None, 
                  end_date: datetime = None, mode: str = None) -> pd.DataFrame:
        """
        Get trades from database.
        
        Args:
            symbol: Optional symbol filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            mode: Optional mode filter (paper, live, backtest)
            
        Returns:
            DataFrame with trades
        """
        try:
            with self.get_connection() as conn:
                query = 'SELECT * FROM trades WHERE 1=1'
                params = []
                
                if symbol:
                    query += ' AND symbol = ?'
                    params.append(symbol)
                
                if start_date:
                    query += ' AND timestamp >= ?'
                    params.append(start_date)
                
                if end_date:
                    query += ' AND timestamp <= ?'
                    params.append(end_date)
                
                if mode:
                    query += ' AND mode = ?'
                    params.append(mode)
                
                query += ' ORDER BY timestamp DESC'
                
                df = pd.read_sql_query(query, conn, params=params)
                
                if not df.empty:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                return df
                
        except Exception as e:
            self.logger.error(f"Error getting trades: {str(e)}")
            return pd.DataFrame()
    
    def save_position(self, position_data: Dict) -> int:
        """
        Save position to database.
        
        Args:
            position_data: Position data dictionary
            
        Returns:
            Position ID
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO positions
                    (symbol, size, avg_price, entry_time, stop_loss, take_profit, 
                     unrealized_pnl, status, mode)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    position_data['symbol'],
                    position_data['size'],
                    position_data['avg_price'],
                    position_data.get('entry_time', datetime.now()),
                    position_data.get('stop_loss'),
                    position_data.get('take_profit'),
                    position_data.get('unrealized_pnl', 0),
                    position_data.get('status', 'open'),
                    position_data.get('mode', 'paper')
                ))
                
                position_id = cursor.lastrowid
                conn.commit()
                
                return position_id or 0
                
        except Exception as e:
            self.logger.error(f"Error saving position: {str(e)}")
            raise
    
    def get_positions(self, status: str = 'open', mode: str = None) -> pd.DataFrame:
        """
        Get positions from database.
        
        Args:
            status: Position status filter
            mode: Optional mode filter
            
        Returns:
            DataFrame with positions
        """
        try:
            with self.get_connection() as conn:
                query = 'SELECT * FROM positions WHERE status = ?'
                params = [status]
                
                if mode:
                    query += ' AND mode = ?'
                    params.append(mode)
                
                query += ' ORDER BY entry_time DESC'
                
                df = pd.read_sql_query(query, conn, params=params)
                
                if not df.empty:
                    df['entry_time'] = pd.to_datetime(df['entry_time'])
                
                return df
                
        except Exception as e:
            self.logger.error(f"Error getting positions: {str(e)}")
            return pd.DataFrame()
    
    def save_portfolio_snapshot(self, snapshot_data: Dict):
        """
        Save portfolio snapshot to database.
        
        Args:
            snapshot_data: Portfolio snapshot data
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO portfolio_snapshots
                    (timestamp, total_value, cash, positions_value, daily_pnl, 
                     total_return, mode)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    snapshot_data.get('timestamp', datetime.now()),
                    snapshot_data['total_value'],
                    snapshot_data['cash'],
                    snapshot_data['positions_value'],
                    snapshot_data.get('daily_pnl', 0),
                    snapshot_data.get('total_return', 0),
                    snapshot_data.get('mode', 'paper')
                ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error saving portfolio snapshot: {str(e)}")
    
    def get_portfolio_history(self, mode: str = None, days: int = 30) -> pd.DataFrame:
        """
        Get portfolio history.
        
        Args:
            mode: Optional mode filter
            days: Number of days to retrieve
            
        Returns:
            DataFrame with portfolio history
        """
        try:
            with self.get_connection() as conn:
                query = '''
                    SELECT * FROM portfolio_snapshots 
                    WHERE timestamp >= datetime('now', '-{} days')
                '''.format(days)
                
                params = []
                
                if mode:
                    query += ' AND mode = ?'
                    params.append(mode)
                
                query += ' ORDER BY timestamp'
                
                df = pd.read_sql_query(query, conn, params=params)
                
                if not df.empty:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                return df
                
        except Exception as e:
            self.logger.error(f"Error getting portfolio history: {str(e)}")
            return pd.DataFrame()
    
    def save_signal(self, signal_data: Dict) -> int:
        """
        Save trading signal to database.
        
        Args:
            signal_data: Signal data dictionary
            
        Returns:
            Signal ID
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO signals
                    (timestamp, symbol, action, price, confidence, strategy, executed, mode)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    signal_data.get('timestamp', datetime.now()),
                    signal_data['symbol'],
                    signal_data['action'],
                    signal_data['price'],
                    signal_data['confidence'],
                    signal_data.get('strategy'),
                    signal_data.get('executed', False),
                    signal_data.get('mode', 'paper')
                ))
                
                signal_id = cursor.lastrowid
                conn.commit()
                
                return signal_id
                
        except Exception as e:
            self.logger.error(f"Error saving signal: {str(e)}")
            raise
    
    def update_signal_execution(self, signal_id: int, executed: bool = True):
        """
        Update signal execution status.
        
        Args:
            signal_id: Signal ID
            executed: Execution status
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE signals SET executed = ? WHERE id = ?
                ''', (executed, signal_id))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error updating signal execution: {str(e)}")
    
    def save_strategy_performance(self, performance_data: Dict):
        """
        Save strategy performance metrics.
        
        Args:
            performance_data: Performance data dictionary
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO strategy_performance
                    (strategy_name, symbol, start_date, end_date, total_return,
                     sharpe_ratio, max_drawdown, total_trades, win_rate, mode)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    performance_data['strategy_name'],
                    performance_data['symbol'],
                    performance_data['start_date'],
                    performance_data['end_date'],
                    performance_data['total_return'],
                    performance_data.get('sharpe_ratio'),
                    performance_data.get('max_drawdown'),
                    performance_data.get('total_trades', 0),
                    performance_data.get('win_rate', 0),
                    performance_data.get('mode', 'backtest')
                ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error saving strategy performance: {str(e)}")
    
    def get_system_state(self, key: str) -> Optional[Any]:
        """
        Get system state value.
        
        Args:
            key: State key
            
        Returns:
            State value or None
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT value FROM system_state WHERE key = ?', (key,))
                result = cursor.fetchone()
                
                if result:
                    try:
                        return json.loads(result['value'])
                    except json.JSONDecodeError:
                        return result['value']
                
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting system state: {str(e)}")
            return None
    
    def set_system_state(self, key: str, value: Any):
        """
        Set system state value.
        
        Args:
            key: State key
            value: State value
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Convert value to JSON string if not already a string
                if isinstance(value, (dict, list)):
                    value_str = json.dumps(value)
                else:
                    value_str = str(value)
                
                cursor.execute('''
                    INSERT OR REPLACE INTO system_state (key, value, updated_at)
                    VALUES (?, ?, ?)
                ''', (key, value_str, datetime.now()))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error setting system state: {str(e)}")
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """
        Clean up old data from database.
        
        Args:
            days_to_keep: Number of days of data to keep
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cutoff_date = datetime.now() - pd.Timedelta(days=days_to_keep)
                
                # Clean up old trades (except live trades)
                cursor.execute('''
                    DELETE FROM trades 
                    WHERE timestamp < ? AND mode != 'live'
                ''', (cutoff_date,))
                
                # Clean up old portfolio snapshots
                cursor.execute('''
                    DELETE FROM portfolio_snapshots 
                    WHERE timestamp < ?
                ''', (cutoff_date,))
                
                # Clean up old signals
                cursor.execute('''
                    DELETE FROM signals 
                    WHERE timestamp < ?
                ''', (cutoff_date,))
                
                conn.commit()
                
                self.logger.info(f"Cleaned up data older than {days_to_keep} days")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {str(e)}")
    
    def get_database_stats(self) -> Dict:
        """
        Get database statistics.
        
        Returns:
            Database statistics dictionary
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Count records in each table
                # Using explicit SQL queries to avoid dynamic string construction
                table_queries = {
                    'trades': 'SELECT COUNT(*) as count FROM trades',
                    'positions': 'SELECT COUNT(*) as count FROM positions', 
                    'portfolio_snapshots': 'SELECT COUNT(*) as count FROM portfolio_snapshots',
                    'signals': 'SELECT COUNT(*) as count FROM signals',
                    'strategy_performance': 'SELECT COUNT(*) as count FROM strategy_performance'
                }
                
                for table_name, query in table_queries.items():
                    cursor.execute(query)
                    result = cursor.fetchone()
                    stats[f'{table_name}_count'] = result['count']
                
                # Database file size
                if os.path.exists(self.db_path):
                    stats['file_size_mb'] = os.path.getsize(self.db_path) / (1024 * 1024)
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Error getting database stats: {str(e)}")
            return {}
    
    def reset_all_trades(self, mode: str = None):
        """
        Reset all trades from database.
        
        Args:
            mode: Optional mode filter (paper, live, backtest). If None, clears all modes.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if mode:
                    cursor.execute('DELETE FROM trades WHERE mode = ?', (mode,))
                    self.logger.info(f"Cleared all {mode} trades")
                else:
                    cursor.execute('DELETE FROM trades')
                    self.logger.info("Cleared all trades from database")
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error resetting trades: {str(e)}")
            raise
    
    def reset_all_positions(self, mode: str = None):
        """
        Reset all positions from database.
        
        Args:
            mode: Optional mode filter (paper, live, backtest). If None, clears all modes.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if mode:
                    cursor.execute('DELETE FROM positions WHERE mode = ?', (mode,))
                    self.logger.info(f"Cleared all {mode} positions")
                else:
                    cursor.execute('DELETE FROM positions')
                    self.logger.info("Cleared all positions from database")
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error resetting positions: {str(e)}")
            raise
    
    def reset_portfolio_snapshots(self, mode: str = None):
        """
        Reset portfolio snapshots from database.
        
        Args:
            mode: Optional mode filter. If None, clears all modes.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if mode:
                    cursor.execute('DELETE FROM portfolio_snapshots WHERE mode = ?', (mode,))
                    self.logger.info(f"Cleared all {mode} portfolio snapshots")
                else:
                    cursor.execute('DELETE FROM portfolio_snapshots')
                    self.logger.info("Cleared all portfolio snapshots from database")
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error resetting portfolio snapshots: {str(e)}")
            raise
