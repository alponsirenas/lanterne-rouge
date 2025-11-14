"""Tests for the backend API authentication endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from lanterne_rouge.backend.db.session import get_db
from lanterne_rouge.backend.main import app
from lanterne_rouge.backend.models.user import Base, User
from lanterne_rouge.backend.core.security import get_password_hash

# Test database
TEST_DATABASE_URL = "sqlite:///./test_lanterne.db"
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
    """Apply dependency override for this module only."""
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
    """Create a test user."""
    db = TestSessionLocal()
    user = User(
        email="testuser@example.com",
        hashed_password=get_password_hash("testpassword123"),
        is_active=True,
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return {"email": "testuser@example.com", "password": "testpassword123", "id": user.id}


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["version"] == "1.0.0"


def test_register_success(client):
    """Test successful user registration."""
    response = client.post(
        "/auth/register",
        json={"email": "newuser@example.com", "password": "strongpassword123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["is_active"] is True
    assert data["is_admin"] is False
    assert "id" in data
    assert "created_at" in data


def test_register_duplicate_email(client, test_user):
    """Test registration with duplicate email."""
    response = client.post(
        "/auth/register",
        json={"email": test_user["email"], "password": "anotherpassword123"},
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_register_invalid_password(client):
    """Test registration with invalid password (too short)."""
    response = client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "short"},
    )
    assert response.status_code == 422  # Validation error


def test_login_success(client, test_user):
    """Test successful login."""
    response = client.post(
        "/auth/login",
        json={"email": test_user["email"], "password": test_user["password"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_email(client):
    """Test login with invalid email."""
    response = client.post(
        "/auth/login",
        json={"email": "nonexistent@example.com", "password": "password123"},
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_invalid_password(client, test_user):
    """Test login with invalid password."""
    response = client.post(
        "/auth/login",
        json={"email": test_user["email"], "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_inactive_user(client):
    """Test login with inactive user."""
    db = TestSessionLocal()
    user = User(
        email="inactive@example.com",
        hashed_password=get_password_hash("password123"),
        is_active=False,
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.close()

    response = client.post(
        "/auth/login",
        json={"email": "inactive@example.com", "password": "password123"},
    )
    assert response.status_code == 403
    assert "inactive" in response.json()["detail"].lower()


def test_refresh_token_success(client, test_user):
    """Test successful token refresh."""
    # First, login to get tokens
    login_response = client.post(
        "/auth/login",
        json={"email": test_user["email"], "password": test_user["password"]},
    )
    assert login_response.status_code == 200
    refresh_token = login_response.json()["refresh_token"]

    # Now refresh the token
    response = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    # New tokens should be different
    assert data["refresh_token"] != refresh_token


def test_refresh_token_invalid(client):
    """Test refresh with invalid token."""
    response = client.post(
        "/auth/refresh",
        json={"refresh_token": "invalid_token_string"},
    )
    assert response.status_code == 401


def test_refresh_token_wrong_type(client, test_user):
    """Test refresh with access token instead of refresh token."""
    # First, login to get tokens
    login_response = client.post(
        "/auth/login",
        json={"email": test_user["email"], "password": test_user["password"]},
    )
    access_token = login_response.json()["access_token"]

    # Try to use access token for refresh
    response = client.post(
        "/auth/refresh",
        json={"refresh_token": access_token},
    )
    assert response.status_code == 401
    assert "Invalid token type" in response.json()["detail"]


def test_refresh_token_reuse(client, test_user):
    """Test that refresh token can only be used once."""
    # Login to get tokens
    login_response = client.post(
        "/auth/login",
        json={"email": test_user["email"], "password": test_user["password"]},
    )
    refresh_token = login_response.json()["refresh_token"]

    # First refresh should succeed
    first_refresh = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert first_refresh.status_code == 200

    # Second refresh with same token should fail
    second_refresh = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert second_refresh.status_code == 401


def test_admin_flag(client):
    """Test that admin flag is properly set."""
    # Create admin user
    db = TestSessionLocal()
    admin = User(
        email="admin@example.com",
        hashed_password=get_password_hash("adminpass123"),
        is_active=True,
        is_admin=True,
    )
    db.add(admin)
    db.commit()
    db.close()

    # Register endpoint should create non-admin users
    reg_response = client.post(
        "/auth/register",
        json={"email": "regular@example.com", "password": "regularpass123"},
    )
    assert reg_response.json()["is_admin"] is False

    # Verify admin user exists with admin flag
    # (would need protected endpoint to verify, but we can check in DB)
    db = TestSessionLocal()
    admin_user = db.query(User).filter(User.email == "admin@example.com").first()
    assert admin_user.is_admin is True
    db.close()
