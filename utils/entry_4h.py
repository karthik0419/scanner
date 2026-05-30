import numpy as np

def detect_4h_entry(df_4h, breakout_level):
    if df_4h is None or len(df_4h) < 50:
        return False, {}

    highs = df_4h['High']
    lows = df_4h['Low']
    close = df_4h['Close']
    volume = df_4h['Volume']

    current_price = float(close.iloc[-1])

    # -----------------------
    # 🔥 SHORT TERM TREND
    # -----------------------
    ema20 = close.ewm(span=20).mean()
    trend_up = current_price > ema20.iloc[-1]

    # -----------------------
    # 🔥 MICRO BREAKOUT
    # -----------------------
    recent_high = highs.tail(10).max()

    micro_breakout = current_price > recent_high * 1.002

    # -----------------------
    # 🔥 TIGHT RANGE BREAK
    # -----------------------
    range_5 = highs.tail(5).max() - lows.tail(5).min()
    range_10 = highs.tail(10).max() - lows.tail(10).min()

    tight_range = range_5 < range_10 * 0.7

    # -----------------------
    # 🔥 VOLUME PUSH
    # -----------------------
    vol_short = volume.tail(3).mean()
    vol_long = volume.tail(15).mean()

    volume_push = vol_short > vol_long * 1.2

    # -----------------------
    # 🔥 NEAR DAILY BREAKOUT
    # -----------------------
    near_daily_level = abs(current_price - breakout_level) / breakout_level < 0.03

    # -----------------------
    # FINAL ENTRY LOGIC
    # -----------------------
    entry_signal = (
        trend_up and
        (micro_breakout or tight_range) and
        near_daily_level
    )

    confidence = 0

    if trend_up:
        confidence += 1
    if micro_breakout:
        confidence += 2
    if tight_range:
        confidence += 1
    if volume_push:
        confidence += 2

    return entry_signal, {
        "trend_up": trend_up,
        "micro_breakout": micro_breakout,
        "tight_range": tight_range,
        "volume_push": volume_push,
        "confidence": confidence
    }