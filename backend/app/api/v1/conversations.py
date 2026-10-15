"""Conversation / AI assistant endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends, status

from app.core.auth import get_current_user, AuthenticatedUser
from app.core.supabase_client import get_supabase_admin
from app.services.conversation_service import process_conversation_turn
from app.services.reminder_service import create_reminder
from app.services.safety_service import record_audit_event
from app.schemas.models import (
    ConversationTurnRequest,
    ConversationTurnResponse,
    ReminderCreateRequest,
)

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/chat", response_model=ConversationTurnResponse)
async def chat(
    req: ConversationTurnRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Process a conversation turn through the AI pipeline."""
    if not user.profile_id:
        raise HTTPException(status_code=404, detail="No senior profile found")

    admin = get_supabase_admin()
    profile = admin.table("senior_profiles").select("timezone").eq("id", user.profile_id).execute()
    tz = profile.data[0]["timezone"] if profile.data else "UTC"

    result = process_conversation_turn(
        profile_id=user.profile_id,
        user_id=user.id,
        req=req,
        timezone_str=tz,
    )

    return result


@router.post("/confirm-reminder", response_model=ConversationTurnResponse)
async def confirm_reminder(
    data: dict,
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Confirm a reminder that was previously previewed in conversation."""
    if not user.profile_id:
        raise HTTPException(status_code=404, detail="No senior profile found")

    label = data.get("label", "")
    scheduled_date = data.get("scheduled_date", "")
    scheduled_time = data.get("scheduled_time", "")
    recurrence = data.get("recurrence", "none")
    is_medication = data.get("is_medication", False)

    if not label or not scheduled_date or not scheduled_time:
        raise HTTPException(status_code=400, detail="Missing reminder details")

    admin = get_supabase_admin()
    profile = admin.table("senior_profiles").select("timezone").eq("id", user.profile_id).execute()
    tz = profile.data[0]["timezone"] if profile.data else "UTC"

    try:
        req = ReminderCreateRequest(
            label=label,
            scheduled_date=scheduled_date,
            scheduled_time=scheduled_time,
            recurrence=recurrence,
            is_medication=is_medication,
            confirmed=True,
        )

        reminder = create_reminder(
            profile_id=user.profile_id,
            req=req,
            created_by=user.id,
            timezone=tz,
        )

        record_audit_event(
            profile_id=user.profile_id,
            user_id=user.id,
            event_type="reminder_confirmed_via_voice",
            description=f"Voice-confirmed reminder: {label}",
            metadata={"reminder_id": reminder.id},
        )

        return ConversationTurnResponse(
            message=f"Done! I've set your reminder: \"{label}\" on {scheduled_date} at {scheduled_time}.",
            intent="REMINDER_CREATE",
            action_taken="reminder_created",
            action_result={"reminder_id": reminder.id, "label": label},
            conversation_id=data.get("conversation_id", ""),
        )

    except Exception as e:
        return ConversationTurnResponse(
            message=f"I wasn't able to create that reminder. {str(e)}",
            intent="REMINDER_CREATE",
            action_taken="reminder_failed",
            conversation_id=data.get("conversation_id", ""),
        )
