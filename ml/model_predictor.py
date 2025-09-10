# ml/model_predictor.py

import joblib
import numpy as np

MODEL_PATH = "buy_signal_model.pkl"
model = joblib.load(MODEL_PATH)

def predict_buy_opportunity(indicator_data: dict) -> float:
    """
    Takes indicator dict and returns probability of profitable trade
    """
    features = ["rsi", "volatility", "confidence_score", "volume_ratio"]
    X = np.array([[indicator_data.get(f, 0) for f in features]])
    prob = model.predict_proba(X)[0][1]  # class 1 = profitable
    return round(prob, 4)