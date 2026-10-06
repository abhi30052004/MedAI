"""Pydantic schemas for audit log endpoints."""
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from uuid import UUID


class AuditLogResponse(BaseModel):
    id: int
    org_id: UUID
    user_id: int
    action: str
    entity: str
    entity_id: str
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default=None, validation_alias="metadata_")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
