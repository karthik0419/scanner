from config.settings import *

def score_setup(data):
    score = 0

    cmp = data["cmp"]
    target = data["target"]
    stop = data["stop_loss"]

    upside = (target - cmp) / cmp
    risk = (cmp - stop) / cmp

    rr = upside / risk if risk > 0 else 0

    if rr >= RR_HIGH:
        score += 30
    elif rr >= RR_MEDIUM:
        score += 20

    if data["volume"]:
        score += 20

    if data["status"] == "BREAKOUT":
        score += 25
    elif data["status"] == "NEAR":
        score += 15

    if abs(cmp - data["breakout"]) / data["breakout"] < NEAR_BREAKOUT_THRESHOLD:
        score += 15

    return score, rr, upside * 100, risk * 100