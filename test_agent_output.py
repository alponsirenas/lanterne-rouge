#!/usr/bin/env python
"""
Test script to demonstrate the new agent-based output with LLM reasoning.
"""
import sys
import os
from datetime import date, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from lanterne_rouge.mission_config import bootstrap
from lanterne_rouge.tour_coach import TourCoach
    def __init__(self):
        self.id = "tdf-sim-2025"
        self.name = "Tour de France Simulation 2025"
        self.start_date = date(2025, 5, 1)
        self.goal_date = date(2025, 7, 27)  # TDF finish
        self.athlete_ftp = 280
    
    def training_phase(self, today: date) -> str:
        """Determine current training phase based on date."""
        days_out = (self.goal_date - today).days
        if days_out > 42:
            return "Base"
        elif 42 >= days_out > 21:
            return "Build"
        elif 21 >= days_out > 7:
            return "Peak"
        else:
            return "Taper"
    
    def next_phase_start(self, today: date) -> date | None:
        """Calculate when the next training phase begins."""
        if today >= self.goal_date:
            return None
        phase = self.training_phase(today)
        if phase == "Base":
            return self.goal_date - timedelta(days=42)
        elif phase == "Build":
            return self.goal_date - timedelta(days=21)
        elif phase == "Peak":
            return self.goal_date - timedelta(days=7)
        return self.goal_date

class MockTrainingDecision:
    def __init__(self, action, reason, intensity, flags, confidence):
        self.action = action
        self.reason = reason
        self.intensity_recommendation = intensity
        self.flags = flags
        self.confidence = confidence

class MockWorkoutPlan:
    def __init__(self, workout_type, description, duration, zones, load):
        self.workout_type = workout_type
        self.description = description
        self.duration_minutes = duration
        self.zones = zones
        self.estimated_load = load

def test_output_scenarios():
    """Test different training scenarios and show output."""
    
    # Import our communication agent
    from lanterne_rouge.ai_clients import CommunicationAgent
    
    config = MockMissionConfig()
    comm_agent = CommunicationAgent()
    
    print("=" * 80)
    print("LANTERNE ROUGE AGENT-BASED OUTPUT EXAMPLES")
    print("=" * 80)
    
    # Scenario 1: Base Phase, Good Metrics
    print("\n🔸 SCENARIO 1: Base Phase, Good Metrics")
    print("-" * 50)
    
    metrics1 = {
        "readiness_score": 85,
        "ctl": 45,
        "atl": 42,
        "tsb": 3
    }
    
    decision1 = MockTrainingDecision(
        action="maintain",
        reason="Metrics indicate steady training state with good recovery",
        intensity="moderate",
        flags=[],
        confidence=0.8
    )
    
    workout1 = MockWorkoutPlan(
        workout_type="Base Endurance",
        description="Aerobic base building with steady effort",
        duration=90,
        zones={"Zone 1": 15, "Zone 2": 70, "Zone 3": 5},
        load=75
    )
    
    current_date = date(2025, 6, 1)  # Early base phase
    summary1 = comm_agent.generate_summary(decision1, workout1, metrics1, config, current_date)
    print(summary1)
    
    # Scenario 2: Build Phase, Moderate Fatigue
    print("\n\n🔸 SCENARIO 2: Build Phase, Moderate Fatigue")
    print("-" * 50)
    
    metrics2 = {
        "readiness_score": 72,
        "ctl": 58,
        "atl": 68,
        "tsb": -10
    }
    
    decision2 = MockTrainingDecision(
        action="ease",
        reason="TSB at -10.0 suggests moderate fatigue",
        intensity="moderate",
        flags=["negative_tsb"],
        confidence=0.8
    )
    
    workout2 = MockWorkoutPlan(
        workout_type="Endurance Ride",
        description="Steady aerobic effort to maintain fitness",
        duration=75,
        zones={"Zone 1": 10, "Zone 2": 60, "Zone 3": 5},
        load=65
    )
    
    current_date = date(2025, 6, 30)  # Build phase
    summary2 = comm_agent.generate_summary(decision2, workout2, metrics2, config, current_date)
    print(summary2)
    
    # Scenario 3: Peak Phase, High Readiness
    print("\n\n🔸 SCENARIO 3: Peak Phase, High Readiness")
    print("-" * 50)
    
    metrics3 = {
        "readiness_score": 92,
        "ctl": 68,
        "atl": 55,
        "tsb": 13
    }
    
    decision3 = MockTrainingDecision(
        action="push",
        reason="TSB at 13.0 indicates good recovery state",
        intensity="high",
        flags=[],
        confidence=0.9
    )
    
    workout3 = MockWorkoutPlan(
        workout_type="VO2max Intervals",
        description="High-intensity work to sharpen racing fitness",
        duration=60,
        zones={"Zone 1": 15, "Zone 2": 25, "Zone 5": 15, "Zone 3": 5},
        load=105
    )
    
    current_date = date(2025, 7, 15)  # Peak phase
    summary3 = comm_agent.generate_summary(decision3, workout3, metrics3, config, current_date)
    print(summary3)
    
    # Scenario 4: Recovery Day
    print("\n\n🔸 SCENARIO 4: Recovery Day (Low Readiness)")
    print("-" * 50)
    
    metrics4 = {
        "readiness_score": 65,
        "ctl": 62,
        "atl": 78,
        "tsb": -16
    }
    
    decision4 = MockTrainingDecision(
        action="recover",
        reason="Readiness at 65 and TSB at -16.0 indicate need for recovery",
        intensity="low",
        flags=["low_readiness", "negative_tsb"],
        confidence=0.9
    )
    
    workout4 = MockWorkoutPlan(
        workout_type="Recovery Ride",
        description="Easy spinning to promote recovery",
        duration=45,
        zones={"Zone 1": 40, "Zone 2": 5},
        load=30
    )
    
    current_date = date(2025, 6, 15)  # Build phase but need recovery
    summary4 = comm_agent.generate_summary(decision4, workout4, metrics4, config, current_date)
    print(summary4)
    
    print("\n" + "=" * 80)
    print("END OF EXAMPLES")
    print("=" * 80)

if __name__ == "__main__":
    test_output_scenarios()
