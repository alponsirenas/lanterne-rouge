"""MissionConfig – load/validate/ cache mission parameters.

Usage
-----
>>> cfg = load_config(Path("missions/ana_may24.toml"))
>>> cache_to_sqlite(cfg)            # defaults to lantern.db
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
import sqlite3
# tomllib is in the standard library starting with Python 3.11.
# On earlier interpreters we fall back to the third‑party “tomli” package,
# imported under the same alias so the rest of the code stays unchanged.
try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # ≤ 3.10
    import tomli as tomllib  # type: ignore

from pydantic import BaseModel, Field, ValidationError, ConfigDict

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
        data = tomllib.loads(path.read_text()) if path.suffix else tomllib.load(path.open("rb"))  # type: ignore[arg-type]
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

def cache_to_sqlite(cfg: MissionConfig, db_path: str | Path = "lanterne.db") -> None:
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


# Convenience – load + cache in one call

def bootstrap(path: Path | str, db_path: str | Path = "lanterne.db") -> MissionConfig:
    cfg = load_config(path)
    cache_to_sqlite(cfg, db_path)
    return cfg