"""Background job API endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from lanterne_rouge.backend.api.dependencies import get_current_admin_user
from lanterne_rouge.backend.db.session import get_db
from lanterne_rouge.backend.models.user import User
from lanterne_rouge.backend.services.mission_lifecycle import MissionLifecycleService

router = APIRouter(prefix="/jobs", tags=["background jobs"])


@router.post("/check-mission-transitions")
def check_mission_transitions(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Check all missions and perform automatic state transitions based on dates.
    
    This endpoint should be called periodically (e.g., daily) to automatically
    transition missions:
    - TRAINING -> EVENT_ACTIVE when event_start_date <= today
    - EVENT_ACTIVE -> MISSION_COMPLETE when event_end_date < today
    
    Requires admin privileges.
    
    Args:
        current_admin: Current authenticated admin user
        db: Database session
        
    Returns:
        Dictionary with transitions performed
    """
    transitions = MissionLifecycleService.check_automatic_transitions(db)
    
    return {
        "status": "success",
        "transitions_performed": len(transitions),
        "transitions": transitions
    }
