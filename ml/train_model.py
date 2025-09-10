# ml/train_model.py

import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
from prepare_dataset import load_signal_data, label_profitability

def train_model():
    df = load_signal_data()
    df = label_profitability(df)

    features = ["rsi", "volatility", "confidence_score"]
    if "volume_ratio" in df.columns:
        features.append("volume_ratio")

    X = df[features]
    y = df["profitable"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = xgb.XGBClassifier(use_label_encoder=False, eval_metric="logloss")
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    print(classification_report(y_test, preds))

    joblib.dump(model, "buy_signal_model.pkl")
    print("✅ Model saved: buy_signal_model.pkl")

if __name__ == "__main__":
    train_model()