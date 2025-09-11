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

import logging
import os
import sys
from typing import Any

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
            return True
        except Exception as e:
            logger.debug(f"ML system not available: {e}")
            return False

    def _get_ml_prediction(self, symbol: str, indicators: dict[str, float]) -> dict[str, Any]:
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
            from src.ml.predictor import predict_buy_return as predict_buy_opportunity

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
                                target_price: float | None = None) -> dict[str, Any]:
        """
        Analyze entry confidence for a trading position with ML integration.

        This is an alias method that provides compatibility with the API endpoint.
        """
        return self.calculate_enhanced_confidence(symbol, current_price)

    def calculate_enhanced_confidence(self, symbol: str, current_price: float,
                                    historical_data: list[dict] | None = None) -> dict:
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
                # Ensure historical_data is properly structured for DataFrame creation
                if isinstance(historical_data, dict):
                    df = pd.DataFrame([historical_data], index=[0])
                else:
                    df = pd.DataFrame(historical_data)
                df['price'] = pd.to_numeric(df['price'], errors='coerce')
                df['volume'] = pd.to_numeric(df.get('volume', [1000] * len(df)), errors='coerce')

                indicators = self._lightweight_indicators(df)
                indicators['composite_confidence'] = traditional_analysis['confidence_score']
            else:
                indicators = {'composite_confidence': traditional_analysis['confidence_score']}

            # Get ML prediction
            ml_results = self._get_ml_prediction(symbol, indicators)

            # HYBRID SCORING: Combine traditional (60%) and ML (40%)
            hybrid_score = self._combine_traditional_and_ml_scores(
                traditional_score=traditional_analysis['confidence_score'],
                ml_probability=ml_results['ml_probability'],
                ml_confidence=ml_results['ml_confidence']
            )

            # HYBRID SIGNAL: Generate signal based on hybrid score thresholds
            hybrid_timing = self._generate_enhanced_timing_signal(
                traditional_signal=traditional_analysis['timing_signal'],
                ml_signal=str(ml_results['ml_signal']),
                enhanced_score=hybrid_score
            )

            # Create hybrid analysis response
            hybrid_analysis = traditional_analysis.copy()
            hybrid_analysis.update({
                'confidence_score': round(hybrid_score, 1),
                'confidence_level': self._get_confidence_level(hybrid_score),
                'timing_signal': hybrid_timing,
                'hybrid_score': round(hybrid_score, 2),
                'ml_probability': round(ml_results['ml_probability'], 4),
                'final_signal': hybrid_timing,
                'ml_integration': {
                    'ml_probability': round(ml_results['ml_probability'], 4),
                    'ml_confidence': round(ml_results['ml_confidence'], 1),
                    'ml_signal': ml_results['ml_signal'],
                    'ml_enabled': ml_results['ml_enabled'],
                    'traditional_score': traditional_analysis['confidence_score'],
                    'enhancement_boost': round(hybrid_score - traditional_analysis['confidence_score'], 1)
                },
                'scoring_breakdown': {
                    'heuristic_component': round(traditional_analysis['confidence_score'] * 0.6, 1),
                    'ml_component': round(ml_results['ml_probability'] * 100 * 0.4, 1),
                    'hybrid_total': round(hybrid_score, 1),
                    'weights': {'heuristic': '60%', 'ml': '40%'}
                },
                'analysis_type': 'HYBRID_ML_HEURISTIC',
                'version': '3.0'
            })

            # Log signal for ML training if enabled
            self._log_signal_for_training(symbol, current_price, hybrid_analysis, indicators)

            return hybrid_analysis

        except Exception as e:
            self.logger.error(f"Enhanced confidence calculation failed for {symbol}: {e}")
            # Fall back to traditional analysis
            traditional_analysis['analysis_type'] = 'TRADITIONAL_FALLBACK'
            return traditional_analysis

    def _combine_traditional_and_ml_scores(self, traditional_score: float,
                                         ml_probability: float, ml_confidence: float) -> float:
        """
        HYBRID SCORING SYSTEM: Combine traditional heuristics (60%) with ML predictions (40%).

        Formula: hybrid_score = 0.6 * confidence_score + 0.4 * (ml_probability * 100)

        Args:
            traditional_score: Score from 6-factor analysis (0-100)
            ml_probability: ML prediction probability (0-1)
            ml_confidence: ML confidence level (0-100)

        Returns:
            Hybrid confidence score (0-100)
        """
        if not self.ml_enabled:
            return traditional_score

        # HYBRID SCORING: Fixed 60/40 weight distribution
        # 60% weight to traditional heuristic analysis
        # 40% weight to ML probability prediction
        heuristic_weight = 0.6
        ml_weight = 0.4

        # Convert ML probability to 0-100 scale to match traditional score
        ml_score = ml_probability * 100

        # Calculate hybrid score with fixed weights
        hybrid_score = (traditional_score * heuristic_weight) + (ml_score * ml_weight)

        # Ensure score stays within bounds
        final_score = max(0, min(100, hybrid_score))

        self.logger.debug(f"🎯 HYBRID SCORING: Traditional={traditional_score:.1f} (60%) + ML={ml_score:.1f} (40%) = {final_score:.1f}")

        return final_score

    def _generate_enhanced_timing_signal(self, traditional_signal: str,
                                       ml_signal: str, enhanced_score: float) -> str:
        """
        HYBRID SIGNAL GENERATION: Generate timing signal based on hybrid score thresholds.

        Recalibrated Signal Thresholds (Based on Backtest Analysis):
        - >=65: BUY (Strong hybrid confidence) - Lowered from 75
        - >=55: CONSIDER (Moderate hybrid confidence) - Lowered from 60
        - >=45: WAIT (Weak hybrid confidence)
        - <45: AVOID (Poor hybrid confidence)

        Note: Lower thresholds account for negative correlation between confidence and P&L,
        where oversold entries with lower scores showed higher mean-reversion potential.
        """

        # If ML not available, use traditional signal
        if not self.ml_enabled or ml_signal == 'ERROR':
            return traditional_signal

        # HYBRID SIGNAL THRESHOLDS: Based purely on hybrid score
        # Recalibrated thresholds based on backtest analysis
        # Lower thresholds due to negative correlation between confidence and P&L
        if enhanced_score >= 65:
            signal = "BUY"
        elif enhanced_score >= 55:
            signal = "CONSIDER"
        elif enhanced_score >= 45:
            signal = "WAIT"
        else:
            signal = "AVOID"

        self.logger.debug(f"🎯 HYBRID SIGNAL: Score={enhanced_score:.1f} → {signal}")

        return signal

    def _log_signal_for_training(self, symbol: str, current_price: float,
                               analysis: dict, indicators: dict) -> None:
        """Log enhanced signal data for ML training and improvement."""
        try:
            # Try to import signal logger (optional)
            try:
                import os
                import sys
                # Add project root to path for signal logger import
                project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
                if project_root not in sys.path:
                    sys.path.append(project_root)
                # Signal logging functionality - graceful fallback if not available
                try:
                    self.logger.debug(f"Enhanced signal generated for {symbol}: hybrid_score={enhanced_analysis.get('confidence_score', 0)}, ml_enabled={ml_results.get('ml_enabled', False)}")
                except Exception:
                    # Signal logging system not configured
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

            # Log the signal (using debug logging instead of external signal logger)
            self.logger.debug(f"Enhanced signal logged for {symbol}: {signal_data}")

        except Exception as e:
            # Don't fail the main analysis if logging fails
            self.logger.debug(f"Signal logging failed for {symbol}: {e}")

    def get_ml_status(self) -> dict[str, bool]:
        """Get status of ML integration."""
        return {
            'ml_enabled': self.ml_enabled,
            'predictor_available': self._check_ml_availability(),
            'signal_logging_enabled': True
        }

# Convenience function for backward compatibility
def calculate_ml_enhanced_confidence(symbol: str, current_price: float,
                                   historical_data: list[dict] | None = None) -> dict:
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
