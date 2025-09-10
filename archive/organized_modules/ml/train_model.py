# ml/train_model.py

import joblib
import numpy as np
import xgboost as xgb
from prepare_dataset import label_profitability, load_signal_data
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split


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
    y = df["pnl_pct"]  # Switch to continuous P&L percentage target

    print(f"📊 Features: {features}")
    print(f"📊 Target P&L% stats: Mean={y.mean():.2f}%, Std={y.std():.2f}%, Min={y.min():.2f}%, Max={y.max():.2f}%")
    print(f"📊 Positive P&L samples: {(y > 0).sum()}/{len(y)} ({(y > 0).mean():.1%})")

    # For very small datasets, skip train/test split and use all data
    if len(df) < 4:
        print("⚠️ Small dataset - using all data for training")
        X_train, y_train = X, y
        X_test, y_test = X, y  # Use same data for testing (demo purposes)
    else:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = xgb.XGBRegressor(
        objective='reg:squarederror',
        eval_metric="rmse",
        max_depth=3,  # Slightly deeper for regression
        n_estimators=20,  # More trees for better regression performance
        learning_rate=0.1
    )

    model.fit(X_train, y_train)

    preds = model.predict(X_test)

    # Regression evaluation metrics
    mae = mean_absolute_error(y_test, preds)
    mse = mean_squared_error(y_test, preds)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, preds)

    print("🎯 Regression Performance:")
    print(f"   MAE (Mean Absolute Error): {mae:.2f}%")
    print(f"   RMSE (Root Mean Squared Error): {rmse:.2f}%")
    print(f"   R² Score: {r2:.3f}")

    # Show prediction vs actual comparison
    print("📈 Sample Predictions vs Actual:")
    for i in range(min(5, len(y_test))):
        if hasattr(y_test, 'iloc'):
            actual = y_test.iloc[i]
        else:
            actual = list(y_test)[i] if hasattr(y_test, '__iter__') else y_test[i]
        predicted = preds[i]
        print(f"   Actual: {actual:+.2f}% | Predicted: {predicted:+.2f}% | Diff: {abs(actual-predicted):.2f}%")

    joblib.dump(model, "buy_signal_model.pkl")
    print("✅ Model saved: buy_signal_model.pkl")

if __name__ == "__main__":
    train_model()
