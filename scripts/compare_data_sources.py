#!/usr/bin/env python
"""
Compare Bannister model calculations using different data sources:
1. Test CSV data vs. live Strava data
2. Different date ranges

This helps identify if discrepancies are due to the data source or calculation method.
"""
import math
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the src directory to Python path to find lanterne_rouge package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import pandas as pd

from lanterne_rouge.monitor import ATL_TC, CTL_TC
from lanterne_rouge.strava_api import strava_get


# Define constants
K_CTL = 1 - math.exp(-1 / CTL_TC)
K_ATL = 1 - math.exp(-1 / ATL_TC)


def calculate_from_strava(days=90):
    """Calculate CTL, ATL, TSB using live Strava data."""
    print(f"Calculating from Strava for past {days} days...")

    # Get activities from Strava
    activities = strava_get("athlete/activities?per_page=200")
    if not activities:
        print("No activities found.")
        return None, None, None, None

    print(f"Found {len(activities)} activities.")

    # Process activities
    return process_activities(activities, days)


def calculate_from_csv(csv_path, days=90):
    """Calculate CTL, ATL, TSB using CSV test data."""
    print(f"Calculating from {csv_path} for past {days} days...")

    if not os.path.exists(csv_path):
        print(f"CSV file not found: {csv_path}")
        return None, None, None, None

    # Load CSV
    try:
        activities_df = pd.read_csv(csv_path)
        activities = activities_df.to_dict('records')
        print(f"Loaded {len(activities)} activities from CSV.")
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return None, None, None, None

    # Process activities
    return process_activities(activities, days)


def process_activities(activities, days=90):
    """Process activities and calculate CTL, ATL, TSB."""
    # Use naive datetimes consistently
    today = datetime.now().replace(tzinfo=None)
    start_day = today - timedelta(days=days)

    # Map to store daily TSS
    daily_tss = {}

    # Earliest and latest dates found in data
    earliest_date = None
    latest_date = None

    # Aggregate TSS per local day
    for act in activities:
        if not isinstance(act, dict):
            continue

        start_local = act.get("start_date_local")
        if not start_local:
            continue

        # Parse date
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

        # Track date range in data
        if earliest_date is None or act_dt < earliest_date:
            earliest_date = act_dt
        if latest_date is None or act_dt > latest_date:
            latest_date = act_dt

        # Skip if outside calculation range
        if act_dt < start_day:
            continue

        # Get day key
        day_key = act_dt.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%d")

        # Prioritize icu_training_load
        if 'icu_training_load' in act and act['icu_training_load'] is not None:
            effort = float(act['icu_training_load'])
        else:
            effort = act.get("relative_effort") or act.get("suffer_score") or 0

        daily_tss[day_key] = daily_tss.get(day_key, 0) + effort

    if earliest_date and latest_date:
        print(
            f"Activities date range: {earliest_date.strftime('%Y-%m-%d')} to {latest_date.strftime('%Y-%m-%d')}")
    else:
        print("No valid activities found.")
        return None, None, None, None

    # Create a sorted list of dates
    date_range = [(start_day + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]

    # Create training load series
    tss_series = [daily_tss.get(day, 0) for day in date_range]

    # Print recent training loads
    print("\nRecent daily training loads:")
    for i in range(-10, 0):
        print(f"  {date_range[i]}: {tss_series[i]}")

    # Calculate CTL/ATL
    ctl = atl = 0.0
    for tss in tss_series:
        ctl = ctl * (1 - K_CTL) + tss * K_CTL
        atl = atl * (1 - K_ATL) + tss * K_ATL

    tsb = ctl - atl

    ctl = round(ctl, 1)
    atl = round(atl, 1)
    tsb = round(tsb, 1)

    print(f"Final values: CTL={ctl}, ATL={atl}, TSB={tsb}")

    return ctl, atl, tsb, daily_tss


def main():
    """Run calculations on different data sources and compare."""
    print("=== COMPARING CALCULATIONS ON DIFFERENT DATA SOURCES ===")

    # Calculate using test CSV
    test_csv = Path(__file__).resolve().parents[1] / "tests" / "i296483_activities.csv"
    csv_ctl, csv_atl, csv_tsb, csv_tss = calculate_from_csv(test_csv)

    print("\n" + "-" * 60 + "\n")

    # Calculate using Strava
    strava_ctl, strava_atl, strava_tsb, strava_tss = calculate_from_strava()

    # Compare results
    if csv_ctl is not None and strava_ctl is not None:
        print("\nComparison (Strava - CSV):")
        print(f"CTL diff: {strava_ctl - csv_ctl:.1f}")
        print(f"ATL diff: {strava_atl - csv_atl:.1f}")
        print(f"TSB diff: {strava_tsb - csv_tsb:.1f}")

        # Compare daily TSS for recent days
        if csv_tss and strava_tss:
            print("\nTraining load differences (most recent days):")
            today = datetime.now().replace(tzinfo=None)

            for i in range(10):
                day_key = (today - timedelta(days=i)).strftime("%Y-%m-%d")
                strava_value = strava_tss.get(day_key, 0)
                csv_value = csv_tss.get(day_key, 0)

                if strava_value != 0 or csv_value != 0:
                    print(
                        f"  {day_key}: Strava={strava_value}, CSV={csv_value}, Diff={
                            strava_value - csv_value}")


if __name__ == "__main__":
    main()
