"""
Dynamic Stock Universe Builder
Runs before the screener to pick the best stocks to scan today.

How it works:
1. Loads nifty500.txt (full universe ~200 stocks)
2. Fetches all in parallel using cache (fast)
3. Scores each by: volume surge + near 52w high + above MA50
4. Takes top N momentum stocks
5. Merges with backbone50 (always included)
6. Saves to today_universe.txt

Usage:
  python stock_universe.py            # default top 80
  python stock_universe.py --top 100  # top 100 momentum stocks
"""

import os, sys, argparse, warnings
import pandas as pd
import numpy as np

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.fetcher import fetch_all_parallel


def load_list(path):
    try:
        with open(path) as f:
            return [l.strip() for l in f if l.strip() and not l.startswith("#")]
    except FileNotFoundError:
        return []


def momentum_score(df):
    """Quick score: volume surge + near 52w high + above MA50."""
    if df is None or len(df) < 60:
        return 0
    try:
        cmp      = float(df['Close'].iloc[-1])
        h52      = float(df['High'].tail(252).max())
        ma50     = float(df['Close'].rolling(50).mean().iloc[-1])
        ma20     = float(df['Close'].rolling(20).mean().iloc[-1])
        avg_vol  = float(df['Volume'].tail(20).mean())
        cur_vol  = float(df['Volume'].iloc[-1])

        score = 0

        # Near 52w high (within 15%) — approaching breakout
        dist = (h52 - cmp) / h52
        if dist <= 0.05:   score += 40
        elif dist <= 0.10: score += 30
        elif dist <= 0.15: score += 20
        else:              score += 0

        # Above MA50
        if cmp > ma50: score += 25

        # Above MA20
        if cmp > ma20: score += 15

        # Volume surge
        ratio = cur_vol / avg_vol if avg_vol > 0 else 1
        if ratio >= 2.0:   score += 20
        elif ratio >= 1.5: score += 12
        elif ratio >= 1.2: score += 6

        return score
    except Exception:
        return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--universe", default="nifty500.txt")
    parser.add_argument("--backbone", default="backbone50.txt")
    parser.add_argument("--output",   default="today_universe.txt")
    parser.add_argument("--top",      type=int, default=80)
    args = parser.parse_args()

    universe = load_list(args.universe)
    backbone = load_list(args.backbone)

    if not universe:
        print(f"No stocks in {args.universe}")
        sys.exit(1)

    print(f"Building universe: {len(universe)} stocks in nifty500 + {len(backbone)} backbone")
    print("Fetching data in parallel (cached)...")

    # Fetch all in parallel
    all_symbols = list(set(universe + backbone))
    data = fetch_all_parallel(all_symbols, days=400, max_workers=15)

    # Score each symbol
    scores = {}
    for sym, df in data.items():
        scores[sym] = momentum_score(df)

    # Sort universe by score, take top N
    universe_scored = sorted(
        [(s, scores.get(s, 0)) for s in universe],
        key=lambda x: x[1], reverse=True
    )
    top_dynamic = [s for s, sc in universe_scored[:args.top] if sc > 0]

    # Always include backbone
    final = list(dict.fromkeys(backbone + top_dynamic))  # backbone first, no duplicates

    # Write output
    with open(args.output, "w") as f:
        f.write(f"# Auto-generated universe — {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"# Backbone: {len(backbone)} | Dynamic top: {len(top_dynamic)} | Total: {len(final)}\n\n")
        f.write("# --- BACKBONE (always included) ---\n")
        for s in backbone:
            f.write(s + "\n")
        f.write("\n# --- DYNAMIC TOP MOMENTUM ---\n")
        for s in top_dynamic:
            if s not in backbone:
                f.write(s + "\n")

    print(f"\nUniverse built: {len(final)} stocks -> saved to {args.output}")
    print(f"Top 10 momentum picks today:")
    for sym, sc in universe_scored[:10]:
        print(f"  {sym:20s} score={sc}")


if __name__ == "__main__":
    main()
