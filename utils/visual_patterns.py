import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
import base64

class VisualPatternSystem:
    def __init__(self):
        self.pattern_library = {
            "cup_handle": {
                "name": "Cup & Handle",
                "description": "Bullish continuation with U-shaped cup and handle",
                "trade_logic": "Buy on breakout above handle resistance",
                "target_calculation": "Height of cup from bottom to handle",
                "stop_loss": "Below cup's lowest point"
            },
            "double_bottom": {
                "name": "Double Bottom",
                "description": "Bullish reversal with two similar low points",
                "trade_logic": "Buy on breakout above middle peak",
                "target_calculation": "Previous resistance level + 8%",
                "stop_loss": "Below the lower bottom"
            },
            "double_top": {
                "name": "Double Top",
                "description": "Bearish reversal with two similar high points",
                "trade_logic": "Sell on breakdown below middle trough",
                "target_calculation": "Previous support level - 8%",
                "stop_loss": "Above the higher top"
            },
            "darvas_box": {
                "name": "Darvas Box",
                "description": "Consolidation breakout with defined box levels",
                "trade_logic": "Buy on breakout above box high",
                "target_calculation": "Height of box added to breakout",
                "stop_loss": "Below box low"
            }
        }
    
    def analyze_and_visualize(self, symbol):
        """Complete pattern analysis with visual representation"""
        try:
            # Fetch 6 months of data
            data = yf.download(symbol, period="6mo", interval="1d", progress=False)
            if data.empty:
                return None
            
            # Detect patterns
            patterns = self.detect_all_patterns(data)
            
            # Create visualization
            chart_data = self.create_pattern_chart(data, symbol, patterns)
            
            # Generate detailed analysis
            analysis = self.generate_pattern_report(patterns)
            
            return {
                "symbol": symbol,
                "patterns": patterns,
                "chart": chart_data,
                "analysis": analysis,
                "summary": f"Found {len(patterns)} patterns in {symbol}"
            }
            
        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")
            return None
    
    def detect_all_patterns(self, data):
        """Detect all chart patterns"""
        patterns = []
        
        # Cup & Handle
        cup_handle = self.detect_cup_handle(data)
        if cup_handle:
            patterns.append(cup_handle)
        
        # Double Bottom
        double_bottom = self.detect_double_bottom(data)
        if double_bottom:
            patterns.append(double_bottom)
        
        # Double Top
        double_top = self.detect_double_top(data)
        if double_top:
            patterns.append(double_top)
        
        # Darvas Box
        darvas_box = self.detect_darvas_box(data)
        if darvas_box:
            patterns.append(darvas_box)
        
        return patterns
    
    def detect_cup_handle(self, data):
        """Detect Cup & Handle pattern"""
        if len(data) < 60:
            return None
        
        # Use last 100 days for pattern detection
        recent_data = data.tail(100)
        
        # Find potential cup bottom
        min_price = recent_data['Low'].min()
        min_idx = recent_data['Low'].idxmin()
        
        # Find cup edges (higher points around the bottom)
        left_edge = recent_data['High'].head(30).max()
        right_edge = recent_data['High'].tail(30).max()
        
        # Calculate cup depth
        if left_edge > 0:
            cup_depth = (left_edge - min_price) / left_edge
        
            # Valid cup depth: 15-40%
            if 0.15 <= cup_depth <= 0.40:
                # Look for handle formation
                handle_data = recent_data.tail(20)
                current_price = recent_data['Close'].iloc[-1]
                
                # Handle criteria: small consolidation
                price_range = handle_data['High'].max() - handle_data['Low'].min()
                avg_price = handle_data['Close'].mean()
                
                if (current_price > left_edge * 0.9 and 
                    price_range < avg_price * 0.1):
                    
                    confidence = min(85, int(cup_depth * 100))
                    
                    return {
                        "type": "cup_handle",
                        "confidence": confidence,
                        "cup_depth": f"{cup_depth*100:.1f}%",
                        "cup_bottom": min_price,
                        "cup_left": left_edge,
                        "cup_right": right_edge,
                        "handle_level": current_price,
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
            window_min = lows.iloc[i-10:i+10].min()
            if abs(lows.iloc[i] - window_min) / window_min < 0.02:
                low_points.append(lows.iloc[i])
        
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
                middle_peak = middle_data['High'].max()
                current_price = recent_data['Close'].iloc[-1]
                
                confidence = min(80, int((1 - similarity) * 100))
                
                return {
                    "type": "double_bottom",
                    "confidence": confidence,
                    "first_bottom": first_bottom,
                    "second_bottom": second_bottom,
                    "middle_peak": middle_peak,
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
            window_max = highs.iloc[i-10:i+10].max()
            if abs(highs.iloc[i] - window_max) / window_max < 0.02:
                high_points.append(highs.iloc[i])
        
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
                middle_trough = middle_data['Low'].min()
                current_price = recent_data['Close'].iloc[-1]
                
                confidence = min(80, int((1 - similarity) * 100))
                
                return {
                    "type": "double_top",
                    "confidence": confidence,
                    "first_top": first_top,
                    "second_top": second_top,
                    "middle_trough": middle_trough,
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
                            "confidence": 75,
                            "box_high": box_high_4,
                            "box_low": box_low,
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
    
    def create_pattern_chart(self, data, symbol, patterns):
        """Create chart with pattern annotations"""
        plt.style.use('default')
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Plot price data
        ax.plot(data.index, data['Close'], label='Close Price', linewidth=2, color='blue')
        ax.fill_between(data.index, data['Low'], data['High'], alpha=0.1, color='gray', label='Price Range')
        
        # Draw patterns
        for pattern in patterns:
            self.draw_pattern(ax, pattern, data)
        
        # Chart formatting
        ax.set_title(f'{symbol} - Pattern Analysis', fontsize=16, fontweight='bold')
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Price (₹)', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper right')
        
        # Save to base64
        buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        chart_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return chart_base64
    
    def draw_pattern(self, ax, pattern, data):
        """Draw specific pattern on chart"""
        try:
            pattern_type = pattern['type']
            
            if pattern_type == 'cup_handle':
                # Draw cup arc
                cup_bottom = pattern['cup_bottom']
                cup_left = pattern['cup_left']
                cup_right = pattern['cup_right']
                
                # Simple cup visualization
                cup_points = 50
                theta = np.linspace(0, np.pi, cup_points)
                cup_radius = (cup_left - cup_bottom) / 2
                cup_x = np.linspace(len(data) - 80, len(data) - 20, cup_points)
                cup_y = cup_bottom + cup_radius * np.sin(theta)
                
                ax.plot(cup_x, cup_y, 'r--', linewidth=2, label='Cup & Handle')
                ax.axhline(y=pattern['breakout_level'], color='green', linestyle='--', alpha=0.7)
                
            elif pattern_type == 'double_bottom':
                # Mark bottoms
                ax.axhline(y=pattern['first_bottom'], color='blue', linestyle='--', alpha=0.7, label='Double Bottom')
                ax.axhline(y=pattern['second_bottom'], color='blue', linestyle='--', alpha=0.7)
                ax.axhline(y=pattern['breakout_level'], color='green', linestyle='--', alpha=0.7)
                
            elif pattern_type == 'double_top':
                # Mark tops
                ax.axhline(y=pattern['first_top'], color='red', linestyle='--', alpha=0.7, label='Double Top')
                ax.axhline(y=pattern['second_top'], color='red', linestyle='--', alpha=0.7)
                ax.axhline(y=pattern['breakdown_level'], color='green', linestyle='--', alpha=0.7)
                
            elif pattern_type == 'darvas_box':
                # Draw box
                box_start = len(data) - 30
                ax.add_patch(plt.Rectangle((box_start, pattern['box_low']), 
                                       30, pattern['box_high'] - pattern['box_low'],
                                       fill=False, edgecolor='blue', linewidth=2, label='Darvas Box'))
                ax.axhline(y=pattern['breakout_level'], color='green', linestyle='--', alpha=0.7)
                
        except Exception as e:
            print(f"Error drawing pattern: {e}")
    
    def generate_pattern_report(self, patterns):
        """Generate detailed pattern analysis report"""
        report = {
            "summary": f"Detected {len(patterns)} patterns",
            "patterns": []
        }
        
        for pattern in patterns:
            pattern_info = self.pattern_library.get(pattern['type'], {})
            
            pattern_report = {
                "type": pattern_info.get('name', pattern['type']).title(),
                "confidence": f"{pattern['confidence']}%",
                "description": pattern_info.get('description', ''),
                "trade_logic": pattern_info.get('trade_logic', ''),
                "entry_level": pattern.get('breakout_level', pattern.get('breakdown_level', 'N/A')),
                "target": pattern.get('target', 'N/A'),
                "stop_loss": pattern.get('stop_loss', 'N/A'),
                "risk_reward": pattern.get('risk_reward', 'N/A'),
                "key_levels": self.get_key_levels(pattern)
            }
            
            report["patterns"].append(pattern_report)
        
        return report
    
    def get_key_levels(self, pattern):
        """Extract key levels for the pattern"""
        levels = []
        
        if pattern['type'] == 'cup_handle':
            levels.append(f"Cup Bottom: ₹{pattern['cup_bottom']:.2f}")
            levels.append(f"Handle Level: ₹{pattern['handle_level']:.2f}")
            levels.append(f"Breakout: ₹{pattern['breakout_level']:.2f}")
            
        elif pattern['type'] == 'double_bottom':
            levels.append(f"First Bottom: ₹{pattern['first_bottom']:.2f}")
            levels.append(f"Second Bottom: ₹{pattern['second_bottom']:.2f}")
            levels.append(f"Middle Peak: ₹{pattern['middle_peak']:.2f}")
            
        elif pattern['type'] == 'double_top':
            levels.append(f"First Top: ₹{pattern['first_top']:.2f}")
            levels.append(f"Second Top: ₹{pattern['second_top']:.2f}")
            levels.append(f"Middle Trough: ₹{pattern['middle_trough']:.2f}")
            
        elif pattern['type'] == 'darvas_box':
            levels.append(f"Box High: ₹{pattern['box_high']:.2f}")
            levels.append(f"Box Low: ₹{pattern['box_low']:.2f}")
            levels.append(f"Breakout: ₹{pattern['breakout_level']:.2f}")
        
        return levels

# Global instance
visual_system = VisualPatternSystem()

def analyze_visual_patterns(symbol):
    """Convenience function for visual pattern analysis"""
    return visual_system.analyze_and_visualize(symbol)
