import pandas as pd
import numpy as np
import yfinance as yf

class SimpleVisualPatterns:
    def __init__(self):
        self.pattern_info = {
            "cup_handle": {
                "name": "Cup & Handle",
                "description": "Bullish continuation with U-shaped cup and handle",
                "trade_logic": "Buy on breakout above handle resistance",
                "target": "Height of cup from bottom to handle",
                "stop_loss": "Below cup's lowest point"
            },
            "double_bottom": {
                "name": "Double Bottom",
                "description": "Bullish reversal with two similar low points",
                "trade_logic": "Buy on breakout above middle peak",
                "target": "Previous resistance level + 8%",
                "stop_loss": "Below the lower bottom"
            },
            "double_top": {
                "name": "Double Top",
                "description": "Bearish reversal with two similar high points",
                "trade_logic": "Sell on breakdown below middle trough",
                "target": "Previous support level - 8%",
                "stop_loss": "Above the higher top"
            },
            "darvas_box": {
                "name": "Darvas Box",
                "description": "Consolidation breakout with defined box levels",
                "trade_logic": "Buy on breakout above box high",
                "target": "Height of box added to breakout",
                "stop_loss": "Below box low"
            }
        }
    
    def analyze_patterns(self, symbol):
        """Analyze patterns for a stock symbol"""
        try:
            # Fetch data
            data = yf.download(symbol, period="6mo", interval="1d", progress=False)
            if data.empty:
                return None
            
            detected_patterns = []
            
            # Detect patterns
            cup_handle = self.detect_cup_handle(data)
            if cup_handle:
                detected_patterns.append(cup_handle)
            
            double_bottom = self.detect_double_bottom(data)
            if double_bottom:
                detected_patterns.append(double_bottom)
            
            double_top = self.detect_double_top(data)
            if double_top:
                detected_patterns.append(double_top)
            
            darvas_box = self.detect_darvas_box(data)
            if darvas_box:
                detected_patterns.append(darvas_box)
            
            return {
                "symbol": symbol,
                "detected_patterns": detected_patterns,
                "analysis": self.generate_analysis(detected_patterns)
            }
            
        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")
            return None
    
    def detect_cup_handle(self, data):
        """Detect Cup & Handle pattern"""
        if len(data) < 60:
            return None
        
        # Use recent data for pattern detection
        recent_data = data.tail(100)
        
        # Find potential cup bottom
        min_price = float(recent_data['Low'].min())
        
        # Find cup edges
        left_edge = float(recent_data['High'].head(30).max())
        right_edge = float(recent_data['High'].tail(30).max())
        
        # Calculate cup depth
        if left_edge > 0:
            cup_depth = (left_edge - min_price) / left_edge
        
            # Valid cup depth: 15-40%
            if 0.15 <= cup_depth <= 0.40:
                # Look for handle formation
                handle_data = recent_data.tail(20)
                current_price = float(recent_data['Close'].iloc[-1])
                
                # Handle criteria: small consolidation
                price_range = float(handle_data['High'].max() - handle_data['Low'].min())
                avg_price = float(handle_data['Close'].mean())
                
                if (current_price > left_edge * 0.9 and 
                    price_range < avg_price * 0.1):
                    
                    confidence = min(85, int(cup_depth * 100))
                    
                    return {
                        "type": "cup_handle",
                        "confidence": confidence,
                        "cup_depth": f"{cup_depth*100:.1f}%",
                        "breakout_level": current_price * 1.02,
                        "target": current_price + (left_edge - min_price) * 0.8,
                        "stop_loss": min_price * 0.98,
                        "risk_reward": self.calculate_rr(current_price, current_price * 1.02, current_price + (left_edge - min_price) * 0.8, min_price * 0.98)
                    }
        
        return None
    
    def detect_double_bottom(self, data):
        """Detect Double Bottom pattern"""
        if len(data) < 60:
            return None
        
        recent_data = data.tail(100)
        lows = recent_data['Low']
        
        # Find two significant lows
        low_points = []
        for i in range(10, len(lows) - 10):
            window_min = float(lows.iloc[i-10:i+10].min())
            current_low = float(lows.iloc[i])
            if abs(current_low - window_min) / window_min < 0.02:
                low_points.append(current_low)
        
        if len(low_points) >= 2:
            # Get two lowest points
            low_points = sorted(low_points)[:2]
            first_bottom = low_points[0]
            second_bottom = low_points[1]
            
            # Check similarity (within 3%)
            similarity = abs(first_bottom - second_bottom) / first_bottom
            
            if similarity <= 0.03:
                # Find middle peak
                middle_data = recent_data.tail(50)
                middle_peak = float(middle_data['High'].max())
                current_price = float(recent_data['Close'].iloc[-1])
                
                confidence = min(80, int((1 - similarity) * 100))
                
                return {
                    "type": "double_bottom",
                    "confidence": confidence,
                    "first_bottom": f"₹{first_bottom:.2f}",
                    "second_bottom": f"₹{second_bottom:.2f}",
                    "middle_peak": f"₹{middle_peak:.2f}",
                    "breakout_level": middle_peak,
                    "target": middle_peak * 1.08,
                    "stop_loss": min(first_bottom, second_bottom) * 0.98,
                    "risk_reward": self.calculate_rr(current_price, middle_peak, middle_peak * 1.08, min(first_bottom, second_bottom) * 0.98)
                }
        
        return None
    
    def detect_double_top(self, data):
        """Detect Double Top pattern"""
        if len(data) < 60:
            return None
        
        recent_data = data.tail(100)
        highs = recent_data['High']
        
        # Find two significant highs
        high_points = []
        for i in range(10, len(highs) - 10):
            window_max = float(highs.iloc[i-10:i+10].max())
            current_high = float(highs.iloc[i])
            if abs(current_high - window_max) / window_max < 0.02:
                high_points.append(current_high)
        
        if len(high_points) >= 2:
            # Get two highest points
            high_points = sorted(high_points, reverse=True)[:2]
            first_top = high_points[0]
            second_top = high_points[1]
            
            # Check similarity (within 3%)
            similarity = abs(first_top - second_top) / first_top
            
            if similarity <= 0.03:
                # Find middle trough
                middle_data = recent_data.tail(50)
                middle_trough = float(middle_data['Low'].min())
                current_price = float(recent_data['Close'].iloc[-1])
                
                confidence = min(80, int((1 - similarity) * 100))
                
                return {
                    "type": "double_top",
                    "confidence": confidence,
                    "first_top": f"₹{first_top:.2f}",
                    "second_top": f"₹{second_top:.2f}",
                    "middle_trough": f"₹{middle_trough:.2f}",
                    "breakdown_level": middle_trough,
                    "target": middle_trough * 0.92,
                    "stop_loss": max(first_top, second_top) * 1.02,
                    "risk_reward": self.calculate_rr(current_price, middle_trough, middle_trough * 0.92, max(first_top, second_top) * 1.02)
                }
        
        return None
    
    def detect_darvas_box(self, data):
        """Detect Darvas Box pattern"""
        if len(data) < 50:
            return None
        
        recent_data = data.tail(100)
        highs = recent_data['High']
        lows = recent_data['Low']
        
        # Look for 4-box Darvas pattern
        for i in range(10, len(highs) - 30):
            if (i+27) < len(highs):
                box_high_1 = float(highs.iloc[i])
                box_high_2 = float(highs.iloc[i+9])
                box_high_3 = float(highs.iloc[i+18])
                box_high_4 = float(highs.iloc[i+27])
                
                # Check for rising boxes
                if (box_high_2 > box_high_1 and 
                    box_high_3 > box_high_2 and 
                    box_high_4 > box_high_3):
                    
                    # Find corresponding lows
                    box_low = float(min(lows.iloc[i:i+28]))
                    current_price = float(recent_data['Close'].iloc[-1])
                    
                    # Check if breaking out
                    if current_price > box_high_4:
                        return {
                            "type": "darvas_box",
                            "confidence": 75,
                            "box_high": f"₹{box_high_4:.2f}",
                            "box_low": f"₹{box_low:.2f}",
                            "breakout_level": current_price,
                            "target": current_price + (box_high_4 - box_low),
                            "stop_loss": box_low * 0.98,
                            "risk_reward": self.calculate_rr(current_price, current_price, current_price + (box_high_4 - box_low), box_low * 0.98)
                        }
        
        return None
    
    def calculate_rr(self, current_price, entry, target, stop_loss):
        """Calculate risk/reward ratio"""
        try:
            risk = abs(entry - stop_loss)
            reward = abs(target - entry)
            
            if risk == 0:
                return "N/A"
            
            return f"{reward/risk:.2f}:1"
        except:
            return "N/A"
    
    def generate_analysis(self, detected_patterns):
        """Generate detailed pattern analysis"""
        analysis = {
            "summary": f"Detected {len(detected_patterns)} patterns",
            "patterns": []
        }
        
        for pattern in detected_patterns:
            pattern_info = self.pattern_info.get(pattern['type'], {})
            
            pattern_analysis = {
                "type": pattern_info.get('name', pattern['type']).title(),
                "confidence": f"{pattern['confidence']}%",
                "description": pattern_info.get('description', ''),
                "trade_logic": pattern_info.get('trade_logic', ''),
                "entry_level": pattern.get('breakout_level', pattern.get('breakdown_level', 'N/A')),
                "target": pattern.get('target', 'N/A'),
                "stop_loss": pattern.get('stop_loss', 'N/A'),
                "risk_reward": pattern.get('risk_reward', 'N/A')
            }
            
            analysis["patterns"].append(pattern_analysis)
        
        return analysis

# Global instance
simple_visual = SimpleVisualPatterns()

def analyze_simple_visual_patterns(symbol):
    """Convenience function for simple visual pattern analysis"""
    return simple_visual.analyze_patterns(symbol)
