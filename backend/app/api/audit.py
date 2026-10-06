from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api import deps
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.audit import AuditLogResponse

router = APIRouter()

@router.get("/", response_model=List[AuditLogResponse])
def read_audit_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.require_roles("admin")),
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    entity: Optional[str] = None
):
    query = db.query(AuditLog).filter(AuditLog.org_id == current_user.org_id)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if entity:
        query = query.filter(AuditLog.entity == entity)
        
    logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    return logs
