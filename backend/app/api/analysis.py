from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api import deps
from app.models.user import User
from app.models.case import Case
from app.models.case_summary import CaseSummary
from app.models.extracted_item import ExtractedItem
from app.schemas.analysis import AnalysisStatusResponse, CaseSummaryResponse, ExtractedItemResponse, ExtractedItemReview
from app.workers.queue import enqueue_job
from app.services.audit_service import create_audit_log
from datetime import datetime, timezone

router = APIRouter()

@router.post("/cases/{case_id}/analyze")
def trigger_analysis(
    case_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.require_roles("admin", "doctor"))
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case or case.org_id != current_user.org_id:
        raise HTTPException(status_code=404, detail="Case not found")
        
    if case.status not in ["DOCUMENTS_UPLOADED", "COMPLETED"]:
        pass # Allow triggering anyway for MVP, but normally restrict
        
    enqueue_job(
        db=db,
        org_id=current_user.org_id,
        job_type="CASE_ANALYSIS",
        payload={"case_id": case.id}
    )
    
    create_audit_log(db, user=current_user, action="ANALYSIS_TRIGGERED", entity="case", entity_id=case.id, request=request)
    
    return {"message": "Analysis queued"}

@router.get("/cases/{case_id}/analysis", response_model=AnalysisStatusResponse)
def get_case_analysis_status(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case or case.org_id != current_user.org_id:
        raise HTTPException(status_code=404, detail="Case not found")
        
    # Get latest summary
    latest_summary = db.query(CaseSummary).filter(CaseSummary.case_id == case_id).order_by(CaseSummary.version.desc()).first()
    
    # Get counts
    total_items = db.query(ExtractedItem).filter(ExtractedItem.case_id == case_id).count()
    pending_items = db.query(ExtractedItem).filter(ExtractedItem.case_id == case_id, ExtractedItem.review_status == "PENDING").count()
    
    # Determine status
    status = "not_started"
    if case.status == "UNDER_ANALYSIS":
        status = "processing"
    elif case.status in ["UNDER_REVIEW", "COMPLETED"] and latest_summary:
        status = "completed"
        
    return {
        "status": status,
        "latest_summary": latest_summary,
        "extracted_items_count": total_items,
        "pending_review_count": pending_items
    }

@router.get("/cases/{case_id}/analysis/versions", response_model=List[CaseSummaryResponse])
def get_analysis_versions(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case or case.org_id != current_user.org_id:
        raise HTTPException(status_code=404, detail="Case not found")
        
    versions = db.query(CaseSummary).filter(CaseSummary.case_id == case_id).order_by(CaseSummary.version.desc()).all()
    return versions

@router.get("/cases/{case_id}/extracted-items", response_model=List[ExtractedItemResponse])
def get_extracted_items(
    case_id: int,
    category: Optional[str] = None,
    review_status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case or case.org_id != current_user.org_id:
        raise HTTPException(status_code=404, detail="Case not found")
        
    query = db.query(ExtractedItem).filter(ExtractedItem.case_id == case_id)
    if category:
        query = query.filter(ExtractedItem.category == category)
    if review_status:
        query = query.filter(ExtractedItem.review_status == review_status)
        
    return query.all()

@router.patch("/extracted-items/{item_id}", response_model=ExtractedItemResponse)
def review_extracted_item(
    item_id: int,
    review: ExtractedItemReview,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.require_roles("admin", "doctor", "insurance_reviewer"))
):
    item = db.query(ExtractedItem).filter(ExtractedItem.id == item_id).first()
    if not item or item.org_id != current_user.org_id:
        raise HTTPException(status_code=404, detail="Item not found")
        
    if review.action == "confirm":
        item.review_status = "CONFIRMED"
    elif review.action == "reject":
        item.review_status = "REJECTED"
    elif review.action == "edit":
        item.review_status = "EDITED"
        item.original_value = item.value
        item.value = review.value or item.value
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
        
    item.reviewed_by = current_user.id
    item.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(item)
    
    create_audit_log(db, user=current_user, action=f"ITEM_REVIEW_{review.action.upper()}", entity="extracted_item", entity_id=item.id, request=request)
    
    return item
