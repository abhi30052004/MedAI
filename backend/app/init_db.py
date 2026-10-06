import logging
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.models.organization import Organization
from app.models.patient import Patient
from app.models.case import Case
from app.models.document import Document
from app.models.audit import AuditLog
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
            role=UserRole.ADMIN.value,
            organization_id=org.id,
            is_active=True,
        )
        db.add(user)
        db.commit()
        logger.info("Created admin user: admin@medai.com / admin123")

def main() -> None:
    logger.info("Creating initial data")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    init_db(db)
    logger.info("Initial data created")

if __name__ == "__main__":
    main()
