"""Mission API endpoints."""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from lanterne_rouge.backend.api.dependencies import get_current_user
from lanterne_rouge.backend.db.session import get_db
from lanterne_rouge.backend.models.mission import Mission
from lanterne_rouge.backend.models.user import AuditLog, User
from lanterne_rouge.backend.schemas.mission import (
    MissionCreate,
    MissionResponse,
    MissionTransition,
    MissionUpdate,
)
from lanterne_rouge.backend.schemas.mission_builder import (
    MissionBuilderQuestionnaire,
    MissionDraftResponse,
)
from lanterne_rouge.backend.services.mission_lifecycle import MissionLifecycleService
from lanterne_rouge.backend.services.mission_builder import generate_mission_draft

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/missions", tags=["missions"])


@router.get("", response_model=List[MissionResponse])
def list_missions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    List all missions for the current user.

    Args:
        current_user: Current authenticated user
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of missions
    """
    missions = db.query(Mission).filter(
        Mission.user_id == current_user.id
    ).offset(skip).limit(limit).all()

    return missions


@router.post("", response_model=MissionResponse, status_code=status.HTTP_201_CREATED)
def create_mission(
    mission_data: MissionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new mission.

    Args:
        mission_data: Mission creation data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created mission
    """
    # Validate dates
    if mission_data.event_end_date <= mission_data.event_start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event end date must be after start date"
        )

    if mission_data.prep_start_date and mission_data.prep_end_date:
        if mission_data.prep_end_date <= mission_data.prep_start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prep end date must be after prep start date"
            )

    # Create mission
    mission = Mission(
        user_id=current_user.id,
        name=mission_data.name,
        mission_type=mission_data.mission_type,
        event_start_date=mission_data.event_start_date,
        event_end_date=mission_data.event_end_date,
        prep_start_date=mission_data.prep_start_date,
        prep_end_date=mission_data.prep_end_date,
        points_schema=mission_data.points_schema,
        timezone=mission_data.timezone,
        constraints=mission_data.constraints,
        notification_preferences=mission_data.notification_preferences,
    )
    db.add(mission)

    # Log creation
    audit_log = AuditLog(
        user_id=current_user.id,
        action="create",
        resource="mission",
        resource_id=str(mission.id),
        details=f"Created mission: {mission.name}",
    )
    db.add(audit_log)

    db.commit()
    db.refresh(mission)

    return mission


@router.get("/{mission_id}", response_model=MissionResponse)
def get_mission(
    mission_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific mission by ID.

    Args:
        mission_id: Mission ID (UUID string)
        current_user: Current authenticated user
        db: Database session

    Returns:
        Mission details

    Raises:
        HTTPException: If mission not found or access denied
    """
    mission = db.query(Mission).filter(Mission.id == mission_id).first()

    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mission not found"
        )

    # Check ownership
    if mission.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this mission"
        )

    return mission


@router.put("/{mission_id}", response_model=MissionResponse)
def update_mission(
    mission_id: str,
    mission_data: MissionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a mission.

    Args:
        mission_id: Mission ID (UUID string)
        mission_data: Mission update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated mission

    Raises:
        HTTPException: If mission not found or access denied
    """
    mission = db.query(Mission).filter(Mission.id == mission_id).first()

    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mission not found"
        )

    # Check ownership
    if mission.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this mission"
        )

    # Update fields if provided
    update_data = mission_data.model_dump(exclude_unset=True)

    # Validate dates if updated
    event_start = update_data.get("event_start_date", mission.event_start_date)
    event_end = update_data.get("event_end_date", mission.event_end_date)
    if event_end <= event_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event end date must be after start date"
        )

    prep_start = update_data.get("prep_start_date", mission.prep_start_date)
    prep_end = update_data.get("prep_end_date", mission.prep_end_date)
    if prep_start and prep_end and prep_end <= prep_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prep end date must be after prep start date"
        )

    for field, value in update_data.items():
        setattr(mission, field, value)

    # Log update
    audit_log = AuditLog(
        user_id=current_user.id,
        action="update",
        resource="mission",
        resource_id=str(mission.id),
        details=f"Updated mission: {mission.name}",
    )
    db.add(audit_log)

    db.commit()
    db.refresh(mission)

    return mission


@router.delete("/{mission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mission(
    mission_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a mission.

    Args:
        mission_id: Mission ID (UUID string)
        current_user: Current authenticated user
        db: Database session

    Raises:
        HTTPException: If mission not found or access denied
    """
    mission = db.query(Mission).filter(Mission.id == mission_id).first()

    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mission not found"
        )

    # Check ownership
    if mission.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this mission"
        )

    # Log deletion
    audit_log = AuditLog(
        user_id=current_user.id,
        action="delete",
        resource="mission",
        resource_id=str(mission.id),
        details=f"Deleted mission: {mission.name}",
    )
    db.add(audit_log)

    db.delete(mission)
    db.commit()


@router.post("/{mission_id}/transition", response_model=MissionResponse)
def transition_mission(
    mission_id: str,
    transition_data: MissionTransition,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Manually transition a mission to a new state.

    Args:
        mission_id: Mission ID (UUID string)
        transition_data: Transition data with target state
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated mission

    Raises:
        HTTPException: If mission not found, access denied, or invalid transition
    """
    mission = db.query(Mission).filter(Mission.id == mission_id).first()

    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mission not found"
        )

    # Check ownership
    if mission.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to transition this mission"
        )

    # Perform transition
    mission = MissionLifecycleService.transition_state(
        db=db,
        mission=mission,
        target_state=transition_data.target_state,
        is_admin=current_user.is_admin
    )

    # Log transition
    audit_log = AuditLog(
        user_id=current_user.id,
        action="transition",
        resource="mission",
        resource_id=str(mission.id),
        details=f"Transitioned mission {mission.name} to {mission.state}",
    )
    db.add(audit_log)
    db.commit()

    return mission


@router.post("/draft", response_model=MissionDraftResponse, status_code=status.HTTP_201_CREATED)
async def create_mission_draft(
    questionnaire: MissionBuilderQuestionnaire,
    current_user: User = Depends(get_current_user),
):
    """
    Generate a mission draft using LLM based on questionnaire responses.
    
    This endpoint uses OpenAI GPT-4o-mini in JSON mode to create a personalized
    mission configuration. The draft is NOT saved to the database - it's returned
    for the user to review and confirm.
    
    Args:
        questionnaire: User's questionnaire responses
        current_user: Current authenticated user
    
    Returns:
        MissionDraftResponse with generated mission configuration
    
    Raises:
        HTTPException: 502 if LLM generation fails after retry
        HTTPException: 500 for other server errors
    """
    try:
        # Generate draft using LLM
        draft_response, error = await generate_mission_draft(questionnaire)
        
        if error:
            # Log the actual error details for debugging
            logger.error(f"Failed to generate mission draft: {error}")
            # Return generic error message to client to avoid leaking system internals
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to generate mission draft due to an upstream service error"
            )
        
        return draft_response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log unexpected errors with full details
        logger.error(f"Unexpected error generating mission draft: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating the mission draft"
        )
