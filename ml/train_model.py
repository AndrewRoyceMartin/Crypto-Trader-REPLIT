# ml/train_model.py

import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
from prepare_dataset import load_signal_data, label_profitability

def train_model():
    df = load_signal_data("../signals_log.csv")
    
    # For small datasets, use horizon=1 to get more samples
    df = label_profitability(df, horizon=1)
    
    print(f"📊 Dataset size after labeling: {len(df)} samples")
    
    if len(df) == 0:
        print("❌ No data available for training")
        return
    
    features = ["rsi", "volatility", "confidence_score"]
    if "volume_ratio" in df.columns:
        # Convert boolean to numeric
        df["volume_ratio"] = df["volume_ratio"].astype(int)
        features.append("volume_ratio")

    X = df[features]
    y = df["profitable"]
    
    print(f"📊 Features: {features}")
    print(f"📊 Target distribution: {y.value_counts().to_dict()}")

    # For very small datasets, skip train/test split and use all data
    if len(df) < 4:
        print("⚠️ Small dataset - using all data for training")
        X_train, y_train = X, y
        X_test, y_test = X, y  # Use same data for testing (demo purposes)
    else:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = xgb.XGBClassifier(
        use_label_encoder=False, 
        eval_metric="logloss",
        max_depth=2,  # Reduce complexity for small data
        n_estimators=10
    )
    
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    print(f"🎯 Training accuracy: {(preds == y_test).mean():.1%}")
    
    if len(set(y_test)) > 1:  # Only if we have both classes
        print(classification_report(y_test, preds, zero_division=0))

    joblib.dump(model, "buy_signal_model.pkl")
    print("✅ Model saved: buy_signal_model.pkl")

if __name__ == "__main__":
    train_model()