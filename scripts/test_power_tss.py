#!/usr/bin/env python
"""
Test script to validate power-based TSS calculation against Strava/TrainingPeaks values.
"""
import os
import subprocess
import sys

# Add the src directory to Python path to find lanterne_rouge package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from lanterne_rouge.mission_config import get_athlete_ftp
from lanterne_rouge.monitor import _calculate_power_tss
from lanterne_rouge.strava_api import strava_get


def test_power_tss_calculation():
    """
    Test the power-based TSS calculation on recent Strava activities with power data.
    Output a comparison between calculated TSS and any available Strava/TrainingPeaks values.
    """
    # Get athlete FTP from mission config
    ftp = get_athlete_ftp(default_ftp=int(os.getenv("USER_FTP") or 250))

    print("=== POWER-BASED TSS VALIDATION ===")
    print(f"Using FTP value: {ftp} watts from mission config")

    # Update mission config to use 128 as FTP
    subprocess.run(["python", "scripts/update_athlete_ftp.py", "tdf-sim-2025", "128"], check=True)

    # Get updated FTP
    ftp = get_athlete_ftp()
    print(f"Updated FTP to: {ftp} watts")

    activities = strava_get("athlete/activities?per_page=30")
    if not activities:
        print("No activities found.")
        return

    print(f"Found {len(activities)} recent activities")

    # Create a data table for comparison
    results = []

    for act in activities:
        if not isinstance(act, dict):
            continue

        # Basic activity info
        activity_id = act.get("id", "Unknown")
        activity_name = act.get("name", "Unnamed activity")
        activity_type = act.get("type", "Unknown")
        activity_date = act.get("start_date_local", "Unknown date")

        # Power data
        avg_watts = act.get("average_watts")
        normalized_watts = act.get("weighted_average_watts", avg_watts)

        # Only process activities with power data
        if not avg_watts:
            continue

        # Calculate power-based TSS
        calculated_tss = _calculate_power_tss(act)

        # Get Strava's stress score for comparison
        strava_score = act.get("relative_effort") or act.get("suffer_score") or 0
        icu_score = act.get("icu_training_load", 0)

        # Record result
        results.append({
            "activity_id": activity_id,
            "activity_name": activity_name,
            "activity_type": activity_type,
            "activity_date": activity_date,
            "avg_watts": avg_watts,
            "normalized_watts": normalized_watts,
            "duration_seconds": act.get("moving_time"),
            "calculated_power_tss": round(calculated_tss, 1),
            "strava_score": strava_score,
            "icu_score": icu_score,
        })

    # Print results in a table format
    if results:
        print("\nPower-Based TSS Comparison:")
        print("=" * 100)
        print(f"{'Date':<12} | {'Type':<12} | {'Avg W':<6} | {'NP':<6} | {'Duration':<10} | "
              f"{'Power TSS':>9} | {'Strava':>8} | {'ICU':>8} | {'Activity Name':<30}")
        print("-" * 100)

        for r in sorted(results, key=lambda x: x["activity_date"], reverse=True):
            date = r["activity_date"].split("T")[0] if "T" in r["activity_date"] else r["activity_date"]
            duration_mins = round(r["duration_seconds"] / 60, 1) if r["duration_seconds"] else "?"

            print(f"{date:<12} | {r['activity_type']:<12} | {r['avg_watts']:<6} | "
                  f"{r['normalized_watts'] or '?':<6} | {duration_mins:<10} | "
                  f"{r['calculated_power_tss']:>9} | {r['strava_score']:>8} | "
                  f"{r['icu_score']:>8} | {r['activity_name'][:30]}")
    else:
        print("No activities with power data found")


if __name__ == "__main__":
    test_power_tss_calculation()
