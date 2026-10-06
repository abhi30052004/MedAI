"""Pydantic schemas for document endpoints."""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID


class DocumentResponse(BaseModel):
    id: int
    org_id: UUID
    case_id: int
    filename: str
    mime_type: str
    size: int
    doc_type: str
    status: str
    error: Optional[str] = None
    page_count: Optional[int] = None
    uploaded_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentStatusResponse(BaseModel):
    id: int
    status: str
    error: Optional[str] = None
    page_count: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
