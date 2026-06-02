"""
Telegram Notifier — Swing Screener v3
Reads today's results CSV and sends top setups to Telegram.

Usage:
  python telegram_notify.py                        # auto-picks latest results CSV
  python telegram_notify.py --csv results_x.csv   # specific file
  python telegram_notify.py --top 10              # how many setups to send (default 5)
"""

import os, sys, argparse, glob
import pandas as pd
import requests
from datetime import date

# Fix emoji printing on Windows terminals
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def load_env():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    env = {}
    try:
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    except FileNotFoundError:
        pass
    return env

def send_message(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        print(f"Telegram send failed: {e}")
        return False

def latest_csv():
    files = sorted(glob.glob("results_*.csv"), reverse=True)
    return files[0] if files else None

def pattern_emoji(pattern):
    mapping = {
        "Cup & Handle (Weekly)": "🏆",
        "Cup & Handle":          "🥇",
        "Break & Retest":        "🔄",
        "Ascending Triangle":    "📐",
        "Symmetrical Triangle":  "📐",
        "Channel Breakout":      "📉",
        "Darvas Box":            "📦",
        "S&R Breakout":          "🔓",
        "S&R Support":           "🛡",
        "Bullish Flag":          "🚩",
        "Resistance Breakout":   "💥",
        "No Pattern":            "📊",
    }
    return mapping.get(pattern, "📊")

def format_message(df, total_scanned, csv_file):
    today = date.today().strftime("%d %b %Y")
    total_setups = len(df)

    lines = [
        f"<b>🔍 SWING SCAN — {today}</b>",
        f"📊 Scanned: {total_scanned} stocks | Found: {total_setups} setups",
        "",
    ]

    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    for i, (_, row) in enumerate(df.iterrows()):
        symbol  = row["symbol"].replace(".NS", "")
        pattern = row["pattern"]
        cmp     = row["cmp"]
        breakout= row["breakout"]
        stop    = row["stop_loss"]
        target  = row["target"]
        upside  = row["upside_%"]
        rr      = row["rr"]
        score   = int(row["score"])
        emoji   = pattern_emoji(pattern)
        medal   = medals[i] if i < len(medals) else "▪️"

        tf     = row.get("timeframe", "-")
        sector = row.get("sector", "")
        signal = row.get("sector_signal", "")
        tf_icon = "📅 Monthly" if tf == "Monthly" else "📆 Weekly" if tf == "Weekly" else "📊 Daily"
        sec_icon = "🔥" if signal == "BOOM" else "↑" if signal == "RISING" else "↓" if signal == "COOLING" else "🔴" if signal == "WEAK" else ""
        sector_line = f"🏭 {sector} {sec_icon} {signal}" if sector and sector != "Unknown" else ""

        lines += [
            f"━━━━━━━━━━━━━━━━━━━",
            f"{medal} <b>{symbol}</b> | Score: {score} | {emoji} {pattern}",
            f"{tf_icon}" + (f"  |  {sector_line}" if sector_line else ""),
            f"💰 CMP: ₹{cmp:,.2f}  |  Entry: ₹{breakout:,.2f}",
            f"🛑 Stop: ₹{stop:,.2f}  |  🎯 Target: ₹{target:,.2f}",
            f"📈 Upside: {upside}%  |  RR: {rr}x",
        ]

    lines += [
        "━━━━━━━━━━━━━━━━━━━",
        "",
        "⚠️ For research only. Not financial advice.",
    ]

    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv",  default=None)
    parser.add_argument("--top",  type=int, default=5)
    parser.add_argument("--scanned", type=int, default=0, help="Total stocks scanned (optional)")
    args = parser.parse_args()

    # Load credentials
    env = load_env()
    token   = env.get("TELEGRAM_TOKEN") or os.environ.get("TELEGRAM_TOKEN")
    chat_id = env.get("TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("ERROR: TELEGRAM_TOKEN or TELEGRAM_CHAT_ID missing in .env")
        sys.exit(1)

    # Find CSV
    csv_file = args.csv or latest_csv()
    if not csv_file or not os.path.exists(csv_file):
        print(f"No results CSV found.")
        sys.exit(1)

    df = pd.read_csv(csv_file)
    if df.empty:
        print("No setups in CSV.")
        sys.exit(1)

    df = df.sort_values("score", ascending=False).head(args.top)

    total_scanned = args.scanned if args.scanned else len(df)

    msg = format_message(df, total_scanned, csv_file)

    print("Sending to Telegram...")
    print(msg)
    print()

    ok = send_message(token, chat_id, msg)
    if ok:
        print("Sent successfully.")
    else:
        print("Send failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
