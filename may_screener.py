"""
Enhanced May 2026 Swing Screener
Combines: Cup & Handle (weekly + daily), RSI momentum, relative strength
vs Nifty, 52-week high proximity, volume surge, ATR-based risk.

Usage:
  python may_screener.py
  python may_screener.py --stocks nifty200.txt --top 20
"""

import sys, os, argparse, warnings
import pandas as pd
import numpy as np
from datetime import date, timedelta

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.loader import _resample_weekly
from data.fetcher import fetch_cached, fetch_all_parallel
from patterns.cup_handle import detect_cup_handle, detect_cup_handle_weekly
from patterns.breakout import detect_breakout
from patterns.darvas_box import detect_darvas_box
from patterns.flags import detect_flag_pennant
from patterns.break_retest import detect_break_retest
from patterns.triangle import detect_triangle
from patterns.sr_levels import detect_sr_levels
from patterns.channel import detect_descending_channel


# ──────────────────────────────────────────────
#  INDICATOR HELPERS
# ──────────────────────────────────────────────

def _atr(df, period=14):
    h, l, c = df['High'], df['Low'], df['Close']
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return float(tr.rolling(period).mean().iloc[-1])


def _rsi(df, period=14):
    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return float(100 - 100 / (1 + rs.iloc[-1]))


def _high_52w(df):
    return float(df['High'].tail(252).max())


def _low_52w(df):
    return float(df['Low'].tail(252).min())


def _rel_strength(df, df_nifty, period=20):
    """Return vs Nifty over last `period` bars."""
    if df_nifty is None or len(df) < period or len(df_nifty) < period:
        return 0.0
    stock_ret = float(df['Close'].iloc[-1] / df['Close'].iloc[-period] - 1)
    nifty_ret = float(df_nifty['Close'].iloc[-1] / df_nifty['Close'].iloc[-period] - 1)
    return round((stock_ret - nifty_ret) * 100, 2)


def _vol_surge(df, period=20):
    avg = df['Volume'].tail(period).mean()
    cur = float(df['Volume'].iloc[-1])
    return round(cur / avg, 2) if avg > 0 else 1.0


def _ma(df, n):
    return float(df['Close'].rolling(n).mean().iloc[-1])


# ──────────────────────────────────────────────
#  PER-STOCK ANALYSIS
# ──────────────────────────────────────────────

def analyse_stock(symbol, df=None, df_nifty=None):
    if df is None:
        df = fetch_cached(symbol, days=400)
    if df is None or len(df) < 80:
        return None

    cmp = float(df['Close'].iloc[-1])
    atr_val = _atr(df)
    rsi_val = _rsi(df)
    h52 = _high_52w(df)
    l52 = _low_52w(df)
    rs = _rel_strength(df, df_nifty)
    vol_ratio = _vol_surge(df)
    ma20 = _ma(df, 20)
    ma50 = _ma(df, 50)

    # 52-week position: how far from 52w high (lower = closer to breakout)
    dist_52h = round((h52 - cmp) / h52 * 100, 2)  # % below 52w high

    # ── Pattern detection (priority order) ──
    df_weekly = _resample_weekly(df)
    pattern_result = (
        detect_cup_handle_weekly(df_weekly) or
        detect_cup_handle(df) or
        detect_break_retest(df) or
        detect_descending_channel(df) or
        detect_triangle(df) or
        detect_darvas_box(df) or
        detect_flag_pennant(df) or
        detect_sr_levels(df) or
        detect_breakout(df)
    )

    pattern = pattern_result["pattern"] if pattern_result else "No Pattern"
    # For no-pattern stocks use recent 20-day high as breakout (realistic near-term resistance)
    recent_resistance = float(df['High'].tail(20).max())
    breakout_level = pattern_result["breakout"] if pattern_result else recent_resistance
    stop_loss = pattern_result["stop_loss"] if pattern_result else (cmp - 2 * atr_val)
    target = pattern_result["target"] if pattern_result else (cmp + 3 * atr_val)
    p_status = pattern_result.get("status", "") if pattern_result else ""

    # Skip if breakout is more than 20% above CMP — unreachable in a swing
    if breakout_level > cmp * 1.20:
        return None

    # ── Scoring system ──
    score = 0
    reasons = []

    # 1. Pattern quality (40 pts)
    pattern_scores = {
        "Cup & Handle (Weekly)": 40,
        "Cup & Handle":          35,
        "Break & Retest":        33,
        "Channel Breakout":      32,
        "Ascending Triangle":    30,
        "Symmetrical Triangle":  28,
        "Darvas Box":            28,
        "S&R Support":           25,
        "S&R Breakout":          25,
        "Bullish Flag":          25,
        "Bullish Pennant":       25,
        "Resistance Breakout":   20,
        "No Pattern":             0,
    }
    score += pattern_scores.get(pattern, 15)
    if pattern != "No Pattern":
        reasons.append(pattern)

    # 2. RSI zone (20 pts) — want 45-65: recovering but not overbought
    if 45 <= rsi_val <= 65:
        score += 20
        reasons.append(f"RSI healthy ({rsi_val:.0f})")
    elif 35 <= rsi_val < 45:
        score += 12
        reasons.append(f"RSI recovering ({rsi_val:.0f})")
    elif rsi_val > 65:
        score += 8  # overbought — still ok but risky

    # 3. Relative strength vs Nifty (15 pts)
    if rs >= 5:
        score += 15
        reasons.append(f"RS vs Nifty +{rs}%")
    elif rs >= 2:
        score += 10
        reasons.append(f"RS vs Nifty +{rs}%")
    elif rs >= 0:
        score += 5

    # 4. Near 52-week high (15 pts) — within 15% = potential breakout
    if dist_52h <= 5:
        score += 15
        reasons.append(f"Near 52w high ({dist_52h:.1f}% below)")
    elif dist_52h <= 10:
        score += 10
        reasons.append(f"{dist_52h:.1f}% below 52w high")
    elif dist_52h <= 15:
        score += 5

    # 5. Volume surge (10 pts)
    if vol_ratio >= 1.5:
        score += 10
        reasons.append(f"Volume surge {vol_ratio:.1f}x")
    elif vol_ratio >= 1.2:
        score += 5

    # 6. MA alignment — price above MA20 and MA50 (10 pts)
    if cmp > ma20 > ma50:
        score += 10
        reasons.append("Above MA20 & MA50")
    elif cmp > ma20:
        score += 5

    # ── Risk/Reward ──
    risk_amt = cmp - stop_loss
    reward_amt = target - cmp
    rr = round(reward_amt / risk_amt, 2) if risk_amt > 0 else 0
    upside_pct = round(reward_amt / cmp * 100, 2)
    risk_pct = round(risk_amt / cmp * 100, 2)

    if rr < 1.0:
        return None  # skip bad RR trades

    # Penalise if RR is poor
    if rr >= 2.5:
        score += 10
    elif rr >= 1.5:
        score += 5

    return {
        "symbol":       symbol,
        "pattern":      pattern,
        "status":       p_status,
        "cmp":          round(cmp, 2),
        "breakout":     round(breakout_level, 2),
        "stop_loss":    round(stop_loss, 2),
        "target":       round(target, 2),
        "upside_%":     upside_pct,
        "risk_%":       risk_pct,
        "rr":           rr,
        "rsi":          round(rsi_val, 1),
        "rs_vs_nifty":  rs,
        "vol_ratio":    vol_ratio,
        "dist_52h_%":   dist_52h,
        "atr":          round(atr_val, 2),
        "score":        round(score, 1),
        "reasons":      " | ".join(reasons),
    }


# ──────────────────────────────────────────────
#  MAIN
# ──────────────────────────────────────────────

def load_stocks(path):
    try:
        with open(path) as f:
            return [l.strip() for l in f if l.strip() and not l.startswith("#")]
    except FileNotFoundError:
        return []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stocks", default="nifty200.txt")
    parser.add_argument("--symbols", nargs="+")
    parser.add_argument("--top", type=int, default=15)
    parser.add_argument("--min-score", type=float, default=30)
    today_str = date.today().strftime("%Y-%m-%d")
    parser.add_argument("--output", default=f"results_{today_str}.csv")
    args = parser.parse_args()

    symbols = args.symbols if args.symbols else load_stocks(args.stocks)
    symbols = list(dict.fromkeys(symbols))  # remove duplicates, preserve order
    if not symbols:
        print("No symbols. Use --symbols or a stocks file.")
        sys.exit(1)

    # Pre-fetch all stocks in parallel
    print(f"Fetching data for {len(symbols)} stocks in parallel...")
    stock_data = fetch_all_parallel(symbols, days=400, max_workers=10)
    print("Done fetching.\n")

    df_nifty = None  # NSE index not available via jugaad-data

    print(f"Scanning {len(symbols)} stocks for May 2026 swing setups...\n")

    results = []
    for sym in symbols:
        print(f"  {sym}...", end=" ", flush=True)
        try:
            df = stock_data.get(sym)
            res = analyse_stock(sym, df=df, df_nifty=df_nifty)
            if res and res["score"] >= args.min_score:
                results.append(res)
                print(f"  FOUND score={res['score']} | {res['pattern']} | RR={res['rr']} | upside={res['upside_%']}%")
            else:
                print("skip")
        except Exception as e:
            print(f"err: {e}")

    if not results:
        print("\nNo setups found. Try lowering --min-score.")
        return

    df = pd.DataFrame(results).sort_values("score", ascending=False).head(args.top)
    df.to_csv(args.output, index=False)

    print(f"\n{'='*75}")
    print(f"  TOP {len(df)} SWING SETUPS — MAY 2026")
    print(f"{'='*75}")

    display_cols = ["symbol", "pattern", "cmp", "breakout", "stop_loss",
                    "target", "upside_%", "risk_%", "rr", "rsi",
                    "rs_vs_nifty", "score", "reasons"]
    print(df[display_cols].to_string(index=False))

    print(f"\n{'='*75}")
    print(f"  MARKET CONTEXT (May 2026)")
    print(f"{'='*75}")
    print("  Nifty range:   23,800 – 24,300  |  Breakout above 24,300 = bullish")
    print("  India VIX:     ~18.75 (elevated) |  Use ATR-based stops, 2–5%")
    print("  Best sectors:  Capital Goods, Healthcare, Private Banks")
    print("  Risk:          India-Pakistan tensions, Crude $110+")
    print(f"\n  Saved to: {args.output}")


if __name__ == "__main__":
    main()
