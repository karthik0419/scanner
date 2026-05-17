import os
import pickle
import pandas as pd
from datetime import date, timedelta
from pathlib import Path

# Fix jugaad-data Windows makedirs bug (tries makedirs without exist_ok)
_orig_makedirs = os.makedirs
os.makedirs = lambda p, *a, **kw: _orig_makedirs(p, *a, exist_ok=True, **{k: v for k, v in kw.items() if k != "exist_ok"})

from jugaad_data.nse import stock_df as nse_stock_df

_CACHE_DIR = Path(__file__).parent / "cache"
_CACHE_DIR.mkdir(exist_ok=True)


def _cache_path(symbol, days):
    key = f"{symbol.replace('.', '_')}_{days}_{date.today()}.pkl"
    return _CACHE_DIR / key


def _cache_load(symbol, days):
    p = _cache_path(symbol, days)
    if p.exists():
        try:
            with open(p, "rb") as f:
                return pickle.load(f)
        except Exception:
            p.unlink(missing_ok=True)
    return None


def _cache_save(symbol, days, df):
    try:
        with open(_cache_path(symbol, days), "wb") as f:
            pickle.dump(df, f)
    except Exception:
        pass


def _nse_symbol(symbol):
    """Strip .NS / .BO suffix — jugaad-data uses bare NSE symbols."""
    return symbol.replace(".NS", "").replace(".BO", "").upper()


def _fetch_nse(symbol, days=180):
    """Fetch daily OHLCV from NSE via jugaad-data, with yfinance fallback. Results cached for the day."""
    cached = _cache_load(symbol, days)
    if cached is not None:
        return cached

    sym = _nse_symbol(symbol)
    to_dt = date.today()
    from_dt = to_dt - timedelta(days=days)
    raw = None
    try:
        raw = nse_stock_df(symbol=sym, from_date=from_dt, to_date=to_dt, series="EQ")
    except Exception as e:
        print(f"  [NSE] fetch failed for {sym}: {e}")

    if raw is not None and not raw.empty:
        raw = raw.rename(columns={
            "DATE": "Date", "OPEN": "Open", "HIGH": "High",
            "LOW": "Low", "CLOSE": "Close", "VOLUME": "Volume",
        })
        raw["Date"] = pd.to_datetime(raw["Date"]).dt.tz_localize(None).dt.normalize()
        raw = raw.set_index("Date").sort_index()
        cols = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in raw.columns]
        result = raw[cols].dropna()
        _cache_save(symbol, days, result)
        return result

    # Fallback: yfinance
    try:
        import yfinance as yf
        yf_sym = symbol if symbol.endswith(".NS") else sym + ".NS"
        period_map = {180: "6mo", 400: "2y", 730: "3y"}
        period = period_map.get(days) or ("2y" if days <= 400 else "5y")
        df = yf.download(yf_sym, period=period, interval="1d", progress=False, auto_adjust=True)
        if df is not None and not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
            result = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
            _cache_save(symbol, days, result)
            return result
    except Exception:
        pass

    return None


def _resample_weekly(df_daily):
    """Resample daily → weekly OHLCV."""
    return (
        df_daily.resample("W")
        .agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"})
        .dropna()
    )


# -----------------------
# SINGLE TIMEFRAME
# -----------------------
def fetch_data(symbol, period="6mo", interval="1d"):
    days_map = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730}
    days = days_map.get(period, 180)
    return _fetch_nse(symbol, days=days)


# -----------------------
# MULTI TIMEFRAME
# -----------------------
def fetch_multi_tf(symbol):
    try:
        # Daily — 12 months (increased from 6mo to catch longer Cup & Handle formations)
        df_daily = _fetch_nse(symbol, days=365)
        if df_daily is None or df_daily.empty:
            return None, None, None

        # Weekly — resample from 2y of daily data
        df_daily_2y = _fetch_nse(symbol, days=730)
        df_weekly = _resample_weekly(df_daily_2y) if df_daily_2y is not None else None

        # NSE historical intraday is not publicly available;
        # use last 60 daily bars resampled to simulate 4H sessions
        df_4h = None
        if df_daily is not None and len(df_daily) >= 15:
            # Each trading day has ~2 "4H sessions"; duplicate rows as a proxy
            df_4h = df_daily.tail(60).copy()

        return df_daily, df_weekly, df_4h

    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None, None, None
