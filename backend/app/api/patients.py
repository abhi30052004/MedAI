from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api import deps
from app.models.user import User
from app.models.patient import Patient
from app.schemas.patient import PatientResponse, PatientCreate, PatientUpdate

router = APIRouter()

@router.get("/", response_model=List[PatientResponse])
def read_patients(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
    skip: int = 0,
    limit: int = 100
):
    patients = db.query(Patient).filter(Patient.org_id == current_user.org_id).offset(skip).limit(limit).all()
    return patients

@router.post("/", response_model=PatientResponse)
def create_patient(
    patient_in: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.require_roles("admin", "doctor", "staff"))
):
    db_patient = Patient(
        first_name=patient_in.first_name,
        last_name=patient_in.last_name,
        dob=patient_in.dob,
        gender=patient_in.gender,
        contact=patient_in.contact,
        identifiers=patient_in.identifiers,
        medical_history=patient_in.medical_history,
        org_id=current_user.org_id,
        created_by=current_user.id
    )
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

@router.get("/{patient_id}", response_model=PatientResponse)
def read_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient or patient.org_id != current_user.org_id:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@router.put("/{patient_id}", response_model=PatientResponse)
def update_patient(
    patient_id: int,
    patient_in: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.require_roles("admin", "doctor", "staff"))
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient or patient.org_id != current_user.org_id:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    update_data = patient_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(patient, field, value)
        
    db.commit()
    db.refresh(patient)
    return patient
