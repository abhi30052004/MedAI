from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.core.database import get_db
from app.api import deps
from app.models.user import User
from app.models.case import Case, CaseNote
from app.models.patient import Patient
from app.schemas.case import CaseResponse, CaseCreate, CaseUpdate, CaseNoteResponse, CaseNoteCreate, CaseReviewDecision
from app.services.audit_service import create_audit_log
from sqlalchemy import func, or_

router = APIRouter()

@router.get("/", response_model=List[CaseResponse])
def read_cases(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
    skip: int = 0,
    limit: int = 100
):
    query = db.query(Case).filter(Case.org_id == current_user.org_id, Case.archived == False)
    if current_user.role == "insurance_reviewer":
        query = query.filter(Case.assigned_insurance_reviewer == current_user.id)
    elif current_user.role == "doctor":
        query = query.filter(or_(Case.assigned_to == current_user.id, Case.created_by == current_user.id))
    cases = query.offset(skip).limit(limit).all()
    return cases

@router.post("/", response_model=CaseResponse)
def create_case(
    case_in: CaseCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.require_roles("admin", "doctor", "staff"))
):
    try:
        if case_in.patient_id:
            patient = db.query(Patient).filter(
                Patient.id == case_in.patient_id,
                Patient.org_id == current_user.org_id,
            ).first()
            if not patient:
                raise HTTPException(status_code=404, detail="Patient not found or not in your organization")
        else:
            patient_data = case_in.patient
            duplicate = db.query(Patient).filter(
                Patient.org_id == current_user.org_id,
                func.lower(Patient.first_name) == patient_data.first_name.strip().lower(),
                func.lower(Patient.last_name) == patient_data.last_name.strip().lower(),
                Patient.dob == patient_data.dob,
            ).first()
            if duplicate:
                raise HTTPException(
                    status_code=409,
                    detail={"message": "A similar patient already exists.", "patient_id": duplicate.id},
                )
            patient = Patient(
                first_name=patient_data.first_name.strip(),
                last_name=patient_data.last_name.strip(),
                dob=patient_data.dob,
                gender=patient_data.gender,
                contact=patient_data.contact,
                identifiers=patient_data.identifiers,
                medical_history=patient_data.medical_history,
                org_id=current_user.org_id,
                created_by=current_user.id,
            )
            db.add(patient)
            db.flush()

        def validate_assignee(user_id, role, label):
            if user_id is None:
                return
            user = db.query(User).filter(
                User.id == user_id,
                User.org_id == current_user.org_id,
                User.role == role,
                User.is_active == True,
            ).first()
            if not user:
                raise HTTPException(status_code=422, detail=f"Selected {label} is not available in your organization")

        validate_assignee(case_in.assigned_to, "doctor", "doctor")
        reviewer_id = case_in.assigned_insurance_reviewer if case_in.insurance_available else None
        validate_assignee(reviewer_id, "insurance_reviewer", "insurance reviewer")

        db_case = Case(
            title=case_in.title.strip(),
            patient_id=patient.id,
            status="NEW",
            symptoms=case_in.symptoms,
            diagnoses=case_in.diagnoses,
            previous_treatments=case_in.previous_treatments,
            assigned_to=case_in.assigned_to,
            insurance_available=case_in.insurance_available,
            insurance_provider=case_in.insurance_provider if case_in.insurance_available else None,
            insurance_number=case_in.insurance_number if case_in.insurance_available else None,
            assigned_insurance_reviewer=reviewer_id,
            insurance_review_status="PENDING" if case_in.insurance_available else "NOT_REQUIRED",
            org_id=current_user.org_id,
            created_by=current_user.id,
        )
        db.add(db_case)
        db.flush()

        if case_in.additional_notes and case_in.additional_notes.strip():
            db.add(CaseNote(
                case_id=db_case.id,
                org_id=current_user.org_id,
                author_id=current_user.id,
                text=case_in.additional_notes.strip(),
            ))

        create_audit_log(
            db, user=current_user, action="CASE_CREATED", entity="case",
            entity_id=db_case.id, request=request, commit=False,
            metadata={"patient_id": patient.id},
        )
        db.commit()
        db.refresh(db_case)
        return db_case
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Unable to create the case. Please try again.")

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
    if current_user.role == "insurance_reviewer" and db_case.assigned_insurance_reviewer != current_user.id:
        raise HTTPException(status_code=404, detail="Case not found")
    if current_user.role == "doctor" and db_case.assigned_to != current_user.id and db_case.created_by != current_user.id:
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
    protected = {"status", "doctor_review_status", "insurance_review_status"}
    if protected.intersection(update_data):
        raise HTTPException(status_code=403, detail="Use the case review workflow for status and approvals")
    for field, value in update_data.items():
        setattr(db_case, field, value)
        
    db_case.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_case)
    
    create_audit_log(db, user=current_user, action="CASE_UPDATED", entity="case", entity_id=db_case.id, request=request)
    
    return db_case


@router.post("/{case_id}/review", response_model=CaseResponse)
def review_case(
    case_id: int,
    review: CaseReviewDecision,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    db_case = db.query(Case).filter(Case.id == case_id, Case.org_id == current_user.org_id).first()
    if not db_case:
        raise HTTPException(status_code=404, detail="Case not found")
    if db_case.status not in ("UNDER_REVIEW", "COMPLETED"):
        raise HTTPException(status_code=409, detail="The case is not ready for review")

    if current_user.role == "doctor":
        if db_case.assigned_to and db_case.assigned_to != current_user.id:
            raise HTTPException(status_code=403, detail="This case is assigned to another doctor")
        db_case.doctor_review_status = review.decision
        db_case.doctor_review_reason = review.reason.strip() if review.reason else None
        action = f"DOCTOR_REVIEW_{review.decision}"
    elif current_user.role == "insurance_reviewer":
        if not db_case.insurance_available:
            raise HTTPException(status_code=409, detail="Insurance review is not required")
        if db_case.assigned_insurance_reviewer != current_user.id:
            raise HTTPException(status_code=403, detail="This case is not assigned to you")
        db_case.insurance_review_status = review.decision
        db_case.insurance_review_reason = review.reason.strip() if review.reason else None
        action = f"INSURANCE_REVIEW_{review.decision}"
    else:
        raise HTTPException(status_code=403, detail="Only the assigned doctor or insurance reviewer may review a case")

    if (
        db_case.doctor_review_status == "APPROVED"
        and db_case.insurance_review_status in ("APPROVED", "NOT_REQUIRED")
    ):
        db_case.status = "COMPLETED"
    elif db_case.status == "COMPLETED":
        db_case.status = "UNDER_REVIEW"

    create_audit_log(
        db, user=current_user, action=action, entity="case", entity_id=db_case.id,
        request=request, commit=False,
    )
    db.commit()
    db.refresh(db_case)
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
