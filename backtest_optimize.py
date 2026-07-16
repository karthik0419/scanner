"""
Volume Alert Optimizer — tests all filter permutations to maximise win rate.
Filters tested:
  - vol_threshold : 2.0 / 3.0 / 4.0 / 5.0
  - green_day     : True / False  (close > open on surge day)
  - min_score     : 0 / 70 / 85 / 100
  - status_filter : any / NEAR+BREAKOUT only
  - proximity_pct : any / within 15% / within 10% / within 5% of breakout

Output: results/backtest_optimize.csv  — sorted by win rate then sample size
"""
import os, sys, csv, glob, warnings, itertools
warnings.filterwarnings("ignore")
import logging, pandas as pd
for n in ["yfinance","urllib3","peewee"]: logging.getLogger(n).setLevel(logging.CRITICAL)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data.loader import _fetch_nse

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


# ── Load and cache all data upfront ─────────────────────────────────────────

def load_all_scans():
    scans = []
    for f in sorted(glob.glob(os.path.join(RESULTS_DIR, "results_*.csv"))):
        date_str = os.path.basename(f).replace("results_","").replace(".csv","")[:10]
        try:
            for row in csv.DictReader(open(f, encoding="utf-8", errors="ignore")):
                sym = row.get("symbol","").replace(".NS","")
                if not sym: continue
                try:    score = float(row.get("score",0) or 0)
                except: score = 0
                try:    cmp   = float(row.get("cmp",0) or 0)
                except: cmp   = 0
                try:    bo    = float(row.get("breakout",0) or 0)
                except: bo    = 0
                scans.append({
                    "scan_date": date_str,
                    "symbol":    sym,
                    "pattern":   row.get("pattern",""),
                    "score":     score,
                    "status":    row.get("status",""),
                    "cmp":       cmp,
                    "breakout":  bo,
                })
        except Exception:
            pass
    return scans


def build_signal_db(scans):
    """For each (symbol, scan_date) compute vol ratio, green_day, forward returns."""
    from collections import defaultdict
    sym_records = defaultdict(list)
    for s in scans:
        sym_records[s["symbol"]].append(s)

    db = []
    total = len(sym_records)
    done  = 0
    for sym, records in sym_records.items():
        done += 1
        if done % 20 == 0:
            print(f"  Loading price data {done}/{total}...", end="\r")
        df = _fetch_nse(sym, days=180)
        if df is None or len(df) < 30:
            continue

        for rec in records:
            scan_dt = pd.Timestamp(rec["scan_date"])
            before  = df[df.index <= scan_dt]
            if len(before) < 22:
                continue

            today_row = before.iloc[-1]
            avg_vol   = float(before["Volume"].iloc[-21:-1].mean())
            today_vol = float(today_row["Volume"])
            if avg_vol <= 0:
                continue

            vol_ratio = round(today_vol / avg_vol, 2)
            green_day = float(today_row["Close"]) > float(today_row["Open"])
            entry     = float(today_row["Close"])

            after = df[df.index > scan_dt]
            def pct(i):
                if len(after) <= i: return None
                return round((float(after["Close"].iloc[i]) - entry) / entry * 100, 2)

            prox = abs(entry - rec["breakout"]) / rec["breakout"] * 100 if rec["breakout"] > 0 else 999

            db.append({
                "scan_date":  rec["scan_date"],
                "symbol":     sym,
                "score":      rec["score"],
                "status":     rec["status"],
                "vol_ratio":  vol_ratio,
                "green_day":  green_day,
                "prox_pct":   round(prox, 2),
                "ret_1d":     pct(0),
                "ret_3d":     pct(2),
                "ret_5d":     pct(4),
            })
    print()
    return db


# ── Filter + score ────────────────────────────────────────────────────────────

def apply_filters(db, vol_thr, green_only, min_score, status_strict, max_prox):
    filtered = []
    for r in db:
        if r["vol_ratio"] < vol_thr:                   continue
        if green_only and not r["green_day"]:           continue
        if r["score"] < min_score:                     continue
        if status_strict and r["status"] not in ("NEAR","BREAKOUT"): continue
        if r["prox_pct"] > max_prox:                   continue
        filtered.append(r)
    return filtered


def win_rate(filtered):
    valid = [r for r in filtered if r["ret_5d"] is not None]
    if len(valid) < 3:
        return None, None, None
    wins = sum(1 for r in valid if r["ret_5d"] > 0)
    avg  = round(sum(r["ret_5d"] for r in valid) / len(valid), 2)
    return round(wins / len(valid) * 100), avg, len(valid)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("="*65)
    print("  VOLUME ALERT OPTIMIZER")
    print("="*65)

    scans = load_all_scans()
    print(f"\n  Building signal database from {len(scans)} scan records...")
    db = build_signal_db(scans)
    print(f"  Database built: {len(db)} signal records\n")

    # Parameter grid
    vol_thresholds   = [2.0, 3.0, 4.0, 5.0]
    green_day_opts   = [False, True]
    min_score_opts   = [0, 70, 85, 100]
    status_opts      = [False, True]   # False=any, True=NEAR/BREAKOUT only
    prox_opts        = [999, 20, 15, 10]  # max % from breakout

    combos = list(itertools.product(vol_thresholds, green_day_opts,
                                    min_score_opts, status_opts, prox_opts))
    print(f"  Testing {len(combos)} parameter combinations...\n")

    results = []
    for vol, green, score, strict, prox in combos:
        filtered = apply_filters(db, vol, green, score, strict, prox)
        wr, avg_r, n = win_rate(filtered)
        if wr is None:
            continue
        results.append({
            "win_rate_%":    wr,
            "avg_5d_ret_%":  avg_r,
            "sample_size":   n,
            "vol_threshold": vol,
            "green_day":     green,
            "min_score":     score,
            "status_strict": strict,
            "max_prox_%":    prox,
        })

    results.sort(key=lambda x: (-x["win_rate_%"], -x["avg_5d_ret_%"], -x["sample_size"]))

    # Print top 20
    print(f"  TOP 20 COMBINATIONS (by win rate):")
    print(f"  {'WR%':>5} {'Avg5d':>7} {'N':>4}  {'VolThr':>7}  {'Green':>6}  {'MinScore':>9}  {'Status':>7}  {'MaxProx':>8}")
    print("  "+"-"*72)
    for r in results[:20]:
        print(f"  {r['win_rate_%']:>4}%  {r['avg_5d_ret_%']:>+6.2f}%  {r['sample_size']:>4}  "
              f"{r['vol_threshold']:>6}x  {'YES' if r['green_day'] else 'NO':>6}  "
              f"{r['min_score']:>9}  {'NEAR/BO' if r['status_strict'] else 'ANY':>7}  "
              f"{r['max_prox_%']:>7}%")

    # Save all
    out = os.path.join(RESULTS_DIR, "backtest_optimize.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader(); w.writerows(results)

    best = results[0]
    print(f"\n  {'='*65}")
    print(f"  BEST CONFIGURATION:")
    print(f"    Volume threshold : {best['vol_threshold']}x")
    print(f"    Green day only   : {best['green_day']}")
    print(f"    Min score        : {best['min_score']}")
    print(f"    Status filter    : {'NEAR/BREAKOUT only' if best['status_strict'] else 'Any'}")
    print(f"    Max proximity    : within {best['max_prox_%']}% of breakout")
    print(f"    Win rate         : {best['win_rate_%']}%")
    print(f"    Avg 5d return    : {best['avg_5d_ret_%']:+.2f}%")
    print(f"    Sample size      : {best['sample_size']} trades")
    print(f"  {'='*65}")
    print(f"\n  Saved → {out}\n")


if __name__ == "__main__":
    main()
