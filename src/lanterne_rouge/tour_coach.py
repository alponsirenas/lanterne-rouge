"""
Tour Coach - Core module for the Lanterne Rouge training plan application.

This module provides the main functionality for generating training recommendations
based on athlete data from Strava and wellness data from Oura.
"""

# This script generates a daily update for the Tour Coach program, including
# workout plans, readiness scores, and recommendations based on the user's
# data from Oura and Strava.

import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from lanterne_rouge.ai_clients import generate_workout_adjustment
from lanterne_rouge.memory_bus import (
    load_memory,
    log_decision,
    log_observation,
    log_reflection,
)
from lanterne_rouge.mission_config import MissionConfig, bootstrap
from lanterne_rouge.monitor import ATL_TC, CTL_TC, get_ctl_atl_tsb, get_oura_readiness
from lanterne_rouge.peloton_matcher import match_peloton_class
from lanterne_rouge.plan_generator import generate_workout_plan
from lanterne_rouge.reasoner import decide_adjustment

load_dotenv()


# Helper function to get the agent version
def get_version():
    """Get the current version of the Lanterne Rouge agent from the VERSION file."""
    try:
        with open(Path(__file__).resolve().parents[2] / "VERSION", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "0.0.0-dev"


# Helper: first non-empty line from list of strings
def first_line(lines: list[str]) -> str | None:
    """Return the first non‑empty line from a list of strings."""
    for ln in lines:
        if ln.strip():
            return ln.strip().lstrip("- ").strip()
    return None


def run(cfg: MissionConfig | None = None):
    """Generate the daily Tour Coach summary."""
    # Always reload mission configuration to ensure latest FTP value is used
    config_path = os.getenv("MISSION_CONFIG_PATH", "missions/tdf_sim_2025.toml")
    cfg = bootstrap(Path(config_path))  # Bootstrap both loads and caches to DB

    # Load agent memory
    memory = load_memory()

    # 1. Pull today's data
    readiness_score, hrv_balance, readiness_day = get_oura_readiness()

    # Get CTL, ATL, TSB with additional debug output
    print("\n===== BANNISTER MODEL DEBUG =====")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"Time Constants: CTL={CTL_TC} days, ATL={ATL_TC} days")
    ctl, atl, tsb = get_ctl_atl_tsb()
    print("================================\n")

    # Log today's observations to memory
    log_observation({
        "readiness_score": readiness_score,
        "hrv_balance": hrv_balance,
        "readiness_day": readiness_day,
        "ctl": ctl,
        "atl": atl,
        "tsb": tsb,
    })

    # 2. Decide if we need to adjust today's plan
    recommendations = decide_adjustment(
        readiness_score=readiness_score,
        readiness_details={
            "hrv_balance": hrv_balance,
            "readiness_day": readiness_day
        },
        ctl=ctl,
        atl=atl,
        tsb=tsb,
        cfg=cfg,
    )

    # Log decision (recommendations) to memory
    log_decision({"recommendations": recommendations})

    # Generate LLM‑driven workout adjustment lines
    adjustment_lines = generate_workout_adjustment(
        readiness_score=readiness_score,
        readiness_details={
            "hrv_balance": hrv_balance,
            "readiness_day": readiness_day,
        },
        ctl=ctl,
        atl=atl,
        tsb=tsb,
        mission_cfg=cfg,
    )

    # 3. Get today's workout plan (multi‑day planner may still be useful)
    workout = generate_workout_plan(cfg, memory)
    today_workout_type = workout.get("workout", "")
    today_workout_details = workout.get("description", "")

    # If the plan generator did not return a workout, fall back to the first
    # line suggested by the adjustment LLM.
    if not today_workout_type:
        fallback = first_line(adjustment_lines)
        if fallback:
            today_workout_type = fallback
            today_workout_details = ""
        else:
            today_workout_type = "No workout generated"

    # 4. Match to Peloton class
    peloton_class = match_peloton_class(today_workout_type)

    # 5. Read version
    version = get_version()

    # 6. Write the daily update
    today_display_date = datetime.now().strftime("%A, %B %d, %Y")

    summary_lines = []
    summary_lines.append(f"Date: {today_display_date}\n")
    summary_lines.append("Planned Workout:\n")
    summary_lines.append(f"- {today_workout_type} ({today_workout_details})\n")
    summary_lines.append("\nReadiness and Recovery:\n")
    summary_lines.append(
        f"- Readiness Score: {readiness_score if readiness_score else 'Unavailable'}\n"
    )
    summary_lines.append(
        f"- Readiness Day: {readiness_day if readiness_day else 'Unavailable'}\n"
    )
    summary_lines.append(f"- CTL (Fitness): {ctl if ctl else 'Unavailable'}\n")
    summary_lines.append(f"- ATL (Fatigue): {atl if atl else 'Unavailable'}\n")
    summary_lines.append(f"- TSB (Form): {tsb if tsb else 'Unavailable'}\n")
    summary_lines.append("\nRecommendation:\n")
    combined_recs = recommendations + [ln for ln in adjustment_lines if ln not in recommendations]
    for rec in combined_recs:
        summary_lines.append(f"- {rec}\n")
    summary_lines.append("\nPeloton Class Suggestion:\n")
    summary_lines.append(f"- {peloton_class}\n")
    summary_lines.append("\nNotes:\n")
    summary_lines.append(
        "- Adjust fueling based on today's effort. Stay hydrated and recover smart.\n"
    )
    summary_lines.append(f"\nGenerated by Tour Coach Agent v{version}\n")

    summary = "".join(summary_lines)

    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)

    # Write to file
    with open("output/tour_coach_update.txt", "w", encoding="utf-8") as f:
        f.write(summary)

    # Log reflection (summary) to memory
    log_reflection({"summary": summary})

    print(
        f"✅ Tour Coach Agent v{version} daily update generated: "
        "output/tour_coach_update.txt"
    )

    # Build log dictionary with structured data
    log = {
        "date": today_display_date,
        "workout": {
            "type": today_workout_type,
            "details": today_workout_details,
        },
        "readiness": {
            "score": readiness_score,
            "hrv_balance": hrv_balance,
            "day": readiness_day,
        },
        "ctl": ctl,
        "atl": atl,
        "tsb": tsb,
        "recommendations": recommendations,
        "adjustment_lines": adjustment_lines,
        "peloton_class": peloton_class,
        "version": version,
    }
    return summary, log


if __name__ == "__main__":
    run()
