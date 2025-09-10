# src/ml/train_regression.py
"""
Trains a regression model to predict buy signal returns based on confidence score and ML probability.
Saves the trained model to src/models/buy_regression_model.pkl
"""

import os
import sys
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
from pathlib import Path

def load_training_data():
    """Load training data from signals_log.csv if available."""
    data_path = "signals_log.csv"
    
    if not os.path.exists(data_path):
        print(f"Warning: {data_path} not found, generating synthetic training data")
        return generate_synthetic_data()
    
    try:
        df = pd.read_csv(data_path)
        print(f"Loaded {len(df)} records from {data_path}")
        
        # Extract features and target
        required_cols = ['confidence_score', 'ml_probability']
        if not all(col in df.columns for col in required_cols):
            print("Warning: Required columns missing, generating synthetic data")
            return generate_synthetic_data()
            
        # Use confidence score and ml_probability as features
        X = df[required_cols].fillna(0)
        
        # Generate synthetic returns based on confidence (for training purposes)
        # In real implementation, this would be actual historical returns
        y = (X['confidence_score'] / 100 * 0.05 + 
             X['ml_probability'] * 0.03 + 
             np.random.normal(0, 0.01, len(X)))
        
        return X, y
        
    except Exception as e:
        print(f"Error loading data: {e}, generating synthetic data")
        return generate_synthetic_data()

def generate_synthetic_data(n_samples=1000):
    """Generate synthetic training data for model development."""
    print(f"Generating {n_samples} synthetic training samples")
    
    # Generate realistic confidence scores and ML probabilities
    confidence_scores = np.random.beta(2, 3, n_samples) * 100  # Skewed toward lower values
    ml_probabilities = np.random.beta(2, 2, n_samples)  # More uniform
    
    # Generate correlated returns (higher confidence/probability = higher returns on average)
    returns = (confidence_scores / 100 * 0.04 + 
               ml_probabilities * 0.03 + 
               np.random.normal(0, 0.015, n_samples))
    
    X = pd.DataFrame({
        'confidence_score': confidence_scores,
        'ml_probability': ml_probabilities
    })
    
    return X, returns

def train_model():
    """Train the regression model and save it."""
    print("🤖 Training buy return prediction model...")
    
    # Load training data
    X, y = load_training_data()
    
    print(f"Training data shape: {X.shape}")
    print(f"Feature columns: {list(X.columns)}")
    print(f"Target range: {y.min():.4f} to {y.max():.4f}")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Train model
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"Model performance:")
    print(f"  MSE: {mse:.6f}")
    print(f"  R²: {r2:.4f}")
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(f"Feature importance:")
    for _, row in feature_importance.iterrows():
        print(f"  {row['feature']}: {row['importance']:.4f}")
    
    # Save model
    model_dir = Path("src/models")
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "buy_regression_model.pkl"
    
    joblib.dump(model, model_path)
    print(f"✅ Model saved to {model_path}")
    
    return model

if __name__ == "__main__":
    try:
        model = train_model()
        print("🎯 Training completed successfully!")
    except Exception as e:
        print(f"❌ Training failed: {e}")
        sys.exit(1)