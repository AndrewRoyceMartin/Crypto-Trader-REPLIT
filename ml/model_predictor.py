# ml/model_predictor.py

import pandas as pd
import numpy as np
import joblib
from typing import Dict, List
from datetime import datetime

class CryptoSignalPredictor:
    def __init__(self, model_path: str = "ml/crypto_signal_model.pkl"):
        """Initialize predictor with trained model"""
        self.model_data = None
        self.model = None
        self.feature_columns = None
        self.load_model(model_path)
    
    def load_model(self, model_path: str):
        """Load the trained model and metadata"""
        try:
            self.model_data = joblib.load(model_path)
            self.model = self.model_data['model']
            self.feature_columns = self.model_data['feature_columns']
            
            print(f"✅ Model loaded from {model_path}")
            print(f"   Model type: {self.model_data.get('model_type', 'Unknown')}")
            print(f"   Trained on: {self.model_data.get('training_date', 'Unknown')}")
            print(f"   Features: {len(self.feature_columns)}")
            
        except FileNotFoundError:
            print(f"❌ Model file {model_path} not found. Train a model first.")
        except Exception as e:
            print(f"❌ Error loading model: {e}")
    
    def prepare_signal_features(self, signal_data: Dict) -> np.ndarray:
        """
        Convert signal data to feature vector for prediction.
        
        Expected signal_data format:
        {
            'confidence_score': 75.0,
            'rsi': 29.4,
            'volatility': 8.3,
            'volume_ratio': True,
            'momentum_signal': True, 
            'support_signal': False,
            'bollinger_signal': True,
            'current_price': 1650.22
        }
        """
        if self.model is None:
            raise ValueError("Model not loaded")
        
        # Create base features
        features = {
            'current_price': signal_data['current_price'],
            'confidence_score': signal_data['confidence_score'],
            'rsi': signal_data['rsi'],
            'volatility': signal_data['volatility'],
            'volume_ratio': signal_data['volume_ratio'],
            'momentum_signal': signal_data['momentum_signal'],
            'support_signal': signal_data['support_signal'],
            'bollinger_signal': signal_data['bollinger_signal']
        }
        
        # Engineer additional features (same as in prepare_dataset.py)
        features['confidence_x_rsi'] = features['confidence_score'] * features['rsi']
        features['volatility_normalized'] = features['volatility'] / 10.0  # Approximate normalization
        
        # Boolean feature encoding
        features['volume_signal_int'] = int(features['volume_ratio'])
        features['momentum_signal_int'] = int(features['momentum_signal'])
        features['support_signal_int'] = int(features['support_signal'])
        features['bollinger_signal_int'] = int(features['bollinger_signal'])
        
        # Technical signal strength
        features['signal_strength'] = (
            features['volume_signal_int'] + 
            features['momentum_signal_int'] + 
            features['support_signal_int'] + 
            features['bollinger_signal_int']
        )
        
        # RSI zones
        features['rsi_oversold'] = int(features['rsi'] < 30)
        features['rsi_overbought'] = int(features['rsi'] > 70)
        features['rsi_neutral'] = int(30 <= features['rsi'] <= 70)
        
        # Create feature vector in correct order
        feature_vector = []
        for col in self.feature_columns:
            if col in features:
                feature_vector.append(features[col])
            else:
                print(f"⚠️ Missing feature: {col}, using default value 0")
                feature_vector.append(0)
        
        return np.array(feature_vector).reshape(1, -1)
    
    def predict_signal_profitability(self, signal_data: Dict) -> Dict:
        """
        Predict if a trading signal will be profitable.
        
        Returns:
        {
            'is_profitable_prediction': 1 or 0,
            'profit_probability': 0.75,
            'confidence_level': 'HIGH',
            'recommendation': 'STRONG BUY'
        }
        """
        if self.model is None:
            return {'error': 'Model not loaded'}
        
        try:
            # Prepare features
            X = self.prepare_signal_features(signal_data)
            
            # Make prediction
            prediction = self.model.predict(X)[0]
            probability = self.model.predict_proba(X)[0, 1]  # Probability of class 1 (profitable)
            
            # Determine confidence level
            if probability >= 0.8:
                confidence_level = "VERY HIGH"
                recommendation = "STRONG BUY"
            elif probability >= 0.7:
                confidence_level = "HIGH"
                recommendation = "BUY"
            elif probability >= 0.6:
                confidence_level = "MODERATE"
                recommendation = "CONSIDER BUY"
            elif probability >= 0.4:
                confidence_level = "LOW"
                recommendation = "NEUTRAL"
            else:
                confidence_level = "VERY LOW"
                recommendation = "AVOID"
            
            return {
                'symbol': signal_data.get('symbol', 'Unknown'),
                'is_profitable_prediction': int(prediction),
                'profit_probability': probability,
                'confidence_level': confidence_level,
                'recommendation': recommendation,
                'ml_score': probability * 100,  # 0-100 scale
                'prediction_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'error': f'Prediction failed: {e}'}
    
    def bulk_predict(self, signals_list: List[Dict]) -> List[Dict]:
        """Predict profitability for multiple signals"""
        predictions = []
        
        for signal_data in signals_list:
            prediction = self.predict_signal_profitability(signal_data)
            predictions.append(prediction)
        
        return predictions
    
    def get_model_info(self) -> Dict:
        """Get information about the loaded model"""
        if self.model_data is None:
            return {'error': 'No model loaded'}
        
        return {
            'model_type': self.model_data.get('model_type', 'Unknown'),
            'training_date': self.model_data.get('training_date', 'Unknown'),
            'feature_count': len(self.feature_columns),
            'feature_list': self.feature_columns
        }

# Example usage
if __name__ == "__main__":
    predictor = CryptoSignalPredictor()
    
    # Test prediction with sample signal
    test_signal = {
        'symbol': 'ETH',
        'current_price': 1650.22,
        'confidence_score': 78.5,
        'rsi': 29.4,
        'volatility': 8.3,
        'volume_ratio': True,
        'momentum_signal': True,
        'support_signal': False,
        'bollinger_signal': True
    }
    
    result = predictor.predict_signal_profitability(test_signal)
    
    if 'error' not in result:
        print("🔮 ML Prediction Results:")
        print(f"   Symbol: {result['symbol']}")
        print(f"   Profitable: {'Yes' if result['is_profitable_prediction'] else 'No'}")
        print(f"   Probability: {result['profit_probability']:.1%}")
        print(f"   Confidence: {result['confidence_level']}")
        print(f"   Recommendation: {result['recommendation']}")
        print(f"   ML Score: {result['ml_score']:.1f}/100")
    else:
        print(f"❌ Prediction error: {result['error']}")