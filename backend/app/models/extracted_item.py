import uuid
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Float, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class ExtractedItem(Base):
    __tablename__ = "extracted_items"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    category = Column(String, nullable=False) # diagnosis, procedure, medication, etc
    value = Column(String, nullable=False)
    details = Column(JSONB, nullable=True)
    source_page = Column(Integer, nullable=True)
    source_snippet = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    ai_generated = Column(Boolean, default=True)
    review_status = Column(String, default="PENDING") # PENDING, CONFIRMED, EDITED, REJECTED
    original_value = Column(String, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    organization = relationship("Organization", back_populates="extracted_items")
    case = relationship("Case", back_populates="extracted_items")
    document = relationship("Document", back_populates="extracted_items")
    reviewer = relationship("User")
