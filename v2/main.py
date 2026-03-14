#!/usr/bin/env python3
"""
Lanterne Rouge v2 — daily coaching loop.

Usage:
    python main.py [path/to/mission.toml]

The mission TOML defaults to missions/example.toml, or set MISSION_CONFIG env var.
"""

import json
import os
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Allow running from the v2/ directory
sys.path.insert(0, str(Path(__file__).parent))

from src.coach.monitor import get_oura_readiness, get_ctl_atl_tsb
from src.coach.mission import load_config
from src.coach.memory import append, recent
from src.coach.coach import recommend


def main():
    today = date.today()

    mission_path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else os.getenv("MISSION_CONFIG", "missions/example.toml")
    )

    print(f"\n🚴  Lanterne Rouge v2 — {today}\n")

    # Load mission
    mission = load_config(mission_path)
    phase = mission.training_phase(today)
    days_to_goal = (mission.goal_date - today).days
    print(f"📋  Mission : {mission.name}")
    print(f"    Phase   : {phase} ({days_to_goal}d to goal)\n")

    # Gather data
    print("📡  Fetching Oura readiness…")
    readiness, hrv_balance, readiness_day = get_oura_readiness()

    print("📡  Fetching Strava training load…")
    ctl, atl, tsb = get_ctl_atl_tsb(ftp=mission.athlete.ftp)

    # Apply safe defaults when APIs are unavailable
    if readiness is None:
        print("⚠️   No Oura data — using neutral defaults\n")
        readiness, hrv_balance = 75, None
    if ctl is None:
        print("⚠️   No Strava data — using zero load\n")
        ctl, atl, tsb = 0.0, 0.0, 0.0

    # Persist observation
    append("observation", {
        "date": str(today),
        "readiness": readiness,
        "hrv_balance": hrv_balance,
        "ctl": ctl,
        "atl": atl,
        "tsb": tsb,
    })

    # Ask Claude
    print("🤖  Generating coaching recommendation…\n")
    rec = recommend(readiness, hrv_balance, ctl, atl, tsb, mission, today)

    # Persist decision
    append("decision", {"date": str(today), **rec})

    # Display
    action = rec.get("action", "maintain").upper()
    intensity = rec.get("intensity", "moderate")
    separator = "=" * 60
    print(separator)
    print(f"  {action}  —  {intensity} intensity")
    print(separator)
    print(f"\n{rec.get('reason', '')}\n")
    print(f"🏋️   Today's workout: {rec.get('workout', 'See reason above')}")
    if rec.get("flags"):
        print(f"⚠️   Flags: {', '.join(rec['flags'])}")
    print()

    # Write output file for CI/CD artifact collection
    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"recommendation_{today}.json"
    out_path.write_text(json.dumps(rec, indent=2))
    print(f"💾  Saved to {out_path}")


if __name__ == "__main__":
    main()
