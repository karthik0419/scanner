"""
Descending Channel Breakout Detection

Logic:
1. Identify a descending channel — lower highs + lower lows in parallel
2. Price breaks above the upper channel line (resistance trendline)
3. Breakout confirmed with volume surge
4. Entry on breakout, target = channel height projected upward

Like SHAKTIPUMP — long downtrend in channel, then breaks above upper line.
"""

import numpy as np


def _fit_trendline(indices, values):
    """Fit a linear trendline. Returns (slope, intercept)."""
    coeffs = np.polyfit(indices, values, 1)
    return coeffs[0], coeffs[1]


def detect_descending_channel(df, lookback=60, min_touches=3):
    if df is None or len(df) < lookback + 10:
        return None

    try:
        df_slice = df.tail(lookback + 10)
        highs  = df_slice['High'].values
        lows   = df_slice['Low'].values
        closes = df_slice['Close'].values
        vols   = df_slice['Volume'].values
        n      = len(df_slice)

        cmp     = float(closes[-1])
        avg_vol = float(np.mean(vols[-20:]))
        cur_vol = float(vols[-1])

        # Find swing highs and lows
        window = 4
        swing_high_idx, swing_high_val = [], []
        swing_low_idx,  swing_low_val  = [], []

        for i in range(window, n - window):
            if highs[i] == max(highs[i - window: i + window + 1]):
                swing_high_idx.append(i)
                swing_high_val.append(highs[i])
            if lows[i] == min(lows[i - window: i + window + 1]):
                swing_low_idx.append(i)
                swing_low_val.append(lows[i])

        if len(swing_high_idx) < min_touches or len(swing_low_idx) < min_touches:
            return None

        # Fit trendlines to swing highs and lows
        h_slope, h_intercept = _fit_trendline(swing_high_idx, swing_high_val)
        l_slope, l_intercept = _fit_trendline(swing_low_idx,  swing_low_val)

        # Must be descending channel — both slopes negative
        if h_slope >= -0.05 or l_slope >= -0.05:
            return None

        # Slopes must be roughly parallel (within 60% of each other)
        if abs(h_slope) == 0:
            return None
        slope_ratio = abs(l_slope) / abs(h_slope)
        if not (0.4 <= slope_ratio <= 2.5):
            return None

        # Upper channel line value at current bar
        upper_line = h_slope * (n - 1) + h_intercept
        lower_line = l_slope * (n - 1) + l_intercept
        channel_height = upper_line - lower_line

        if channel_height <= 0:
            return None

        # Breakout: current price must be ABOVE the upper channel line
        if cmp <= upper_line:
            return None
        if cmp > upper_line * 1.08:
            return None  # ran too far above already

        # Volume confirmation on breakout
        breakout_vol_ok = cur_vol > avg_vol * 1.3

        # Stop loss = back inside channel (upper line)
        stop_loss = upper_line * 0.98
        risk_amt  = cmp - stop_loss

        if risk_amt <= 0:
            return None

        # Target = channel height projected upward from breakout
        target = upper_line + channel_height
        rr     = round((target - cmp) / risk_amt, 2)

        if rr < 1.0:
            return None

        return {
            "pattern":   "Channel Breakout",
            "cmp":       cmp,
            "breakout":  round(upper_line, 2),
            "stop_loss": round(stop_loss, 2),
            "target":    round(target, 2),
            "volume":    breakout_vol_ok,
            "status":    "BREAKOUT" if cmp > upper_line else "NEAR",
        }

    except Exception:
        return None
