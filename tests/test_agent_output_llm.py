#!/usr/bin/env python
"""
Test script to demonstrate the new agent-based output with LLM reasoning.
"""
from datetime import date
from dotenv import load_dotenv

# Add project to path
from setup import setup_path
setup_path()

# Load environment variables
load_dotenv()

# Import local modules
from src.lanterne_rouge.mission_config import bootstrap
from src.lanterne_rouge.tour_coach import TourCoach

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
        # These values are used in the full agent flow but not needed in this test
        # next_phase_start = config.next_phase_start(scenario["test_date"])
        # days_to_next calculation removed - not needed in this test
        # days_to_goal calculation removed - not needed in this test

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
