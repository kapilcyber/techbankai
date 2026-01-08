from sqlalchemy import delete
from src.models.resume import Resume, Experience, Certification

async def save_structured_resume_data(db, resume_id, parsed_data, clear_existing=False):
    """
    Extracts and saves structured Experience and Certification records 
    from parsed_data JSON into dedicated tables.
    """
    try:
        if clear_existing:
            await db.execute(delete(Experience).where(Experience.resume_id == resume_id))
            await db.execute(delete(Certification).where(Certification.resume_id == resume_id))

        # 1. Save Certifications
        certs = parsed_data.get("resume_certificates", [])
        for cert_name in certs:
            if cert_name and cert_name != "Not mentioned":
                new_cert = Certification(
                    resume_id=resume_id,
                    name=cert_name,
                    issuer="Detected"
                )
                db.add(new_cert)

        # 2. Save Experience (Initial implementation from primary role)
        # In a more advanced version, we would iterate through a list of past jobs
        role = parsed_data.get("resume_role") or parsed_data.get("role")
        if role and role != "Not mentioned":
            new_exp = Experience(
                resume_id=resume_id,
                role=role,
                company=parsed_data.get("resume_company") or "Detected",
                description=parsed_data.get("resume_summary") or ""
            )
            db.add(new_exp)
            
        return True
    except Exception as e:
        print(f"Error saving structured data: {e}")
        return False
