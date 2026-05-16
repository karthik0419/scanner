import pandas as pd
import numpy as np

def calculate_advanced_targets(df, pattern_type, result):
    """
    Calculate more sophisticated targets and stop losses based on:
    - Fibonacci levels
    - Support/Resistance zones
    - Volatility-based stops
    - Pattern-specific targets
    """
    current_price = float(df['Close'].iloc[-1])
    high_20 = float(df['High'].tail(20).max())
    low_20 = float(df['Low'].tail(20).min())
    high_50 = float(df['High'].tail(50).max())
    low_50 = float(df['Low'].tail(50).min())
    
    # Calculate ATR for volatility-based stops
    atr = calculate_atr(df)
    
    if pattern_type == "Breakout Retest":
        return calculate_retest_targets(df, result, atr)
    elif pattern_type == "Double Bottom":
        return calculate_double_bottom_targets(df, result, atr)
    elif pattern_type == "Double Top":
        return calculate_double_top_targets(df, result, atr)
    elif pattern_type == "Cup & Handle":
        return calculate_cup_handle_targets(df, result, atr)
    elif pattern_type == "Darvas Box":
        return calculate_darvas_box_targets(df, result, atr)
    elif pattern_type in ["Bullish Flag", "Bearish Flag", "Bullish Pennant", "Bearish Pennant"]:
        return calculate_flag_targets(df, result, atr)
    else:
        return default_targets(result, atr)

def calculate_atr(df, period=14):
    """Calculate Average True Range"""
    high = df['High']
    low = df['Low']
    close = df['Close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean().iloc[-1]
    return float(atr)

def calculate_retest_targets(df, result, atr):
    """Advanced targets for breakout retest patterns"""
    current_price = float(df['Close'].iloc[-1])
    breakout_level = float(result["breakout"])
    
    # Find next resistance levels
    resistance_levels = find_resistance_levels(df)
    support_levels = find_support_levels(df)
    
    # Multiple targets
    targets = []
    
    # Target 1: Next resistance level
    next_resistance = min([r for r in resistance_levels if r > breakout_level], default=breakout_level * 1.08)
    targets.append(next_resistance)
    
    # Target 2: Fibonacci extension (1.618)
    fib_extension = breakout_level + (breakout_level - min(support_levels)) * 0.618
    targets.append(fib_extension)
    
    # Target 3: Measured move (recent range)
    recent_range = breakout_level - min(support_levels)
    measured_move = breakout_level + recent_range
    targets.append(measured_move)
    
    # Advanced stop loss
    stop_loss = calculate_volatility_stop(df, atr, direction="long")
    
    # Validate stop loss
    if stop_loss >= current_price * 0.95:  # If stop is too close
        stop_loss = min(support_levels) * 0.98
    
    return {
        "targets": targets[:3],  # Top 3 targets
        "stop_loss": stop_loss,
        "atr": atr,
        "target_type": "Multi-level (Resistance + Fib + Measured)"
    }

def calculate_double_bottom_targets(df, result, atr):
    """Targets for double bottom reversal"""
    current_price = float(df['Close'].iloc[-1])
    breakout_level = float(result["breakout"])
    bottom_level = float(result["stop_loss"]) / 0.98  # Approximate bottom
    
    # Calculate targets based on double bottom pattern
    targets = []
    
    # Target 1: Conservative (50% of pattern height)
    pattern_height = breakout_level - bottom_level
    target1 = breakout_level + pattern_height * 0.5
    targets.append(target1)
    
    # Target 2: Measured move (100% of pattern height)
    target2 = breakout_level + pattern_height
    targets.append(target2)
    
    # Target 3: Fibonacci extension (1.272)
    target3 = breakout_level + pattern_height * 1.272
    targets.append(target3)
    
    # Tight stop loss based on recent low
    recent_low = df['Low'].tail(5).min()
    stop_loss = min(recent_low, bottom_level) * 0.98
    
    return {
        "targets": targets[:3],
        "stop_loss": stop_loss,
        "atr": atr,
        "target_type": "Double Bottom (Pattern Height + Fib)"
    }

def calculate_cup_handle_targets(df, result, atr):
    """Targets for cup and handle pattern"""
    targets = []
    
    # Cup measurements
    cup_high = float(result["breakout"])
    cup_low = float(result["stop_loss"]) / 0.98  # Approximate cup low
    
    cup_depth = cup_high - cup_low
    
    # Target 1: Conservative (50% of cup depth)
    target1 = cup_high + cup_depth * 0.5
    targets.append(target1)
    
    # Target 2: Full cup depth projection
    target2 = cup_high + cup_depth
    targets.append(target2)
    
    # Target 3: Fibonacci extension (1.618)
    target3 = cup_high + cup_depth * 1.618
    targets.append(target3)
    
    # Stop loss below handle
    stop_loss = float(result["stop_loss"])
    
    return {
        "targets": targets[:3],
        "stop_loss": stop_loss,
        "atr": atr,
        "target_type": "Cup & Handle (Depth Projection)"
    }

def calculate_darvas_box_targets(df, result, atr):
    """Targets for Darvas box breakout"""
    box_high = float(result["breakout"])
    box_low = float(result["stop_loss"]) / 0.98
    box_range = box_high - box_low
    
    targets = []
    
    # Target 1: Conservative (50% of box range)
    target1 = box_high + box_range * 0.5
    targets.append(target1)
    
    # Target 2: Full box range projection
    target2 = box_high + box_range
    targets.append(target2)
    
    # Target 3: Extended move (1.5x box range)
    target3 = box_high + box_range * 1.5
    targets.append(target3)
    
    # Stop loss below box
    stop_loss = box_low * 0.98
    
    return {
        "targets": targets[:3],
        "stop_loss": stop_loss,
        "atr": atr,
        "target_type": "Darvas Box (Range Projection)"
    }

def calculate_flag_targets(df, result, atr):
    """Targets for flag and pennant patterns"""
    current_price = float(df['Close'].iloc[-1])
    breakout_level = float(result["breakout"])
    
    # Find flagpole height
    flagpole_data = df.tail(20).head(10)  # First 10 of last 20 candles
    flagpole_low = flagpole_data['Low'].min()
    flagpole_high = flagpole_data['High'].max()
    flagpole_height = abs(flagpole_high - flagpole_low)
    
    targets = []
    
    # Target 1: Conservative (50% of flagpole)
    target1 = breakout_level + flagpole_height * 0.5
    targets.append(target1)
    
    # Target 2: Full flagpole projection
    target2 = breakout_level + flagpole_height
    targets.append(target2)
    
    # Target 3: Extended (1.272 of flagpole)
    target3 = breakout_level + flagpole_height * 1.272
    targets.append(target3)
    
    # Tight stop loss
    stop_loss = calculate_volatility_stop(df, atr, direction="long")
    
    return {
        "targets": targets[:3],
        "stop_loss": stop_loss,
        "atr": atr,
        "target_type": "Flag/Pennant (Flagpole Projection)"
    }

def calculate_volatility_stop(df, atr, direction="long"):
    """Calculate volatility-based stop loss"""
    current_price = float(df['Close'].iloc[-1])
    
    if direction == "long":
        # 2x ATR below current price
        stop = current_price - (2 * atr)
        # Ensure stop is not too far (max 5%)
        max_stop = current_price * 0.95
        return max(stop, max_stop)
    else:
        # 2x ATR above current price
        stop = current_price + (2 * atr)
        # Ensure stop is not too far (max 5%)
        max_stop = current_price * 1.05
        return min(stop, max_stop)

def find_resistance_levels(df, lookback=50):
    """Find significant resistance levels"""
    highs = df['High'].tail(lookback)
    
    # Find peaks using simple method
    resistance_levels = []
    
    for i in range(2, len(highs) - 2):
        current_high = highs.iloc[i]
        
        # Check if it's a peak
        if (current_high > highs.iloc[i-1] and 
            current_high > highs.iloc[i-2] and 
            current_high > highs.iloc[i+1] and 
            current_high > highs.iloc[i+2]):
            
            resistance_levels.append(float(current_high))
    
    return sorted(list(set(resistance_levels)), reverse=True)

def find_support_levels(df, lookback=50):
    """Find significant support levels"""
    lows = df['Low'].tail(lookback)
    
    # Find troughs using simple method
    support_levels = []
    
    for i in range(2, len(lows) - 2):
        current_low = lows.iloc[i]
        
        # Check if it's a trough
        if (current_low < lows.iloc[i-1] and 
            current_low < lows.iloc[i-2] and 
            current_low < lows.iloc[i+1] and 
            current_low < lows.iloc[i+2]):
            
            support_levels.append(float(current_low))
    
    return sorted(list(set(support_levels)))

def default_targets(result, atr):
    """Default target calculation"""
    current_price = float(result["cmp"])
    breakout_level = float(result["breakout"])
    
    # Simple targets
    target1 = breakout_level + (breakout_level - current_price) * 0.5
    target2 = breakout_level + (breakout_level - current_price)
    target3 = breakout_level + (breakout_level - current_price) * 1.5
    
    return {
        "targets": [target1, target2, target3],
        "stop_loss": float(result["stop_loss"]),
        "atr": atr,
        "target_type": "Default (Conservative)"
    }
