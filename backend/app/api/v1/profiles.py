"""Profile and preferences endpoints."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, status

from app.core.auth import get_current_user, authorize_profile_access, AuthenticatedUser
from app.core.supabase_client import get_supabase_admin
from app.schemas.models import SeniorProfileOut, ProfileUpdateRequest

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/me", response_model=SeniorProfileOut)
async def get_my_profile(user: AuthenticatedUser = Depends(get_current_user)):
    """Get the current senior's profile."""
    if not user.profile_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No senior profile found for this account",
        )

    admin = get_supabase_admin()
    result = admin.table("senior_profiles").select("*").eq("id", user.profile_id).execute()

    if not result.data or len(result.data) == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    return SeniorProfileOut(**result.data[0])


@router.get("/{profile_id}", response_model=SeniorProfileOut)
async def get_profile(
    profile_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Get a specific senior profile (with authorization check)."""
    await authorize_profile_access(user, profile_id)

    admin = get_supabase_admin()
    result = admin.table("senior_profiles").select("*").eq("id", profile_id).execute()

    if not result.data or len(result.data) == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    return SeniorProfileOut(**result.data[0])


@router.patch("/me", response_model=SeniorProfileOut)
async def update_my_profile(
    req: ProfileUpdateRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Update the current senior's profile settings."""
    if not user.profile_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No profile found")

    admin = get_supabase_admin()
    updates = req.model_dump(exclude_none=True)
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()

    result = (
        admin.table("senior_profiles")
        .update(updates)
        .eq("id", user.profile_id)
        .execute()
    )

    if result.data and len(result.data) > 0:
        return SeniorProfileOut(**result.data[0])

    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Update failed")
