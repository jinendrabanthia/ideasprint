"""Check-in endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends, Query

from app.core.auth import get_current_user, authorize_profile_access, AuthenticatedUser
from app.services.checkin_service import (
    get_checkin_config,
    update_checkin_config,
    get_todays_checkin,
    submit_checkin,
    list_checkins,
)
from app.schemas.models import CheckInConfigRequest, CheckInSubmitRequest, CheckInOut

router = APIRouter(prefix="/checkins", tags=["checkins"])


@router.get("/today")
async def today(user: AuthenticatedUser = Depends(get_current_user)):
    """Get or create today's check-in."""
    if not user.profile_id:
        raise HTTPException(status_code=404, detail="No senior profile found")
    checkin = get_todays_checkin(user.profile_id)
    return checkin or {"status": "no_checkin", "message": "Check-ins are not enabled"}


@router.post("/submit")
async def submit(
    req: CheckInSubmitRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Submit a check-in response."""
    if not user.profile_id:
        raise HTTPException(status_code=404, detail="No senior profile found")

    try:
        result = submit_checkin(
            profile_id=user.profile_id,
            checkin_id=req.checkin_id,
            response=req.response.value,
            notes=req.notes,
            user_id=user.id,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history")
async def history(
    user: AuthenticatedUser = Depends(get_current_user),
    date: str | None = Query(None),
    profile_id: str | None = Query(None),
):
    """List check-in history."""
    target = profile_id or user.profile_id
    if not target:
        raise HTTPException(status_code=404, detail="No profile found")
    await authorize_profile_access(user, target)
    return list_checkins(target, date_filter=date)


@router.get("/config")
async def get_config(user: AuthenticatedUser = Depends(get_current_user)):
    """Get check-in configuration."""
    if not user.profile_id:
        raise HTTPException(status_code=404, detail="No profile found")
    return get_checkin_config(user.profile_id)


@router.put("/config")
async def set_config(
    req: CheckInConfigRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Update check-in configuration."""
    if not user.profile_id:
        raise HTTPException(status_code=404, detail="No profile found")
    return update_checkin_config(
        profile_id=user.profile_id,
        enabled=req.enabled,
        time=req.time,
        questions=req.questions,
    )
