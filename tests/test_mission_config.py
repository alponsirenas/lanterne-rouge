"""Tests for the mission_config module functionality."""
import json
import os
import sqlite3
import sys
from datetime import date

# Add the src directory to Python path to find lanterne_rouge package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lanterne_rouge.mission_config import (
    Constraints,
    MissionConfig,
    Targets,
    cache_to_sqlite,
    load_config,
)
from lanterne_rouge.reasoner import decide_adjustment

# Dummy mission config for tests
_dummy_cfg = MissionConfig(
    id="test",
    athlete_id="strava:0",
    start_date=date(2025, 1, 1),
    goal_event="test_event",
    goal_date=date(2025, 12, 31),
    targets=Targets(
        ctl_peak=100,
        long_ride_minutes=100,
        stage_climb_minutes=60,
        threshold_interval_min=20,
    ),
    constraints=Constraints(
        min_readiness=65,
        max_rhr=999,
        min_tsb=-10,
    ),
)


def test_high_readiness_good_tsb():
    """Test that high readiness and positive TSB leads to increase recommendations."""
    readiness = 70
    ctl = 80
    atl = 50
    tsb = 20
    adj = decide_adjustment(readiness, {}, ctl, atl, tsb, _dummy_cfg)
    # expect an "increase" style recommendation in the returned list
    assert any("increase" in m.lower() or "positive" in m.lower() for m in adj)


def test_low_readiness_warning():
    """Test that low readiness leads to decrease/reduce recommendations."""
    readiness = 50
    ctl = 80
    atl = 50
    tsb = 20
    adj = decide_adjustment(readiness, {}, ctl, atl, tsb, _dummy_cfg)
    # expect guidance to reduce / decrease / reducing load
    assert any(word in m.lower() for word in ("decrease", "reduce", "reducing") for m in adj)


def test_high_fatigue_warning():
    """Test that high fatigue (negative TSB) leads to decrease/reduce recommendations."""
    readiness = 70
    ctl = 80
    atl = 70
    tsb = -15
    adj = decide_adjustment(readiness, {}, ctl, atl, tsb, _dummy_cfg)
    # expect guidance to reduce / decrease / reducing load due to fatigue
    assert any(word in m.lower() for word in ("decrease", "reduce", "reducing") for m in adj)


def test_cache_to_sqlite(tmp_path):
    """Test the sqlite caching functionality for mission config."""
    db_file = tmp_path / "mc.db"
    cache_to_sqlite(_dummy_cfg, db_file)

    with sqlite3.connect(db_file) as con:
        row = con.execute(
            "SELECT json FROM mission_config WHERE id=?",
            (_dummy_cfg.id,),
        ).fetchone()

    assert row is not None
    loaded = MissionConfig(**json.loads(row[0]))
    assert loaded == _dummy_cfg


def test_load_and_cache_mission_config(tmp_path):
    """Test loading and caching a mission config from a TOML file."""
    # Create a temporary mission config file
    mission_config_content = """
    id = "test"
    athlete_id = "strava:0"
    start_date = 2025-01-01
    goal_event = "test_event"
    goal_date = 2025-12-31

    [targets]
    ctl_peak = 100
    long_ride_minutes = 100
    stage_climb_minutes = 60
    threshold_interval_min = 20

    [constraints]
    min_readiness = 65
    max_rhr = 999
    min_tsb = -10
    """
    mission_config_path = tmp_path / "test_mission_config.toml"
    mission_config_path.write_text(mission_config_content)

    # Load and cache the mission config
    mission_config = load_config(mission_config_path)
    db_file = tmp_path / "mc.db"
    cache_to_sqlite(mission_config, db_file)

    # Verify the mission config is loaded correctly
    assert mission_config.id == "test"
    assert mission_config.athlete_id == "strava:0"
    assert mission_config.start_date == date(2025, 1, 1)
    assert mission_config.goal_event == "test_event"
    assert mission_config.goal_date == date(2025, 12, 31)
    assert mission_config.targets.ctl_peak == 100
    assert mission_config.targets.long_ride_minutes == 100
    assert mission_config.targets.stage_climb_minutes == 60
    assert mission_config.targets.threshold_interval_min == 20
    assert mission_config.constraints.min_readiness == 65
    assert mission_config.constraints.max_rhr == 999
    assert mission_config.constraints.min_tsb == -10

    # Verify the mission config is cached correctly
    with sqlite3.connect(db_file) as con:
        row = con.execute(
            "SELECT json FROM mission_config WHERE id=?",
            (mission_config.id,),
        ).fetchone()

    assert row is not None
    loaded = MissionConfig(**json.loads(row[0]))
    assert loaded == mission_config
