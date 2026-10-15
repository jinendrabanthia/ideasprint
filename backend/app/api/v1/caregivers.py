"""Caregiver dashboard and relationship management endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, status

from app.core.auth import get_current_user, authorize_profile_access, AuthenticatedUser
from app.core.supabase_client import get_supabase_admin
from app.services.safety_service import record_audit_event
from app.services.reminder_service import list_reminders
from app.services.checkin_service import list_checkins
from app.schemas.models import (
    CaregiverRelationshipRequest,
    CaregiverRelationshipOut,
    CaregiverDashboardData,
    SeniorProfileOut,
)

router = APIRouter(prefix="/caregiver", tags=["caregiver"])


@router.get("/dashboard", response_model=CaregiverDashboardData)
async def dashboard(user: AuthenticatedUser = Depends(get_current_user)):
    """Get caregiver dashboard data — only authorized senior profiles."""
    if user.role != "caregiver":
        raise HTTPException(status_code=403, detail="Caregiver access required")

    admin = get_supabase_admin()
    rels = (
        admin.table("caregiver_relationships")
        .select("*")
        .eq("caregiver_user_id", user.id)
        .eq("status", "active")
        .execute()
    )

    relationships = [CaregiverRelationshipOut(**r) for r in (rels.data or [])]
    profiles = []

    for rel in relationships:
        profile_result = (
            admin.table("senior_profiles")
            .select("*")
            .eq("id", rel.senior_profile_id)
            .execute()
        )
        if profile_result.data:
            profiles.append(SeniorProfileOut(**profile_result.data[0]))

    return CaregiverDashboardData(senior_profiles=profiles, relationships=relationships)


@router.get("/seniors/{profile_id}/reminders")
async def senior_reminders(
    profile_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """View reminders for an authorized senior."""
    if user.role != "caregiver":
        raise HTTPException(status_code=403, detail="Caregiver access required")
    await authorize_profile_access(user, profile_id)
    return list_reminders(profile_id)


@router.get("/seniors/{profile_id}/checkins")
async def senior_checkins(
    profile_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """View check-in history for an authorized senior."""
    if user.role != "caregiver":
        raise HTTPException(status_code=403, detail="Caregiver access required")
    await authorize_profile_access(user, profile_id)
    return list_checkins(profile_id)


@router.get("/seniors/{profile_id}/notifications")
async def senior_notifications(
    profile_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """View notification history for an authorized senior."""
    if user.role != "caregiver":
        raise HTTPException(status_code=403, detail="Caregiver access required")
    await authorize_profile_access(user, profile_id)

    admin = get_supabase_admin()
    result = (
        admin.table("notifications")
        .select("*")
        .eq("profile_id", profile_id)
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )
    return result.data or []


@router.post("/relationships", response_model=CaregiverRelationshipOut, status_code=201)
async def create_relationship(
    req: CaregiverRelationshipRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Create a caregiver relationship (must be a caregiver user)."""
    if user.role != "caregiver":
        raise HTTPException(status_code=403, detail="Caregiver access required")

    admin = get_supabase_admin()

    # Check the senior profile exists
    profile = admin.table("senior_profiles").select("id").eq("id", req.senior_profile_id).execute()
    if not profile.data:
        raise HTTPException(status_code=404, detail="Senior profile not found")

    # Check for existing relationship
    existing = (
        admin.table("caregiver_relationships")
        .select("id, status")
        .eq("caregiver_user_id", user.id)
        .eq("senior_profile_id", req.senior_profile_id)
        .execute()
    )
    if existing.data:
        if existing.data[0]["status"] == "active":
            raise HTTPException(status_code=409, detail="Relationship already exists")
        # Reactivate revoked relationship
        admin.table("caregiver_relationships").update({
            "status": "active",
            "permissions": req.permissions,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", existing.data[0]["id"]).execute()
        updated = admin.table("caregiver_relationships").select("*").eq("id", existing.data[0]["id"]).execute()
        return CaregiverRelationshipOut(**updated.data[0])

    rel_id = str(uuid.uuid4())
    data = {
        "id": rel_id,
        "caregiver_user_id": user.id,
        "senior_profile_id": req.senior_profile_id,
        "status": "active",
        "permissions": req.permissions,
    }
    result = admin.table("caregiver_relationships").insert(data).execute()

    record_audit_event(
        profile_id=req.senior_profile_id,
        user_id=user.id,
        event_type="caregiver_linked",
        description="Caregiver relationship created",
        metadata={"caregiver_id": user.id},
    )

    return CaregiverRelationshipOut(**(result.data[0] if result.data else data))


@router.patch("/relationships/{relationship_id}/revoke")
async def revoke_relationship(
    relationship_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Revoke a caregiver relationship."""
    admin = get_supabase_admin()

    # Verify the relationship belongs to this user (as caregiver or as the senior)
    rel = admin.table("caregiver_relationships").select("*").eq("id", relationship_id).execute()
    if not rel.data:
        raise HTTPException(status_code=404, detail="Relationship not found")

    relationship = rel.data[0]

    # Either the caregiver or the senior can revoke
    is_caregiver = relationship["caregiver_user_id"] == user.id
    is_senior = user.profile_id == relationship["senior_profile_id"]

    if not is_caregiver and not is_senior:
        raise HTTPException(status_code=403, detail="Not authorized to revoke this relationship")

    admin.table("caregiver_relationships").update({
        "status": "revoked",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", relationship_id).execute()

    record_audit_event(
        profile_id=relationship["senior_profile_id"],
        user_id=user.id,
        event_type="caregiver_revoked",
        description="Caregiver relationship revoked",
        metadata={"relationship_id": relationship_id, "revoked_by": user.id},
    )

    return {"status": "revoked", "relationship_id": relationship_id}
