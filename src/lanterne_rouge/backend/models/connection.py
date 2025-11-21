"""Database models for data connections (Strava, Oura, Apple Health)."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    DateTime, ForeignKey, Integer, String, Text
)
from sqlalchemy.orm import Mapped, mapped_column

from lanterne_rouge.backend.models.user import Base


class DataConnection(Base):
    """Data connection model for tracking user's connected services."""
    __tablename__ = "data_connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Connection type: strava, oura, apple_health
    connection_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )

    # Connection status: connected, disconnected, error
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="disconnected"
    )

    # Encrypted credentials (JSON string encrypted with Fernet)
    encrypted_credentials: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Last successful data refresh
    last_refresh_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Last refresh status message
    last_refresh_status: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Error message if connection failed
    error_message: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Timestamps
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


class StravaActivity(Base):
    """Strava activity data storage."""
    __tablename__ = "strava_activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Strava activity ID (from Strava API)
    strava_activity_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Activity details
    activity_name: Mapped[str] = mapped_column(String(255), nullable=False)
    activity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    activity_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    # Metrics (stored as JSON string for flexibility)
    metrics: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
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


class OuraData(Base):
    """Oura readiness and HRV data storage."""
    __tablename__ = "oura_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Date for the data point
    data_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    # Readiness score
    readiness_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # HRV metrics (stored as JSON string for flexibility)
    hrv_metrics: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Raw data from Oura API (stored as JSON string)
    raw_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
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


class AppleHealthData(Base):
    """Apple Health data storage."""
    __tablename__ = "apple_health_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Date for the data point
    data_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    # Daily metrics (stored as JSON string for flexibility)
    daily_metrics: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Upload batch ID (to track which upload this data came from)
    upload_batch_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Timestamps
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
