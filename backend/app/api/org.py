from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.org import OrgResponse
from app.models.user import User
from app.models.organization import Organization
from app.core.database import get_db

router = APIRouter()

@router.get("/", response_model=OrgResponse)
def get_organization(
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(get_db)
):
    org = db.query(Organization).filter(Organization.id == current_user.org_id).first()
    return org
