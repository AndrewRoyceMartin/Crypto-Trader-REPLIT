# ml/model_predictor.py

import joblib
import numpy as np

model = joblib.load("buy_regression_model.pkl")

def predict_buy_return(indicators: dict) -> float:
    X = np.array([[indicators.get("confidence_score", 0), indicators.get("ml_probability", 0)]])
    return round(float(model.predict(X)[0]), 3)