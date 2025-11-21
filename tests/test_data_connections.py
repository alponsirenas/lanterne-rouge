"""Tests for data connections API."""
import json
from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import MagicMock, patch
from zipfile import ZipFile

import pytest
from fastapi.testclient import TestClient

from lanterne_rouge.backend.db.session import SessionLocal
from lanterne_rouge.backend.main import app
from lanterne_rouge.backend.models.connection import DataConnection, StravaActivity, OuraData
from lanterne_rouge.backend.models.user import User
from lanterne_rouge.backend.core.security import get_password_hash
from lanterne_rouge.backend.services.encryption import get_encryption_service


@pytest.fixture(scope="function")
def test_db():
    """Create a test database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        # Clean up test data
        db.query(DataConnection).delete()
        db.query(StravaActivity).delete()
        db.query(OuraData).delete()
        db.commit()
        db.close()


@pytest.fixture
def test_user(test_db):
    """Create a test user."""
    user = test_db.query(User).filter(User.email == "testuser@example.com").first()
    if not user:
        user = User(
            email="testuser@example.com",
            hashed_password=get_password_hash("testpass123"),
            is_active=True
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Get authentication headers for test user."""
    client = TestClient(app)
    response = client.post(
        "/auth/login",
        json={"email": "testuser@example.com", "password": "testpass123"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_connections_status_empty(auth_headers):
    """Test getting connection status when no connections exist."""
    client = TestClient(app)
    response = client.get("/connections/status", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["strava"] is None
    assert data["oura"] is None
    assert data["apple_health"] is None


def test_strava_authorize(auth_headers):
    """Test initiating Strava OAuth flow."""
    client = TestClient(app)
    
    with patch.dict('os.environ', {'STRAVA_CLIENT_ID': '12345'}):
        response = client.post(
            "/connections/strava/authorize",
            json={"redirect_uri": "http://localhost:3000/callback"},
            headers=auth_headers
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "authorization_url" in data
    assert "strava.com/oauth/authorize" in data["authorization_url"]


@patch('lanterne_rouge.backend.services.data_connections.requests.post')
def test_strava_callback_success(mock_post, auth_headers, test_user, test_db):
    """Test successful Strava OAuth callback."""
    # Mock token exchange response
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "expires_at": 1234567890,
        "athlete": {"id": 12345}
    }
    
    client = TestClient(app)
    response = client.post(
        "/connections/strava/callback",
        json={
            "code": "test_auth_code",
            "scope": "read,activity:read_all"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Strava connected successfully"
    assert data["status"]["connection_type"] == "strava"
    assert data["status"]["status"] == "connected"
    
    # Verify connection was stored in database
    conn = test_db.query(DataConnection).filter(
        DataConnection.user_id == test_user.id,
        DataConnection.connection_type == "strava"
    ).first()
    assert conn is not None
    assert conn.status == "connected"
    assert conn.encrypted_credentials is not None


def test_strava_callback_invalid_code(auth_headers):
    """Test Strava callback with invalid authorization code."""
    client = TestClient(app)
    
    with patch('lanterne_rouge.backend.services.data_connections.requests.post') as mock_post:
        mock_post.return_value.status_code = 400
        mock_post.return_value.raise_for_status.side_effect = Exception("Invalid code")
        
        response = client.post(
            "/connections/strava/callback",
            json={
                "code": "invalid_code",
                "scope": "read,activity:read_all"
            },
            headers=auth_headers
        )
    
    assert response.status_code == 400


@patch('lanterne_rouge.backend.services.data_connections.requests.get')
def test_oura_connect_success(mock_get, auth_headers, test_user, test_db):
    """Test successful Oura connection with PAT."""
    # Mock token validation
    mock_get.return_value.status_code = 200
    
    client = TestClient(app)
    response = client.post(
        "/connections/oura/connect",
        json={"personal_access_token": "test_oura_token"},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Oura connected successfully"
    assert data["status"]["connection_type"] == "oura"
    assert data["status"]["status"] == "connected"
    
    # Verify connection was stored in database
    conn = test_db.query(DataConnection).filter(
        DataConnection.user_id == test_user.id,
        DataConnection.connection_type == "oura"
    ).first()
    assert conn is not None
    assert conn.status == "connected"
    
    # Verify credentials are encrypted
    encryption_service = get_encryption_service()
    decrypted = encryption_service.decrypt_credentials(conn.encrypted_credentials)
    assert decrypted["personal_access_token"] == "test_oura_token"


@patch('lanterne_rouge.backend.services.data_connections.requests.get')
def test_oura_connect_invalid_token(mock_get, auth_headers):
    """Test Oura connection with invalid PAT."""
    # Mock token validation failure
    mock_get.return_value.status_code = 401
    
    client = TestClient(app)
    response = client.post(
        "/connections/oura/connect",
        json={"personal_access_token": "invalid_token"},
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "Invalid Oura Personal Access Token" in response.json()["detail"]


def test_apple_health_upload_invalid_file(auth_headers):
    """Test Apple Health upload with invalid file type."""
    client = TestClient(app)
    
    # Create a fake file with wrong extension
    file_content = b"This is not a valid file"
    
    response = client.post(
        "/connections/apple-health/upload",
        files={"file": ("test.txt", file_content, "text/plain")},
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "ZIP or XML export" in response.json()["detail"]


def test_apple_health_upload_xml_success(auth_headers, test_user, test_db):
    """Test successful Apple Health XML upload."""
    client = TestClient(app)
    
    # Create a minimal valid Health export XML
    xml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
    <HealthData locale="en_US">
        <Record type="HKQuantityTypeIdentifierStepCount" value="5000" startDate="2025-01-01 12:00:00 +0000" />
        <Record type="HKQuantityTypeIdentifierDistanceWalkingRunning" value="3500.5" startDate="2025-01-01 12:00:00 +0000" />
    </HealthData>
    """
    
    response = client.post(
        "/connections/apple-health/upload",
        files={"file": ("export.xml", xml_content, "application/xml")},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Apple Health data uploaded successfully"
    assert data["records_processed"] >= 0
    assert "upload_batch_id" in data


def test_disconnect_success(auth_headers, test_user, test_db):
    """Test disconnecting a data source."""
    # First create a connection
    encryption_service = get_encryption_service()
    encrypted = encryption_service.encrypt_credentials({"token": "test"})
    
    conn = DataConnection(
        user_id=test_user.id,
        connection_type="strava",
        status="connected",
        encrypted_credentials=encrypted
    )
    test_db.add(conn)
    test_db.commit()
    
    # Now disconnect
    client = TestClient(app)
    response = client.post(
        "/connections/disconnect",
        json={"connection_type": "strava"},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "disconnected successfully" in data["message"].lower()
    
    # Verify connection was updated
    test_db.refresh(conn)
    assert conn.status == "disconnected"
    assert conn.encrypted_credentials is None


def test_disconnect_not_found(auth_headers):
    """Test disconnecting a non-existent connection."""
    client = TestClient(app)
    response = client.post(
        "/connections/disconnect",
        json={"connection_type": "strava"},
        headers=auth_headers
    )
    
    assert response.status_code == 404


def test_disconnect_invalid_type(auth_headers):
    """Test disconnecting with invalid connection type."""
    client = TestClient(app)
    response = client.post(
        "/connections/disconnect",
        json={"connection_type": "invalid"},
        headers=auth_headers
    )
    
    assert response.status_code == 400


@patch('lanterne_rouge.backend.services.data_connections.requests.get')
def test_refresh_strava_success(mock_get, auth_headers, test_user, test_db):
    """Test manual refresh of Strava data."""
    # Create a Strava connection
    encryption_service = get_encryption_service()
    credentials = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "expires_at": 9999999999,  # Far in the future
        "athlete_id": 12345
    }
    encrypted = encryption_service.encrypt_credentials(credentials)
    
    conn = DataConnection(
        user_id=test_user.id,
        connection_type="strava",
        status="connected",
        encrypted_credentials=encrypted
    )
    test_db.add(conn)
    test_db.commit()
    
    # Mock Strava API response
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = [
        {
            "id": 123456,
            "name": "Morning Ride",
            "type": "Ride",
            "start_date": "2025-01-01T08:00:00Z",
            "distance": 10000,
            "moving_time": 3600,
            "average_speed": 5.5
        }
    ]
    mock_get.return_value.raise_for_status = MagicMock()
    
    client = TestClient(app)
    response = client.post(
        "/connections/refresh",
        json={"connection_type": "strava"},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "Successfully refreshed" in data["message"]
    assert data["records_updated"] >= 0


def test_refresh_not_connected(auth_headers):
    """Test refresh when connection doesn't exist."""
    client = TestClient(app)
    response = client.post(
        "/connections/refresh",
        json={"connection_type": "strava"},
        headers=auth_headers
    )
    
    assert response.status_code == 400


def test_refresh_apple_health_not_supported(auth_headers, test_user, test_db):
    """Test that manual refresh is not supported for Apple Health."""
    # Create an Apple Health connection
    conn = DataConnection(
        user_id=test_user.id,
        connection_type="apple_health",
        status="connected"
    )
    test_db.add(conn)
    test_db.commit()
    
    client = TestClient(app)
    response = client.post(
        "/connections/refresh",
        json={"connection_type": "apple_health"},
        headers=auth_headers
    )
    
    assert response.status_code == 400


def test_encryption_service():
    """Test encryption service encrypts and decrypts correctly."""
    encryption_service = get_encryption_service()
    
    original = {
        "access_token": "secret_token_123",
        "refresh_token": "refresh_secret_456",
        "user_id": 789
    }
    
    # Encrypt
    encrypted = encryption_service.encrypt_credentials(original)
    assert encrypted != json.dumps(original)
    assert isinstance(encrypted, str)
    
    # Decrypt
    decrypted = encryption_service.decrypt_credentials(encrypted)
    assert decrypted == original


def test_encryption_service_redaction():
    """Test that encryption service properly redacts sensitive fields."""
    encryption_service = get_encryption_service()
    
    credentials = {
        "access_token": "very_secret_access_token",
        "refresh_token": "very_secret_refresh_token",
        "user_id": 123,
        "athlete_id": 456
    }
    
    redacted = encryption_service.redact_for_logging(credentials)
    
    # Sensitive fields should be redacted
    assert "very_secret_access_token" not in str(redacted["access_token"])
    assert "very_secret_refresh_token" not in str(redacted["refresh_token"])
    
    # Non-sensitive fields should remain
    assert redacted["user_id"] == 123
    assert redacted["athlete_id"] == 456


def test_connections_status_with_data(auth_headers, test_user, test_db):
    """Test getting connection status when connections exist."""
    # Create connections
    encryption_service = get_encryption_service()
    
    strava_conn = DataConnection(
        user_id=test_user.id,
        connection_type="strava",
        status="connected",
        encrypted_credentials=encryption_service.encrypt_credentials({"token": "test"}),
        last_refresh_at=datetime.now(timezone.utc),
        last_refresh_status="Success: 5 activities"
    )
    
    oura_conn = DataConnection(
        user_id=test_user.id,
        connection_type="oura",
        status="connected",
        encrypted_credentials=encryption_service.encrypt_credentials({"pat": "test"}),
        last_refresh_at=datetime.now(timezone.utc),
        last_refresh_status="Success: 10 records"
    )
    
    test_db.add_all([strava_conn, oura_conn])
    test_db.commit()
    
    client = TestClient(app)
    response = client.get("/connections/status", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["strava"] is not None
    assert data["strava"]["status"] == "connected"
    assert data["strava"]["last_refresh_status"] == "Success: 5 activities"
    
    assert data["oura"] is not None
    assert data["oura"]["status"] == "connected"
    assert data["oura"]["last_refresh_status"] == "Success: 10 records"
    
    assert data["apple_health"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
