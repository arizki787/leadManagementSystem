from fastapi import FastAPI, Depends, HTTPException, status
from models.lead import Lead
from database import get_db
from sqlalchemy.orm import Session
from schemas.lead import LeadDB
from sqlalchemy import select, func
import io
from fastapi.responses import StreamingResponse
import pandas as pd
from helper.leads import apply_lead_filters 

app = FastAPI()

@app.get("/leads")
def get_leads(
    status: str | None = None,
    owner: str | None = None,
    country: str | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
):
    base_stmt = select(LeadDB)
    filtered_stmt = apply_lead_filters(base_stmt, status, owner, country, q)
    
    count_stmt = select(func.count()).select_from(filtered_stmt.subquery())
    total_count = db.scalar(count_stmt)

    results = db.scalars(filtered_stmt).all()
    
    return {"count": total_count, "res": results}
    # return {"res": results}

@app.get("/leads/export")
def export_leads(
    status: str | None = None,
    owner: str | None = None,
    country: str | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(LeadDB)
    stmt = apply_lead_filters(stmt, status, owner, country, q)

    df = pd.read_sql(stmt, db.bind)

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

    stream = io.StringIO()
    df.to_csv(stream, index=False)
    stream.seek(0)

    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="leads_export.csv"'},
    )

@app.get("/leads/{id}")
def get_lead_by_id(id: int, db: Session = Depends(get_db)):
    stmt = select(LeadDB).where(LeadDB.id == id)
    db_lead = db.scalars(stmt).first()

    if not db_lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Lead not found"
        )
    return db_lead


@app.patch("/leads/{id}")
def update_lead(id: int, lead_data: Lead, db: Session = Depends(get_db)):
    stmt = select(LeadDB).where(LeadDB.id == id)
    db_lead = db.scalars(stmt).first()

    if not db_lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Lead not found"
        )

    update_dict = lead_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(db_lead, field, value)

    try:
        db.commit()
        db.refresh(db_lead)
        return db_lead
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
