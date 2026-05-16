# engine/scanner.py

from data.loader import fetch_multi_tf
from patterns.breakout import detect_breakout
from patterns.retest import detect_retest
from patterns.compression import detect_compression
from patterns.cup_handle import detect_cup_handle, detect_cup_handle_weekly
from patterns.double_top_bottom import detect_double_top, detect_double_bottom
from patterns.darvas_box import detect_darvas_box
from patterns.flags import detect_flag_pennant, detect_pennant
from scoring.scorer import score_setup
from utils.entry_4h import detect_4h_entry
from utils.pattern_validator import validate_pattern_quality
from utils.target_calculator import calculate_advanced_targets
from utils.sector_analyzer import analyze_stock_sector, get_market_conditions, filter_by_market_conditions
from utils.performance_tracker import get_pattern_success_rate
from utils.verification_tools import generate_full_verification_report
from utils.entry_confirmation import confirm_entry_signal


def scan_stock(symbol):
    # 🔥 MULTI TIMEFRAME DATA
    df_daily, df_weekly, df_4h = fetch_multi_tf(symbol)

    if df_daily is None:
        return None

    # -----------------------
    # 🔥 DAILY PATTERN (Advanced)
    # -----------------------
    result = (
        detect_cup_handle_weekly(df_weekly) or  # Highest priority — weekly C&H
        detect_cup_handle(df_daily) or  # Daily C&H
        detect_double_bottom(df_daily) or  # Reversal
        detect_double_top(df_daily) or  # Short setup
        detect_darvas_box(df_daily) or  # Consolidation breakout
        detect_flag_pennant(df_daily) or  # Continuation
        detect_pennant(df_daily) or  # Continuation
        detect_retest(df_daily) or  # Basic
        detect_compression(df_daily) or  # Basic
        detect_breakout(df_daily)  # Basic
    )

    if not result:
        return None

    # -----------------------
    # 🔥 ADVANCED PATTERN VALIDATION
    # -----------------------
    is_valid_pattern, validation_score, validation_reasons = validate_pattern_quality(df_daily, result["pattern"], result)
    
    if not is_valid_pattern:
        return None

    # -----------------------
    # 🔥 4H ENTRY LOGIC
    # -----------------------
    entry_ok, entry_data = detect_4h_entry(df_4h, result["breakout"])

    # -----------------------
    # 🔥 ADVANCED TARGET CALCULATION
    # -----------------------
    advanced_targets = calculate_advanced_targets(df_daily, result["pattern"], result)
    
    # Update result with advanced targets
    result.update({
        "target1": advanced_targets["targets"][0] if len(advanced_targets["targets"]) > 0 else result["target"],
        "target2": advanced_targets["targets"][1] if len(advanced_targets["targets"]) > 1 else result["target"],
        "target3": advanced_targets["targets"][2] if len(advanced_targets["targets"]) > 2 else result["target"],
        "stop_loss": advanced_targets["stop_loss"],
        "atr": advanced_targets["atr"],
        "target_type": advanced_targets["target_type"]
    })

    # -----------------------
    # 🔥 BASE SCORING
    # -----------------------
    score, rr, upside, risk = score_setup(result)

    # ❌ Reject only invalid setups
    if rr == 0 or risk <= 0:
        return None

    # -----------------------------
    # 🔥 SOFT SCORING (ENHANCED)
    # -----------------------------
    bonus = 0

    # Volume contribution
    if result["volume"]:
        bonus += 10

    # Distance to breakout
    distance = abs(result["cmp"] - result["breakout"]) / result["breakout"]

    if distance < 0.02:
        bonus += 20
    elif distance < 0.05:
        bonus += 15
    elif distance < 0.10:
        bonus += 8

    # RR contribution
    if rr >= 2:
        bonus += 15
    elif rr >= 1.2:
        bonus += 10
    elif rr >= 1.0:
        bonus += 5

    # Pattern priority (Advanced patterns get higher bonus)
    if result["pattern"] == "Cup & Handle":
        bonus += 25  # Very reliable
    elif result["pattern"] == "Double Bottom":
        bonus += 20  # Strong reversal
    elif result["pattern"] == "Double Top":
        bonus += 20  # Strong reversal
    elif result["pattern"] == "Darvas Box":
        bonus += 18  # Consolidation breakout
    elif result["pattern"] == "Bullish Flag":
        bonus += 15  # Continuation
    elif result["pattern"] == "Bearish Flag":
        bonus += 15  # Continuation
    elif result["pattern"] == "Bullish Pennant":
        bonus += 15  # Continuation
    elif result["pattern"] == "Bearish Pennant":
        bonus += 15  # Continuation
    elif result["pattern"] == "Breakout Retest":
        bonus += 10  # Basic pattern
    elif result["pattern"] == "Higher-Low Compression":
        bonus += 8   # Basic pattern

    # Validation quality bonus
    bonus += validation_score * 0.2  # Add validation score as bonus

    # Status boost
    if result["status"] == "BREAKOUT":
        bonus += 10
    elif result["status"] == "NEAR":
        bonus += 5
    elif result["status"] == "PRE_BREAKOUT":
        bonus += 10

    # -----------------------------
    # 🔥 4H ENTRY SCORING (KEY)
    # -----------------------------
    if entry_ok:
        bonus += 20  # strong entry signal

    # confidence scaling
    bonus += entry_data.get("confidence", 0) * 3

    score += bonus

    # -----------------------------
    # FINAL SELECTION
    # -----------------------------
    if score < 10:
        return None

    # Add sector analysis
    sector_analysis = analyze_stock_sector(symbol)
    result.update(sector_analysis)

    # Add pattern success rate from historical data
    pattern_success_rate, pattern_info = get_pattern_success_rate(result["pattern"])
    
    # Generate verification report (Step 6)
    verification_report = generate_full_verification_report(df_daily, result)
    
    # Generate entry confirmation (Step 7)
    entry_confirmation = confirm_entry_signal(df_daily, df_4h, df_weekly, result)
    
    result.update({
        "symbol": symbol,
        "score": round(score, 2),
        "rr": round(rr, 2),
        "upside_pct": round(upside, 2),
        "risk_pct": round(risk, 2),
        "distance_to_breakout": round(distance, 3),
        "entry_signal": entry_ok,
        "entry_confidence": entry_data.get("confidence", 0),
        "pattern_success_rate": pattern_success_rate,
        "pattern_trades_info": pattern_info,
        # Step 6: Verification Tools
        "verification_score": verification_report["confidence_level"]["percentage"],
        "verification_rating": verification_report["confidence_level"]["level"],
        "verification_factors": len(verification_report["risk_factors"]),
        "verification_recommendation": verification_report["final_recommendation"],
        # Step 7: Entry Confirmation
        "entry_confirmation_score": entry_confirmation["overall_score"],
        "entry_confidence_level": entry_confirmation["confidence_level"],
        "entry_recommendation": entry_confirmation["recommendation"],
        "entry_signals_count": len(entry_confirmation["signals"])
    })

    return result