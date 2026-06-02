"""
Generate 3 charts per stock: Daily / Weekly / Monthly
Clean, labelled, easy to read.
"""
import os, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import mplfinance as mpf
import pandas as pd
from data.loader import _fetch_nse, _resample_weekly
from patterns.cup_handle_monthly import resample_monthly
from engine.scanner import scan_stock


def _detect_and_targets(symbol, df, dfw):
    """Use the daily scanner's scan_stock, fall back to pattern only."""
    res = scan_stock(symbol)
    if res:
        # Normalise field names to match gen_charts expectations
        res.setdefault("target_1", res.get("target1", res.get("target", 0)))
        res.setdefault("target_2", res.get("target2", res.get("target", 0)))
        res.setdefault("cmp", float(df["Close"].iloc[-1]))
        return res
    return None

CHARTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "charts")
for tf in ("daily", "weekly", "monthly"):
    os.makedirs(os.path.join(CHARTS_DIR, tf), exist_ok=True)

STOCKS = [
    "ABB","ABFRL","A2ZINFRA","360ONE","AADHARHFC","AARVI","ADANIENT",
    "ADANIPOWER","ACL","ABDL","ABBOTINDIA","ACC","ABREL","ABMINTLLTD",
    "ACI","ACEINTEG","ADANIENSOL","ADANIGREEN","3MINDIA","ACCURACY",
    "AAATECH","3IINFOLTD","ACE","AAVAS","ACMESOLAR","ABCAPITAL",
    "AARTIDRUGS","5PAISA","20MICRONS","ADFFOODS"
]

# ── level config: (value_key, label, color, linewidth, linestyle)
LEVELS = [
    ("target_2",  "T2",      "#00CC44", 1.5, "dashed"),
    ("target_1",  "T1",      "#00FF88", 2.0, "dashed"),
    ("breakout",  "BO",      "#2196F3", 2.0, "dashed"),
    ("cmp",       "CMP",     "#FFFFFF", 2.5, "solid"),
    ("stop_loss", "SL",      "#FF4444", 2.0, "dashed"),
]

STYLE = mpf.make_mpf_style(
    base_mpf_style="nightclouds",
    marketcolors=mpf.make_marketcolors(
        up="#26A69A", down="#EF5350",
        edge="inherit", wick="inherit",
        volume={"up": "#26A69A", "down": "#EF5350"},
    ),
    facecolor="#0D1117",
    figcolor="#0D1117",
    gridcolor="#1C2333",
    gridstyle="--",
    gridaxis="both",
    rc={
        "axes.labelcolor":  "#AAAAAA",
        "xtick.color":      "#AAAAAA",
        "ytick.color":      "#AAAAAA",
        "axes.edgecolor":   "#2A3A5C",
        "font.size":        10,
    }
)


def _save(df, tf_label, symbol, res, bars, mav):
    orig_len = len(df)
    df = df.tail(bars).copy()
    df.index.name = "Date"
    if len(df) < 10:
        return
    bars = len(df)

    # Clip extreme wick outliers (>4x IQR from median) to avoid scale distortion
    import numpy as np
    for col in ("High", "Low"):
        q1, q3 = df[col].quantile(0.05), df[col].quantile(0.95)
        iqr = q3 - q1
        df[col] = df[col].clip(q1 - 4*iqr, q3 + 4*iqr)

    # Build hlines + colours
    hline_vals, hline_cols, hline_styles, hline_widths = [], [], [], []
    for key, _, col, lw, ls in LEVELS:
        v = res.get(key, 0)
        if v and v > 0:
            hline_vals.append(v)
            hline_cols.append(col)
            hline_styles.append(ls)
            hline_widths.append(lw)

    hlines = dict(
        hlines=hline_vals,
        colors=hline_cols,
        linestyle=hline_styles,
        linewidths=hline_widths,
    )

    # Set Y-axis range to include all levels with 10% padding
    all_levels = [v for v in [res.get(k,0) for k in ("stop_loss","cmp","breakout","target_1","target_2")] if v > 0]
    price_min = min(df["Low"].min(), min(all_levels) if all_levels else df["Low"].min())
    price_max = max(df["High"].max(), max(all_levels) if all_levels else df["High"].max())
    padding   = (price_max - price_min) * 0.08
    ylim      = (price_min - padding, price_max + padding)

    fig, axes = mpf.plot(
        df, type="candle", style=STYLE,
        volume=True, mav=mav,
        hlines=hlines,
        figsize=(16, 9),
        ylim=ylim,
        returnfig=True,
        tight_layout=True,
    )

    ax = axes[0]

    # ── Pattern annotations helper
    def _shade(x0, x1, color, label, alpha=0.12):
        if x1 > x0 >= 0:
            ax.axvspan(x0, x1, alpha=alpha, color=color, zorder=0)
            ax.text((x0+x1)/2, ax.get_ylim()[1]*0.98, label,
                    ha="center", va="top", fontsize=8, color=color, fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.2", fc="#0D1117", ec=color, alpha=0.85))

    pattern = res.get("pattern", "")
    offset  = orig_len - bars

    # ── Cup & Handle shading
    cup_start    = res.get("cup_start_idx")
    cup_end      = res.get("cup_end_idx")
    handle_start = res.get("handle_start_idx")
    handle_end   = res.get("handle_end_idx")

    # Cup & Handle
    if cup_start is not None and "Cup" in pattern:
        cs = max(cup_start - offset, 0);  ce = max(cup_end - offset, 0)
        hs = max(handle_start - offset, 0); he = min(handle_end - offset, bars-1)
        _shade(cs, ce, "#2196F3", "CUP", alpha=0.10)
        _shade(hs, he, "#FF9800", "HANDLE", alpha=0.15)

    # Double Bottom — shade the two bottom regions
    elif "Double Bottom" in pattern:
        b1 = res.get("bottom_1"); b2 = res.get("bottom_2")
        window = res.get("window", 60)
        w_start = max(bars - window, 0)
        w_mid   = w_start + window // 2
        _shade(w_start, w_mid,  "#9C27B0", "BOTTOM 1", alpha=0.10)
        _shade(w_mid,   bars-1, "#E91E63", "BOTTOM 2", alpha=0.10)

    # Channel Breakout — shade the channel region
    elif "Channel" in pattern:
        chan_bars = min(80, bars)
        _shade(bars - chan_bars, bars - 1, "#00BCD4", "CHANNEL", alpha=0.08)

    # Triangle — shade the converging zone
    elif "Triangle" in pattern:
        tri_bars = min(60, bars)
        _shade(bars - tri_bars, bars - 1, "#8BC34A", "TRIANGLE", alpha=0.08)

    # Darvas Box — shade the box
    elif "Darvas" in pattern:
        box_bars = min(40, bars)
        _shade(bars - box_bars, bars - 1, "#FF5722", "DARVAS BOX", alpha=0.10)

    # Flag / Pennant — shade the pole + flag
    elif "Flag" in pattern or "Pennant" in pattern:
        flag_bars = min(30, bars)
        pole_bars = min(60, bars)
        _shade(bars - pole_bars, bars - flag_bars, "#FFEB3B", "POLE",   alpha=0.08)
        _shade(bars - flag_bars, bars - 1,         "#FF9800", "FLAG",   alpha=0.12)

    # Descending Wedge
    elif "Wedge" in pattern:
        wedge_bars = min(80, bars)
        _shade(bars - wedge_bars, bars - 1, "#76FF03", "WEDGE", alpha=0.08)

    # Break & Retest / S&R
    elif "Retest" in pattern or "S&R" in pattern or "Breakout" in pattern:
        _shade(max(bars - 20, 0), bars - 1, "#00E5FF", "RETEST ZONE", alpha=0.10)

    # ── Title
    t1   = res.get("target_1", 0)
    t2   = res.get("target_2", 0)
    cmp_ = res.get("cmp", 0)
    bo   = res.get("breakout", 0)
    sl   = res.get("stop_loss", 0)
    upside = round((t1 - cmp_) / cmp_ * 100, 1) if cmp_ else 0
    risk   = round((cmp_ - sl)  / cmp_ * 100, 1) if cmp_ else 0
    rr     = round(upside / risk, 2) if risk else 0

    fig.suptitle(
        f"{symbol}  [{tf_label}]   {res.get('pattern','')}   ({res.get('status','')})",
        fontsize=13, fontweight="bold", color="#E0E0E0", y=0.98,
        wrap=True,
    )

    # ── Right-side labels on each level
    xmax = len(df) - 1
    label_map = {k: (lbl, col) for k, lbl, col, _, _ in LEVELS}
    for key, lbl, col, _, _ in LEVELS:
        v = res.get(key, 0)
        if not v or v <= 0:
            continue
        ax.annotate(
            f" {lbl}  {v:,.2f}",
            xy=(1.0, v), xycoords=("axes fraction", "data"),
            fontsize=9.5, fontweight="bold", color=col,
            va="center",
            bbox=dict(boxstyle="round,pad=0.2", fc="#0D1117", ec=col, lw=0.8, alpha=0.9),
        )

    # ── Info box bottom-left
    info = (
        f"CMP  {cmp_:,.2f}    BO  {bo:,.2f}    SL  {sl:,.2f}\n"
        f"T1  {t1:,.2f}  (+{upside}%)    T2  {t2:,.2f}    RR  {rr}"
    )
    ax.text(
        0.01, 0.02, info,
        transform=ax.transAxes,
        fontsize=9, color="#CCCCCC",
        va="bottom", ha="left",
        bbox=dict(boxstyle="round,pad=0.4", fc="#161B27", ec="#2A3A5C", alpha=0.9),
    )

    # ── Legend
    patches = [mpatches.Patch(color=col, label=f"{lbl}") for _, lbl, col, _, _ in LEVELS
               if res.get({"target_2":"target_2","target_1":"target_1",
                           "breakout":"breakout","cmp":"cmp","stop_loss":"stop_loss"}.get(_,""),0)]
    if patches:
        ax.legend(handles=patches, loc="upper left", fontsize=8,
                  facecolor="#161B27", edgecolor="#2A3A5C", labelcolor="#CCCCCC")

    out = os.path.join(CHARTS_DIR, tf_label.lower(), f"{symbol}.png")
    fig.savefig(out, dpi=100, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def plot(symbol):
    df = _fetch_nse(symbol, days=730)
    if df is None or len(df) < 140:
        print(f"  {symbol}: no data"); return

    dfw = _resample_weekly(df)
    dfm = resample_monthly(df)

    res = _detect_and_targets(symbol, df, dfw)
    if not res:
        print(f"  {symbol}: no pattern"); return

    _save(df,  "Daily",   symbol, res, bars=180, mav=(20, 50))
    _save(dfw, "Weekly",  symbol, res, bars=104, mav=(10, 30))
    _save(dfm, "Monthly", symbol, res, bars=60,  mav=(6, 12))
    print(f"  {symbol}: 3 charts saved")


if __name__ == "__main__":
    print(f"Saving to {CHARTS_DIR}/daily|weekly|monthly\n")
    for s in STOCKS:
        plot(s)
    print("\nDone.")
