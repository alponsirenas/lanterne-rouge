# mission.py
# Loads a TOML mission file and validates it with Pydantic.
# No SQLite caching — just load from disk each run. It's fast enough.

import tomllib
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, ValidationError


class AthleteConfig(BaseModel):
    ftp: int = Field(description="Functional Threshold Power in watts")
    weight_kg: Optional[float] = None


class ConstraintsConfig(BaseModel):
    min_readiness: float = Field(default=70)
    min_tsb: float = Field(default=-15)


class MissionConfig(BaseModel):
    id: str
    name: str
    start_date: date
    goal_date: date
    goal_description: Optional[str] = None
    athlete: AthleteConfig
    constraints: ConstraintsConfig = Field(default_factory=ConstraintsConfig)

    def training_phase(self, today: date) -> str:
        days_out = (self.goal_date - today).days
        if days_out > 42:
            return "Base"
        if days_out > 21:
            return "Build"
        if days_out > 7:
            return "Peak"
        return "Taper"

    def next_phase_start(self, today: date) -> date | None:
        if today >= self.goal_date:
            return None
        phase = self.training_phase(today)
        offsets = {"Base": 42, "Build": 21, "Peak": 7}
        offset = offsets.get(phase)
        return (self.goal_date - timedelta(days=offset)) if offset else self.goal_date


def load_config(path: str | Path) -> MissionConfig:
    path = Path(path)
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Mission config not found: {path}")
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f"TOML syntax error in {path}: {e}")

    try:
        return MissionConfig(**data)
    except ValidationError as e:
        raise ValueError(f"Invalid mission config in {path}: {e}")
