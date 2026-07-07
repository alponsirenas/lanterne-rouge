"""The morning loop's pure parts: stage matching and the status.json contract."""

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import run_morning as rm  # noqa: E402
import monitor  # noqa: E402

MISSION = rm.load_mission()

RIDE_DETAIL = {
    "moving_time": 1800,
    "distance": 12900.0,
    "average_heartrate": 150.2,
    "max_heartrate": 167.0,
    "average_watts": 101.4,
    "suffer_score": 84,
}
TIZ = {"z1": 3, "z2": 13, "z3": 7, "z4": 5, "z5": 2}
OURA = {"score": 81, "sleep_score": 78, "resting_hr": 53, "hrv": 63, "sleep_hours": 7.4}


def test_stage_matching():
    assert rm.stage_on(MISSION, date(2026, 7, 4))["n"] == 1
    assert rm.stage_on(MISSION, date(2026, 7, 26))["n"] == 21
    assert rm.stage_on(MISSION, date(2026, 7, 13)) is None
    assert rm.is_rest_day(MISSION, date(2026, 7, 13))
    assert rm.is_rest_day(MISSION, date(2026, 7, 20))
    assert rm.stage_on(MISSION, date(2026, 7, 3)) is None
    assert not rm.is_rest_day(MISSION, date(2026, 7, 3))


def test_finished_entry_matches_contract():
    entry = rm.build_stage_entry(RIDE_DETAIL, "ride", TIZ, OURA, True,
                                 {"call": "push", "note": "Stage one, taken clean."})
    assert entry["status"] == "finished"
    assert entry["completed_via"] == "ride"
    s = entry["strava"]
    assert s["duration_min"] == 30
    assert s["distance_km"] == 12.9
    assert s["avg_hr"] == 150 and s["max_hr"] == 167
    assert s["avg_watts"] == 101
    assert s["relative_effort"] == 84
    assert s["time_in_zone"] == TIZ
    assert entry["oura"] == OURA
    assert entry["verdict"] == {"call": "push", "hit_target": True,
                                "note": "Stage one, taken clean."}


def test_walk_has_no_watts():
    entry = rm.build_stage_entry(RIDE_DETAIL, "walk", TIZ, OURA, True,
                                 {"call": "ease", "note": "It counts, fully."})
    assert entry["completed_via"] == "walk"
    assert entry["strava"]["avg_watts"] is None


def test_missed_entry_matches_contract():
    entry = rm.build_stage_entry(None, None, None, OURA, False,
                                 {"call": "recover", "note": "Call it a mechanical."})
    assert entry["status"] == "missed"
    assert entry["completed_via"] is None
    assert entry["strava"] is None
    # a missed stage still carries a verdict the dashboard renders without guarding
    assert entry["verdict"]["call"] == "recover"
    assert entry["verdict"]["hit_target"] is False
    assert entry["verdict"]["note"]


HR_ZONES = [{"min": 0, "max": 115}, {"min": 115, "max": 135}, {"min": 135, "max": 155},
            {"min": 155, "max": 175}, {"min": 175, "max": -1}]
POWER_ZONES = [{"min": 0, "max": 55}, {"min": 55, "max": 75}, {"min": 75, "max": 90},
               {"min": 90, "max": 105}, {"min": 105, "max": 120},
               {"min": 120, "max": 150}, {"min": 150, "max": -1}]


def test_minutes_in_zone_buckets_per_zone():
    times = list(range(0, 181, 60))  # three one-minute samples
    values = [0, 50, 80, 110]  # first sample carries no time
    tiz = monitor.minutes_in_zone(times, values, POWER_ZONES)
    assert tiz == {"z1": 1, "z2": 0, "z3": 1, "z4": 0, "z5": 1}


def test_minutes_in_zone_folds_high_power_zones_into_z5():
    times = list(range(0, 181, 60))
    values = [0, 130, 200, 200]  # z6 and the open-ended z7 both land in z5
    tiz = monitor.minutes_in_zone(times, values, POWER_ZONES)
    assert tiz == {"z1": 0, "z2": 0, "z3": 0, "z4": 0, "z5": 3}


def test_minutes_in_zone_skips_pauses_and_gaps():
    times = [0, 60, 120, 720]  # a ten-minute pause at the end
    values = [140, 140, None, 140]
    tiz = monitor.minutes_in_zone(times, values, HR_ZONES)
    assert tiz == {"z1": 0, "z2": 0, "z3": 1, "z4": 0, "z5": 0}


def _fake_strava(zones: dict, streams: dict):
    def fake(endpoint, params=None):
        return zones if endpoint == "athlete/zones" else streams
    return fake


STREAMS = {
    "time": {"data": [0, 60, 120]},
    "heartrate": {"data": [120, 120, 160]},
    "watts": {"data": [60, 60, 130]},
}


def test_ride_uses_power_zones(monkeypatch):
    monkeypatch.setattr(monitor, "strava_get", _fake_strava(
        {"heart_rate": {"zones": HR_ZONES}, "power": {"zones": POWER_ZONES}}, STREAMS))
    assert monitor.time_in_zone(1, "ride") == {"z1": 0, "z2": 1, "z3": 0, "z4": 0, "z5": 1}


def test_walk_uses_heart_rate_zones(monkeypatch):
    monkeypatch.setattr(monitor, "strava_get", _fake_strava(
        {"heart_rate": {"zones": HR_ZONES}, "power": {"zones": POWER_ZONES}}, STREAMS))
    assert monitor.time_in_zone(1, "walk") == {"z1": 0, "z2": 1, "z3": 0, "z4": 1, "z5": 0}


def test_ride_without_power_zones_falls_back_to_heart_rate(monkeypatch):
    monkeypatch.setattr(monitor, "strava_get", _fake_strava(
        {"heart_rate": {"zones": HR_ZONES}}, STREAMS))
    assert monitor.time_in_zone(1, "ride") == {"z1": 0, "z2": 1, "z3": 0, "z4": 1, "z5": 0}


def test_finished_without_zone_context():
    entry = rm.build_stage_entry(RIDE_DETAIL, "ride", None, None, None,
                                 {"call": "ease", "note": "Finished without context."})
    assert entry["status"] == "finished"
    assert "time_in_zone" not in entry["strava"]
    assert "oura" not in entry
    assert entry["verdict"]["hit_target"] is None
