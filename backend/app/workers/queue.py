"""
Background processing job queue using the database.
"""
import uuid
import traceback
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import SessionLocal
from app.models.job import Job


def enqueue_job(
    db: Session,
    org_id: uuid.UUID,
    job_type: str,
    payload: Dict[str, Any],
) -> Job:
    """Add a new job to the queue."""
    job = Job(
        org_id=org_id,
        type=job_type,
        payload=payload,
        status="QUEUED"
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def claim_job(db: Session, max_attempts: int = 3) -> Optional[Job]:
    """
    Find and claim a pending job.
    Also handles jobs stuck in RUNNING state (timeout recovery).
    """
    # Find QUEUED jobs, or RUNNING jobs that haven't been updated in 15 mins (stuck)
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=15)
    
    # In a real distributed system with multiple workers, we'd use SELECT FOR UPDATE SKIP LOCKED
    # Here, for our simple in-process worker, a basic query + update works
    job = db.query(Job).filter(
        Job.attempts < max_attempts,
        or_(
            Job.status == "QUEUED",
            (Job.status == "RUNNING") & (Job.locked_at < cutoff)
        )
    ).order_by(Job.created_at.asc()).first()

    if not job:
        return None

    job.status = "RUNNING"
    job.locked_at = datetime.now(timezone.utc)
    job.attempts += 1
    db.commit()
    db.refresh(job)
    
    return job


def complete_job(db: Session, job: Job) -> None:
    """Mark a job as done."""
    job.status = "DONE"
    job.finished_at = datetime.now(timezone.utc)
    db.commit()


def fail_job(db: Session, job: Job, error: str) -> None:
    """Mark a job as failed."""
    job.status = "FAILED"
    job.error = error[-1000:]  # truncate error
    job.finished_at = datetime.now(timezone.utc)
    db.commit()
