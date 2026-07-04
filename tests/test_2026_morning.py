"""The morning loop's pure parts: stage matching and the status.json contract."""

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import run_morning as rm  # noqa: E402

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


def test_finished_without_zone_context():
    entry = rm.build_stage_entry(RIDE_DETAIL, "ride", None, None, None,
                                 {"call": "ease", "note": "Finished without context."})
    assert entry["status"] == "finished"
    assert "time_in_zone" not in entry["strava"]
    assert "oura" not in entry
    assert entry["verdict"]["hit_target"] is None
