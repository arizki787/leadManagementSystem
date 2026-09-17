from database import session, engine, Base
from datetime import datetime
from schemas.lead import LeadDB
import pandas as pd
import os


def clean_value(value):
    if value is None or pd.isna(value):
        return None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


def parse_date(date_str):
    date_str = clean_value(date_str)
    if not date_str:
        return None
    for fmt in ("%m/%d/%Y", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(date_str), fmt)
        except ValueError:
            continue
    return None


def parse_lead_status(value):
    value = clean_value(value)
    if value is None:
        return None

    status = {
        "closed lost": "Closed Lost",
        "closed won": "Closed Won",
        "connected": "Connected",
        "contacted": "Contacted",
        "new": "New",
        "opportunity": "Opportunity",
        "qualified": "Qualified",
    }

    key = str(value).lower().strip()
    if not key:
        return None
    return status.get(key, str(value).strip())


def parse_phone_number(value):
    value = clean_value(value)
    if value is None:
        return None

    clean_text = str(value).replace(" ", "").replace("-", "")
    if not clean_text:
        return None
    if clean_text[0] != "+":
        clean_text = "+" + clean_text
    return clean_text


def resolve_full_name(row):
    full_name = clean_value(row.get("Full Name"))
    if full_name:
        return full_name

    fname = clean_value(row.get("First Name")) or ""
    lname = clean_value(row.get("Last Name")) or ""
    return f"{fname} {lname}".strip() or None


def seed_leads(csv_file):
    Base.metadata.create_all(bind=engine)

    db = session()

    try:
        reader = pd.read_csv(csv_file)
        reader = reader.where(pd.notnull(reader), None)
        leads = []

        for _, row in reader.iterrows():
            row = {key: clean_value(value) for key, value in row.items()}

            lead = LeadDB(
                id=int(row["Record ID"]),
                fname=row.get("First Name"),
                lname=row.get("Last Name"),
                fullname=row.get("Full Name"),
                resolved_name=resolve_full_name(row),
                job_title=row.get("Job Title"),
                company_name=row.get("Company Name"),
                email=row.get("Email"),
                phone=parse_phone_number(row.get("Phone Number")),
                country=row.get("Country/Region"),
                city=row.get("City"),
                lead_status=parse_lead_status(row.get("Lead Status")),
                lifecycle_stage=row.get("Lifecycle Stage"),
                original_source=row.get("Original Source"),
                original_source_drilldown=row.get("Original Source Drill-Down 1"),
                contact_owner=row.get("Contact Owner"),
                create_date=parse_date(row.get("Create Date")),
                last_modified_date=parse_date(row.get("Last Modified Date")),
                notes=row.get("Notes"),
                annual_revenue=row.get("Annual Revenue"),
                marketing_contact_status=row.get("Marketing contact status"),
                gdpr_consent=row.get("GDPR consent"),
                lead_score=int(row["Lead Score"]) if row.get("Lead Score") is not None else None,
            )

            leads.append(lead)

        db.add_all(leads)
        db.commit()

        print(f"Successfully seeded {len(leads)} leads.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    print(os.getcwd())
    seed_leads("./data/leads_seed.csv")