"""Tests for report upload and management endpoints."""
import io
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


def get_auth_token(client):
    """Register a user and get auth token."""
    user_data = {
        "email": unique_email(),
        "password": "SecurePass123!",
        "full_name": "Test User",
    }
    response = client.post("/api/auth/register", json=user_data)
    return response.json()["access_token"]


def test_upload_pdf(client):
    """Test uploading a PDF file."""
    token = get_auth_token(client)
    
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    files = {"file": ("test_report.pdf", io.BytesIO(pdf_content), "application/pdf")}
    
    response = client.post(
        "/api/reports/upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["original_filename"] == "test_report.pdf"
    assert data["status"] == "uploaded"


def test_upload_image(client):
    """Test uploading an image file."""
    token = get_auth_token(client)
    
    from PIL import Image
    img = Image.new("RGB", (100, 100), color="white")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    
    files = {"file": ("test_image.png", img_bytes, "image/png")}
    
    response = client.post(
        "/api/reports/upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["original_filename"] == "test_image.png"


def test_upload_invalid_type(client):
    """Test uploading an invalid file type."""
    token = get_auth_token(client)
    
    files = {"file": ("test.exe", io.BytesIO(b"not a valid file"), "application/octet-stream")}
    
    response = client.post(
        "/api/reports/upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 422
    assert "not allowed" in response.json()["detail"].lower()


def test_upload_duplicate(client):
    """Test uploading a duplicate file."""
    token = get_auth_token(client)
    
    pdf_content = b"%PDF-1.4 unique content " + uuid.uuid4().bytes
    files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
    
    response1 = client.post(
        "/api/reports/upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response1.status_code == 201
    
    files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
    response2 = client.post(
        "/api/reports/upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response2.status_code == 422
    assert "already" in response2.json()["detail"].lower()


def test_list_reports(client):
    """Test listing reports."""
    token = get_auth_token(client)
    
    pdf_content = b"%PDF-1.4 list test " + uuid.uuid4().bytes
    files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
    client.post(
        "/api/reports/upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    
    response = client.get(
        "/api/reports",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) >= 1


def test_get_report(client):
    """Test getting a specific report."""
    token = get_auth_token(client)
    
    pdf_content = b"%PDF-1.4 get test " + uuid.uuid4().bytes
    files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
    upload_response = client.post(
        "/api/reports/upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    report_id = upload_response.json()["id"]
    
    response = client.get(
        f"/api/reports/{report_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == report_id


def test_get_report_not_found(client):
    """Test getting a non-existent report."""
    token = get_auth_token(client)
    fake_id = str(uuid.uuid4())
    
    response = client.get(
        f"/api/reports/{fake_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 404


def test_delete_report(client):
    """Test deleting a report."""
    token = get_auth_token(client)
    
    pdf_content = b"%PDF-1.4 delete test " + uuid.uuid4().bytes
    files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
    upload_response = client.post(
        "/api/reports/upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    report_id = upload_response.json()["id"]
    
    response = client.delete(
        f"/api/reports/{report_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 204
    
    get_response = client.get(
        f"/api/reports/{report_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_response.status_code == 404


def test_upload_without_auth(client):
    """Test uploading without authentication."""
    pdf_content = b"%PDF-1.4 no auth"
    files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
    
    response = client.post("/api/reports/upload", files=files)
    
    assert response.status_code == 401
