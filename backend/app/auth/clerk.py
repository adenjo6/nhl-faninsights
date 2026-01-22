"""
Clerk authentication integration.
"""
import httpx
from fastapi import HTTPException, Header
from typing import Optional
from app.config import settings


async def verify_clerk_token(authorization: str = Header(None)) -> dict:
    """
    Verify Clerk session token and return user info.

    In production, this validates the JWT token with Clerk.
    For MVP/development, we'll do a simple check.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Extract Bearer token
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    # In production, verify with Clerk API
    if settings.CLERK_SECRET_KEY:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.clerk.com/v1/sessions/{token}/verify",
                    headers={"Authorization": f"Bearer {settings.CLERK_SECRET_KEY}"}
                )

                if response.status_code != 200:
                    raise HTTPException(status_code=401, detail="Invalid token")

                session_data = response.json()
                return {
                    "user_id": session_data["user_id"],
                    "user_name": session_data.get("user", {}).get("username", "Anonymous"),
                    "avatar_url": session_data.get("user", {}).get("image_url"),
                    "email": session_data.get("user", {}).get("email_addresses", [{}])[0].get("email_address"),
                }
        except httpx.HTTPError:
            raise HTTPException(status_code=401, detail="Could not verify token")

    # Development mode - mock user
    return {
        "user_id": "dev_user_123",
        "user_name": "Dev User",
        "avatar_url": None,
        "email": "dev@example.com",
        "is_admin": False
    }


def check_admin(user: dict) -> bool:
    """Check if user has admin privileges."""
    # In production, check against admin user IDs or roles
    admin_user_ids = []  # Add admin Clerk user IDs here
    return user.get("user_id") in admin_user_ids or user.get("is_admin", False)
