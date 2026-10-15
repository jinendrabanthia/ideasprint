"""Trusted contact management endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Depends, status

from app.core.auth import get_current_user, authorize_profile_access, AuthenticatedUser
from app.core.supabase_client import get_supabase_admin
from app.services.safety_service import record_audit_event
from app.schemas.models import TrustedContactCreateRequest, TrustedContactOut

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.post("/", response_model=TrustedContactOut, status_code=status.HTTP_201_CREATED)
async def create_contact(
    req: TrustedContactCreateRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Add a trusted contact for the authenticated senior."""
    if not user.profile_id:
        raise HTTPException(status_code=404, detail="No senior profile found")

    admin = get_supabase_admin()
    contact_id = str(uuid.uuid4())

    data = {
        "id": contact_id,
        "profile_id": user.profile_id,
        "name": req.name,
        "phone": req.phone,
        "email": req.email,
        "relationship": req.relationship,
        "is_emergency": req.is_emergency,
        "notify_on_help": req.notify_on_help,
        "notify_on_missed_checkin": req.notify_on_missed_checkin,
    }

    result = admin.table("trusted_contacts").insert(data).execute()

    record_audit_event(
        profile_id=user.profile_id,
        user_id=user.id,
        event_type="contact_added",
        description=f"Trusted contact added: {req.name}",
        metadata={"contact_id": contact_id},
    )

    if result.data and len(result.data) > 0:
        return TrustedContactOut(**result.data[0])
    return TrustedContactOut(**data)


@router.get("/", response_model=list[TrustedContactOut])
async def list_contacts(
    user: AuthenticatedUser = Depends(get_current_user),
):
    """List trusted contacts for the authenticated senior."""
    if not user.profile_id:
        raise HTTPException(status_code=404, detail="No senior profile found")

    admin = get_supabase_admin()
    result = (
        admin.table("trusted_contacts")
        .select("*")
        .eq("profile_id", user.profile_id)
        .order("created_at")
        .execute()
    )
    return [TrustedContactOut(**c) for c in (result.data or [])]


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Remove a trusted contact (ownership verified)."""
    if not user.profile_id:
        raise HTTPException(status_code=404, detail="No senior profile found")

    admin = get_supabase_admin()
    existing = (
        admin.table("trusted_contacts")
        .select("id")
        .eq("id", contact_id)
        .eq("profile_id", user.profile_id)
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=404, detail="Contact not found or access denied")

    admin.table("trusted_contacts").delete().eq("id", contact_id).eq("profile_id", user.profile_id).execute()

    record_audit_event(
        profile_id=user.profile_id,
        user_id=user.id,
        event_type="contact_removed",
        description="Trusted contact removed",
        metadata={"contact_id": contact_id},
    )
