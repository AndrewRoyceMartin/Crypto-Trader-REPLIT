# loaders/ohlcv_loader.py

from concurrent.futures import ThreadPoolExecutor

import pandas as pd


def fetch_ohlcv_for_symbol(symbol: str, days: int = 7) -> pd.DataFrame:
    """
    Fetch daily OHLCV candles for a symbol using OKX native client.
    Assumes symbol like 'BTC', 'ETH' – appends '-USDT'.
    """
    try:
        from src.utils.okx_native import OKXCreds, OKXNative
        creds = OKXCreds.from_env()
        client = OKXNative(creds)

        inst_id = f"{symbol}-USDT"
        candles = client.candles(inst_id, bar="1D", limit=days)

        if not candles:
            return pd.DataFrame()

        df = pd.DataFrame([{
            'timestamp': int(c[0]),
            'open': float(c[1]),
            'high': float(c[2]),
            'low': float(c[3]),
            'close': float(c[4]),
            'volume': float(c[5]),
            'price': float(c[4])
        } for c in candles])

        df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df.sort_values('date')

        return df

    except Exception as e:
        print(f"[ERROR] Failed to fetch OHLCV for {symbol}: {e}")
        return pd.DataFrame()

def load_all_ohlcv_parallel(symbols: list[str], days: int = 7, max_workers: int = 10) -> dict[str, pd.DataFrame]:
    """
    Load OHLCV data for multiple symbols in parallel using threading.
    """
    results = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(fetch_ohlcv_for_symbol, sym, days): sym
            for sym in symbols
        }

        for future in futures:
            symbol = futures[future]
            try:
                df = future.result()
                if not df.empty:
                    results[symbol] = df
            except Exception as e:
                print(f"[ERROR] Error loading {symbol}: {e}")

    return results
