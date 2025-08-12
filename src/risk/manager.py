"""
Risk management system.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from ..strategies.base import Signal


class RiskManager:
    """Risk management system for trading operations."""
    
    def __init__(self, config):
        """
        Initialize risk manager.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Risk parameters
        self.max_portfolio_risk = config.get_float('risk', 'max_portfolio_risk', 10.0)
        self.max_single_position_risk = config.get_float('risk', 'max_single_position_risk', 5.0)
        self.max_daily_loss = config.get_float('risk', 'max_daily_loss', 5.0)
        self.trailing_stop_percent = config.get_float('risk', 'trailing_stop_percent', 1.0)
        
        # Daily tracking
        self.daily_pnl = 0.0
        self.daily_reset_time = None
        self.max_positions = config.get_int('trading', 'max_positions', 3)
        
        # Risk state
        self.trading_halted = False
        self.halt_reason = None
        
        self.logger.info(f"Risk manager initialized - Max portfolio risk: {self.max_portfolio_risk}%")
    
    def check_trading_allowed(self, portfolio_value: float) -> bool:
        """
        Check if trading is allowed based on risk limits.
        
        Args:
            portfolio_value: Current portfolio value
            
        Returns:
            True if trading is allowed, False otherwise
        """
        # Reset daily tracking if new day
        self._reset_daily_tracking()
        
        # Check if trading is halted
        if self.trading_halted:
            self.logger.warning(f"Trading halted: {self.halt_reason}")
            return False
        
        # Check daily loss limit
        daily_loss_percent = abs(self.daily_pnl) / portfolio_value * 100
        if daily_loss_percent >= self.max_daily_loss:
            self._halt_trading(f"Daily loss limit exceeded: {daily_loss_percent:.2f}% >= {self.max_daily_loss}%")
            return False
        
        return True
    
    def validate_position_size(self, signal: Signal, portfolio_value: float) -> bool:
        """
        Validate if position size is within risk limits.
        
        Args:
            signal: Trading signal
            portfolio_value: Current portfolio value
            
        Returns:
            True if position size is acceptable
        """
        try:
            # Calculate position value
            position_value = portfolio_value * signal.size
            position_risk_percent = (position_value / portfolio_value) * 100
            
            # Check single position risk limit
            if position_risk_percent > self.max_single_position_risk:
                self.logger.warning(f"Position size exceeds risk limit: {position_risk_percent:.2f}% > {self.max_single_position_risk}%")
                return False
            
            # Check if position has stop loss
            if signal.action in ['buy', 'sell'] and not signal.stop_loss:
                self.logger.warning("Position rejected: No stop loss specified")
                return False
            
            # Additional position size validation
            min_position_size = 50  # Minimum $50 position
            if position_value < min_position_size:
                self.logger.warning(f"Position size too small: ${position_value:.2f} < ${min_position_size}")
                return False
            
            max_position_size = portfolio_value * 0.2  # Max 20% of portfolio
            if position_value > max_position_size:
                self.logger.warning(f"Position size too large: ${position_value:.2f} > ${max_position_size:.2f}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating position size: {str(e)}")
            return False
    
    def calculate_stop_loss(self, entry_price: float, side: str, atr: float = None) -> float:
        """
        Calculate stop loss price.
        
        Args:
            entry_price: Entry price
            side: 'long' or 'short'
            atr: Average True Range for dynamic stops
            
        Returns:
            Stop loss price
        """
        try:
            if atr and atr > 0:
                # Dynamic stop based on ATR
                stop_distance = atr * 2  # 2x ATR
            else:
                # Fixed percentage stop
                stop_distance = entry_price * (self.max_single_position_risk / 100)
            
            if side == 'long':
                stop_loss = entry_price - stop_distance
            else:  # short
                stop_loss = entry_price + stop_distance
            
            return max(stop_loss, 0.01)  # Ensure positive price
            
        except Exception as e:
            self.logger.error(f"Error calculating stop loss: {str(e)}")
            return entry_price * 0.95 if side == 'long' else entry_price * 1.05
    
    def calculate_position_size_kelly(self, win_rate: float, avg_win: float, avg_loss: float, 
                                    portfolio_value: float) -> float:
        """
        Calculate optimal position size using Kelly Criterion.
        
        Args:
            win_rate: Historical win rate (0.0 to 1.0)
            avg_win: Average winning trade return
            avg_loss: Average losing trade return (positive value)
            portfolio_value: Current portfolio value
            
        Returns:
            Optimal position size as percentage of portfolio
        """
        try:
            if avg_loss <= 0 or win_rate <= 0:
                return 0.01  # 1% default
            
            # Kelly formula: f = (bp - q) / b
            # where: b = avg_win/avg_loss, p = win_rate, q = 1 - win_rate
            b = avg_win / avg_loss
            p = win_rate
            q = 1 - win_rate
            
            kelly_fraction = (b * p - q) / b
            
            # Apply safety factor (use 25% of Kelly)
            safe_kelly = kelly_fraction * 0.25
            
            # Clamp to reasonable limits
            safe_kelly = max(0.01, min(safe_kelly, self.max_single_position_risk / 100))
            
            self.logger.debug(f"Kelly calculation: {kelly_fraction:.3f} -> Safe: {safe_kelly:.3f}")
            
            return safe_kelly
            
        except Exception as e:
            self.logger.error(f"Error calculating Kelly position size: {str(e)}")
            return 0.01  # 1% fallback
    
    def update_daily_pnl(self, trade_pnl: float):
        """
        Update daily P&L tracking.
        
        Args:
            trade_pnl: P&L from completed trade
        """
        self._reset_daily_tracking()
        self.daily_pnl += trade_pnl
        
        self.logger.debug(f"Daily P&L updated: ${self.daily_pnl:.2f}")
    
    def check_position_limits(self, current_positions: int) -> bool:
        """
        Check if we can open new positions.
        
        Args:
            current_positions: Number of current open positions
            
        Returns:
            True if we can open new positions
        """
        if current_positions >= self.max_positions:
            self.logger.warning(f"Maximum positions reached: {current_positions} >= {self.max_positions}")
            return False
        
        return True
    
    def calculate_portfolio_risk(self, positions: List[Dict], portfolio_value: float) -> float:
        """
        Calculate total portfolio risk.
        
        Args:
            positions: List of open positions
            portfolio_value: Current portfolio value
            
        Returns:
            Total portfolio risk as percentage
        """
        try:
            total_risk = 0.0
            
            for position in positions:
                position_value = position.get('value', 0)
                risk_percent = (position_value / portfolio_value) * 100
                total_risk += risk_percent
            
            return total_risk
            
        except Exception as e:
            self.logger.error(f"Error calculating portfolio risk: {str(e)}")
            return 0.0
    
    def _reset_daily_tracking(self):
        """Reset daily tracking if new day."""
        current_date = datetime.now().date()
        
        if self.daily_reset_time is None or self.daily_reset_time != current_date:
            self.daily_pnl = 0.0
            self.daily_reset_time = current_date
            self.trading_halted = False
            self.halt_reason = None
            
            self.logger.info("Daily risk tracking reset")
    
    def _halt_trading(self, reason: str):
        """
        Halt trading operations.
        
        Args:
            reason: Reason for halting trading
        """
        self.trading_halted = True
        self.halt_reason = reason
        
        self.logger.critical(f"TRADING HALTED: {reason}")
    
    def force_resume_trading(self):
        """Force resume trading (emergency override)."""
        self.trading_halted = False
        self.halt_reason = None
        
        self.logger.warning("Trading force resumed")
    
    def get_risk_summary(self) -> Dict:
        """
        Get risk management summary.
        
        Returns:
            Risk summary dictionary
        """
        return {
            'max_portfolio_risk': self.max_portfolio_risk,
            'max_single_position_risk': self.max_single_position_risk,
            'max_daily_loss': self.max_daily_loss,
            'daily_pnl': self.daily_pnl,
            'trading_halted': self.trading_halted,
            'halt_reason': self.halt_reason,
            'max_positions': self.max_positions
        }
    
    def validate_trade_timing(self, last_trade_time: Optional[datetime]) -> bool:
        """
        Validate if enough time has passed since last trade.
        
        Args:
            last_trade_time: Timestamp of last trade
            
        Returns:
            True if timing is valid for new trade
        """
        if last_trade_time is None:
            return True
        
        min_time_between_trades = timedelta(minutes=30)  # 30 minutes minimum
        time_since_last_trade = datetime.now() - last_trade_time
        
        if time_since_last_trade < min_time_between_trades:
            self.logger.warning(f"Trade too soon after last trade: {time_since_last_trade}")
            return False
        
        return True
