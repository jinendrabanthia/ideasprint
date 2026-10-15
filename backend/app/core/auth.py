"""Authentication and authorization utilities.

Uses Supabase Auth JWT tokens. Every protected endpoint requires a valid
Bearer token. The token is verified against Supabase, and the user's
profile and role are loaded to enforce object-level authorization.
"""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Header, status
from pydantic import BaseModel

from app.core.supabase_client import get_supabase_admin


class AuthenticatedUser(BaseModel):
    """Represents the currently authenticated user after JWT validation."""
    id: str  # Supabase auth user ID
    email: str
    role: str  # "senior", "caregiver", or "admin"
    profile_id: str | None = None  # senior_profile ID if role is senior


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> AuthenticatedUser:
    """Extract and validate the user from the Authorization header.

    Uses Supabase's getUser() which verifies the JWT server-side,
    avoiding the need to manage JWT secrets ourselves.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
        )

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Empty token",
        )

    try:
        admin = get_supabase_admin()
        user_response = admin.auth.get_user(token)
        user = user_response.user
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed",
        )

    # Load user profile from our users table
    try:
        result = admin.table("users").select("*").eq("auth_id", user.id).execute()
        if result.data and len(result.data) > 0:
            db_user = result.data[0]
            profile_id = None
            if db_user.get("role") == "senior":
                profile_result = (
                    admin.table("senior_profiles")
                    .select("id")
                    .eq("user_id", db_user["id"])
                    .execute()
                )
                if profile_result.data and len(profile_result.data) > 0:
                    profile_id = profile_result.data[0]["id"]

            return AuthenticatedUser(
                id=db_user["id"],
                email=user.email or "",
                role=db_user.get("role", "senior"),
                profile_id=profile_id,
            )
    except HTTPException:
        raise
    except Exception:
        pass

    # First-time user — create a record
    new_user_id = str(uuid.uuid4())
    try:
        admin.table("users").insert({
            "id": new_user_id,
            "auth_id": user.id,
            "email": user.email or "",
            "role": "senior",
            "display_name": (user.user_metadata or {}).get("display_name", ""),
        }).execute()

        # Auto-create a senior profile
        profile_id = str(uuid.uuid4())
        admin.table("senior_profiles").insert({
            "id": profile_id,
            "user_id": new_user_id,
            "display_name": (user.user_metadata or {}).get("display_name", ""),
            "timezone": "Asia/Kolkata",
            "language": "en",
            "speech_rate": 1.0,
            "onboarding_complete": False,
        }).execute()

        return AuthenticatedUser(
            id=new_user_id,
            email=user.email or "",
            role="senior",
            profile_id=profile_id,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user profile",
        )


def require_senior(user: AuthenticatedUser) -> AuthenticatedUser:
    """Ensure the user has the senior role."""
    if user.role != "senior":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires a senior account",
        )
    return user


def require_caregiver(user: AuthenticatedUser) -> AuthenticatedUser:
    """Ensure the user has the caregiver role."""
    if user.role != "caregiver":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires a caregiver account",
        )
    return user


async def authorize_profile_access(
    user: AuthenticatedUser, profile_id: str
) -> str:
    """Verify the authenticated user can access the given senior profile.

    - Seniors can only access their own profile.
    - Caregivers can access profiles they have an active relationship with.
    - Returns the validated profile_id.
    """
    if user.role == "senior":
        if user.profile_id != profile_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own profile",
            )
        return profile_id

    if user.role == "caregiver":
        admin = get_supabase_admin()
        result = (
            admin.table("caregiver_relationships")
            .select("id")
            .eq("caregiver_user_id", user.id)
            .eq("senior_profile_id", profile_id)
            .eq("status", "active")
            .execute()
        )
        if not result.data or len(result.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have an active caregiver relationship with this senior",
            )
        return profile_id

    if user.role == "admin":
        # Admins can access any profile — but this should be audited
        return profile_id

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Unauthorized access",
    )
