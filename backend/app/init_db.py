import logging
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.organization import Organization
from app.models.patient import Patient
from app.models.case import Case
from app.models.document import Document
from app.core.security import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db(db: Session) -> None:
    # Check if organization exists
    org = db.query(Organization).first()
    if not org:
        org = Organization(name="MedAI Default Org")
        db.add(org)
        db.commit()
        db.refresh(org)
        logger.info("Created default organization.")

    # Check if admin user exists
    user = db.query(User).filter(User.email == "admin@medai.com").first()
    if not user:
        user = User(
            email="admin@medai.com",
            password_hash=get_password_hash("admin123"),
            name="Admin User",
            role="admin",
            org_id=org.id,
            is_active=True,
        )
        db.add(user)
        db.commit()
        logger.info("Created admin user: admin@medai.com / admin123")

    # Check if doctor user exists
    doctor = db.query(User).filter(User.email == "doctor@medai.com").first()
    if not doctor:
        doctor = User(
            email="doctor@medai.com",
            password_hash=get_password_hash("doctor123"),
            name="Doctor User",
            role="doctor",
            org_id=org.id,
            is_active=True,
        )
        db.add(doctor)
        db.commit()
        logger.info("Created doctor user: doctor@medai.com / doctor123")

    # Check if insurance user exists
    insurance = db.query(User).filter(User.email == "insurance@medai.com").first()
    if not insurance:
        insurance = User(
            email="insurance@medai.com",
            password_hash=get_password_hash("insurance123"),
            name="Insurance User",
            role="insurance",
            org_id=org.id,
            is_active=True,
        )
        db.add(insurance)
        db.commit()
        logger.info("Created insurance user: insurance@medai.com / insurance123")

    # Check if staff user exists
    staff = db.query(User).filter(User.email == "staff@medai.com").first()
    if not staff:
        staff = User(
            email="staff@medai.com",
            password_hash=get_password_hash("staff123"),
            name="Staff User",
            role="staff",
            org_id=org.id,
            is_active=True,
        )
        db.add(staff)
        db.commit()
        logger.info("Created staff user: staff@medai.com / staff123")

def main() -> None:
    logger.info("Creating initial data")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    init_db(db)
    logger.info("Initial data created")

if __name__ == "__main__":
    main()
