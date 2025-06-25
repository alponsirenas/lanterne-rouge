# monitor.py
"""
Observation‑layer utilities for Lanterne Rouge.

* Pulls Oura readiness (detailed contributors logged separately)
* Pulls Strava activities and computes CTL / ATL / TSB
* All metrics are returned as floats rounded to one decimal
"""

import csv
import json
import math
import os
from datetime import datetime, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

from lanterne_rouge.strava_api import strava_get

# --------------------------------------------------------------------------- #
#  Environment
# --------------------------------------------------------------------------- #

load_dotenv()
OURA_TOKEN = os.getenv("OURA_TOKEN")

# Optional; used by future helpers such as Workout Plan Generator
USER_FTP = int(os.getenv("USER_FTP", 250))

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
    Return (readiness_score:int | None, hrv_balance:int | None, readiness_day:str | None)
    """
    today = datetime.now().date()
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
CTL_TC = 42  # days
ATL_TC = 7   # days
K_CTL = 1 - math.exp(-1 / CTL_TC)
K_ATL = 1 - math.exp(-1 / ATL_TC)


def _bucket_to_local_midnight(dt: datetime) -> str:
    """Return YYYY‑MM‑DD key representing the athlete’s *local* training day."""
    return dt.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%d")


def get_ctl_atl_tsb(days: int = 45):
    """
    Compute CTL, ATL, TSB using Bannister’s impulse‑response model.

    Returns (ctl:float, atl:float, tsb:float) rounded to 1 decimal place.
    """
    print("🔍  Pulling activities from Strava for CTL/ATL/TSB…")
    activities = strava_get("athlete/activities?per_page=200")
    if not activities:
        print("⚠️  No activities from Strava; CTL/ATL/TSB unavailable.")
        return None, None, None

    today = datetime.now()
    start_day = today - timedelta(days=days)
    daily_tss: dict[str, float] = {}

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
        except ValueError:
            # Fallback for legacy "Z" suffix
            act_dt = datetime.strptime(start_local, "%Y-%m-%dT%H:%M:%SZ")

        if act_dt < start_day:
            continue

        day_key = _bucket_to_local_midnight(act_dt)
        effort = act.get("relative_effort") or act.get("suffer_score") or 0
        daily_tss[day_key] = daily_tss.get(day_key, 0) + effort

    # Ensure full window length with zeros for rest days
    tss_series = [
        daily_tss.get((start_day + timedelta(days=i)).strftime("%Y-%m-%d"), 0)
        for i in range(days)
    ]

    # --------------------------------------------------------------------- #
    # 2.  Exponential moving averages
    # --------------------------------------------------------------------- #
    ctl = atl = 0.0
    for tss in tss_series:
        ctl += K_CTL * (tss - ctl)
        atl += K_ATL * (tss - atl)

    tsb = ctl - atl
    print(f"✅  Calculated CTL={ctl:.1f}, ATL={atl:.1f}, TSB={tsb:.1f}")
    return round(ctl, 1), round(atl, 1), round(tsb, 1)