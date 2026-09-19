from sqlalchemy import or_
from schemas.lead import LeadDB

def apply_lead_filters(
    query,
    status: str | None = None,
    owner: str | None = None,
    country: str | None = None,
    q: str | None = None,
):
    if status:
        search_status = f"%{status}%"
        query = query.filter(LeadDB.lead_status.ilike(search_status))

    if owner:
        search_owner = f"%{owner}%"
        query = query.filter(LeadDB.contact_owner.ilike(search_owner))

    if country:
        query = query.filter(LeadDB.country.ilike(country))

    if q:
        search = f"%{q}%"

        query = query.filter(
            or_(
                LeadDB.resolved_name.ilike(search),
                LeadDB.company_name.ilike(search),
                LeadDB.email.ilike(search),
            )
        )

    return query