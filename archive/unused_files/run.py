\
import os, json, math, argparse, warnings, time
from dataclasses import dataclass
import numpy as np
import pandas as pd
import yaml
from typing import List, Optional, Tuple

warnings.filterwarnings("ignore")

def ensure_dir(p):
    os.makedirs(p, exist_ok=True)

def find_datetime_col(df: pd.DataFrame) -> Optional[str]:
    candidates = ["timestamp", "time", "date", "datetime"]
    for c in candidates:
        if c in df.columns:
            return c
    return None

def to_datetime_utc(s):
    return pd.to_datetime(s, utc=True)

def set_seed(seed: int = 1337):
    import random, numpy as np, os
    random.seed(seed)
    np.random.seed(seed)
    try:
        import tensorflow as tf
        tf.random.set_seed(seed)
        os.environ["TF_DETERMINISTIC_OPS"] = "1"
    except Exception:
        pass

def fetch_ohlcv_ccxt(exchange_id: str, symbol: str, timeframe: str,
                     since_days: int = 365, limit_per_call: int = 1000) -> pd.DataFrame:
    import ccxt
    ex = getattr(ccxt, exchange_id)({"enableRateLimit": True})
    ms_in_min = 60 * 1000
    tf_to_min = {
        "1m":1, "3m":3, "5m":5, "15m":15, "30m":30, "1h":60,
        "2h":120, "4h":240, "6h":360, "8h":480, "12h":720,
        "1d":1440, "3d":4320, "1w":10080
    }
    step_ms = tf_to_min.get(timeframe, 60) * ms_in_min
    since_ms = int((pd.Timestamp.utcnow() - pd.Timedelta(days=since_days)).timestamp() * 1000)

    all_rows = []
    last = since_ms
    while True:
        batch = ex.fetch_ohlcv(symbol, timeframe=timeframe, since=last, limit=limit_per_call)
        if not batch:
            break
        all_rows.extend(batch)
        last_batch_end = batch[-1][0]
        last = last_batch_end + step_ms
        if last > int(pd.Timestamp.utcnow().timestamp()*1000) - 2*step_ms:
            break
        time.sleep(ex.rateLimit/1000.0 if hasattr(ex, "rateLimit") else 0.3)

    if not all_rows:
        raise RuntimeError("No OHLCV received. Check symbol/timeframe/exchange or API limits.")

    df = pd.DataFrame(all_rows, columns=["timestamp","open","high","low","close","volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    df = df.set_index("timestamp").sort_index()
    return df

def load_onchain_csvs(paths: List[str]) -> pd.DataFrame:
    if not paths:
        return pd.DataFrame()
    frames = []
    for p in paths:
        t = pd.read_csv(p)
        dcol = find_datetime_col(t)
        if dcol is None:
            raise ValueError(f"No datetime column found in {p}. Expected one of timestamp/time/date/datetime")
        t[dcol] = to_datetime_utc(t[dcol])
        t = t.set_index(dcol).sort_index()
        frames.append(t)
    merged = pd.concat(frames, axis=1).sort_index()
    merged = merged.ffill()
    return merged

def add_ta_features(df: pd.DataFrame, bb_window=20, bb_std=2.0,
                    rsi_window=14, macd_fast=12, macd_slow=26, macd_signal=9) -> pd.DataFrame:
    out = df.copy()
    m = out["close"].rolling(bb_window, min_periods=bb_window).mean()
    s = out["close"].rolling(bb_window, min_periods=bb_window).std(ddof=0)
    out["bb_mid"] = m
    out["bb_up"] = m + bb_std * s
    out["bb_dn"] = m - bb_std * s
    out["bb_pctb"] = (out["close"] - out["bb_dn"]) / (out["bb_up"] - out["bb_dn"])
    out["bb_width"] = (out["bb_up"] - out["bb_dn"]) / out["bb_mid"]

    delta = out["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(rsi_window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(rsi_window).mean()
    rs = gain / (loss.replace(0, np.nan))
    out["rsi"] = 100 - (100 / (1 + rs))

    ema_fast = out["close"].ewm(span=macd_fast, adjust=False).mean()
    ema_slow = out["close"].ewm(span=macd_slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal = macd.ewm(span=macd_signal, adjust=False).mean()
    out["macd"] = macd
    out["macd_signal"] = signal
    out["macd_hist"] = macd - signal

    out["ret1"] = out["close"].pct_change()
    out["logret1"] = np.log(out["close"]).diff()

    return out

def add_regime_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    ema100 = out["close"].ewm(span=100, adjust=False).mean()
    slope = ema100.diff()
    out["ema100"] = ema100
    out["ema100_slope"] = slope
    out["regime"] = np.where(slope > 0, "up", np.where(slope < 0, "down", "chop"))
    return out

def bollinger_next_forecast(row) -> float:
    return float(row["bb_mid"]) if not math.isnan(row["bb_mid"]) else float(row["close"])

def make_sequences(X: np.ndarray, y: np.ndarray, lookback: int):
    xs, ys = [], []
    for i in range(lookback, len(X)):
        xs.append(X[i-lookback:i])
        ys.append(y[i])
    return np.array(xs), np.array(ys)

def build_lstm(input_shape, units=64, dropout=0.2, lr=1e-3):
    import tensorflow as tf
    from tensorflow.keras import layers, models, optimizers
    model = models.Sequential([
        layers.Input(shape=input_shape),
        layers.LSTM(units, return_sequences=False),
        layers.Dropout(dropout),
        layers.Dense(32, activation="relu"),
        layers.Dense(1)
    ])
    opt = optimizers.Adam(learning_rate=lr)
    model.compile(optimizer=opt, loss="mae")
    return model

def time_series_splits(n: int, test_size_ratio: float, n_splits: int):
    test_size = int(n * test_size_ratio)
    train_total = n - test_size
    fold_size = train_total // n_splits
    splits = []
    for i in range(1, n_splits+1):
        train_end = i * fold_size
        if train_end < 50:
            continue
        splits.append((0, train_end))
    test_slice = (train_total, n)
    return splits, test_slice

def directional_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    r_true = np.sign(np.diff(y_true, prepend=y_true[0]))
    r_pred = np.sign(np.diff(y_pred, prepend=y_pred[0]))
    return float((r_true == r_pred).mean())

def backtest_simple(prices: np.ndarray, forecast: np.ndarray, long_thr=0.002, short_thr=-0.002, fee=0.0005):
    ret = (prices[1:] - prices[:-1]) / prices[:-1]
    exp_ret = (forecast[1:] - prices[:-1]) / prices[:-1]
    pos = np.where(exp_ret > long_thr, 1, np.where(exp_ret < short_thr, -1, 0))
    strat = pos * ret - np.abs(np.diff(pos, prepend=0)) * fee
    sharpe = strat.mean() / (strat.std() + 1e-9) * np.sqrt(365*24)
    return {"avg_return": float(strat.mean()), "vol": float(strat.std()), "sharpe": float(sharpe), "cum_return": float((1+strat).prod() - 1)}

def run(cfg):
    set_seed(cfg.get("seed", 1337))

    df = fetch_ohlcv_ccxt(cfg["exchange"], cfg["symbol"], cfg["timeframe"],
                          cfg.get("since_days", 365), cfg.get("fetch_limit_per_call", 1000))

    onchain = load_onchain_csvs(cfg.get("onchain_csvs", []))
    if not onchain.empty:
        df = df.merge(onchain, left_index=True, right_index=True, how="left")
        df = df.ffill()

    df = add_ta_features(df,
        bb_window=cfg.get("bollinger_window",20),
        bb_std=cfg.get("bollinger_std",2.0),
        rsi_window=cfg.get("rsi_window",14),
        macd_fast=cfg.get("macd_fast",12),
        macd_slow=cfg.get("macd_slow",26),
        macd_signal=cfg.get("macd_signal",9),
    )

    df = add_regime_features(df)

    horizon = int(cfg.get("horizon",1))
    df["y"] = df["close"].shift(-horizon)
    df = df.dropna().copy()

    feature_cols = [c for c in df.columns if c not in ["y"]]
    X = df[feature_cols].values.astype(np.float32)
    y = df["y"].values.astype(np.float32)
    prices = df["close"].values.astype(np.float32)
    idx = df.index

    splits, test_slice = time_series_splits(len(df), cfg["walkforward"]["test_size_ratio"], cfg["walkforward"]["n_splits"])

    from sklearn.preprocessing import RobustScaler
    from sklearn.metrics import mean_absolute_error, mean_squared_error

    lcfg = cfg["lstm"]
    lookback = int(lcfg.get("lookback", 64))

    val_mae, val_rmse = [], []
    ensemble_weights = []

    oof_boll, oof_lstm, oof_ens = np.full(len(df), np.nan), np.full(len(df), np.nan), np.full(len(df), np.nan)

    for (start, train_end) in splits:
        trX, trY = X[start:train_end], y[start:train_end]

        val_len = int(len(trX) * cfg["walkforward"]["val_ratio"])
        if val_len < lookback + 10:
            continue
        vstart = train_end - val_len
        X_train, y_train = trX[:vstart-start], trY[:vstart-start]
        X_val, y_val = trX[vstart-start:], trY[vstart-start:]

        xs = RobustScaler()
        ys = RobustScaler()
        X_train_s = xs.fit_transform(X_train)
        y_train_s = ys.fit_transform(y_train.reshape(-1,1)).ravel()
        X_val_s = xs.transform(X_val)
        y_val_s = ys.transform(y_val.reshape(-1,1)).ravel()

        Xtr_seq, ytr_seq = (np.array([]), np.array([]))
        Xva_seq, yva_seq = (np.array([]), np.array([]))

        def make_sequences(Xm, ym, lb):
            xs, ys = [], []
            for i in range(lb, len(Xm)):
                xs.append(Xm[i-lb:i])
                ys.append(ym[i])
            return np.array(xs), np.array(ys)

        Xtr_seq, ytr_seq = make_sequences(X_train_s, y_train_s, lookback)
        Xva_seq, yva_seq = make_sequences(X_val_s, y_val_s, lookback)

        if len(Xtr_seq) < 50 or len(Xva_seq) < 10:
            continue

        import tensorflow as tf
        from tensorflow.keras.callbacks import EarlyStopping
        model = build_lstm(
            input_shape=(Xtr_seq.shape[1], Xtr_seq.shape[2]),
            units=lcfg.get("units",64), dropout=lcfg.get("dropout",0.2),
            lr=lcfg.get("learning_rate",1e-3)
        )
        es = EarlyStopping(monitor="val_loss", patience=lcfg.get("patience",5), restore_best_weights=True, verbose=0)
        model.fit(Xtr_seq, ytr_seq, validation_data=(Xva_seq, yva_seq),
                  epochs=lcfg.get("epochs",25), batch_size=lcfg.get("batch_size",64), verbose=0, callbacks=[es])

        offset = lookback
        val_pred_s = model.predict(Xva_seq, verbose=0).ravel()
        val_pred = ys.inverse_transform(val_pred_s.reshape(-1,1)).ravel()

        val_idx_range = slice(vstart + offset, train_end)
        bb_val = df.iloc[val_idx_range].apply(bollinger_next_forecast, axis=1).values
        lstm_val = val_pred.copy()

        best_w, best_mae = 0.5, 1e9
        from sklearn.metrics import mean_absolute_error
        for w in np.linspace(0,1,21):
            ens = w * lstm_val + (1-w) * bb_val
            mae = mean_absolute_error(df["y"].values[val_idx_range], ens)
            if mae < best_mae:
                best_mae, best_w = mae, w

        ensemble_weights.append(float(best_w))
        oof_boll[val_idx_range] = bb_val
        oof_lstm[val_idx_range] = lstm_val
        oof_ens[val_idx_range]  = best_w * lstm_val + (1-best_w) * bb_val
        val_mae.append(best_mae)
        val_rmse.append(mean_squared_error(df["y"].values[val_idx_range], oof_ens[val_idx_range], squared=False))

    test_start, test_end = test_slice
    X_train_full, y_train_full = X[:test_start], y[:test_start]
    from sklearn.preprocessing import RobustScaler
    xs = RobustScaler(); ys = RobustScaler()
    X_train_s = xs.fit_transform(X_train_full)
    y_train_s = ys.fit_transform(y_train_full.reshape(-1,1)).ravel()

    def make_sequences2(Xm, ym, lb):
        xs, ys = [], []
        for i in range(lb, len(Xm)):
            xs.append(Xm[i-lb:i])
            ys.append(ym[i])
        return np.array(xs), np.array(ys)

    Xtr_seq, ytr_seq = make_sequences2(X_train_s, y_train_s, lookback)

    import tensorflow as tf
    model = build_lstm(input_shape=(Xtr_seq.shape[1], Xtr_seq.shape[2]),
                       units=lcfg.get("units",64), dropout=lcfg.get("dropout",0.2),
                       lr=lcfg.get("learning_rate",1e-3))
    model.fit(Xtr_seq, ytr_seq, epochs=max(5, lcfg.get("epochs",25)//2),
              batch_size=lcfg.get("batch_size",64), verbose=0)

    X_test = X[test_start:test_end]
    y_test = y[test_start:test_end]
    prices_test = prices[test_start:test_end]

    X_test_s = xs.transform(X_test)
    def make_sequences3(Xm, ym, lb):
        xs, ys = [], []
        for i in range(lb, len(Xm)):
            xs.append(Xm[i-lb:i])
            ys.append(ym[i])
        return np.array(xs), np.array(ys)
    Xte_seq, _ = make_sequences3(X_test_s, y_test, lookback)
    y_test_aligned = y_test[lookback:]
    idx_test_aligned = idx[test_start+lookback:test_end]

    lstm_pred_s = model.predict(Xte_seq, verbose=0).ravel()
    lstm_pred = ys.inverse_transform(lstm_pred_s.reshape(-1,1)).ravel()

    bb_test = df.iloc[test_start+lookback:test_end].apply(bollinger_next_forecast, axis=1).values

    w = float(np.nanmedian(ensemble_weights)) if ensemble_weights else 0.5
    ens_test = w * lstm_pred + (1-w) * bb_test

    from sklearn.metrics import mean_absolute_error, mean_squared_error
    mae_b = mean_absolute_error(y_test_aligned, bb_test)
    mae_l = mean_absolute_error(y_test_aligned, lstm_pred)
    mae_e = mean_absolute_error(y_test_aligned, ens_test)
    rmse_b = mean_squared_error(y_test_aligned, bb_test, squared=False)
    rmse_l = mean_squared_error(y_test_aligned, lstm_pred, squared=False)
    rmse_e = mean_squared_error(y_test_aligned, ens_test, squared=False)
    mape_b = float(np.mean(np.abs((y_test_aligned - bb_test) / y_test_aligned)))
    mape_l = float(np.mean(np.abs((y_test_aligned - lstm_pred) / y_test_aligned)))
    mape_e = float(np.mean(np.abs((y_test_aligned - ens_test) / y_test_aligned)))

    da_b = directional_accuracy(y_test_aligned, bb_test)
    da_l = directional_accuracy(y_test_aligned, lstm_pred)
    da_e = directional_accuracy(y_test_aligned, ens_test)

    bt_b = backtest_simple(prices[test_start:test_end], np.concatenate([prices[test_start:test_start+lookback], bb_test]),
                           cfg["backtest"]["long_threshold"], cfg["backtest"]["short_threshold"], cfg["backtest"]["fee_rate"])
    bt_l = backtest_simple(prices[test_start:test_end], np.concatenate([prices[test_start:test_start+lookback], lstm_pred]),
                           cfg["backtest"]["long_threshold"], cfg["backtest"]["short_threshold"], cfg["backtest"]["fee_rate"])
    bt_e = backtest_simple(prices[test_start:test_end], np.concatenate([prices[test_start:test_start+lookback], ens_test]),
                           cfg["backtest"]["long_threshold"], cfg["backtest"]["short_threshold"], cfg["backtest"]["fee_rate"])

    # --- Probability mapping (sigmoid on z-scored expected return) ---
    prev_close = prices[test_start+lookback-1:test_end-1]
    exp_ret = (ens_test - prev_close) / prev_close
    ret_test_all = (prices[test_start:test_end][1:] - prices[test_start:test_end][:-1]) / prices[test_start:test_end][:-1]
    ret_test_all = np.insert(ret_test_all, 0, 0.0)
    sigma = pd.Series(ret_test_all, index=idx[test_start:test_end]).rolling(64).std().values[lookback:]
    z = exp_ret / (sigma + 1e-9)
    prob = 1.0 / (1.0 + np.exp(-5.0 * z))

    regime_test = df.iloc[test_start+lookback:test_end]["regime"].values
    bb_up_slice = df.iloc[test_start+lookback:test_end]["bb_up"].values
    bb_dn_slice = df.iloc[test_start+lookback:test_end]["bb_dn"].values
    prices_aligned = prices[test_start+lookback:test_end]
    index_aligned = idx[test_start+lookback:test_end]

    from strategy import compute_actions
    actions = compute_actions(
        index=index_aligned,
        prices=prices_aligned,
        bb_up=bb_up_slice,
        bb_dn=bb_dn_slice,
        prob=prob,
        regime=regime_test,
        fee=cfg["backtest"]["fee_rate"],
        long_thr=0.60,
        strong_thr=0.85,
        sigma_ret_lookback=64
    )

    metrics = {
        "val": {
            "folds": len(val_mae),
            "ensemble_weight_median": float(np.nanmedian(ensemble_weights)) if ensemble_weights else None,
            "mae_mean": float(np.mean(val_mae)) if val_mae else None,
            "rmse_mean": float(np.mean(val_rmse)) if val_rmse else None,
        },
        "test": {
            "Bollinger": {"MAE": float(mae_b), "RMSE": float(rmse_b), "MAPE": float(mape_b), "DirAcc": float(da_b), **bt_b},
            "LSTM":      {"MAE": float(mae_l), "RMSE": float(rmse_l), "MAPE": float(mape_l), "DirAcc": float(da_l), **bt_l},
            "Ensemble":  {"MAE": float(mae_e), "RMSE": float(rmse_e), "MAPE": float(mape_e), "DirAcc": float(da_e), **bt_e},
        }
    }

    outdir = os.path.join("artifacts", f"{cfg['symbol'].replace('/','_')}_{cfg['timeframe']}")
    ensure_dir(outdir)

    out_df = pd.DataFrame({
        "timestamp": idx_test_aligned.tz_convert("UTC"),
        "actual_close": y_test_aligned,
        "boll_forecast": bb_test,
        "lstm_forecast": lstm_pred,
        "ensemble_forecast": ens_test,
        "prob_up": prob
    }).set_index("timestamp")
    out_df.to_csv(os.path.join(outdir, "predictions.csv"))

    with open(os.path.join(outdir, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    with open(os.path.join(outdir, "actions.json"), "w") as f:
        json.dump(actions, f, indent=2)

    import matplotlib.pyplot as plt
    plt.figure(figsize=(12,5))
    plt.plot(idx_test_aligned, y_test_aligned, label="Actual")
    plt.plot(idx_test_aligned, bb_test, label="Bollinger forecast")
    plt.plot(idx_test_aligned, lstm_pred, label="LSTM forecast")
    plt.plot(idx_test_aligned, ens_test, label="Ensemble forecast")
    plt.legend()
    plt.title(f"{cfg['symbol']} {cfg['timeframe']} – Actual vs Forecasts")
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, "pred_vs_actual.png"))
    plt.close()

    print(json.dumps(metrics, indent=2))
    print(f"\nArtifacts written to: {outdir}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=str, default="config.yaml")
    args = ap.parse_args()
    with open(args.config, "r") as f:
        cfg = yaml.safe_load(f)
    run(cfg)

if __name__ == "__main__":
    main()
