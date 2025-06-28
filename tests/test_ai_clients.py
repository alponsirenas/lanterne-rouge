"""Tests for the AI clients module functionality."""
import os
import sys
from unittest.mock import MagicMock, patch

# Add the src directory to Python path to find lanterne_rouge package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lanterne_rouge.ai_clients import generate_workout_adjustment


@patch("lanterne_rouge.ai_clients.call_llm")
def test_generate_workout_adjustment_returns_list(mock_call_llm):
    """Test that generate_workout_adjustment returns a list of strings."""
    mock_call_llm.return_value = "- Rest day\n- Easy ride"
    mission_cfg = MagicMock()
    mission_cfg.dict.return_value = {}
    adj = generate_workout_adjustment(
        readiness_score=80,
        readiness_details={},
        ctl=50,
        atl=40,
        tsb=10,
        mission_cfg=mission_cfg,
    )
    assert isinstance(adj, list)
    assert adj == ["Rest day", "Easy ride"]


@patch("lanterne_rouge.ai_clients.call_llm")
def test_generate_workout_adjustment_handles_invalid_json(mock_call_llm):
    """Test that generate_workout_adjustment handles invalid JSON responses gracefully."""
    mock_call_llm.return_value = "Invalid JSON"
    mission_cfg = MagicMock()
    mission_cfg.dict.return_value = {}
    adj = generate_workout_adjustment(
        readiness_score=80,
        readiness_details={},
        ctl=50,
        atl=40,
        tsb=10,
        mission_cfg=mission_cfg,
    )
    # The function now handles invalid responses gracefully
    assert isinstance(adj, list)
    assert len(adj) > 0  # Should have a default response


@patch("lanterne_rouge.ai_clients.call_llm")
def test_generate_workout_adjustment_handles_empty_response(mock_call_llm):
    """Test that generate_workout_adjustment handles empty responses gracefully."""
    mock_call_llm.return_value = ""  # Empty response
    mission_cfg = MagicMock()
    mission_cfg.dict.return_value = {}
    adj = generate_workout_adjustment(
        readiness_score=80,
        readiness_details={},
        ctl=50,
        atl=40,
        tsb=10,
        mission_cfg=mission_cfg,
    )
    # Should return default response
    assert isinstance(adj, list)
    assert adj == ["Plan looks good. Continue with scheduled workout."]
