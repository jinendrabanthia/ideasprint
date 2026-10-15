"""Reminder service — create, list, cancel, and manage reminders.

All operations enforce profile-level authorization. Reminders require
explicit confirmation before being persisted (preview → confirm flow).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.core.supabase_client import get_supabase_admin
from app.schemas.models import (
    ReminderCreateRequest,
    ReminderOut,
    ReminderPreview,
    ReminderStatus,
)


def _parse_datetime_display(date_str: str, time_str: str, tz: str) -> str:
    """Create a human-readable local datetime display string."""
    try:
        from dateutil import parser as dateutil_parser
        import pytz

        local_tz = pytz.timezone(tz)
        dt = dateutil_parser.parse(f"{date_str} {time_str}")
        dt = local_tz.localize(dt)
        return dt.strftime("%A, %B %d, %Y at %I:%M %p %Z")
    except Exception:
        return f"{date_str} at {time_str}"


def _compute_utc(date_str: str, time_str: str, tz: str) -> str | None:
    """Convert local date+time to UTC ISO string."""
    try:
        from dateutil import parser as dateutil_parser
        import pytz

        local_tz = pytz.timezone(tz)
        dt = dateutil_parser.parse(f"{date_str} {time_str}")
        dt = local_tz.localize(dt)
        utc_dt = dt.astimezone(pytz.utc)
        return utc_dt.isoformat()
    except Exception:
        return None


def preview_reminder(
    req: ReminderCreateRequest,
    timezone: str = "UTC",
) -> ReminderPreview:
    """Generate a preview of the reminder for user confirmation."""
    display = _parse_datetime_display(req.scheduled_date, req.scheduled_time, timezone)
    return ReminderPreview(
        label=req.label,
        scheduled_date=req.scheduled_date,
        scheduled_time=req.scheduled_time,
        local_datetime_display=display,
        recurrence=req.recurrence,
        is_medication=req.is_medication,
        needs_confirmation=True,
    )


def create_reminder(
    profile_id: str,
    req: ReminderCreateRequest,
    created_by: str,
    timezone: str = "UTC",
    idempotency_key: str | None = None,
) -> ReminderOut:
    """Create a confirmed reminder in the database.

    Raises ValueError if not confirmed or if a duplicate idempotency key exists.
    """
    if not req.confirmed:
        raise ValueError("Reminder must be confirmed before creation. Use preview first.")

    admin = get_supabase_admin()

    # Idempotency check
    if idempotency_key:
        existing = (
            admin.table("reminders")
            .select("*")
            .eq("idempotency_key", idempotency_key)
            .execute()
        )
        if existing.data and len(existing.data) > 0:
            row = existing.data[0]
            return ReminderOut(**row, created_by=row.get("created_by", ""))

    reminder_id = str(uuid.uuid4())
    utc_time = _compute_utc(req.scheduled_date, req.scheduled_time, timezone)

    data = {
        "id": reminder_id,
        "profile_id": profile_id,
        "label": req.label,
        "scheduled_date": req.scheduled_date,
        "scheduled_time": req.scheduled_time,
        "scheduled_utc": utc_time,
        "recurrence": req.recurrence,
        "is_medication": req.is_medication,
        "status": "scheduled",
        "created_by": created_by,
    }
    if idempotency_key:
        data["idempotency_key"] = idempotency_key

    result = admin.table("reminders").insert(data).execute()
    if result.data and len(result.data) > 0:
        row = result.data[0]
        return ReminderOut(
            id=row["id"],
            profile_id=row["profile_id"],
            label=row["label"],
            scheduled_date=row["scheduled_date"],
            scheduled_time=row["scheduled_time"],
            scheduled_utc=row.get("scheduled_utc"),
            recurrence=row.get("recurrence", "none"),
            is_medication=row.get("is_medication", False),
            status=row.get("status", "scheduled"),
            created_by=row.get("created_by", ""),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    raise RuntimeError("Failed to create reminder")


def list_reminders(
    profile_id: str,
    date_filter: str | None = None,
    status_filter: str | None = None,
    limit: int = 50,
) -> list[ReminderOut]:
    """List reminders for a profile, optionally filtered by date and status."""
    admin = get_supabase_admin()
    query = admin.table("reminders").select("*").eq("profile_id", profile_id)

    if date_filter:
        query = query.eq("scheduled_date", date_filter)
    if status_filter:
        query = query.eq("status", status_filter)

    query = query.order("scheduled_date").order("scheduled_time").limit(limit)
    result = query.execute()

    return [
        ReminderOut(
            id=r["id"],
            profile_id=r["profile_id"],
            label=r["label"],
            scheduled_date=r["scheduled_date"],
            scheduled_time=r["scheduled_time"],
            scheduled_utc=r.get("scheduled_utc"),
            recurrence=r.get("recurrence", "none"),
            is_medication=r.get("is_medication", False),
            status=r.get("status", "pending"),
            created_by=r.get("created_by", ""),
            created_at=r.get("created_at"),
            updated_at=r.get("updated_at"),
        )
        for r in (result.data or [])
    ]


def cancel_reminder(profile_id: str, reminder_id: str) -> ReminderOut:
    """Cancel a reminder. Verifies ownership before cancellation."""
    admin = get_supabase_admin()

    # Verify ownership
    existing = (
        admin.table("reminders")
        .select("*")
        .eq("id", reminder_id)
        .eq("profile_id", profile_id)
        .execute()
    )
    if not existing.data or len(existing.data) == 0:
        raise ValueError("Reminder not found or access denied")

    row = existing.data[0]
    if row["status"] == "cancelled":
        raise ValueError("Reminder is already cancelled")

    result = (
        admin.table("reminders")
        .update({"status": "cancelled", "updated_at": datetime.now(timezone.utc).isoformat()})
        .eq("id", reminder_id)
        .eq("profile_id", profile_id)
        .execute()
    )

    if result.data and len(result.data) > 0:
        r = result.data[0]
        return ReminderOut(
            id=r["id"],
            profile_id=r["profile_id"],
            label=r["label"],
            scheduled_date=r["scheduled_date"],
            scheduled_time=r["scheduled_time"],
            scheduled_utc=r.get("scheduled_utc"),
            recurrence=r.get("recurrence", "none"),
            is_medication=r.get("is_medication", False),
            status=r.get("status", "cancelled"),
            created_by=r.get("created_by", ""),
            created_at=r.get("created_at"),
            updated_at=r.get("updated_at"),
        )

    raise RuntimeError("Failed to cancel reminder")


def get_next_reminder(profile_id: str) -> ReminderOut | None:
    """Get the next upcoming reminder for a profile."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    admin = get_supabase_admin()
    result = (
        admin.table("reminders")
        .select("*")
        .eq("profile_id", profile_id)
        .in_("status", ["pending", "scheduled"])
        .gte("scheduled_date", today)
        .order("scheduled_date")
        .order("scheduled_time")
        .limit(1)
        .execute()
    )

    if result.data and len(result.data) > 0:
        r = result.data[0]
        return ReminderOut(
            id=r["id"],
            profile_id=r["profile_id"],
            label=r["label"],
            scheduled_date=r["scheduled_date"],
            scheduled_time=r["scheduled_time"],
            scheduled_utc=r.get("scheduled_utc"),
            recurrence=r.get("recurrence", "none"),
            is_medication=r.get("is_medication", False),
            status=r.get("status", "pending"),
            created_by=r.get("created_by", ""),
            created_at=r.get("created_at"),
            updated_at=r.get("updated_at"),
        )
    return None
