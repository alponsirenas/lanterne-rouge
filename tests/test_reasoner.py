"""
Tests for the reasoner module.
"""
from datetime import date

# Add project to path
from setup import setup_path
setup_path()

from src.lanterne_rouge.reasoner import ReasoningAgent, TrainingDecision
from src.lanterne_rouge.mission_config import MissionConfig, AthleteConfig, ConstraintsConfig

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

def test_reasoning_agent_rule_based():
    """Test the rule-based reasoning in ReasoningAgent."""
    config = create_test_config()
    agent = ReasoningAgent(use_llm=False)
    
    # Test case 1: Good metrics
    metrics = {
        "readiness_score": 85,
        "ctl": 50,
        "atl": 45,
        "tsb": 5,
    }
    decision = agent.make_decision(metrics, config, date(2025, 6, 1))
    assert isinstance(decision, TrainingDecision)
    assert decision.action in ["recover", "maintain", "increase", "ease"]
    assert decision.reason is not None
    assert decision.intensity_recommendation in ["low", "moderate", "high"]
    
    # Test case 2: Low readiness
    metrics = {
        "readiness_score": 60,
        "ctl": 50,
        "atl": 45,
        "tsb": 5,
    }
    decision = agent.make_decision(metrics, config, date(2025, 6, 1))
    assert decision.action == "recover"
    
    # Test case 3: High fatigue (negative TSB)
    metrics = {
        "readiness_score": 70,
        "ctl": 50,
        "atl": 65,
        "tsb": -15,
    }
    decision = agent.make_decision(metrics, config, date(2025, 6, 1))
    assert decision.action in ["recover", "ease"]  # Should be conservative

if __name__ == "__main__":
    # Run the tests
    test_reasoning_agent_rule_based()
    print("All reasoner tests passed!")
