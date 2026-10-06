import pytest
import uuid
import json
import io
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.models.organization import Organization
from app.models.user import User
from app.models.patient import Patient
from app.models.case import Case
from app.models.document import Document
from app.models.extracted_item import ExtractedItem
from app.services.ai import ai_service
from app.ocr import extract_text_from_pdf, extract_text_from_image

from sqlalchemy.pool import StaticPool

# Let's use SQLite in-memory for fast and isolated tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Org A
    org_a = Organization(name="Test Org A")
    db.add(org_a)
    db.commit()
    
    # Org B (for cross-org testing)
    org_b = Organization(name="Test Org B")
    db.add(org_b)
    db.commit()

    # Admin User A
    admin_a = User(
        org_id=org_a.id, name="Admin A", email="admin_a@test.com",
        password_hash=get_password_hash("test1234"), role="admin",
        is_active=True, email_verified=True
    )
    db.add(admin_a)
    
    # Doctor User A
    doc_a = User(
        org_id=org_a.id, name="Doc A", email="doc_a@test.com",
        password_hash=get_password_hash("test1234"), role="doctor",
        is_active=True, email_verified=True
    )
    db.add(doc_a)

    # Reviewer User A
    rev_a = User(
        org_id=org_a.id, name="Rev A", email="rev_a@test.com",
        password_hash=get_password_hash("test1234"), role="insurance_reviewer",
        is_active=True, email_verified=True
    )
    db.add(rev_a)

    # Admin User B
    admin_b = User(
        org_id=org_b.id, name="Admin B", email="admin_b@test.com",
        password_hash=get_password_hash("test1234"), role="admin",
        is_active=True, email_verified=True
    )
    db.add(admin_b)
    
    db.commit()
    yield
    Base.metadata.drop_all(bind=engine)


def get_token(email: str):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "test1234"}
    )
    return response.json()["access_token"]


def test_auth_and_org_signup(setup_db):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "org_name": "New Signup Org",
            "admin_name": "New Admin",
            "admin_email": "new_admin@test.com",
            "admin_password": "newpassword123"
        }
    )
    assert response.status_code == 200
    
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "new_admin@test.com", "password": "newpassword123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "new_admin@test.com"
    assert me_response.json()["role"] == "admin"


def test_rbac_matrix_and_cross_org(setup_db):
    token_admin_a = get_token("admin_a@test.com")
    token_doc_a = get_token("doc_a@test.com")
    token_rev_a = get_token("rev_a@test.com")
    token_admin_b = get_token("admin_b@test.com")

    # 1. Admin A can create a patient
    res = client.post(
        "/api/v1/patients/",
        json={"first_name": "John", "last_name": "Doe"},
        headers={"Authorization": f"Bearer {token_admin_a}"}
    )
    assert res.status_code == 200
    patient_id = res.json()["id"]

    # 2. Doctor A can create a case
    res = client.post(
        "/api/v1/cases/",
        json={"title": "Test Case", "patient_id": patient_id},
        headers={"Authorization": f"Bearer {token_doc_a}"}
    )
    assert res.status_code == 200
    case_id = res.json()["id"]

    # 3. Reviewer A can view cases but CANNOT create
    res = client.get(
        "/api/v1/cases/",
        headers={"Authorization": f"Bearer {token_rev_a}"}
    )
    assert res.status_code == 200
    
    res = client.post(
        "/api/v1/cases/",
        json={"title": "Hacked Case", "patient_id": patient_id},
        headers={"Authorization": f"Bearer {token_rev_a}"}
    )
    assert res.status_code == 403 # RBAC works

    # 4. Admin B CANNOT view Admin A's cases (cross org isolation)
    res = client.get(
        f"/api/v1/cases/{case_id}",
        headers={"Authorization": f"Bearer {token_admin_b}"}
    )
    assert res.status_code == 404

    # 5. Audit log isolation (Admin A only sees Org A's logs)
    res = client.get(
        "/api/v1/audit-logs/",
        headers={"Authorization": f"Bearer {token_admin_a}"}
    )
    assert res.status_code == 200
    assert len(res.json()) > 0
    
    res = client.get(
        "/api/v1/audit-logs/",
        headers={"Authorization": f"Bearer {token_admin_b}"}
    )
    assert res.status_code == 200
    assert len(res.json()) == 0


def test_document_upload_validation(setup_db):
    token = get_token("doc_a@test.com")
    
    # We need a case
    res = client.get("/api/v1/cases/", headers={"Authorization": f"Bearer {token}"})
    case_id = res.json()[0]["id"]
    
    # Invalid extension
    invalid_file = io.BytesIO(b"fake exe content")
    res = client.post(
        f"/api/v1/cases/{case_id}/documents",
        files={"file": ("virus.exe", invalid_file, "application/x-msdownload")},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 400
    assert "File type not supported" in res.json()["detail"]


def test_llm_mock(setup_db):
    # Test our mock AI service fallback
    old_provider = ai_service.provider
    ai_service.provider = None
    try:
        result = ai_service.generate_analysis(1, "Patient has a headache.")
        assert result.confidence == "low"
        assert "Mock summary" in result.patient_summary
    finally:
        ai_service.provider = old_provider


def test_review_confirm_edit_reject(setup_db):
    db = TestingSessionLocal()
    org_a = db.query(Organization).filter(Organization.name == "Test Org A").first()
    
    patient = Patient(org_id=org_a.id, first_name="Test", last_name="Patient", created_by=1)
    db.add(patient)
    db.commit()
    
    case = Case(org_id=org_a.id, patient_id=patient.id, title="Test Case", status="NEW", created_by=1)
    db.add(case)
    db.commit()
    
    doc = Document(org_id=org_a.id, case_id=case.id, filename="x", mime_type="x", size=1, doc_type="x", storage_key="x", uploaded_by=1)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    item = ExtractedItem(org_id=org_a.id, case_id=case.id, document_id=doc.id, category="diagnosis", value="Fever", review_status="PENDING", ai_generated=True)
    db.add(item)
    db.commit()
    db.refresh(item)
    item_id = item.id
    db.close()

    token_doc = get_token("doc_a@test.com")
    
    # Edit
    res = client.patch(
        f"/api/v1/extracted-items/{item_id}",
        json={"action": "edit", "value": "High Fever"},
        headers={"Authorization": f"Bearer {token_doc}"}
    )
    assert res.status_code == 200
    assert res.json()["review_status"] == "EDITED"
    assert res.json()["value"] == "High Fever"
    assert res.json()["original_value"] == "Fever"

    # Confirm
    res = client.patch(
        f"/api/v1/extracted-items/{item_id}",
        json={"action": "confirm"},
        headers={"Authorization": f"Bearer {token_doc}"}
    )
    assert res.status_code == 200
    assert res.json()["review_status"] == "CONFIRMED"

    # Reject
    res = client.patch(
        f"/api/v1/extracted-items/{item_id}",
        json={"action": "reject"},
        headers={"Authorization": f"Bearer {token_doc}"}
    )
    assert res.status_code == 200
    assert res.json()["review_status"] == "REJECTED"

