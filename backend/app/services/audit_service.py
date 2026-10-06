"""
Audit service: creates audit log entries for security-relevant actions.
Never logs PHI values — only IDs and action metadata.
"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import Request

from app.models.audit_log import AuditLog
from app.models.user import User


def create_audit_log(
    db: Session,
    *,
    user: User,
    action: str,
    entity: str,
    entity_id: str,
    request: Optional[Request] = None,
    metadata: Optional[Dict[str, Any]] = None,
    commit: bool = True,
) -> AuditLog:
    """
    Record an auditable event. Call from service layer or route handlers.
    """
    ip = None
    user_agent = None
    if request:
        ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

    log = AuditLog(
        org_id=user.org_id,
        user_id=user.id,
        action=action,
        entity=entity,
        entity_id=str(entity_id),
        ip=ip,
        user_agent=user_agent,
        metadata_=metadata,
    )
    db.add(log)
    if commit:
        db.commit()
        db.refresh(log)
    else:
        db.flush()
    return log
