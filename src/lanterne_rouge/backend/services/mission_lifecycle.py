"""Mission lifecycle service."""
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from lanterne_rouge.backend.models.mission import Mission, MissionState


class MissionLifecycleService:
    """Service for managing mission lifecycle and state transitions."""

    # Valid state transitions
    VALID_TRANSITIONS = {
        MissionState.PREP: [MissionState.TRAINING],
        MissionState.TRAINING: [MissionState.EVENT_ACTIVE],  # PREP revert is admin-only
        MissionState.EVENT_ACTIVE: [MissionState.MISSION_COMPLETE],
        MissionState.MISSION_COMPLETE: [],  # Terminal state
    }

    @classmethod
    def validate_transition(
        cls,
        current_state: MissionState,
        target_state: MissionState,
        is_admin: bool = False
    ) -> tuple[bool, Optional[str]]:
        """
        Validate if a state transition is allowed.

        Args:
            current_state: Current mission state
            target_state: Target mission state
            is_admin: Whether the user has admin privileges

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Can't transition to same state
        if current_state == target_state:
            return False, "Mission is already in target state"

        # Check if transition is valid
        valid_next_states = cls.VALID_TRANSITIONS.get(current_state, [])
        if target_state not in valid_next_states:
            # Special case: admin can revert TRAINING -> PREP
            if (is_admin and
                current_state == MissionState.TRAINING and
                target_state == MissionState.PREP):
                return True, None

            return False, (
                f"Invalid transition from {current_state.value} to {target_state.value}. "
                f"Valid transitions: {[s.value for s in valid_next_states]}"
            )

        return True, None

    @classmethod
    def transition_state(
        cls,
        db: Session,
        mission: Mission,
        target_state: str,
        is_admin: bool = False
    ) -> Mission:
        """
        Transition a mission to a new state.

        Args:
            db: Database session
            mission: Mission to transition
            target_state: Target state string
            is_admin: Whether the user has admin privileges

        Returns:
            Updated mission

        Raises:
            HTTPException: If transition is invalid
        """
        # Parse target state
        try:
            target = MissionState(target_state)
        except ValueError as exc:
            valid_states = [s.value for s in MissionState]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid state '{target_state}'. Valid states: {valid_states}"
            ) from exc

        # Validate transition
        current = MissionState(mission.state)
        is_valid, error_msg = cls.validate_transition(current, target, is_admin)

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_msg
            )

        # Update state
        mission.state = target.value
        mission.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(mission)

        return mission

    @classmethod
    def check_automatic_transitions(cls, db: Session) -> list[dict]:
        """
        Check all missions and perform automatic state transitions based on dates.

        Automatic transitions:
        - TRAINING -> EVENT_ACTIVE when event_start_date <= today
        - EVENT_ACTIVE -> MISSION_COMPLETE when event_end_date < today

        Args:
            db: Database session

        Returns:
            List of transitions performed with details
        """
        transitions = []
        today = date.today()

        # Find missions in TRAINING state that should move to EVENT_ACTIVE
        training_missions = db.query(Mission).filter(
            Mission.state == MissionState.TRAINING.value,
            Mission.event_start_date <= today
        ).all()

        for mission in training_missions:
            old_state = mission.state
            mission.state = MissionState.EVENT_ACTIVE.value
            mission.updated_at = datetime.now(timezone.utc)
            transitions.append({
                "mission_id": str(mission.id),
                "mission_name": mission.name,
                "old_state": old_state,
                "new_state": mission.state,
                "reason": f"Event start date reached ({mission.event_start_date})"
            })

        # Find missions in EVENT_ACTIVE state that should move to MISSION_COMPLETE
        active_missions = db.query(Mission).filter(
            Mission.state == MissionState.EVENT_ACTIVE.value,
            Mission.event_end_date < today
        ).all()

        for mission in active_missions:
            old_state = mission.state
            mission.state = MissionState.MISSION_COMPLETE.value
            mission.updated_at = datetime.now(timezone.utc)
            transitions.append({
                "mission_id": str(mission.id),
                "mission_name": mission.name,
                "old_state": old_state,
                "new_state": mission.state,
                "reason": f"Event end date passed ({mission.event_end_date})"
            })

        if transitions:
            db.commit()

        return transitions
