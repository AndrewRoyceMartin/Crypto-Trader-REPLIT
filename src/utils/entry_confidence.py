#!/usr/bin/env python3
"""
Predictive Entry Point Confidence Indicator

Analyzes multiple factors to provide confidence scores for entry timing:
- Technical indicators (RSI, Bollinger Bands, MACD)
- Market volatility and momentum
- Volume analysis
- Support/resistance levels
- Market sentiment indicators
"""

import numpy as np
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests
import time

logger = logging.getLogger(__name__)

class EntryConfidenceAnalyzer:
    """
    Analyzes market conditions to provide entry point confidence scores.
    
    Confidence Scale:
    - 90-100: Excellent entry (strong technical setup + favorable conditions)
    - 75-89: Good entry (solid technical signals)
    - 60-74: Fair entry (mixed signals, proceed with caution)
    - 40-59: Weak entry (unfavorable conditions)
    - 0-39: Poor entry (avoid, wait for better setup)
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def calculate_confidence(self, symbol: str, current_price: float, 
                           historical_data: Optional[List[Dict]] = None) -> Dict:
        """
        Calculate entry confidence score for a symbol.
        
        Args:
            symbol: Cryptocurrency symbol
            current_price: Current market price
            historical_data: Optional historical price data
            
        Returns:
            Dict with confidence score and breakdown
        """
        try:
            # Get or generate historical data for analysis
            if not historical_data:
                historical_data = self._fetch_market_data(symbol)
            
            if not historical_data or len(historical_data) < 20:
                return self._create_basic_confidence(symbol, current_price)
            
            # Convert to DataFrame for analysis
            df = pd.DataFrame(historical_data)
            df['price'] = df['price'].astype(float)
            df['volume'] = df.get('volume', [1000] * len(df)).astype(float)
            
            # Calculate individual confidence components
            technical_score = self._calculate_technical_score(df, current_price)
            volatility_score = self._calculate_volatility_score(df, current_price)
            momentum_score = self._calculate_momentum_score(df, current_price)
            volume_score = self._calculate_volume_score(df)
            support_resistance_score = self._calculate_support_resistance_score(df, current_price)
            
            # Weighted composite score
            weights = {
                'technical': 0.30,
                'volatility': 0.25,
                'momentum': 0.20,
                'volume': 0.15,
                'support_resistance': 0.10
            }
            
            composite_score = (
                technical_score * weights['technical'] +
                volatility_score * weights['volatility'] +
                momentum_score * weights['momentum'] +
                volume_score * weights['volume'] +
                support_resistance_score * weights['support_resistance']
            )
            
            # Generate entry timing recommendation
            timing_signal = self._generate_timing_signal(composite_score, df, current_price)
            
            # CRITICAL: Calculate intelligent target buy price using 3-day analysis
            suggested_target_price = self._calculate_intelligent_target_price(df, current_price, composite_score)

            return {
                'symbol': symbol,
                'confidence_score': round(composite_score, 1),
                'confidence_level': self._get_confidence_level(composite_score),
                'timing_signal': timing_signal,
                'suggested_target_price': suggested_target_price,  # NEW: Intelligent target based on 3-day analysis
                'breakdown': {
                    'technical_analysis': round(technical_score, 1),
                    'volatility_assessment': round(volatility_score, 1),
                    'momentum_indicators': round(momentum_score, 1),
                    'volume_analysis': round(volume_score, 1),
                    'support_resistance': round(support_resistance_score, 1)
                },
                'enhanced_filters': self._get_enhanced_filter_breakdown(df, current_price),
                'entry_recommendation': self._get_entry_recommendation(composite_score),
                'risk_level': self._assess_risk_level(volatility_score, momentum_score),
                'calculated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating confidence for {symbol}: {e}")
            return self._create_basic_confidence(symbol, current_price)
    
    def _calculate_technical_score(self, df: pd.DataFrame, current_price: float) -> float:
        """
        ENHANCED: Calculate technical analysis score using new multiple confirmation filters.
        
        Uses the same enhanced criteria as the Bollinger strategy:
        - RSI oversold confirmation
        - Volume confirmation 
        - Higher timeframe support
        - Support level proximity
        - Market regime filter
        - Bollinger Band position
        """
        try:
            # Apply the same enhanced filters as the Bollinger strategy
            confirmations = []
            
            # FILTER 1: RSI Oversold Confirmation (RSI < 30)
            if len(df) >= 14:
                rsi = self._calculate_rsi(df['price'].values, 14)
                rsi_oversold = rsi < 30.0
                confirmations.append(("RSI_Oversold", rsi_oversold))
                self.logger.debug(f"RSI Analysis: {rsi:.1f} (oversold < 30.0) = {rsi_oversold}")
            
            # FILTER 2: Volume Confirmation (1.2x above average)
            if 'volume' in df.columns and len(df) >= 20:
                avg_volume = df['volume'].tail(20).mean()
                current_volume = df['volume'].iloc[-1]
                volume_confirmed = current_volume >= (avg_volume * 1.2)
                confirmations.append(("Volume_Confirmed", volume_confirmed))
                self.logger.debug(f"Volume: Current={current_volume:.0f}, Avg={avg_volume:.0f}, "
                                f"Multiplier={current_volume/avg_volume:.1f}x = {volume_confirmed}")
            
            # FILTER 3: Higher Timeframe Support (50-SMA analysis)
            if len(df) >= 100:
                sma_50 = df['price'].rolling(window=50).mean()
                current_price_val = df['price'].iloc[-1]
                sma_50_current = sma_50.iloc[-1]
                
                # Not more than 10% below SMA50
                distance_from_sma = ((current_price_val - sma_50_current) / sma_50_current) * 100
                sma_50_slope = (sma_50.iloc[-1] - sma_50.iloc[-10]) / sma_50.iloc[-10] * 100
                
                higher_tf_ok = (distance_from_sma > -10.0 and sma_50_slope > -2.0)
                confirmations.append(("Higher_TF_Support", higher_tf_ok))
                self.logger.debug(f"Higher TF: Distance from SMA50={distance_from_sma:.1f}%, "
                                f"slope={sma_50_slope:.2f}% = {higher_tf_ok}")
            
            # FILTER 4: Support Level Proximity (within 2% of support)
            if len(df) >= 50:
                near_support = self._check_support_proximity(df, current_price)
                confirmations.append(("Near_Support", near_support))
            
            # FILTER 5: Market Regime Filter (not in severe downtrend)
            if len(df) >= 30:
                sma_10 = df['price'].rolling(window=10).mean()
                sma_30 = df['price'].rolling(window=30).mean()
                current_price_val = df['price'].iloc[-1]
                
                above_sma_10 = current_price_val > sma_10.iloc[-1] * 0.95
                sma_alignment = sma_10.iloc[-1] > sma_30.iloc[-1] * 0.98
                price_change_10d = (current_price_val - df['price'].iloc[-10]) / df['price'].iloc[-10] * 100
                not_severe_downtrend = price_change_10d > -15.0
                
                regime_ok = (above_sma_10 or sma_alignment) and not_severe_downtrend
                confirmations.append(("Market_Regime_OK", regime_ok))
                self.logger.debug(f"Market Regime: Price vs SMA10={(current_price_val/sma_10.iloc[-1]-1)*100:.1f}%, "
                                f"10d change={price_change_10d:.1f}% = {regime_ok}")
            
            # FILTER 6: Bollinger Band Position (at lower band)
            if len(df) >= 20:
                # Calculate Bollinger Bands
                sma_20 = df['price'].rolling(window=20).mean()
                std_20 = df['price'].rolling(window=20).std()
                bb_lower = sma_20 - (2 * std_20)
                
                at_lower_band = current_price <= bb_lower.iloc[-1]
                confirmations.append(("Bollinger_Band", at_lower_band))
                self.logger.debug(f"Bollinger Band: Price={current_price:.4f}, Lower={bb_lower.iloc[-1]:.4f} = {at_lower_band}")
            
            # COUNT CONFIRMATIONS - Apply same strict requirements as Bollinger strategy
            confirmed_filters = [name for name, passed in confirmations if passed]
            total_confirmations = len(confirmed_filters)
            minimum_confirmations = 4  # Same as enhanced strategy
            
            if total_confirmations >= minimum_confirmations:
                # HIGH PROBABILITY SETUP - Scale score based on confirmations
                base_score = 75.0  # Minimum for high probability
                bonus_score = (total_confirmations - minimum_confirmations) * 5.0  # 5 points per extra confirmation
                final_score = min(95.0, base_score + bonus_score)
                
                self.logger.info(f"🎯 HIGH PROBABILITY TECHNICAL SETUP: {total_confirmations}/6 confirmations = {final_score:.1f}%")
                self.logger.info(f"   ✅ Confirmed filters: {', '.join(confirmed_filters)}")
                return final_score
            else:
                # INSUFFICIENT CONFIRMATIONS - Much lower score 
                failed_filters = [name for name, passed in confirmations if not passed]
                penalty_score = max(20.0, 60.0 - (minimum_confirmations - total_confirmations) * 10.0)
                
                self.logger.debug(f"❌ INSUFFICIENT CONFIRMATIONS: Only {total_confirmations}/{len(confirmations)} = {penalty_score:.1f}%")
                self.logger.debug(f"   Failed filters: {', '.join(failed_filters)}")
                return penalty_score
            
        except Exception as e:
            self.logger.error(f"Technical score calculation error: {e}")
            return 40.0  # Conservative fallback
    
    def _check_support_proximity(self, df: pd.DataFrame, current_price: float) -> bool:
        """Check if current price is near a significant support level."""
        try:
            # Find recent swing lows (potential support levels)
            low_prices = df['low'].tail(50).values if 'low' in df.columns else df['price'].tail(50).values
            
            # Identify significant lows (lowest points in local windows)
            support_levels = []
            window_size = 5
            
            for i in range(window_size, len(low_prices) - window_size):
                if low_prices[i] == min(low_prices[i-window_size:i+window_size+1]):
                    support_levels.append(low_prices[i])
            
            if not support_levels:
                return True  # No clear support levels found, don't penalize
            
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
    
    def _get_enhanced_filter_breakdown(self, df: pd.DataFrame, current_price: float) -> dict:
        """
        ENHANCED: Return detailed breakdown of all 6 enhanced confirmation filters for frontend display.
        """
        try:
            filters = {}
            
            # FILTER 1: RSI Oversold Confirmation
            if len(df) >= 14:
                rsi = self._calculate_rsi(df['price'].values, 14)
                filters['rsi_oversold'] = {
                    'passed': bool(rsi < 30.0),
                    'value': round(float(rsi), 1),
                    'threshold': 30.0,
                    'description': 'RSI below 30 indicates oversold conditions'
                }
            
            # FILTER 2: Volume Confirmation
            if 'volume' in df.columns and len(df) >= 20:
                avg_volume = df['volume'].tail(20).mean()
                current_volume = df['volume'].iloc[-1]
                volume_multiplier = current_volume / avg_volume if avg_volume > 0 else 0
                filters['volume_confirmation'] = {
                    'passed': bool(volume_multiplier >= 1.2),
                    'value': round(float(volume_multiplier), 2),
                    'threshold': 1.2,
                    'description': 'Current volume should be 1.2x above 20-day average'
                }
            
            # FILTER 3: Higher Timeframe Support
            if len(df) >= 100:
                sma_50 = df['price'].rolling(window=50).mean()
                current_price_val = df['price'].iloc[-1]
                sma_50_current = sma_50.iloc[-1]
                distance_from_sma = ((current_price_val - sma_50_current) / sma_50_current) * 100
                sma_50_slope = (sma_50.iloc[-1] - sma_50.iloc[-10]) / sma_50.iloc[-10] * 100
                higher_tf_ok = (distance_from_sma > -10.0 and sma_50_slope > -2.0)
                
                filters['higher_timeframe_support'] = {
                    'passed': bool(higher_tf_ok),
                    'sma_distance': round(float(distance_from_sma), 1),
                    'sma_slope': round(float(sma_50_slope), 2),
                    'description': 'Price within 10% of SMA50 and not in severe downtrend'
                }
            
            # FILTER 4: Support Level Proximity
            if len(df) >= 50:
                near_support = self._check_support_proximity(df, current_price)
                filters['support_level_proximity'] = {
                    'passed': bool(near_support),
                    'description': 'Price within 2% of significant support level'
                }
            
            # FILTER 5: Market Regime Filter
            if len(df) >= 30:
                sma_10 = df['price'].rolling(window=10).mean()
                sma_30 = df['price'].rolling(window=30).mean()
                current_price_val = df['price'].iloc[-1]
                
                above_sma_10 = current_price_val > sma_10.iloc[-1] * 0.95
                sma_alignment = sma_10.iloc[-1] > sma_30.iloc[-1] * 0.98
                price_change_10d = (current_price_val - df['price'].iloc[-10]) / df['price'].iloc[-10] * 100
                regime_ok = (above_sma_10 or sma_alignment) and price_change_10d > -15.0
                
                filters['market_regime'] = {
                    'passed': bool(regime_ok),
                    'price_vs_sma10': round(float((current_price_val/sma_10.iloc[-1]-1)*100), 1),
                    'price_change_10d': round(float(price_change_10d), 1),
                    'description': 'Market not in severe downtrend (within 15% of 10-day high)'
                }
            
            # FILTER 6: Bollinger Band Position
            if len(df) >= 20:
                sma_20 = df['price'].rolling(window=20).mean()
                std_20 = df['price'].rolling(window=20).std()
                bb_lower = sma_20 - (2 * std_20)
                at_lower_band = current_price <= bb_lower.iloc[-1]
                
                filters['bollinger_band_position'] = {
                    'passed': bool(at_lower_band),
                    'lower_band': round(float(bb_lower.iloc[-1]), 6),
                    'current_price': float(current_price),
                    'description': 'Price at or below lower Bollinger Band (oversold)'
                }
            
            # Calculate total confirmations
            total_confirmations = sum(1 for f in filters.values() if f.get('passed', False))
            filters['summary'] = {
                'total_confirmations': int(total_confirmations),
                'total_filters': int(len(filters) - 1),  # Subtract summary itself
                'minimum_required': 4,
                'meets_requirements': bool(total_confirmations >= 4)
            }
            
            return filters
            
        except Exception as e:
            self.logger.error(f"Enhanced filter breakdown error: {e}")
            return {'error': 'Unable to calculate enhanced filters'}
    
    def _calculate_ma_score(self, prices: np.ndarray, current_price: float) -> float:
        """Calculate moving average score."""
        try:
            ma_20 = np.mean(prices[-20:])
            ma_50 = np.mean(prices[-50:]) if len(prices) >= 50 else ma_20
            
            score = 50
            
            # Price above both MAs
            if current_price > ma_20 and current_price > ma_50:
                score += 20
            # Price above 20 MA but below 50 MA
            elif current_price > ma_20:
                score += 10
            # Price below both MAs
            else:
                score -= 10
            
            # MA alignment (20 above 50 is bullish)
            if ma_20 > ma_50:
                score += 10
            else:
                score -= 5
            
            return max(0, min(100, score))
            
        except Exception as e:
            self.logger.debug(f"MA score calculation error: {e}")
            return 50.0
    
    def _calculate_volatility_score(self, df: pd.DataFrame, current_price: float) -> float:
        """Calculate volatility-based score (0-100)."""
        try:
            prices = df['price'].values
            
            # Calculate 14-day volatility
            returns = np.diff(np.log(prices))
            volatility = np.std(returns) * np.sqrt(14) * 100
            
            # Score based on volatility level
            if volatility < 5:  # Low volatility (good for entries)
                return 85
            elif volatility < 15:  # Moderate volatility
                return 70
            elif volatility < 25:  # High volatility
                return 50
            else:  # Extreme volatility (risky)
                return 25
                
        except Exception as e:
            self.logger.debug(f"Volatility score calculation error: {e}")
            return 50.0
    
    def _calculate_momentum_score(self, df: pd.DataFrame, current_price: float) -> float:
        """Calculate momentum score (0-100)."""
        try:
            prices = df['price'].values
            
            # Short-term momentum (3-day vs 7-day)
            if len(prices) >= 7:
                recent_avg = np.mean(prices[-3:])
                week_avg = np.mean(prices[-7:])
                short_momentum = (recent_avg - week_avg) / week_avg * 100
            else:
                short_momentum = 0
            
            # Medium-term momentum (current vs 14-day avg)
            if len(prices) >= 14:
                two_week_avg = np.mean(prices[-14:])
                medium_momentum = (current_price - two_week_avg) / two_week_avg * 100
            else:
                medium_momentum = 0
            
            # Score based on momentum
            momentum_score = 50  # Base score
            
            # Positive momentum adds points
            if short_momentum > 2:
                momentum_score += 20
            elif short_momentum > 0:
                momentum_score += 10
            elif short_momentum < -2:
                momentum_score -= 15
            
            if medium_momentum > 5:
                momentum_score += 15
            elif medium_momentum > 0:
                momentum_score += 5
            elif medium_momentum < -5:
                momentum_score -= 10
            
            return max(0, min(100, momentum_score))
            
        except Exception as e:
            self.logger.debug(f"Momentum score calculation error: {e}")
            return 50.0
    
    def _calculate_volume_score(self, df: pd.DataFrame) -> float:
        """Calculate volume-based score (0-100)."""
        try:
            volumes = df['volume'].values
            
            if len(volumes) < 5:
                return 50.0
            
            # Compare recent volume to average
            recent_volume = np.mean(volumes[-3:])
            avg_volume = np.mean(volumes[:-3])
            
            if avg_volume > 0:
                volume_ratio = recent_volume / avg_volume
                
                if volume_ratio > 1.5:  # High volume (good confirmation)
                    return 80
                elif volume_ratio > 1.2:  # Above average volume
                    return 70
                elif volume_ratio > 0.8:  # Normal volume
                    return 60
                else:  # Low volume (weak signal)
                    return 40
            
            return 50.0
            
        except Exception as e:
            self.logger.debug(f"Volume score calculation error: {e}")
            return 50.0
    
    def _calculate_support_resistance_score(self, df: pd.DataFrame, current_price: float) -> float:
        """Calculate support/resistance score (0-100)."""
        try:
            prices = df['price'].values
            
            # Find potential support levels (recent lows)
            if len(prices) >= 10:
                recent_low = np.min(prices[-10:])
                distance_from_support = (current_price - recent_low) / recent_low * 100
                
                if distance_from_support < 2:  # Very close to support
                    return 85
                elif distance_from_support < 5:  # Near support
                    return 75
                elif distance_from_support < 10:  # Moderate distance
                    return 60
                else:  # Far from support
                    return 45
            
            return 50.0
            
        except Exception as e:
            self.logger.debug(f"Support/resistance score calculation error: {e}")
            return 50.0
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """Calculate RSI indicator."""
        try:
            deltas = np.diff(prices)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            avg_gain = np.mean(gains[-period:])
            avg_loss = np.mean(losses[-period:])
            
            if avg_loss == 0:
                return 100
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
            
        except Exception:
            return 50.0
    
    def _calculate_bollinger_position(self, prices: np.ndarray, current_price: float, period: int = 20) -> float:
        """Calculate position within Bollinger Bands (0-1)."""
        try:
            sma = np.mean(prices[-period:])
            std = np.std(prices[-period:])
            
            upper_band = sma + (2 * std)
            lower_band = sma - (2 * std)
            
            # Position within bands (0 = lower band, 1 = upper band)
            position = (current_price - lower_band) / (upper_band - lower_band)
            return max(0, min(1, position))
            
        except Exception:
            return 0.5
    
    def _calculate_ma_score(self, prices: np.ndarray, current_price: float) -> float:
        """Calculate moving average score."""
        try:
            ma_20 = np.mean(prices[-20:])
            ma_50 = np.mean(prices[-50:]) if len(prices) >= 50 else ma_20
            
            score = 50
            
            # Price above moving averages is positive
            if current_price > ma_20:
                score += 15
            if current_price > ma_50:
                score += 10
            
            # Golden cross (short MA above long MA)
            if ma_20 > ma_50:
                score += 15
            
            return min(100, score)
            
        except Exception:
            return 50.0
    
    def _generate_timing_signal(self, confidence_score: float, df: pd.DataFrame, current_price: float) -> str:
        """Generate entry timing signal ALIGNED with Enhanced 6-Filter Bollinger Bands strategy."""
        try:
            # Check if we're in Bollinger Bands BUY ZONE (at or below lower band)
            bollinger_zone = False
            if len(df) >= 20:
                prices = df['price'].values
                sma = np.mean(prices[-20:])
                std = np.std(prices[-20:])
                bb_lower = sma - (2 * std)
                bollinger_zone = current_price <= bb_lower * 1.01  # Within 1% of lower band
            
            # ENHANCED CRITERIA: Align with 6-filter system thresholds
            # Score of 75+ means 4+ confirmations (minimum requirement)
            # Score of 85+ means 5-6 confirmations (excellent setup)
            
            if confidence_score >= 85:
                # EXCELLENT: 5-6 confirmations passed
                return "STRONG_BUY"
            elif confidence_score >= 75:
                # HIGH PROBABILITY: 4+ confirmations passed (meets enhanced criteria)
                return "BUY"
            elif confidence_score >= 65:
                # MODERATE: 3 confirmations + some additional factors
                if bollinger_zone:
                    return "CAUTIOUS_BUY"  # At Bollinger Band gives slight boost
                else:
                    return "WAIT"  # Not quite enough confirmations
            elif confidence_score >= 50:
                # WEAK: Only 2-3 confirmations, insufficient for enhanced strategy
                return "WAIT"
            else:
                # POOR: Very few confirmations, avoid entry
                return "AVOID"
                
        except Exception:
            pass
            
        # Fallback for score-based decisions
        if confidence_score >= 75:
            return "BUY"  # Meets enhanced minimum requirement
        elif confidence_score >= 65:
            return "CAUTIOUS_BUY"
        elif confidence_score >= 50:
            return "WAIT"
        elif confidence_score >= 40:
            return "WAIT"
        else:
            return "AVOID"
    
    def _get_confidence_level(self, score: float) -> str:
        """Convert score to confidence level."""
        if score >= 90:
            return "EXCELLENT"
        elif score >= 75:
            return "GOOD"
        elif score >= 60:
            return "FAIR"
        elif score >= 40:
            return "WEAK"
        else:
            return "POOR"
    
    def _get_entry_recommendation(self, score: float) -> str:
        """Get entry recommendation text."""
        if score >= 85:
            return "Strong technical setup with favorable conditions. Consider entering position."
        elif score >= 75:
            return "Good entry opportunity with solid technical signals."
        elif score >= 60:
            return "Mixed signals present. Use smaller position size and tight stops."
        elif score >= 40:
            return "Unfavorable conditions. Wait for better setup."
        else:
            return "Poor entry conditions. Avoid until technical picture improves."
    
    def _calculate_intelligent_target_price(self, df: pd.DataFrame, current_price: float, confidence_score: float) -> float:
        """
        Calculate intelligent target buy price using 3-day momentum analysis.
        
        This replaces the simple discount-based system with sophisticated analysis.
        """
        try:
            prices = df['price'].values
            
            # 3-day vs 7-day momentum analysis (core algorithm)
            recent_avg = np.mean(prices[-3:]) if len(prices) >= 3 else current_price
            week_avg = np.mean(prices[-7:]) if len(prices) >= 7 else current_price
            short_momentum = (recent_avg - week_avg) / week_avg * 100 if week_avg > 0 else 0
            
            # 14-day medium-term momentum
            two_week_avg = np.mean(prices[-14:]) if len(prices) >= 14 else current_price
            medium_momentum = (current_price - two_week_avg) / two_week_avg * 100 if two_week_avg > 0 else 0
            
            # Support level calculation
            support_level = np.min(prices[-14:]) if len(prices) >= 14 else current_price * 0.95
            
            # Bollinger Bands lower band (strong support)
            if len(prices) >= 20:
                sma = np.mean(prices[-20:])
                std = np.std(prices[-20:])
                bb_lower = sma - (2 * std)
            else:
                bb_lower = current_price * 0.97
            
            # RSI-based adjustment
            rsi = self._calculate_rsi(prices, 14) if len(prices) >= 14 else 50
            
            # INTELLIGENT TARGET CALCULATION
            base_target = current_price
            
            # 1. Momentum-based adjustment
            if short_momentum < -5:  # Strong downward momentum
                momentum_discount = 0.03 + (abs(short_momentum) * 0.001)  # 3%+ based on momentum
            elif short_momentum < -2:  # Moderate downward momentum
                momentum_discount = 0.02 + (abs(short_momentum) * 0.002)  # 2%+ 
            elif short_momentum < 0:  # Slight downward momentum
                momentum_discount = 0.015  # 1.5%
            else:  # Upward momentum - be more aggressive
                momentum_discount = 0.01  # 1% only
            
            # 2. Support level consideration
            support_distance = (current_price - support_level) / current_price
            if support_distance > 0.05:  # Far from support
                support_factor = 0.98  # Can go lower
            else:  # Near support
                support_factor = 1.005  # Be more conservative
                
            # 3. RSI-based fine tuning
            if rsi < 30:  # Oversold - more aggressive
                rsi_factor = 0.98
            elif rsi < 40:  # Getting oversold
                rsi_factor = 0.99
            elif rsi > 70:  # Overbought - be cautious
                rsi_factor = 1.01
            else:  # Neutral
                rsi_factor = 1.0
            
            # 4. Confidence-based adjustment
            if confidence_score >= 75:  # High confidence - be more aggressive
                confidence_factor = 0.985
            elif confidence_score >= 60:  # Moderate confidence
                confidence_factor = 0.995
            else:  # Low confidence - be conservative
                confidence_factor = 1.005
            
            # FINAL INTELLIGENT TARGET PRICE
            # Use the most conservative of: momentum target, Bollinger lower, or support level
            momentum_target = current_price * (1 - momentum_discount) * support_factor * rsi_factor * confidence_factor
            technical_target = min(bb_lower * 1.002, support_level * 1.005)  # Slight buffer above key levels
            
            # Choose the higher of the two (more conservative entry)
            target_price = max(momentum_target, technical_target)
            
            # Safety bounds: never more than 10% below current price
            min_target = current_price * 0.90
            max_target = current_price * 0.99
            
            final_target = max(min_target, min(max_target, target_price))
            
            self.logger.debug(f"🎯 INTELLIGENT TARGET: {current_price:.6f} → {final_target:.6f} "
                            f"(momentum: {short_momentum:.1f}%, support: {support_level:.6f}, "
                            f"confidence: {confidence_score:.1f})")
            
            return final_target
            
        except Exception as e:
            self.logger.warning(f"Error calculating intelligent target price: {e}")
            # Fallback to conservative 2% discount
            return current_price * 0.98

    def _assess_risk_level(self, volatility_score: float, momentum_score: float) -> str:
        """Assess overall risk level."""
        avg_score = (volatility_score + momentum_score) / 2
        
        if avg_score >= 75:
            return "LOW"
        elif avg_score >= 60:
            return "MODERATE"
        elif avg_score >= 40:
            return "HIGH"
        else:
            return "VERY_HIGH"
    
    def _fetch_market_data(self, symbol: str, days: int = 30) -> List[Dict]:
        """Fetch historical market data for analysis."""
        try:
            # Generate synthetic historical data for demonstration
            # In production, this would fetch from actual price APIs
            
            base_price = 100.0  # Starting price
            data = []
            
            for i in range(days):
                # Simulate realistic price movement
                change = np.random.normal(0, 0.02)  # 2% daily volatility
                base_price *= (1 + change)
                
                # Simulate volume
                volume = np.random.uniform(1000, 5000)
                
                date = datetime.now() - timedelta(days=days-i)
                
                data.append({
                    'date': date.isoformat(),
                    'price': base_price,
                    'volume': volume
                })
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error fetching market data for {symbol}: {e}")
            return []
    
    def _create_basic_confidence(self, symbol: str, current_price: float) -> Dict:
        """Create basic confidence assessment when data is limited."""
        # Conservative assessment for unknown conditions
        basic_score = 55.0
        
        return {
            'symbol': symbol,
            'confidence_score': basic_score,
            'confidence_level': "FAIR",
            'timing_signal': "CAUTIOUS_BUY",
            'breakdown': {
                'technical_analysis': 50.0,
                'volatility_assessment': 55.0,
                'momentum_indicators': 50.0,
                'volume_analysis': 50.0,
                'support_resistance': 50.0
            },
            'entry_recommendation': "Limited data available. Use conservative position sizing.",
            'risk_level': "MODERATE",
            'calculated_at': datetime.now().isoformat(),
            'note': "Analysis based on limited data"
        }

# Global instance
_confidence_analyzer = None

def get_confidence_analyzer() -> EntryConfidenceAnalyzer:
    """Get singleton confidence analyzer instance."""
    global _confidence_analyzer
    if _confidence_analyzer is None:
        _confidence_analyzer = EntryConfidenceAnalyzer()
    return _confidence_analyzer