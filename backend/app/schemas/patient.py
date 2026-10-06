"""Pydantic schemas for patient endpoints."""
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class PatientBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    dob: Optional[str] = None
    gender: Optional[str] = None
    contact: Optional[Dict[str, Any]] = None
    identifiers: Optional[Dict[str, Any]] = None
    medical_history: Optional[Dict[str, Any]] = None


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    contact: Optional[Dict[str, Any]] = None
    identifiers: Optional[Dict[str, Any]] = None
    medical_history: Optional[Dict[str, Any]] = None


class PatientResponse(PatientBase):
    id: int
    created_by: int

    model_config = ConfigDict(from_attributes=True)
