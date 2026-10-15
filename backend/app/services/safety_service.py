"""Safety router — evaluates utterances for safety concerns before normal processing.

This module provides:
- Keyword-based safety detection (limited safeguard, not diagnostic).
- Urgency classification.
- Controlled response templates.
- Escalation workflow routing.

IMPORTANT: This module does NOT diagnose medical conditions, replace
emergency services, or provide medical advice. It is a limited
safeguard that routes potential urgent situations to human help.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.core.supabase_client import get_supabase_admin
from app.schemas.models import HelpUrgency, SafetyCheckResult


# Safety keyword categories — these are limited safeguards, not reliable detection
EMERGENCY_KEYWORDS = [
    "can't breathe", "cant breathe", "not breathing",
    "chest pain", "heart attack", "stroke",
    "unconscious", "passed out", "fainted",
    "bleeding badly", "severe bleeding",
    "fell down", "fallen", "i fell", "collapsed", "collapse", "on the floor",
    "call ambulance", "call 911", "call 112", "emergency",
    "help me", "please help", "need help now",
    "numb", "numbness", "arm is numb", "face is drooping",
    "i'm dying", "im dying",
]

HIGH_URGENCY_KEYWORDS = [
    "dizzy", "dizziness", "confused", "disoriented",
    "pain", "hurting", "hurt", "injured",
    "sick", "nauseous", "vomiting",
    "can't move", "cant move", "stuck",
    "scared", "afraid", "frightened",
    "feel bad", "feeling bad", "not well",
    "forgot medication", "missed medication",
    "lost", "don't know where i am",
]

MEDIUM_URGENCY_KEYWORDS = [
    "tired", "exhausted", "weak",
    "lonely", "sad", "upset",
    "worried", "anxious", "nervous",
    "headache", "stomach ache",
    "can't sleep", "cant sleep",
]

# Controlled response templates
SAFETY_RESPONSES = {
    HelpUrgency.EMERGENCY: (
        "I hear that you need urgent help. Your safety is the most important thing. "
        "If you believe you are in immediate danger, please call your local emergency "
        "number (such as 112 or 911) right away, or ask someone nearby to help you. "
        "I am not an emergency service and cannot guarantee help will arrive. "
        "I will attempt to notify your emergency contact if one is configured."
    ),
    HelpUrgency.HIGH: (
        "I'm concerned about what you're describing. I want to make sure you're safe. "
        "Would you like me to notify your trusted contact? If you feel this is an "
        "emergency, please call your local emergency number right away. "
        "I am not a doctor and cannot diagnose what's happening."
    ),
    HelpUrgency.MEDIUM: (
        "I understand you're not feeling your best. I'm here to help in the ways I can. "
        "Would you like me to reach out to your trusted contact, or is there something "
        "else I can help with?"
    ),
    HelpUrgency.LOW: None,  # No safety intervention needed
}


def check_safety(text: str) -> SafetyCheckResult:
    """Evaluate an utterance for safety concerns.

    Returns a SafetyCheckResult with urgency level and recommended response.
    This is a keyword-based heuristic — a limited safeguard, not reliable
    medical diagnosis or guaranteed emergency detection.
    """
    text_lower = text.lower().strip()
    matched_keywords = []

    # Check emergency keywords first
    for keyword in EMERGENCY_KEYWORDS:
        if keyword in text_lower:
            matched_keywords.append(keyword)

    if matched_keywords:
        return SafetyCheckResult(
            is_safe=False,
            urgency=HelpUrgency.EMERGENCY,
            safety_response=SAFETY_RESPONSES[HelpUrgency.EMERGENCY],
            should_escalate=True,
            keywords_matched=matched_keywords,
        )

    # Check high urgency
    for keyword in HIGH_URGENCY_KEYWORDS:
        if keyword in text_lower:
            matched_keywords.append(keyword)

    if matched_keywords:
        return SafetyCheckResult(
            is_safe=False,
            urgency=HelpUrgency.HIGH,
            safety_response=SAFETY_RESPONSES[HelpUrgency.HIGH],
            should_escalate=True,
            keywords_matched=matched_keywords,
        )

    # Check medium urgency
    for keyword in MEDIUM_URGENCY_KEYWORDS:
        if keyword in text_lower:
            matched_keywords.append(keyword)

    if matched_keywords:
        return SafetyCheckResult(
            is_safe=True,
            urgency=HelpUrgency.MEDIUM,
            safety_response=SAFETY_RESPONSES[HelpUrgency.MEDIUM],
            should_escalate=False,
            keywords_matched=matched_keywords,
        )

    return SafetyCheckResult(
        is_safe=True,
        urgency=HelpUrgency.LOW,
        safety_response=None,
        should_escalate=False,
        keywords_matched=[],
    )


def handle_help_request(
    profile_id: str,
    user_id: str,
    message: str,
    urgency: HelpUrgency = HelpUrgency.MEDIUM,
) -> dict:
    """Process a help request through the escalation workflow.

    1. Log the help request as an audit event.
    2. Find configured trusted contacts.
    3. Attempt notification (mock or real).
    4. Record notification outcome.
    5. Return truthful status.
    """
    admin = get_supabase_admin()
    actions_taken = []
    notification_status = "no_contacts_configured"
    is_simulated = True

    # 1. Record audit event
    audit_id = str(uuid.uuid4())
    admin.table("audit_events").insert({
        "id": audit_id,
        "profile_id": profile_id,
        "user_id": user_id,
        "event_type": "help_request",
        "description": f"Help request with urgency: {urgency.value}",
        "metadata": {
            "urgency": urgency.value,
            "message_length": len(message),
            "has_message": bool(message),
        },
    }).execute()
    actions_taken.append("Help request recorded")

    # 2. Find trusted contacts
    contacts_result = (
        admin.table("trusted_contacts")
        .select("*")
        .eq("profile_id", profile_id)
        .eq("notify_on_help", True)
        .execute()
    )

    contacts = contacts_result.data or []

    if urgency == HelpUrgency.EMERGENCY:
        # Also get emergency-specific contacts
        emergency_result = (
            admin.table("trusted_contacts")
            .select("*")
            .eq("profile_id", profile_id)
            .eq("is_emergency", True)
            .execute()
        )
        emergency_contacts = emergency_result.data or []
        contact_ids = {c["id"] for c in contacts}
        for ec in emergency_contacts:
            if ec["id"] not in contact_ids:
                contacts.append(ec)

    if not contacts:
        actions_taken.append("No trusted contacts configured for notification")
        emergency_note = (
            "No trusted contacts are configured. If you need immediate help, "
            "please call your local emergency number."
        )
    else:
        emergency_note = ""
        for contact in contacts:
            # Create notification record
            notif_id = str(uuid.uuid4())
            admin.table("notifications").insert({
                "id": notif_id,
                "profile_id": profile_id,
                "type": "help" if urgency != HelpUrgency.EMERGENCY else "escalation",
                "message": f"Help request from senior: {urgency.value} urgency",
                "status": "simulated",
                "is_simulated": True,
                "recipient": contact.get("name", "Unknown"),
                "metadata": {
                    "contact_id": contact["id"],
                    "contact_phone": contact.get("phone", ""),
                    "urgency": urgency.value,
                },
            }).execute()

            actions_taken.append(
                f"[SIMULATED] Notification sent to {contact.get('name', 'contact')}"
            )
            notification_status = "simulated"

    safety_check = check_safety(message)
    response_message = safety_check.safety_response or SAFETY_RESPONSES[HelpUrgency.MEDIUM]

    return {
        "message": response_message,
        "urgency": urgency.value,
        "actions_taken": actions_taken,
        "notification_status": notification_status,
        "is_simulated": is_simulated,
        "emergency_note": emergency_note,
    }


def record_audit_event(
    profile_id: str,
    user_id: str,
    event_type: str,
    description: str,
    metadata: dict | None = None,
) -> str:
    """Record a minimal, privacy-conscious audit event."""
    admin = get_supabase_admin()
    event_id = str(uuid.uuid4())
    admin.table("audit_events").insert({
        "id": event_id,
        "profile_id": profile_id,
        "user_id": user_id,
        "event_type": event_type,
        "description": description,
        "metadata": metadata or {},
    }).execute()
    return event_id
