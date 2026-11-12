"""Tests for user settings / preferences API."""
import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, engine


@pytest.fixture(scope="module")
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)


def unique_email():
    return f"settings_{uuid.uuid4().hex[:8]}@example.com"


def auth_headers(client):
    email = unique_email()
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "SecurePass123!", "full_name": "Settings User"},
    )
    assert response.status_code == 201
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_get_settings_defaults(client):
    headers = auth_headers(client)
    response = client.get("/api/settings", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["preferences"]["email_notifications"] is True
    assert data["preferences"]["processing_alerts"] is True
    assert data["preferences"]["show_confidence"] is True
    assert data["preferences"]["auto_process"] is False
    assert data["retention_days"] == 365


def test_update_settings_persists(client):
    headers = auth_headers(client)
    response = client.put(
        "/api/settings",
        headers=headers,
        json={
            "email_notifications": False,
            "processing_alerts": False,
            "show_confidence": False,
            "auto_process": True,
        },
    )
    assert response.status_code == 200
    prefs = response.json()["preferences"]
    assert prefs["email_notifications"] is False
    assert prefs["processing_alerts"] is False
    assert prefs["show_confidence"] is False
    assert prefs["auto_process"] is True

    reload = client.get("/api/settings", headers=headers)
    assert reload.status_code == 200
    prefs2 = reload.json()["preferences"]
    assert prefs2["email_notifications"] is False
    assert prefs2["auto_process"] is True


def test_settings_requires_auth(client):
    response = client.get("/api/settings")
    assert response.status_code == 401
