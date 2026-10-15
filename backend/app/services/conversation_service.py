"""Conversation service — orchestrates the voice/text AI pipeline.

Pipeline steps:
1. Validate input
2. Run safety check before LLM
3. Extract intent
4. Validate intent against supported actions
5. Execute approved command through domain services
6. Generate response
7. Record audit event
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.core.supabase_client import get_supabase_admin
from app.adapters.ai_adapter import extract_intent, generate_response
from app.services.reminder_service import (
    create_reminder,
    list_reminders,
    cancel_reminder,
    preview_reminder,
)
from app.services.checkin_service import submit_checkin, get_todays_checkin
from app.services.safety_service import check_safety, handle_help_request, record_audit_event
from app.schemas.models import (
    ConversationTurnRequest,
    ConversationTurnResponse,
    IntentType,
    ReminderCreateRequest,
    HelpUrgency,
)


def process_conversation_turn(
    profile_id: str,
    user_id: str,
    req: ConversationTurnRequest,
    timezone_str: str = "UTC",
) -> ConversationTurnResponse:
    """Process a single conversation turn through the full AI pipeline."""
    message = req.message.strip()
    conversation_id = req.conversation_id or str(uuid.uuid4())

    # Step 1: Validate input
    if not message:
        return ConversationTurnResponse(
            message="I didn't catch that. Could you try again?",
            intent="UNKNOWN",
            conversation_id=conversation_id,
        )

    # Step 2: Safety check BEFORE LLM processing
    safety_result = check_safety(message)

    if not safety_result.is_safe or safety_result.should_escalate:
        # Handle safety concern
        help_result = handle_help_request(
            profile_id=profile_id,
            user_id=user_id,
            message=message,
            urgency=safety_result.urgency,
        )

        _save_conversation_turn(conversation_id, profile_id, message, "user", "HELP_REQUEST")
        _save_conversation_turn(
            conversation_id, profile_id,
            help_result["message"], "assistant", "HELP_REQUEST"
        )

        return ConversationTurnResponse(
            message=help_result["message"],
            intent="HELP_REQUEST",
            action_taken="help_escalation",
            action_result=help_result,
            is_simulated=help_result.get("is_simulated", True),
            conversation_id=conversation_id,
        )

    # Step 3: Extract intent
    intent = extract_intent(message)

    # Step 4: Handle based on intent
    action_taken = None
    action_result = None
    needs_confirmation = False
    confirmation_data = None
    response_message = ""

    if intent.needs_clarification:
        response_message = intent.clarification_question or "Could you tell me more about what you need?"
        _save_conversation_turn(conversation_id, profile_id, message, "user", intent.intent.value)
        _save_conversation_turn(conversation_id, profile_id, response_message, "assistant", intent.intent.value)

        return ConversationTurnResponse(
            message=response_message,
            intent=intent.intent.value,
            conversation_id=conversation_id,
        )

    if intent.intent == IntentType.REMINDER_CREATE:
        response_message, action_taken, action_result, needs_confirmation, confirmation_data = (
            _handle_reminder_create(profile_id, user_id, intent, timezone_str)
        )

    elif intent.intent == IntentType.REMINDER_LIST:
        response_message, action_taken, action_result = _handle_reminder_list(
            profile_id, intent
        )

    elif intent.intent == IntentType.REMINDER_CANCEL:
        response_message, action_taken, action_result = _handle_reminder_cancel(
            profile_id, intent
        )

    elif intent.intent == IntentType.CHECKIN_RESPONSE:
        response_message, action_taken, action_result = _handle_checkin_response(
            profile_id, user_id, intent
        )

    elif intent.intent == IntentType.HELP_REQUEST:
        help_result = handle_help_request(
            profile_id=profile_id,
            user_id=user_id,
            message=message,
            urgency=HelpUrgency.MEDIUM,
        )
        response_message = help_result["message"]
        action_taken = "help_request"
        action_result = help_result

    else:
        # General question — generate conversational response
        response_message = generate_response(message, intent)
        action_taken = None

    # Record conversation
    _save_conversation_turn(conversation_id, profile_id, message, "user", intent.intent.value)
    _save_conversation_turn(
        conversation_id, profile_id, response_message, "assistant",
        intent.intent.value, action_taken
    )

    # Record audit event
    record_audit_event(
        profile_id=profile_id,
        user_id=user_id,
        event_type="conversation_turn",
        description=f"Intent: {intent.intent.value}",
        metadata={"intent": intent.intent.value, "action": action_taken},
    )

    return ConversationTurnResponse(
        message=response_message,
        intent=intent.intent.value,
        action_taken=action_taken,
        action_result=action_result,
        needs_confirmation=needs_confirmation,
        confirmation_data=confirmation_data,
        conversation_id=conversation_id,
    )


def _handle_reminder_create(
    profile_id: str,
    user_id: str,
    intent,
    timezone_str: str,
) -> tuple:
    """Handle reminder creation intent."""
    entities = intent.entities

    label = entities.get("label", "")
    date = entities.get("date", "")
    time = entities.get("time", "")
    is_medication = entities.get("is_medication", False)
    recurrence = entities.get("recurrence", "none")

    if not label or not date or not time:
        return (
            "I'd like to help set a reminder. Could you tell me what to remind you about, and when?",
            None, None, False, None,
        )

    # Generate preview
    req = ReminderCreateRequest(
        label=label,
        scheduled_date=date,
        scheduled_time=time,
        recurrence=recurrence,
        is_medication=is_medication,
        confirmed=False,
    )

    preview = preview_reminder(req, timezone_str)

    return (
        f"I'll set a reminder: \"{label}\" on {preview.local_datetime_display}. Shall I go ahead?",
        None,
        None,
        True,
        {
            "label": label,
            "scheduled_date": date,
            "scheduled_time": time,
            "recurrence": recurrence,
            "is_medication": is_medication,
            "display": preview.local_datetime_display,
        },
    )


def _handle_reminder_list(profile_id: str, intent) -> tuple:
    """Handle reminder list intent."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    reminders = list_reminders(profile_id)

    reminder_list = [
        {
            "id": r.id,
            "label": r.label,
            "date": r.scheduled_date,
            "time": r.scheduled_time,
            "status": r.status,
            "is_medication": r.is_medication,
        }
        for r in reminders
    ]

    result = {"reminders": reminder_list, "total": len(reminder_list)}
    response = generate_response(intent.raw_text, intent, result)

    return response, "list_reminders", result


def _handle_reminder_cancel(profile_id: str, intent) -> tuple:
    """Handle reminder cancellation intent."""
    label_to_cancel = intent.entities.get("label", "")

    if not label_to_cancel:
        return (
            "Which reminder would you like to cancel? You can tell me the name or description.",
            None, None,
        )

    # Find matching reminders
    reminders = list_reminders(profile_id)
    matching = [
        r for r in reminders
        if label_to_cancel.lower() in r.label.lower()
        and r.status not in ("cancelled", "delivered")
    ]

    if not matching:
        return (
            f"I couldn't find an active reminder matching \"{label_to_cancel}\". "
            "Would you like to see your current reminders?",
            None, None,
        )

    if len(matching) == 1:
        cancelled = cancel_reminder(profile_id, matching[0].id)
        return (
            f"I've cancelled the reminder: \"{cancelled.label}\".",
            "cancel_reminder",
            {"cancelled_id": cancelled.id, "label": cancelled.label},
        )

    # Multiple matches — ask for clarification
    labels = ", ".join(f'"{r.label}"' for r in matching[:5])
    return (
        f"I found several matching reminders: {labels}. Which one would you like to cancel?",
        None, None,
    )


def _handle_checkin_response(profile_id: str, user_id: str, intent) -> tuple:
    """Handle check-in response."""
    response_val = intent.entities.get("response", "okay")
    notes = intent.entities.get("notes", "")

    checkin = get_todays_checkin(profile_id)
    if not checkin:
        return (
            "You don't have a check-in scheduled for today.",
            None, None,
        )

    if checkin.get("status") == "completed":
        return (
            "You've already completed today's check-in. Thank you!",
            None, None,
        )

    try:
        result = submit_checkin(
            profile_id=profile_id,
            checkin_id=checkin["id"],
            response=response_val,
            notes=notes,
            user_id=user_id,
        )

        if response_val == "need_help":
            return (
                "I've recorded that you need help. I'm reaching out to your trusted contacts. "
                "If this is an emergency, please call your local emergency number.",
                "checkin_escalation",
                result,
            )
        elif response_val == "skip":
            return (
                "No problem, I'll skip today's check-in. See you next time!",
                "checkin_skip",
                result,
            )
        else:
            return (
                "Great to hear you're doing well! Thank you for checking in.",
                "checkin_complete",
                result,
            )

    except ValueError as e:
        return (str(e), None, None)


def _save_conversation_turn(
    conversation_id: str,
    profile_id: str,
    content: str,
    role: str,
    intent: str | None = None,
    action_taken: str | None = None,
) -> None:
    """Save a conversation turn to the database."""
    try:
        admin = get_supabase_admin()

        # Ensure conversation exists
        existing = (
            admin.table("conversations")
            .select("id")
            .eq("id", conversation_id)
            .execute()
        )

        if not existing.data or len(existing.data) == 0:
            admin.table("conversations").insert({
                "id": conversation_id,
                "profile_id": profile_id,
            }).execute()

        # Save turn (don't store full conversation content for privacy)
        turn_id = str(uuid.uuid4())
        admin.table("conversation_turns").insert({
            "id": turn_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": content[:500],  # Truncate for privacy
            "intent": intent,
            "action_taken": action_taken,
        }).execute()
    except Exception:
        pass  # Non-critical — don't fail the conversation
