"""Pydantic schemas for auth endpoints."""
from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    org_name: str
    admin_name: str
    admin_email: EmailStr
    admin_password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class VerifyEmailRequest(BaseModel):
    token: str


class AcceptInviteRequest(BaseModel):
    token: str
    name: str
    password: str
