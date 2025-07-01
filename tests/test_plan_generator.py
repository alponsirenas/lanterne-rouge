"""
Tests for the plan_generator module.
"""
import pytest
from datetime import date
from unittest.mock import patch, MagicMock

# Add project to path
from setup import setup_path
setup_path()

from src.lanterne_rouge.plan_generator import WorkoutPlanner
from src.lanterne_rouge.mission_config import MissionConfig, AthleteConfig, ConstraintsConfig
from src.lanterne_rouge.reasoner import TrainingDecision

def create_test_config():
    """Create a test configuration."""
    return MissionConfig(
        id="test",
        name="Test Mission",
        athlete=AthleteConfig(ftp=250, weight_kg=70),
        start_date=date(2025, 1, 1),
        goal_date=date(2025, 12, 31),
        constraints=ConstraintsConfig(
            min_readiness=65,
            min_tsb=-10,
        )
    )

def test_workout_planner_generate():
    """Test the WorkoutPlanner.generate_workout method."""
    config = create_test_config()
    planner = WorkoutPlanner(config)
    
    # Test MAINTAIN decision in Base phase
    decision = TrainingDecision(
        action="maintain", 
        reason="Test reason",
        intensity_recommendation="moderate",
        flags=[],
        confidence=1.0
    )
    workout = planner.generate_workout(decision, "Base")
    
    # Verify workout structure
    assert workout.workout_type is not None
    assert workout.description is not None
    assert workout.duration_minutes > 0
    assert workout.estimated_load > 0
    assert len(workout.zones) > 0
    assert sum(workout.zones.values()) == workout.duration_minutes
    
    # Test RECOVER decision in Build phase
    decision = TrainingDecision(
        action="recover", 
        reason="Test reason",
        intensity_recommendation="low",
        flags=["fatigue"],
        confidence=1.0
    )
    workout = planner.generate_workout(decision, "Build")
    
    # Recovery workouts should be easier
    assert workout.estimated_load < 80  # Lower load for recovery
    assert workout.workout_type is not None
    
    # Test INCREASE decision in Peak phase
    decision = TrainingDecision(
        action="increase", 
        reason="Test reason",
        intensity_recommendation="high",
        flags=["ready_for_load"],
        confidence=1.0
    )
    workout = planner.generate_workout(decision, "Peak")
    
    # Increased intensity workouts should be harder
    assert workout.estimated_load > 80  # Higher load for intense workouts
    assert workout.workout_type is not None

if __name__ == "__main__":
    # Run the tests
    test_workout_planner_generate()
    print("All plan_generator tests passed!")
