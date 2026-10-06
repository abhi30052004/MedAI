import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    users = relationship("User", back_populates="organization")
    patients = relationship("Patient", back_populates="organization")
    cases = relationship("Case", back_populates="organization")
    audit_logs = relationship("AuditLog", back_populates="organization")
    teams = relationship("Team", back_populates="organization")
    documents = relationship("Document", back_populates="organization")
    extracted_items = relationship("ExtractedItem", back_populates="organization")
    case_summaries = relationship("CaseSummary", back_populates="organization")
    jobs = relationship("Job", back_populates="organization")
