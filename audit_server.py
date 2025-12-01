"""
FastAPI Server for Government Audit Authority - Audit Report UI
Creates a simple, styled webpage and JSON API to view patient records from healthcare.db
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func
from datetime import datetime
import os

# Database (same SQLite file used by agent.py)
DB_URL = "sqlite:///healthcare.db"
engine = create_engine(DB_URL, echo=False, connect_args={"check_same_thread": False})
Base = declarative_base()
Session = sessionmaker(bind=engine)

class PatientDetails(Base):
    __tablename__ = "patient_details"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

# Ensure table exists (no-op if already present)
Base.metadata.create_all(engine)

app = FastAPI(title="Government Health Audit Authority")

templates = Jinja2Templates(directory="templates")

def get_patient_records():
    """
    Retrieves all patient records from the database.

    Returns:
        A list of PatientDetails objects ordered by their ID.
    """
    session = Session()
    try:
        return session.query(PatientDetails).order_by(PatientDetails.id).all()
    finally:
        session.close()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Serves the home page of the audit server.

    This endpoint returns an HTML page with a welcome message and links to the audit report
    and the JSON API.

    Returns:
        An HTMLResponse containing the home page.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"INFO: / served at {now}")
    return templates.TemplateResponse(request, "index.html", {"NOW": now})

@app.get("/audit-report", response_class=HTMLResponse)
async def audit_report(request: Request):
    """
    Serves the audit report page.

    This endpoint retrieves all patient records from the database and displays them in a
    formatted HTML table. It also shows some basic statistics about the records.

    Returns:
        An HTMLResponse containing the audit report.
    """
    patients = get_patient_records()
    total = len(patients)
    avg_age = (sum(p.age for p in patients) / total) if total else 0.0

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return templates.TemplateResponse(request, "audit_report.html", {"patients": patients, "total": total, "avg_age": avg_age, "now": now})

@app.get("/api/records")
async def api_records():
    """
    Serves the patient records as a JSON API.

    This endpoint retrieves all patient records from the database and returns them in a
    JSON format, including the total count of records and a timestamp.

    Returns:
        A dictionary containing the patient records and metadata.
    """

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Government Audit Authority Server...")
    print("📍 Visit: http://localhost:8000")
    uvicorn.run("audit_server:app", host="0.0.0.0", port=8000, reload=False)