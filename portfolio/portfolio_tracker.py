"""
Portfolio Tracker — Daily P&L monitoring
Reads portfolio CSV, fetches current prices, computes live P&L.

Usage:
  python portfolio/portfolio_tracker.py
"""

import os, sys, glob, warnings
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.loader import _fetch_nse


def latest_portfolio():
    portfolio_dir = os.path.dirname(os.path.abspath(__file__))
    files = sorted(glob.glob(os.path.join(portfolio_dir, "portfolio_*.csv")))
    return files[-1] if files else None


def fetch_live_price(symbol):
    sym = symbol.replace(".NS", "")
    try:
        df = _fetch_nse(sym, days=5)
        if df is not None and not df.empty:
            return float(df["Close"].iloc[-1])
    except Exception:
        pass
    return None


def main():
    path = latest_portfolio()
    if not path:
        print("No portfolio CSV found.")
        return

    df = pd.read_csv(path)
    open_positions = df[df["status"] == "OPEN"].copy()

    print("=" * 110)
    print(f"  PORTFOLIO TRACKER — Loaded: {os.path.basename(path)}")
    print("=" * 110)
    print(f"{'Symbol':<14}{'Entry':>9}{'Live':>9}{'Qty':>5}{'Invested':>11}{'Current':>11}{'P&L':>11}{'%':>8}{'Stop':>10}{'Target':>10}{'Status':>10}")
    print("-" * 110)

    total_inv = total_cur = 0
    for _, row in open_positions.iterrows():
        sym   = row["symbol"]
        entry = float(row["entry"])
        stop  = float(row["stop_loss"])
        tgt   = float(row["target"])
        qty   = int(row["qty"])
        cost  = float(row["cost"])

        live = fetch_live_price(sym)
        if live is None:
            print(f"{sym:<14} fetch failed")
            continue

        cur_val = qty * live
        pnl     = cur_val - cost
        pct     = pnl / cost * 100

        # Status
        if live <= stop:
            verdict = "STOP HIT"
        elif live >= tgt:
            verdict = "TARGET HIT"
        elif live >= entry * 1.05:
            verdict = "WINNING"
        elif live <= entry * 0.97:
            verdict = "LOSING"
        else:
            verdict = "TRACKING"

        total_inv += cost
        total_cur += cur_val

        print(f"{sym:<14}{entry:>9.2f}{live:>9.2f}{qty:>5}{cost:>11.0f}{cur_val:>11.0f}{pnl:>+11.0f}{pct:>+7.2f}%{stop:>10.2f}{tgt:>10.2f}{verdict:>10}")

    total_pnl = total_cur - total_inv
    total_pct = total_pnl / total_inv * 100 if total_inv else 0

    print("-" * 110)
    print(f"{'TOTAL':<14}{'':>27}{total_inv:>11.0f}{total_cur:>11.0f}{total_pnl:>+11.0f}{total_pct:>+7.2f}%")
    print("=" * 110)
    print(f"\n  Cash deployed: Rs {total_inv:,.0f}")
    print(f"  Current value: Rs {total_cur:,.0f}")
    print(f"  P&L          : Rs {total_pnl:+,.0f}  ({total_pct:+.2f}%)")
    print()


if __name__ == "__main__":
    main()
