#!/usr/bin/env python3
"""
Hybrid Signal System - Combines ML + Heuristics for Trading Decisions

Goal 1: ✅ Hybrid Scoring System (ML + Heuristic)
Goal 2: 🔄 Auto-Backtest on Real OKX Trade History (Next Phase)

Scoring Strategy:
- heuristic_score: 60% weight (Your current confidence_score)  
- ml_probability: 40% weight (Output from ML model: predict_buy_opportunity())

Final Decision Logic:
- hybrid_score >= 75: BUY (Strong confidence)
- hybrid_score >= 60: CONSIDER (Moderate confidence)
- hybrid_score >= 45: WAIT (Weak confidence)
- hybrid_score < 45: AVOID (Poor confidence)
"""

import os
import sys
import logging
from typing import Dict, Any

# Add project root to path for ML import
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

logger = logging.getLogger(__name__)

def calculate_hybrid_signal(confidence_score: float, indicators: Dict[str, Any]) -> Dict[str, Any]:
    """
    HYBRID SIGNAL SYSTEM: Combine heuristic analysis (60%) with ML predictions (40%).
    
    Formula: hybrid_score = 0.6 * confidence_score + 0.4 * (ml_probability * 100)
    
    Args:
        confidence_score: Traditional 6-factor confidence score (0-100)
        indicators: Technical indicators dict for ML prediction
        
    Returns:
        Dict with hybrid score, ML probability, and final signal
    """
    try:
        # Try to get ML prediction
        ml_prob = _get_ml_prediction(indicators)
        
        # HYBRID SCORING: Fixed 60/40 weight distribution
        heuristic_weight = 0.6
        ml_weight = 0.4
        
        # Calculate hybrid score
        hybrid_score = (confidence_score * heuristic_weight) + (ml_prob * 100 * ml_weight)
        
        # Generate final signal based on hybrid score thresholds
        if hybrid_score >= 75:
            signal = "BUY"
        elif hybrid_score >= 60:
            signal = "CONSIDER"
        elif hybrid_score >= 45:
            signal = "WAIT"
        else:
            signal = "AVOID"
        
        # Calculate component breakdown
        heuristic_component = confidence_score * heuristic_weight
        ml_component = ml_prob * 100 * ml_weight
        
        result = {
            "hybrid_score": round(hybrid_score, 2),
            "ml_probability": round(ml_prob, 4),
            "final_signal": signal,
            "breakdown": {
                "heuristic_component": round(heuristic_component, 1),
                "ml_component": round(ml_component, 1),
                "weights": {"heuristic": "60%", "ml": "40%"}
            },
            "thresholds": {
                "BUY": "≥75",
                "CONSIDER": "≥60", 
                "WAIT": "≥45",
                "AVOID": "<45"
            }
        }
        
        logger.debug(f"🎯 HYBRID SIGNAL: {confidence_score:.1f} (60%) + {ml_prob*100:.1f} (40%) = {hybrid_score:.1f} → {signal}")
        
        return result
        
    except Exception as e:
        logger.error(f"Hybrid signal calculation failed: {e}")
        # Fallback to heuristic-only
        return {
            "hybrid_score": round(confidence_score, 2),
            "ml_probability": 0.5,  # Neutral
            "final_signal": _heuristic_only_signal(confidence_score),
            "breakdown": {
                "heuristic_component": round(confidence_score, 1),
                "ml_component": 0.0,
                "weights": {"heuristic": "100%", "ml": "0% (unavailable)"}
            },
            "error": str(e)
        }

def _get_ml_prediction(indicators: Dict[str, Any]) -> float:
    """Get ML prediction probability for the given indicators."""
    try:
        from ml.model_predictor import predict_buy_opportunity
        
        # Prepare ML features from indicators
        ml_features = {
            'rsi': indicators.get('rsi_14', indicators.get('rsi', 50.0)),
            'volatility': indicators.get('volatility_7', indicators.get('volatility', 10.0)), 
            'confidence_score': indicators.get('composite_confidence', indicators.get('confidence_score', 50.0)),
            'volume_ratio': 1 if indicators.get('volume_ratio', 1.0) > 1.2 else 0
        }
        
        # Get ML prediction
        probability = predict_buy_opportunity(ml_features)
        return probability
        
    except Exception as e:
        logger.debug(f"ML prediction unavailable: {e}")
        return 0.5  # Neutral prediction when ML unavailable

def _heuristic_only_signal(confidence_score: float) -> str:
    """Generate signal based on heuristic score only when ML unavailable."""
    if confidence_score >= 80:
        return "BUY"
    elif confidence_score >= 65:
        return "CONSIDER"
    elif confidence_score >= 45:
        return "WAIT"
    else:
        return "AVOID"

def test_hybrid_system():
    """Test the hybrid signal system with sample data."""
    print("🧪 Testing Hybrid Signal System")
    print("=" * 50)
    
    # Test cases with different scenarios
    test_cases = [
        {
            "name": "Strong Heuristic + Strong ML",
            "confidence": 85.0,
            "indicators": {"rsi": 25, "volatility": 15, "volume_ratio": 1.5}
        },
        {
            "name": "Moderate Heuristic + Weak ML", 
            "confidence": 70.0,
            "indicators": {"rsi": 45, "volatility": 8, "volume_ratio": 0.9}
        },
        {
            "name": "Weak Heuristic + Strong ML",
            "confidence": 45.0,
            "indicators": {"rsi": 20, "volatility": 20, "volume_ratio": 2.0}
        },
        {
            "name": "Poor All Around",
            "confidence": 30.0,
            "indicators": {"rsi": 70, "volatility": 5, "volume_ratio": 0.5}
        }
    ]
    
    for test in test_cases:
        print(f"\n📊 {test['name']}")
        result = calculate_hybrid_signal(test['confidence'], test['indicators'])
        
        print(f"   Heuristic: {test['confidence']:.1f}")
        print(f"   ML Prob: {result['ml_probability']:.3f}")
        print(f"   Hybrid Score: {result['hybrid_score']:.1f}")
        print(f"   Signal: {result['final_signal']}")
        print(f"   Breakdown: {result['breakdown']['heuristic_component']:.1f} + {result['breakdown']['ml_component']:.1f}")

if __name__ == "__main__":
    test_hybrid_system()