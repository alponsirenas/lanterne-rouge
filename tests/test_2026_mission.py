"""mission/stages.json is the shared source of truth; keep it whole."""

import json
from datetime import date, timedelta
from pathlib import Path

MISSION = json.loads(
    (Path(__file__).resolve().parents[1] / "mission" / "stages.json").read_text(encoding="utf-8")
)
STAGES = [s for s in MISSION["stages"] if not s.get("rest")]
RESTS = [s for s in MISSION["stages"] if s.get("rest")]

VALID_TYPES = {"tt", "flat", "hills", "mountains"}
VALID_ZONES = {"z1", "z2", "z3", "z4", "z5"}


def test_route_shape():
    assert len(STAGES) == 21
    assert len(RESTS) == 2
    assert [s["n"] for s in STAGES] == list(range(1, 22))
    assert [s["id"] for s in STAGES] == [f"s{i}" for i in range(1, 22)]


def test_calendar_is_contiguous():
    days = [s["date"] for s in MISSION["stages"]]
    first = date.fromisoformat(days[0])
    assert days == [(first + timedelta(days=i)).isoformat() for i in range(len(days))]
    assert days[0] == "2026-07-04"
    assert days[-1] == "2026-07-26"


def test_stages_carry_everything_both_halves_need():
    for s in STAGES:
        for key in ("date", "day", "route", "km", "type", "note",
                    "rideMin", "ride", "walkMin", "walk", "targets", "geo", "history"):
            assert key in s, f"stage {s['n']} missing {key}"
        assert s["type"] in VALID_TYPES
        assert 0 < s["rideMin"] <= 60
        assert 0 < s["walkMin"] <= 60


def test_targets_are_checkable():
    for s in STAGES:
        assert s["targets"], f"stage {s['n']} has no target blocks"
        for block in s["targets"]:
            assert block["zone"] in VALID_ZONES
            assert 0 < block["minutes"] <= s["rideMin"]


def test_map_geometry():
    for s in STAGES:
        for end in ("s", "f"):
            lat, lon = s["geo"][end]
            assert 40 < lat < 52, f"stage {s['n']} {end} latitude off the map"
            assert -6 < lon < 9, f"stage {s['n']} {end} longitude off the map"
