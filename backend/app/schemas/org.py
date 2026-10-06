"""Pydantic schemas for organization endpoints."""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID


class OrgBase(BaseModel):
    name: str


class OrgCreate(OrgBase):
    pass


class OrgResponse(OrgBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
