"""Security utilities for authentication and authorization."""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from lanterne_rouge.backend.core.config import get_settings

settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token with unique identifier."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    # Add unique identifier to make each token unique
    to_encode.update({"exp": expire, "type": "access", "jti": str(uuid.uuid4())})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token with unique identifier."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    # Add unique identifier to make each token unique
    to_encode.update({"exp": expire, "type": "refresh", "jti": str(uuid.uuid4())})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        raise ValueError("Invalid token")
