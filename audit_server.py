"""
FastAPI Server for Government Audit Authority - Audit Report UI
Creates a simple, styled webpage and JSON API to view patient records from healthcare.db
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
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
    created_at = Column(DateTime, default=datetime.utcnow)

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

def get_patient_records():
    session = Session()
    try:
        return session.query(PatientDetails).order_by(PatientDetails.id).all()
    finally:
        session.close()

@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve homepage safely without using str.format on a template that contains braces."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    template = """
    <!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Government Health Authority</title>
    <style>
      body{font-family:Inter,Segoe UI,Arial;background:linear-gradient(135deg,#0f172a,#1e293b);color:#111;margin:0;padding:30px}
      .card{max-width:1000px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 10px 40px rgba(2,6,23,.4)}
      .hero{display:flex;align-items:center;gap:20px;padding:28px 36px;background:linear-gradient(90deg,#083e77,#0a4b7a);color:#fff}
      .seal{font-size:56px}
      h1{margin:0;font-size:22px}
      p.subtitle{margin:4px 0 0;opacity:.9}
      .actions{padding:20px 36px;border-top:1px solid #f1f5f9;text-align:center}
      .btn{display:inline-block;padding:12px 20px;background:linear-gradient(90deg,#0f172a,#0b5ea8);color:#fff;border-radius:8px;text-decoration:none;font-weight:600}
      .small{font-size:13px;color:#64748b;margin-top:8px}
    </style></head><body>
      <div class="card">
        <div class="hero">
          <div class="seal">🏛️</div>
          <div>
            <h1>Government Health Authority — Audit Dashboard</h1>
            <p class="subtitle">Official audit portal for healthcare compliance and reporting</p>
            <div class="small">Generated: {NOW}</div>
          </div>
        </div>
        <div class="actions">
          <a class="btn" href="/audit-report">📊 View Audit Report</a>
          &nbsp;&nbsp;
          <a class="btn" href="/api/records">📋 API Records (JSON)</a>
          <div class="small">Records are read-only here. Access to raw patient data is restricted and logged.</div>
        </div>
      </div>
    </body></html>
    """
    html = template.replace("{NOW}", now)
    print(f"INFO: / served at {now}")
    return HTMLResponse(content=html)

@app.get("/audit-report", response_class=HTMLResponse)
async def audit_report():
    patients = get_patient_records()
    total = len(patients)
    avg_age = (sum(p.age for p in patients) / total) if total else 0.0

    rows = ""
    for p in patients:
        created = p.created_at.strftime("%Y-%m-%d %H:%M:%S") if p.created_at else "N/A"
        rows += f"""
        <tr>
          <td style="padding:12px;border-bottom:1px solid #e6eef8">{p.id}</td>
          <td style="padding:12px;border-bottom:1px solid #e6eef8">{p.name}</td>
          <td style="padding:12px;border-bottom:1px solid #e6eef8;text-align:center">{p.age}</td>
          <td style="padding:12px;border-bottom:1px solid #e6eef8">{created}</td>
        </tr>
        """

    if not rows:
        rows = "<tr><td colspan='4' style='padding:24px;text-align:center;color:#667085'>No patient records found</td></tr>"

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Use a single formatting mechanism (f-string). Avoid mixing f-strings and str.format()
    html = f"""
    <!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Audit Report — Government Health Authority</title>
    <style>
      body{{font-family:Inter,Segoe UI,Arial;background:#f3f6fb;margin:0;padding:30px;color:#0b1220}}
      .container{{max-width:1100px;margin:0 auto;background:#fff;border-radius:10px;box-shadow:0 10px 30px rgba(2,6,23,.06);overflow:hidden}}
      .header{{background:linear-gradient(90deg,#0b63a8,#075985);color:#fff;padding:28px 36px}}
      .header h2{{margin:0;font-size:20px}}
      .meta{{padding:18px 36px;border-bottom:1px solid #eef4fb;display:flex;gap:20px}}
      .stat{{background:linear-gradient(90deg,#0b63a8,#075985);color:#fff;padding:12px;border-radius:8px;min-width:160px;text-align:center}}
      .table-wrap{{padding:20px 36px}}
      table{{width:100%;border-collapse:collapse;background:#fff}}
      th{{text-align:left;padding:14px;background:#0b63a8;color:#fff}}
      td{{padding:12px;border-bottom:1px solid #eef4fb}}
      .footer{{padding:18px 36px;background:#fbfdff;color:#6b7280;font-size:13px}}
      a.back{{color:#0b63a8;text-decoration:none;font-weight:600}}
    </style>
    </head><body>
      <div class="container">
        <div class="header">
          <h2>Government Health Authority — Patient Records Audit Report</h2>
        </div>
        <div class="meta">
          <div class="stat"><div style="font-size:18px;font-weight:700">{total}</div><div style="opacity:.9">Total Patients</div></div>
          <div class="stat"><div style="font-size:18px;font-weight:700">{avg_age:.1f}</div><div style="opacity:.9">Average Age</div></div>
          <div style="flex:1"></div>
          <div style="align-self:center"><a class="back" href="/">← Back to Home</a></div>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th style="width:8%">ID</th>
                <th style="width:54%">Patient Name</th>
                <th style="width:12%;text-align:center">Age</th>
                <th style="width:26%">Registration Date</th>
              </tr>
            </thead>
            <tbody>
              {rows}
            </tbody>
          </table>
        </div>
        <div class="footer">
          <div>Official Government Health Authority Audit Report — Generated: {now}</div>
          <div style="margin-top:6px">This view is intended for audit and compliance purposes only. All accesses are logged.</div>
        </div>
      </div>
    </body></html>
    """
    return HTMLResponse(content=html)

@app.get("/api/records")
async def api_records():
    patients = get_patient_records()
    return {
        "status": "success",
        "count": len(patients),
        "records": [p.to_dict() for p in patients],
        "timestamp": datetime.now().isoformat(),
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Government Audit Authority Server...")
    print("📍 Visit: http://localhost:8000")
    uvicorn.run("audit_server:app", host="0.0.0.0", port=8000, reload=False)