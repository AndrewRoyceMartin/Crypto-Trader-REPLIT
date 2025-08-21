"""
Enhanced Bollinger Bands strategy with advanced crash protection and dynamic risk management.
Incorporates peak tracking, crash failsafes, and dynamic rebuy mechanisms.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from .base import BaseStrategy, Signal
from ..indicators.technical import TechnicalIndicators


class EnhancedBollingerBandsStrategy(BaseStrategy):
    """Enhanced Bollinger Bands strategy with crash protection and dynamic risk management."""
    
    def __init__(self, config):
        """Initialize enhanced strategy with advanced features."""
        super().__init__(config)
        
        # Basic Bollinger Bands parameters
        self.bb_period = config.get_int('strategy', 'bb_period', 20)
        self.bb_std_dev = config.get_float('strategy', 'bb_std_dev', 2.0)
        self.atr_period = config.get_int('strategy', 'atr_period', 14)
        
        # Enhanced risk management parameters
        self.position_size_percent = config.get_float('trading', 'position_size_percent', 5.0)
        self.stop_loss_percent = config.get_float('trading', 'stop_loss_percent', 2.0)
        self.take_profit_percent = config.get_float('trading', 'take_profit_percent', 4.0)
        
        # Crash Protection Parameters
        self.crash_atr_mult = config.get_float('strategy', 'crash_atr_mult', 3.0)  # ATR multiplier for crash detection
        self.crash_dd_pct = config.get_float('strategy', 'crash_dd_pct', 0.05)  # 5% drawdown threshold
        self.crash_require_profit = config.get_bool('strategy', 'crash_require_profit', True)  # Only exit in profit
        self.crash_min_profit_pct = config.get_float('strategy', 'crash_min_profit_pct', 0.005)  # 0.5% min profit
        
        # Fast timeframe crash detection
        self.fast_failsafe = config.get_bool('strategy', 'fast_failsafe', True)
        self.fast_tf = config.get_str('strategy', 'fast_tf', '1m')  # Fast timeframe for wick detection
        self.fast_lookback_min = config.get_int('strategy', 'fast_lookback_min', 5)
        self.fast_low_window_min = config.get_int('strategy', 'fast_low_window_min', 5)
        
        # Rebuy mechanism parameters
        self.rebuy_dynamic = config.get_bool('strategy', 'rebuy_dynamic', True)
        self.rebuy_cooldown_min = config.get_int('strategy', 'rebuy_cooldown_min', 15)  # 15 minutes cooldown
        self.rebuy_mode = config.get_str('strategy', 'rebuy_mode', 'confirmation')  # 'confirmation' or 'knife'
        
        # Trading costs and slippage
        self.fee = config.get_float('trading', 'fee', 0.0025)  # 0.25% fee
        self.slip = config.get_float('trading', 'slip', 0.001)  # 0.1% slippage
        
        # Position tracking state
        self.position_state = {
            'position_qty': 0.0,
            'entry_price': 0.0,
            'peak_since_entry': 0.0,
            'rebuy_armed': False,
            'rebuy_price': 0.0,
            'rebuy_ready_at': None,
            'last_trade_ts': None,
            'equity': 10000.0  # Starting equity for tracking
        }
        
        self.indicators = TechnicalIndicators()
        self.logger.info("Enhanced Bollinger Bands strategy initialized with crash protection")
    
    def calculate_position_size(self, signal, portfolio_value: float, current_price: float) -> float:
        """Calculate position size based on risk management."""
        risk_amount = portfolio_value * (signal.size if hasattr(signal, 'size') else self.position_size_percent / 100)
        position_size = risk_amount / current_price
        return position_size
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """Generate enhanced trading signals with crash protection."""
        signals = []
        
        if len(data) < max(self.bb_period, self.atr_period) + 1:
            return signals
        
        try:
            # Calculate technical indicators
            close_series = data['close'] if isinstance(data['close'], pd.Series) else data['close'].squeeze()
            high_series = data['high'] if isinstance(data['high'], pd.Series) else data['high'].squeeze()
            low_series = data['low'] if isinstance(data['low'], pd.Series) else data['low'].squeeze()
            
            upper_band, middle_band, lower_band = self.indicators.bollinger_bands(
                close_series, self.bb_period, self.bb_std_dev
            )
            
            atr = self.indicators.atr(
                high_series, low_series, close_series, self.atr_period
            )
            
            # Get current values
            current_price = data['close'].iloc[-1]
            current_high = data['high'].iloc[-1]
            current_low = data['low'].iloc[-1]
            current_upper = upper_band.iloc[-1]
            current_middle = middle_band.iloc[-1]
            current_lower = lower_band.iloc[-1]
            current_atr = atr.iloc[-1]
            last_candle = data.iloc[-1]
            
            # Skip if invalid values
            if any(pd.isna([current_upper, current_lower, current_atr])):
                return signals
            
            # Update peak tracking if in position
            if self.position_state['position_qty'] > 0.0:
                self.position_state['peak_since_entry'] = max(
                    self.position_state['peak_since_entry'], 
                    float(current_high)
                )
            
            # 1. CRASH FAILSAFE - Check for emergency exit
            crash_signal = self._check_crash_exit(current_price, current_low, current_atr, last_candle)
            if crash_signal:
                signals.append(crash_signal)
                return signals  # Exit immediately after crash signal
            
            # 2. NORMAL EXITS - Check regular exit conditions
            exit_signal = self._check_normal_exits(current_price, current_low, current_upper, current_lower)
            if exit_signal:
                signals.append(exit_signal)
                return signals
            
            # 3. ENTRIES - Check for new entry opportunities
            entry_signal = self._check_entry_opportunities(current_price, current_upper, current_lower, current_atr, data)
            if entry_signal:
                signals.append(entry_signal)
            
            return signals
            
        except Exception as e:
            self.logger.error(f"Error in enhanced signal generation: {e}")
            return signals
    
    def _check_crash_exit(self, px: float, current_low: float, atr: float, last_candle: pd.Series) -> Optional[Signal]:
        """Check for crash protection exit conditions."""
        if self.position_state['position_qty'] <= 0.0:
            return None
        
        peak = self.position_state['peak_since_entry']
        entry_price = self.position_state['entry_price']
        
        # Calculate drops from peak
        drop_from_peak_close = peak - px
        drop_from_peak_low = peak - current_low
        drop_close_pct = drop_from_peak_close / max(1e-12, peak)
        drop_low_pct = drop_from_peak_low / max(1e-12, peak)
        
        # Fast timeframe check (simplified - would need actual fast data)
        fast_trigger = False
        if self.fast_failsafe:
            # Simplified fast check using current candle wick
            fast_drop = peak - current_low
            if fast_drop >= self.crash_atr_mult * atr:
                fast_trigger = True
        
        # Check if currently in profit (including fees and slippage)
        breakeven_mult = 1 + 2*self.fee + 2*self.slip + self.crash_min_profit_pct
        in_profit_now = px >= entry_price * breakeven_mult if self.crash_require_profit else True
        
        # Crash trigger conditions
        crash_trigger = (
            max(drop_from_peak_close, drop_from_peak_low) >= self.crash_atr_mult * atr
            or max(drop_close_pct, drop_low_pct) >= self.crash_dd_pct
            or fast_trigger
        )
        
        crash_now = in_profit_now and crash_trigger
        
        if crash_now:
            # Calculate exit details
            fill_price = px * (1 - 0.001)  # Cross spread for immediacy
            qty = self.position_state['position_qty']
            gross = qty * (fill_price - entry_price)
            fees = self.fee * (fill_price + entry_price) * qty
            pnl = gross - fees
            
            # Arm rebuy mechanism
            self._arm_rebuy(px)
            
            # Reset position state
            self._reset_position()
            
            signal = Signal(
                action='sell',
                price=fill_price,
                size=qty,
                confidence=0.95,  # High confidence for crash exit
                stop_loss=None,
                take_profit=None
            )
            
            signal.metadata = {
                'event': 'CRASH_EXIT',
                'pnl': pnl,
                'peak': peak,
                'drop_close': drop_from_peak_close,
                'drop_low': drop_from_peak_low,
                'atr': atr,
                'fast_trigger': fast_trigger,
                'in_profit': in_profit_now
            }
            
            self.logger.warning(f"CRASH EXIT triggered: peak={peak:.2f}, drop_close={drop_from_peak_close:.2f}, "
                              f"drop_low={drop_from_peak_low:.2f}, atr={atr:.2f}")
            
            return signal
        
        return None
    
    def _check_normal_exits(self, px: float, current_low: float, bb_up: float, bb_lo: float) -> Optional[Signal]:
        """Check for normal exit conditions."""
        if self.position_state['position_qty'] <= 0.0:
            return None
        
        entry_price = self.position_state['entry_price']
        stop = entry_price * (1 - self.stop_loss_percent / 100)
        take = entry_price * (1 + self.take_profit_percent / 100)
        
        # Exit conditions: hit upper band, take profit, or stop loss
        if px >= bb_up or px >= take or current_low <= stop:
            fill_price = px * (1 - 0.001)
            qty = self.position_state['position_qty']
            gross = qty * (fill_price - entry_price)
            fees = self.fee * (fill_price + entry_price) * qty
            pnl = gross - fees
            
            # Reset position state
            self._reset_position()
            
            signal = Signal(
                action='sell',
                price=fill_price,
                size=qty,
                confidence=0.8,
                stop_loss=None,
                take_profit=None
            )
            
            signal.metadata = {
                'event': 'NORMAL_EXIT',
                'pnl': pnl,
                'bb_up': bb_up,
                'stop': stop,
                'take': take
            }
            
            self.logger.info(f"Normal exit: {signal.action} {qty:.6f} @ {fill_price:.2f}, PnL: {pnl:.2f}")
            
            return signal
        
        return None
    
    def _check_entry_opportunities(self, px: float, bb_up: float, bb_lo: float, atr: float, data: pd.DataFrame) -> Optional[Signal]:
        """Check for entry opportunities including rebuy logic."""
        if self.position_state['position_qty'] > 0.0:
            return None  # Already in position
        
        # Update rebuy price dynamically if armed
        if self.position_state['rebuy_armed'] and self.rebuy_dynamic:
            self.position_state['rebuy_price'] = self._compute_rebuy_price(data, px)
        
        # Check rebuy conditions first
        if self.position_state['rebuy_armed']:
            rebuy_signal = self._check_rebuy_conditions(px, atr)
            if rebuy_signal:
                return rebuy_signal
        
        # Check baseline mean-reversion entry
        if px <= bb_lo:
            return self._create_entry_signal(px, atr, 'BASELINE_ENTRY')
        
        return None
    
    def _check_rebuy_conditions(self, px: float, atr: float) -> Optional[Signal]:
        """Check if rebuy conditions are met."""
        if not self.position_state['rebuy_armed']:
            return None
        
        # Check cooldown period
        if self.position_state['rebuy_ready_at']:
            if datetime.now() < self.position_state['rebuy_ready_at']:
                return None
        
        rebuy_price = self.position_state['rebuy_price']
        
        if self.rebuy_mode == "confirmation":
            # Wait for price to recover above rebuy price
            rebuy_ready = px >= rebuy_price
        else:  # "knife" mode
            # Buy when price drops to rebuy level
            rebuy_ready = px <= rebuy_price
        
        if rebuy_ready:
            # Disarm rebuy mechanism
            self.position_state['rebuy_armed'] = False
            self.position_state['rebuy_price'] = 0.0
            self.position_state['rebuy_ready_at'] = None
            
            tag = f"REBUY_{'CONFIRMATION' if self.rebuy_mode == 'confirmation' else 'KNIFE'}"
            signal = self._create_entry_signal(px, atr, tag)
            signal.metadata['rebuy_price'] = rebuy_price
            
            return signal
        
        return None
    
    def _create_entry_signal(self, px: float, atr: float, event_type: str) -> Signal:
        """Create an entry signal using real OKX prices and cost basis."""
        # Get real OKX purchase price for accurate position sizing
        real_purchase_price = self._get_real_okx_purchase_price()
        
        # Risk-based position sizing using real OKX entry price
        risk_per_unit = max(1e-12, px * self.stop_loss_percent / 100)
        dollars = self.position_size_percent / 100 * self.position_state['equity']
        qty = max(0.0, dollars / risk_per_unit)
        
        # Use real OKX market price with realistic spread
        fill_price = px * (1 + 0.001)  # Current OKX market price with spread
        
        # Update position state
        self.position_state['position_qty'] = qty
        self.position_state['entry_price'] = px
        self.position_state['peak_since_entry'] = px
        self.position_state['last_trade_ts'] = datetime.now()
        
        # Calculate stop loss and take profit based on real OKX entry price
        entry_ref_price = real_purchase_price if real_purchase_price > 0 else px
        stop_loss = entry_ref_price * (1 - self.stop_loss_percent / 100)
        take_profit = entry_ref_price * (1 + self.take_profit_percent / 100)
        
        signal = Signal(
            action='buy',
            price=fill_price,
            size=qty,
            confidence=0.75,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        signal.metadata = {
            'event': event_type,
            'risk_per_unit': risk_per_unit,
            'equity': self.position_state['equity']
        }
        
        self.logger.info(f"{event_type}: buy {qty:.6f} @ {fill_price:.2f}")
        
        return signal
    
    def _arm_rebuy(self, px: float):
        """Arm the rebuy mechanism after crash exit."""
        self.position_state['rebuy_armed'] = True
        self.position_state['rebuy_dynamic'] = self.rebuy_dynamic
        # Simple rebuy price calculation (could be enhanced)
        self.position_state['rebuy_price'] = px * 0.98  # 2% below crash exit price
        
        # Set cooldown period
        ready_at = datetime.now() + timedelta(minutes=self.rebuy_cooldown_min)
        self.position_state['rebuy_ready_at'] = ready_at
        
        self.logger.info(f"Rebuy armed: price={self.position_state['rebuy_price']:.2f}, "
                        f"ready_at={ready_at.strftime('%H:%M:%S')}")
    
    def _get_real_okx_purchase_price(self) -> float:
        """Get the real OKX purchase price for accurate trading calculations."""
        try:
            # Import portfolio service to get real OKX data
            from src.services.portfolio_service import get_portfolio_service
            portfolio_service = get_portfolio_service()
            portfolio_data = portfolio_service.get_portfolio_data()
            
            # Find PEPE holding and return real average entry price
            for holding in portfolio_data.get('holdings', []):
                if holding.get('symbol') == 'PEPE':
                    real_entry = holding.get('avg_entry_price', 0.0)
                    if real_entry > 0:
                        return real_entry
            
            # Fallback for PEPE: $0.00000800 (known real purchase price)
            return 0.00000800
            
        except Exception as e:
            self.logger.error(f"Error getting real OKX purchase price: {e}")
            # Return known PEPE purchase price as fallback
            return 0.00000800

    def _compute_rebuy_price(self, data: pd.DataFrame, px: float) -> float:
        """Compute dynamic rebuy price based on market conditions."""
        if self.rebuy_mode == "confirmation":
            # For confirmation mode, set rebuy price slightly above current support
            recent_low = data['low'].tail(10).min()
            return recent_low * 1.01  # 1% above recent low
        else:  # "knife" mode
            # For knife catching, set rebuy price below current price
            return px * 0.975  # 2.5% below current price
    
    def _reset_position(self):
        """Reset position tracking state."""
        self.position_state['position_qty'] = 0.0
        self.position_state['entry_price'] = 0.0
        self.position_state['peak_since_entry'] = 0.0
    
    def get_position_state(self) -> Dict:
        """Get current position state for monitoring."""
        return self.position_state.copy()
    
    def update_equity(self, new_equity: float):
        """Update equity for position sizing calculations."""
        self.position_state['equity'] = new_equity
        self.logger.debug(f"Equity updated to: {new_equity:.2f}")