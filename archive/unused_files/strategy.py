\
import numpy as np
import pandas as pd

def rolling_sigma(returns: np.ndarray, lookback: int = 64) -> np.ndarray:
    s = pd.Series(returns).rolling(lookback).std().bfill().values
    s[s == 0] = np.nan
    s = pd.Series(s).fillna(method="bfill").fillna(method="ffill").fillna(1e-6).values
    return s

def ladder_levels(anchor_price: float, sigma_price: float, levels=(-1.5, -2.0, -2.5)):
    return [anchor_price * (1 + z * sigma_price) for z in levels]

def compute_actions(index, prices, bb_up, bb_dn, prob, regime,
                    fee=0.0005, long_thr=0.60, strong_thr=0.85,
                    sigma_ret_lookback=64):
    actions = []
    pos = 0
    anchor = None

    ret = (prices[1:] - prices[:-1]) / prices[:-1]
    ret = np.insert(ret, 0, 0.0)
    sigma_ret = rolling_sigma(ret, lookback=sigma_ret_lookback)
    sigma_price = sigma_ret * prices

    rolling_high = np.maximum.accumulate(prices)
    crash_k = 1.5  # ~1.5 sigma drawdown from local max

    for i in range(2, len(prices)):
        p = prices[i]
        reg = regime[i]
        pr = prob[i]

        touch_lower = p <= bb_dn[i]
        band_width = (bb_up[i] - bb_dn[i]) + 1e-9
        pctb = (p - bb_dn[i]) / band_width
        deep_z = pctb < -0.15  # ≈ -1.5σ

        if pos == 0:
            if reg != "down" and (touch_lower or deep_z) and pr >= long_thr:
                pos = 1
                anchor = p
                size_hint = min(0.001 / (sigma_ret[i] + 1e-6), 1.0)
                actions.append({"timestamp": str(index[i]), "action": "BUY", "size_hint": float(size_hint)})
                continue
            if reg == "down" and deep_z and pr >= max(long_thr, 0.70):
                pos = 1
                anchor = p
                size_hint = 0.5 * min(0.001 / (sigma_ret[i] + 1e-6), 1.0)
                actions.append({"timestamp": str(index[i]), "action": "BUY", "size_hint": float(size_hint)})
                continue

        if pos == 1 and anchor is not None:
            lvls = ladder_levels(anchor, sigma_price[i], (-1.5, -2.0, -2.5))
            if p <= lvls[0] and pr >= 0.60:
                actions.append({"timestamp": str(index[i]), "action": "REBUY1", "size_hint": 0.5})
                anchor = (anchor + p) / 2
            elif p <= lvls[1] and pr >= 0.70:
                actions.append({"timestamp": str(index[i]), "action": "REBUY2", "size_hint": 0.5})
                anchor = (anchor + p) / 2
            elif p <= lvls[2] and pr >= 0.80:
                actions.append({"timestamp": str(index[i]), "action": "REBUY3", "size_hint": 0.5})
                anchor = (anchor + p) / 2

        upper_touch = p >= bb_up[i]
        crash_exit = p < (rolling_high[i] - crash_k * sigma_price[i])
        if pos == 1 and ((upper_touch and pr < 0.55) or pr < 0.45 or crash_exit):
            pos = 0
            actions.append({"timestamp": str(index[i]), "action": "SELL", "size_hint": 1.0})
            anchor = None

    return actions
