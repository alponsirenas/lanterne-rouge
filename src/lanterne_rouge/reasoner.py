"""
Decide if today's workout should be adjusted based on readiness, CTL,
ATL, and TSB.
"""

from .mission_config import MissionConfig


def decide_adjustment(
    readiness_score: float,
    readiness_details: dict[str, float],
    ctl: float,
    atl: float,
    tsb: float,
    cfg: MissionConfig
) -> list[str]:
    recommendations = []

    # LLM-first override: delegate all adjustment logic to the LLM if enabled
    if getattr(cfg, "use_llm_for_plan", False):
        from .ai_clients import generate_workout_adjustment
        # generate_workout_adjustment should return list[str]
        return generate_workout_adjustment(
            readiness_score=readiness_score,
            readiness_details=readiness_details,
            ctl=ctl,
            atl=atl,
            tsb=tsb,
            mission_cfg=cfg
        )

    # 1. Basic Readiness Checks
    if readiness_score is not None and readiness_score < cfg.constraints.min_readiness:
        recommendations.append(
            f"⚠️ Readiness is low (<{cfg.constraints.min_readiness}). Consider reducing intensity or volume."
        )

    # 2. TSB (Form) Checks
    if tsb < cfg.constraints.min_tsb * 2:
        recommendations.append(
            "🚨 Form is very negative (TSB < -20). Strongly recommend easier or "
            "recovery day."
        )
    elif tsb < cfg.constraints.min_tsb:
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
    if ctl < cfg.targets.ctl_peak * 0.4:
        recommendations.append(
            "⚠️ Chronic fitness level (CTL) is relatively low (<30). Gradually "
            "build volume."
        )
    elif ctl > cfg.targets.ctl_peak * 0.9:
        recommendations.append(
            "✅ Chronic fitness (CTL > 70) is excellent. Maintain consistency."
        )

    # Example contributor-based rule (requires defining thresholds in config)
    if readiness_details.get("hrv_balance", 100) < cfg.constraints.min_readiness:
        recommendations.append(
            f"⚠️ HRV balance is low (<{cfg.constraints.min_readiness}). Favor recovery."
        )


    # Default recommendation
    if not recommendations:
        recommendations.append(
            "✅ All metrics look good. Proceed with planned workout."
        )

    return recommendations
