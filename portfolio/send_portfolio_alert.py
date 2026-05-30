"""
Send portfolio entry log to Telegram.
Uses existing TELEGRAM_BOT_TOKEN and CHAT_ID from .env
"""

import os, sys, io
import requests
from datetime import datetime

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_env():
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
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


def main():
    env = load_env()
    token   = env.get("TELEGRAM_BOT_TOKEN") or env.get("TELEGRAM_TOKEN")
    chat_id = env.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("Missing telegram credentials in .env")
        return

    msg = f"""<b>🎯 PORTFOLIO ENTRY LOG — 27 May 2026</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>💼 Capital deployed:</b> ₹49,773 / ₹50,000
<b>🎯 Strategy:</b> Swing trading (4-12 weeks)
<b>📊 Risk:R reward:</b> 1:3.65

━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>1️⃣ GREAVESCOT</b>  (Top Conviction — 35.7%)
🏭 Auto/EV — Greaves Cotton
📥 BUY: 95 sh @ ₹183.50 = ₹17,800
🛑 STOP: ₹155 (GTT active ✅)
🎯 TARGET: ₹286 (+55.9%)
📈 Pattern: Cup &amp; Handle Daily | Score 105
💡 Why: Cleanest pattern, rising volume on right rim
━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>2️⃣ HIKAL</b>
🏭 Pharma midcap
📥 BUY: 54 sh @ ₹223.15 = ₹12,050
🛑 STOP: ₹191 (GTT active ✅)
🎯 TARGET: ₹335 (+50.2%)
📈 Pattern: Cup &amp; Handle Daily | Score 105
💡 Why: Clean cup formed Jan-Apr, handle complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>3️⃣ HINDALCO</b>
🏭 Aluminum Large Cap
📥 BUY: 10 sh @ ₹1,146.10 = ₹11,461
🛑 STOP: ₹1,032 (GTT active ✅)
🎯 TARGET: ₹1,592 (+38.9%)
📈 Pattern: Cup &amp; Handle Weekly | Score 110
💡 Why: Highest quality chart, large cap safety
━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>4️⃣ PSPPROJECT</b>
🏭 Construction / Infra
📥 BUY: 10 sh @ ₹846.25 = ₹8,462
🛑 STOP: ₹731 (GTT active ✅)
🎯 TARGET: ₹1,323 (+56.4%)
📈 Pattern: Cup &amp; Handle Daily | Score 97
💡 Why: Highest RR (4.17x), watch for breakout
━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>📊 Portfolio Risk Summary:</b>
🛑 Max Loss: -₹6,905 (-13.9%)
🎯 Max Gain: +₹25,226 (+50.7%)
⚖️ Avg RR: 3.65x

<b>🔑 Trading Rules:</b>
✅ All stops placed on Kite (GTT active)
✅ Hold period: 4-12 weeks
✅ Book half at +25%, trail rest
✅ Exit if no breakout in 4 weeks

⚠️ <i>For self-tracking. Not financial advice.</i>
━━━━━━━━━━━━━━━━━━━━━━━━━━━
🕐 {datetime.now().strftime('%d %b %Y %H:%M')}
"""

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(url, json={
        "chat_id":    chat_id,
        "text":       msg,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }, timeout=15)

    if resp.ok:
        print("✅ Portfolio entry log sent to Telegram")
    else:
        print(f"❌ Failed: {resp.status_code} - {resp.text}")


if __name__ == "__main__":
    main()
