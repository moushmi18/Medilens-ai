"""Tests for authenticated report file/text preview endpoints."""
import io
import uuid
from pathlib import Path

import pytest
from docx import Document
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.database import Base, engine


@pytest.fixture(scope="module")
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)


def unique_email():
    return f"file_{uuid.uuid4().hex[:8]}@example.com"


def register(client, email=None):
    email = email or unique_email()
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "SecurePass123!", "full_name": "File User"},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def test_get_report_file_pdf(client):
    token = register(client)
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    upload = client.post(
        "/api/reports/upload",
        files={"file": ("preview.pdf", io.BytesIO(pdf_content), "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert upload.status_code == 201
    report_id = upload.json()["id"]

    response = client.get(
        f"/api/reports/{report_id}/file",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content.startswith(b"%PDF")


def test_get_report_file_image(client):
    token = register(client)
    img = Image.new("RGB", (40, 40), color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    upload = client.post(
        "/api/reports/upload",
        files={"file": ("scan.png", buf, "image/png")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert upload.status_code == 201
    report_id = upload.json()["id"]

    response = client.get(
        f"/api/reports/{report_id}/file",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert "image/png" in response.headers["content-type"]


def test_get_report_text_docx(client, tmp_path):
    token = register(client)
    doc = Document()
    doc.add_paragraph("Hemoglobin: 14.2 g/dL")
    path = tmp_path / "thyroid.docx"
    doc.save(path)

    upload = client.post(
        "/api/reports/upload",
        files={
            "file": (
                "thyroid.docx",
                path.read_bytes(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert upload.status_code == 201
    report_id = upload.json()["id"]

    response = client.get(
        f"/api/reports/{report_id}/text",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert "Hemoglobin" in response.text


def test_file_requires_auth(client):
    response = client.get(f"/api/reports/{uuid.uuid4()}/file")
    assert response.status_code == 401


def test_file_rejects_other_user(client):
    token_a = register(client)
    token_b = register(client)

    pdf_content = b"%PDF-1.4 private " + uuid.uuid4().bytes
    upload = client.post(
        "/api/reports/upload",
        files={"file": ("private.pdf", io.BytesIO(pdf_content), "application/pdf")},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    report_id = upload.json()["id"]

    response = client.get(
        f"/api/reports/{report_id}/file",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response.status_code in (403, 404)
