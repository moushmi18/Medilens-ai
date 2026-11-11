"""Tests for authentication endpoints."""
import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal, Base, engine


@pytest.fixture(scope="module")
def client():
    """Create test client with fresh database."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)


def unique_email():
    """Generate unique email for testing."""
    return f"test_{uuid.uuid4().hex[:8]}@example.com"


def test_register_user(client):
    """Test user registration."""
    user_data = {
        "email": unique_email(),
        "password": "SecurePass123!",
        "full_name": "Test User",
    }
    response = client.post("/api/auth/register", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0


def test_register_duplicate_email(client):
    """Test registration with duplicate email fails."""
    email = unique_email()
    user_data = {
        "email": email,
        "password": "SecurePass123!",
        "full_name": "Test User",
    }
    client.post("/api/auth/register", json=user_data)
    response = client.post("/api/auth/register", json=user_data)
    assert response.status_code == 422
    assert "already registered" in response.json()["detail"].lower()


def test_login_success(client):
    """Test successful login."""
    user_data = {
        "email": unique_email(),
        "password": "SecurePass123!",
        "full_name": "Test User",
    }
    client.post("/api/auth/register", json=user_data)
    response = client.post("/api/auth/login", json={
        "email": user_data["email"],
        "password": user_data["password"],
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_login_wrong_password(client):
    """Test login with wrong password fails."""
    user_data = {
        "email": unique_email(),
        "password": "SecurePass123!",
        "full_name": "Test User",
    }
    client.post("/api/auth/register", json=user_data)
    response = client.post("/api/auth/login", json={
        "email": user_data["email"],
        "password": "WrongPassword123!",
    })
    assert response.status_code == 401


def test_login_nonexistent_user(client):
    """Test login with nonexistent user fails."""
    response = client.post("/api/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "SomePassword123!",
    })
    assert response.status_code == 401


def test_get_current_user(client):
    """Test getting current user with valid token."""
    user_data = {
        "email": unique_email(),
        "password": "SecurePass123!",
        "full_name": "Test User",
    }
    reg_response = client.post("/api/auth/register", json=user_data)
    assert reg_response.status_code == 201
    token = reg_response.json()["access_token"]
    
    response = client.get("/api/auth/me", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["full_name"] == user_data["full_name"]
    assert "id" in data
    assert "password" not in data
    assert "password_hash" not in data


def test_get_current_user_no_token(client):
    """Test getting current user without token fails."""
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_get_current_user_invalid_token(client):
    """Test getting current user with invalid token fails."""
    response = client.get("/api/auth/me", headers={
        "Authorization": "Bearer invalid_token"
    })
    assert response.status_code == 401


def test_refresh_token(client):
    """Test token refresh."""
    user_data = {
        "email": unique_email(),
        "password": "SecurePass123!",
        "full_name": "Test User",
    }
    reg_response = client.post("/api/auth/register", json=user_data)
    assert reg_response.status_code == 201
    refresh_token = reg_response.json()["refresh_token"]
    
    response = client.post("/api/auth/refresh", json={
        "refresh_token": refresh_token
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_refresh_token_invalid(client):
    """Test refresh with invalid token fails."""
    response = client.post("/api/auth/refresh", json={
        "refresh_token": "invalid_token"
    })
    assert response.status_code == 401


def test_logout(client):
    """Test logout."""
    user_data = {
        "email": unique_email(),
        "password": "SecurePass123!",
        "full_name": "Test User",
    }
    reg_response = client.post("/api/auth/register", json=user_data)
    assert reg_response.status_code == 201
    token = reg_response.json()["access_token"]
    
    response = client.post("/api/auth/logout", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 204
