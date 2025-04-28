# reasoner.py

"""
Decide if today's workout should be adjusted based on readiness, CTL,
ATL, and TSB.
"""


def decide_adjustment(readiness_score, ctl, atl, tsb):
    recommendations = []

    # 1. Basic Readiness Checks
    if readiness_score is not None and readiness_score < 60:
        recommendations.append(
            "⚠️ Readiness is low (<60). Consider reducing workout intensity or "
            "volume today."
        )

    # 2. TSB (Form) Checks
    if tsb < -20:
        recommendations.append(
            "🚨 Form is very negative (TSB < -20). Strongly recommend easier or "
            "recovery day."
        )
    elif tsb < -10:
        recommendations.append(
            "⚠️ Form is moderately negative (TSB < -10). Training OK but monitor "
            "fatigue."
        )
    elif tsb > 10:
        recommendations.append(
            "✅ Form is highly positive (TSB > 10). Excellent day for intensity or "
            "longer ride."
        )

    # 3. CTL Trend (Optional Extension Later)
    if ctl < 30:
        recommendations.append(
            "⚠️ Chronic fitness level (CTL) is relatively low (<30). Gradually "
            "build volume."
        )
    elif ctl > 70:
        recommendations.append(
            "✅ Chronic fitness (CTL > 70) is excellent. Maintain consistency."
        )

    # Default recommendation
    if not recommendations:
        recommendations.append(
            "✅ All metrics look good. Proceed with planned workout."
        )

    return recommendations
