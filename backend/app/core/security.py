"""
Security utilities: password hashing, JWT token creation/validation.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union
import secrets

from jose import jwt, JWTError
import bcrypt

from app.core.config import settings

# ── Password hashing ────────────────────────────────────────────

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


# ── JWT access token ────────────────────────────────────────────

def create_access_token(
    subject: Union[str, Any],
    role: str,
    organization_id: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "role": role,
        "org_id": str(organization_id),
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token. Raises JWTError on failure."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


# ── Refresh token ───────────────────────────────────────────────

def create_refresh_token() -> str:
    """Generate a cryptographically secure random refresh token."""
    return secrets.token_urlsafe(64)


def hash_token(token: str) -> str:
    """Hash a refresh/reset token for storage using SHA-256 via passlib."""
    import hashlib
    return hashlib.sha256(token.encode()).hexdigest()


# ── Email verification / password reset tokens ──────────────────

def create_verification_token() -> str:
    """Generate an expiring token for email verification or password reset."""
    return secrets.token_urlsafe(32)
