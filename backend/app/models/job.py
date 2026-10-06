import uuid
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    type = Column(String, nullable=False) # DOCUMENT_PROCESSING, CASE_ANALYSIS
    payload = Column(JSONB, nullable=False)
    status = Column(String, default="QUEUED") # QUEUED, RUNNING, DONE, FAILED
    attempts = Column(Integer, default=0)
    error = Column(Text, nullable=True)
    locked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    finished_at = Column(DateTime(timezone=True), nullable=True)

    organization = relationship("Organization", back_populates="jobs")
