"""Check-in service — manage daily wellness check-ins."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.core.supabase_client import get_supabase_admin
from app.services.safety_service import record_audit_event


def get_checkin_config(profile_id: str) -> dict:
    """Get or create default check-in configuration for a profile."""
    admin = get_supabase_admin()
    result = (
        admin.table("checkin_configs")
        .select("*")
        .eq("profile_id", profile_id)
        .execute()
    )

    if result.data and len(result.data) > 0:
        return result.data[0]

    # Create default config
    config_id = str(uuid.uuid4())
    default = {
        "id": config_id,
        "profile_id": profile_id,
        "enabled": True,
        "time": "09:00",
        "questions": ["How are you feeling today?"],
    }
    admin.table("checkin_configs").insert(default).execute()
    return default


def update_checkin_config(
    profile_id: str,
    enabled: bool | None = None,
    time: str | None = None,
    questions: list[str] | None = None,
) -> dict:
    """Update check-in configuration for a profile."""
    admin = get_supabase_admin()
    config = get_checkin_config(profile_id)

    updates = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if enabled is not None:
        updates["enabled"] = enabled
    if time is not None:
        updates["time"] = time
    if questions is not None:
        updates["questions"] = questions

    result = (
        admin.table("checkin_configs")
        .update(updates)
        .eq("id", config["id"])
        .execute()
    )

    return result.data[0] if result.data else config


def create_daily_checkin(profile_id: str) -> dict | None:
    """Create today's check-in if not already created and config is enabled."""
    config = get_checkin_config(profile_id)
    if not config.get("enabled", True):
        return None

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    admin = get_supabase_admin()

    # Check if today's checkin already exists
    existing = (
        admin.table("checkins")
        .select("*")
        .eq("profile_id", profile_id)
        .eq("scheduled_date", today)
        .execute()
    )

    if existing.data and len(existing.data) > 0:
        return existing.data[0]

    checkin_id = str(uuid.uuid4())
    data = {
        "id": checkin_id,
        "profile_id": profile_id,
        "scheduled_time": config.get("time", "09:00"),
        "scheduled_date": today,
        "status": "pending",
    }

    result = admin.table("checkins").insert(data).execute()
    return result.data[0] if result.data else data


def submit_checkin(
    profile_id: str,
    checkin_id: str,
    response: str,
    notes: str = "",
    user_id: str = "",
) -> dict:
    """Submit a check-in response. Handles escalation for 'need_help'."""
    admin = get_supabase_admin()

    # Verify ownership
    existing = (
        admin.table("checkins")
        .select("*")
        .eq("id", checkin_id)
        .eq("profile_id", profile_id)
        .execute()
    )

    if not existing.data or len(existing.data) == 0:
        raise ValueError("Check-in not found or access denied")

    checkin = existing.data[0]
    if checkin["status"] == "completed":
        raise ValueError("Check-in already completed")

    now = datetime.now(timezone.utc).isoformat()
    should_escalate = response == "need_help"

    updates = {
        "response": response,
        "notes": notes,
        "status": "completed" if not should_escalate else "escalated",
        "escalated": should_escalate,
        "responded_at": now,
    }

    result = (
        admin.table("checkins")
        .update(updates)
        .eq("id", checkin_id)
        .eq("profile_id", profile_id)
        .execute()
    )

    # Record audit event
    record_audit_event(
        profile_id=profile_id,
        user_id=user_id,
        event_type="checkin_response",
        description=f"Check-in response: {response}",
        metadata={"checkin_id": checkin_id, "response": response, "escalated": should_escalate},
    )

    if should_escalate:
        # Trigger notification to trusted contacts
        _escalate_checkin(profile_id, checkin_id)

    return result.data[0] if result.data else updates


def _escalate_checkin(profile_id: str, checkin_id: str) -> None:
    """Escalate a check-in by notifying trusted contacts."""
    admin = get_supabase_admin()

    contacts = (
        admin.table("trusted_contacts")
        .select("*")
        .eq("profile_id", profile_id)
        .eq("notify_on_missed_checkin", True)
        .execute()
    )

    for contact in (contacts.data or []):
        notif_id = str(uuid.uuid4())
        admin.table("notifications").insert({
            "id": notif_id,
            "profile_id": profile_id,
            "type": "escalation",
            "message": f"Senior needs help during check-in",
            "status": "simulated",
            "is_simulated": True,
            "recipient": contact.get("name", "Unknown"),
            "metadata": {
                "checkin_id": checkin_id,
                "contact_id": contact["id"],
            },
        }).execute()


def list_checkins(
    profile_id: str,
    date_filter: str | None = None,
    limit: int = 30,
) -> list[dict]:
    """List check-ins for a profile."""
    admin = get_supabase_admin()
    query = admin.table("checkins").select("*").eq("profile_id", profile_id)

    if date_filter:
        query = query.eq("scheduled_date", date_filter)

    query = query.order("scheduled_date", desc=True).limit(limit)
    result = query.execute()
    return result.data or []


def get_todays_checkin(profile_id: str) -> dict | None:
    """Get today's check-in, creating it if needed."""
    return create_daily_checkin(profile_id)
