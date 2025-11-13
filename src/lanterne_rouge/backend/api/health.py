"""Health check endpoint."""
from datetime import datetime, timezone

from fastapi import APIRouter

from lanterne_rouge.backend.schemas.auth import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/healthz", response_model=HealthResponse)
def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status, timestamp, and API version
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
        version="1.0.0"
    )
