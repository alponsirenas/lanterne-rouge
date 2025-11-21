"""Pydantic schemas for data connections."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# Connection status schemas
class ConnectionStatus(BaseModel):
    """Connection status response."""
    connection_type: str = Field(..., description="Type of connection (strava, oura, apple_health)")
    status: str = Field(..., description="Connection status (connected, disconnected, error)")
    last_refresh_at: Optional[datetime] = Field(None, description="Last successful refresh timestamp")
    last_refresh_status: Optional[str] = Field(None, description="Status message from last refresh")
    error_message: Optional[str] = Field(None, description="Error message if connection failed")


class AllConnectionsStatus(BaseModel):
    """Status of all data connections."""
    strava: Optional[ConnectionStatus] = None
    oura: Optional[ConnectionStatus] = None
    apple_health: Optional[ConnectionStatus] = None


# Strava OAuth schemas
class StravaAuthRequest(BaseModel):
    """Request to initiate Strava OAuth."""
    redirect_uri: str = Field(..., description="URI to redirect to after authorization")


class StravaAuthResponse(BaseModel):
    """Response with Strava authorization URL."""
    authorization_url: str = Field(..., description="URL to redirect user to for authorization")


class StravaCallbackRequest(BaseModel):
    """Strava OAuth callback data."""
    code: str = Field(..., description="Authorization code from Strava")
    scope: str = Field(..., description="Scope granted by user")


class StravaConnectionResponse(BaseModel):
    """Response after successful Strava connection."""
    message: str = Field(..., description="Success message")
    status: ConnectionStatus


# Oura PAT schemas
class OuraConnectRequest(BaseModel):
    """Request to connect Oura with Personal Access Token."""
    personal_access_token: str = Field(..., description="Oura Personal Access Token")


class OuraConnectionResponse(BaseModel):
    """Response after successful Oura connection."""
    message: str = Field(..., description="Success message")
    status: ConnectionStatus


# Apple Health schemas
class AppleHealthUploadResponse(BaseModel):
    """Response after Apple Health data upload."""
    message: str = Field(..., description="Success message")
    records_processed: int = Field(..., description="Number of records processed")
    upload_batch_id: str = Field(..., description="Unique identifier for this upload batch")


# Disconnect schemas
class DisconnectRequest(BaseModel):
    """Request to disconnect a data source."""
    connection_type: str = Field(..., description="Type of connection to disconnect")


class DisconnectResponse(BaseModel):
    """Response after disconnecting a data source."""
    message: str = Field(..., description="Success message")


# Data refresh schemas
class RefreshRequest(BaseModel):
    """Request to manually refresh data from a source."""
    connection_type: str = Field(..., description="Type of connection to refresh")


class RefreshResponse(BaseModel):
    """Response after data refresh."""
    message: str = Field(..., description="Status message")
    records_updated: int = Field(..., description="Number of records updated")
    last_refresh_at: datetime = Field(..., description="Timestamp of refresh")


# Activity data schemas
class ActivityMetrics(BaseModel):
    """Metrics from a single activity."""
    distance: Optional[float] = None
    duration: Optional[float] = None
    elevation_gain: Optional[float] = None
    average_speed: Optional[float] = None
    max_speed: Optional[float] = None
    average_power: Optional[float] = None
    max_power: Optional[float] = None
    average_heartrate: Optional[float] = None
    max_heartrate: Optional[float] = None
    calories: Optional[float] = None
    tss: Optional[float] = None  # Training Stress Score
    if_score: Optional[float] = None  # Intensity Factor


class StravaActivityResponse(BaseModel):
    """Response with Strava activity data."""
    id: int
    strava_activity_id: str
    activity_name: str
    activity_type: str
    activity_date: datetime
    metrics: Optional[ActivityMetrics] = None


# Readiness data schemas
class ReadinessData(BaseModel):
    """Readiness data from Oura."""
    date: datetime
    readiness_score: Optional[int] = None
    hrv_balance: Optional[float] = None
    recovery_index: Optional[float] = None
    temperature_deviation: Optional[float] = None
    resting_heart_rate: Optional[int] = None


class OuraDataResponse(BaseModel):
    """Response with Oura data."""
    id: int
    data_date: datetime
    readiness_score: Optional[int] = None
    hrv_metrics: Optional[dict] = None


# Apple Health data schemas
class AppleHealthMetrics(BaseModel):
    """Daily metrics from Apple Health."""
    steps: Optional[int] = None
    distance: Optional[float] = None
    active_energy: Optional[float] = None
    resting_heart_rate: Optional[int] = None
    hrv: Optional[float] = None
    sleep_hours: Optional[float] = None


class AppleHealthDataResponse(BaseModel):
    """Response with Apple Health data."""
    id: int
    data_date: datetime
    daily_metrics: Optional[AppleHealthMetrics] = None
