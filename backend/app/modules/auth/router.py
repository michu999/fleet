"""
Auth module router.
API endpoints for Google OAuth 2.0 authentication.
"""

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import create_access_token, set_auth_cookie, clear_auth_cookie
from app.modules.auth.models import User
from app.modules.auth.schemas import UserRead
from app.modules.auth.service import verify_google_token, get_or_create_oauth_user

router = APIRouter()


# =============================================================================
# Request/Response Schemas
# =============================================================================

class GoogleAuthRequest(BaseModel):
    """Request body for Google OAuth login."""
    credential: str


class AuthResponse(BaseModel):
    """Response after successful authentication."""
    user: UserRead
    is_new_user: bool


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str


# =============================================================================
# Auth Endpoints
# =============================================================================

@router.post("/google", response_model=AuthResponse)
async def google_auth(
    body: GoogleAuthRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """
    Authenticate with Google OAuth 2.0.

    Flow:
    1. Frontend gets Google ID token via Google Sign-In
    2. Frontend sends token to this endpoint
    3. Backend verifies token with Google
    4. Backend creates/updates user and tenant
    5. Backend sets httpOnly cookie with JWT

    Returns:
        User data and whether this is a new registration.
    """
    # Verify Google token and get user info
    google_data = await verify_google_token(body.credential)

    # Get or create user
    user, is_new_user = await get_or_create_oauth_user(db, google_data)

    # Create JWT token
    token = create_access_token({
        "sub": str(user.id),
        "tenant_id": str(user.tenant_id),
        "role": user.role.value if hasattr(user.role, 'value') else user.role,
    })

    # Set httpOnly cookie
    set_auth_cookie(response, token)

    return AuthResponse(
        user=UserRead.model_validate(user),
        is_new_user=is_new_user,
    )


@router.get("/me", response_model=UserRead)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserRead:
    """
    Get current authenticated user.

    Requires valid JWT in httpOnly cookie.

    Returns:
        Current user data.
    """
    return UserRead.model_validate(current_user)


@router.post("/logout", response_model=MessageResponse)
async def logout(response: Response) -> MessageResponse:
    """
    Logout current user.

    Clears the authentication cookie.

    Returns:
        Confirmation message.
    """
    clear_auth_cookie(response)
    return MessageResponse(message="Logged out successfully")
