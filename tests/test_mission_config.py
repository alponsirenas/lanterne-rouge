from datetime import date
from pathlib import Path
import json
import sqlite3

from lanterne_rouge.mission_config import (
    load_config,
    cache_to_sqlite,
    MissionConfig,
)

# ---------------------------------------------------------------------------
# Inline sample mission (TOML v1.0)
# ---------------------------------------------------------------------------
_SAMPLE_TOML = """
id = "ana_may24"
athlete_id = "strava:123456"

start_date = 2025-05-01
goal_event = "Tour of California"
goal_date = 2025-10-01

[targets]
ctl_peak = 90
long_ride_minutes = 300
stage_climb_minutes = 60
threshold_interval_min = 40

[constraints]
min_readiness = 65
max_rhr = 58
min_tsb = -10
"""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def test_load_config(tmp_path: Path):
    toml_file = tmp_path / "mission.toml"
    toml_file.write_text(_SAMPLE_TOML)

    cfg = load_config(toml_file)

    assert isinstance(cfg, MissionConfig)
    assert cfg.id == "ana_may24"
    assert cfg.targets.long_ride_minutes == 300
    assert cfg.constraints.min_readiness == 65
    assert cfg.start_date == date(2025, 5, 1)


def test_cache_to_sqlite(tmp_path: Path):
    toml_file = tmp_path / "mission.toml"
    toml_file.write_text(_SAMPLE_TOML)
    cfg = load_config(toml_file)

    db_file = tmp_path / "lanterne.db"
    cache_to_sqlite(cfg, db_file)

    con = sqlite3.connect(db_file)
    row = con.execute(
        "SELECT json FROM mission_config WHERE id = ?", (cfg.id,)
    ).fetchone()
    con.close()

    assert row is not None
    reloaded = MissionConfig(**json.loads(row[0]))
    assert reloaded == cfg