import pytest
from unittest.mock import MagicMock, patch
from lanterne_rouge.ai_clients import generate_workout_adjustment

@patch("lanterne_rouge.ai_clients.call_llm")
def test_generate_workout_adjustment_returns_list(mock_call_llm):
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
