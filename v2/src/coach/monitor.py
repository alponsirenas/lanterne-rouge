# monitor.py
# Fetches Oura readiness and computes CTL/ATL/TSB from Strava.
# Stripped down from the original: no CSV logging, no TDF workout analysis.

import os
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv

from .strava_api import strava_get

load_dotenv()

OURA_TOKEN = os.getenv("OURA_TOKEN")

# Bannister impulse-response constants (industry standard)
_K_CTL = 2 / (42 + 1)  # 42-day time constant (chronic fitness)
_K_ATL = 2 / (7 + 1)   # 7-day time constant (acute fatigue)


def get_oura_readiness() -> tuple[int | None, int | None, str | None]:
    """Return (readiness_score, hrv_balance, date_str) from the most recent Oura entry."""
    today = datetime.now().date()
    params = {
        "start_date": (today - timedelta(days=6)).isoformat(),
        "end_date": today.isoformat(),
    }
    try:
        resp = requests.get(
            "https://api.ouraring.com/v2/usercollection/daily_readiness",
            headers={"Authorization": f"Bearer {OURA_TOKEN}"},
            params=params,
            timeout=10,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"❌ Oura API error: {exc}")
        return None, None, None

    entries = resp.json().get("data", [])
    for entry in sorted(entries, key=lambda x: x["day"], reverse=True):
        score = entry.get("score")
        if score is not None:
            hrv_balance = entry.get("contributors", {}).get("hrv_balance")
            return score, hrv_balance, entry["day"]

    print("⚠️  No Oura readiness data in the past 7 days.")
    return None, None, None


def get_ctl_atl_tsb(ftp: int = 250, days: int = 90) -> tuple[float | None, float | None, float | None]:
    """Compute CTL, ATL, TSB using the Bannister model over the past `days` days."""
    print("🔍 Pulling Strava activities for CTL/ATL/TSB…")
    activities = strava_get("athlete/activities?per_page=200")
    if not activities:
        print("⚠️  No Strava activities found.")
        return None, None, None

    today = datetime.now().replace(tzinfo=None)
    start = today - timedelta(days=days)
    daily_tss: dict[str, float] = {}

    for act in activities:
        if not isinstance(act, dict):
            continue
        raw = act.get("start_date_local", "")
        try:
            dt = datetime.fromisoformat(raw).replace(tzinfo=None)
        except ValueError:
            try:
                dt = datetime.strptime(raw, "%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                continue

        if dt < start:
            continue

        day_key = dt.strftime("%Y-%m-%d")
        tss = _power_tss(act, ftp) or act.get("relative_effort") or act.get("suffer_score") or 0
        daily_tss[day_key] = daily_tss.get(day_key, 0) + tss

    date_range = [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
    tss_series = [daily_tss.get(d, 0) for d in date_range]

    # Seed with average of first two weeks
    init = sum(tss_series[: min(14, len(tss_series))]) / min(14, len(tss_series)) if tss_series else 0
    ctl = atl = init

    for tss in tss_series:
        ctl = ctl * (1 - _K_CTL) + tss * _K_CTL
        atl = atl * (1 - _K_ATL) + tss * _K_ATL

    tsb = ctl - atl
    print(f"✅ CTL={ctl:.1f}, ATL={atl:.1f}, TSB={tsb:.1f}")
    return round(ctl, 1), round(atl, 1), round(tsb, 1)


def _power_tss(activity: dict, ftp: int) -> float:
    """TSS = (duration × NP × IF) / (FTP × 3600) × 100"""
    np = activity.get("weighted_average_watts") or activity.get("average_watts")
    duration = activity.get("moving_time") or activity.get("elapsed_time")
    if not (np and duration and ftp):
        return 0.0
    intensity_factor = np / ftp
    return (duration * np * intensity_factor) / (ftp * 3600) * 100
