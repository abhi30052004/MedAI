import uuid
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    dob = Column(String, nullable=True) # or Date
    gender = Column(String, nullable=True)
    contact = Column(JSONB, nullable=True)
    identifiers = Column(JSONB, nullable=True)
    medical_history = Column(JSONB, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    organization = relationship("Organization", back_populates="patients")
    cases = relationship("Case", back_populates="patient", cascade="all, delete-orphan")
