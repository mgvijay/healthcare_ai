import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from agent import PatientDetails # Import PatientDetails from agent.py for consistent model definition

# Import the FastAPI app from audit_server.py
from audit_server import app, Base

# Fixture for the TestClient
@pytest.fixture(scope="module")
def client():
    # Use the TestClient for FastAPI
    with TestClient(app) as c:
        yield c

# Fixture for a mock database session
@pytest.fixture(scope="function")
def mock_db_session():
    # Create an in-memory SQLite database for testing
    test_engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(test_engine) # Ensure tables are created on the test engine
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    # Patch the global Session in audit_server to use our test session
    with patch('audit_server.Session', TestSession):
        session = TestSession()
        yield session
        session.close()
        Base.metadata.drop_all(test_engine)

# Fixture for mock patient data
@pytest.fixture
def mock_patients():
    return [
        PatientDetails(name="Alice", age=30), # Removed created_at
        PatientDetails(name="Bob", age=25), # Removed created_at
    ]

# Test for the home page endpoint
def test_home(client, mock_db_session):
    response = client.get("/")
    assert response.status_code == 200
    assert "Government Health Authority — Audit Dashboard" in response.text
    assert "View Audit Report" in response.text
    assert "API Records (JSON)" in response.text

# Test for the /api/records endpoint with mock data
def test_api_records_with_data(client, mock_db_session, mock_patients):
    # Add mock patients to the test database
    mock_db_session.add_all(mock_patients)
    mock_db_session.commit()

    response = client.get("/api/records")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["count"] == 2
    assert len(data["records"]) == 2
    assert data["records"][0]["name"] == "Alice"
    assert data["records"][1]["age"] == 25

# Test for the /api/records endpoint with no data
def test_api_records_no_data(client, mock_db_session):
    response = client.get("/api/records")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["count"] == 0
    assert len(data["records"]) == 0

# Test for the /audit-report endpoint with mock data
def test_audit_report_with_data(client, mock_db_session, mock_patients):
    # Add mock patients to the test database
    mock_db_session.add_all(mock_patients)
    mock_db_session.commit()

    response = client.get("/audit-report")
    assert response.status_code == 200
    assert "Patient Records Audit Report" in response.text
    assert "Total Patients</div></div><div style=\"font-size:18px;font-weight:700\">2</div>" in response.text
    assert "Average Age</div></div><div style=\"font-size:18px;font-weight:700\">27.5</div>" in response.text
    assert "Alice" in response.text
    assert "Bob" in response.text

# Test for the /audit-report endpoint with no data
def test_audit_report_no_data(client, mock_db_session):
    response = client.get("/audit-report")
    assert response.status_code == 200
    assert "No patient records found" in response.text
    assert "Total Patients</div></div><div style=\"font-size:18px;font-weight:700\">0</div>" in response.text
    assert "Average Age</div></div><div style=\"font-size:18px;font-weight:700\">0.0</div>" in response.text
