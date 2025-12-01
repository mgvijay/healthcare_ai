import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import pytest
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from agent import Base, PatientDetails, insert_patient_record, get_all_patient_records, display_patient_records, get_patient_records_json

@pytest.fixture(scope="function")
def Session():
    """
    Fixture to create a new in-memory SQLite database for each test function.
    """
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    yield Session
    Base.metadata.drop_all(engine)


def test_insert_patient_record(Session):
    """
    Test case for the insert_patient_record function.
    """
    with patch('agent.Session', Session):
        # Insert a new patient record
        patient = insert_patient_record("John Doe", 30, 70.5)

        # Check if the patient record was inserted correctly
        assert patient is not None
        assert patient.name == "John Doe"
        assert patient.age == 30
        assert patient.weight == 70.5

        # Check if the patient record is in the database
        session = Session()
        db_patient = session.query(PatientDetails).filter_by(id=patient.id).first()
        assert db_patient is not None
        assert db_patient.name == "John Doe"
        assert db_patient.age == 30
        assert db_patient.weight == 70.5
        session.close()

def test_get_all_patient_records(Session):
    """
    Test case for the get_all_patient_records function.
    """
    with patch('agent.Session', Session):
        # Insert some patient records
        insert_patient_record("John Doe", 30, 70.5)
        insert_patient_record("Jane Doe", 25, 60.2)

        # Get all patient records
        patients = get_all_patient_records()

        # Check if the correct number of records were retrieved
        assert len(patients) == 2

        # Check if the records are correct
        assert patients[0].name == "John Doe"
        assert patients[1].name == "Jane Doe"

def test_display_patient_records(Session):
    """
    Test case for the display_patient_records function.
    """
    with patch('agent.Session', Session):
        # Insert some patient records
        insert_patient_record("John Doe", 30, 70.5)
        insert_patient_record("Jane Doe", 25, 60.2)

        # Get the formatted patient records
        records_str = display_patient_records()

        # Check if the output string contains the patient names
        assert "John Doe" in records_str
        assert "Jane Doe" in records_str

def test_get_patient_records_json(Session):
    """
    Test case for the get_patient_records_json function.
    """
    with patch('agent.Session', Session):
        # Insert some patient records
        insert_patient_record("John Doe", 30, 70.5)
        insert_patient_record("Jane Doe", 25, 60.2)

        # Get the patient records in JSON format
        records_json = get_patient_records_json()

        # Check if the count is correct
        assert records_json["count"] == 2

        # Check if the records are correct
        assert records_json["records"][0]["name"] == "John Doe"
        assert records_json["records"][1]["name"] == "Jane Doe"