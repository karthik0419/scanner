"""
Backtest — Volume Surge Alert
For each past scan date, simulate the volume alert firing and track
price 1, 3, 5 trading days after the surge.

Output: results/backtest_volume_alert.csv
"""
import os, sys, csv, glob, warnings
warnings.filterwarnings("ignore")
import logging
for n in ["yfinance","urllib3","peewee"]: logging.getLogger(n).setLevel(logging.CRITICAL)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data.loader import _fetch_nse
import pandas as pd
from datetime import timedelta

RESULTS_DIR     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
SURGE_THRESHOLD = 2.0
LOOKBACK_DAYS   = 7


def load_all_scans():
    """Returns list of (scan_date, symbol, pattern, score, status, cmp)"""
    scans = []
    files = sorted(glob.glob(os.path.join(RESULTS_DIR, "results_*.csv")))
    for f in files:
        date_str = os.path.basename(f).replace("results_","").replace(".csv","")[:10]
        try:
            for row in csv.DictReader(open(f, encoding="utf-8", errors="ignore")):
                sym = row.get("symbol","").replace(".NS","")
                if sym:
                    scans.append({
                        "scan_date": date_str,
                        "symbol":    sym,
                        "pattern":   row.get("pattern",""),
                        "score":     row.get("score",""),
                        "status":    row.get("status",""),
                        "cmp":       float(row.get("cmp",0) or 0),
                    })
        except Exception:
            pass
    return scans


def get_price_on_date(df, target_date):
    """Get close price on or after target_date."""
    try:
        future = df[df.index >= pd.Timestamp(target_date)]
        if len(future) == 0:
            return None
        return float(future["Close"].iloc[0])
    except Exception:
        return None


def simulate_alert(symbol, scan_date, lookback_scans):
    """
    Check if on scan_date, this symbol would have triggered a volume surge alert.
    Returns surge_ratio or None.
    """
    df = _fetch_nse(symbol, days=90)
    if df is None or len(df) < 25:
        return None, None

    # Find the row for scan_date
    scan_dt = pd.Timestamp(scan_date)
    before  = df[df.index <= scan_dt]
    if len(before) < 22:
        return None, None

    today_row = before.iloc[-1]
    avg_vol   = float(before["Volume"].iloc[-21:-1].mean())  # 20-day avg before today
    today_vol = float(today_row["Volume"])

    if avg_vol <= 0:
        return None, None

    ratio = round(today_vol / avg_vol, 1)
    if ratio < SURGE_THRESHOLD:
        return None, None

    return ratio, today_row


def main():
    print("="*60)
    print("  VOLUME ALERT BACKTEST")
    print("  Simulating alerts on all past scan dates")
    print("="*60)

    scans = load_all_scans()
    print(f"\n  Total scan records: {len(scans)}")

    # Group by symbol — get all dates a stock was flagged
    from collections import defaultdict
    symbol_dates = defaultdict(list)
    for s in scans:
        symbol_dates[s["symbol"]].append(s)

    results = []
    checked = 0
    alerts  = 0

    for sym, records in symbol_dates.items():
        df = _fetch_nse(sym, days=180)
        if df is None or len(df) < 30:
            continue

        for rec in records:
            scan_date = rec["scan_date"]
            scan_dt   = pd.Timestamp(scan_date)

            before = df[df.index <= scan_dt]
            if len(before) < 22:
                continue

            today_vol = float(before["Volume"].iloc[-1])
            avg_vol   = float(before["Volume"].iloc[-21:-1].mean())

            if avg_vol <= 0:
                continue

            ratio = round(today_vol / avg_vol, 1)
            checked += 1

            if ratio < SURGE_THRESHOLD:
                continue

            alerts += 1
            entry_price = float(before["Close"].iloc[-1])

            # Track forward prices
            after = df[df.index > scan_dt]
            p1 = float(after["Close"].iloc[0])  if len(after) >= 1 else None
            p3 = float(after["Close"].iloc[2])  if len(after) >= 3 else None
            p5 = float(after["Close"].iloc[4])  if len(after) >= 5 else None

            def pct(p):
                if p is None or entry_price == 0: return None
                return round((p - entry_price) / entry_price * 100, 2)

            r1, r3, r5 = pct(p1), pct(p3), pct(p5)

            outcome = "WIN" if r5 and r5 > 0 else "LOSS" if r5 and r5 < 0 else "OPEN"

            results.append({
                "scan_date":   scan_date,
                "symbol":      sym,
                "pattern":     rec["pattern"],
                "score":       rec["score"],
                "status":      rec["status"],
                "entry":       round(entry_price, 2),
                "vol_ratio":   ratio,
                "ret_1d_%":    r1,
                "ret_3d_%":    r3,
                "ret_5d_%":    r5,
                "outcome_5d":  outcome,
            })

    # Save
    out = os.path.join(RESULTS_DIR, "backtest_volume_alert.csv")
    if results:
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
            w.writeheader(); w.writerows(results)

    # Stats
    wins   = [r for r in results if r["outcome_5d"] == "WIN"]
    losses = [r for r in results if r["outcome_5d"] == "LOSS"]
    open_  = [r for r in results if r["outcome_5d"] == "OPEN"]

    valid  = [r for r in results if r["ret_5d_%"] is not None]
    avg_r1 = round(sum(r["ret_1d_%"] for r in results if r["ret_1d_%"] is not None) / max(len([r for r in results if r["ret_1d_%"] is not None]),1), 2)
    avg_r3 = round(sum(r["ret_3d_%"] for r in results if r["ret_3d_%"] is not None) / max(len([r for r in results if r["ret_3d_%"] is not None]),1), 2)
    avg_r5 = round(sum(r["ret_5d_%"] for r in results if r["ret_5d_%"] is not None) / max(len(valid),1), 2)

    print(f"\n{'='*60}")
    print(f"  BACKTEST RESULTS")
    print(f"{'='*60}")
    print(f"  Stocks checked      : {checked}")
    print(f"  Alerts triggered    : {alerts}")
    print(f"  Alert rate          : {round(alerts/checked*100,1) if checked else 0}%")
    print()
    print(f"  Avg return 1 day    : {avg_r1:+.2f}%")
    print(f"  Avg return 3 days   : {avg_r3:+.2f}%")
    print(f"  Avg return 5 days   : {avg_r5:+.2f}%")
    print()
    print(f"  Win rate (5d)       : {len(wins)}/{len(valid)}  ({round(len(wins)/len(valid)*100) if valid else 0}%)")
    print(f"  Loss rate (5d)      : {len(losses)}/{len(valid)}  ({round(len(losses)/len(valid)*100) if valid else 0}%)")
    print(f"  Still open          : {len(open_)}")

    if results:
        best  = max(results, key=lambda r: r["ret_5d_%"] or -999)
        worst = min(results, key=lambda r: r["ret_5d_%"] or 999)
        print()
        print(f"  Best trade          : {best['symbol']} ({best['scan_date']}) {best['vol_ratio']}x vol → {best['ret_5d_%']:+.2f}% in 5d")
        print(f"  Worst trade         : {worst['symbol']} ({worst['scan_date']}) {worst['vol_ratio']}x vol → {worst['ret_5d_%']:+.2f}% in 5d")

    print(f"\n  Saved → {out}")
    print(f"{'='*60}\n")

    # Top signals
    print("  TOP ALERTS BY 5-DAY RETURN:")
    print(f"  {'Symbol':<14} {'Date':<12} {'Vol':>5}x  {'1d%':>7}  {'3d%':>7}  {'5d%':>7}  Outcome")
    print("  "+"-"*68)
    for r in sorted(results, key=lambda x: x["ret_5d_%"] or -999, reverse=True)[:15]:
        print(f"  {r['symbol']:<14} {r['scan_date']:<12} {r['vol_ratio']:>4}x  {str(r['ret_1d_%'] or ''):>7}  {str(r['ret_3d_%'] or ''):>7}  {str(r['ret_5d_%'] or ''):>7}  {r['outcome_5d']}")


if __name__ == "__main__":
    main()
