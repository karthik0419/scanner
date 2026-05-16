import pandas as pd
import numpy as np
import yfinance as yf

class BasicPatternAnalyzer:
    def __init__(self):
        self.pattern_descriptions = {
            "cup_handle": {
                "name": "Cup & Handle",
                "description": "Bullish continuation with U-shaped cup",
                "entry": "Buy on breakout above handle",
                "target": "Height of cup added to breakout",
                "stop_loss": "Below cup's lowest point"
            },
            "double_bottom": {
                "name": "Double Bottom",
                "description": "Bullish reversal with two similar lows",
                "entry": "Buy on breakout above middle peak",
                "target": "Previous resistance level",
                "stop_loss": "Below the lower bottom"
            },
            "double_top": {
                "name": "Double Top", 
                "description": "Bearish reversal with two similar highs",
                "entry": "Sell on breakdown below middle trough",
                "target": "Previous support level",
                "stop_loss": "Above the higher top"
            },
            "darvas_box": {
                "name": "Darvas Box",
                "description": "Consolidation breakout with defined box",
                "entry": "Buy on breakout above box high",
                "target": "Height of box added to breakout",
                "stop_loss": "Below box low"
            }
        }
    
    def analyze_basic_patterns(self, symbol):
        """Basic pattern analysis without complex charting"""
        try:
            # Fetch data
            data = yf.download(symbol, period="6mo", interval="1d", progress=False)
            if data.empty:
                return None
            
            detected_patterns = []
            
            # Simple Cup & Handle detection
            cup_handle = self.detect_basic_cup_handle(data)
            if cup_handle:
                detected_patterns.append(cup_handle)
            
            # Simple Double Bottom detection
            double_bottom = self.detect_basic_double_bottom(data)
            if double_bottom:
                detected_patterns.append(double_bottom)
            
            # Simple Double Top detection
            double_top = self.detect_basic_double_top(data)
            if double_top:
                detected_patterns.append(double_top)
            
            # Simple Darvas Box detection
            darvas_box = self.detect_basic_darvas_box(data)
            if darvas_box:
                detected_patterns.append(darvas_box)
            
            return {
                "symbol": symbol,
                "detected_patterns": detected_patterns,
                "analysis": self.generate_basic_analysis(detected_patterns)
            }
            
        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")
            return None
    
    def detect_basic_cup_handle(self, data):
        """Basic Cup & Handle detection"""
        if len(data) < 60:
            return None
        
        # Look for U-shaped formation in last 100 days
        recent_data = data.tail(100)
        
        # Find potential cup bottom
        min_price = recent_data['Low'].min()
        
        # Find cup edges
        left_edge = recent_data['High'].head(30).max()
        right_edge = recent_data['High'].tail(30).max()
        
        # Calculate cup depth
        cup_depth = (left_edge - min_price) / left_edge
        
        # Check if it's a valid cup (depth between 15-40%)
        if 0.15 <= cup_depth <= 0.40:
            # Look for handle formation
            handle_data = recent_data.tail(20)
            current_price = recent_data['Close'].iloc[-1]
            
            # Handle should be small consolidation
            price_range = handle_data['High'].max() - handle_data['Low'].min()
            avg_price = handle_data['Close'].mean()
            
            # Handle criteria: current price near recent high, consolidation
            if (current_price > left_edge * 0.9 and 
                price_range < avg_price * 0.1):
                
                return {
                    "type": "cup_handle",
                    "confidence": min(85, int(cup_depth * 100)),  # Higher depth = more confident
                    "cup_depth": f"{cup_depth*100:.1f}%",
                    "handle_level": current_price,
                    "breakout_level": current_price * 1.02,  # 2% above current
                    "target": current_price + (left_edge - min_price) * 0.8,
                    "stop_loss": min_price * 0.98
                }
        
        return None
    
    def detect_basic_double_bottom(self, data):
        """Basic Double Bottom detection"""
        if len(data) < 60:
            return None
        
        recent_data = data.tail(100)
        
        # Find two significant lows
        lows = recent_data['Low']
        
        # Find lowest points in last 80 days
        low_points = []
        for i in range(10, len(lows) - 10):
            window_min = lows.iloc[i-10:i+10].min()
            if abs(lows.iloc[i] - window_min) / window_min < 0.02:  # Within 2%
                low_points.append({
                    "price": lows.iloc[i],
                    "index": i
                })
        
        if len(low_points) >= 2:
            # Sort by price (lowest first)
            low_points.sort(key=lambda x: x["price"])
            
            first_bottom = low_points[0]
            second_bottom = low_points[1]
            
            # Check if bottoms are similar (within 3%)
            similarity = abs(first_bottom["price"] - second_bottom["price"]) / first_bottom["price"]
            
            if similarity <= 0.03:
                # Find middle peak between bottoms
                middle_data = recent_data.iloc[first_bottom["index"]:second_bottom["index"]]
                middle_peak = middle_data['High'].max()
                current_price = recent_data['Close'].iloc[-1]
                
                return {
                    "type": "double_bottom",
                    "confidence": min(80, int((1 - similarity) * 100)),  # More similar = more confident
                    "first_bottom": f"₹{first_bottom['price']:.2f}",
                    "second_bottom": f"₹{second_bottom['price']:.2f}",
                    "middle_peak": f"₹{middle_peak:.2f}",
                    "breakout_level": middle_peak,
                    "target": middle_peak * 1.08,  # 8% target
                    "stop_loss": min(first_bottom["price"], second_bottom["price"]) * 0.98
                }
        
        return None
    
    def detect_basic_double_top(self, data):
        """Basic Double Top detection"""
        if len(data) < 60:
            return None
        
        recent_data = data.tail(100)
        
        # Find two significant highs
        highs = recent_data['High']
        
        # Find highest points in last 80 days
        high_points = []
        for i in range(10, len(highs) - 10):
            window_max = highs.iloc[i-10:i+10].max()
            if abs(highs.iloc[i] - window_max) / window_max < 0.02:  # Within 2%
                high_points.append({
                    "price": highs.iloc[i],
                    "index": i
                })
        
        if len(high_points) >= 2:
            # Sort by price (highest first)
            high_points.sort(key=lambda x: x["price"], reverse=True)
            
            first_top = high_points[0]
            second_top = high_points[1]
            
            # Check if tops are similar (within 3%)
            similarity = abs(first_top["price"] - second_top["price"]) / first_top["price"]
            
            if similarity <= 0.03:
                # Find middle trough between tops
                middle_data = recent_data.iloc[first_top["index"]:second_top["index"]]
                middle_trough = middle_data['Low'].min()
                current_price = recent_data['Close'].iloc[-1]
                
                return {
                    "type": "double_top",
                    "confidence": min(80, int((1 - similarity) * 100)),
                    "first_top": f"₹{first_top['price']:.2f}",
                    "second_top": f"₹{second_top['price']:.2f}",
                    "middle_trough": f"₹{middle_trough:.2f}",
                    "breakdown_level": middle_trough,
                    "target": middle_trough * 0.92,  # 8% downside target
                    "stop_loss": max(first_top["price"], second_top["price"]) * 1.02
                }
        
        return None
    
    def detect_basic_darvas_box(self, data):
        """Basic Darvas Box detection"""
        if len(data) < 50:
            return None
        
        recent_data = data.tail(100)
        
        # Look for 4-box Darvas pattern
        highs = recent_data['High']
        lows = recent_data['Low']
        
        for i in range(10, len(highs) - 30):
            if (i+27) < len(highs):
                box_high_1 = highs.iloc[i]
                box_high_2 = highs.iloc[i+9]
                box_high_3 = highs.iloc[i+18]
                box_high_4 = highs.iloc[i+27]
                
                # Check for rising boxes
                if (box_high_2 > box_high_1 and 
                    box_high_3 > box_high_2 and 
                    box_high_4 > box_high_3):
                    
                    # Find corresponding lows
                    box_low = min(lows.iloc[i:i+28])
                    current_price = recent_data['Close'].iloc[-1]
                    
                    # Check if breaking out
                    if current_price > box_high_4:
                        return {
                            "type": "darvas_box",
                            "confidence": 75,  # Fixed confidence for Darvas
                            "box_high": f"₹{box_high_4:.2f}",
                            "box_low": f"₹{box_low:.2f}",
                            "breakout_level": current_price,
                            "target": current_price + (box_high_4 - box_low),
                            "stop_loss": box_low * 0.98
                        }
        
        return None
    
    def generate_basic_analysis(self, detected_patterns):
        """Generate basic analysis of detected patterns"""
        analysis = {
            "summary": f"Detected {len(detected_patterns)} patterns",
            "patterns": []
        }
        
        for pattern in detected_patterns:
            pattern_info = self.pattern_descriptions.get(pattern['type'], {})
            
            pattern_analysis = {
                "type": pattern_info.get('name', pattern['type']).title(),
                "confidence": f"{pattern['confidence']}%",
                "description": pattern_info.get('description', ''),
                "entry_logic": pattern_info.get('entry', ''),
                "entry_level": pattern.get('breakout_level', pattern.get('breakdown_level', 'N/A')),
                "target": pattern.get('target', 'N/A'),
                "stop_loss": pattern.get('stop_loss', 'N/A'),
                "risk_reward": self.calculate_basic_rr(pattern)
            }
            
            analysis["patterns"].append(pattern_analysis)
        
        return analysis
    
    def calculate_basic_rr(self, pattern):
        """Calculate basic risk/reward ratio"""
        try:
            entry = pattern.get('breakout_level', pattern.get('breakdown_level', 0))
            target = pattern.get('target', 0)
            stop_loss = pattern.get('stop_loss', 0)
            
            if entry <= 0 or target <= 0 or stop_loss <= 0:
                return "N/A"
            
            risk = abs(entry - stop_loss)
            reward = abs(target - entry)
            
            if risk == 0:
                return "N/A"
            
            return f"{reward/risk:.2f}:1"
            
        except:
            return "N/A"

# Global instance
basic_analyzer = BasicPatternAnalyzer()

def analyze_basic_patterns(symbol):
    """Convenience function for basic pattern analysis"""
    return basic_analyzer.analyze_basic_patterns(symbol)
