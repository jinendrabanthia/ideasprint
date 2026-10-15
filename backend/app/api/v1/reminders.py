"""Reminder management endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, Query, status

from app.core.auth import get_current_user, authorize_profile_access, AuthenticatedUser
from app.core.supabase_client import get_supabase_admin
from app.services.reminder_service import (
    preview_reminder,
    create_reminder,
    list_reminders,
    cancel_reminder,
    get_next_reminder,
)
from app.services.safety_service import record_audit_event
from app.schemas.models import (
    ReminderCreateRequest,
    ReminderPreview,
    ReminderOut,
    ReminderListResponse,
)

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.post("/preview", response_model=ReminderPreview)
async def preview(
    req: ReminderCreateRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Preview a reminder before confirming creation."""
    if not user.profile_id:
        raise HTTPException(status_code=404, detail="No senior profile found")

    admin = get_supabase_admin()
    profile = admin.table("senior_profiles").select("timezone").eq("id", user.profile_id).execute()
    tz = profile.data[0]["timezone"] if profile.data else "UTC"

    return preview_reminder(req, tz)


@router.post("/", response_model=ReminderOut, status_code=status.HTTP_201_CREATED)
async def create(
    req: ReminderCreateRequest,
    user: AuthenticatedUser = Depends(get_current_user),
    idempotency_key: str | None = Query(None),
):
    """Create a confirmed reminder. Must set confirmed=True."""
    if not user.profile_id:
        raise HTTPException(status_code=404, detail="No senior profile found")

    if not req.confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reminder must be confirmed before creation. Use /preview first.",
        )

    admin = get_supabase_admin()
    profile = admin.table("senior_profiles").select("timezone").eq("id", user.profile_id).execute()
    tz = profile.data[0]["timezone"] if profile.data else "UTC"

    try:
        reminder = create_reminder(
            profile_id=user.profile_id,
            req=req,
            created_by=user.id,
            timezone=tz,
            idempotency_key=idempotency_key or str(uuid.uuid4()),
        )

        record_audit_event(
            profile_id=user.profile_id,
            user_id=user.id,
            event_type="reminder_created",
            description=f"Reminder created: {req.label}",
            metadata={"reminder_id": reminder.id},
        )

        return reminder

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=ReminderListResponse)
async def list_all(
    user: AuthenticatedUser = Depends(get_current_user),
    date: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    profile_id: str | None = Query(None),
):
    """List reminders for the authenticated user's profile."""
    target_profile = profile_id or user.profile_id
    if not target_profile:
        raise HTTPException(status_code=404, detail="No senior profile found")

    await authorize_profile_access(user, target_profile)

    reminders = list_reminders(
        profile_id=target_profile,
        date_filter=date,
        status_filter=status_filter,
    )

    return ReminderListResponse(reminders=reminders, total=len(reminders))


@router.get("/next", response_model=ReminderOut | None)
async def next_reminder(
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Get the next upcoming reminder."""
    if not user.profile_id:
        raise HTTPException(status_code=404, detail="No senior profile found")

    return get_next_reminder(user.profile_id)


@router.patch("/{reminder_id}/cancel", response_model=ReminderOut)
async def cancel(
    reminder_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Cancel a specific reminder."""
    if not user.profile_id:
        raise HTTPException(status_code=404, detail="No senior profile found")

    try:
        result = cancel_reminder(user.profile_id, reminder_id)

        record_audit_event(
            profile_id=user.profile_id,
            user_id=user.id,
            event_type="reminder_cancelled",
            description=f"Reminder cancelled: {result.label}",
            metadata={"reminder_id": reminder_id},
        )

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
