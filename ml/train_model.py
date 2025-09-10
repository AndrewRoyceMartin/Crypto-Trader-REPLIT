# ml/train_model.py

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import xgboost as xgb
import joblib
from datetime import datetime

class CryptoSignalTrainer:
    def __init__(self):
        self.model = None
        self.feature_columns = None
        
    def load_dataset(self, dataset_path: str = "ml/training_dataset.csv") -> pd.DataFrame:
        """Load the prepared ML dataset"""
        try:
            df = pd.read_csv(dataset_path)
            print(f"✅ Loaded training dataset: {len(df)} samples")
            return df
        except FileNotFoundError:
            print(f"❌ Dataset file {dataset_path} not found. Run prepare_dataset.py first.")
            return pd.DataFrame()
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare features and target for ML training.
        """
        # Define feature columns (exclude metadata and target)
        exclude_cols = ['signal_id', 'timestamp', 'symbol', 'future_price', 'is_profitable', 'hours_ahead']
        self.feature_columns = [col for col in df.columns if col not in exclude_cols]
        
        print(f"🔧 Selected features: {self.feature_columns}")
        
        # Prepare X (features) and y (target)
        X = df[self.feature_columns].values
        y = df['is_profitable'].values
        
        print(f"📊 Feature matrix shape: {X.shape}")
        print(f"📊 Target distribution: {np.bincount(y)}")
        
        return X, y
    
    def train_model(self, X: np.ndarray, y: np.ndarray) -> Dict:
        """
        Train XGBoost model with optimal parameters.
        """
        print("🚀 Training XGBoost model...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"   Training samples: {len(X_train)}")
        print(f"   Test samples: {len(X_test)}")
        
        # Configure XGBoost parameters
        self.model = xgb.XGBClassifier(
            objective='binary:logistic',
            eval_metric='auc',
            max_depth=6,
            learning_rate=0.1,
            n_estimators=100,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbosity=1
        )
        
        # Train model
        self.model.fit(X_train, y_train)
        
        # Make predictions
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        
        # Calculate metrics
        auc_score = roc_auc_score(y_test, y_pred_proba)
        
        print("✅ Training complete!")
        print(f"🎯 ROC AUC Score: {auc_score:.3f}")
        
        # Detailed classification report
        print("\n📊 Classification Report:")
        print(classification_report(y_test, y_pred))
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\n🔥 Top 10 Most Important Features:")
        for idx, row in feature_importance.head(10).iterrows():
            print(f"   {row['feature']}: {row['importance']:.3f}")
        
        # Cross-validation
        cv_scores = cross_val_score(self.model, X, y, cv=5, scoring='roc_auc')
        print(f"\n🎯 Cross-validation AUC: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
        
        return {
            'auc_score': auc_score,
            'cv_scores': cv_scores,
            'feature_importance': feature_importance,
            'test_accuracy': (y_pred == y_test).mean()
        }
    
    def save_model(self, model_path: str = "ml/crypto_signal_model.pkl"):
        """Save the trained model and feature columns"""
        if self.model is None:
            print("❌ No model to save. Train a model first.")
            return
        
        model_data = {
            'model': self.model,
            'feature_columns': self.feature_columns,
            'training_date': datetime.now().isoformat(),
            'model_type': 'XGBoost_Binary_Classifier'
        }
        
        joblib.dump(model_data, model_path)
        print(f"✅ Model saved to {model_path}")
    
    def full_training_pipeline(self, dataset_path: str = "ml/training_dataset.csv") -> Dict:
        """
        Complete training pipeline: load → prepare → train → save
        """
        print("🚀 Starting full ML training pipeline...")
        
        # Load dataset
        df = self.load_dataset(dataset_path)
        if df.empty:
            return {}
        
        # Prepare features
        X, y = self.prepare_features(df)
        
        # Train model
        results = self.train_model(X, y)
        
        # Save model
        self.save_model()
        
        print("🎉 Training pipeline complete!")
        return results

if __name__ == "__main__":
    trainer = CryptoSignalTrainer()
    results = trainer.full_training_pipeline()
    
    if results:
        print(f"\n🎯 Final Model Performance:")
        print(f"   ROC AUC: {results['auc_score']:.3f}")
        print(f"   Test Accuracy: {results['test_accuracy']:.3f}")
        print(f"   CV AUC: {results['cv_scores'].mean():.3f}")