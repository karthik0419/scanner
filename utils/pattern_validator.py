import pandas as pd
import numpy as np

def validate_pattern_quality(df, pattern_type, result):
    """
    Advanced pattern validation to filter out false signals
    Returns validation score (0-100) and boolean if pattern is valid
    """
    validation_score = 0
    validation_reasons = []
    
    # 1. Volume Pattern Validation
    volume_score, volume_reasons = validate_volume_pattern(df, pattern_type)
    validation_score += volume_score * 0.3
    validation_reasons.extend(volume_reasons)
    
    # 2. Price Action Validation
    price_score, price_reasons = validate_price_action(df, pattern_type, result)
    validation_score += price_score * 0.4
    validation_reasons.extend(price_reasons)
    
    # 3. Trend Context Validation
    trend_score, trend_reasons = validate_trend_context(df, pattern_type)
    validation_score += trend_score * 0.3
    validation_reasons.extend(trend_reasons)
    
    # Pattern is valid if score > 60
    is_valid = validation_score >= 60
    
    return is_valid, validation_score, validation_reasons

def validate_volume_pattern(df, pattern_type):
    """Validate volume patterns for the setup"""
    score = 0
    reasons = []
    
    # Recent volume analysis
    recent_volume = df['Volume'].tail(10)
    avg_volume = df['Volume'].tail(50).mean()
    current_volume = df['Volume'].iloc[-1]
    
    # Volume trend analysis
    volume_trend = np.polyfit(range(len(recent_volume)), recent_volume, 1)[0]
    
    # Volume spike detection
    volume_spike = current_volume > avg_volume * 1.5
    
    if volume_spike:
        score += 40
        reasons.append("Strong volume spike")
    elif current_volume > avg_volume * 1.2:
        score += 25
        reasons.append("Above average volume")
    else:
        reasons.append("Low volume confirmation")
    
    # Volume trend validation
    if volume_trend > 0:
        score += 30
        reasons.append("Rising volume trend")
    elif volume_trend > -avg_volume * 0.01:
        score += 15
        reasons.append("Stable volume")
    else:
        reasons.append("Declining volume trend")
    
    # Volume consistency
    volume_std = recent_volume.std()
    if volume_std < avg_volume * 0.5:
        score += 30
        reasons.append("Consistent volume pattern")
    
    return score, reasons

def validate_price_action(df, pattern_type, result):
    """Validate price action quality"""
    score = 0
    reasons = []
    
    current_price = df['Close'].iloc[-1]
    recent_prices = df['Close'].tail(20)
    
    # Price momentum
    price_momentum = (current_price - recent_prices.iloc[0]) / recent_prices.iloc[0]
    
    # Volatility analysis
    returns = df['Close'].pct_change().tail(20)
    volatility = returns.std()
    avg_volatility = df['Close'].pct_change().tail(50).std()
    
    # Support/Resistance validation
    if pattern_type in ["Breakout Retest", "Cup & Handle", "Double Bottom"]:
        # For bullish patterns, check support strength
        recent_lows = df['Low'].tail(10)
        support_level = recent_lows.min()
        support_touches = sum(1 for low in recent_lows if abs(low - support_level) / support_level < 0.02)
        
        if support_touches >= 2:
            score += 35
            reasons.append("Strong support level")
        
        # Check if price is above key moving averages
        ma_20 = df['Close'].rolling(20).mean().iloc[-1]
        ma_50 = df['Close'].rolling(50).mean().iloc[-1]
        
        if current_price > ma_20:
            score += 20
            reasons.append("Above 20-day MA")
        
        if current_price > ma_50:
            score += 15
            reasons.append("Above 50-day MA")
    
    # Volatility check (avoid extremely volatile stocks)
    if volatility < avg_volatility * 1.5:
        score += 25
        reasons.append("Normal volatility")
    else:
        reasons.append("High volatility warning")
    
    # Price momentum check
    if price_momentum > 0.05:  # 5% momentum
        score += 20
        reasons.append("Positive momentum")
    elif price_momentum > 0:
        score += 10
        reasons.append("Slight momentum")
    
    return score, reasons

def validate_trend_context(df, pattern_type):
    """Validate overall trend context"""
    score = 0
    reasons = []
    
    # Multiple timeframe trend analysis
    ma_20 = df['Close'].rolling(20).mean().iloc[-1]
    ma_50 = df['Close'].rolling(50).mean().iloc[-1]
    ma_200 = df['Close'].rolling(200).mean().iloc[-1]
    
    current_price = df['Close'].iloc[-1]
    
    # Trend alignment
    if pattern_type in ["Breakout Retest", "Cup & Handle", "Double Bottom", "Bullish Flag"]:
        # Bullish patterns - prefer uptrend context
        if current_price > ma_20 > ma_50:
            score += 40
            reasons.append("Strong uptrend")
        elif current_price > ma_20:
            score += 25
            reasons.append("Short-term uptrend")
        elif ma_20 > ma_50:
            score += 15
            reasons.append("Trend turning positive")
        
        # Distance from moving averages
        if current_price > ma_200:
            score += 20
            reasons.append("Above long-term trend")
    
    elif pattern_type in ["Double Top", "Bearish Flag"]:
        # Bearish patterns - prefer downtrend context
        if current_price < ma_20 < ma_50:
            score += 40
            reasons.append("Strong downtrend")
        elif current_price < ma_20:
            score += 25
            reasons.append("Short-term downtrend")
    
    # Trend strength
    ma_slope_20 = np.polyfit(range(20), df['Close'].tail(20), 1)[0]
    ma_slope_50 = np.polyfit(range(50), df['Close'].tail(50), 1)[0]
    
    if abs(ma_slope_20) > abs(ma_slope_50):
        score += 20
        reasons.append("Strengthening trend")
    
    return score, reasons
