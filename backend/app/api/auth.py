from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.api import deps
from app.schemas.user import UserResponse
from app.schemas.auth import RegisterRequest, Token
from app.models.user import User
from app.models.organization import Organization
from app.core.database import get_db

router = APIRouter()

@router.post("/register")
def register(
    req: RegisterRequest,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(User.email == req.admin_email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    org = Organization(name=req.org_name)
    db.add(org)
    db.commit()
    db.refresh(org)

    user = User(
        org_id=org.id,
        name=req.admin_name,
        email=req.admin_email,
        password_hash=security.get_password_hash(req.admin_password),
        role="admin",
        is_active=True,
        email_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "Registration successful"}

@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
        
    if not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            subject=str(user.id), 
            role=user.role,
            organization_id=str(user.org_id),
            expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.get("/me", response_model=UserResponse)
def read_users_me(
    current_user: User = Depends(deps.get_current_active_user)
):
    return current_user
