import pandas as pd
import numpy as np
from datetime import datetime

class VerificationTools:
    def __init__(self):
        self.checklist_items = self.get_checklist_template()
    
    def get_checklist_template(self):
        """Get comprehensive verification checklist"""
        return {
            "pattern_quality": {
                "title": "Pattern Quality Check",
                "items": [
                    {
                        "id": "pq1",
                        "question": "Is the pattern structure clearly visible?",
                        "weight": 15,
                        "options": ["Yes", "No", "Partially"],
                        "scores": {"Yes": 15, "Partially": 8, "No": 0}
                    },
                    {
                        "id": "pq2", 
                        "question": "Are the pattern proportions correct?",
                        "weight": 12,
                        "options": ["Yes", "No", "Mostly"],
                        "scores": {"Yes": 12, "Mostly": 8, "No": 0}
                    },
                    {
                        "id": "pq3",
                        "question": "Is there proper volume confirmation?",
                        "weight": 10,
                        "options": ["Strong", "Moderate", "Weak", "None"],
                        "scores": {"Strong": 10, "Moderate": 6, "Weak": 3, "None": 0}
                    },
                    {
                        "id": "pq4",
                        "question": "Are support/resistance levels well-defined?",
                        "weight": 13,
                        "options": ["Very Clear", "Clear", "Fuzzy", "Unclear"],
                        "scores": {"Very Clear": 13, "Clear": 10, "Fuzzy": 5, "Unclear": 0}
                    }
                ]
            },
            "market_context": {
                "title": "Market Context Analysis",
                "items": [
                    {
                        "id": "mc1",
                        "question": "Is sector trend aligned with pattern?",
                        "weight": 12,
                        "options": ["Strongly Aligned", "Aligned", "Neutral", "Conflicting"],
                        "scores": {"Strongly Aligned": 12, "Aligned": 9, "Neutral": 5, "Conflicting": 0}
                    },
                    {
                        "id": "mc2",
                        "question": "Are market conditions favorable?",
                        "weight": 10,
                        "options": ["Very Favorable", "Favorable", "Neutral", "Unfavorable"],
                        "scores": {"Very Favorable": 10, "Favorable": 7, "Neutral": 4, "Unfavorable": 0}
                    },
                    {
                        "id": "mc3",
                        "question": "Is there any major news affecting the stock?",
                        "weight": 8,
                        "options": ["None", "Minor", "Significant", "Major"],
                        "scores": {"None": 8, "Minor": 5, "Significant": 2, "Major": 0}
                    },
                    {
                        "id": "mc4",
                        "question": "Is index correlation positive?",
                        "weight": 7,
                        "options": ["Strong", "Moderate", "Weak", "Negative"],
                        "scores": {"Strong": 7, "Moderate": 5, "Weak": 3, "Negative": 0}
                    }
                ]
            },
            "risk_management": {
                "title": "Risk Management Check",
                "items": [
                    {
                        "id": "rm1",
                        "question": "Is stop loss placement logical?",
                        "weight": 15,
                        "options": ["Excellent", "Good", "Acceptable", "Poor"],
                        "scores": {"Excellent": 15, "Good": 12, "Acceptable": 8, "Poor": 0}
                    },
                    {
                        "id": "rm2",
                        "question": "Is risk/reward ratio acceptable?",
                        "weight": 12,
                        "options": [">2:1", "1.5-2:1", "1-1.5:1", "<1:1"],
                        "scores": {">2:1": 12, "1.5-2:1": 10, "1-1.5:1": 6, "<1:1": 0}
                    },
                    {
                        "id": "rm3",
                        "question": "Is position size appropriate?",
                        "weight": 10,
                        "options": ["Conservative", "Moderate", "Aggressive", "Very Aggressive"],
                        "scores": {"Conservative": 10, "Moderate": 8, "Aggressive": 5, "Very Aggressive": 0}
                    },
                    {
                        "id": "rm4",
                        "question": "Is maximum risk < 2% of capital?",
                        "weight": 8,
                        "options": ["Yes", "No", "Unsure"],
                        "scores": {"Yes": 8, "No": 0, "Unsure": 2}
                    }
                ]
            },
            "technical_confirmation": {
                "title": "Technical Confirmation",
                "items": [
                    {
                        "id": "tc1",
                        "question": "Are moving averages aligned?",
                        "weight": 10,
                        "options": ["Strongly", "Moderately", "Weakly", "Not"],
                        "scores": {"Strongly": 10, "Moderately": 7, "Weakly": 4, "Not": 0}
                    },
                    {
                        "id": "tc2",
                        "question": "Is momentum indicator positive?",
                        "weight": 8,
                        "options": ["Strong", "Moderate", "Weak", "Negative"],
                        "scores": {"Strong": 8, "Moderate": 6, "Weak": 3, "Negative": 0}
                    },
                    {
                        "id": "tc3",
                        "question": "Is volatility normal?",
                        "weight": 6,
                        "options": ["Normal", "Slightly High", "High", "Extreme"],
                        "scores": {"Normal": 6, "Slightly High": 4, "High": 2, "Extreme": 0}
                    },
                    {
                        "id": "tc4",
                        "question": "Are there no conflicting patterns?",
                        "weight": 7,
                        "options": ["None", "Minor", "Significant", "Major"],
                        "scores": {"None": 7, "Minor": 4, "Significant": 2, "Major": 0}
                    }
                ]
            }
        }
    
    def generate_checklist(self, setup_data):
        """Generate checklist for a specific setup"""
        checklist = {
            "setup_info": setup_data,
            "categories": {},
            "total_score": 0,
            "max_score": 0,
            "overall_rating": "",
            "recommendation": ""
        }
        
        total_score = 0
        max_score = 0
        
        for category_key, category_data in self.checklist_items.items():
            category_result = {
                "title": category_data["title"],
                "items": [],
                "category_score": 0,
                "category_max": 0
            }
            
            for item in category_data["items"]:
                item_result = {
                    "id": item["id"],
                    "question": item["question"],
                    "weight": item["weight"],
                    "options": item["options"],
                    "selected": "",
                    "score": 0
                }
                
                category_result["items"].append(item_result)
                category_result["category_max"] += item["weight"]
            
            max_score += category_result["category_max"]
            checklist["categories"][category_key] = category_result
        
        checklist["total_score"] = total_score
        checklist["max_score"] = max_score
        checklist["overall_rating"] = self.calculate_rating(total_score, max_score)
        checklist["recommendation"] = self.get_recommendation(total_score, max_score)
        
        return checklist
    
    def calculate_rating(self, score, max_score):
        """Calculate overall rating based on score"""
        if max_score == 0:
            return "No Data"
        
        percentage = (score / max_score) * 100
        
        if percentage >= 85:
            return "Excellent (A+)"
        elif percentage >= 75:
            return "Very Good (A)"
        elif percentage >= 65:
            return "Good (B+)"
        elif percentage >= 55:
            return "Average (B)"
        elif percentage >= 45:
            return "Below Average (C+)"
        elif percentage >= 35:
            return "Poor (C)"
        else:
            return "Very Poor (D)"
    
    def get_recommendation(self, score, max_score):
        """Get trading recommendation based on score"""
        if max_score == 0:
            return "Complete the checklist first"
        
        percentage = (score / max_score) * 100
        
        if percentage >= 85:
            return "Strong Buy - High confidence setup"
        elif percentage >= 75:
            return "Buy - Good setup with proper risk management"
        elif percentage >= 65:
            return "Consider - Moderate setup, be cautious"
        elif percentage >= 55:
            return "Wait - Setup needs more confirmation"
        elif percentage >= 45:
            return "Avoid - Too many red flags"
        else:
            return "Strong Avoid - High risk setup"
    
    def analyze_setup_strength(self, df, setup_data):
        """Analyze setup strength using technical indicators"""
        analysis = {
            "trend_strength": self.calculate_trend_strength(df),
            "volume_confirmation": self.check_volume_confirmation(df),
            "support_resistance": self.analyze_support_resistance(df, setup_data),
            "momentum": self.calculate_momentum(df),
            "volatility": self.analyze_volatility(df),
            "overall_strength": 0
        }
        
        # Calculate overall strength score
        analysis["overall_strength"] = (
            analysis["trend_strength"] * 0.25 +
            analysis["volume_confirmation"] * 0.20 +
            analysis["support_resistance"] * 0.25 +
            analysis["momentum"] * 0.15 +
            analysis["volatility"] * 0.15
        )
        
        return analysis
    
    def calculate_trend_strength(self, df):
        """Calculate trend strength using multiple indicators"""
        if len(df) < 20:
            return 50  # Neutral
        
        # Moving averages
        ma_20 = df['Close'].rolling(20).mean().iloc[-1]
        ma_50 = df['Close'].rolling(50).mean().iloc[-1]
        current_price = df['Close'].iloc[-1]
        
        trend_score = 50  # Base score
        
        # Price vs MA relationship
        if current_price > ma_20 > ma_50:
            trend_score += 25
        elif current_price > ma_20:
            trend_score += 15
        elif current_price < ma_20 < ma_50:
            trend_score -= 25
        elif current_price < ma_20:
            trend_score -= 15
        
        # MA slope
        ma_20_slope = np.polyfit(range(20), df['Close'].tail(20), 1)[0]
        if ma_20_slope > 0:
            trend_score += 15
        else:
            trend_score -= 15
        
        return max(0, min(100, trend_score))
    
    def check_volume_confirmation(self, df):
        """Check volume confirmation for the setup"""
        if len(df) < 10:
            return 50
        
        recent_volume = df['Volume'].tail(5)
        avg_volume = df['Volume'].tail(20).mean()
        current_volume = df['Volume'].iloc[-1]
        
        volume_score = 50  # Base score
        
        # Volume spike
        if current_volume > avg_volume * 1.5:
            volume_score += 30
        elif current_volume > avg_volume * 1.2:
            volume_score += 15
        elif current_volume > avg_volume:
            volume_score += 5
        
        # Volume trend
        volume_trend = np.polyfit(range(5), recent_volume, 1)[0]
        if volume_trend > 0:
            volume_score += 20
        else:
            volume_score -= 10
        
        return max(0, min(100, volume_score))
    
    def analyze_support_resistance(self, df, setup_data):
        """Analyze support/resistance levels"""
        if len(df) < 20:
            return 50
        
        current_price = df['Close'].iloc[-1]
        recent_highs = df['High'].tail(20)
        recent_lows = df['Low'].tail(20)
        
        resistance_level = setup_data.get('breakout', current_price)
        support_level = setup_data.get('stop_loss', current_price * 0.95)
        
        sr_score = 50  # Base score
        
        # Resistance quality
        resistance_touches = sum(1 for high in recent_highs if abs(high - resistance_level) / resistance_level < 0.02)
        if resistance_touches >= 3:
            sr_score += 25
        elif resistance_touches >= 2:
            sr_score += 15
        elif resistance_touches >= 1:
            sr_score += 5
        
        # Support quality
        support_touches = sum(1 for low in recent_lows if abs(low - support_level) / support_level < 0.02)
        if support_touches >= 3:
            sr_score += 25
        elif support_touches >= 2:
            sr_score += 15
        elif support_touches >= 1:
            sr_score += 5
        
        return max(0, min(100, sr_score))
    
    def calculate_momentum(self, df):
        """Calculate momentum indicators"""
        if len(df) < 14:
            return 50
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        momentum_score = 50  # Base score
        
        # RSI based momentum
        if 40 <= current_rsi <= 60:
            momentum_score += 20
        elif 30 <= current_rsi <= 70:
            momentum_score += 10
        else:
            momentum_score -= 10
        
        # Price momentum
        price_change_5 = (df['Close'].iloc[-1] - df['Close'].iloc[-6]) / df['Close'].iloc[-6]
        price_change_10 = (df['Close'].iloc[-1] - df['Close'].iloc[-11]) / df['Close'].iloc[-11]
        
        if price_change_5 > 0.02 and price_change_10 > 0.03:
            momentum_score += 30
        elif price_change_5 > 0 or price_change_10 > 0:
            momentum_score += 15
        else:
            momentum_score -= 15
        
        return max(0, min(100, momentum_score))
    
    def analyze_volatility(self, df):
        """Analyze volatility for setup quality"""
        if len(df) < 20:
            return 50
        
        # Calculate volatility
        returns = df['Close'].pct_change().dropna()
        current_vol = returns.tail(10).std() * 100
        avg_vol = returns.tail(50).std() * 100
        
        vol_score = 50  # Base score
        
        # Volatility comparison
        if current_vol <= avg_vol * 1.2:
            vol_score += 20  # Normal volatility
        elif current_vol <= avg_vol * 1.5:
            vol_score += 10  # Slightly high
        else:
            vol_score -= 10  # Too high
        
        # Volatility trend
        vol_trend = current_vol / avg_vol
        if 0.8 <= vol_trend <= 1.2:
            vol_score += 30  # Stable
        elif 0.6 <= vol_trend <= 1.4:
            vol_score += 15  # Acceptable
        else:
            vol_score -= 15  # Unstable
        
        return max(0, min(100, vol_score))
    
    def generate_verification_report(self, df, setup_data):
        """Generate comprehensive verification report"""
        checklist = self.generate_checklist(setup_data)
        analysis = self.analyze_setup_strength(df, setup_data)
        
        report = {
            "setup": setup_data,
            "checklist": checklist,
            "technical_analysis": analysis,
            "final_recommendation": self.get_final_recommendation(checklist, analysis),
            "risk_factors": self.identify_risk_factors(checklist, analysis),
            "confidence_level": self.calculate_confidence(checklist, analysis)
        }
        
        return report
    
    def get_final_recommendation(self, checklist, analysis):
        """Get final trading recommendation"""
        checklist_score = checklist["total_score"] / checklist["max_score"] * 100
        technical_score = analysis["overall_strength"]
        
        combined_score = (checklist_score * 0.6) + (technical_score * 0.4)
        
        if combined_score >= 85:
            return "STRONG BUY - High confidence setup with strong technical confirmation"
        elif combined_score >= 75:
            return "BUY - Good setup with proper risk management"
        elif combined_score >= 65:
            return "CONSIDER - Moderate setup, be cautious with position size"
        elif combined_score >= 55:
            return "WAIT - Setup needs more confirmation before entry"
        elif combined_score >= 45:
            return "AVOID - Too many risk factors, better opportunities exist"
        else:
            return "STRONG AVOID - High risk setup, do not trade"
    
    def identify_risk_factors(self, checklist, analysis):
        """Identify specific risk factors"""
        risk_factors = []
        
        # Pattern quality risks
        if checklist["total_score"] / checklist["max_score"] < 0.6:
            risk_factors.append("Low pattern quality score")
        
        # Technical risks
        if analysis["trend_strength"] < 40:
            risk_factors.append("Weak trend strength")
        
        if analysis["volume_confirmation"] < 40:
            risk_factors.append("Poor volume confirmation")
        
        if analysis["volatility"] < 30 or analysis["volatility"] > 80:
            risk_factors.append("Abnormal volatility")
        
        # Setup-specific risks
        if analysis["support_resistance"] < 40:
            risk_factors.append("Weak support/resistance levels")
        
        return risk_factors
    
    def calculate_confidence(self, checklist, analysis):
        """Calculate overall confidence level"""
        checklist_confidence = checklist["total_score"] / checklist["max_score"]
        technical_confidence = analysis["overall_strength"] / 100
        
        overall_confidence = (checklist_confidence * 0.6) + (technical_confidence * 0.4)
        
        return {
            "percentage": round(overall_confidence * 100, 1),
            "level": self.get_confidence_level(overall_confidence)
        }
    
    def get_confidence_level(self, confidence):
        """Get confidence level description"""
        if confidence >= 0.85:
            return "Very High"
        elif confidence >= 0.75:
            return "High"
        elif confidence >= 0.65:
            return "Moderate"
        elif confidence >= 0.55:
            return "Low"
        else:
            return "Very Low"

# Global instance
verifier = VerificationTools()

def generate_verification_checklist(setup_data):
    """Convenience function to generate checklist"""
    return verifier.generate_checklist(setup_data)

def analyze_setup_technically(df, setup_data):
    """Convenience function for technical analysis"""
    return verifier.analyze_setup_strength(df, setup_data)

def generate_full_verification_report(df, setup_data):
    """Convenience function for full verification"""
    return verifier.generate_verification_report(df, setup_data)
