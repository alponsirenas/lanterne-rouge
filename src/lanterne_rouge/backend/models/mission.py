"""Database models for missions and related entities."""
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lanterne_rouge.backend.models.user import Base
import enum


class MissionState(str, enum.Enum):
    """Mission lifecycle states."""
    PREP = "PREP"
    TRAINING = "TRAINING"
    EVENT_ACTIVE = "EVENT_ACTIVE"
    MISSION_COMPLETE = "MISSION_COMPLETE"


class Mission(Base):
    """Mission model for tracking training missions and events."""
    __tablename__ = "missions"

    # Primary key - using UUID as string (SQLite compatible)
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
        nullable=False
    )
    
    # Foreign key to user
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Mission metadata
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    mission_type: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Date fields
    prep_start_date: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)
    prep_end_date: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)
    event_start_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    event_end_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    
    # State management
    state: Mapped[str] = mapped_column(
        SQLEnum(MissionState),
        default=MissionState.PREP,
        nullable=False,
        index=True
    )
    
    # Points schema stored as JSON
    points_schema: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # Timezone for date calculations
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    
    # Constraints and preferences stored as JSON
    constraints: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    notification_preferences: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    # Relationships
    runs: Mapped[list["MissionRun"]] = relationship(
        "MissionRun",
        back_populates="mission",
        cascade="all, delete-orphan"
    )
    progress_entries: Mapped[list["EventProgress"]] = relationship(
        "EventProgress",
        back_populates="mission",
        cascade="all, delete-orphan"
    )


class MissionRun(Base):
    """Mission run tracking individual workout/ride sessions."""
    __tablename__ = "mission_runs"

    # Primary key - using UUID as specified
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
        nullable=False
    )
    
    # Foreign key to mission
    mission_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("missions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Run metadata
    run_date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Workout and metrics data stored as JSON
    workout_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    metrics_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    # Relationships
    mission: Mapped["Mission"] = relationship("Mission", back_populates="runs")


class EventProgress(Base):
    """Event progress tracking for multi-stage missions."""
    __tablename__ = "event_progress"

    # Composite primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to mission
    mission_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("missions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Stage information
    stage_number: Mapped[int] = mapped_column(Integer, nullable=False)
    stage_type: Mapped[str] = mapped_column(String(50), nullable=False)
    ride_mode: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Points and completion
    points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Bonuses stored as JSON
    bonuses: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    # Relationships
    mission: Mapped["Mission"] = relationship("Mission", back_populates="progress_entries")
