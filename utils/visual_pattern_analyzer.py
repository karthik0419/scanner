import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Arc
import yfinance as yf
import io
import base64

class VisualPatternAnalyzer:
    def __init__(self):
        self.pattern_descriptions = {
            "cup_handle": {
                "name": "Cup & Handle",
                "description": "Bullish continuation pattern with U-shaped cup followed by small handle",
                "trade_logic": "Buy on breakout above handle resistance",
                "target": "Height of cup added to breakout level",
                "stop_loss": "Below cup's lowest point"
            },
            "double_bottom": {
                "name": "Double Bottom",
                "description": "Bullish reversal pattern with two similar low points",
                "trade_logic": "Buy on breakout above middle peak",
                "target": "Previous resistance level",
                "stop_loss": "Below the lower bottom"
            },
            "double_top": {
                "name": "Double Top", 
                "description": "Bearish reversal pattern with two similar high points",
                "trade_logic": "Sell on breakdown below middle trough",
                "target": "Previous support level",
                "stop_loss": "Above the higher top"
            },
            "darvas_box": {
                "name": "Darvas Box",
                "description": "Consolidation pattern with defined box levels",
                "trade_logic": "Buy on breakout above box high",
                "target": "Height of box added to breakout",
                "stop_loss": "Below box low"
            },
            "head_shoulders": {
                "name": "Head & Shoulders",
                "description": "Bearish reversal pattern with head higher than shoulders",
                "trade_logic": "Sell on breakdown below neckline",
                "target": "Height from head to neckline",
                "stop_loss": "Above the right shoulder"
            }
        }
    
    def analyze_and_visualize_pattern(self, symbol, pattern_type="auto"):
        """Analyze stock for patterns and create visual chart with annotations"""
        try:
            # Fetch data
            data = yf.download(symbol, period="6mo", interval="1d", progress=False)
            if data.empty:
                return None
            
            # Detect patterns
            detected_patterns = self.detect_all_patterns(data)
            
            # Create visualization
            chart_data = self.create_pattern_chart(data, symbol, detected_patterns)
            
            return {
                "symbol": symbol,
                "detected_patterns": detected_patterns,
                "chart_data": chart_data,
                "analysis": self.generate_pattern_analysis(detected_patterns)
            }
            
        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")
            return None
    
    def detect_all_patterns(self, data):
        """Detect all types of patterns in the data"""
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
        
        # Head & Shoulders
        head_shoulders = self.detect_head_shoulders(data)
        if head_shoulders:
            patterns.append(head_shoulders)
        
        return patterns
    
    def detect_cup_handle(self, data):
        """Detect Cup & Handle pattern"""
        if len(data) < 60:
            return None
        
        # Look for U-shaped formation in last 100 days
        recent_data = data.tail(100)
        
        # Find potential cup bottom
        min_price = recent_data['Low'].min()
        min_idx = recent_data['Low'].idxmin()
        # Convert to integer position for indexing
        if hasattr(min_idx, 'timestamp'):
            min_pos = recent_data.index.get_loc(min_idx)
        else:
            min_pos = min_idx
        
        # Find left and right cup edges
        left_edge = recent_data.loc[:min_idx]['High'].max()
        right_edge = recent_data.loc[min_idx:]['High'].max()
        
        # Calculate cup depth
        cup_depth = (left_edge - min_price) / left_edge
        
        # Check if it's a valid cup (depth between 15-40%)
        if 0.15 <= cup_depth <= 0.40:
            # Look for handle formation
            handle_data = recent_data.tail(20)
            handle_high = handle_data['High'].max()
            handle_low = handle_data['Low'].min()
            
            # Handle should be small consolidation
            handle_height = (handle_high - handle_low) / handle_high
            
            if handle_height <= 0.15:  # Handle less than 15% of price
                return {
                    "type": "cup_handle",
                    "confidence": self.calculate_confidence(recent_data, "cup_handle"),
                    "cup_bottom": min_price,
                    "cup_left": left_edge,
                    "cup_right": right_edge,
                    "handle_high": handle_high,
                    "handle_low": handle_low,
                    "breakout_level": handle_high,
                    "target": handle_high + (left_edge - min_price),
                    "stop_loss": min_price * 0.98
                }
        
        return None
    
    def detect_double_bottom(self, data):
        """Detect Double Bottom pattern"""
        if len(data) < 60:
            return None
        
        recent_data = data.tail(100)
        
        # Find two significant lows
        lows = recent_data['Low']
        
        # Find first bottom
        first_bottom_idx = None
        first_bottom_price = None
        
        for i in range(10, len(lows) - 20):
            window_min = lows.iloc[i-10:i+10].min()
            if abs(lows.iloc[i] - window_min) / window_min < 0.01:  # Within 1%
                first_bottom_idx = lows.index[i]
                first_bottom_price = lows.iloc[i]
                break
        
        if first_bottom_price is None:
            return None
        
        # Find second bottom
        second_bottom_idx = None
        second_bottom_price = None
        
        for i in range(len(lows) - 20, len(lows)):
            window_min = lows.iloc[i-10:i+10].min()
            if abs(lows.iloc[i] - window_min) / window_min < 0.01:  # Within 1%
                second_bottom_idx = lows.index[i]
                second_bottom_price = lows.iloc[i]
                break
        
        if second_bottom_price is None:
            return None
        
        # Check if bottoms are similar (within 2%)
        similarity = abs(first_bottom_price - second_bottom_price) / first_bottom_price
        
        if similarity <= 0.02:
            # Find middle peak between bottoms
            middle_data = recent_data.loc[first_bottom_idx:second_bottom_idx]
            middle_peak = middle_data['High'].max()
            
            return {
                "type": "double_bottom",
                "confidence": self.calculate_confidence(recent_data, "double_bottom"),
                "first_bottom": first_bottom_price,
                "second_bottom": second_bottom_price,
                "middle_peak": middle_peak,
                "breakout_level": middle_peak,
                "target": middle_peak * 1.08,  # 8% target
                "stop_loss": min(first_bottom_price, second_bottom_price) * 0.98
            }
        
        return None
    
    def detect_double_top(self, data):
        """Detect Double Top pattern"""
        if len(data) < 60:
            return None
        
        recent_data = data.tail(100)
        
        # Find two significant highs
        highs = recent_data['High']
        
        # Find first top
        first_top_idx = None
        first_top_price = None
        
        for i in range(10, len(highs) - 20):
            window_max = highs.iloc[i-10:i+10].max()
            if abs(highs.iloc[i] - window_max) / window_max < 0.01:  # Within 1%
                first_top_idx = highs.index[i]
                first_top_price = highs.iloc[i]
                break
        
        if first_top_price is None:
            return None
        
        # Find second top
        second_top_idx = None
        second_top_price = None
        
        for i in range(len(highs) - 20, len(highs)):
            window_max = highs.iloc[i-10:i+10].max()
            if abs(highs.iloc[i] - window_max) / window_max < 0.01:  # Within 1%
                second_top_idx = highs.index[i]
                second_top_price = highs.iloc[i]
                break
        
        if second_top_price is None:
            return None
        
        # Check if tops are similar (within 2%)
        similarity = abs(first_top_price - second_top_price) / first_top_price
        
        if similarity <= 0.02:
            # Find middle trough between tops
            middle_data = recent_data.loc[first_top_idx:second_top_idx]
            middle_trough = middle_data['Low'].min()
            
            return {
                "type": "double_top",
                "confidence": self.calculate_confidence(recent_data, "double_top"),
                "first_top": first_top_price,
                "second_top": second_top_price,
                "middle_trough": middle_trough,
                "breakdown_level": middle_trough,
                "target": middle_trough * 0.92,  # 8% downside target
                "stop_loss": max(first_top_price, second_top_price) * 1.02
            }
        
        return None
    
    def detect_darvas_box(self, data):
        """Detect Darvas Box pattern"""
        if len(data) < 50:
            return None
        
        recent_data = data.tail(100)
        
        # Look for Darvas box formation (4 consecutive higher highs)
        highs = recent_data['High']
        lows = recent_data['Low']
        closes = recent_data['Close']
        
        for i in range(10, len(highs) - 10):
            # Check for 4-box Darvas pattern
            if (i+9 < len(highs)):
                box_high_1 = highs.iloc[i]
                box_high_2 = highs.iloc[i+3]
                box_high_3 = highs.iloc[i+6]
                box_high_4 = highs.iloc[i+9]
                
                if (box_high_2 > box_high_1 and 
                    box_high_3 > box_high_2 and 
                    box_high_4 > box_high_3):
                    
                    # Find corresponding lows
                    box_low = min(lows.iloc[i:i+10])
                    
                    # Check if price is breaking out
                    current_price = closes.iloc[-1]
                    
                    if current_price > box_high_4:
                        return {
                            "type": "darvas_box",
                            "confidence": self.calculate_confidence(recent_data, "darvas_box"),
                            "box_high": box_high_4,
                            "box_low": box_low,
                            "breakout_level": box_high_4,
                            "target": box_high_4 + (box_high_4 - box_low),
                            "stop_loss": box_low * 0.98
                        }
        
        return None
    
    def detect_head_shoulders(self, data):
        """Detect Head & Shoulders pattern"""
        if len(data) < 60:
            return None
        
        recent_data = data.tail(120)
        
        # Simplified H&S detection
        highs = recent_data['High']
        lows = recent_data['Low']
        
        # Find potential left shoulder
        left_shoulder_idx = None
        left_shoulder_price = None
        
        for i in range(20, len(highs) - 60):
            if highs.iloc[i] == highs.iloc[i-15:i+15].max():
                left_shoulder_idx = highs.index[i]
                left_shoulder_price = highs.iloc[i]
                break
        
        if left_shoulder_price is None:
            return None
        
        # Find potential head (higher than left shoulder)
        head_start = left_shoulder_idx + pd.Timedelta(days=10)
        head_data = recent_data.loc[head_start:head_start + pd.Timedelta(days=40)]
        
        head_price = head_data['High'].max()
        head_idx = head_data['High'].idxmax()
        
        if head_price <= left_shoulder_price * 1.05:  # Head should be at least 5% higher
            return None
        
        # Find right shoulder
        right_shoulder_start = head_idx + pd.Timedelta(days=10)
        right_shoulder_data = recent_data.loc[right_shoulder_start:right_shoulder_start + pd.Timedelta(days=30)]
        
        right_shoulder_price = right_shoulder_data['High'].max()
        
        if right_shoulder_price is None:
            return None
        
        # Calculate neckline
        neckline = (left_shoulder_price + right_shoulder_price) / 2
        
        return {
            "type": "head_shoulders",
            "confidence": self.calculate_confidence(recent_data, "head_shoulders"),
            "left_shoulder": left_shoulder_price,
            "head": head_price,
            "right_shoulder": right_shoulder_price,
            "neckline": neckline,
            "breakdown_level": neckline,
            "target": neckline - (head_price - neckline),
            "stop_loss": head_price * 1.02
        }
    
    def calculate_confidence(self, data, pattern_type):
        """Calculate confidence score for detected pattern"""
        # Volume confirmation
        recent_volume = data['Volume'].tail(20).mean()
        current_volume = data['Volume'].iloc[-1]
        volume_score = min(current_volume / recent_volume, 2.0) * 25
        
        # Price momentum
        returns = data['Close'].pct_change().tail(10)
        momentum_score = min(max(returns.mean() * 100, -2), 2) * 25 + 25
        
        # Pattern completion
        completion_score = 25  # Base score for detection
        
        # Pattern-specific scoring
        if pattern_type in ["cup_handle", "double_bottom"]:
            pattern_score = 25  # Bullish patterns get bonus
        elif pattern_type in ["double_top", "head_shoulders"]:
            pattern_score = 20  # Bearish patterns
        else:
            pattern_score = 22
        
        total_score = volume_score + momentum_score + completion_score + pattern_score
        return min(total_score, 100)
    
    def create_pattern_chart(self, data, symbol, detected_patterns):
        """Create chart with pattern annotations"""
        plt.style.use('default')
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Plot candlestick-like chart
        for i in range(len(data)):
            color = 'green' if data['Close'].iloc[i] >= data['Open'].iloc[i] else 'red'
            ax.plot([i, i], [data['Low'].iloc[i], data['High'].iloc[i]], 
                    color=color, linewidth=1, alpha=0.7)
            ax.plot([i-0.5, i+0.5], [data['Close'].iloc[i], data['Close'].iloc[i]], 
                    color=color, linewidth=2)
        
        # Draw detected patterns
        for pattern in detected_patterns:
            self.draw_pattern_on_chart(ax, pattern, data)
        
        # Chart formatting
        ax.set_title(f'{symbol} - Pattern Analysis', fontsize=16, fontweight='bold')
        ax.set_xlabel('Days', fontsize=12)
        ax.set_ylabel('Price (₹)', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # Add pattern legend
        pattern_names = [p['type'].replace('_', ' ').title() for p in detected_patterns]
        if pattern_names:
            ax.legend(pattern_names, loc='upper right', fontsize=10)
        
        # Save chart to base64
        buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        chart_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return chart_base64
    
    def draw_pattern_on_chart(self, ax, pattern, data):
        """Draw specific pattern on chart"""
        try:
            pattern_type = pattern['type']
            
            if pattern_type == 'cup_handle':
                # Draw cup curve
                cup_bottom_idx = data.index.get_loc(pattern['cup_bottom']) if pattern['cup_bottom'] in data.index else len(data) - 50
                
                # Cup arc
                theta = np.linspace(0, np.pi, 50)
                cup_radius = (pattern['cup_left'] - pattern['cup_bottom']) / 2
                cup_x = cup_bottom_idx + np.linspace(-30, 30, 50)
                cup_y = pattern['cup_bottom'] + cup_radius * np.sin(theta)
                ax.plot(cup_x, cup_y, 'b--', linewidth=2, alpha=0.7, label='Cup')
                
                # Handle rectangle
                handle_start_idx = len(data) - 20
                handle_start = data.index[handle_start_idx]
                ax.add_patch(plt.Rectangle((handle_start, pattern['handle_low']), 
                                       20, pattern['handle_high'] - pattern['handle_low'],
                                       fill=False, edgecolor='orange', linewidth=2, label='Handle'))
                
                # Breakout line
                ax.axhline(y=pattern['breakout_level'], color='green', linestyle='--', 
                          linewidth=2, alpha=0.8, label='Breakout')
                
            elif pattern_type == 'double_bottom':
                # Mark bottoms
                bottom_indices = []
                bottom_prices = [pattern['first_bottom'], pattern['second_bottom']]
                
                for price in bottom_prices:
                    # Find the most recent occurrence of this price
                    matching_indices = data.index[data['Low'] == price]
                    if len(matching_indices) > 0:
                        idx = matching_indices[-1]  # Most recent
                        bottom_indices.append(idx)
                
                for i, price in enumerate(bottom_prices):
                    ax.scatter(bottom_indices[i], price, color='blue', s=100, zorder=5)
                    ax.annotate('Bottom', (bottom_indices[i], price), xytext=(5, 5), 
                               textcoords='offset points', fontsize=9)
                
                # Middle peak line
                ax.axhline(y=pattern['middle_peak'], color='red', linestyle='--', 
                          linewidth=2, alpha=0.8, label='Peak')
                
            elif pattern_type == 'double_top':
                # Mark tops
                top_indices = []
                top_prices = [pattern['first_top'], pattern['second_top']]
                
                for price in top_prices:
                    # Find most recent occurrence of this price
                    matching_indices = data.index[data['High'] == price]
                    if len(matching_indices) > 0:
                        idx = matching_indices[-1]  # Most recent
                        top_indices.append(idx)
                
                for i, price in enumerate(top_prices):
                    ax.scatter(top_indices[i], price, color='red', s=100, zorder=5)
                    ax.annotate('Top', (top_indices[i], price), xytext=(5, 5), 
                               textcoords='offset points', fontsize=9)
                
                # Middle trough line
                ax.axhline(y=pattern['middle_trough'], color='green', linestyle='--', 
                          linewidth=2, alpha=0.8, label='Trough')
                
            elif pattern_type == 'darvas_box':
                # Draw box
                box_start_idx = len(data) - 30
                box_start = data.index[box_start_idx]
                ax.add_patch(plt.Rectangle((box_start, pattern['box_low']), 
                                       30, pattern['box_high'] - pattern['box_low'],
                                       fill=False, edgecolor='blue', linewidth=3, label='Darvas Box'))
                
                # Breakout line
                ax.axhline(y=pattern['breakout_level'], color='green', linestyle='--', 
                          linewidth=2, alpha=0.8, label='Breakout')
                
            elif pattern_type == 'head_shoulders':
                # Mark H&S points
                hs_prices = [pattern['left_shoulder'], pattern['head'], pattern['right_shoulder']]
                hs_labels = ['L Shoulder', 'Head', 'R Shoulder']
                hs_indices = []
                
                for price in hs_prices:
                    # Find most recent occurrence of this price in respective columns
                    if price in pattern['left_shoulder']:
                        matching_indices = data.index[data['High'] == price]
                    elif price in pattern['head']:
                        matching_indices = data.index[data['High'] == price]
                    elif price in pattern['right_shoulder']:
                        matching_indices = data.index[data['High'] == price]
                    else:
                        matching_indices = []
                    
                    if len(matching_indices) > 0:
                        idx = matching_indices[-1]  # Most recent
                        hs_indices.append(idx)
                        ax.scatter(idx, price, color='red', s=100, zorder=5)
                        ax.annotate(hs_labels[hs_prices.index(price)], (idx, price), xytext=(5, 5), 
                                   textcoords='offset points', fontsize=9)
                
                # Neckline
                ax.axhline(y=pattern['neckline'], color='blue', linestyle='--', 
                          linewidth=2, alpha=0.8, label='Neckline')
                
        except Exception as e:
            print(f"Error drawing pattern: {e}")
    
    def generate_pattern_analysis(self, detected_patterns):
        """Generate detailed analysis of detected patterns"""
        analysis = {
            "summary": f"Detected {len(detected_patterns)} patterns",
            "patterns": []
        }
        
        for pattern in detected_patterns:
            pattern_info = self.pattern_descriptions.get(pattern['type'], {})
            
            pattern_analysis = {
                "type": pattern['type'].replace('_', ' ').title(),
                "confidence": f"{pattern['confidence']:.1f}%",
                "description": pattern_info.get('description', ''),
                "trade_logic": pattern_info.get('trade_logic', ''),
                "entry_level": pattern.get('breakout_level', pattern.get('breakdown_level', 'N/A')),
                "target": pattern.get('target', 'N/A'),
                "stop_loss": pattern.get('stop_loss', 'N/A'),
                "risk_reward": self.calculate_rr(pattern)
            }
            
            analysis["patterns"].append(pattern_analysis)
        
        return analysis
    
    def calculate_rr(self, pattern):
        """Calculate risk/reward ratio"""
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
visual_analyzer = VisualPatternAnalyzer()

def analyze_visual_patterns(symbol, pattern_type="auto"):
    """Convenience function for visual pattern analysis"""
    return visual_analyzer.analyze_and_visualize_pattern(symbol, pattern_type)

def create_pattern_chart_with_annotations(data, symbol, patterns):
    """Convenience function for chart creation"""
    return visual_analyzer.create_pattern_chart(data, symbol, patterns)
