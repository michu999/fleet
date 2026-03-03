"""
Auth module router.
API endpoints for authentication and user management.

Note: Most endpoints require authentication which will be implemented
when the OAuth flow is finalized.
"""

from fastapi import APIRouter

router = APIRouter()


# Placeholder - endpoints will be added when auth flow is decided
# Examples of future endpoints:
#
# @router.get("/me", response_model=UserRead)
# async def get_current_user(current_user: User = Depends(get_current_user)):
#     return current_user
#
# @router.get("/google/login")
# async def google_login():
#     ...
#
# @router.get("/google/callback")
# async def google_callback():
#     ...
