"""Tests for mission builder LLM integration and draft endpoint."""
import json
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from lanterne_rouge.backend.db.session import get_db
from lanterne_rouge.backend.main import app
from lanterne_rouge.backend.models.user import Base
from lanterne_rouge.backend.schemas.mission_builder import (
    MissionBuilderQuestionnaire,
    MissionDraft,
    WeeklyHours,
)

# Test database
TEST_DATABASE_URL = "sqlite:///./test_mission_builder.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """Override database dependency for testing."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def apply_db_override():
    """Apply dependency override scoped to this module."""
    original = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    yield
    if original is not None:
        app.dependency_overrides[get_db] = original
    else:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """Create and tear down test database for each test."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def test_user(client):
    """Create a test user and return user data with auth token."""
    user_data = {
        "email": "testuser@example.com",
        "password": "testpassword123"
    }
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 201

    # Login to get token
    response = client.post("/auth/login", json=user_data)
    assert response.status_code == 200
    token_data = response.json()

    return {
        "email": user_data["email"],
        "token": token_data["access_token"],
    }


@pytest.fixture
def sample_questionnaire():
    """Sample questionnaire data for testing."""
    event_date = date.today() + timedelta(days=90)
    return {
        "event_name": "Unbound 200",
        "event_date": event_date.isoformat(),
        "mission_type": "gravel_ultra",
        "weekly_hours": {"min": 8, "max": 12},
        "current_ftp": 250,
        "preferred_training_days": ["Monday", "Wednesday", "Saturday"],
        "constraints": "No injuries. Weekend mornings work best.",
        "riding_style": "steady",
        "notification_preferences": {
            "morning_briefing": True,
            "evening_summary": True,
            "weekly_review": True
        }
    }


@pytest.fixture
def sample_llm_response():
    """Sample LLM response data matching expected format."""
    prep_start = date.today() + timedelta(days=7)
    event_date = date.today() + timedelta(days=90)
    
    return {
        "name": "Unbound 200 Preparation Mission",
        "mission_type": "gravel_ultra",
        "prep_start": prep_start.isoformat(),
        "event_start": event_date.isoformat(),
        "event_end": event_date.isoformat(),
        "points_schema": {
            "description": "Points reward consistency and endurance focus for ultra-distance gravel",
            "daily_base": 15,
            "intensity_multipliers": {
                "easy": 1.1,
                "moderate": 1.8,
                "hard": 2.8
            }
        },
        "constraints": {
            "min_readiness": 70,
            "min_tsb": -12,
            "max_weekly_hours": 12
        },
        "notification_preferences": {
            "morning_briefing": True,
            "evening_summary": True,
            "weekly_review": True
        },
        "notes": "14-week preparation focusing on progressive volume build and event-specific demands."
    }


def test_questionnaire_validation_success(sample_questionnaire):
    """Test that valid questionnaire passes validation."""
    questionnaire = MissionBuilderQuestionnaire(**sample_questionnaire)
    assert questionnaire.event_name == "Unbound 200"
    assert questionnaire.mission_type == "gravel_ultra"
    assert questionnaire.current_ftp == 250


def test_questionnaire_validation_past_event():
    """Test that past event dates are rejected."""
    past_date = date.today() - timedelta(days=1)
    data = {
        "event_name": "Past Event",
        "event_date": past_date.isoformat(),
        "mission_type": "road_century",
        "weekly_hours": {"min": 5, "max": 10},
        "current_ftp": 200,
    }
    
    with pytest.raises(ValueError, match="Event date must be in the future"):
        MissionBuilderQuestionnaire(**data)


def test_questionnaire_validation_invalid_hours():
    """Test that invalid weekly hours are rejected."""
    future_date = date.today() + timedelta(days=30)
    data = {
        "event_name": "Test Event",
        "event_date": future_date.isoformat(),
        "mission_type": "road_century",
        "weekly_hours": {"min": 10, "max": 5},  # max < min
        "current_ftp": 200,
    }
    
    with pytest.raises(ValueError, match="max must be greater than or equal to min"):
        MissionBuilderQuestionnaire(**data)


def test_questionnaire_validation_ftp_bounds():
    """Test that FTP is within reasonable bounds."""
    future_date = date.today() + timedelta(days=30)
    
    # Too low
    with pytest.raises(ValueError):
        MissionBuilderQuestionnaire(
            event_name="Test",
            event_date=future_date,
            mission_type="road_century",
            weekly_hours={"min": 5, "max": 10},
            current_ftp=30  # Below minimum of 50
        )
    
    # Too high
    with pytest.raises(ValueError):
        MissionBuilderQuestionnaire(
            event_name="Test",
            event_date=future_date,
            mission_type="road_century",
            weekly_hours={"min": 5, "max": 10},
            current_ftp=600  # Above maximum of 500
        )


def test_mission_draft_validation_success(sample_llm_response):
    """Test that valid mission draft passes validation."""
    draft = MissionDraft(**sample_llm_response)
    assert draft.name == "Unbound 200 Preparation Mission"
    assert draft.mission_type == "gravel_ultra"
    assert draft.points_schema.daily_base == 15


def test_mission_draft_validation_invalid_dates():
    """Test that invalid dates are rejected in draft."""
    prep_date = date.today() + timedelta(days=7)
    event_date = date.today() + timedelta(days=5)  # Event before prep
    
    data = {
        "name": "Invalid Mission",
        "mission_type": "road_century",
        "prep_start": prep_date.isoformat(),
        "event_start": event_date.isoformat(),
        "event_end": event_date.isoformat(),
        "points_schema": {
            "description": "Test",
            "daily_base": 15,
            "intensity_multipliers": {"easy": 1.1, "moderate": 1.8, "hard": 2.8}
        },
        "constraints": {
            "min_readiness": 70,
            "min_tsb": -12,
            "max_weekly_hours": 10
        },
        "notification_preferences": {
            "morning_briefing": True,
            "evening_summary": True,
            "weekly_review": True
        },
        "notes": "Test notes"
    }
    
    with pytest.raises(ValueError, match="prep_start must be before event_start"):
        MissionDraft(**data)


@patch('lanterne_rouge.backend.services.mission_builder.openai.OpenAI')
@patch('lanterne_rouge.backend.services.mission_builder.os.getenv')
def test_draft_endpoint_success(mock_getenv, mock_openai, client, test_user, 
                                     sample_questionnaire, sample_llm_response):
    """Test successful mission draft generation via API."""
    # Mock environment variable
    mock_getenv.return_value = "fake-api-key"
    
    # Mock OpenAI client
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    
    # Mock completion response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps(sample_llm_response)
    mock_response.usage.prompt_tokens = 500
    mock_response.usage.completion_tokens = 300
    
    mock_client.chat.completions.create.return_value = mock_response
    
    # Make request
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    response = client.post("/missions/draft", json=sample_questionnaire, headers=headers)
    
    assert response.status_code == 201
    data = response.json()
    
    assert "draft" in data
    assert "generated_at" in data
    assert "model_used" in data
    assert data["draft"]["name"] == "Unbound 200 Preparation Mission"
    assert data["draft"]["mission_type"] == "gravel_ultra"


@patch('lanterne_rouge.backend.services.mission_builder.openai.OpenAI')
@patch('lanterne_rouge.backend.services.mission_builder.os.getenv')
def test_draft_endpoint_malformed_json_retry(mock_getenv, mock_openai, client, 
                                                    test_user, sample_questionnaire, 
                                                    sample_llm_response):
    """Test that malformed JSON triggers retry with temperature=0."""
    mock_getenv.return_value = "fake-api-key"
    
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    
    # First response: malformed JSON (with markdown)
    mock_response_1 = MagicMock()
    mock_response_1.choices = [MagicMock()]
    mock_response_1.choices[0].message.content = f"```json\n{json.dumps(sample_llm_response)}\n```"
    mock_response_1.usage.prompt_tokens = 500
    mock_response_1.usage.completion_tokens = 300
    
    # Second response: valid JSON
    mock_response_2 = MagicMock()
    mock_response_2.choices = [MagicMock()]
    mock_response_2.choices[0].message.content = json.dumps(sample_llm_response)
    mock_response_2.usage.prompt_tokens = 520
    mock_response_2.usage.completion_tokens = 300
    
    # Note: The first response with markdown should actually parse fine
    # Let's make the first one truly malformed
    mock_response_1.choices[0].message.content = "Here's your mission: " + json.dumps(sample_llm_response)
    
    mock_client.chat.completions.create.side_effect = [mock_response_1, mock_response_2]
    
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    response = client.post("/missions/draft", json=sample_questionnaire, headers=headers)
    
    # Should succeed on retry
    assert response.status_code == 201
    assert mock_client.chat.completions.create.call_count == 2


@patch('lanterne_rouge.backend.services.mission_builder.openai.OpenAI')
@patch('lanterne_rouge.backend.services.mission_builder.os.getenv')
def test_draft_endpoint_llm_failure(mock_getenv, mock_openai, client, test_user, 
                                         sample_questionnaire):
    """Test error handling when LLM fails."""
    mock_getenv.return_value = "fake-api-key"
    
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    
    # Mock API failure
    mock_client.chat.completions.create.side_effect = Exception("API Error")
    
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    response = client.post("/missions/draft", json=sample_questionnaire, headers=headers)
    
    # Should return 502 Bad Gateway
    assert response.status_code == 502
    assert "Failed to generate mission draft" in response.json()["detail"]


def test_draft_endpoint_unauthorized(client, sample_questionnaire):
    """Test that draft endpoint requires authentication."""
    response = client.post("/missions/draft", json=sample_questionnaire)
    # FastAPI returns 403 when authentication is required but not provided
    assert response.status_code == 403


def test_draft_endpoint_invalid_questionnaire(client, test_user):
    """Test that invalid questionnaire data is rejected."""
    invalid_data = {
        "event_name": "Test",
        # Missing required fields
    }
    
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    response = client.post("/missions/draft", json=invalid_data, headers=headers)
    assert response.status_code == 422  # Validation error


@patch('lanterne_rouge.backend.services.mission_builder.os.getenv')
def test_draft_endpoint_missing_api_key(mock_getenv, client, test_user, 
                                               sample_questionnaire):
    """Test error handling when OpenAI API key is not set."""
    mock_getenv.return_value = None
    
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    response = client.post("/missions/draft", json=sample_questionnaire, headers=headers)
    
    # Should return 502 due to configuration issue
    assert response.status_code == 502
    assert "OPENAI_API_KEY" in response.json()["detail"]
