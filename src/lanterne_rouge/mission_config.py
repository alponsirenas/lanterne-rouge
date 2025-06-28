"""MissionConfig – load/validate/ cache mission parameters.

Usage
-----
>>> cfg = load_config(Path("missions/ana_may24.toml"))
>>> cache_to_sqlite(cfg)            # defaults to lantern.db
"""
from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

# tomllib is in the standard library starting with Python 3.11.
# On earlier interpreters we fall back to the third‑party “tomli” package,
# imported under the same alias so the rest of the code stays unchanged.
try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # ≤ 3.10
    import tomli as tomllib  # type: ignore

from pydantic import BaseModel, ConfigDict, Field, ValidationError


# ──────────────────────────────────────────────────────────────────────────
# Nested models for explicit schema (v0.3.0)
# ──────────────────────────────────────────────────────────────────────────
class Targets(BaseModel):
    """Performance objectives the Reasoner can optimise for."""
    ctl_peak: int
    long_ride_minutes: int
    stage_climb_minutes: int
    threshold_interval_min: int


class Constraints(BaseModel):
    """Readiness / fatigue bounds the plan must respect."""
    min_readiness: int
    max_rhr: int
    min_tsb: int


class AthleteData(BaseModel):
    """Athlete-specific data needed for calculations."""
    ftp: int = Field(250, description="Functional Threshold Power in watts")

# ──────────────────────────────────────────────────────────────────────────────
# Pydantic Model
# ──────────────────────────────────────────────────────────────────────────────


class MissionConfig(BaseModel):
    """Schema-checked representation of an athlete mission."""

    id: str = Field(..., description="Unique mission slug → primary key")
    athlete_id: str = Field(..., description="External user-id (Oura/Strava)")

    start_date: date
    goal_event: str
    goal_date: date

    targets: Targets
    constraints: Constraints
    athlete: AthleteData = Field(
        default_factory=AthleteData,
        description="Athlete-specific data like FTP")

    # ─── Model-level config (Pydantic v2) ────────────────────────────────
    model_config = ConfigDict(
        ser_json_encoders={date: lambda d: d.isoformat()},
        frozen=True,
    )


# ──────────────────────────────────────────────────────────────────────────────
# TOML Loader
# ──────────────────────────────────────────────────────────────────────────────

def load_config(path: Path | str) -> MissionConfig:
    """Read & validate a single TOML mission file."""
    path = Path(path)
    try:
        if path.suffix:
            with open(path, "rb") as file_obj:
                data = tomllib.load(file_obj)
        else:
            data = tomllib.loads(path.read_text())
    except FileNotFoundError as e:
        raise FileNotFoundError(f"MissionConfig file not found: {path}") from e
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f"TOML syntax error in {path}: {e}") from e

    try:
        return MissionConfig(**data)
    except ValidationError as e:
        raise ValueError(f"Invalid MissionConfig in {path}: {e}") from e


# ──────────────────────────────────────────────────────────────────────────────
# Cache Layer (SQLite for v0.3)
# ──────────────────────────────────────────────────────────────────────────────

def cache_to_sqlite(cfg: MissionConfig, db_path: str | Path = "memory/lanterne.db") -> None:
    """Upsert the JSON blob so other modules can query cheaply."""
    db_path = Path(db_path)
    con = sqlite3.connect(db_path)
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS mission_config (
            id TEXT PRIMARY KEY,
            json TEXT NOT NULL
        )
        """
    )
    con.execute(
        "REPLACE INTO mission_config VALUES (?, ?)", (cfg.id, cfg.model_dump_json())
    )
    con.commit()
    con.close()


# ──────────────────────────────────────────────────────────────────────────────
# Data Access
# ──────────────────────────────────────────────────────────────────────────────

def get_current_mission(db_path: str | Path = "memory/lanterne.db") -> MissionConfig | None:
    """Retrieve the most recent mission config from SQLite."""
    db_path = Path(db_path)
    if not db_path.exists():
        return None

    try:
        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row
        row = con.execute("SELECT json FROM mission_config ORDER BY id DESC LIMIT 1").fetchone()
        con.close()

        if row is None:
            return None

        return MissionConfig.model_validate_json(row["json"])
    except (sqlite3.Error, ValidationError) as e:
        print(f"Error retrieving mission config: {e}")
        return None


def get_athlete_ftp(db_path: str | Path = "memory/lanterne.db", default_ftp: int = 250) -> int:
    """Retrieve the athlete's FTP from the mission config or return default value."""
    import json
    
    try:
        db_path = Path(db_path)
        if not db_path.exists():
            return default_ftp

        # Connect directly to the database to ensure we get the latest value
        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row
        row = con.execute("SELECT json FROM mission_config ORDER BY id DESC LIMIT 1").fetchone()
        con.close()

        if row is None:
            return default_ftp

        # Extract FTP from JSON
        config_data = json.loads(row["json"])
        if "athlete" in config_data and "ftp" in config_data["athlete"]:
            return config_data["athlete"]["ftp"]
        return default_ftp
    except (sqlite3.Error, json.JSONDecodeError, KeyError) as e:
        print(f"Error retrieving athlete FTP: {e}")
        return default_ftp


def get_cached_mission_config(db_path: str | Path = "memory/lanterne.db") -> MissionConfig | None:
    """
    Retrieve the most recent mission configuration from the SQLite cache.
    
    Args:
        db_path: Path to the SQLite database file
        
    Returns:
        MissionConfig object if found, None otherwise
    """
    db_path = Path(db_path)
    if not db_path.exists():
        return None

    try:
        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row
        row = con.execute("SELECT json FROM mission_config ORDER BY id DESC LIMIT 1").fetchone()
        con.close()

        if row is None:
            return None

        return MissionConfig.model_validate_json(row["json"])
    except Exception as e:
        print(f"Error retrieving mission config: {e}")
        return None


# Convenience – load + cache in one call

def bootstrap(path: Path | str, db_path: str | Path = "memory/lanterne.db") -> MissionConfig:
    cfg = load_config(path)
    cache_to_sqlite(cfg, db_path)
    return cfg
