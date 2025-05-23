import pytest
from datetime import date
from unittest.mock import patch, MagicMock
import openai
import os

os.environ["OPENAI_API_KEY"] = "test-key"
from lanterne_rouge.plan_generator import generate_workout_plan
from lanterne_rouge.mission_config import MissionConfig, Targets, Constraints

# Dummy mission config for tests
_dummy_cfg = MissionConfig(
    id="test",
    athlete_id="strava:0",
    start_date=date(2025, 1, 1),
    goal_event="test_event",
    goal_date=date(2025, 12, 31),
    targets=Targets(
        ctl_peak=100,
        long_ride_minutes=100,
        stage_climb_minutes=60,
        threshold_interval_min=20,
    ),
    constraints=Constraints(
        min_readiness=65,
        max_rhr=999,
        min_tsb=-10,
    ),
)

@patch("lanterne_rouge.plan_generator.openai.chat.completions.create")
@patch("lanterne_rouge.plan_generator.get_ctl_atl_tsb", return_value=(50, 40, 10))
@patch("lanterne_rouge.plan_generator.get_oura_readiness", return_value=(80, {}, "2025-01-01"))
def test_generate_workout_plan_happy_path(mock_readiness, mock_ctl_atl, mock_openai):
    openai.api_key = "test-key"
    # Prepare a fake LLM response object
    fake_message = MagicMock()
    fake_message.content = '{"workouts": ["test_plan"]}'
    fake_choice = MagicMock()
    fake_choice.message = fake_message
    mock_openai.return_value = MagicMock(choices=[fake_choice])

    plan = generate_workout_plan(_dummy_cfg, memory={"foo":"bar"})
    assert isinstance(plan, dict)
    assert "workouts" in plan
    assert plan["workouts"] == ["test_plan"]
    mock_openai.assert_called_once()


@patch("lanterne_rouge.plan_generator.openai.chat.completions.create", side_effect=openai.OpenAIError("boom"))
@patch("lanterne_rouge.plan_generator.get_ctl_atl_tsb", return_value=(50, 40, 10))
@patch("lanterne_rouge.plan_generator.get_oura_readiness", return_value=(80, {}, "2025-01-01"))
def test_generate_workout_plan_openai_error(mock_readiness, mock_ctl_atl, mock_openai):
    openai.api_key = "test-key"
    plan = generate_workout_plan(_dummy_cfg, memory={"foo": "bar"})
    assert plan == {}

@patch("lanterne_rouge.plan_generator.print")
@patch("lanterne_rouge.plan_generator.openai.chat.completions.create")
@patch("lanterne_rouge.plan_generator.get_ctl_atl_tsb", return_value=(50, 40, 10))
@patch("lanterne_rouge.plan_generator.get_oura_readiness", return_value=(80, {}, "2025-01-01"))
def test_generate_workout_plan_prints_messages(mock_readiness, mock_ctl_atl, mock_openai, mock_print):
    openai.api_key = "test-key"
    # Prepare a fake LLM response object
    fake_message = MagicMock()
    fake_message.content = '{"workouts": ["test_plan"]}'
    fake_choice = MagicMock()
    fake_choice.message = fake_message
    mock_openai.return_value = MagicMock(choices=[fake_choice])

    plan = generate_workout_plan(_dummy_cfg, memory={"foo":"bar"})
    assert isinstance(plan, dict)
    assert plan["workouts"] == ["test_plan"]
    mock_openai.assert_called_once()
    mock_print.assert_any_call("Generating workout plan...")
    mock_print.assert_any_call("Workout plan generated successfully")


@patch("lanterne_rouge.plan_generator.openai.chat.completions.create")
@patch("lanterne_rouge.plan_generator.get_ctl_atl_tsb", return_value=(50, 40, 10))
@patch("lanterne_rouge.plan_generator.get_oura_readiness", return_value=(80, {}, "2025-01-01"))
def test_generate_workout_plan_missing_workouts(mock_readiness, mock_ctl_atl, mock_openai):
    openai.api_key = "test-key"
    fake_message = MagicMock()
    fake_message.content = '{"foo": "bar"}'
    fake_choice = MagicMock()
    fake_choice.message = fake_message
    mock_openai.return_value = MagicMock(choices=[fake_choice])

    with pytest.raises(ValueError):
        generate_workout_plan(_dummy_cfg, memory={"foo": "bar"})
