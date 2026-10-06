import uuid
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    status = Column(String, default="NEW") # NEW, DOCUMENTS_UPLOADED, UNDER_ANALYSIS, UNDER_REVIEW, COMPLETED
    symptoms = Column(JSONB, nullable=True)
    diagnoses = Column(JSONB, nullable=True)
    previous_treatments = Column(JSONB, nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    insurance_available = Column(Boolean, default=False, nullable=False)
    insurance_provider = Column(String, nullable=True)
    insurance_number = Column(String, nullable=True)
    assigned_insurance_reviewer = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    doctor_review_status = Column(String, default="PENDING")
    insurance_review_status = Column(String, default="PENDING")
    doctor_review_reason = Column(Text, nullable=True)
    insurance_review_reason = Column(Text, nullable=True)
    archived = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    organization = relationship("Organization", back_populates="cases")
    patient = relationship("Patient", back_populates="cases")
    documents = relationship("Document", back_populates="case", cascade="all, delete-orphan")
    extracted_items = relationship("ExtractedItem", back_populates="case", cascade="all, delete-orphan")
    summaries = relationship("CaseSummary", back_populates="case", cascade="all, delete-orphan")
    notes = relationship("CaseNote", back_populates="case", cascade="all, delete-orphan")

class CaseNote(Base):
    __tablename__ = "case_notes"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    case = relationship("Case", back_populates="notes")
    author = relationship("User")
