# Crypto Forecast Framework (Bollinger + LSTM + Ensemble + On-Chain)

A practical, testable pipeline that compares **Bollinger mean-reversion** against an **LSTM** model,
optionally augments with **on-chain features**, and combines them via a simple **ensemble**.
Includes **walk-forward validation**, **probabilities**, **regime filter**, **σ‑scaled rebuys**, and a **lightweight backtest**.

## Quick Start

```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py --config config.yaml
```

Artifacts are written to `./artifacts/<symbol>_<timeframe>/`:
- `predictions.csv` – timestamps, actual close, Bollinger forecast, LSTM forecast, ensemble forecast, prob_up
- `metrics.json` – MAE, RMSE, MAPE, directional accuracy, Sharpe (simple backtest), etc.
- `pred_vs_actual.png` – visual check
- `actions.json` – BUY/REBUY/SELL with timestamps and size hints
