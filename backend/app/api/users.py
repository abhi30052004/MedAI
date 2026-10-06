from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core.security import get_password_hash
from app.schemas.user import UserResponse, UserCreate, UserUpdate
from app.models.user import User
from app.models.audit_log import AuditLog
from app.core.database import get_db

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.require_roles("admin"))
):
    users = db.query(User).filter(User.org_id == current_user.org_id).offset(skip).limit(limit).all()
    return users

@router.post("/", response_model=UserResponse)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.require_roles("admin"))
):
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
        
    user = User(
        name=user_in.name,
        email=user_in.email,
        role=user_in.role,
        is_active=user_in.is_active,
        org_id=current_user.org_id,
        password_hash=get_password_hash(user_in.password),
        email_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Audit Log
    audit_log = AuditLog(
        action="USER_CREATED",
        entity="user",
        entity_id=str(user.id),
        org_id=current_user.org_id,
        user_id=current_user.id,
        metadata_={"role": user.role, "email": user.email}
    )
    db.add(audit_log)
    db.commit()
    
    return user

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.require_roles("admin"))
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Not enough privileges")
        
    update_data = user_in.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["password_hash"] = get_password_hash(update_data.pop("password"))
        
    for key, value in update_data.items():
        setattr(user, key, value)
        
    db.commit()
    db.refresh(user)
    return user
