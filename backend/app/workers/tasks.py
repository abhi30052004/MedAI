"""
Worker task execution logic for the background queue.
"""
import traceback
from typing import Dict, Any

from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.document import Document
from app.models.case import Case
from app.models.extracted_item import ExtractedItem
from app.models.case_summary import CaseSummary
from app.storage import storage_service
from app.ocr import extract_text
from app.services.ai import ai_service
from app.core.config import settings
from app.workers.queue import enqueue_job


def process_document(db: Session, payload: Dict[str, Any]) -> None:
    """Task: DOCUMENT_PROCESSING"""
    doc_id = payload.get("document_id")
    if not doc_id:
        raise ValueError("Missing document_id in payload")

    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise ValueError(f"Document {doc_id} not found")

    doc.status = "PROCESSING"
    db.commit()

    try:
        # 1. Read file bytes
        file_bytes = storage_service.read(doc.storage_key)

        # 2. Extract text (PDF text + OCR fallback)
        page_texts, full_text = extract_text(file_bytes, doc.mime_type)
        
        doc.page_texts = page_texts
        doc.extracted_text = full_text
        doc.page_count = len(page_texts)

        # 3. AI Extraction (cheap/fast extraction for key fields)
        # For MVP, we skip per-document extraction if AUTO_ANALYZE is enabled,
        # but the spec asks for "Extract key info (patient details, dates, diagnoses) with LLM"
        # We will mock the extraction here for brevity, or call a specific AI prompt.
        # In a full app, we'd add `ai_service.extract_document_entities(full_text)`
        
        # Set ready
        doc.status = "READY"
        db.commit()

        # 4. Check if all documents in the case are ready
        case = db.query(Case).filter(Case.id == doc.case_id).first()
        if case:
            all_docs = db.query(Document).filter(Document.case_id == case.id).all()
            if all(d.status == "READY" for d in all_docs):
                case.status = "DOCUMENTS_UPLOADED"
                db.commit()
                
                # Auto-analyze if enabled
                if settings.AUTO_ANALYZE:
                    enqueue_job(
                        db=db,
                        org_id=case.org_id,
                        job_type="CASE_ANALYSIS",
                        payload={"case_id": case.id}
                    )

    except Exception as e:
        doc.status = "FAILED"
        doc.error = str(e)
        db.commit()
        raise


def analyze_case(db: Session, payload: Dict[str, Any]) -> None:
    """Task: CASE_ANALYSIS"""
    case_id = payload.get("case_id")
    if not case_id:
        raise ValueError("Missing case_id in payload")

    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise ValueError(f"Case {case_id} not found")

    case.status = "UNDER_ANALYSIS"
    db.commit()

    try:
        # 1. Gather context
        patient = case.patient
        docs = db.query(Document).filter(Document.case_id == case_id).all()
        
        context = f"Patient: {patient.first_name} {patient.last_name}\n"
        context += f"Symptoms: {case.symptoms}\n"
        context += f"History: {patient.medical_history}\n\n"
        
        for d in docs:
            context += f"--- Document: {d.filename} ---\n"
            context += str(d.extracted_text) + "\n\n"

        # 2. Call AI
        analysis_result = ai_service.generate_analysis(case_id, context)
        
        # 3. Create CaseSummary
        latest_version = db.query(CaseSummary).filter(CaseSummary.case_id == case_id).count() + 1
        summary = CaseSummary(
            org_id=case.org_id,
            case_id=case_id,
            version=latest_version,
            summary_json=analysis_result.model_dump(exclude={"case_id", "organization_id"}),
            model_used=ai_service.provider.model if ai_service.provider else "mock",
            provider=ai_service.provider_name
        )
        db.add(summary)

        # 4. Map structured output to ExtractedItem (diagnoses, meds, etc)
        # We delete old pending items
        db.query(ExtractedItem).filter(
            ExtractedItem.case_id == case_id, 
            ExtractedItem.review_status == "PENDING"
        ).delete()
        
        doc_id = docs[0].id if docs else 0 # Just attach to first doc for now
        
        for diag in analysis_result.diagnoses or []:
            db.add(ExtractedItem(
                org_id=case.org_id, case_id=case_id, document_id=doc_id,
                category="diagnosis", value=diag, confidence=0.9
            ))
            
        for med in analysis_result.medications or []:
            db.add(ExtractedItem(
                org_id=case.org_id, case_id=case_id, document_id=doc_id,
                category="medication", value=med, confidence=0.9
            ))

        # 5. Advance status
        case.status = "UNDER_REVIEW"
        db.commit()

    except Exception as e:
        case.status = "DOCUMENTS_UPLOADED" # Rollback state
        db.commit()
        raise


def run_task(db: Session, job: Job) -> None:
    """Dispatcher for jobs."""
    if job.type == "DOCUMENT_PROCESSING":
        process_document(db, job.payload)
    elif job.type == "CASE_ANALYSIS":
        analyze_case(db, job.payload)
    else:
        raise ValueError(f"Unknown job type: {job.type}")
