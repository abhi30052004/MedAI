"""Pydantic schemas for case endpoints."""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field, model_validator
from datetime import datetime
from app.schemas.patient import PatientCreate


class CaseBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    patient_id: int
    status: str = "NEW"
    symptoms: Optional[Dict[str, Any]] = None
    diagnoses: Optional[Dict[str, Any]] = None
    previous_treatments: Optional[Dict[str, Any]] = None
    assigned_to: Optional[int] = None
    insurance_available: bool = False
    insurance_provider: Optional[str] = None
    insurance_number: Optional[str] = None
    assigned_insurance_reviewer: Optional[int] = None


class CaseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    patient_id: Optional[int] = None
    patient: Optional[PatientCreate] = None
    symptoms: Optional[Dict[str, Any]] = None
    diagnoses: Optional[Dict[str, Any]] = None
    previous_treatments: Optional[Dict[str, Any]] = None
    additional_notes: Optional[str] = Field(default=None, max_length=10000)
    assigned_to: Optional[int] = None
    insurance_available: bool = False
    insurance_provider: Optional[str] = None
    insurance_number: Optional[str] = None
    assigned_insurance_reviewer: Optional[int] = None

    @model_validator(mode="after")
    def validate_case(self):
        if bool(self.patient_id) == bool(self.patient):
            raise ValueError("Provide either patient_id or patient")
        if self.patient and not self.patient.dob:
            raise ValueError("Date of birth is required for a new patient")
        if self.insurance_available and (not self.insurance_provider or not self.insurance_number):
            raise ValueError("Insurance provider and policy number are required")
        return self


class CaseUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    symptoms: Optional[Dict[str, Any]] = None
    diagnoses: Optional[Dict[str, Any]] = None
    previous_treatments: Optional[Dict[str, Any]] = None
    assigned_to: Optional[int] = None
    insurance_available: Optional[bool] = None
    insurance_provider: Optional[str] = None
    insurance_number: Optional[str] = None
    assigned_insurance_reviewer: Optional[int] = None
    doctor_review_status: Optional[str] = None
    insurance_review_status: Optional[str] = None
    archived: Optional[bool] = None


class CaseReviewDecision(BaseModel):
    decision: str
    reason: Optional[str] = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_decision(self):
        if self.decision not in ("APPROVED", "REJECTED"):
            raise ValueError("Decision must be APPROVED or REJECTED")
        if self.decision == "REJECTED" and not (self.reason and self.reason.strip()):
            raise ValueError("A rejection reason is required")
        return self


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
    doctor_review_reason: Optional[str] = None
    insurance_review_reason: Optional[str] = None
    archived: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
