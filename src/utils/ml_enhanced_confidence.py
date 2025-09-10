#!/usr/bin/env python3
"""
ML-Enhanced Entry Point Confidence Analyzer

Integrates machine learning predictions with the existing 6-factor technical analysis
to provide superior entry timing confidence scores for cryptocurrency trading.

Combines:
- Traditional 6-factor technical analysis (RSI, volatility, momentum, volume, support/resistance)
- XGBoost ML model predictions for profitability probability
- Advanced signal logging and learning capabilities
"""

import os
import sys
import logging
from typing import Dict, List, Optional, Tuple, Any

# Add the project root to the path to import ML modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# Import existing confidence analyzer
from src.utils.entry_confidence import EntryConfidenceAnalyzer

logger = logging.getLogger(__name__)

class MLEnhancedConfidenceAnalyzer(EntryConfidenceAnalyzer):
    """
    Enhanced confidence analyzer that combines traditional 6-factor analysis with ML predictions.
    
    Confidence Scale:
    - 90-100: Excellent entry (strong technical setup + high ML probability)
    - 75-89: Good entry (solid technical signals + moderate ML confidence)
    - 60-74: Fair entry (mixed signals, proceed with caution)
    - 40-59: Weak entry (unfavorable conditions)
    - 0-39: Poor entry (avoid, wait for better setup)
    """
    
    def __init__(self):
        super().__init__()
        self.ml_enabled = self._check_ml_availability()
        self.logger = logging.getLogger(__name__)
        
        if self.ml_enabled:
            self.logger.info("✅ ML-Enhanced Confidence Analyzer initialized successfully")
        else:
            self.logger.warning("⚠️ ML predictions unavailable - using traditional 6-factor analysis only")
    
    def _check_ml_availability(self) -> bool:
        """Check if ML prediction system is available."""
        try:
            # Check if ML model file exists
            ml_model_path = os.path.join(project_root, 'ml', 'buy_signal_model.pkl')
            if not os.path.exists(ml_model_path):
                return False
                
            # Try importing ML predictor
            from ml.model_predictor import predict_buy_opportunity
            return True
        except Exception as e:
            logger.debug(f"ML system not available: {e}")
            return False
    
    def _get_ml_prediction(self, symbol: str, indicators: Dict[str, float]) -> Dict[str, Any]:
        """
        Get ML prediction probability for the given signal.
        
        Args:
            symbol: Cryptocurrency symbol
            indicators: Technical indicators dict
            
        Returns:
            Dict with ML prediction results
        """
        if not self.ml_enabled:
            return {
                'ml_probability': 0.5,  # Neutral prediction
                'ml_confidence': 0.0,
                'ml_signal': 'UNAVAILABLE',
                'ml_enabled': False
            }
        
        try:
            from ml.model_predictor import predict_buy_opportunity
            
            # Prepare ML features from technical indicators
            ml_features = {
                'rsi': indicators.get('rsi_14', 50.0),
                'volatility': indicators.get('volatility_7', 10.0), 
                'confidence_score': indicators.get('composite_confidence', 50.0),
                'volume_ratio': 1 if indicators.get('volume_ratio', 1.0) > 1.2 else 0  # Binary feature
            }
            
            # Get ML prediction
            probability = predict_buy_opportunity(ml_features)
            
            # Generate ML signal based on probability
            if probability >= 0.7:
                ml_signal = 'STRONG_BUY'
            elif probability >= 0.6:
                ml_signal = 'BUY'
            elif probability >= 0.5:
                ml_signal = 'NEUTRAL'
            elif probability >= 0.4:
                ml_signal = 'CAUTION'
            else:
                ml_signal = 'AVOID'
            
            # Calculate ML confidence (how far from 0.5 neutral)
            ml_confidence = abs(probability - 0.5) * 2 * 100  # Convert to 0-100 scale
            
            self.logger.debug(f"🔮 ML Prediction for {symbol}: {probability:.1%} probability ({ml_signal})")
            
            return {
                'ml_probability': probability,
                'ml_confidence': ml_confidence,
                'ml_signal': ml_signal,
                'ml_enabled': True,
                'ml_features': ml_features
            }
            
        except Exception as e:
            self.logger.error(f"ML prediction failed for {symbol}: {e}")
            return {
                'ml_probability': 0.5,
                'ml_confidence': 0.0,
                'ml_signal': 'ERROR',
                'ml_enabled': False
            }
    
    def analyze_entry_confidence(self, symbol: str, current_price: float, 
                                volume_24h: float = 0, price_change_24h: float = 0,
                                target_price: Optional[float] = None) -> Dict[str, Any]:
        """
        Analyze entry confidence for a trading position with ML integration.
        
        This is an alias method that provides compatibility with the API endpoint.
        """
        return self.calculate_enhanced_confidence(symbol, current_price)
    
    def calculate_enhanced_confidence(self, symbol: str, current_price: float, 
                                    historical_data: Optional[List[Dict]] = None) -> Dict:
        """
        Calculate enhanced confidence score combining 6-factor analysis with ML predictions.
        
        Args:
            symbol: Cryptocurrency symbol
            current_price: Current market price
            historical_data: Optional historical price data
            
        Returns:
            Dict with enhanced confidence score and ML integration
        """
        # First get traditional 6-factor analysis
        traditional_analysis = self.calculate_confidence(symbol, current_price, historical_data)
        
        if not traditional_analysis:
            return self._create_basic_confidence(symbol, current_price)
        
        # Extract technical indicators for ML prediction
        try:
            if not historical_data:
                historical_data = self._fetch_market_data(symbol, days=30, current_price=current_price)
            
            # Calculate lightweight indicators for ML
            if historical_data and len(historical_data) >= 7:
                import pandas as pd
                df = pd.DataFrame(historical_data)
                df['price'] = pd.to_numeric(df['price'], errors='coerce')
                df['volume'] = pd.to_numeric(df.get('volume', [1000] * len(df)), errors='coerce')
                
                indicators = self._lightweight_indicators(df)
                indicators['composite_confidence'] = traditional_analysis['confidence_score']
            else:
                indicators = {'composite_confidence': traditional_analysis['confidence_score']}
            
            # Get ML prediction
            ml_results = self._get_ml_prediction(symbol, indicators)
            
            # Combine traditional and ML scores
            enhanced_score = self._combine_traditional_and_ml_scores(
                traditional_score=traditional_analysis['confidence_score'],
                ml_probability=ml_results['ml_probability'],
                ml_confidence=ml_results['ml_confidence']
            )
            
            # Enhanced timing signal combining both analyses
            enhanced_timing = self._generate_enhanced_timing_signal(
                traditional_signal=traditional_analysis['timing_signal'],
                ml_signal=str(ml_results['ml_signal']),
                enhanced_score=enhanced_score
            )
            
            # Create enhanced response
            enhanced_analysis = traditional_analysis.copy()
            enhanced_analysis.update({
                'confidence_score': round(enhanced_score, 1),
                'confidence_level': self._get_confidence_level(enhanced_score),
                'timing_signal': enhanced_timing,
                'ml_integration': {
                    'ml_probability': round(ml_results['ml_probability'], 3),
                    'ml_confidence': round(ml_results['ml_confidence'], 1),
                    'ml_signal': ml_results['ml_signal'],
                    'ml_enabled': ml_results['ml_enabled'],
                    'traditional_score': traditional_analysis['confidence_score'],
                    'enhancement_boost': round(enhanced_score - traditional_analysis['confidence_score'], 1)
                },
                'analysis_type': 'ML_ENHANCED',
                'version': '2.0'
            })
            
            # Log signal for ML training if enabled
            self._log_signal_for_training(symbol, current_price, enhanced_analysis, indicators)
            
            return enhanced_analysis
            
        except Exception as e:
            self.logger.error(f"Enhanced confidence calculation failed for {symbol}: {e}")
            # Fall back to traditional analysis
            traditional_analysis['analysis_type'] = 'TRADITIONAL_FALLBACK'
            return traditional_analysis
    
    def _combine_traditional_and_ml_scores(self, traditional_score: float, 
                                         ml_probability: float, ml_confidence: float) -> float:
        """
        Intelligently combine traditional 6-factor score with ML prediction.
        
        Args:
            traditional_score: Score from 6-factor analysis (0-100)
            ml_probability: ML prediction probability (0-1)
            ml_confidence: ML confidence level (0-100)
            
        Returns:
            Enhanced confidence score (0-100)
        """
        if not self.ml_enabled:
            return traditional_score
        
        # Convert ML probability to 0-100 scale
        ml_score = ml_probability * 100
        
        # Dynamic weighting based on ML confidence
        # High ML confidence = more weight to ML
        # Low ML confidence = more weight to traditional analysis
        ml_weight = min(ml_confidence / 100 * 0.4, 0.4)  # Max 40% weight to ML
        traditional_weight = 1.0 - ml_weight
        
        # Combine scores
        combined_score = (traditional_score * traditional_weight) + (ml_score * ml_weight)
        
        # Apply boost/penalty based on ML-traditional agreement
        agreement_factor = 1.0
        score_diff = abs(traditional_score - ml_score) / 100
        
        if score_diff < 0.2:  # Good agreement (within 20 points)
            agreement_factor = 1.1  # 10% boost for agreement
        elif score_diff > 0.4:  # Poor agreement (>40 points difference)
            agreement_factor = 0.95  # 5% penalty for disagreement
        
        final_score = combined_score * agreement_factor
        
        # Ensure score stays within bounds
        return max(0, min(100, final_score))
    
    def _generate_enhanced_timing_signal(self, traditional_signal: str, 
                                       ml_signal: str, enhanced_score: float) -> str:
        """Generate enhanced timing signal combining traditional and ML signals."""
        
        # If ML not available, use traditional signal
        if not self.ml_enabled or ml_signal == 'ERROR':
            return traditional_signal
        
        # Priority matrix for signal combination
        signal_priority = {
            'STRONG_BUY': 5,
            'BUY': 4,
            'CAUTIOUS_BUY': 3,
            'NEUTRAL': 2,
            'WAIT': 1,
            'AVOID': 0
        }
        
        # Map ML signals to traditional format
        ml_mapped = {
            'STRONG_BUY': 'STRONG_BUY',
            'BUY': 'BUY', 
            'NEUTRAL': 'WAIT',
            'CAUTION': 'WAIT',
            'AVOID': 'AVOID'
        }.get(ml_signal, 'WAIT')
        
        # Combine signals based on enhanced score
        if enhanced_score >= 80:
            # High confidence - take the more aggressive signal
            return traditional_signal if signal_priority.get(traditional_signal, 1) >= signal_priority.get(ml_mapped, 1) else ml_mapped
        elif enhanced_score >= 60:
            # Moderate confidence - be conservative 
            return 'CAUTIOUS_BUY' if 'BUY' in [traditional_signal, ml_mapped] else 'WAIT'
        else:
            # Low confidence - be very conservative
            return 'WAIT' if enhanced_score >= 40 else 'AVOID'
    
    def _log_signal_for_training(self, symbol: str, current_price: float, 
                               analysis: Dict, indicators: Dict) -> None:
        """Log enhanced signal data for ML training and improvement."""
        try:
            # Try to import signal logger (optional)
            try:
                import sys
                import os
                # Add project root to path for signal logger import
                project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
                if project_root not in sys.path:
                    sys.path.append(project_root)
                # Try to import signal logger - it's optional
                try:
                    from logger.signal_logger import log_buy_signal
                except ImportError:
                    # Signal logging not available
                    self.logger.debug("Signal logging not available")
                    return
            except (ImportError, AttributeError):
                # Signal logging not available
                self.logger.debug("Signal logging not available")
                return
            
            # Extract key data for logging
            signal_data = {
                'symbol': symbol,
                'current_price': current_price,
                'confidence_score': analysis['confidence_score'],
                'timing_signal': analysis['timing_signal'],
                'ml_probability': analysis.get('ml_integration', {}).get('ml_probability', 0),
                'traditional_score': analysis.get('ml_integration', {}).get('traditional_score', 0),
                'rsi': indicators.get('rsi_14', 50),
                'volatility': indicators.get('volatility_7', 10),
                'volume_ratio': indicators.get('volume_ratio', 1),
                'analysis_type': 'ML_ENHANCED'
            }
            
            # Log the signal
            log_buy_signal(
                symbol=symbol,
                price=current_price,
                confidence_score=analysis['confidence_score'],
                rsi=signal_data['rsi'],
                volatility=signal_data['volatility'], 
                volume_ratio=signal_data['volume_ratio'],
                timing_signal=analysis['timing_signal'],
                ml_probability=signal_data['ml_probability'],
                analysis_type='ML_ENHANCED'
            )
            
        except Exception as e:
            # Don't fail the main analysis if logging fails
            self.logger.debug(f"Signal logging failed for {symbol}: {e}")
    
    def get_ml_status(self) -> Dict[str, bool]:
        """Get status of ML integration."""
        return {
            'ml_enabled': self.ml_enabled,
            'predictor_available': self._check_ml_availability(),
            'signal_logging_enabled': True
        }

# Convenience function for backward compatibility
def calculate_ml_enhanced_confidence(symbol: str, current_price: float, 
                                   historical_data: Optional[List[Dict]] = None) -> Dict:
    """
    Convenience function to calculate ML-enhanced confidence.
    
    Args:
        symbol: Cryptocurrency symbol
        current_price: Current market price  
        historical_data: Optional historical price data
        
    Returns:
        Enhanced confidence analysis with ML integration
    """
    analyzer = MLEnhancedConfidenceAnalyzer()
    return analyzer.calculate_enhanced_confidence(symbol, current_price, historical_data)

# Export the main class and convenience function
__all__ = ['MLEnhancedConfidenceAnalyzer', 'calculate_ml_enhanced_confidence']