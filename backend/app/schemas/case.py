"""Pydantic schemas for case endpoints."""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class CaseBase(BaseModel):
    title: str
    patient_id: int
    status: str = "NEW"
    symptoms: Optional[Dict[str, Any]] = None
    diagnoses: Optional[Dict[str, Any]] = None
    previous_treatments: Optional[Dict[str, Any]] = None
    assigned_to: Optional[int] = None


class CaseCreate(CaseBase):
    pass


class CaseUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    symptoms: Optional[Dict[str, Any]] = None
    diagnoses: Optional[Dict[str, Any]] = None
    previous_treatments: Optional[Dict[str, Any]] = None
    assigned_to: Optional[int] = None
    doctor_review_status: Optional[str] = None
    insurance_review_status: Optional[str] = None
    archived: Optional[bool] = None


class CaseNoteCreate(BaseModel):
    text: str


class CaseNoteResponse(BaseModel):
    id: int
    case_id: int
    author_id: int
    text: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CaseResponse(CaseBase):
    id: int
    created_by: int
    doctor_review_status: Optional[str] = "PENDING"
    insurance_review_status: Optional[str] = "PENDING"
    archived: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
