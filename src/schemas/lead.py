from sqlalchemy import Column, Integer, String, Date, Text
from database import Base

class LeadDB(Base): 
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True)
    fname = Column(String)
    lname = Column(String)
    fullname = Column(String)
    resolved_name = Column(String)
    job_title = Column(String)
    company_name = Column(String)
    email = Column(String)
    phone = Column(String)
    country = Column(String)
    city = Column(String)
    lead_status = Column(String)
    lifecycle_stage = Column(String)
    original_source = Column(String)
    original_source_drilldown = Column(String)
    contact_owner = Column(String)
    create_date = Column(Date)
    last_modified_date = Column(Date)
    notes = Column(Text)
    annual_revenue = Column(String)
    marketing_contact_status = Column(String)
    gdpr_consent = Column(String)
    lead_score = Column(Integer)