#!/usr/bin/env python
"""
Diagnostic script to compare Bannister model calculations with intervals.icu.
This script helps identify discrepancies between our implementation and reference values.
"""
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the src directory to Python path to find lanterne_rouge package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import pandas as pd

from lanterne_rouge.monitor import ATL_TC, CTL_TC, K_ATL, K_CTL, get_ctl_atl_tsb
from lanterne_rouge.strava_api import strava_get


def run_production_calculation():
    """Run the production get_ctl_atl_tsb method and return the results."""
    print("=== RUNNING PRODUCTION CALCULATION ===")
    ctl, atl, tsb = get_ctl_atl_tsb(days=90)
    print(f"Production CTL: {ctl}, ATL: {atl}, TSB: {tsb}")
    return ctl, atl, tsb


def run_manual_calculation(activities_source="strava", csv_path=None, target_date=None):
    """
    Run a calculation from scratch using either Strava API or a CSV file.

    Args:
        activities_source: "strava" or "csv"
        csv_path: Path to the CSV file (if activities_source is "csv")
        target_date: Target date for calculation (default: today)
    """
    print("=== RUNNING MANUAL CALCULATION ===")

    # Get activities either from Strava or CSV
    if activities_source == "strava":
        print("Fetching activities from Strava...")
        activities = strava_get("athlete/activities?per_page=200")
        if not activities:
            print("No activities found.")
            return None, None, None
    else:
        # Load from CSV
        if not csv_path:
            print("No CSV path provided.")
            return None, None, None

        print(f"Loading activities from {csv_path}...")
        try:
            activities_df = pd.read_csv(csv_path)
            activities = activities_df.to_dict('records')
        except Exception as e:
            print(f"Error loading CSV: {e}")
            return None, None, None

    # Setup date range
    if target_date:
        if isinstance(target_date, str):
            target_date = datetime.strptime(target_date, "%Y-%m-%d")
        end_date = target_date
    else:
        end_date = datetime.now().replace(tzinfo=None)

    # Look back 90 days for stability
    start_date = end_date - timedelta(days=90)

    print(f"Calculating from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

    # Aggregate TSS by day
    daily_tss = {}

    for activity in activities:
        if not isinstance(activity, dict):
            continue

        # Parse start date
        start_local = activity.get("start_date_local")
        if not start_local:
            continue

        try:
            act_dt = datetime.fromisoformat(start_local)
            # Strip timezone info if present
            if act_dt.tzinfo is not None:
                act_dt = act_dt.replace(tzinfo=None)
        except ValueError:
            # Fallback for legacy "Z" suffix
            try:
                act_dt = datetime.strptime(start_local, "%Y-%m-%dT%H:%M:%SZ")
            except BaseException:
                print(f"Could not parse date: {start_local}")
                continue

        # Skip if outside range
        if act_dt < start_date or act_dt > end_date:
            continue

        # Get day key
        day_key = act_dt.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%d")

        # Get TSS - prioritize icu_training_load
        if 'icu_training_load' in activity and activity['icu_training_load'] is not None:
            effort = float(activity['icu_training_load'])
        else:
            effort = activity.get("relative_effort") or activity.get("suffer_score") or 0

        daily_tss[day_key] = daily_tss.get(day_key, 0) + effort

    # Generate date range
    date_range = []
    current_date = start_date
    while current_date <= end_date:
        date_range.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)

    # Create TSS series with zeros for missing days
    tss_series = [daily_tss.get(day, 0) for day in date_range]

    # Show recent training loads
    print("\nRecent daily training loads:")
    for i in range(-10, 0):
        if abs(i) <= len(date_range):
            print(f"  {date_range[i]}: {tss_series[i]}")

    # Calculate CTL/ATL using Bannister model
    ctl = atl = 0.0
    for i, tss in enumerate(tss_series):
        ctl = ctl * (1 - K_CTL) + tss * K_CTL
        atl = atl * (1 - K_ATL) + tss * K_ATL

        # Log milestone days
        if i == 0 or i == len(tss_series) - 1 or (i+1) % 30 == 0:
            print(f"Day {i+1} ({date_range[i]}): CTL={ctl:.2f}, ATL={atl:.2f}, TSB={(ctl-atl):.2f}")

    tsb = ctl - atl

    print(f"\nManual calculation results:")
    print(f"CTL: {ctl:.2f}")
    print(f"ATL: {atl:.2f}")
    print(f"TSB: {tsb:.2f}")

    return ctl, atl, tsb


def check_memory_db():
    """Check the recent observations in the memory database."""
    print("=== CHECKING MEMORY DATABASE ===")
    try:
        import sqlite3
        from pathlib import Path

        db_path = Path(__file__).resolve().parents[1] / "memory" / "lanterne.db"
        if not db_path.exists():
            print(f"Memory database not found at {db_path}")
            return

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        # Get recent observations
        cursor = conn.execute(
            "SELECT timestamp, type, data FROM memory WHERE type='observation' ORDER BY timestamp DESC LIMIT 5"
        )

        print("Recent observations in memory database:")
        for row in cursor:
            data = json.loads(row["data"])
            print(
                f"{
                    row['timestamp']}: CTL={
                    data.get('ctl')}, ATL={
                    data.get('atl')}, TSB={
                    data.get('tsb')}")

        conn.close()

    except Exception as e:
        print(f"Error checking memory database: {e}")


def compare_with_intervals_icu(target_date=None):
    """
    Compare our implementation with intervals.icu values.

    Args:
        target_date: Target date for comparison (default: latest date in wellness data)
    """
    print("=== COMPARING WITH INTERVALS.ICU DATA ===")

    # Load wellness data
    test_dir = Path(__file__).resolve().parents[1] / "tests"
    wellness_path = test_dir / 'athlete_i296483_wellness.csv'

    if not wellness_path.exists():
        print(f"Wellness data not found at {wellness_path}")
        return

    wellness_df = pd.read_csv(wellness_path)
    wellness_df['date'] = pd.to_datetime(wellness_df['date'])

    # Get target row
    if target_date:
        target_dt = pd.to_datetime(target_date)
        wellness_row = wellness_df[wellness_df['date'] == target_dt]
        if len(wellness_row) == 0:
            print(f"No wellness data found for date {target_date}")
            return
    else:
        wellness_row = wellness_df.sort_values('date', ascending=False).iloc[0:1]
        target_date = wellness_row['date'].iloc[0].strftime('%Y-%m-%d')

    # Extract intervals.icu values
    icu_ctl = wellness_row['ctl'].iloc[0]
    icu_atl = wellness_row['atl'].iloc[0]
    icu_tsb = icu_ctl - icu_atl

    print(f"Intervals.icu values for {target_date}:")
    print(f"CTL: {icu_ctl:.2f}")
    print(f"ATL: {icu_atl:.2f}")
    print(f"TSB: {icu_tsb:.2f}")

    # Run manual calculation on test data
    activities_path = test_dir / 'i296483_activities.csv'
    our_ctl, our_atl, our_tsb = run_manual_calculation(
        activities_source="csv",
        csv_path=activities_path,
        target_date=target_date
    )

    # Compare results
    if our_ctl is not None:
        print(f"\nDifferences (Our - intervals.icu):")
        print(f"CTL diff: {our_ctl - icu_ctl:.2f}")
        print(f"ATL diff: {our_atl - icu_atl:.2f}")
        print(f"TSB diff: {our_tsb - icu_tsb:.2f}")


def main():
    """Main diagnostic function."""
    print("=== BANNISTER MODEL DIAGNOSTIC TOOL ===")
    print(f"Current date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Using CTL time constant: {CTL_TC} days (k={K_CTL:.6f})")
    print(f"Using ATL time constant: {ATL_TC} days (k={K_ATL:.6f})")

    # Run various diagnostics
    run_production_calculation()
    print("\n" + "-" * 60 + "\n")

    check_memory_db()
    print("\n" + "-" * 60 + "\n")

    # Attempt to run calculation on Strava data directly
    run_manual_calculation()
    print("\n" + "-" * 60 + "\n")

    # Compare with intervals.icu (test data)
    compare_with_intervals_icu()

    print("\n=== DIAGNOSTIC COMPLETE ===")


if __name__ == "__main__":
    main()
