"""Integration tests for mission API endpoints."""
from datetime import date, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from lanterne_rouge.backend.core.security import get_password_hash
from lanterne_rouge.backend.db.session import get_db
from lanterne_rouge.backend.main import app
from lanterne_rouge.backend.models.user import Base, User

# Test database
TEST_DATABASE_URL = "sqlite:///./test_missions.db"
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
def apply_mission_db_override():
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
    # Register user
    user_data = {
        "email": "testuser@example.com",
        "password": "testpassword123"
    }
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 201
    user_id = response.json()["id"]

    # Login to get token
    response = client.post("/auth/login", json=user_data)
    assert response.status_code == 200
    token_data = response.json()

    return {
        "email": user_data["email"],
        "token": token_data["access_token"],
        "user_id": user_id
    }


@pytest.fixture
def test_admin(client):
    """Create a test admin user and return user data with auth token."""
    # Create admin user directly in database
    db = TestSessionLocal()
    admin = User(
        email="admin@example.com",
        hashed_password=get_password_hash("adminpassword123"),
        is_active=True,
        is_admin=True
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    admin_id = admin.id
    db.close()

    # Login to get token
    response = client.post("/auth/login", json={
        "email": "admin@example.com",
        "password": "adminpassword123"
    })
    assert response.status_code == 200
    token_data = response.json()

    return {
        "email": "admin@example.com",
        "token": token_data["access_token"],
        "user_id": admin_id
    }


@pytest.fixture
def sample_mission_data():
    """Sample mission data for testing."""
    today = date.today()
    return {
        "name": "Tour de France Simulation 2025",
        "mission_type": "TDF_SIMULATION",
        "event_start_date": (today + timedelta(days=30)).isoformat(),
        "event_end_date": (today + timedelta(days=51)).isoformat(),
        "prep_start_date": today.isoformat(),
        "prep_end_date": (today + timedelta(days=29)).isoformat(),
        "points_schema": {
            "flat": {"gc": 5, "breakaway": 8},
            "mountain": {"gc": 6, "breakaway": 10},
            "itt": {"gc": 7, "breakaway": 9},
            "bonuses": {
                "consecutive_5": {"threshold": 5, "points": 5},
                "breakaway_10": {"threshold": 10, "points": 15}
            }
        },
        "timezone": "America/Los_Angeles",
        "constraints": {"max_daily_tss": 150},
        "notification_preferences": {"email": True, "sms": False}
    }


def test_create_mission(client, test_user, sample_mission_data):
    """Test creating a new mission."""
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    response = client.post("/missions", json=sample_mission_data, headers=headers)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == sample_mission_data["name"]
    assert data["mission_type"] == sample_mission_data["mission_type"]
    assert data["state"] == "PREP"
    assert "id" in data
    assert data["timezone"] == "America/Los_Angeles"


def test_create_mission_invalid_dates(client, test_user, sample_mission_data):
    """Test creating mission with invalid dates."""
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    # Event end before start
    invalid_data = sample_mission_data.copy()
    invalid_data["event_end_date"] = invalid_data["event_start_date"]
    response = client.post("/missions", json=invalid_data, headers=headers)
    assert response.status_code == 400


def test_create_mission_unauthorized(client, sample_mission_data):
    """Test creating mission without authentication."""
    response = client.post("/missions", json=sample_mission_data)
    assert response.status_code == 403  # No authorization header


def test_list_missions(client, test_user, sample_mission_data):
    """Test listing missions for current user."""
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    # Create two missions
    client.post("/missions", json=sample_mission_data, headers=headers)

    mission_data_2 = sample_mission_data.copy()
    mission_data_2["name"] = "Second Mission"
    client.post("/missions", json=mission_data_2, headers=headers)

    # List missions
    response = client.get("/missions", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == sample_mission_data["name"]
    assert data[1]["name"] == "Second Mission"


def test_get_mission(client, test_user, sample_mission_data):
    """Test getting a specific mission."""
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    # Create mission
    create_response = client.post("/missions", json=sample_mission_data, headers=headers)
    mission_id = create_response.json()["id"]

    # Get mission
    response = client.get(f"/missions/{mission_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == mission_id
    assert data["name"] == sample_mission_data["name"]


def test_get_mission_not_found(client, test_user):
    """Test getting a non-existent mission."""
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    fake_id = str(uuid4())

    response = client.get(f"/missions/{fake_id}", headers=headers)
    assert response.status_code == 404


def test_get_mission_unauthorized_access(client, test_user, sample_mission_data):
    """Test that users cannot access other users' missions."""
    # Create mission with first user
    headers1 = {"Authorization": f"Bearer {test_user['token']}"}
    create_response = client.post("/missions", json=sample_mission_data, headers=headers1)
    mission_id = create_response.json()["id"]

    # Create second user
    user2_data = {
        "email": "user2@example.com",
        "password": "password123"
    }
    client.post("/auth/register", json=user2_data)
    login_response = client.post("/auth/login", json=user2_data)
    token2 = login_response.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    # Try to access first user's mission
    response = client.get(f"/missions/{mission_id}", headers=headers2)
    assert response.status_code == 403


def test_update_mission(client, test_user, sample_mission_data):
    """Test updating a mission."""
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    # Create mission
    create_response = client.post("/missions", json=sample_mission_data, headers=headers)
    mission_id = create_response.json()["id"]

    # Update mission
    update_data = {
        "name": "Updated Mission Name",
        "timezone": "UTC"
    }
    response = client.put(f"/missions/{mission_id}", json=update_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Mission Name"
    assert data["timezone"] == "UTC"
    # Other fields should remain unchanged
    assert data["mission_type"] == sample_mission_data["mission_type"]


def test_delete_mission(client, test_user, sample_mission_data):
    """Test deleting a mission."""
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    # Create mission
    create_response = client.post("/missions", json=sample_mission_data, headers=headers)
    mission_id = create_response.json()["id"]

    # Delete mission
    response = client.delete(f"/missions/{mission_id}", headers=headers)
    assert response.status_code == 204

    # Verify it's deleted
    response = client.get(f"/missions/{mission_id}", headers=headers)
    assert response.status_code == 404


def test_transition_mission_prep_to_training(client, test_user, sample_mission_data):
    """Test transitioning mission from PREP to TRAINING."""
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    # Create mission
    create_response = client.post("/missions", json=sample_mission_data, headers=headers)
    mission_id = create_response.json()["id"]

    # Transition to TRAINING
    response = client.post(
        f"/missions/{mission_id}/transition",
        json={"target_state": "TRAINING"},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "TRAINING"


def test_transition_mission_invalid(client, test_user, sample_mission_data):
    """Test invalid mission transition."""
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    # Create mission (starts in PREP)
    create_response = client.post("/missions", json=sample_mission_data, headers=headers)
    mission_id = create_response.json()["id"]

    # Try to transition directly to EVENT_ACTIVE (not allowed from PREP)
    response = client.post(
        f"/missions/{mission_id}/transition",
        json={"target_state": "EVENT_ACTIVE"},
        headers=headers
    )
    assert response.status_code == 409  # Conflict


def test_transition_mission_same_state(client, test_user, sample_mission_data):
    """Test transitioning to same state."""
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    # Create mission
    create_response = client.post("/missions", json=sample_mission_data, headers=headers)
    mission_id = create_response.json()["id"]

    # Try to transition to PREP (already in PREP)
    response = client.post(
        f"/missions/{mission_id}/transition",
        json={"target_state": "PREP"},
        headers=headers
    )
    assert response.status_code == 409


def test_transition_mission_invalid_state(client, test_user, sample_mission_data):
    """Test transitioning to invalid state."""
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    # Create mission
    create_response = client.post("/missions", json=sample_mission_data, headers=headers)
    mission_id = create_response.json()["id"]

    # Try to transition to invalid state
    response = client.post(
        f"/missions/{mission_id}/transition",
        json={"target_state": "INVALID_STATE"},
        headers=headers
    )
    assert response.status_code == 400


def test_transition_training_to_prep_admin_only(client, test_user, test_admin, sample_mission_data):
    """Test that only admins can revert TRAINING to PREP."""
    # Create mission with regular user
    user_headers = {"Authorization": f"Bearer {test_user['token']}"}
    create_response = client.post("/missions", json=sample_mission_data, headers=user_headers)
    mission_id = create_response.json()["id"]

    # Transition to TRAINING
    client.post(
        f"/missions/{mission_id}/transition",
        json={"target_state": "TRAINING"},
        headers=user_headers
    )

    # Try to revert to PREP as regular user (should fail)
    response = client.post(
        f"/missions/{mission_id}/transition",
        json={"target_state": "PREP"},
        headers=user_headers
    )
    assert response.status_code == 409

    # Now create a mission for admin
    admin_headers = {"Authorization": f"Bearer {test_admin['token']}"}
    create_response = client.post("/missions", json=sample_mission_data, headers=admin_headers)
    admin_mission_id = create_response.json()["id"]

    # Transition to TRAINING
    client.post(
        f"/missions/{admin_mission_id}/transition",
        json={"target_state": "TRAINING"},
        headers=admin_headers
    )

    # Revert to PREP as admin (should succeed)
    response = client.post(
        f"/missions/{admin_mission_id}/transition",
        json={"target_state": "PREP"},
        headers=admin_headers
    )
    assert response.status_code == 200
    assert response.json()["state"] == "PREP"


def test_mission_state_flow(client, test_user, sample_mission_data):
    """Test complete mission state flow."""
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    # Create mission
    create_response = client.post("/missions", json=sample_mission_data, headers=headers)
    mission_id = create_response.json()["id"]
    assert create_response.json()["state"] == "PREP"

    # PREP -> TRAINING
    response = client.post(
        f"/missions/{mission_id}/transition",
        json={"target_state": "TRAINING"},
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["state"] == "TRAINING"

    # TRAINING -> EVENT_ACTIVE
    response = client.post(
        f"/missions/{mission_id}/transition",
        json={"target_state": "EVENT_ACTIVE"},
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["state"] == "EVENT_ACTIVE"

    # EVENT_ACTIVE -> MISSION_COMPLETE
    response = client.post(
        f"/missions/{mission_id}/transition",
        json={"target_state": "MISSION_COMPLETE"},
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["state"] == "MISSION_COMPLETE"

    # Cannot transition from MISSION_COMPLETE (terminal state)
    response = client.post(
        f"/missions/{mission_id}/transition",
        json={"target_state": "PREP"},
        headers=headers
    )
    assert response.status_code == 409
    """Verify non-admin users cannot trigger background job endpoint."""
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    response = client.post("/jobs/check-mission-transitions", headers=headers)
    assert response.status_code == 403


def test_jobs_endpoint_updates_states(client, test_user, test_admin, sample_mission_data):
    """Ensure job endpoint advances missions automatically."""
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    today = date.today()
    mission_payload = sample_mission_data.copy()
    mission_payload["event_start_date"] = (today - timedelta(days=1)).isoformat()
    mission_payload["event_end_date"] = (today + timedelta(days=1)).isoformat()
    mission_id = client.post("/missions", json=mission_payload, headers=headers).json()["id"]

    # Move to TRAINING so automatic transition can fire
    client.post(
        f"/missions/{mission_id}/transition",
        json={"target_state": "TRAINING"},
        headers=headers
    )

    admin_headers = {"Authorization": f"Bearer {test_admin['token']}"}
    job_response = client.post("/jobs/check-mission-transitions", headers=admin_headers)
    assert job_response.status_code == 200
    assert job_response.json()["transitions_performed"] >= 1

    mission_state = client.get(f"/missions/{mission_id}", headers=headers).json()["state"]
    assert mission_state == "EVENT_ACTIVE"

    # Create second mission to validate EVENT_ACTIVE -> MISSION_COMPLETE
    mission_payload2 = sample_mission_data.copy()
    mission_payload2["event_start_date"] = (today - timedelta(days=3)).isoformat()
    mission_payload2["event_end_date"] = (today - timedelta(days=1)).isoformat()
    mission_id2 = client.post("/missions", json=mission_payload2, headers=headers).json()["id"]

    # PREP -> TRAINING -> EVENT_ACTIVE (manual) so job can finish it
    client.post(
        f"/missions/{mission_id2}/transition",
        json={"target_state": "TRAINING"},
        headers=headers
    )
    client.post(
        f"/missions/{mission_id2}/transition",
        json={"target_state": "EVENT_ACTIVE"},
        headers=headers
    )

    job_response = client.post("/jobs/check-mission-transitions", headers=admin_headers)
    assert job_response.status_code == 200

    mission_state_2 = client.get(f"/missions/{mission_id2}", headers=headers).json()["state"]
    assert mission_state_2 == "MISSION_COMPLETE"
