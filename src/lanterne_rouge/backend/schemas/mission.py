"""Pydantic schemas for mission API."""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


# Mission Schemas
class MissionBase(BaseModel):
    """Base mission schema."""
    name: str = Field(..., min_length=1, max_length=255)
    mission_type: str = Field(..., min_length=1, max_length=100)
    event_start_date: date
    event_end_date: date
    prep_start_date: Optional[date] = None
    prep_end_date: Optional[date] = None
    points_schema: dict
    timezone: str = Field(default="UTC", max_length=50)
    constraints: Optional[dict] = None
    notification_preferences: Optional[dict] = None


class MissionCreate(MissionBase):
    """Schema for creating a mission."""


class MissionUpdate(BaseModel):
    """Schema for updating a mission (all fields optional)."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    mission_type: Optional[str] = Field(None, min_length=1, max_length=100)
    event_start_date: Optional[date] = None
    event_end_date: Optional[date] = None
    prep_start_date: Optional[date] = None
    prep_end_date: Optional[date] = None
    points_schema: Optional[dict] = None
    timezone: Optional[str] = Field(None, max_length=50)
    constraints: Optional[dict] = None
    notification_preferences: Optional[dict] = None


class MissionResponse(MissionBase):
    """Schema for mission response."""
    id: str
    user_id: int
    state: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MissionTransition(BaseModel):
    """Schema for mission state transition request."""
    target_state: str = Field(..., description="Target state for transition")


# MissionRun Schemas
class MissionRunBase(BaseModel):
    """Base mission run schema."""
    run_date: date
    summary: Optional[str] = None
    workout_json: Optional[dict] = None
    metrics_json: Optional[dict] = None


class MissionRunCreate(MissionRunBase):
    """Schema for creating a mission run."""


class MissionRunUpdate(BaseModel):
    """Schema for updating a mission run (all fields optional)."""
    run_date: Optional[date] = None
    summary: Optional[str] = None
    workout_json: Optional[dict] = None
    metrics_json: Optional[dict] = None


class MissionRunResponse(MissionRunBase):
    """Schema for mission run response."""
    id: str
    mission_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# EventProgress Schemas
class EventProgressBase(BaseModel):
    """Base event progress schema."""
    stage_number: int = Field(..., ge=1)
    stage_type: str = Field(..., min_length=1, max_length=50)
    ride_mode: Optional[str] = Field(None, max_length=50)
    points: int = Field(default=0, ge=0)
    completed_at: Optional[datetime] = None
    bonuses: Optional[dict] = None


class EventProgressCreate(EventProgressBase):
    """Schema for creating event progress."""


class EventProgressUpdate(BaseModel):
    """Schema for updating event progress (all fields optional)."""
    stage_number: Optional[int] = Field(None, ge=1)
    stage_type: Optional[str] = Field(None, min_length=1, max_length=50)
    ride_mode: Optional[str] = Field(None, max_length=50)
    points: Optional[int] = Field(None, ge=0)
    completed_at: Optional[datetime] = None
    bonuses: Optional[dict] = None


class EventProgressResponse(EventProgressBase):
    """Schema for event progress response."""
    id: int
    mission_id: str
    created_at: datetime

    model_config = {"from_attributes": True}
