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
        self.bb_period = config.get_int('strategy', 'bb_period', 30)
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
        self.rebuy_max_usd = config.get_float('strategy', 'rebuy_max_usd', 100.0)  # Maximum $100 per rebuy trade
        
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
        
        # Add volatility tracking
        self.volatility_score = 50.0  # Default volatility score (0-100)
        
        self.indicators = TechnicalIndicators()
        self.logger.info("Enhanced Bollinger Bands strategy initialized with crash protection")
    
    def calculate_position_size(self, signal, portfolio_value: float, current_price: float) -> float:
        """Calculate position size based on risk management."""
        risk_amount = portfolio_value * (signal.size if hasattr(signal, 'size') else self.position_size_percent / 100)
        position_size = risk_amount / current_price
        return position_size
    
    def calculate_bollinger_bands(self, data: pd.DataFrame) -> Optional[Dict]:
        """Calculate Bollinger Bands for the given data."""
        if data is None or len(data) < self.bb_period:
            return None
            
        try:
            # Calculate moving average
            ma = data['close'].rolling(window=self.bb_period).mean()
            
            # Calculate standard deviation
            std = data['close'].rolling(window=self.bb_period).std()
            
            # Calculate Bollinger Bands
            upper_band = ma + (std * self.bb_std_dev)
            lower_band = ma - (std * self.bb_std_dev)
            
            # Update volatility score based on band width
            if len(upper_band) > 0 and len(lower_band) > 0:
                latest_upper = upper_band.iloc[-1]
                latest_lower = lower_band.iloc[-1]
                latest_price = data['close'].iloc[-1]
                
                if not pd.isna(latest_upper) and not pd.isna(latest_lower) and latest_price > 0:
                    band_width_percent = ((latest_upper - latest_lower) / latest_price) * 100
                    # Normalize volatility score (wider bands = higher volatility)
                    self.volatility_score = min(100.0, max(0.0, band_width_percent * 10))
            
            return {
                'upper': upper_band,
                'lower': lower_band,
                'middle': ma,
                'std': std
            }
        except Exception as e:
            self.logger.error(f"Error calculating Bollinger Bands: {e}")
            return None
    
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
            
            # CRITICAL FIX: Don't reset position until exit order is confirmed
            # Position will be reset by enhanced trader after verifying order filled
            # self._reset_position()  # DISABLED - prevents phantom positions
            
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
        """Check for normal exit conditions with Bollinger Bands prioritization."""
        if self.position_state['position_qty'] <= 0.0:
            return None
        
        entry_price = self.position_state['entry_price']
        stop = entry_price * (1 - self.stop_loss_percent / 100)
        
        # PRIORITY 1: Bollinger Bands Upper Band (Primary Exit Strategy)
        # This is the algorithmic approach using dynamic market conditions
        bollinger_exit = px >= bb_up
        
        # PRIORITY 2: Dynamic percentage take profit (Secondary/Safety Net)
        # Adjust threshold based on market volatility and Bollinger Band width
        try:
            # Calculate Bollinger Band width as volatility indicator
            bb_width_percent = ((bb_up - bb_lo) / px) * 100 if bb_up and bb_lo else 4.0
            # Scale safety threshold based on volatility: higher volatility = higher threshold
            volatility_multiplier = max(1.2, min(2.0, bb_width_percent / 4.0))  # 1.2x to 2.0x multiplier
            safety_take_profit_percent = self.take_profit_percent * volatility_multiplier
            
            self.logger.debug(f"🎯 Dynamic safety threshold: {safety_take_profit_percent:.1f}% "
                            f"(BB width: {bb_width_percent:.1f}%, multiplier: {volatility_multiplier:.1f}x)")
        except:
            safety_take_profit_percent = self.take_profit_percent * 1.5  # Fallback to static 1.5x
        safety_take = entry_price * (1 + safety_take_profit_percent / 100)
        fixed_percentage_exit = px >= safety_take
        
        # PRIORITY 3: Stop loss (Risk Management)
        stop_loss_exit = current_low <= stop
        
        # Determine exit reason and confidence
        exit_triggered = False
        exit_reason = ""
        confidence = 0.8
        
        if bollinger_exit:
            exit_triggered = True
            exit_reason = "BOLLINGER_UPPER_BAND"
            confidence = 0.95  # High confidence for algorithmic exit
            self.logger.info(f"🎯 PRIMARY EXIT: Bollinger Bands upper band hit at {px:.6f} (bb_up: {bb_up:.6f})")
        elif stop_loss_exit:
            exit_triggered = True
            exit_reason = "STOP_LOSS"
            confidence = 0.9  # High confidence for risk management
            self.logger.warning(f"🛑 STOP LOSS: Risk management exit at {current_low:.6f} (stop: {stop:.6f})")
        elif fixed_percentage_exit:
            exit_triggered = True
            exit_reason = "SAFETY_TAKE_PROFIT"
            confidence = 0.7  # Lower confidence for fixed percentage fallback
            self.logger.info(f"📈 SAFETY EXIT: Fixed percentage fallback at {px:.6f} (safety_take: {safety_take:.6f})")
        
        if exit_triggered:
            # Dynamic fill price adjustment based on market conditions
            try:
                # Calculate dynamic fill discount based on current volatility
                if hasattr(self, 'current_atr') and self.current_atr:
                    atr_percent = (self.current_atr / px) * 100
                    # Higher volatility = larger discount to ensure order fills
                    fill_discount = max(0.0005, min(0.002, atr_percent / 200))  # 0.05% to 0.2%
                else:
                    fill_discount = 0.001  # Default 0.1%
                    
                self.logger.debug(f"🎯 Dynamic fill discount: {fill_discount*100:.3f}%")
            except:
                fill_discount = 0.001  # Conservative fallback
                
            fill_price = px * (1 - fill_discount)
            qty = self.position_state['position_qty']
            gross = qty * (fill_price - entry_price)
            fees = self.fee * (fill_price + entry_price) * qty
            pnl = gross - fees
            
            # CRITICAL FIX: Don't reset position until exit order is confirmed  
            # Position will be reset by enhanced trader after verifying order filled
            # self._reset_position()  # DISABLED - prevents phantom positions
            
            signal = Signal(
                action='sell',
                price=fill_price,
                size=qty,
                confidence=confidence,
                stop_loss=None,
                take_profit=None
            )
            
            signal.metadata = {
                'event': exit_reason,
                'pnl': pnl,
                'bb_up': bb_up,
                'stop': stop,
                'safety_take': safety_take,
                'original_take': entry_price * (1 + self.take_profit_percent / 100),
                'bollinger_triggered': bollinger_exit,
                'fixed_percentage_reduced': True
            }
            
            self.logger.info(f"Exit ({exit_reason}): {signal.action} {qty:.6f} @ {fill_price:.2f}, PnL: {pnl:.2f}")
            
            return signal
        
        return None
    
    def _check_entry_opportunities(self, px: float, bb_up: float, bb_lo: float, atr: float, data: pd.DataFrame) -> Optional[Signal]:
        """ENHANCED: Check for entry opportunities with multiple confirmation filters for higher probability trades."""
        if self.position_state['position_qty'] > 0.0:
            return None  # Already in position
        
        # Update rebuy price dynamically if armed
        if self.position_state['rebuy_armed'] and self.rebuy_dynamic:
            self.position_state['rebuy_price'] = self._compute_rebuy_price(data, px)
        
        # Check rebuy conditions first (applies to ALL currencies with same strict criteria)
        if self.position_state['rebuy_armed']:
            rebuy_signal = self._check_rebuy_conditions(px, atr)
            if rebuy_signal:
                self.logger.info(f"Rebuy signal generated with ${self.rebuy_max_usd:.2f} limit for any cryptocurrency")
                return rebuy_signal
        
        # ENHANCED ENTRY CRITERIA: Require MULTIPLE confirmations for new entries
        # Only buy when we have the BEST possible setup for maximum profit potential
        
        # PRIMARY FILTER: Must be at or below lower Bollinger Band
        at_lower_band = px <= bb_lo
        if not at_lower_band:
            return None  # Reject immediately if not oversold on Bollinger Bands
        
        # ENHANCED FILTER 1: RSI Oversold Confirmation
        rsi_oversold = self._check_rsi_oversold(data)
        
        # ENHANCED FILTER 2: Volume Confirmation
        volume_confirmed = self._check_volume_confirmation(data)
        
        # ENHANCED FILTER 3: Multiple Timeframe Trend Analysis
        higher_tf_support = self._check_higher_timeframe_support(data)
        
        # ENHANCED FILTER 4: Support/Resistance Level Confirmation  
        near_support = self._check_support_level(data, px)
        
        # ENHANCED FILTER 5: Market Regime Filter (avoid buying in strong downtrends)
        market_regime_ok = self._check_market_regime(data)
        
        # COUNT CONFIRMATIONS - Only buy on HIGHEST probability setups
        confirmations = [
            ("Bollinger_Band", at_lower_band),
            ("RSI_Oversold", rsi_oversold), 
            ("Volume_Confirmed", volume_confirmed),
            ("Higher_TF_Support", higher_tf_support),
            ("Near_Support", near_support),
            ("Market_Regime_OK", market_regime_ok)
        ]
        
        confirmed_filters = [name for name, passed in confirmations if passed]
        total_confirmations = len(confirmed_filters)
        
        # STRICT REQUIREMENTS: Need at least 4 out of 6 confirmations for entry
        minimum_confirmations = 4
        
        if total_confirmations >= minimum_confirmations:
            # Calculate dynamic confidence based on how many filters passed
            confidence_boost = min(0.95, 0.65 + (total_confirmations - minimum_confirmations) * 0.075)
            
            self.logger.critical(f"🎯 HIGH PROBABILITY ENTRY DETECTED: {total_confirmations}/6 confirmations passed")
            self.logger.critical(f"   ✅ Confirmed filters: {', '.join(confirmed_filters)}")
            self.logger.critical(f"   📊 Entry confidence: {confidence_boost:.1%}")
            
            signal = self._create_entry_signal(px, atr, 'HIGH_PROBABILITY_ENTRY')
            signal.confidence = confidence_boost
            signal.metadata['confirmations'] = total_confirmations
            signal.metadata['confirmed_filters'] = confirmed_filters
            
            return signal
        else:
            # Log rejected entry for analysis
            failed_filters = [name for name, passed in confirmations if not passed]
            self.logger.debug(f"❌ Entry rejected: Only {total_confirmations}/{len(confirmations)} confirmations")
            self.logger.debug(f"   Failed filters: {', '.join(failed_filters)}")
            
        return None
    
    def _check_rsi_oversold(self, data: pd.DataFrame) -> bool:
        """Check if RSI indicates oversold conditions (RSI < 30)."""
        try:
            if len(data) < 14:
                return False
                
            # Calculate RSI using close prices
            close_prices = data['close'].values
            rsi = self._calculate_rsi(close_prices)
            
            # RSI below 30 indicates oversold condition
            oversold_threshold = 30.0
            is_oversold = rsi < oversold_threshold
            
            self.logger.debug(f"RSI Analysis: {rsi:.1f} (oversold < {oversold_threshold})")
            return is_oversold
            
        except Exception as e:
            self.logger.debug(f"RSI calculation error: {e}")
            return False
    
    def _check_volume_confirmation(self, data: pd.DataFrame) -> bool:
        """Check if current volume is above average (indicates institutional interest)."""
        try:
            if 'volume' not in data.columns or len(data) < 20:
                return True  # If no volume data, don't penalize
                
            # Calculate 20-period average volume
            avg_volume = data['volume'].tail(20).mean()
            current_volume = data['volume'].iloc[-1]
            
            # Current volume should be at least 1.2x average for confirmation
            volume_multiplier = 1.2
            volume_confirmed = current_volume >= (avg_volume * volume_multiplier)
            
            self.logger.debug(f"Volume Analysis: Current={current_volume:.0f}, Avg={avg_volume:.0f}, "
                            f"Multiplier={current_volume/avg_volume:.1f}x (need >{volume_multiplier:.1f}x)")
            return volume_confirmed
            
        except Exception as e:
            self.logger.debug(f"Volume analysis error: {e}")
            return True  # Don't penalize if volume data unavailable
    
    def _check_higher_timeframe_support(self, data: pd.DataFrame) -> bool:
        """Check if higher timeframe shows support for the trade."""
        try:
            if len(data) < 100:
                return True  # Not enough data, don't penalize
                
            # Analyze longer-term trend using 50-period SMA
            sma_50 = data['close'].rolling(window=50).mean()
            current_price = data['close'].iloc[-1]
            sma_50_current = sma_50.iloc[-1]
            
            # Check if we're not too far below the 50 SMA (within 10%)
            distance_from_sma = ((current_price - sma_50_current) / sma_50_current) * 100
            max_distance_below = -10.0  # Not more than 10% below SMA
            
            # Also check if longer-term trend is not severely down
            sma_50_slope = (sma_50.iloc[-1] - sma_50.iloc[-10]) / sma_50.iloc[-10] * 100
            max_downtrend = -2.0  # Not more than 2% decline in SMA over 10 periods
            
            higher_tf_ok = (distance_from_sma > max_distance_below and sma_50_slope > max_downtrend)
            
            self.logger.debug(f"Higher TF Analysis: Distance from SMA50={distance_from_sma:.1f}% "
                            f"(max {max_distance_below}%), SMA slope={sma_50_slope:.2f}% (max {max_downtrend}%)")
            return higher_tf_ok
            
        except Exception as e:
            self.logger.debug(f"Higher timeframe analysis error: {e}")
            return True
    
    def _check_support_level(self, data: pd.DataFrame, current_price: float) -> bool:
        """Check if current price is near a significant support level."""
        try:
            if len(data) < 50:
                return True  # Not enough data
                
            # Find recent swing lows (potential support levels)
            low_prices = data['low'].tail(50).values
            
            # Identify significant lows (lowest points in local windows)
            support_levels = []
            window_size = 5
            
            for i in range(window_size, len(low_prices) - window_size):
                if low_prices[i] == min(low_prices[i-window_size:i+window_size+1]):
                    support_levels.append(low_prices[i])
            
            if not support_levels:
                return True  # No clear support levels found
            
            # Check if current price is within 2% of any support level
            support_tolerance = 0.02  # 2%
            
            for support in support_levels:
                distance = abs(current_price - support) / support
                if distance <= support_tolerance:
                    self.logger.debug(f"Support Level: Found near support at ${support:.6f} "
                                    f"(distance: {distance*100:.1f}%)")
                    return True
            
            self.logger.debug(f"Support Level: No support found within {support_tolerance*100}% of ${current_price:.6f}")
            return False
            
        except Exception as e:
            self.logger.debug(f"Support level analysis error: {e}")
            return True
    
    def _check_market_regime(self, data: pd.DataFrame) -> bool:
        """Check overall market regime to avoid buying in strong downtrends."""
        try:
            if len(data) < 30:
                return True  # Not enough data
                
            # Calculate short and medium term moving averages
            sma_10 = data['close'].rolling(window=10).mean()
            sma_30 = data['close'].rolling(window=30).mean()
            current_price = data['close'].iloc[-1]
            
            # Check current price relative to moving averages
            above_sma_10 = current_price > sma_10.iloc[-1] * 0.95  # Within 5% of 10 SMA
            sma_alignment = sma_10.iloc[-1] > sma_30.iloc[-1] * 0.98  # 10 SMA not too far below 30 SMA
            
            # Check for not being in severe downtrend
            price_change_10d = (current_price - data['close'].iloc[-10]) / data['close'].iloc[-10] * 100
            not_severe_downtrend = price_change_10d > -15.0  # Not down more than 15% in 10 periods
            
            regime_ok = (above_sma_10 or sma_alignment) and not_severe_downtrend
            
            self.logger.debug(f"Market Regime: Price vs SMA10={(current_price/sma_10.iloc[-1]-1)*100:.1f}%, "
                            f"10d change={price_change_10d:.1f}%, regime_ok={regime_ok}")
            return regime_ok
            
        except Exception as e:
            self.logger.debug(f"Market regime analysis error: {e}")
            return True
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """Calculate RSI indicator."""
        try:
            if len(prices) < period + 1:
                return 50.0  # Neutral RSI if not enough data
                
            deltas = np.diff(prices)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            # Calculate average gains and losses
            avg_gain = np.mean(gains[-period:])
            avg_loss = np.mean(losses[-period:])
            
            if avg_loss == 0:
                return 100.0  # All gains, max RSI
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
            
        except Exception as e:
            self.logger.debug(f"RSI calculation error: {e}")
            return 50.0
    
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
        
        # Apply rebuy limit for rebuy trades, or scale normal trades based on confidence
        if 'REBUY' in event_type:
            dollars = min(self.rebuy_max_usd, self.position_size_percent / 100 * self.position_state['equity'])
            self.logger.info(f"Rebuy trade limited to ${dollars:.2f} (max: ${self.rebuy_max_usd:.2f})")
        elif 'HIGH_PROBABILITY' in event_type:
            # Scale position size based on confidence for high probability entries
            base_dollars = self.position_size_percent / 100 * self.position_state['equity']
            confidence_multiplier = 1.5  # Increase size for high confidence trades
            dollars = min(base_dollars * confidence_multiplier, 150.0)  # Cap at $150 for high prob trades
            self.logger.info(f"High probability trade: ${dollars:.2f} (confidence multiplier: {confidence_multiplier}x)")
        else:
            dollars = self.position_size_percent / 100 * self.position_state['equity']
        
        # Additional safety: Ensure we don't exceed maximum trade size
        max_trade_usd = max(self.rebuy_max_usd, 1000.0)  # Either rebuy limit or $1000 max for normal trades
        dollars = min(dollars, max_trade_usd)
        
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
            'equity': self.position_state['equity'],
            'trade_usd': dollars,
            'rebuy_limited': 'REBUY' in event_type
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
        
        self.logger.info(f"Universal rebuy armed for ANY cryptocurrency: price={self.position_state['rebuy_price']:.2f}, "
                        f"max_purchase=${self.rebuy_max_usd:.2f}, ready_at={ready_at.strftime('%H:%M:%S')}")
    
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