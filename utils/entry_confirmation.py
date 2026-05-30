import pandas as pd
import numpy as np
from datetime import datetime

class EntryConfirmationSystem:
    def __init__(self):
        self.confirmation_indicators = self.get_confirmation_indicators()
    
    def get_confirmation_indicators(self):
        """Get all entry confirmation indicators"""
        return {
            "price_action": {
                "title": "Price Action Confirmation",
                "indicators": [
                    {
                        "name": "Candlestick Pattern",
                        "description": "Bullish candlestick at entry",
                        "weight": 20,
                        "signals": self.check_candlestick_patterns
                    },
                    {
                        "name": "Breakout Confirmation",
                        "description": "Price closes above resistance",
                        "weight": 25,
                        "signals": self.check_breakout_confirmation
                    },
                    {
                        "name": "Pullback Entry",
                        "description": "Pullback to support/resistance",
                        "weight": 15,
                        "signals": self.check_pullback_entry
                    },
                    {
                        "name": "Consolidation Break",
                        "description": "Break from consolidation",
                        "weight": 18,
                        "signals": self.check_consolidation_break
                    }
                ]
            },
            "volume": {
                "title": "Volume Confirmation",
                "indicators": [
                    {
                        "name": "Volume Spike",
                        "description": "Above average volume",
                        "weight": 20,
                        "signals": self.check_volume_spike
                    },
                    {
                        "name": "Volume Accumulation",
                        "description": "Consistent high volume",
                        "weight": 15,
                        "signals": self.check_volume_accumulation
                    },
                    {
                        "name": "Volume Divergence",
                        "description": "Volume-price relationship",
                        "weight": 10,
                        "signals": self.check_volume_divergence
                    }
                ]
            },
            "momentum": {
                "title": "Momentum Confirmation",
                "indicators": [
                    {
                        "name": "RSI Confirmation",
                        "description": "RSI in favorable range",
                        "weight": 15,
                        "signals": self.check_rsi_confirmation
                    },
                    {
                        "name": "MACD Signal",
                        "description": "MACD bullish crossover",
                        "weight": 18,
                        "signals": self.check_macd_signal
                    },
                    {
                        "name": "Moving Average Cross",
                        "description": "MA bullish crossover",
                        "weight": 12,
                        "signals": self.check_ma_crossover
                    },
                    {
                        "name": "Price Momentum",
                        "description": "Positive price momentum",
                        "weight": 10,
                        "signals": self.check_price_momentum
                    }
                ]
            },
            "timeframe": {
                "title": "Multi-Timeframe Confirmation",
                "indicators": [
                    {
                        "name": "4H Alignment",
                        "description": "4H timeframe confirms setup",
                        "weight": 15,
                        "signals": self.check_4h_alignment
                    },
                    {
                        "name": "Weekly Alignment",
                        "description": "Weekly trend alignment",
                        "weight": 12,
                        "signals": self.check_weekly_alignment
                    },
                    {
                        "name": "Time of Day",
                        "description": "Optimal entry timing",
                        "weight": 8,
                        "signals": self.check_time_of_day
                    }
                ]
            }
        }
    
    def confirm_entry(self, df_daily, df_4h, df_weekly, setup_data):
        """Generate comprehensive entry confirmation"""
        confirmation = {
            "setup": setup_data,
            "overall_score": 0,
            "max_score": 0,
            "confidence_level": "",
            "recommendation": "",
            "categories": {},
            "signals": [],
            "warnings": []
        }
        
        total_score = 0
        max_score = 0
        
        # Check each category
        for category_key, category_data in self.confirmation_indicators.items():
            category_result = {
                "title": category_data["title"],
                "indicators": [],
                "category_score": 0,
                "category_max": 0
            }
            
            for indicator in category_data["indicators"]:
                indicator_result = {
                    "name": indicator["name"],
                    "description": indicator["description"],
                    "weight": indicator["weight"],
                    "signal_strength": 0,
                    "signal_details": "",
                    "confirmed": False
                }
                
                # Check the signal
                try:
                    signal_data = indicator["signals"](df_daily, df_4h, df_weekly, setup_data)
                    indicator_result["signal_strength"] = signal_data["strength"]
                    indicator_result["signal_details"] = signal_data["details"]
                    indicator_result["confirmed"] = signal_data["confirmed"]
                    
                    # Add to signals list if confirmed
                    if signal_data["confirmed"]:
                        confirmation["signals"].append({
                            "category": category_key,
                            "indicator": indicator["name"],
                            "strength": signal_data["strength"],
                            "details": signal_data["details"]
                        })
                    
                except Exception as e:
                    indicator_result["signal_details"] = f"Error: {str(e)}"
                    indicator_result["confirmed"] = False
                
                category_result["indicators"].append(indicator_result)
                category_result["category_max"] += indicator["weight"]
                
                if signal_data["confirmed"]:
                    category_result["category_score"] += indicator["weight"] * (signal_data["strength"] / 100)
            
            max_score += category_result["category_max"]
            total_score += category_result["category_score"]
            confirmation["categories"][category_key] = category_result
        
        # Calculate overall metrics
        confirmation["overall_score"] = total_score
        confirmation["max_score"] = max_score
        
        if max_score > 0:
            confidence_percentage = (total_score / max_score) * 100
            confirmation["confidence_level"] = self.get_confidence_level(confidence_percentage)
            confirmation["recommendation"] = self.get_entry_recommendation(confidence_percentage)
        else:
            confirmation["confidence_level"] = "No Data"
            confirmation["recommendation"] = "Insufficient data for confirmation"
        
        # Generate warnings
        confirmation["warnings"] = self.generate_warnings(confirmation)
        
        return confirmation
    
    def get_confidence_level(self, percentage):
        """Get confidence level based on percentage"""
        if percentage >= 85:
            return "Very High"
        elif percentage >= 75:
            return "High"
        elif percentage >= 65:
            return "Moderate"
        elif percentage >= 55:
            return "Low"
        else:
            return "Very Low"
    
    def get_entry_recommendation(self, confidence_percentage):
        """Get entry recommendation based on confidence"""
        if confidence_percentage >= 85:
            return "ENTER NOW - Strong confirmation across multiple indicators"
        elif confidence_percentage >= 75:
            return "ENTER - Good confirmation, monitor closely"
        elif confidence_percentage >= 65:
            return "CONSIDER ENTRY - Moderate confirmation, be cautious"
        elif confidence_percentage >= 55:
            return "WAIT FOR BETTER SIGNAL - Weak confirmation, wait"
        else:
            return "DO NOT ENTER - Poor confirmation, avoid trade"
    
    def generate_warnings(self, confirmation):
        """Generate specific warnings based on confirmation analysis"""
        warnings = []
        
        # Check category weaknesses
        for category_key, category_data in confirmation["categories"].items():
            category_percentage = (category_data["category_score"] / category_data["category_max"]) * 100 if category_data["category_max"] > 0 else 0
            
            if category_percentage < 40:
                warnings.append(f"Weak {category_data['title']} confirmation ({category_percentage:.0f}%)")
            elif category_percentage < 60:
                warnings.append(f"Moderate {category_data['title']} confirmation ({category_percentage:.0f}%)")
        
        # Check specific indicator issues
        confirmed_signals = len(confirmation["signals"])
        if confirmed_signals < 3:
            warnings.append(f"Low signal count ({confirmed_signals} confirmed)")
        
        # Check overall score
        if confirmation["max_score"] > 0:
            overall_percentage = (confirmation["overall_score"] / confirmation["max_score"]) * 100
            if overall_percentage < 50:
                warnings.append("Overall confirmation below 50%")
        
        return warnings
    
    # Price Action Confirmation Methods
    def check_candlestick_patterns(self, df_daily, df_4h, df_weekly, setup_data):
        """Check for bullish candlestick patterns"""
        if len(df_daily) < 3:
            return {"strength": 0, "confirmed": False, "details": "Insufficient data"}
        
        last_candle = df_daily.iloc[-1]
        prev_candle = df_daily.iloc[-2]
        
        # Check for bullish patterns
        bullish_patterns = []
        
        # Hammer pattern
        if (last_candle['Close'] > prev_candle['Close'] and 
            (last_candle['High'] - last_candle['Low']) > 2 * abs(last_candle['Open'] - last_candle['Close'])):
            bullish_patterns.append("Hammer")
        
        # Bullish engulfing
        if (prev_candle['Close'] < prev_candle['Open'] and 
            last_candle['Close'] > last_candle['Open'] and 
            last_candle['Close'] > prev_candle['Open'] and 
            last_candle['Open'] < prev_candle['Close']):
            bullish_patterns.append("Bullish Engulfing")
        
        # Strong bullish candle
        if (last_candle['Close'] > last_candle['Open'] and 
            (last_candle['Close'] - last_candle['Open']) / last_candle['Open'] > 0.02):
            bullish_patterns.append("Strong Bullish Candle")
        
        if bullish_patterns:
            return {
                "strength": 80,
                "confirmed": True,
                "details": f"Bullish patterns: {', '.join(bullish_patterns)}"
            }
        
        return {"strength": 20, "confirmed": False, "details": "No bullish patterns detected"}
    
    def check_breakout_confirmation(self, df_daily, df_4h, df_weekly, setup_data):
        """Check for confirmed breakout"""
        if len(df_daily) < 5:
            return {"strength": 0, "confirmed": False, "details": "Insufficient data"}
        
        current_price = df_daily['Close'].iloc[-1]
        breakout_level = setup_data.get('breakout', current_price)
        
        # Check if price closed above breakout
        if current_price > breakout_level * 1.002:
            # Check for sustained breakout (not just spike)
            recent_closes = df_daily['Close'].tail(3)
            if len([c for c in recent_closes if c > breakout_level]) >= 2:
                return {
                    "strength": 90,
                    "confirmed": True,
                    "details": f"Confirmed breakout above {breakout_level:.2f}"
                }
            else:
                return {
                    "strength": 60,
                    "confirmed": True,
                    "details": f"Breakout but needs confirmation above {breakout_level:.2f}"
                }
        
        return {"strength": 10, "confirmed": False, "details": "No breakout confirmation"}
    
    def check_pullback_entry(self, df_daily, df_4h, df_weekly, setup_data):
        """Check for pullback entry opportunity"""
        if len(df_daily) < 10:
            return {"strength": 0, "confirmed": False, "details": "Insufficient data"}
        
        current_price = df_daily['Close'].iloc[-1]
        breakout_level = setup_data.get('breakout', current_price)
        support_level = setup_data.get('stop_loss', current_price * 0.95)
        
        # Check if price is pulling back to support
        if (current_price < breakout_level and 
            current_price > support_level and 
            abs(current_price - support_level) / support_level < 0.05):
            
            # Check if pullback is happening with volume decrease
            recent_volume = df_daily['Volume'].tail(3)
            avg_volume = df_daily['Volume'].tail(20).mean()
            
            if recent_volume.iloc[-1] < avg_volume * 0.8:
                return {
                    "strength": 75,
                    "confirmed": True,
                    "details": f"Pullback to support at {current_price:.2f}"
                }
        
        return {"strength": 30, "confirmed": False, "details": "No pullback entry detected"}
    
    def check_consolidation_break(self, df_daily, df_4h, df_weekly, setup_data):
        """Check for consolidation break"""
        if len(df_daily) < 15:
            return {"strength": 0, "confirmed": False, "details": "Insufficient data"}
        
        # Check for recent consolidation
        recent_prices = df_daily['Close'].tail(10)
        price_range = recent_prices.max() - recent_prices.min()
        avg_price = recent_prices.mean()
        
        current_price = df_daily['Close'].iloc[-1]
        
        # If recent range was tight and now breaking out
        if (price_range / avg_price < 0.03 and 
            current_price > recent_prices.max() * 1.01):
            return {
                "strength": 85,
                "confirmed": True,
                "details": f"Break from consolidation at {current_price:.2f}"
            }
        
        return {"strength": 25, "confirmed": False, "details": "No consolidation break"}
    
    # Volume Confirmation Methods
    def check_volume_spike(self, df_daily, df_4h, df_weekly, setup_data):
        """Check for volume spike confirmation"""
        if len(df_daily) < 20:
            return {"strength": 0, "confirmed": False, "details": "Insufficient data"}
        
        current_volume = df_daily['Volume'].iloc[-1]
        avg_volume = df_daily['Volume'].tail(20).mean()
        
        if current_volume > avg_volume * 1.5:
            return {
                "strength": 85,
                "confirmed": True,
                "details": f"Volume spike: {current_volume:.0f} vs avg {avg_volume:.0f}"
            }
        elif current_volume > avg_volume * 1.2:
            return {
                "strength": 60,
                "confirmed": True,
                "details": f"Above average volume: {current_volume:.0f}"
            }
        
        return {"strength": 20, "confirmed": False, "details": "No volume spike"}
    
    def check_volume_accumulation(self, df_daily, df_4h, df_weekly, setup_data):
        """Check for volume accumulation"""
        if len(df_daily) < 10:
            return {"strength": 0, "confirmed": False, "details": "Insufficient data"}
        
        recent_volume = df_daily['Volume'].tail(5)
        avg_volume = df_daily['Volume'].tail(20).mean()
        
        # Check if volume is consistently high
        if all(v > avg_volume * 1.1 for v in recent_volume):
            return {
                "strength": 75,
                "confirmed": True,
                "details": "Consistent high volume accumulation"
            }
        elif sum(1 for v in recent_volume if v > avg_volume) >= 3:
            return {
                "strength": 50,
                "confirmed": True,
                "details": "Moderate volume accumulation"
            }
        
        return {"strength": 25, "confirmed": False, "details": "No volume accumulation"}
    
    def check_volume_divergence(self, df_daily, df_4h, df_weekly, setup_data):
        """Check volume-price divergence"""
        if len(df_daily) < 10:
            return {"strength": 0, "confirmed": False, "details": "Insufficient data"}
        
        recent_prices = df_daily['Close'].tail(5)
        recent_volume = df_daily['Volume'].tail(5)
        
        price_trend = np.polyfit(range(5), recent_prices, 1)[0]
        volume_trend = np.polyfit(range(5), recent_volume, 1)[0]
        
        # Positive divergence (price up, volume up)
        if price_trend > 0 and volume_trend > 0:
            return {
                "strength": 70,
                "confirmed": True,
                "details": "Positive volume-price divergence"
            }
        # Negative divergence (price up, volume down)
        elif price_trend > 0 and volume_trend < -0.1:
            return {
                "strength": 30,
                "confirmed": False,
                "details": "Negative volume-price divergence"
            }
        
        return {"strength": 50, "confirmed": True, "details": "Neutral volume-price relationship"}
    
    # Momentum Confirmation Methods
    def check_rsi_confirmation(self, df_daily, df_4h, df_weekly, setup_data):
        """Check RSI confirmation"""
        if len(df_daily) < 14:
            return {"strength": 0, "confirmed": False, "details": "Insufficient data"}
        
        # Calculate RSI
        delta = df_daily['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        if 40 <= current_rsi <= 60:
            return {
                "strength": 80,
                "confirmed": True,
                "details": f"RSI in optimal range: {current_rsi:.1f}"
            }
        elif 30 <= current_rsi <= 70:
            return {
                "strength": 60,
                "confirmed": True,
                "details": f"RSI in acceptable range: {current_rsi:.1f}"
            }
        elif current_rsi > 70:
            return {
                "strength": 30,
                "confirmed": False,
                "details": f"RSI overbought: {current_rsi:.1f}"
            }
        else:
            return {
                "strength": 30,
                "confirmed": False,
                "details": f"RSI oversold: {current_rsi:.1f}"
            }
    
    def check_macd_signal(self, df_daily, df_4h, df_weekly, setup_data):
        """Check MACD signal"""
        if len(df_daily) < 26:
            return {"strength": 0, "confirmed": False, "details": "Insufficient data"}
        
        # Calculate MACD
        exp1 = df_daily['Close'].ewm(span=12).mean()
        exp2 = df_daily['Close'].ewm(span=26).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9).mean()
        
        current_macd = macd.iloc[-1]
        current_signal = signal.iloc[-1]
        prev_macd = macd.iloc[-2]
        prev_signal = signal.iloc[-2]
        
        # Bullish crossover
        if (prev_macd <= prev_signal and current_macd > current_signal):
            return {
                "strength": 75,
                "confirmed": True,
                "details": "MACD bullish crossover confirmed"
            }
        elif current_macd > current_signal:
            return {
                "strength": 50,
                "confirmed": True,
                "details": "MACD above signal line"
            }
        
        return {"strength": 25, "confirmed": False, "details": "No MACD bullish signal"}
    
    def check_ma_crossover(self, df_daily, df_4h, df_weekly, setup_data):
        """Check moving average crossover"""
        if len(df_daily) < 50:
            return {"strength": 0, "confirmed": False, "details": "Insufficient data"}
        
        ma_20 = df_daily['Close'].rolling(20).mean()
        ma_50 = df_daily['Close'].rolling(50).mean()
        
        current_price = df_daily['Close'].iloc[-1]
        current_ma20 = ma_20.iloc[-1]
        current_ma50 = ma_50.iloc[-1]
        prev_ma20 = ma_20.iloc[-2]
        prev_ma50 = ma_50.iloc[-2]
        
        # Golden cross (20 MA above 50 MA)
        if (prev_ma20 <= prev_ma50 and current_ma20 > current_ma50):
            return {
                "strength": 85,
                "confirmed": True,
                "details": "Golden cross detected (20MA > 50MA)"
            }
        elif current_ma20 > current_ma50 and current_price > current_ma20:
            return {
                "strength": 60,
                "confirmed": True,
                "details": "Price above bullish MAs"
            }
        
        return {"strength": 30, "confirmed": False, "details": "No MA bullish signal"}
    
    def check_price_momentum(self, df_daily, df_4h, df_weekly, setup_data):
        """Check price momentum"""
        if len(df_daily) < 10:
            return {"strength": 0, "confirmed": False, "details": "Insufficient data"}
        
        # Calculate momentum
        price_change_5 = (df_daily['Close'].iloc[-1] - df_daily['Close'].iloc[-6]) / df_daily['Close'].iloc[-6]
        price_change_10 = (df_daily['Close'].iloc[-1] - df_daily['Close'].iloc[-11]) / df_daily['Close'].iloc[-11]
        
        if price_change_5 > 0.02 and price_change_10 > 0.03:
            return {
                "strength": 75,
                "confirmed": True,
                "details": f"Strong momentum: 5d={price_change_5*100:.1f}%, 10d={price_change_10*100:.1f}%"
            }
        elif price_change_5 > 0 or price_change_10 > 0:
            return {
                "strength": 50,
                "confirmed": True,
                "details": f"Positive momentum: 5d={price_change_5*100:.1f}%, 10d={price_change_10*100:.1f}%"
            }
        
        return {"strength": 25, "confirmed": False, "details": "Negative momentum"}
    
    # Multi-Timeframe Confirmation Methods
    def check_4h_alignment(self, df_daily, df_4h, df_weekly, setup_data):
        """Check 4H timeframe alignment"""
        if df_4h is None or len(df_4h) < 10:
            return {"strength": 50, "confirmed": True, "details": "4H data unavailable"}
        
        current_price_4h = df_4h['Close'].iloc[-1]
        ma_20_4h = df_4h['Close'].rolling(20).mean().iloc[-1]
        
        if current_price_4h > ma_20_4h:
            return {
                "strength": 70,
                "confirmed": True,
                "details": "4H trend alignment confirmed"
            }
        
        return {"strength": 30, "confirmed": False, "details": "4H trend not aligned"}
    
    def check_weekly_alignment(self, df_daily, df_4h, df_weekly, setup_data):
        """Check weekly trend alignment"""
        if df_weekly is None or len(df_weekly) < 10:
            return {"strength": 50, "confirmed": True, "details": "Weekly data unavailable"}
        
        current_price_weekly = df_weekly['Close'].iloc[-1]
        ma_10_weekly = df_weekly['Close'].rolling(10).mean().iloc[-1]
        
        if current_price_weekly > ma_10_weekly:
            return {
                "strength": 65,
                "confirmed": True,
                "details": "Weekly trend alignment confirmed"
            }
        
        return {"strength": 35, "confirmed": False, "details": "Weekly trend not aligned"}
    
    def check_time_of_day(self, df_daily, df_4h, df_weekly, setup_data):
        """Check optimal entry timing"""
        current_time = datetime.now().hour
        
        # Optimal trading hours (9:30 AM - 3:30 PM)
        if 9 <= current_time <= 15:
            return {
                "strength": 60,
                "confirmed": True,
                "details": f"Optimal entry time: {current_time}:00"
            }
        elif 15 < current_time <= 18:
            return {
                "strength": 40,
                "confirmed": True,
                "details": f"Late entry time: {current_time}:00"
            }
        else:
            return {
                "strength": 20,
                "confirmed": False,
                "details": f"Off-hours entry: {current_time}:00"
            }

# Global instance
entry_confirmer = EntryConfirmationSystem()

def confirm_entry_signal(df_daily, df_4h, df_weekly, setup_data):
    """Convenience function for entry confirmation"""
    return entry_confirmer.confirm_entry(df_daily, df_4h, df_weekly, setup_data)

def get_entry_confidence_level(confirmation_data):
    """Get confidence level from confirmation data"""
    return confirmation_data.get("confidence_level", "Unknown")
