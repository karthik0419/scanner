"""
Fast parallel fetcher with 1-day disk cache.
Replaces sequential _fetch_nse calls.
"""

import os
import pandas as pd
from datetime import date, datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from data.loader import _fetch_nse, _resample_weekly

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "cache")
os.makedirs(CACHE_DIR, exist_ok=True)


def _cache_path(symbol, days):
    safe = symbol.replace(".", "_").replace("^", "")
    return os.path.join(CACHE_DIR, f"{safe}_{days}d.csv")


def _is_fresh(path, max_age_hours=8):
    if not os.path.exists(path):
        return False
    age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(path))
    return age < timedelta(hours=max_age_hours)


def fetch_cached(symbol, days=400):
    path = _cache_path(symbol, days)
    if _is_fresh(path):
        try:
            df = pd.read_csv(path, index_col=0, parse_dates=True)
            if not df.empty:
                return df
        except Exception:
            pass

    df = _fetch_nse(symbol, days=days)
    if df is not None and not df.empty:
        df.to_csv(path)
    return df


def fetch_all_parallel(symbols, days=400, max_workers=10):
    """Fetch all symbols in parallel. Returns dict {symbol: df}."""
    results = {}

    def _fetch(sym):
        return sym, fetch_cached(sym, days)

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_fetch, s): s for s in symbols}
        for f in as_completed(futures):
            sym, df = f.result()
            results[sym] = df

    return results
