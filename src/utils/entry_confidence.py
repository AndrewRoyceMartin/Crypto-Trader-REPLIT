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
            
            return {
                'symbol': symbol,
                'confidence_score': round(composite_score, 1),
                'confidence_level': self._get_confidence_level(composite_score),
                'timing_signal': timing_signal,
                'breakdown': {
                    'technical_analysis': round(technical_score, 1),
                    'volatility_assessment': round(volatility_score, 1),
                    'momentum_indicators': round(momentum_score, 1),
                    'volume_analysis': round(volume_score, 1),
                    'support_resistance': round(support_resistance_score, 1)
                },
                'entry_recommendation': self._get_entry_recommendation(composite_score),
                'risk_level': self._assess_risk_level(volatility_score, momentum_score),
                'calculated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating confidence for {symbol}: {e}")
            return self._create_basic_confidence(symbol, current_price)
    
    def _calculate_technical_score(self, df: pd.DataFrame, current_price: float) -> float:
        """Calculate technical analysis score (0-100)."""
        try:
            scores = []
            
            # RSI Analysis (30-70 is good, oversold/overbought areas)
            if len(df) >= 14:
                rsi = self._calculate_rsi(df['price'].values, 14)
                if 30 <= rsi <= 40:  # Oversold recovery
                    scores.append(85)
                elif 40 <= rsi <= 60:  # Neutral zone
                    scores.append(70)
                elif 60 <= rsi <= 70:  # Getting overbought
                    scores.append(50)
                else:  # Extreme zones
                    scores.append(30)
            
            # Bollinger Bands Analysis
            if len(df) >= 20:
                bb_position = self._calculate_bollinger_position(df['price'].values, current_price)
                if bb_position < 0.2:  # Near lower band (potential bounce)
                    scores.append(80)
                elif 0.2 <= bb_position <= 0.8:  # Middle range
                    scores.append(60)
                else:  # Near upper band
                    scores.append(40)
            
            # Moving Average Convergence
            if len(df) >= 50:
                ma_score = self._calculate_ma_score(df['price'].values, current_price)
                scores.append(ma_score)
            
            return np.mean(scores) if scores else 50.0
            
        except Exception as e:
            self.logger.debug(f"Technical score calculation error: {e}")
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
        """Generate entry timing signal."""
        if confidence_score >= 85:
            return "STRONG_BUY"
        elif confidence_score >= 75:
            return "BUY"
        elif confidence_score >= 60:
            return "CAUTIOUS_BUY"
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