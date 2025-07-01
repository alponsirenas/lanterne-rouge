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

def test_agent_output():
    """Test the agent-based output with various scenarios."""
    
    # Load real mission config
    config = bootstrap("missions/tdf_sim_2025.toml")
    
    # Create tour coach with LLM reasoning (default)
    coach = TourCoach(config)
    
    print("=" * 80)
    print("LANTERNE ROUGE AGENT-BASED OUTPUT EXAMPLES (LLM MODE)")
    print("=" * 80)
    
    # Test scenarios
    scenarios = [
        {
            "title": "Base Phase, Good Metrics",
            "metrics": {
                "readiness_score": 85,
                "ctl": 45,
                "atl": 42,
                "tsb": 3,
                "resting_heart_rate": 48,
                "hrv": 45
            },
            "test_date": date(2025, 5, 15)  # Base phase
        },
        {
            "title": "Build Phase, Moderate Fatigue", 
            "metrics": {
                "readiness_score": 72,
                "ctl": 58,
                "atl": 68,
                "tsb": -10,
                "resting_heart_rate": 52,
                "hrv": 38
            },
            "test_date": date(2025, 6, 8)  # Build phase
        },
        {
            "title": "Peak Phase, High Readiness",
            "metrics": {
                "readiness_score": 92,
                "ctl": 68,
                "atl": 55,
                "tsb": 13,
                "resting_heart_rate": 46,
                "hrv": 52
            },
            "test_date": date(2025, 6, 23)  # Peak phase
        },
        {
            "title": "Recovery Day (Low Readiness)",
            "metrics": {
                "readiness_score": 65,
                "ctl": 62,
                "atl": 78,
                "tsb": -16,
                "resting_heart_rate": 56,
                "hrv": 32
            },
            "test_date": date(2025, 6, 1)  # Build phase
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n🔸 SCENARIO {i}: {scenario['title']}")
        print("-" * 50)
        
        # Generate recommendation using real coach
        metrics = scenario["metrics"]
        
        # Get individual components to show the reasoning in detail
        decision = coach.reasoning_agent.make_decision(
            metrics, config, scenario["test_date"]
        )
        
        phase = config.training_phase(scenario["test_date"])
        next_phase_start = config.next_phase_start(scenario["test_date"])
        days_to_next = (next_phase_start - scenario["test_date"]).days if next_phase_start else None
        days_to_goal = (config.goal_date - scenario["test_date"]).days
        
        workout = coach.workout_planner.generate_workout(decision, phase)
        
        # Generate summary using communication agent
        summary = coach.communication_agent.generate_summary(
            decision, workout, metrics, config, scenario["test_date"]
        )
        
        print(summary)
        print()
    
    print("=" * 80)
    print("END OF EXAMPLES")
    print("=" * 80)

if __name__ == "__main__":
    test_agent_output()
