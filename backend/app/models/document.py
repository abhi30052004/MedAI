import uuid
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    doc_type = Column(String, nullable=False) # lab_report, discharge_summary, etc
    storage_key = Column(String, nullable=False)
    status = Column(String, default="UPLOADED") # UPLOADED, PROCESSING, READY, FAILED
    error = Column(Text, nullable=True)
    page_count = Column(Integer, nullable=True)
    extracted_text = Column(Text, nullable=True)
    page_texts = Column(JSONB, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    organization = relationship("Organization", back_populates="documents")
    case = relationship("Case", back_populates="documents")
    extracted_items = relationship("ExtractedItem", back_populates="document", cascade="all, delete-orphan")
