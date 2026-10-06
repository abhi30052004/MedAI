"""Pydantic schemas for user endpoints."""
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str = "staff"
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class InviteRequest(BaseModel):
    email: EmailStr
    role: str = "staff"


class UserResponse(UserBase):
    id: int
    organization_id: UUID = Field(validation_alias="org_id")
    email_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
