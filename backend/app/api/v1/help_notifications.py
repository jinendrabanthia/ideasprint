"""Help, notifications, and audit event endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends, Query

from app.core.auth import get_current_user, authorize_profile_access, AuthenticatedUser
from app.core.supabase_client import get_supabase_admin
from app.services.safety_service import handle_help_request
from app.schemas.models import HelpRequest, HelpResponse, NotificationOut, AuditEventOut

router = APIRouter(tags=["help-notifications"])


# ── Help ─────────────────────────────────────────────

@router.post("/help", response_model=HelpResponse)
async def request_help(
    req: HelpRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Submit a help request and trigger the escalation workflow."""
    if not user.profile_id:
        raise HTTPException(status_code=404, detail="No senior profile found")

    result = handle_help_request(
        profile_id=user.profile_id,
        user_id=user.id,
        message=req.message,
        urgency=req.urgency,
    )

    return HelpResponse(**result)


# ── Notifications ────────────────────────────────────

@router.get("/notifications", response_model=list[NotificationOut])
async def list_notifications(
    user: AuthenticatedUser = Depends(get_current_user),
    profile_id: str | None = Query(None),
    limit: int = Query(50, le=100),
):
    """List notification history for the authenticated user's profile."""
    target = profile_id or user.profile_id
    if not target:
        raise HTTPException(status_code=404, detail="No profile found")
    await authorize_profile_access(user, target)

    admin = get_supabase_admin()
    result = (
        admin.table("notifications")
        .select("*")
        .eq("profile_id", target)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return [NotificationOut(**n) for n in (result.data or [])]


# ── Audit Events ─────────────────────────────────────

@router.get("/activity", response_model=list[AuditEventOut])
async def list_activity(
    user: AuthenticatedUser = Depends(get_current_user),
    profile_id: str | None = Query(None),
    limit: int = Query(30, le=100),
):
    """List activity/audit events for the authenticated user's profile."""
    target = profile_id or user.profile_id
    if not target:
        raise HTTPException(status_code=404, detail="No profile found")
    await authorize_profile_access(user, target)

    admin = get_supabase_admin()
    result = (
        admin.table("audit_events")
        .select("*")
        .eq("profile_id", target)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return [AuditEventOut(**e) for e in (result.data or [])]
