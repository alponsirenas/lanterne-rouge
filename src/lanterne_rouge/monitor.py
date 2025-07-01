# monitor.py
"""
Observation‑layer utilities for Lanterne Rouge.

* Pulls Oura readiness (detailed contributors logged separately)
* Pulls Strava activities and computes CTL / ATL / TSB
* All metrics are returned as floats rounded to one decimal
"""

import csv
import os
from datetime import datetime, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

from .strava_api import strava_get
from .mission_config import get_athlete_ftp

# --------------------------------------------------------------------------- #
#  Environment
# --------------------------------------------------------------------------- #

load_dotenv()
OURA_TOKEN = os.getenv("OURA_TOKEN")

# Function to get the current FTP from mission config
def get_current_ftp():
    """Get the current athlete FTP value from mission config."""
    return get_athlete_ftp(default_ftp=int(os.getenv("USER_FTP", 250)))

# Output folder
OUTPUT_DIR = Path(__file__).resolve().parents[2] / "output"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)


# --------------------------------------------------------------------------- #
#  Oura Readiness helpers
# --------------------------------------------------------------------------- #
def record_readiness_contributors(day_entry: dict) -> None:
    """
    Persist a full contributor snapshot to CSV (`output/readiness_score_log.csv`).

    Keeps a wide schema but sparsely populated if Oura adds new fields.
    """
    filename = OUTPUT_DIR / "readiness_score_log.csv"
    contributors = day_entry.get("contributors", {})

    # Base row
    row = {
        "day": day_entry.get("day"),
        "readiness_score": day_entry.get("score"),
        **contributors,
    }

    fieldnames = ["day", "readiness_score"] + sorted(contributors.keys())
    file_exists = filename.exists()

    with filename.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

    print("✅  Saved detailed readiness contributors.")


def get_oura_readiness():
    """
    Return a tuple of (readiness_score:int | None, hrv_balance:int | None, readiness_day:str | None)

    Note: This function returns scalar values, not dictionaries. The full readiness data
    is processed by record_readiness_contributors() and saved to readiness_score_log.csv.
    """
    # Use naive datetime objects consistently
    today = datetime.now().replace(tzinfo=None).date()
    start_date = today - timedelta(days=6)

    url = "https://api.ouraring.com/v2/usercollection/daily_readiness"
    headers = {"Authorization": f"Bearer {OURA_TOKEN}"}
    params = {"start_date": start_date.isoformat(), "end_date": today.isoformat()}

    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        r.raise_for_status()
    except Exception as exc:
        print(f"❌  Oura API error: {exc}")
        return None, None, None

    data = r.json().get("data", [])
    if not data:
        print("⚠️  No Oura readiness data in the past 7 days.")
        return None, None, None

    # Most‑recent day first
    for entry in sorted(data, key=lambda x: x["day"], reverse=True):
        score = entry.get("score")
        hrv_balance = entry.get("contributors", {}).get("hrv_balance")
        if score is not None:
            record_readiness_contributors(entry)
            return score, hrv_balance, entry["day"]

    return None, None, None


# --------------------------------------------------------------------------- #
#  Strava CTL / ATL / TSB (Bannister model)
# --------------------------------------------------------------------------- #
CTL_TC = 42  # days - Standard time constant for Chronic Training Load
ATL_TC = 7   # days - Standard time constant for Acute Training Load
# Using the formula λ = 2/(N+1) as specified in TrainingPeaks documentation
K_CTL = 2 / (CTL_TC + 1)  # Lambda for CTL (Fitness)
K_ATL = 2 / (ATL_TC + 1)  # Lambda for ATL (Fatigue)


def _bucket_to_local_midnight(dt: datetime) -> str:
    """Return YYYY‑MM‑DD key representing the athlete's *local* training day."""
    return dt.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%d")


def _calculate_power_tss(activity: dict) -> float:
    """
    Calculate TSS using power data if available.

    Formula: TSS = (duration_seconds × NP × IF) / (FTP × 3600) × 100, where IF = NP/FTP

    Returns calculated TSS value or 0 if power data is insufficient.
    """
    # Get current FTP value - force reload from mission config each time
    ftp = get_athlete_ftp(default_ftp=int(os.getenv("USER_FTP", 250)))

    # Extract power metrics from activity
    weighted_avg_watts = activity.get("weighted_average_watts")  # This is NP (Normalized Power)
    avg_watts = activity.get("average_watts")
    duration_seconds = activity.get("moving_time") or activity.get("elapsed_time")

    # Check if we have required fields
    if not all([duration_seconds, ftp]):
        return 0

    # For NP, prefer weighted_average_watts over average_watts
    normalized_power = weighted_avg_watts or avg_watts

    # If no power data available, can't calculate power-based TSS
    if not normalized_power:
        return 0

    # Calculate Intensity Factor (IF)
    intensity_factor = normalized_power / ftp

    # Calculate TSS
    tss = (duration_seconds * normalized_power * intensity_factor) / (ftp * 3600) * 100

    # Log if debug enabled
    print(f"DEBUG: Power-based TSS: {tss:.1f} (NP={normalized_power}, IF={intensity_factor:.2f}, Duration={duration_seconds}s, FTP={ftp})")

    return tss


def get_ctl_atl_tsb(days: int = 90):
    """
    Compute CTL, ATL, TSB using Bannister's impulse‑response model.

    Returns (ctl:float, atl:float, tsb:float) rounded to 1 decimal place.
    """
    print("🔍  Pulling activities from Strava for CTL/ATL/TSB…")
    activities = strava_get("athlete/activities?per_page=200")
    if not activities:
        print("⚠️  No activities from Strava; CTL/ATL/TSB unavailable.")
        return None, None, None

    # Use naive datetimes consistently to avoid timezone comparison issues
    today = datetime.now().replace(tzinfo=None)
    start_day = today - timedelta(days=days)
    daily_tss: dict[str, float] = {}

    # Debug info
    print(f"DEBUG: Today is {today.strftime('%Y-%m-%d')}, looking back to {start_day.strftime('%Y-%m-%d')} ({days} days)")
    print(f"DEBUG: Found {len(activities)} activities from Strava")

    # --------------------------------------------------------------------- #
    # 1.  Aggregate TSS per local day
    # --------------------------------------------------------------------- #
    for act in activities:
        if not isinstance(act, dict):
            continue

        start_local = act.get("start_date_local")
        if not start_local:
            continue

        # Strava returns ISO 8601 local with *no* Z suffix, e.g., 2025‑06‑23T18:05:07
        try:
            act_dt = datetime.fromisoformat(start_local)
            # Strip timezone info if present to make it naive for consistent comparison
            if act_dt.tzinfo is not None:
                act_dt = act_dt.replace(tzinfo=None)
        except ValueError:
            # Fallback for legacy "Z" suffix
            act_dt = datetime.strptime(start_local, "%Y-%m-%dT%H:%M:%SZ")

        if act_dt < start_day:
            continue

        day_key = _bucket_to_local_midnight(act_dt)

        # Priority 1: Calculate power-based TSS if power data is available
        tss = _calculate_power_tss(act)

        # Priority 2: Use Strava's native relative_effort or suffer_score if no power data
        if tss <= 0:
            tss = act.get("relative_effort") or act.get("suffer_score") or 0
            print(f"DEBUG: Using Strava heart rate-based score: {tss}")

        # Priority 3: Fall back to icu_training_load only if no other metric is available
        if tss <= 0 and 'icu_training_load' in act and act['icu_training_load'] is not None:
            tss = float(act['icu_training_load'])
            print(f"DEBUG: Using intervals.icu training load: {tss}")

        daily_tss[day_key] = daily_tss.get(day_key, 0) + tss

    # Create a sorted list of dates from start_day to today
    date_range = [(start_day + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]

    # Create a list of training loads for each day, replacing missing days with 0
    tss_series = [daily_tss.get(day, 0) for day in date_range]

    # Debug: Print the most recent training loads
    print("\nDEBUG: Recent daily training loads (most recent 10 days):")
    recent_days = min(10, len(date_range))
    for i in range(-recent_days, 0):
        print(f"DEBUG: {date_range[i]}: {tss_series[i]}")

    # --------------------------------------------------------------------- #
    # 2.  Exponential moving averages - using formula that matches intervals.icu
    # --------------------------------------------------------------------- #

    # Initialize CTL and ATL with better starting values
    # Use the average of first 14 days of data as a starting point (if available)
    init_period = min(14, len(tss_series))
    if init_period > 0:
        avg_tss = sum(tss_series[:init_period]) / init_period
        ctl = atl = avg_tss
    else:
        ctl = atl = 0.0

    # Debug: Print intermediate calculation steps
    print(f"\nDEBUG: Starting with initial values: CTL={ctl:.1f}, ATL={atl:.1f}")
    print("\nDEBUG: Bannister model calculation steps:")

    # Keep track of daily CTL/ATL values to access yesterday's values at the end
    daily_values = []

    for i, tss in enumerate(tss_series):
        # Calculate new values
        new_ctl = ctl * (1 - K_CTL) + tss * K_CTL
        new_atl = atl * (1 - K_ATL) + tss * K_ATL

        # Store daily values
        daily_values.append((date_range[i], new_ctl, new_atl))

        # Log every 10 days and the last 5 days for debugging
        if i % 10 == 0 or i >= len(tss_series) - 5:
            print(f"DEBUG: Day {i+1} ({date_range[i]}): TSS={tss:.1f}, CTL={new_ctl:.1f} (from {ctl:.1f}), ATL={new_atl:.1f} (from {atl:.1f})")

        # Update values
        ctl = new_ctl
        atl = new_atl

    # Calculate TSB using today's CTL and ATL values
    # TSB = Today's Fitness (CTL) - Today's Fatigue (ATL)
    tsb = ctl - atl
    print(f"DEBUG: Using today's values for TSB: CTL={ctl:.1f}, ATL={atl:.1f}, TSB={tsb:.1f}")

    print(f"✅  Calculated CTL={ctl:.1f}, ATL={atl:.1f}, TSB={tsb:.1f}")

    # Return the final values
    return round(ctl, 1), round(atl, 1), round(tsb, 1)
