from datetime import date
from pydantic import BaseModel


class Lead(BaseModel):
    id: int
    fname: str | None = None
    lname: str | None = None
    fullname: str | None = None
    resolved_name: str | None = None
    job_title: str | None = None
    company_name: str | None = None
    email: str | None = None
    phone: str | None = None
    country: str | None = None
    city: str | None = None
    lead_status: str | None = None
    lifecycle_stage: str | None = None
    original_source: str | None = None
    original_source_drilldown: str | None = None
    contact_owner: str | None = None
    create_date: date | None = None
    last_modified_date: date | None = None
    notes: str | None = None
    annual_revenue: str | None = None
    marketing_contact_status: str | None = None
    gdpr_consent: str | None = None
    lead_score: int | None = None