"""
Historical Volume Alert Backtest
Simulates the full pipeline on 6 months of historical data for 200+ stocks.
For each trading day, runs:
  1. Pattern detection (was this stock flagged as a setup?)
  2. Volume surge check (2x+ avg volume?)
  3. Green day filter (close > open?)
  4. Forward returns 1/3/5/10 days

Tests all parameter combos and finds optimal configuration.
"""
import os, sys, csv, warnings, itertools
warnings.filterwarnings("ignore")
import logging, pandas as pd, numpy as np
for n in ["yfinance","urllib3","peewee"]: logging.getLogger(n).setLevel(logging.CRITICAL)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data.loader import _fetch_nse, _resample_weekly
from patterns.cup_handle import detect_cup_handle, detect_cup_handle_weekly
from patterns.double_bottom import detect_double_bottom
from patterns.channel import detect_descending_channel
from patterns.darvas_box import detect_darvas_box
from patterns.triangle import detect_triangle

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")

# Use the backbone50 + nifty200 as universe
UNIVERSE_FILES = ["backbone50.txt", "nifty200.txt", "nifty500.txt"]

def load_universe():
    syms = set()
    for fname in UNIVERSE_FILES:
        fpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), fname)
        try:
            with open(fpath) as f:
                for line in f:
                    s = line.strip()
                    if s and not s.startswith("#"):
                        syms.add(s.replace(".NS",""))
        except: pass
    return list(syms)


def detect_pattern(df_daily, df_weekly):
    return (
        detect_cup_handle_weekly(df_weekly) or
        detect_cup_handle(df_daily) or
        detect_double_bottom(df_daily) or
        detect_descending_channel(df_daily) or
        detect_darvas_box(df_daily) or
        detect_triangle(df_daily)
    )


def score_simple(result):
    cmp = result.get("cmp",0); tgt = result.get("target",0); sl = result.get("stop_loss",0)
    if cmp<=0 or sl<=0 or sl>=cmp: return 0
    upside = (tgt-cmp)/cmp*100; risk = (cmp-sl)/cmp*100
    rr = upside/risk if risk>0 else 0
    s = 0
    if rr>=3: s+=40
    elif rr>=2: s+=30
    elif rr>=1: s+=15
    if result.get("volume"): s+=15
    if result.get("status")=="NEAR": s+=10
    elif result.get("status")=="BREAKOUT": s+=20
    return s


def simulate_stock(sym, full_df, sim_days=120):
    """
    Slide a window across the last sim_days trading days.
    For each day d:
      - Run pattern detector on data up to d
      - Check volume surge vs 20-day avg
      - Record forward returns
    Returns list of signal records.
    """
    signals = []
    if full_df is None or len(full_df) < 160:
        return signals

    # We need at least 140 bars of history + 10 forward bars
    n = len(full_df)
    start_idx = max(140, n - sim_days - 10)

    for i in range(start_idx, n - 10):
        df_slice  = full_df.iloc[:i+1].copy()
        df_w      = df_slice.resample("W").agg({"Open":"first","High":"max","Low":"min","Close":"last","Volume":"sum"}).dropna()

        try:
            res = detect_pattern(df_slice, df_w)
        except Exception:
            res = None

        if not res:
            continue

        score = score_simple(res)
        if score < 10:
            continue

        # Volume surge
        avg_vol   = float(df_slice["Volume"].iloc[-21:-1].mean())
        today_vol = float(df_slice["Volume"].iloc[-1])
        if avg_vol <= 0:
            continue
        vol_ratio = round(today_vol / avg_vol, 2)

        green_day = float(df_slice["Close"].iloc[-1]) > float(df_slice["Open"].iloc[-1])
        entry     = float(df_slice["Close"].iloc[-1])
        bo        = res.get("breakout", 0)
        prox      = abs(entry - bo) / bo * 100 if bo > 0 else 999

        # Forward returns
        def fwd(days):
            idx = i + days
            if idx >= n: return None
            return round((float(full_df["Close"].iloc[idx]) - entry) / entry * 100, 2)

        signals.append({
            "symbol":    sym,
            "date":      str(df_slice.index[-1].date()),
            "pattern":   res.get("pattern",""),
            "status":    res.get("status",""),
            "score":     score,
            "vol_ratio": vol_ratio,
            "green_day": green_day,
            "prox_pct":  round(prox, 2),
            "ret_1d":    fwd(1),
            "ret_3d":    fwd(3),
            "ret_5d":    fwd(5),
            "ret_10d":   fwd(10),
        })

    return signals


def apply_filters(db, vol_thr, green_only, min_score, status_strict, max_prox):
    out = []
    for r in db:
        if r["vol_ratio"] < vol_thr: continue
        if green_only and not r["green_day"]: continue
        if r["score"] < min_score: continue
        if status_strict and r["status"] not in ("NEAR","BREAKOUT"): continue
        if r["prox_pct"] > max_prox: continue
        out.append(r)
    return out


def stats(filtered, hold_days=5):
    key = f"ret_{hold_days}d"
    valid = [r for r in filtered if r[key] is not None]
    if len(valid) < 5: return None
    wins = sum(1 for r in valid if r[key] > 0)
    avg  = round(sum(r[key] for r in valid) / len(valid), 2)
    wr   = round(wins / len(valid) * 100, 1)
    return {"wr": wr, "avg": avg, "n": len(valid)}


def main():
    print("="*65)
    print("  HISTORICAL VOLUME ALERT BACKTEST")
    print("  6-month simulation on 200+ stocks")
    print("="*65)

    universe = load_universe()
    print(f"\n  Universe: {len(universe)} stocks")
    print(f"  Simulating last 120 trading days per stock...\n")

    all_signals = []
    done = 0
    for sym in universe:
        done += 1
        print(f"  [{done:>3}/{len(universe)}] {sym:<20}", end="\r")
        df = _fetch_nse(sym, days=730)
        sigs = simulate_stock(sym, df, sim_days=120)
        all_signals.extend(sigs)

    print(f"\n\n  Total signals generated: {len(all_signals)}")
    vol_alerts = [s for s in all_signals if s["vol_ratio"] >= 2.0]
    print(f"  Signals with 2x+ volume: {len(vol_alerts)}")

    # Save raw signals
    if all_signals:
        raw_out = os.path.join(RESULTS_DIR, "backtest_historical_signals.csv")
        with open(raw_out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(all_signals[0].keys()))
            w.writeheader(); w.writerows(all_signals)
        print(f"  Raw signals saved → {raw_out}")

    # Optimize
    print(f"\n  Running parameter optimization...")
    combos = list(itertools.product(
        [2.0, 3.0, 4.0, 5.0, 7.0],   # vol threshold
        [False, True],                 # green day
        [0, 50, 70, 85, 100],         # min score
        [False, True],                 # status strict
        [999, 20, 15, 10, 5],         # max prox
    ))
    print(f"  Testing {len(combos)} combinations...\n")

    results = []
    for vol, green, score, strict, prox in combos:
        for hold in [1, 3, 5, 10]:
            filtered = apply_filters(all_signals, vol, green, score, strict, prox)
            s = stats(filtered, hold)
            if s is None: continue
            results.append({
                "hold_days":     hold,
                "win_rate_%":    s["wr"],
                "avg_ret_%":     s["avg"],
                "sample_size":   s["n"],
                "vol_threshold": vol,
                "green_day":     green,
                "min_score":     score,
                "status_strict": strict,
                "max_prox_%":    prox,
            })

    results.sort(key=lambda x: (-x["win_rate_%"], -x["avg_ret_%"], -x["sample_size"]))

    # Save
    opt_out = os.path.join(RESULTS_DIR, "backtest_optimize_historical.csv")
    with open(opt_out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader(); w.writerows(results)

    print(f"  TOP 20 CONFIGURATIONS:")
    print(f"  {'Hold':>5} {'WR%':>5} {'AvgRet':>7} {'N':>5}  {'VolThr':>7}  {'Green':>6}  {'Score':>6}  {'Status':>7}  {'Prox':>6}")
    print("  "+"-"*75)
    seen = set()
    printed = 0
    for r in results:
        key = (r["vol_threshold"], r["green_day"], r["min_score"], r["status_strict"], r["max_prox_%"])
        if key in seen: continue
        seen.add(key)
        print(f"  {r['hold_days']:>4}d  {r['win_rate_%']:>4}%  {r['avg_ret_%']:>+6.2f}%  {r['sample_size']:>5}  "
              f"{r['vol_threshold']:>6}x  {'YES' if r['green_day'] else 'NO':>6}  "
              f"{r['min_score']:>6}  {'NEAR/BO' if r['status_strict'] else 'ANY':>7}  "
              f"{r['max_prox_%']:>5}%")
        printed += 1
        if printed >= 20: break

    best = results[0]
    print(f"\n  {'='*65}")
    print(f"  OPTIMAL CONFIGURATION:")
    print(f"    Hold period      : {best['hold_days']} days")
    print(f"    Volume threshold : {best['vol_threshold']}x")
    print(f"    Green day only   : {best['green_day']}")
    print(f"    Min score        : {best['min_score']}")
    print(f"    Status           : {'NEAR/BREAKOUT' if best['status_strict'] else 'Any'}")
    print(f"    Max prox         : within {best['max_prox_%']}% of breakout")
    print(f"    Win rate         : {best['win_rate_%']}%")
    print(f"    Avg return       : {best['avg_ret_%']:+.2f}%")
    print(f"    Sample size      : {best['sample_size']} trades")
    print(f"  {'='*65}\n")


if __name__ == "__main__":
    main()
