import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class HighQualityStockFetcher:
    def __init__(self):
        self.nifty_50_stocks = self.get_nifty_50_stocks()
        self.nifty_next_50_stocks = self.get_nifty_next_50_stocks()
        self.sector_leaders = self.get_sector_leaders()
        self.liquid_stocks = self.get_liquid_stocks()
    
    def get_nifty_50_stocks(self):
        """Get current Nifty 50 constituents (major stocks)"""
        return [
            "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
            "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS",
            "LT.NS", "AXISBANK.NS", "MARUTI.NS", "SUNPHARMA.NS", "M&M.NS",
            "TITAN.NS", "BAJFINANCE.NS", "ADANIPORTS.NS", "NTPC.NS", "POWERGRID.NS",
            "WIPRO.NS", "HCLTECH.NS", "TECHM.NS", "GRASIM.NS", "DRREDDY.NS",
            "COALINDIA.NS", "ULTRACEMCO.NS", "JSWSTEEL.NS", "BPCL.NS", "ONGC.NS",
            "GAIL.NS", "DIVISLAB.NS", "HEROMOTOCO.NS", "BRITANNIA.NS", "NESTLEIND.NS",
            "CIPLA.NS", "TATAMOTORS.NS", "DABUR.NS", "ASIANPAINT.NS", "EICHERMOT.NS"
        ]
    
    def get_nifty_next_50_stocks(self):
        """Get Nifty Next 50 constituents (mid-cap stocks)"""
        return [
            "TATACONSUM.NS", "L&TFH.NS", "DLF.NS", "BANDHANBNK.NS", "INDUSINDBK.NS",
            "FEDERALBNK.NS", "IDFC.NS", "PFC.NS", "RECLTD.NS", "MUTHOOTFIN.NS",
            "GODREJCP.NS", "JINDALSTEL.NS", "JSWENERGY.NS", "ADANIPOWER.NS", "TATAPOWER.NS",
            "NHPC.NS", "NCC.NS", "SJVN.NS", "POWERFINCORP.NS", "TORNTPOWER.NS",
            "JSWINFRA.NS", "LICHSGFIN.NS", "PNBHOUSING.NS", "RECLTD.NS", "SUNTECK.NS",
            "CHOLAFIN.NS", "BANKBARODA.NS", "INDIANB.NS", "CENTRALBK.NS", "PNB.NS",
            "UCOBANK.NS", "CANBK.NS", "RBLBANK.NS", "FORTIS.NS", "IDFCFIRSTBK.NS",
            "J&KBANK.NS", "KARURVYSYA.NS", "RATNAMANI.NS", "MANAPPURAM.NS", "BALKRISIND.NS",
            "BERGEPAINT.NS", "ASTRAL.NS", "PIIND.NS", "VGUARD.NS", "SUPRAJIT.NS"
        ]
    
    def get_sector_leaders(self):
        """Get top stocks from major sectors"""
        return {
            "IT": ["INFY.NS", "TCS.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS"],
            "Banking": ["HDFCBANK.NS", "ICICIBANK.NS", "KOTAKBANK.NS", "AXISBANK.NS", "SBIN.NS"],
            "Pharma": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "LUPIN.NS", "AUROPHARMA.NS"],
            "FMCG": ["HINDUNILVR.NS", "ITC.NS", "NESTLEIND.NS", "DABUR.NS", "GODREJCP.NS"],
            "Auto": ["MARUTI.NS", "TATAMOTORS.NS", "M&M.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS"],
            "Steel": ["JSWSTEEL.NS", "TATASTEEL.NS", "HINDALCO.NS", "JINDALSTEL.NS", "SAIL.NS"],
            "Infrastructure": ["LT.NS", "L&T.NS", "RECLTD.NS", "NCC.NS", "GMRINFRA.NS"],
            "Energy": ["RELIANCE.NS", "ONGC.NS", "GAIL.NS", "BPCL.NS", "NTPC.NS"],
            "Metals": ["HINDALCO.NS", "VEDL.NS", "COALINDIA.NS", "NMDC.NS", "HINDZINC.NS"],
            "Finance": ["BAJFINANCE.NS", "CHOLAFIN.NS", "BANDHANBNK.NS", "PNBHOUSING.NS", "MAHINDRA.NS"]
        }
    
    def get_liquid_stocks(self):
        """Get highly liquid stocks based on average volume"""
        # These typically have high daily trading volumes
        return [
            "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
            "ITC.NS", "HINDUNILVR.NS", "SBIN.NS", "KOTAKBANK.NS", "LT.NS",
            "AXISBANK.NS", "MARUTI.NS", "M&M.NS", "BAJFINANCE.NS", "SUNPHARMA.NS",
            "TITAN.NS", "ULTRACEMCO.NS", "JSWSTEEL.NS", "TATASTEEL.NS", "DRREDDY.NS"
        ]
    
    def filter_by_liquidity(self, stocks, min_avg_volume=1000000):
        """Filter stocks by minimum average volume"""
        liquid_stocks = []
        
        for stock in stocks:
            try:
                data = yf.download(stock, period="1mo", interval="1d", progress=False)
                if not data.empty:
                    avg_volume = data['Volume'].tail(20).mean()
                    if avg_volume >= min_avg_volume:
                        liquid_stocks.append(stock)
            except:
                continue
        
        return liquid_stocks
    
    def filter_by_market_cap(self, stocks, min_market_cap=10000):
        """Filter stocks by minimum market cap (in crores)"""
        large_cap_stocks = []
        
        for stock in stocks:
            try:
                ticker = yf.Ticker(stock)
                info = ticker.info
                market_cap = info.get('marketCap', 0)
                
                if market_cap and market_cap >= min_market_cap * 10000000:  # Convert to rupees
                    large_cap_stocks.append(stock)
            except:
                continue
        
        return large_cap_stocks
    
    def filter_by_volatility(self, stocks, min_volatility=0.02, max_volatility=0.08):
        """Filter stocks by volatility range for swing trading"""
        volatility_filtered = []
        
        for stock in stocks:
            try:
                data = yf.download(stock, period="1mo", interval="1d", progress=False)
                if not data.empty:
                    returns = data['Close'].pct_change().dropna()
                    volatility = returns.std()
                    
                    if min_volatility <= volatility <= max_volatility:
                        volatility_filtered.append(stock)
            except:
                continue
        
        return volatility_filtered
    
    def get_trending_stocks(self, stocks, days=30):
        """Get stocks with positive momentum over last N days"""
        trending_stocks = []
        
        for stock in stocks:
            try:
                data = yf.download(stock, period=f"{days+5}d", interval="1d", progress=False)
                if not data.empty:
                    current_price = data['Close'].iloc[-1]
                    old_price = data['Close'].iloc[-(days+1)]
                    
                    if current_price > old_price * 1.05:  # 5% gain in period
                        trending_stocks.append(stock)
            except:
                continue
        
        return trending_stocks
    
    def get_quality_screened_stocks(self, criteria="balanced"):
        """Get high-quality stocks based on different criteria"""
        
        if criteria == "conservative":
            # Large cap, high liquidity, moderate volatility
            base_stocks = self.nifty_50_stocks
            filtered = self.filter_by_market_cap(base_stocks, 50000)
            filtered = self.filter_by_liquidity(filtered, 2000000)
            filtered = self.filter_by_volatility(filtered, 0.015, 0.06)
            
        elif criteria == "aggressive":
            # Include mid-caps, trending stocks
            base_stocks = self.nifty_50_stocks + self.nifty_next_50_stocks
            filtered = self.filter_by_liquidity(base_stocks, 500000)
            filtered = self.get_trending_stocks(filtered, 20)
            
        elif criteria == "momentum":
            # Focus on trending stocks
            base_stocks = self.nifty_50_stocks + self.nifty_next_50_stocks
            filtered = self.filter_by_liquidity(base_stocks, 1000000)
            filtered = self.get_trending_stocks(filtered, 15)
            
        else:  # balanced
            # Mix of large caps and liquid stocks
            base_stocks = self.nifty_50_stocks
            filtered = self.filter_by_liquidity(base_stocks, 1000000)
            filtered = self.filter_by_volatility(filtered, 0.02, 0.08)
        
        return list(set(filtered))  # Remove duplicates
    
    def generate_stock_list(self, criteria="balanced", filename="stocks_auto.txt"):
        """Generate and save stock list"""
        stocks = self.get_quality_screened_stocks(criteria)
        
        with open(filename, 'w') as f:
            for stock in stocks:
                f.write(f"{stock}\n")
        
        print(f"Generated {len(stocks)} high-quality stocks in {filename}")
        print(f"Criteria: {criteria}")
        
        return stocks
    
    def get_sector_rotation_stocks(self):
        """Get stocks from currently performing sectors"""
        # Simple sector rotation based on recent performance
        sector_performance = {
            "IT": "Strong", "Banking": "Moderate", "Pharma": "Strong",
            "Auto": "Weak", "FMCG": "Moderate", "Energy": "Strong"
        }
        
        # Prioritize strong sectors
        priority_sectors = ["IT", "Pharma", "Energy", "Banking", "FMCG"]
        selected_stocks = []
        
        for sector in priority_sectors:
            if sector in self.sector_leaders:
                selected_stocks.extend(self.sector_leaders[sector][:3])  # Top 3 from each sector
        
        return list(set(selected_stocks))
    
    def get_custom_screened_stocks(self, custom_criteria):
        """Apply custom screening criteria"""
        base_stocks = self.nifty_50_stocks + self.nifty_next_50_stocks
        
        # Parse custom criteria (example: "market_cap>50000,volume>1000000")
        # This is a placeholder for future enhancement
        
        return base_stocks
    
    def analyze_stock_quality(self, stock):
        """Analyze a single stock for quality metrics"""
        try:
            data = yf.download(stock, period="1mo", interval="1d", progress=False)
            ticker = yf.Ticker(stock)
            info = ticker.info
            
            if data.empty:
                return None
            
            # Calculate metrics
            current_price = data['Close'].iloc[-1]
            avg_volume = data['Volume'].tail(20).mean()
            returns = data['Close'].pct_change().dropna()
            volatility = returns.std()
            market_cap = info.get('marketCap', 0)
            
            # Quality score (0-100)
            quality_score = 0
            
            # Liquidity score (40% weight)
            if avg_volume > 2000000:
                quality_score += 40
            elif avg_volume > 1000000:
                quality_score += 30
            elif avg_volume > 500000:
                quality_score += 20
            
            # Volatility score (30% weight) - moderate volatility preferred
            if 0.02 <= volatility <= 0.06:
                quality_score += 30
            elif 0.015 <= volatility <= 0.08:
                quality_score += 20
            elif 0.01 <= volatility <= 0.1:
                quality_score += 10
            
            # Market cap score (20% weight)
            if market_cap > 100000000000000:  # > 1L crore
                quality_score += 20
            elif market_cap > 500000000000:  # > 5000 crore
                quality_score += 15
            elif market_cap > 100000000000:  # > 1000 crore
                quality_score += 10
            
            # Trend score (10% weight)
            recent_return = (current_price - data['Close'].iloc[-5]) / data['Close'].iloc[-5]
            if recent_return > 0.02:
                quality_score += 10
            elif recent_return > 0:
                quality_score += 5
            
            return {
                "symbol": stock,
                "quality_score": quality_score,
                "avg_volume": avg_volume,
                "volatility": volatility,
                "market_cap": market_cap,
                "recent_return": recent_return,
                "rating": self.get_quality_rating(quality_score)
            }
            
        except Exception as e:
            print(f"Error analyzing {stock}: {e}")
            return None
    
    def get_quality_rating(self, score):
        """Get quality rating based on score"""
        if score >= 80:
            return "Excellent"
        elif score >= 70:
            return "Very Good"
        elif score >= 60:
            return "Good"
        elif score >= 50:
            return "Average"
        elif score >= 40:
            return "Below Average"
        else:
            return "Poor"

# Global instance
stock_fetcher = HighQualityStockFetcher()

def generate_quality_stock_list(criteria="balanced", filename="stocks_auto.txt"):
    """Convenience function to generate stock list"""
    return stock_fetcher.generate_stock_list(criteria, filename)

def get_top_quality_stocks(count=20):
    """Get top N quality stocks"""
    all_stocks = stock_fetcher.nifty_50_stocks + stock_fetcher.nifty_next_50_stocks
    quality_analysis = []
    
    for stock in all_stocks:
        analysis = stock_fetcher.analyze_stock_quality(stock)
        if analysis:
            quality_analysis.append(analysis)
    
    # Sort by quality score
    quality_analysis.sort(key=lambda x: x['quality_score'], reverse=True)
    
    return quality_analysis[:count]

def get_sector_rotation_stocks():
    """Convenience function for sector rotation"""
    return stock_fetcher.get_sector_rotation_stocks()
