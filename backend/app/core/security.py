"""
JWT token handling and cookie management for authentication.
"""

from datetime import datetime, timedelta, timezone

from fastapi import Response
from jose import jwt, JWTError

from app.core.config import get_settings

settings = get_settings()

# JWT Configuration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS: int = 24


def create_access_token(data: dict) -> str:
    """
    Create JWT access token.

    Args:
        data: Payload dict containing at minimum:
            - sub: user_id as string
            - tenant_id: tenant_id as string
            - role: user role value

    Returns:
        Encoded JWT token string.
    """
    payload = data.copy()
    payload["iat"] = datetime.now(timezone.utc)
    payload["exp"] = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """
    Decode and verify JWT token.

    Args:
        token: JWT token string.

    Returns:
        Payload dict if valid, None if invalid/expired.
        Never raises - caller handles None.
    """
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


def set_auth_cookie(response: Response, token: str) -> None:
    """
    Set httpOnly cookie with JWT token.

    Security settings:
        - httponly: Prevents JavaScript access (XSS protection)
        - secure: Only sent over HTTPS (disabled in development)
        - samesite: CSRF protection
        - max_age: 24 hours
    """
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=settings.ENVIRONMENT != "development",  # False for local dev
        samesite="lax",
        max_age=86400,  # 24 hours in seconds
    )


def clear_auth_cookie(response: Response) -> None:
    """
    Remove authentication cookie (logout).
    """
    response.delete_cookie(key="access_token")

