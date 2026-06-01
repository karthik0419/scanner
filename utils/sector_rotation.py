"""
Sector Rotation Engine
Identifies which NSE sectors are hot/cold using sector index performance.
Used to boost scores of stocks in trending sectors.
"""
import warnings
warnings.filterwarnings("ignore")
import yfinance as yf
import pandas as pd

# NSE Sector indices on yfinance
SECTOR_INDICES = {
    'Banking':       '^NSEBANK',
    'IT':            '^CNXIT',
    'Pharma':        '^CNXPHARMA',
    'Auto':          '^CNXAUTO',
    'Metals':        '^CNXMETAL',
    'FMCG':          '^CNXFMCG',
    'Infra':         '^CNXINFRA',
    'Realty':        '^CNXREALTY',
    'Energy':        '^CNXENERGY',
    'Media':         '^CNXMEDIA',
    'MidCap':        '^NSEMDCP50',
    'PSU Bank':      '^CNXPSUBANK',
    'Capital Goods': '^CNXINFRA',
}

# Stock → Sector mapping (expanded)
STOCK_SECTOR = {
    # Banking
    'HDFCBANK.NS':'Banking','ICICIBANK.NS':'Banking','SBIN.NS':'Banking',
    'AXISBANK.NS':'Banking','KOTAKBANK.NS':'Banking','BAJFINANCE.NS':'Banking',
    'PNB.NS':'Banking','BANKBARODA.NS':'Banking','FEDERALBNK.NS':'Banking',
    'RBLBANK.NS':'Banking','INDUSINDBK.NS':'Banking','IDFCFIRSTB.NS':'Banking',
    # IT
    'TCS.NS':'IT','INFY.NS':'IT','WIPRO.NS':'IT','HCLTECH.NS':'IT',
    'TECHM.NS':'IT','MPHASIS.NS':'IT','LTIM.NS':'IT','PERSISTENT.NS':'IT',
    'COFORGE.NS':'IT','KPITTECH.NS':'IT',
    # Pharma
    'SUNPHARMA.NS':'Pharma','DRREDDY.NS':'Pharma','CIPLA.NS':'Pharma',
    'LUPIN.NS':'Pharma','AUROPHARMA.NS':'Pharma','DIVISLAB.NS':'Pharma',
    'NATCOPHARM.NS':'Pharma','LAURUSLABS.NS':'Pharma','HIKAL.NS':'Pharma',
    # Auto
    'TATAMOTORS.NS':'Auto','MARUTI.NS':'Auto','M&M.NS':'Auto',
    'BAJAJ-AUTO.NS':'Auto','HEROMOTOCO.NS':'Auto','EICHERMOT.NS':'Auto',
    'MOTHERSON.NS':'Auto','BHARATFORG.NS':'Auto','SONACOMS.NS':'Auto',
    # Metals
    'TATASTEEL.NS':'Metals','JSWSTEEL.NS':'Metals','HINDALCO.NS':'Metals',
    'VEDL.NS':'Metals','COALINDIA.NS':'Metals','NMDC.NS':'Metals',
    'SAIL.NS':'Metals','JINDALSTEL.NS':'Metals',
    # FMCG
    'ITC.NS':'FMCG','HINDUNILVR.NS':'FMCG','NESTLEIND.NS':'FMCG',
    'DABUR.NS':'FMCG','GODREJCP.NS':'FMCG','MARICO.NS':'FMCG',
    # Oil & Gas / Energy
    'RELIANCE.NS':'Energy','ONGC.NS':'Energy','BPCL.NS':'Energy',
    'HINDPETRO.NS':'Energy','GAIL.NS':'Energy','NTPC.NS':'Energy',
    'POWERGRID.NS':'Energy','TATAPOWER.NS':'Energy',
    # Capital Goods / Infra
    'LT.NS':'Infra','SIEMENS.NS':'Infra','ABB.NS':'Infra',
    'CUMMINSIND.NS':'Infra','THERMAX.NS':'Infra','BHEL.NS':'Infra',
    'DEEPINDS.NS':'Infra','KIRLOSENG.NS':'Infra','GREAVESCOT.NS':'Infra',
    'APARINDS.NS':'Infra','TIMKEN.NS':'Infra','KPIL.NS':'Infra',
    'KALPATPOWR.NS':'Infra','POWERINDIA.NS':'Infra','GVT&D.NS':'Infra',
    # Realty
    'GODREJPROP.NS':'Realty','OBEROIRLTY.NS':'Realty','DLF.NS':'Realty',
    'PHOENIXLTD.NS':'Realty','PRESTIGE.NS':'Realty',
    # MidCap / Others
    'TITAN.NS':'FMCG','ASTRAMICRO.NS':'Defence','CENTUM.NS':'Defence',
    'JSWENERGY.NS':'Energy','PSPPROJECT.NS':'Infra','WELCORP.NS':'Infra',
}

# NSE sector → rotation sector mapping
YF_SECTOR_MAP = {
    'Basic Materials':          'Metals',
    'Consumer Cyclical':        'Auto',
    'Consumer Defensive':       'FMCG',
    'Energy':                   'Energy',
    'Financial Services':       'Banking',
    'Healthcare':               'Pharma',
    'Industrials':              'Infra',
    'Real Estate':              'Realty',
    'Technology':               'IT',
    'Communication Services':   'Media',
    'Utilities':                'Energy',
}

_cache = {}
_sector_lookup_cache = {}


def get_sector_heat(lookback_short=5, lookback_long=20):
    """
    Returns dict: sector -> {'perf_5d', 'perf_20d', 'signal', 'score_bonus'}
    signal: BOOM / RISING / COOLING / WEAK
    score_bonus: +20 BOOM, +10 RISING, 0 COOLING, -10 WEAK
    Cached for the session.
    """
    global _cache
    if _cache:
        return _cache

    heat = {}
    for sector, ticker in SECTOR_INDICES.items():
        try:
            df = yf.download(ticker, period='3mo', interval='1d',
                             progress=False, auto_adjust=True)
            if df is None or df.empty:
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            if len(df) < lookback_long + 2:
                continue

            curr   = float(df['Close'].iloc[-1])
            p5     = float(df['Close'].iloc[-(lookback_short+1)])
            p20    = float(df['Close'].iloc[-(lookback_long+1)])

            perf_5d  = round((curr - p5)  / p5  * 100, 2)
            perf_20d = round((curr - p20) / p20 * 100, 2)

            if perf_5d > 2 and perf_20d > 3:
                signal, bonus = 'BOOM',    20
            elif perf_5d > 0 and perf_20d > 0:
                signal, bonus = 'RISING',  10
            elif perf_5d < 0 and perf_20d > 0:
                signal, bonus = 'COOLING',  0
            else:
                signal, bonus = 'WEAK',   -10

            heat[sector] = {
                'perf_5d':  perf_5d,
                'perf_20d': perf_20d,
                'signal':   signal,
                'bonus':    bonus,
            }
        except Exception:
            pass

    _cache = heat
    return heat


def get_stock_sector(symbol):
    """Return sector name. Checks hardcoded map first, then yfinance as fallback."""
    global _sector_lookup_cache
    sym_ns  = symbol if symbol.endswith('.NS') else symbol + '.NS'
    sym_raw = symbol.replace('.NS','')

    # 1. Hardcoded map (instant)
    sec = STOCK_SECTOR.get(sym_ns) or STOCK_SECTOR.get(sym_raw)
    if sec:
        return sec

    # 2. Session cache
    if sym_ns in _sector_lookup_cache:
        return _sector_lookup_cache[sym_ns]

    # 3. yfinance info (slow but accurate — cached after first call)
    try:
        import yfinance as yf, contextlib, io
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            info = yf.Ticker(sym_ns).info
        yf_sector = info.get('sector', '')
        mapped = YF_SECTOR_MAP.get(yf_sector, yf_sector or 'Unknown')
        _sector_lookup_cache[sym_ns] = mapped
        return mapped
    except Exception:
        _sector_lookup_cache[sym_ns] = 'Unknown'
        return 'Unknown'


def get_sector_bonus(symbol):
    """
    Returns (sector, signal, score_bonus) for a symbol.
    Used by engine/scanner.py to boost/penalise score.
    """
    heat   = get_sector_heat()
    sector = get_stock_sector(symbol)
    if sector == 'Unknown' or sector not in heat:
        return sector, 'Unknown', 0
    h = heat[sector]
    return sector, h['signal'], h['bonus']


def print_sector_heatmap():
    """Print current sector rotation heatmap."""
    heat = get_sector_heat()
    rows = sorted(heat.items(), key=lambda x: x[1]['perf_5d'], reverse=True)
    print('\n  SECTOR ROTATION HEATMAP')
    print(f'  {"Sector":<14} {"5D":>7} {"20D":>7}  Signal')
    print('  ' + '-'*42)
    for s, h in rows:
        icon = '🔥' if h['signal']=='BOOM' else '↑' if h['signal']=='RISING' else '↓' if h['signal']=='COOLING' else '🔴'
        print(f'  {s:<14} {h["perf_5d"]:>+6.2f}%  {h["perf_20d"]:>+6.2f}%  {icon} {h["signal"]}')
    print()


if __name__ == '__main__':
    print_sector_heatmap()
