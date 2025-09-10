# src/ml/predictor.py
from pathlib import Path

import joblib

_MODEL = None
_MODEL_PATH = Path("src/models/buy_regression_model.pkl")

def _load():
    global _MODEL
    if _MODEL is None and _MODEL_PATH.is_file():
        _MODEL = joblib.load(_MODEL_PATH)
    return _MODEL

def predict_buy_return(confidence_score: float, ml_probability: float) -> float:
    m = _load()
    if m is None:
        # graceful fallback, no crashes if model missing
        return 0.0
    import numpy as np
    X = np.array([[confidence_score, ml_probability]], dtype=float)
    return float(m.predict(X)[0])
