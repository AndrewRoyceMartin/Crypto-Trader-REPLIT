import numpy as np
import pandas as pd
from typing import Dict

def calculate_buy_confidence(df: pd.DataFrame, current_price: float) -> Dict:
    """
    Enhanced buy prediction model using 6-factor technical analysis:
    RSI(14), Bollinger Bands, Volume Surge, Momentum, Volatility, Support Proximity
    """
    def rsi(prices, period=14):
        delta = np.diff(prices)
        gain = np.maximum(delta, 0)
        loss = -np.minimum(delta, 0)
        avg_gain = np.mean(gain[-period:])
        avg_loss = np.mean(loss[-period:])
        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    prices = df['price'].values
    volumes = df['volume'].values

    signals = {}
    score = 0

    # RSI
    if len(prices) >= 14:
        rsi_val = rsi(prices)
        signals['rsi'] = rsi_val
        if rsi_val < 35:
            score += 15
            signals['rsi_signal'] = True
        else:
            signals['rsi_signal'] = False

    # Bollinger Bands
    if len(prices) >= 20:
        sma = np.mean(prices[-20:])
        std = np.std(prices[-20:])
        lower_band = sma - 2 * std
        if current_price <= lower_band * 1.02:
            score += 15
            signals['bollinger_signal'] = True
        else:
            signals['bollinger_signal'] = False

    # Volume surge
    if len(volumes) >= 7:
        avg_vol = np.mean(volumes[-7:])
        current_vol = volumes[-1]
        if current_vol > avg_vol * 1.5:
            score += 15
            signals['volume_signal'] = True
        else:
            signals['volume_signal'] = False

    # Momentum
    if len(prices) >= 7:
        short_avg = np.mean(prices[-3:])
        long_avg = np.mean(prices[-7:])
        if short_avg > long_avg:
            score += 10
            signals['momentum_signal'] = True
        else:
            signals['momentum_signal'] = False

    # Volatility
    if len(prices) >= 10:
        returns = np.diff(np.log(prices))
        vol = np.std(returns) * 100
        signals['volatility'] = vol
        if vol < 10:
            score += 10
            signals['volatility_signal'] = True
        else:
            signals['volatility_signal'] = False

    # Support Proximity
    lows = df['low'].values[-20:] if 'low' in df.columns else prices[-20:]
    support = np.min(lows)
    if abs(current_price - support) / support < 0.02:
        score += 10
        signals['support_signal'] = True
    else:
        signals['support_signal'] = False

    # Final Mapping
    if score >= 70:
        signal = "BUY"
    elif score >= 60:
        signal = "CONSIDER"
    elif score >= 45:
        signal = "WAIT"
    else:
        signal = "AVOID"

    return {
        "confidence_score": round(score, 1),
        "timing_signal": signal,
        "indicators": signals
    }