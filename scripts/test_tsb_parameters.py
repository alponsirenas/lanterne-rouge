#!/usr/bin/env python
"""
Compare our TSB calculation with different parameters to see which gives us values closest to -4.

This script tests different combinations of:
1. Time constants (CTL/ATL)
2. TSS scaling factors
3. Using previous day vs current day for TSB calculation

The goal is to find settings that produce TSB values close to what you see on your Strava dashboard.
"""
import math
import os
import sys
from datetime import datetime, timedelta

# Add the src directory to Python path to find lanterne_rouge package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from lanterne_rouge.strava_api import strava_get


def calculate_with_params(ctl_days, atl_days, tss_factor=1.0, use_previous_day=True):
    """Calculate CTL/ATL/TSB with different parameters."""
    print(
        f"Calculating with: CTL={ctl_days} days, ATL={atl_days} days, "
        f"TSS factor={tss_factor}, use_previous_day={use_previous_day}")

    # Constants
    k_ctl = 1 - math.exp(-1 / ctl_days)
    k_atl = 1 - math.exp(-1 / atl_days)

    # Get activities
    activities = strava_get("athlete/activities?per_page=200")
    if not activities:
        print("No activities found.")
        return None, None, None

    # Setup date range - include more days for stability
    days = 90
    today = datetime.now().replace(tzinfo=None)
    start_day = today - timedelta(days=days)

    # Aggregate TSS
    daily_tss = {}
    for act in activities:
        if not isinstance(act, dict):
            continue

        # Get date
        start_local = act.get("start_date_local")
        if not start_local:
            continue

        try:
            act_dt = datetime.fromisoformat(start_local)
            if act_dt.tzinfo is not None:
                act_dt = act_dt.replace(tzinfo=None)
        except ValueError:
            try:
                act_dt = datetime.strptime(start_local, "%Y-%m-%dT%H:%M:%SZ")
            except BaseException:
                continue

        if act_dt < start_day:
            continue

        day_key = act_dt.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%d")

        # Get TSS with scaling factor
        if 'icu_training_load' in act and act['icu_training_load'] is not None:
            effort = float(act['icu_training_load']) * tss_factor
        else:
            effort = (act.get("relative_effort") or act.get("suffer_score") or 0) * tss_factor

        daily_tss[day_key] = daily_tss.get(day_key, 0) + effort

    # Create date range and TSS series
    date_range = [(start_day + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
    tss_series = [daily_tss.get(day, 0) for day in date_range]

    # Recent training loads
    print("\nRecent daily training loads (with scaling):")
    for i in range(-7, 0):
        print(f"  {date_range[i]}: {tss_series[i]}")

    # Calculate
    ctl_values = [0.0]  # Store all values
    atl_values = [0.0]  # Store all values

    for tss in tss_series:
        ctl = ctl_values[-1] * (1 - k_ctl) + tss * k_ctl
        atl = atl_values[-1] * (1 - k_atl) + tss * k_atl
        ctl_values.append(ctl)
        atl_values.append(atl)

    # Final values (exclude the initial 0.0)
    final_ctl = ctl_values[-1]
    final_atl = atl_values[-1]

    # TSB calculation
    if use_previous_day:
        tsb = ctl_values[-2] - atl_values[-2]  # Yesterday's values
        print(f"Using previous day's values: CTL={ctl_values[-2]:.1f}, ATL={atl_values[-2]:.1f}")
    else:
        tsb = final_ctl - final_atl  # Today's values

    print(f"Final values: CTL={final_ctl:.1f}, ATL={final_atl:.1f}, TSB={tsb:.1f}")
    return final_ctl, final_atl, tsb


def main():
    """Test different parameter combinations."""
    print("=== TESTING DIFFERENT BANNISTER MODEL PARAMETERS ===")

    # Original parameters
    print("\n>>> ORIGINAL PARAMETERS <<<")
    calculate_with_params(42, 7, 1.0, True)

    # Different time constants
    print("\n>>> DIFFERENT TIME CONSTANTS <<<")
    calculate_with_params(40, 7, 1.0, True)
    calculate_with_params(42, 5, 1.0, True)

    # Different TSS scaling
    print("\n>>> DIFFERENT TSS SCALING <<<")
    calculate_with_params(42, 7, 0.8, True)
    calculate_with_params(42, 7, 0.6, True)

    # Using current day vs previous day
    print("\n>>> CURRENT DAY VS PREVIOUS DAY <<<")
    calculate_with_params(42, 7, 1.0, False)

    # Combined optimizations
    print("\n>>> COMBINED OPTIMIZATIONS <<<")
    calculate_with_params(40, 5, 0.8, True)
    calculate_with_params(40, 5, 0.6, True)


if __name__ == "__main__":
    main()
