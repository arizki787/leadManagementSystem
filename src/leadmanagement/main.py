from fastapi import FastAPI, Depends
from models.lead import Lead
from database import engine, session
from sqlalchemy.orm import Session
from schemas.lead import LeadDB
from sqlalchemy import or_
import io
from fastapi.responses import StreamingResponse
import pandas as pd

app = FastAPI()

def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()

def apply_lead_filters(
    query,
    status: str | None = None,
    owner: str | None = None,
    country: str | None = None,
    q: str | None = None,
):
    if status:
        query = query.filter(Lead.status == status)

    if owner:
        query = query.filter(Lead.owner == owner)

    if country:
        query = query.filter(Lead.country == country)

    if q:
        search = f"%{q}%"

        query = query.filter(
            or_(
                Lead.resolved_name.ilike(search),
                Lead.company.ilike(search),
                Lead.email.ilike(search),
            )
        )

    return query

@app.get("/leads")
def get_leads(
    status: str | None = None,
    owner: str | None = None,
    country: str | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Lead)

    query = apply_lead_filters(
        query,
        status,
        owner,
        country,
        q,
    )

    return query.all()

@app.get("/leads/export")
def export_leads(
    status: str | None = None,
    owner: str | None = None,
    country: str | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Lead)
    query = apply_lead_filters(query, status, owner, country, q)

    # 1. Load SQLAlchemy query directly into a Pandas DataFrame
    df = pd.read_sql(query.statement, db.bind)

    # 2. Rename columns to match your exact export preference
    column_mapping = {
        "id": "ID",
        "fname": "First Name",
        "lname": "Last Name",
        "fullname": "Full Name",
        "resolved_name": "Resolved Name",
        "job_title": "Job Title",
        "company_name": "Company Name",
        "email": "Email",
        "phone": "Phone",
        "country": "Country",
        "city": "City",
        "lead_status": "Lead Status",
        "lifecycle_stage": "Lifecycle Stage",
        "original_source": "Original Source",
        "original_source_drilldown": "Original Source Drilldown",
        "contact_owner": "Contact Owner",
        "create_date": "Create Date",
        "last_modified_date": "Last Modified Date",
        "notes": "Notes",
        "annual_revenue": "Annual Revenue",
        "marketing_contact_status": "Marketing Contact Status",
        "gdpr_consent": "GDPR Consent",
        "lead_score": "Lead Score",
    }
    df = df.rename(columns=column_mapping)

    # 3. Write DataFrame to an in-memory string buffer
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    stream.seek(0)

    # 4. Return as downloadable file response
    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="leads_export.csv"'},
    )

@app.get("/leads/:id")
def get_lead_by_id(id:int, db: Session = Depends(get_db)):
    try:    
        db_lead = db.query(LeadDB).filter(LeadDB.id == id).first()
        return db_lead
    except Exception:
        return Exception

@app.patch("/leads/:id")
def update_leads(id:int, Lead: Lead, db: Session = Depends(get_db)):
    try:
        db_lead = db.query(LeadDB).filter(LeadDB.id == id).first()
        if db_lead:
            db_lead.fname = Lead.fname
            db_lead.lname = Lead.lname
            db_lead.fullname = Lead.fullname
            db_lead.resolved_name = Lead.resolved_name
            db_lead.job_title = Lead.job_title
            db_lead.company_name = Lead.company_name
            db_lead.email = Lead.email
            db_lead.phone = Lead.phone
            db_lead.country = Lead.country
            db_lead.city = Lead.city
            db_lead.lead_status = Lead.lead_status
            db_lead.lifecycle_stage = Lead.lifecycle_stage
            db_lead.original_source = Lead.original_source
            db_lead.original_source_drilldown = Lead.original_source_drilldown
            db_lead.contact_owner = Lead.contact_owner
            db_lead.create_date = Lead.create_date
            db_lead.last_modified_date = Lead.last_modified_date
            db_lead.notes = Lead.notes
            db_lead.annual_revenue = Lead.annual_revenue
            db_lead.marketing_contact_status = Lead.marketing_contact_status
            db_lead.gdpr_consent = Lead.gdpr_consent
            db_lead.lead_score = Lead.lead_score
            db.commit()
            return "Update Success"
        else:
            return "Update Failed No Lead Found"

    except Exception:
        return Exception
    

