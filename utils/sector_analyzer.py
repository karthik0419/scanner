import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# Sector mapping for NSE stocks
SECTOR_MAPPING = {
    # Banking
    'HDFCBANK.NS': 'Banking', 'ICICIBANK.NS': 'Banking', 'SBIN.NS': 'Banking',
    'AXISBANK.NS': 'Banking', 'KOTAKBANK.NS': 'Banking', 'BAJFINANCE.NS': 'Banking',
    'PNB.NS': 'Banking', 'BANKBARODA.NS': 'Banking',
    
    # IT
    'TCS.NS': 'IT', 'INFY.NS': 'IT', 'WIPRO.NS': 'IT', 'HCLTECH.NS': 'IT',
    'TECHM.NS': 'IT', 'MPHASIS.NS': 'IT',
    
    # Pharma
    'SUNPHARMA.NS': 'Pharma', 'DRREDDY.NS': 'Pharma', 'CIPLA.NS': 'Pharma',
    'LUPIN.NS': 'Pharma', 'AUROPHARMA.NS': 'Pharma',
    
    # Auto
    'TATAMOTORS.NS': 'Auto', 'MARUTI.NS': 'Auto', 'M&M.NS': 'Auto',
    'BAJAJ-AUTO.NS': 'Auto', 'HEROMOTOCO.NS': 'Auto',
    
    # Oil & Gas
    'RELIANCE.NS': 'Oil & Gas', 'ONGC.NS': 'Oil & Gas', 'BPCL.NS': 'Oil & Gas',
    'HINDPETRO.NS': 'Oil & Gas', 'GAIL.NS': 'Oil & Gas',
    
    # Metals
    'TATASTEEL.NS': 'Metals', 'JSWSTEEL.NS': 'Steel', 'HINDALCO.NS': 'Metals',
    'VEDL.NS': 'Metals', 'COALINDIA.NS': 'Metals',
    
    # FMCG
    'ITC.NS': 'FMCG', 'HINDUNILVR.NS': 'FMCG', 'NESTLEIND.NS': 'FMCG',
    'DABUR.NS': 'FMCG', 'GODREJCP.NS': 'FMCG',
    
    # Infrastructure
    'LT.NS': 'Infrastructure', 'L&T.NS': 'Infrastructure',
    'ADANIENT.NS': 'Infrastructure', 'ADANIGREEN.NS': 'Infrastructure',
    'ADANIPOWER.NS': 'Infrastructure',
    
    # Telecom
    'BHARTIARTL.NS': 'Telecom', 'IDEA.NS': 'Telecom', 'VODAFONE.NS': 'Telecom',
    
    # Others
    'TITAN.NS': 'Luxury Goods', 'SHAKTIPUMP.NS': 'Industrial',
    'JAINREC.NS': 'Renewable Energy', 'SANGHVIMOV.NS': 'Textiles',
    'ULTRACEMCO.NS': 'Cement', 'RAILTEL.NS': 'Railways',
    'NETWEB.NS': 'IT Services', 'WEBELSOLAR.NS': 'Solar Energy'
}

def get_sector_performance():
    """Calculate sector performance over different timeframes"""
    sector_performance = {}
    
    # Get all unique sectors
    sectors = list(set(SECTOR_MAPPING.values()))
    
    for sector in sectors:
        sector_stocks = [symbol for symbol, sec in SECTOR_MAPPING.items() if sec == sector]
        
        if not sector_stocks:
            continue
            
        # Calculate sector performance
        sector_data = []
        for stock in sector_stocks[:10]:  # Limit to 10 stocks per sector
            try:
                data = yf.download(stock, period='1mo', interval='1d', progress=False)
                if not data.empty:
                    start_price = data['Close'].iloc[0]
                    current_price = data['Close'].iloc[-1]
                    performance = (current_price - start_price) / start_price * 100
                    sector_data.append(performance)
            except:
                continue
        
        if sector_data and len(sector_data) > 0:
            # Convert to list to avoid pandas Series issues
            try:
                sector_data_list = [float(x) for x in sector_data]
                avg_perf = sum(sector_data_list) / len(sector_data_list)
                momentum = 'Strong' if avg_perf > 2 else 'Moderate' if avg_perf > 0 else 'Weak'
                sector_performance[sector] = {
                    'avg_performance': avg_perf,
                    'num_stocks': len(sector_data_list),
                    'momentum': momentum
                }
            except Exception as e:
                print(f"Error processing sector {sector}: {e}")
                # Skip this sector if there's an error
                pass
    
    return sector_performance

def get_market_conditions():
    """Analyze overall market conditions"""
    try:
        # Get Nifty 50 data
        nifty = yf.download('^NSEI', period='1mo', interval='1d', progress=False)
        
        if nifty.empty:
            return get_default_market_conditions()
        
        current_price = nifty['Close'].iloc[-1]
        start_price = nifty['Close'].iloc[0]
        
        # Calculate metrics
        nifty_change = (float(current_price) - float(start_price)) / float(start_price) * 100
        
        # 20-day moving average
        ma_20 = nifty['Close'].rolling(20).mean().iloc[-1]
        
        # Volatility (using daily returns)
        returns = nifty['Close'].pct_change().dropna()
        volatility = returns.std() * 100  # Convert to percentage
        
        # Market trend
        if float(current_price) > float(ma_20) * 1.02:
            trend = 'Strong Bullish'
        elif float(current_price) > float(ma_20):
            trend = 'Bullish'
        elif float(current_price) < float(ma_20) * 0.98:
            trend = 'Strong Bearish'
        elif float(current_price) < float(ma_20):
            trend = 'Bearish'
        else:
            trend = 'Sideways'
        
        # Market condition
        if volatility > 2.0:
            volatility_level = 'High'
        elif volatility > 1.2:
            volatility_level = 'Medium'
        else:
            volatility_level = 'Low'
        
        # Favorability for swing trading
        favorable = (
            trend in ['Bullish', 'Strong Bullish'] and 
            volatility_level in ['Low', 'Medium'] and
            nifty_change > -2
        )
        
        return {
            'nifty_change': round(nifty_change, 2),
            'trend': trend,
            'volatility': volatility_level,
            'volatility_value': round(volatility, 2),
            'ma_20': round(ma_20, 2),
            'current_price': round(current_price, 2),
            'favorable': favorable,
            'recommendation': 'Good for swing trading' if favorable else 'Caution advised'
        }
        
    except Exception as e:
        print(f"Error getting market conditions: {e}")
        return get_default_market_conditions()

def get_default_market_conditions():
    """Default market conditions if data fetch fails"""
    return {
        'nifty_change': 0,
        'trend': 'Sideways',
        'volatility': 'Medium',
        'volatility_value': 1.5,
        'ma_20': 0,
        'current_price': 0,
        'favorable': False,
        'recommendation': 'Data unavailable - proceed with caution'
    }

def analyze_stock_sector(symbol):
    """Get sector analysis for a specific stock"""
    sector = SECTOR_MAPPING.get(symbol, 'Unknown')
    
    if sector == 'Unknown':
        return {
            'sector': 'Unknown',
            'sector_performance': 0,
            'sector_momentum': 'Unknown',
            'sector_rank': 'N/A'
        }
    
    # Simple sector analysis without complex calculations
    return {
        'sector': sector,
        'sector_performance': 0,  # Will be calculated later
        'sector_momentum': 'Moderate',
        'sector_rank': 'N/A'
    }

def filter_by_market_conditions(results, market_conditions):
    """Filter results based on market conditions"""
    filtered_results = []
    
    for result in results:
        symbol = result.get('symbol', '')
        sector_analysis = analyze_stock_sector(symbol)
        
        # Add sector info to result
        result.update(sector_analysis)
        
        # Apply filters
        should_include = True
        filter_reasons = []
        
        # Market trend filter
        if not market_conditions['favorable']:
            # In unfavorable conditions, be more selective
            if result.get('score', 0) < 100:
                should_include = False
                filter_reasons.append('Market conditions unfavorable - low score')
        
        # Sector momentum filter
        if sector_analysis['sector_momentum'] == 'Weak':
            if result.get('score', 0) < 110:
                should_include = False
                filter_reasons.append('Weak sector momentum - low score')
        
        # Volatility filter
        if market_conditions['volatility'] == 'High':
            # In high volatility, prefer stronger patterns
            if result.get('pattern') not in ['Cup & Handle', 'Double Bottom']:
                should_include = False
                filter_reasons.append('High volatility - prefer stronger patterns')
        
        result['market_filter_passed'] = should_include
        result['filter_reasons'] = filter_reasons
        
        if should_include:
            filtered_results.append(result)
    
    return filtered_results

def get_sector_summary():
    """Get summary of all sectors for reporting"""
    sector_perf = get_sector_performance()
    market_cond = get_market_conditions()
    
    # Sort sectors by performance
    sorted_sectors = sorted(sector_perf.items(), key=lambda x: x[1]['avg_performance'], reverse=True)
    
    summary = {
        'market_conditions': market_cond,
        'top_sectors': sorted_sectors[:5],
        'bottom_sectors': sorted_sectors[-3:] if len(sorted_sectors) > 3 else [],
        'total_sectors_analyzed': len(sorted_sectors)
    }
    
    return summary
