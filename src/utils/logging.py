"""
Logging setup and configuration utilities.
"""

import logging
import logging.handlers
import os
from datetime import datetime


def setup_logging(level: str = 'INFO', log_file: str = 'trading.log', 
                 max_file_size: int = 10485760, backup_count: int = 5):
    """
    Set up logging configuration for the trading system.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Log file path
        max_file_size: Maximum log file size in bytes
        backup_count: Number of backup log files to keep
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file) if os.path.dirname(log_file) else 'logs'
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, 
            maxBytes=max_file_size, 
            backupCount=backup_count
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Set specific logger levels
    logging.getLogger('ccxt').setLevel(logging.WARNING)  # Reduce ccxt verbosity
    logging.getLogger('urllib3').setLevel(logging.WARNING)  # Reduce requests verbosity
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - Level: {level}, File: {log_file}")


def get_trading_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for trading components.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class TradingLogFilter(logging.Filter):
    """Custom log filter for trading-specific messages."""
    
    def filter(self, record):
        """
        Filter log records for trading relevance.
        
        Args:
            record: Log record
            
        Returns:
            True if record should be logged
        """
        # Add custom filtering logic here
        # For example, filter out certain debug messages
        if record.levelno == logging.DEBUG:
            # Skip debug messages from certain modules
            skip_modules = ['ccxt.base', 'urllib3.connectionpool']
            if any(module in record.name for module in skip_modules):
                return False
        
        return True


def setup_trade_logger(log_file: str = 'trades.log') -> logging.Logger:
    """
    Set up a dedicated logger for trade execution.
    
    Args:
        log_file: Trade log file path
        
    Returns:
        Trade logger instance
    """
    trade_logger = logging.getLogger('trading.trades')
    trade_logger.setLevel(logging.INFO)
    
    # Create trade-specific formatter
    trade_formatter = logging.Formatter(
        '%(asctime)s - TRADE - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create file handler for trades
    trade_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=5242880,  # 5MB
        backupCount=10
    )
    trade_handler.setLevel(logging.INFO)
    trade_handler.setFormatter(trade_formatter)
    
    # Avoid duplicate logs in root logger
    trade_logger.propagate = False
    trade_logger.addHandler(trade_handler)
    
    return trade_logger


def log_trade_execution(logger: logging.Logger, action: str, symbol: str, 
                       size: float, price: float, order_id: str = None):
    """
    Log trade execution with standardized format.
    
    Args:
        logger: Logger instance
        action: Trade action (BUY/SELL)
        symbol: Trading symbol
        size: Trade size
        price: Execution price
        order_id: Order ID if available
    """
    message = f"{action} {size:.6f} {symbol} @ ${price:.2f}"
    if order_id:
        message += f" (Order: {order_id})"
    
    logger.info(message)


def log_portfolio_update(logger: logging.Logger, portfolio_value: float, 
                        cash: float, positions: dict):
    """
    Log portfolio status update.
    
    Args:
        logger: Logger instance
        portfolio_value: Total portfolio value
        cash: Available cash
        positions: Current positions dictionary
    """
    message = f"Portfolio: ${portfolio_value:.2f} | Cash: ${cash:.2f} | Positions: {len(positions)}"
    logger.info(message)


def log_signal_generation(logger: logging.Logger, symbol: str, action: str, 
                         confidence: float, price: float):
    """
    Log signal generation.
    
    Args:
        logger: Logger instance
        symbol: Trading symbol
        action: Signal action
        confidence: Signal confidence
        price: Signal price
    """
    message = f"SIGNAL - {symbol}: {action} @ ${price:.2f} (Confidence: {confidence:.2f})"
    logger.info(message)


def log_risk_event(logger: logging.Logger, event_type: str, message: str, 
                  severity: str = 'WARNING'):
    """
    Log risk management events.
    
    Args:
        logger: Logger instance
        event_type: Type of risk event
        message: Event message
        severity: Event severity (INFO, WARNING, ERROR, CRITICAL)
    """
    log_message = f"RISK-{event_type}: {message}"
    
    if severity == 'CRITICAL':
        logger.critical(log_message)
    elif severity == 'ERROR':
        logger.error(log_message)
    elif severity == 'WARNING':
        logger.warning(log_message)
    else:
        logger.info(log_message)


class PerformanceLogger:
    """Logger for performance metrics and timing."""
    
    def __init__(self, name: str = 'performance'):
        """
        Initialize performance logger.
        
        Args:
            name: Logger name
        """
        self.logger = logging.getLogger(f'trading.{name}')
        self.timers = {}
    
    def start_timer(self, operation: str):
        """
        Start timing an operation.
        
        Args:
            operation: Operation name
        """
        self.timers[operation] = datetime.now()
    
    def end_timer(self, operation: str, log_level: str = 'DEBUG'):
        """
        End timing an operation and log the duration.
        
        Args:
            operation: Operation name
            log_level: Logging level for the timing message
        """
        if operation in self.timers:
            duration = datetime.now() - self.timers[operation]
            duration_ms = duration.total_seconds() * 1000
            
            message = f"{operation} completed in {duration_ms:.2f}ms"
            
            if log_level == 'INFO':
                self.logger.info(message)
            elif log_level == 'WARNING':
                self.logger.warning(message)
            elif log_level == 'ERROR':
                self.logger.error(message)
            else:
                self.logger.debug(message)
            
            del self.timers[operation]
    
    def log_metric(self, metric_name: str, value: float, unit: str = ''):
        """
        Log a performance metric.
        
        Args:
            metric_name: Metric name
            value: Metric value
            unit: Metric unit
        """
        message = f"METRIC - {metric_name}: {value:.4f}"
        if unit:
            message += f" {unit}"
        
        self.logger.info(message)
