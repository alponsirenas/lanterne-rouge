"""Tests for background job endpoints."""
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from lanterne_rouge.backend.core.security import get_password_hash
from lanterne_rouge.backend.db.session import get_db
from lanterne_rouge.backend.main import app
from lanterne_rouge.backend.models.mission import Mission, MissionState
from lanterne_rouge.backend.models.user import Base, User

# Test database
TEST_DATABASE_URL = "sqlite:///./test_jobs.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """Override database dependency for testing."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


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
def test_user(client):
    """Create a regular test user."""
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


def test_automatic_transition_training_to_event_active(client, test_admin):
    """Test automatic transition from TRAINING to EVENT_ACTIVE."""
    db = TestSessionLocal()
    
    # Create mission in TRAINING state with event start date as today
    today = date.today()
    mission = Mission(
        user_id=test_admin["user_id"],
        name="Test Mission",
        mission_type="TEST",
        state=MissionState.TRAINING.value,
        event_start_date=today,
        event_end_date=today + timedelta(days=10),
        points_schema={"test": "data"},
        timezone="UTC"
    )
    db.add(mission)
    db.commit()
    db.refresh(mission)
    mission_id = mission.id
    db.close()
    
    # Call the job endpoint
    headers = {"Authorization": f"Bearer {test_admin['token']}"}
    response = client.post("/jobs/check-mission-transitions", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["transitions_performed"] == 1
    assert len(data["transitions"]) == 1
    assert data["transitions"][0]["mission_id"] == mission_id
    assert data["transitions"][0]["old_state"] == "TRAINING"
    assert data["transitions"][0]["new_state"] == "EVENT_ACTIVE"
    
    # Verify mission state changed
    db = TestSessionLocal()
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    assert mission.state == MissionState.EVENT_ACTIVE.value
    db.close()


def test_automatic_transition_event_active_to_complete(client, test_admin):
    """Test automatic transition from EVENT_ACTIVE to MISSION_COMPLETE."""
    db = TestSessionLocal()
    
    # Create mission in EVENT_ACTIVE state with event end date in the past
    today = date.today()
    mission = Mission(
        user_id=test_admin["user_id"],
        name="Test Mission",
        mission_type="TEST",
        state=MissionState.EVENT_ACTIVE.value,
        event_start_date=today - timedelta(days=20),
        event_end_date=today - timedelta(days=1),
        points_schema={"test": "data"},
        timezone="UTC"
    )
    db.add(mission)
    db.commit()
    db.refresh(mission)
    mission_id = mission.id
    db.close()
    
    # Call the job endpoint
    headers = {"Authorization": f"Bearer {test_admin['token']}"}
    response = client.post("/jobs/check-mission-transitions", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["transitions_performed"] == 1
    assert len(data["transitions"]) == 1
    assert data["transitions"][0]["mission_id"] == mission_id
    assert data["transitions"][0]["old_state"] == "EVENT_ACTIVE"
    assert data["transitions"][0]["new_state"] == "MISSION_COMPLETE"
    
    # Verify mission state changed
    db = TestSessionLocal()
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    assert mission.state == MissionState.MISSION_COMPLETE.value
    db.close()


def test_automatic_transitions_multiple_missions(client, test_admin):
    """Test automatic transitions for multiple missions."""
    db = TestSessionLocal()
    
    today = date.today()
    
    # Create mission 1: TRAINING -> EVENT_ACTIVE
    mission1 = Mission(
        user_id=test_admin["user_id"],
        name="Mission 1",
        mission_type="TEST",
        state=MissionState.TRAINING.value,
        event_start_date=today,
        event_end_date=today + timedelta(days=10),
        points_schema={"test": "data"},
        timezone="UTC"
    )
    db.add(mission1)
    
    # Create mission 2: EVENT_ACTIVE -> MISSION_COMPLETE
    mission2 = Mission(
        user_id=test_admin["user_id"],
        name="Mission 2",
        mission_type="TEST",
        state=MissionState.EVENT_ACTIVE.value,
        event_start_date=today - timedelta(days=20),
        event_end_date=today - timedelta(days=1),
        points_schema={"test": "data"},
        timezone="UTC"
    )
    db.add(mission2)
    
    # Create mission 3: No transition (future event)
    mission3 = Mission(
        user_id=test_admin["user_id"],
        name="Mission 3",
        mission_type="TEST",
        state=MissionState.TRAINING.value,
        event_start_date=today + timedelta(days=30),
        event_end_date=today + timedelta(days=40),
        points_schema={"test": "data"},
        timezone="UTC"
    )
    db.add(mission3)
    
    db.commit()
    db.close()
    
    # Call the job endpoint
    headers = {"Authorization": f"Bearer {test_admin['token']}"}
    response = client.post("/jobs/check-mission-transitions", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["transitions_performed"] == 2


def test_automatic_transitions_no_transitions_needed(client, test_admin):
    """Test when no transitions are needed."""
    db = TestSessionLocal()
    
    today = date.today()
    
    # Create mission that doesn't need transition
    mission = Mission(
        user_id=test_admin["user_id"],
        name="Test Mission",
        mission_type="TEST",
        state=MissionState.TRAINING.value,
        event_start_date=today + timedelta(days=30),
        event_end_date=today + timedelta(days=40),
        points_schema={"test": "data"},
        timezone="UTC"
    )
    db.add(mission)
    db.commit()
    db.close()
    
    # Call the job endpoint
    headers = {"Authorization": f"Bearer {test_admin['token']}"}
    response = client.post("/jobs/check-mission-transitions", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["transitions_performed"] == 0
    assert len(data["transitions"]) == 0


def test_automatic_transitions_requires_admin(client, test_user):
    """Test that automatic transitions endpoint requires admin privileges."""
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    response = client.post("/jobs/check-mission-transitions", headers=headers)
    
    assert response.status_code == 403
