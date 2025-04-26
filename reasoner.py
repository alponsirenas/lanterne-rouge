# reasoner.py

def decide_adjustment(readiness_score, hrv_today, hrv_avg, tss_weekly):
    """
    Apply basic agentic reasoning to decide if today's workout needs adjustment.
    """
    adjustments = []

    # 1. Check readiness score
    if readiness_score is not None and readiness_score < 70:
        adjustments.append("⚠️ Readiness low. Recommend replacing today's workout with a Zone 2 Endurance ride.")

    # 2. Check HRV drop
    if hrv_today < 0.85 * hrv_avg:
        adjustments.append("⚠️ HRV significantly lower than 7-day average. Suggest lower intensity today.")

    # 3. Check weekly TSS overage
    planned_weekly_tss = 500  # Example: assume your planned weekly TSS
    if tss_weekly is not None and tss_weekly > 1.2 * planned_weekly_tss:
        adjustments.append("⚠️ Weekly TSS high. Consider reducing next intensity workout.")

    # 4. No issues — proceed normally
    if not adjustments:
        adjustments.append("✅ Proceed with today's planned workout.")

    return adjustments