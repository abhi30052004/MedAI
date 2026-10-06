import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from app.core.database import get_db, SessionLocal
from app.api import deps
from app.models.user import User
from app.models.case import Case
from app.models.document import Document
from app.schemas.document import DocumentResponse, DocumentStatusResponse
from app.storage import storage_service
from app.workers.queue import enqueue_job
from app.workers.tasks import process_document
from app.services.audit_service import create_audit_log

def run_process_document(payload: dict):
    db = SessionLocal()
    try:
        process_document(db, payload)
    finally:
        db.close()
from app.core.config import settings

router = APIRouter()

# Mounted at /cases and /documents
# The spec maps:
# POST /cases/{id}/documents
# GET /cases/{id}/documents
# GET /documents/{id}
# GET /documents/{id}/file
# GET /documents/{id}/status

@router.get("/cases/{case_id}/documents", response_model=List[DocumentResponse])
def read_case_documents(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case or case.org_id != current_user.org_id:
        raise HTTPException(status_code=404, detail="Case not found")
        
    documents = db.query(Document).filter(Document.case_id == case_id).all()
    return documents

@router.post("/cases/{case_id}/documents", response_model=DocumentResponse)
def upload_document(
    case_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.require_roles("admin", "doctor", "staff"))
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case or case.org_id != current_user.org_id:
        raise HTTPException(status_code=404, detail="Case not found")

    # Read and save file
    file_bytes = file.file.read()
    size = len(file_bytes)
    if size > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds the {settings.MAX_UPLOAD_MB} MB limit")
    
    # Very basic validation
    ext = os.path.splitext(file.filename)[1].lower()
    allowed_exts = [".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".docx"]
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail="File type not supported")
        
    storage_key = storage_service.save(file_bytes, file.filename)
    
    doc = Document(
        org_id=current_user.org_id,
        case_id=case_id,
        filename=file.filename,
        mime_type=file.content_type or "application/octet-stream",
        size=size,
        doc_type="other",  # Could be passed in form data
        storage_key=storage_key,
        status="UPLOADED",
        uploaded_by=current_user.id
    )
    db.add(doc)
    if case.status == "NEW":
        case.status = "DOCUMENTS_UPLOADED"
    db.commit()
    db.refresh(doc)
    
    # Process document in background locally instead of remote DB queue
    background_tasks.add_task(
        run_process_document,
        {"document_id": doc.id, "requested_by": current_user.id}
    )
    
    create_audit_log(db, user=current_user, action="DOCUMENT_UPLOADED", entity="document", entity_id=doc.id, request=request)
    
    return doc

@router.get("/documents/{doc_id}", response_model=DocumentResponse)
def read_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc or doc.org_id != current_user.org_id:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.get("/documents/{doc_id}/status", response_model=DocumentStatusResponse)
def get_document_status(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc or doc.org_id != current_user.org_id:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.get("/documents/{doc_id}/file")
def download_document_file(
    doc_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc or doc.org_id != current_user.org_id:
        raise HTTPException(status_code=404, detail="Document not found")
        
    try:
        file_bytes = storage_service.read(doc.storage_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail="File could not be read")
        
    create_audit_log(db, user=current_user, action="DOCUMENT_DOWNLOADED", entity="document", entity_id=doc.id, request=request)
        
    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type=doc.mime_type,
        headers={"Content-Disposition": f"attachment; filename={doc.filename}"}
    )

@router.post("/documents/{doc_id}/retry")
def retry_document_processing(
    doc_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.require_roles("admin", "doctor", "staff"))
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc or doc.org_id != current_user.org_id:
        raise HTTPException(status_code=404, detail="Document not found")
        
    doc.status = "UPLOADED"
    doc.error = None
    db.commit()
    
    background_tasks.add_task(
        run_process_document,
        {"document_id": doc.id, "requested_by": current_user.id}
    )
    return {"message": "Document processing retried"}
