"""Opt-in integration test for the configured PostgreSQL/Neon database.

The API commits normally inside a connection-owned outer transaction. The outer
transaction is rolled back at the end so live data is not polluted.
"""
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.api.deps import get_current_user
from app.core.database import engine, get_db
from app.main import app
from app.models.audit_log import AuditLog
from app.models.case import Case
from app.models.patient import Patient


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_LIVE_DB_TESTS") != "1",
    reason="Set RUN_LIVE_DB_TESTS=1 to test the configured PostgreSQL database",
)


def test_live_new_case_transactional_workflow():
    connection = engine.connect()
    outer_transaction = connection.begin()
    LiveSession = sessionmaker(bind=connection, join_transaction_mode="create_savepoint")

    def override_get_db():
        session = LiveSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    try:
        login = client.post(
            "/api/v1/auth/login",
            data={"username": "staff@test.com", "password": "Staff@12345"},
        )
        assert login.status_code == 200, login.text
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        doctor = client.get("/api/v1/users/?role=doctor&is_active=true", headers=headers).json()[0]
        reviewer = client.get("/api/v1/users/?role=insurance_reviewer&is_active=true", headers=headers).json()[0]

        uninsured = client.post(
            "/api/v1/cases/",
            json={
                "patient": {"first_name": "John", "last_name": "Doe", "dob": "1990-01-01"},
                "title": "General Consultation",
                "diagnoses": {"primary_condition": "Other"},
                "symptoms": {"reason_for_visit": "Headache"},
                "insurance_available": False,
                "assigned_to": doctor["id"],
            },
            headers=headers,
        )
        assert uninsured.status_code == 200, uninsured.text
        assert uninsured.json()["status"] == "NEW"
        assert uninsured.json()["insurance_provider"] is None

        insured = client.post(
            "/api/v1/cases/",
            json={
                "patient": {"first_name": "Jane", "last_name": "Smith", "dob": "1985-06-10"},
                "title": "Hypertension Follow-up",
                "insurance_available": True,
                "insurance_provider": "Example Provider",
                "insurance_number": "POL123456",
                "assigned_to": doctor["id"],
                "assigned_insurance_reviewer": reviewer["id"],
            },
            headers=headers,
        )
        assert insured.status_code == 200, insured.text
        jane_case = insured.json()
        assert jane_case["insurance_number"] == "POL123456"
        assert jane_case["assigned_insurance_reviewer"] == reviewer["id"]

        second_case = client.post(
            "/api/v1/cases/",
            json={
                "patient_id": jane_case["patient_id"],
                "title": "Jane Smith Second Case",
                "insurance_available": False,
            },
            headers=headers,
        )
        assert second_case.status_code == 200, second_case.text

        persisted = LiveSession()
        try:
            assert persisted.query(Patient).filter(Patient.id == jane_case["patient_id"]).one()
            assert persisted.query(Case).filter(Case.id == jane_case["id"]).one().status == "NEW"
            assert persisted.query(AuditLog).filter(
                AuditLog.action == "CASE_CREATED",
                AuditLog.entity_id == str(jane_case["id"]),
            ).one()
            assert persisted.query(Patient).filter(
                Patient.first_name == "Jane", Patient.last_name == "Smith", Patient.dob == "1985-06-10"
            ).count() == 1
        finally:
            persisted.close()
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)
        outer_transaction.rollback()
        connection.close()
