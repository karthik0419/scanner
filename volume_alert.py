"""
Volume Surge Alert
Runs after the daily scan. Checks all stocks that were flagged as setups
in the last 7 days — if any of them show unusual volume today, fires a
separate Telegram alert.

Logic:
  - Load past 7 days of scan CSVs from results/
  - Deduplicate symbols (keep most recent score/pattern)
  - Fetch today's data for each
  - Flag if: current_volume > avg_20d_volume * SURGE_THRESHOLD
  - Send Telegram if any surges found
"""
import os, sys, csv, glob, json, warnings, argparse
warnings.filterwarnings("ignore")
import logging
for n in ["yfinance","urllib3","peewee"]: logging.getLogger(n).setLevel(logging.CRITICAL)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.loader import _fetch_nse

SURGE_THRESHOLD = 2.0   # volume must be 2x 20-day avg
LOOKBACK_DAYS   = 7     # how many days of past CSVs to check
RESULTS_DIR     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


def load_env():
    env = {}
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    try:
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    except Exception:
        pass
    return env


def send_telegram(token, chat_id, text):
    import urllib.request, urllib.parse
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }).encode()
    try:
        req = urllib.request.Request(url, data=data)
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:
        print(f"  Telegram error: {e}")
        return False


def load_past_setups():
    """Load all flagged setups from last LOOKBACK_DAYS scan CSVs."""
    setups = {}  # symbol -> {pattern, score, status, cmp, date}
    files = sorted([f for f in glob.glob(os.path.join(RESULTS_DIR, "results_*.csv")) if "_all" not in f], reverse=True)
    for f in files[:LOOKBACK_DAYS * 2]:  # allow for multiple runs per day
        try:
            date_str = os.path.basename(f).replace("results_","").replace(".csv","")[:10]
            for row in csv.DictReader(open(f, encoding="utf-8", errors="ignore")):
                sym = row.get("symbol","").replace(".NS","")
                if not sym: continue
                if sym not in setups:  # keep most recent
                    setups[sym] = {
                        "pattern": row.get("pattern",""),
                        "score":   row.get("score",""),
                        "status":  row.get("status",""),
                        "cmp":     row.get("cmp",""),
                        "date":    date_str,
                    }
        except Exception:
            pass
    return setups


def check_volume_surge(symbol, setup):
    """Returns surge info dict or None."""
    df = _fetch_nse(symbol, days=60)
    if df is None or len(df) < 22:
        return None

    avg_vol  = float(df["Volume"].tail(21).iloc[:-1].mean())  # 20-day avg excl today
    today_vol = float(df["Volume"].iloc[-1])
    curr      = float(df["Close"].iloc[-1])
    ratio     = round(today_vol / avg_vol, 1) if avg_vol > 0 else 0

    if ratio < SURGE_THRESHOLD:
        return None

    return {
        "symbol":   symbol,
        "ratio":    ratio,
        "volume":   today_vol,
        "avg_vol":  avg_vol,
        "cmp":      curr,
        "pattern":  setup["pattern"],
        "status":   setup["status"],
        "score":    setup["score"],
        "flagged":  setup["date"],
    }


def format_message(surges):
    if not surges:
        return None

    lines = [
        "🚨 <b>[V1] VOLUME SURGE ALERT</b>",
        f"Previously flagged setups showing unusual activity\n",
    ]
    for s in surges:
        icon = "🔥" if s["ratio"] >= 5 else "⚡" if s["ratio"] >= 3 else "📈"
        lines += [
            f"━━━━━━━━━━━━━━━━━━━",
            f"{icon} <b>{s['symbol']}</b>  |  {s['pattern']}  ({s['status']})",
            f"📊 Volume: {s['volume']/1e6:.1f}M  =  <b>{s['ratio']}x avg</b>",
            f"💰 CMP: ₹{s['cmp']:,.2f}  |  Score: {s['score']}  |  Flagged: {s['flagged']}",
        ]
    lines += ["━━━━━━━━━━━━━━━━━━━", "", "⚠️ Monitor these closely — big moves may follow."]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Volume Surge Alert")
    parser.add_argument("--threshold", type=float, default=SURGE_THRESHOLD)
    parser.add_argument("--dry-run",   action="store_true", help="Print without sending Telegram")
    args = parser.parse_args()

    threshold = args.threshold

    print(f"\n{'='*55}")
    print(f"  VOLUME SURGE ALERT — checking past {LOOKBACK_DAYS} days")
    print(f"  Threshold: {threshold}x avg volume")
    print(f"{'='*55}")

    setups = load_past_setups()
    print(f"\n  Checking {len(setups)} previously flagged stocks...\n")

    surges = []
    for sym, setup in setups.items():
        result = check_volume_surge(sym, setup)
        if result:
            surges.append(result)
            icon = "🔥" if result["ratio"] >= 5 else "⚡" if result["ratio"] >= 3 else "📈"
            print(f"  {icon} {sym:<15} {result['ratio']}x vol | {setup['pattern']} | CMP ₹{result['cmp']:.2f} | flagged {setup['date']}")

    if not surges:
        print("  No volume surges detected.")
        return

    surges.sort(key=lambda x: x["ratio"], reverse=True)

    print(f"\n  Found {len(surges)} surge(s)")

    msg = format_message(surges)
    print(f"\n{msg}")

    if args.dry_run:
        print("\n  [DRY RUN] Telegram not sent.")
        return

    env = load_env()
    token   = env.get("TELEGRAM_BOT_TOKEN") or env.get("TELEGRAM_TOKEN") or os.environ.get("TELEGRAM_TOKEN")
    chat_id = env.get("TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("  ERROR: Missing TELEGRAM_TOKEN or TELEGRAM_CHAT_ID in .env")
        return

    if send_telegram(token, chat_id, msg):
        print("  Alert sent to Telegram ✅")
    else:
        print("  Failed to send alert.")


if __name__ == "__main__":
    main()
