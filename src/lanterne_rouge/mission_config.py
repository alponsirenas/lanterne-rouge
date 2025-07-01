"""
Mission configuration module for Lanterne Rouge.

This module provides functionality for loading, validating, and caching mission
configurations from TOML files.
"""
import json
import sqlite3
from pathlib import Path
from typing import Optional
from datetime import date, timedelta

import tomli as tomllib  # tomllib in 3.11+
from pydantic import BaseModel, Field, ValidationError


class AthleteConfig(BaseModel):
    """Athlete configuration."""
    ftp: int = Field(description="Functional Threshold Power in watts")
    weight_kg: Optional[float] = None


class ConstraintsConfig(BaseModel):
    """Training constraints configuration."""
    min_readiness: float = Field(default=70, description="Minimum readiness score")
    min_tsb: float = Field(default=-10, description="Minimum TSB threshold")


class MissionConfig(BaseModel):
    """Mission configuration model."""
    id: str
    name: str
    start_date: date
    goal_date: date
    athlete: AthleteConfig
    constraints: ConstraintsConfig = Field(default_factory=ConstraintsConfig)

    def training_phase(self, today: date) -> str:
        """Determine current training phase based on date."""
        days_out = (self.goal_date - today).days
        if days_out > 42:
            return "Base"
        if 42 >= days_out > 21:
            return "Build"
        if 21 >= days_out > 7:
            return "Peak"
        return "Taper"

    def next_phase_start(self, today: date) -> date | None:
        """Calculate when the next training phase begins."""
        if today >= self.goal_date:
            return None
        phase = self.training_phase(today)
        if phase == "Base":
            return self.goal_date - timedelta(days=42)
        if phase == "Build":
            return self.goal_date - timedelta(days=21)
        if phase == "Peak":
            return self.goal_date - timedelta(days=7)
        return self.goal_date


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


def get_cached_mission_config(db_path: str | Path = "memory/lanterne.db") -> MissionConfig | None:
    """
    Retrieve the most recent mission configuration from the SQLite cache.

    Args:
        db_path: Path to the SQLite database file

    Returns:
        MissionConfig object if found, None otherwise
    """
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


def bootstrap(path: Path | str, db_path: str | Path = "memory/lanterne.db") -> MissionConfig:
    """Convenience – load + cache in one call."""
    cfg = load_config(path)
    cache_to_sqlite(cfg, db_path)
    return cfg
