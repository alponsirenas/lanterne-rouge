"""Pull the day's facts from Strava and Oura. No judgment here, that lives in reason.py."""

import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

STRAVA_BASE = "https://www.strava.com/api/v3"
OURA_BASE = "https://api.ouraring.com/v2/usercollection"
TOKENS_PATH = Path(__file__).resolve().parents[1] / "tokens.json"

RIDE_TYPES = {"Ride", "VirtualRide", "EBikeRide"}
WALK_TYPES = {"Walk", "Run", "VirtualRun", "Hike"}

ZONE_KEYS = ["z1", "z2", "z3", "z4", "z5"]


# --------------------------------------------------------------------------- #
#  Strava
# --------------------------------------------------------------------------- #

def _strava_tokens():
    # tokens.json wins over .env so refreshed tokens survive between runs
    access = os.getenv("STRAVA_ACCESS_TOKEN")
    refresh = os.getenv("STRAVA_REFRESH_TOKEN")
    if TOKENS_PATH.exists():
        cached = json.loads(TOKENS_PATH.read_text())
        access = cached.get("access_token", access)
        refresh = cached.get("refresh_token", refresh)
    return access, refresh


def refresh_strava_token() -> str:
    _, refresh = _strava_tokens()
    r = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": os.getenv("STRAVA_CLIENT_ID"),
            "client_secret": os.getenv("STRAVA_CLIENT_SECRET"),
            "grant_type": "refresh_token",
            "refresh_token": refresh,
        },
        timeout=15,
    )
    r.raise_for_status()
    tokens = r.json()
    TOKENS_PATH.write_text(json.dumps(
        {"access_token": tokens["access_token"], "refresh_token": tokens["refresh_token"]},
        indent=2,
    ))
    return tokens["access_token"]


def strava_get(endpoint: str, params: dict | None = None):
    access, _ = _strava_tokens()

    def call(token):
        return requests.get(
            f"{STRAVA_BASE}/{endpoint}",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=20,
        )

    resp = call(access)
    if resp.status_code == 401:
        resp = call(refresh_strava_token())
    resp.raise_for_status()
    return resp.json()


def activity_for(day: date):
    """Return (activity_detail, "ride"|"walk") for the given local day, or (None, None).

    A ride is a Peloton effort, a walk or run is a treadmill effort. When several
    qualify, take the longest, short warmups should not shadow the stage.
    """
    window_start = datetime.combine(day - timedelta(days=1), datetime.min.time())
    window_end = window_start + timedelta(days=3)
    activities = strava_get("athlete/activities", {
        "after": int(window_start.timestamp()),
        "before": int(window_end.timestamp()),
        "per_page": 50,
    })
    candidates = [
        a for a in activities
        if a.get("start_date_local", "").startswith(day.isoformat())
        and a.get("type") in RIDE_TYPES | WALK_TYPES
    ]
    if not candidates:
        return None, None
    best = max(candidates, key=lambda a: a.get("moving_time", 0))
    via = "ride" if best["type"] in RIDE_TYPES else "walk"
    return strava_get(f"activities/{best['id']}"), via


def time_in_zone(activity_id: int, via: str) -> dict | None:
    """Minutes per zone from the activity streams, or None without usable data.

    The ride prescriptions are power blocks, so a ride is scored against the
    athlete's Strava power zones over the watts stream. A walk has no power,
    its zones are heart-rate based. A ride missing power zones or a watts
    stream falls back to heart rate rather than finishing without context.
    """
    try:
        athlete_zones = strava_get("athlete/zones")
        streams = strava_get(f"activities/{activity_id}/streams", {
            "keys": "time,heartrate,watts",
            "key_by_type": "true",
        })
    except requests.RequestException as exc:
        print(f"Could not fetch zones or streams for activity {activity_id} "
              f"(zones need the profile:read_all scope): {exc}")
        return None
    if "time" not in streams:
        return None
    plans = [("power", "watts"), ("heart_rate", "heartrate")] if via == "ride" \
        else [("heart_rate", "heartrate")]
    for kind, stream_key in plans:
        zones = (athlete_zones.get(kind) or {}).get("zones")
        if zones and stream_key in streams:
            if (kind, stream_key) != plans[0]:
                print(f"Activity {activity_id}: no power zones or watts stream, "
                      "scoring against heart rate instead.")
            return minutes_in_zone(streams["time"]["data"], streams[stream_key]["data"], zones)
    return None


def minutes_in_zone(times: list, values: list, zones: list[dict]) -> dict:
    """Bucket a stream into the contract's z1-z5 minutes. Strava power zones can
    run past five (Coggan has seven), everything above z5 folds into z5."""
    seconds = [0.0] * 5
    for i in range(1, len(times)):
        dt = times[i] - times[i - 1]
        if dt <= 0 or dt > 60:  # skip pauses
            continue
        val = values[i]
        if val is None:
            continue
        for z, zone in enumerate(zones):
            zmax = zone.get("max", -1)
            if val <= zmax or z == len(zones) - 1:  # last zone is open-ended
                seconds[min(z, 4)] += dt
                break
    return {ZONE_KEYS[i]: round(seconds[i] / 60) for i in range(5)}


def strava_summary(detail: dict, tiz: dict | None, via: str) -> dict:
    """The per-stage strava block of the status.json contract."""
    out = {
        "duration_min": round(detail.get("moving_time", 0) / 60),
        "distance_km": round(detail.get("distance", 0) / 1000, 1),
        "avg_hr": round(detail["average_heartrate"]) if detail.get("average_heartrate") else None,
        "max_hr": round(detail["max_heartrate"]) if detail.get("max_heartrate") else None,
        "avg_watts": round(detail["average_watts"]) if via == "ride" and detail.get("average_watts") else None,
        "relative_effort": detail.get("suffer_score"),
    }
    if tiz:
        out["time_in_zone"] = tiz
    return out


# --------------------------------------------------------------------------- #
#  Oura
# --------------------------------------------------------------------------- #

def _oura_get(path: str, params: dict) -> list:
    r = requests.get(
        f"{OURA_BASE}/{path}",
        headers={"Authorization": f"Bearer {os.getenv('OURA_TOKEN')}"},
        params=params,
        timeout=20,
    )
    r.raise_for_status()
    return r.json().get("data", [])


def readiness_for(day: date) -> dict | None:
    """The morning readiness block for a given day: score, sleep score, resting HR,
    HRV, sleep hours. Returns None when Oura has nothing, never invents data."""
    params = {
        "start_date": (day - timedelta(days=1)).isoformat(),
        "end_date": (day + timedelta(days=1)).isoformat(),
    }
    iso = day.isoformat()
    out = {}
    try:
        readiness = [d for d in _oura_get("daily_readiness", params) if d.get("day") == iso]
        if readiness and readiness[-1].get("score") is not None:
            out["score"] = readiness[-1]["score"]
        daily_sleep = [d for d in _oura_get("daily_sleep", params) if d.get("day") == iso]
        if daily_sleep and daily_sleep[-1].get("score") is not None:
            out["sleep_score"] = daily_sleep[-1]["score"]
        sessions = [s for s in _oura_get("sleep", params) if s.get("day") == iso]
        if sessions:
            main = max(sessions, key=lambda s: s.get("total_sleep_duration") or 0)
            if main.get("lowest_heart_rate"):
                out["resting_hr"] = round(main["lowest_heart_rate"])
            if main.get("average_hrv"):
                out["hrv"] = round(main["average_hrv"])
            if main.get("total_sleep_duration"):
                out["sleep_hours"] = round(main["total_sleep_duration"] / 3600, 1)
    except requests.RequestException as exc:
        print(f"Oura request failed: {exc}")
    return out or None
