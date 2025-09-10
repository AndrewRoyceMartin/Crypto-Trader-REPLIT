# main.py

from ml.model_predictor import predict_buy_return

input_features = {
    "confidence_score": 68,
    "ml_probability": 0.72
}

predicted_return = predict_buy_return(input_features)
print(f"📈 Predicted % P&L: {predicted_return}%")