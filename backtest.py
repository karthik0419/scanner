"""
Backtest entry point.

Usage examples:
  python backtest.py --symbols RELIANCE.NS TCS.NS INFY.NS
  python backtest.py --stocks stocks.txt --years 2 --min-score 30
  python backtest.py --symbols HDFCBANK.NS --years 1 --scan-every 3
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backtester.engine import backtest_portfolio
from backtester.report import generate_report


def load_stocks(filepath):
    try:
        with open(filepath) as f:
            return [
                line.strip()
                for line in f
                if line.strip() and not line.startswith("#")
            ]
    except FileNotFoundError:
        print(f"File not found: {filepath}")
        return []


def main():
    parser = argparse.ArgumentParser(description="Swing trading strategy backtester")
    parser.add_argument("--stocks", default="stocks.txt", help="Path to stock symbols file")
    parser.add_argument("--symbols", nargs="+", help="Override with specific symbols (e.g. RELIANCE.NS TCS.NS)")
    parser.add_argument("--years", type=int, default=2, help="Years of history to backtest (default: 2)")
    parser.add_argument("--min-score", type=float, default=30, help="Minimum pattern score to trade (default: 30)")
    parser.add_argument("--scan-every", type=int, default=5, help="Scan every N bars (default: 5, lower = more trades but slower)")
    parser.add_argument("--output", default="backtest_results.csv", help="Output CSV filename")
    args = parser.parse_args()

    if args.symbols:
        symbols = args.symbols
    else:
        symbols = load_stocks(args.stocks)
        if not symbols:
            print("No symbols to backtest. Use --symbols RELIANCE.NS TCS.NS or provide a stocks.txt file.")
            sys.exit(1)

    print(f"\nBacktesting {len(symbols)} symbol(s) | {args.years}yr history | min_score={args.min_score} | scan_every={args.scan_every}d\n")

    trades = backtest_portfolio(
        symbols,
        years=args.years,
        min_score=args.min_score,
        scan_every=args.scan_every,
    )

    generate_report(trades, output_csv=args.output)


if __name__ == "__main__":
    main()
