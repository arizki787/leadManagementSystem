from collections import defaultdict
import csv
import itertools
from pathlib import Path

from rapidfuzz import fuzz
from sqlalchemy import select, text

from database import session
from models.lead import Lead
from schemas.lead import LeadDB


def get_lead(id, db):
    stmt = select(LeadDB).where(LeadDB.id == id)
    result = db.execute(stmt).scalar_one_or_none()

    if result is None:
        return None

    return Lead.model_validate(result)


def get_duplicate_phone(db):
    duplicate_phone_dict = defaultdict(list)

    stmt = select(LeadDB.id, LeadDB.phone)
    rows = db.execute(stmt).all()

    for lead_id, phone in rows:
        if phone:
            duplicate_phone_dict[phone].append(lead_id)

    return duplicate_phone_dict


def get_candidate_pairs(db):
    pairs = set()

    # Block A: same phone
    by_phone = get_duplicate_phone(db)
    for ids in by_phone.values():
        if len(ids) > 1:
            pairs.update(itertools.combinations(sorted(ids), 2))

    # Block B: same email
    rows = db.execute(
        text("""
            SELECT id, LOWER(TRIM(COALESCE(email, ''))) AS e
            FROM leads
        """)
    ).all()

    by_email = defaultdict(list)
    for lead_id, email in rows:
        if email:
            by_email[email].append(lead_id)

    for ids in by_email.values():
        if len(ids) > 1:
            pairs.update(itertools.combinations(sorted(ids), 2))

    # Block C: same normalized name + normalized company
    rows = db.execute(
        text("""
            SELECT id, resolved_name, company_name
            FROM leads
        """)
    ).all()

    by_namecompany = defaultdict(list)
    for lead_id, resolved_name, company_name in rows:
        key = (
            (resolved_name or "").strip().lower(),
            (company_name or "").strip().lower()
        )
        by_namecompany[key].append(lead_id)

    for ids in by_namecompany.values():
        if len(ids) > 1:
            pairs.update(itertools.combinations(sorted(ids), 2))

    return pairs


def score_pair(lead_a, lead_b):
    if lead_a is None or lead_b is None:
        return 0.0, ""

    a_phone = (lead_a.phone or "").strip()
    b_phone = (lead_b.phone or "").strip()
    a_email = (lead_a.email or "").strip().lower()
    b_email = (lead_b.email or "").strip().lower()
    a_name = (lead_a.resolved_name or "").strip()
    b_name = (lead_b.resolved_name or "").strip()
    a_company = (lead_a.company_name or "").strip()
    b_company = (lead_b.company_name or "").strip()

    same_phone = bool(a_phone and b_phone and a_phone == b_phone)
    same_email = bool(a_email and b_email and a_email == b_email)
    name_sim = fuzz.token_sort_ratio(a_name, b_name) / 100 if a_name and b_name else 0.0
    company_sim = fuzz.token_sort_ratio(a_company, b_company) / 100 if a_company and b_company else 0.0

    score = 0.35 * same_phone + 0.35 * same_email + 0.15 * name_sim + 0.15 * company_sim

    reasons = []
    if same_phone:
        reasons.append("same phone number")
    if same_email:
        reasons.append("same email")
    if name_sim > 0.8:
        reasons.append("very similar name")
    if company_sim > 0.8:
        reasons.append("very similar company")

    return score, "; ".join(reasons)


def dedupe_candidates(db):
    pairs = get_candidate_pairs(db)
    scored = []

    for id_a, id_b in pairs:
        lead_a = get_lead(id_a, db)
        lead_b = get_lead(id_b, db)

        if lead_a is None or lead_b is None:
            continue

        score, reason = score_pair(lead_a, lead_b)
        if score >= 0.3:
            scored.append({
                "leads": [id_a, id_b],
                "confidence": round(score, 2),
                "explanation": reason
            })

    scored.sort(key=lambda x: x["confidence"], reverse=True)
    return {"candidates": scored}


def export_candidates_csv(candidates, output_path):
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["lead_a", "lead_b", "confidence", "explanation"]

    with output_file.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for item in candidates:
            lead_a, lead_b = item["leads"]
            writer.writerow({
                "lead_a": lead_a,
                "lead_b": lead_b,
                "confidence": item["confidence"],
                "explanation": item["explanation"],
            })

    return str(output_file)


if __name__ == "__main__":
    db = session()
    res = dedupe_candidates(db)

    csv_path = export_candidates_csv(
        res["candidates"],
        Path(__file__).with_name("duplicate_candidates.csv")
    )

    print(f"Exported {len(res['candidates'])} duplicate candidate(s) to: {csv_path}")