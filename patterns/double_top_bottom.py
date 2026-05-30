def detect_double_top(df):
    if df is None or len(df) < 60:
        return None
    
    # Look for double top pattern (last 40-60 days)
    pattern_period = min(50, len(df) - 10)
    pattern_data = df.tail(pattern_period)
    
    # Find two peaks
    highs = pattern_data['High']
    
    # Find first peak
    first_peak_idx = highs.idxmax()
    first_peak = float(highs.max())
    
    # Look for second peak after first peak
    second_peak_data = pattern_data.loc[first_peak_idx:]
    if len(second_peak_data) < 10:
        return None
    
    second_peak = float(second_peak_data['High'].max())
    second_peak_idx = second_peak_data['High'].idxmax()
    
    # Peaks should be similar height (within 2% for more precision)
    if abs(first_peak - second_peak) / first_peak > 0.02:
        return None
    
    # There should be a valley between peaks
    valley_data = pattern_data.loc[first_peak_idx:second_peak_idx]
    valley = float(valley_data['Low'].min())
    
    # Valley should be significantly lower than peaks
    if (first_peak - valley) / first_peak < 0.05:
        return None
    
    current_price = float(df['Close'].iloc[-1])
    
    # Check if breaking down from double top
    breakdown_level = valley
    near_breakdown = current_price <= breakdown_level * 1.02
    
    if near_breakdown and current_price < first_peak * 0.95:
        # Short setup
        target = valley - (first_peak - valley) * 0.5
        stop_loss = first_peak * 1.02
        
        return {
            "pattern": "Double Top",
            "cmp": current_price,
            "breakout": breakdown_level,
            "stop_loss": stop_loss,
            "target": target,
            "volume": True,
            "status": "BREAKDOWN"
        }
    
    return None

def detect_double_bottom(df):
    if df is None or len(df) < 60:
        return None
    
    # Look for double bottom pattern (last 40-60 days)
    pattern_period = min(50, len(df) - 10)
    pattern_data = df.tail(pattern_period)
    
    # Find two bottoms
    lows = pattern_data['Low']
    
    # Find first bottom
    first_bottom_idx = lows.idxmin()
    first_bottom = float(lows.min())
    
    # Look for second bottom after first bottom
    second_bottom_data = pattern_data.loc[first_bottom_idx:]
    if len(second_bottom_data) < 10:
        return None
    
    second_bottom = float(second_bottom_data['Low'].min())
    second_bottom_idx = second_bottom_data['Low'].idxmin()
    
    # Bottoms should be similar depth (within 2% for more precision)
    if abs(first_bottom - second_bottom) / first_bottom > 0.02:
        return None
    
    # There should be a peak between bottoms
    peak_data = pattern_data.loc[first_bottom_idx:second_bottom_idx]
    peak = float(peak_data['High'].max())
    
    # Peak should be significantly higher than bottoms
    if (peak - first_bottom) / first_bottom < 0.05:
        return None
    
    current_price = float(df['Close'].iloc[-1])
    
    # Check if breaking up from double bottom
    breakout_level = peak
    near_breakout = current_price >= breakout_level * 0.98
    
    if near_breakout and current_price > first_bottom * 1.05:
        # Long setup
        target = peak + (peak - first_bottom) * 0.5
        stop_loss = first_bottom * 0.98
        
        return {
            "pattern": "Double Bottom",
            "cmp": current_price,
            "breakout": breakout_level,
            "stop_loss": stop_loss,
            "target": target,
            "volume": True,
            "status": "BREAKOUT"
        }
    
    return None
