import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.core.security import get_password_hash
from app.models.organization import Organization
from app.models.user import User
from app.models.team import Team, TeamMember

def seed_db(db: Session):
    print("Checking if admin organization exists...")
    admin_org = db.query(Organization).filter(Organization.name == "MedAI Demo Org").first()
    
    if not admin_org:
        print("Creating MedAI Demo Org...")
        admin_org = Organization(name="MedAI Demo Org")
        db.add(admin_org)
        db.commit()
        db.refresh(admin_org)
        print(f"Created Org: {admin_org.id}")

    users_to_create = [
        {"email": "admin@test.com", "name": "Admin User", "role": "admin", "password": "Admin@12345"},
        {"email": "doctor@test.com", "name": "Dr. John Smith", "role": "doctor", "password": "Doctor@12345"},
        {"email": "reviewer@test.com", "name": "Sarah Lee", "role": "insurance_reviewer", "password": "Reviewer@12345"},
        {"email": "staff@test.com", "name": "Mike Roy", "role": "staff", "password": "Staff@12345"},
    ]

    for user_data in users_to_create:
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        if not existing_user:
            print(f"Creating user {user_data['email']} ({user_data['role']})...")
            user = User(
                org_id=admin_org.id,
                name=user_data["name"],
                email=user_data["email"],
                role=user_data["role"],
                password_hash=get_password_hash(user_data["password"]),
                is_active=True,
                email_verified=True
            )
            db.add(user)
    
    db.commit()
    print("Seeding completed successfully.")

if __name__ == "__main__":
    print("Starting database seeding...")
    with SessionLocal() as db:
        seed_db(db)
