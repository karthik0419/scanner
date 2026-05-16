def _validate_cup_shape(cup_data):
    """
    Verify U-shape: the price low should occur in the middle half of the cup,
    not at the very start or end (which would be a V or reverse-V).
    """
    n = len(cup_data)
    if n < 9:
        return False
    low_idx = cup_data['Low'].argmin()
    # Low must be in the central 80% of the cup (not the first or last 10%)
    return int(n * 0.10) <= low_idx <= int(n * 0.90)


def _detect_cup_handle(df, min_bars, cup_bars, handle_bars,
                       min_depth, max_depth, near_pct):
    """Core Cup & Handle logic shared by daily and weekly variants."""
    if df is None or len(df) < min_bars:
        return None

    cup_bars  = min(cup_bars,  len(df) - handle_bars)
    if cup_bars < 15:
        return None

    cup_data    = df.iloc[-(cup_bars + handle_bars) : -handle_bars]
    handle_data = df.tail(handle_bars)

    if cup_data.empty or handle_data.empty:
        return None

    # Left and right rim + rounded bottom
    n = len(cup_data)
    left_high  = float(cup_data['High'].iloc[: n // 3].max())
    cup_low    = float(cup_data['Low'].min())
    right_high = float(cup_data['High'].iloc[2 * n // 3 :].max())
    cup_high   = max(left_high, right_high)

    cup_depth = (cup_high - cup_low) / cup_high
    if not (min_depth <= cup_depth <= max_depth):
        return None

    if not _validate_cup_shape(cup_data):
        return None

    handle_high  = float(handle_data['High'].max())
    handle_low   = float(handle_data['Low'].min())
    current_price = float(df['Close'].iloc[-1])

    # Handle must sit in upper 35% of cup range
    handle_position = (handle_low - cup_low) / (cup_high - cup_low)
    if handle_position < 0.35:
        return None

    # Handle retracement must be tighter than cup
    handle_depth = (handle_high - handle_low) / cup_high
    if handle_depth > cup_depth * 0.65:
        return None

    # Breakout = right rim or handle high, whichever is higher
    breakout_level = max(right_high, handle_high)

    # Price within near_pct% of breakout
    if current_price < breakout_level * (1 - near_pct):
        return None

    avg_volume     = float(df['Volume'].tail(20).mean())
    current_volume = float(df['Volume'].iloc[-1])
    volume_ok      = current_volume > avg_volume * 1.2

    # Full measured-move target (cup depth projected from breakout)
    target    = breakout_level + (cup_high - cup_low)
    stop_loss = handle_low * 0.98

    if stop_loss >= current_price:
        return None

    return {
        "pattern":       "Cup & Handle",
        "cmp":           current_price,
        "breakout":      breakout_level,
        "stop_loss":     stop_loss,
        "target":        target,
        "volume":        volume_ok,
        "status":        "BREAKOUT" if current_price > breakout_level else "NEAR",
        "cup_depth_pct": round(cup_depth * 100, 1),
    }


# -------------------------------------------------- #
#  Daily Cup & Handle  (current price near breakout) #
# -------------------------------------------------- #
def detect_cup_handle(df):
    return _detect_cup_handle(
        df,
        min_bars   = 80,
        cup_bars   = 60,   # ~3 months on daily
        handle_bars = 15,  # ~3 weeks handle
        min_depth  = 0.12, # lowered from 0.15 — catches shallower cups like BAJAJ-AUTO
        max_depth  = 0.60, # raised from 0.50 — catches deeper cups like LAURUSLABS
        near_pct   = 0.08, # raised from 0.05 — within 8% of breakout
    )


# -------------------------------------------------- #
#  Weekly Cup & Handle  (large multi-month setups)   #
# -------------------------------------------------- #
def detect_cup_handle_weekly(df_weekly):
    """
    Detects the kind of weekly C&H shown on Instagram:
    large 6-18 month cups, 3-month handles, 2x targets.
    """
    result = _detect_cup_handle(
        df_weekly,
        min_bars    = 40,   # ~10 months weekly data
        cup_bars    = 65,   # up to ~15 months cup
        handle_bars = 12,   # ~3 months handle
        min_depth   = 0.15,
        max_depth   = 0.65, # weekly cups can be much deeper
        near_pct    = 0.15, # within 15% — weekly setups take time to reach rim
    )
    if result:
        result["pattern"]   = "Cup & Handle (Weekly)"
        result["timeframe"] = "Weekly"
    return result
