from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.core.database import get_db
from app.api import deps
from app.models.user import User
from app.models.case import Case, CaseNote
from app.models.patient import Patient
from app.schemas.case import CaseResponse, CaseCreate, CaseUpdate, CaseNoteResponse, CaseNoteCreate
from app.services.audit_service import create_audit_log

router = APIRouter()

@router.get("/", response_model=List[CaseResponse])
def read_cases(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
    skip: int = 0,
    limit: int = 100
):
    cases = db.query(Case).filter(Case.org_id == current_user.org_id, Case.archived == False).offset(skip).limit(limit).all()
    return cases

@router.post("/", response_model=CaseResponse)
def create_case(
    case_in: CaseCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.require_roles("admin", "doctor", "staff"))
):
    patient = db.query(Patient).filter(Patient.id == case_in.patient_id, Patient.org_id == current_user.org_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found or not in your organization")

    db_case = Case(
        title=case_in.title,
        patient_id=case_in.patient_id,
        status=case_in.status,
        symptoms=case_in.symptoms,
        diagnoses=case_in.diagnoses,
        previous_treatments=case_in.previous_treatments,
        assigned_to=case_in.assigned_to,
        org_id=current_user.org_id,
        created_by=current_user.id
    )
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    
    create_audit_log(db, user=current_user, action="CASE_CREATED", entity="case", entity_id=db_case.id, request=request)
    
    return db_case

@router.get("/{case_id}", response_model=CaseResponse)
def read_case(
    case_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    db_case = db.query(Case).filter(Case.id == case_id).first()
    if not db_case or db_case.org_id != current_user.org_id:
        raise HTTPException(status_code=404, detail="Case not found")
        
    create_audit_log(db, user=current_user, action="CASE_VIEWED", entity="case", entity_id=db_case.id, request=request)
    return db_case

@router.patch("/{case_id}", response_model=CaseResponse)
def update_case(
    case_id: int,
    case_in: CaseUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.require_roles("admin", "doctor", "staff", "insurance_reviewer"))
):
    db_case = db.query(Case).filter(Case.id == case_id).first()
    if not db_case or db_case.org_id != current_user.org_id:
        raise HTTPException(status_code=404, detail="Case not found")
    
    update_data = case_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_case, field, value)
        
    db_case.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_case)
    
    create_audit_log(db, user=current_user, action="CASE_UPDATED", entity="case", entity_id=db_case.id, request=request)
    
    return db_case

@router.patch("/{case_id}/status", response_model=CaseResponse)
def update_case_status(
    case_id: int,
    status_update: dict,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.require_roles("admin", "doctor"))
):
    db_case = db.query(Case).filter(Case.id == case_id).first()
    if not db_case or db_case.org_id != current_user.org_id:
        raise HTTPException(status_code=404, detail="Case not found")
        
    db_case.status = status_update.get("status")
    db_case.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_case)
    
    create_audit_log(db, user=current_user, action="CASE_STATUS_UPDATED", entity="case", entity_id=db_case.id, request=request)
    return db_case

@router.post("/{case_id}/archive", response_model=CaseResponse)
def archive_case(
    case_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.require_roles("admin", "doctor"))
):
    db_case = db.query(Case).filter(Case.id == case_id).first()
    if not db_case or db_case.org_id != current_user.org_id:
        raise HTTPException(status_code=404, detail="Case not found")
        
    db_case.archived = True
    db_case.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_case)
    
    create_audit_log(db, user=current_user, action="CASE_ARCHIVED", entity="case", entity_id=db_case.id, request=request)
    return db_case

@router.get("/{case_id}/notes", response_model=List[CaseNoteResponse])
def get_case_notes(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case or case.org_id != current_user.org_id:
        raise HTTPException(status_code=404, detail="Case not found")
        
    notes = db.query(CaseNote).filter(CaseNote.case_id == case_id).order_by(CaseNote.created_at.asc()).all()
    return notes

@router.post("/{case_id}/notes", response_model=CaseNoteResponse)
def create_case_note(
    case_id: int,
    note_in: CaseNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.require_roles("admin", "doctor", "staff", "insurance_reviewer"))
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case or case.org_id != current_user.org_id:
        raise HTTPException(status_code=404, detail="Case not found")
        
    note = CaseNote(
        case_id=case_id,
        org_id=current_user.org_id,
        author_id=current_user.id,
        text=note_in.text
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note
