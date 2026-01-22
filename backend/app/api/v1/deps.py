from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException
from app.db.session import SessionLocal
from app.auth.clerk import verify_clerk_token, check_admin


def get_db():
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(user: dict = Depends(verify_clerk_token)) -> dict:
    """
    Get current authenticated user.
    Requires valid Clerk session token.
    """
    return user


async def get_current_user_optional(authorization: str = None) -> dict | None:
    """
    Get current user if authenticated, None otherwise.
    Used for endpoints that work with or without auth.
    """
    if not authorization:
        return None

    try:
        return await verify_clerk_token(authorization)
    except HTTPException:
        return None


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """
    Require admin privileges.
    Raises 403 if user is not admin.
    """
    if not check_admin(user):
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user