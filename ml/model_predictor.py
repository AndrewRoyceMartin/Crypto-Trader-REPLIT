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
    Takes indicator dict and returns probability of profitable trade
    """
    # Check if model is loaded
    if model is None:
        print("⚠️ ML model not loaded, returning neutral probability")
        return 0.5  # Neutral probability when model unavailable
    
    try:
        features = ["rsi", "volatility", "confidence_score", "volume_ratio"]
        X = np.array([[indicator_data.get(f, 0) for f in features]])
        prob = model.predict_proba(X)[0][1]  # class 1 = profitable
        return round(prob, 4)
    except Exception as e:
        print(f"❌ ML prediction error: {e}")
        return 0.5  # Fallback to neutral probability