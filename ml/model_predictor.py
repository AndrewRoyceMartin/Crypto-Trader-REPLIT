# ml/model_predictor.py

import os
import joblib
import numpy as np

# Use absolute path for model file
MODEL_PATH = os.path.join(os.path.dirname(__file__), "buy_signal_model.pkl")
try:
    model = joblib.load(MODEL_PATH)
    print(f"✅ Model loaded from {MODEL_PATH}")
except (FileNotFoundError, Exception) as e:
    print(f"❌ Model file {MODEL_PATH} not found or invalid: {e}")
    model = None

def predict_buy_opportunity(indicator_data: dict) -> float:
    """
    Takes indicator dict and returns P&L percentage prediction converted to probability scale.
    Now uses regression model to predict actual P&L% instead of binary classification.
    """
    # Check if model is loaded
    if model is None:
        print("⚠️ ML model not loaded, returning neutral probability")
        return 0.5  # Neutral probability when model unavailable
    
    try:
        features = ["rsi", "volatility", "confidence_score", "volume_ratio"]
        X = np.array([[indicator_data.get(f, 0) for f in features]])
        # Use regression prediction instead of classification probability
        pnl_prediction = model.predict(X)[0]  # Predicted P&L percentage
        
        # Convert P&L percentage to probability-like score for hybrid system
        # Positive P&L gets higher probability, negative gets lower
        # Scale: 0% P&L = 0.5 probability, +10% P&L = ~1.0, -10% P&L = ~0.0
        prob = max(0.0, min(1.0, 0.5 + (pnl_prediction / 20)))  # Scale to 0-1 range
        
        print(f"🎯 ML Regression: Predicted P&L={pnl_prediction:+.2f}% → Probability={prob:.3f}")
        return round(prob, 4)
    except Exception as e:
        print(f"❌ ML prediction error: {e}")
        return 0.5  # Fallback to neutral probability