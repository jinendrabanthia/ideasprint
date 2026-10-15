"""Request and response schemas for the API."""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────

class UserRole(str, Enum):
    SENIOR = "senior"
    CAREGIVER = "caregiver"
    ADMIN = "admin"


class ReminderStatus(str, Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CheckInStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    MISSED = "missed"
    ESCALATED = "escalated"


class CheckInResponse(str, Enum):
    OKAY = "okay"
    SKIP = "skip"
    NEED_HELP = "need_help"


class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    SIMULATED = "simulated"


class IntentType(str, Enum):
    REMINDER_CREATE = "REMINDER_CREATE"
    REMINDER_LIST = "REMINDER_LIST"
    REMINDER_CANCEL = "REMINDER_CANCEL"
    CHECKIN_RESPONSE = "CHECKIN_RESPONSE"
    HELP_REQUEST = "HELP_REQUEST"
    GENERAL_QUESTION = "GENERAL_QUESTION"
    UNKNOWN = "UNKNOWN"


class HelpUrgency(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EMERGENCY = "emergency"


# ── Auth Schemas ───────────────────────────────────────

class SignUpRequest(BaseModel):
    email: str
    password: str
    display_name: str = ""
    role: UserRole = UserRole.SENIOR


class SignInRequest(BaseModel):
    email: str
    password: str


class GoogleAuthRequest(BaseModel):
    id_token: str | None = None
    email: str | None = None
    display_name: str | None = None
    google_id: str | None = None
    role: UserRole = UserRole.SENIOR



class AuthResponse(BaseModel):
    access_token: str
    user_id: str
    email: str
    role: str
    profile_id: str | None = None
    display_name: str = ""


# ── User & Profile Schemas ─────────────────────────────

class UserOut(BaseModel):
    id: str
    email: str
    role: str
    display_name: str = ""
    created_at: str | None = None


class SeniorProfileOut(BaseModel):
    id: str
    user_id: str
    display_name: str = ""
    timezone: str = "UTC"
    language: str = "en"
    speech_rate: float = 1.0
    high_contrast: bool = False
    large_text: bool = False
    onboarding_complete: bool = False
    created_at: str | None = None


class ProfileUpdateRequest(BaseModel):
    display_name: str | None = None
    timezone: str | None = None
    language: str | None = None
    speech_rate: float | None = None
    high_contrast: bool | None = None
    large_text: bool | None = None
    onboarding_complete: bool | None = None


# ── Reminder Schemas ───────────────────────────────────

class ReminderCreateRequest(BaseModel):
    label: str = Field(..., min_length=1, max_length=500)
    scheduled_date: str  # ISO date string YYYY-MM-DD
    scheduled_time: str  # HH:MM (24h)
    recurrence: str = "none"  # "none", "daily", "weekly"
    is_medication: bool = False
    confirmed: bool = False  # Must be True to actually create


class ReminderPreview(BaseModel):
    """Preview of a reminder before confirmation."""
    label: str
    scheduled_date: str
    scheduled_time: str
    local_datetime_display: str
    recurrence: str = "none"
    is_medication: bool = False
    needs_confirmation: bool = True


class ReminderOut(BaseModel):
    id: str
    profile_id: str
    label: str
    scheduled_date: str
    scheduled_time: str
    scheduled_utc: str | None = None
    recurrence: str = "none"
    is_medication: bool = False
    status: str = "pending"
    created_by: str = ""
    created_at: str | None = None
    updated_at: str | None = None


class ReminderListResponse(BaseModel):
    reminders: list[ReminderOut]
    total: int


# ── Check-in Schemas ──────────────────────────────────

class CheckInConfigRequest(BaseModel):
    enabled: bool = True
    time: str = "09:00"  # HH:MM
    questions: list[str] = Field(
        default=["How are you feeling today?"]
    )


class CheckInSubmitRequest(BaseModel):
    checkin_id: str
    response: CheckInResponse
    notes: str = ""


class CheckInOut(BaseModel):
    id: str
    profile_id: str
    scheduled_time: str
    status: str = "pending"
    response: str | None = None
    notes: str = ""
    escalated: bool = False
    created_at: str | None = None
    responded_at: str | None = None


# ── Help & Safety Schemas ─────────────────────────────

class HelpRequest(BaseModel):
    message: str = ""
    urgency: HelpUrgency = HelpUrgency.MEDIUM


class HelpResponse(BaseModel):
    message: str
    urgency: str
    actions_taken: list[str]
    notification_status: str
    is_simulated: bool = True
    emergency_note: str = ""


class SafetyCheckResult(BaseModel):
    is_safe: bool = True
    urgency: HelpUrgency = HelpUrgency.LOW
    safety_response: str | None = None
    should_escalate: bool = False
    keywords_matched: list[str] = []


# ── Conversation / AI Schemas ─────────────────────────

class ConversationTurnRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    is_voice: bool = False
    conversation_id: str | None = None


class ParsedIntent(BaseModel):
    intent: IntentType
    confidence: float = 0.0
    entities: dict[str, Any] = {}
    raw_text: str = ""
    needs_clarification: bool = False
    clarification_question: str = ""


class ConversationTurnResponse(BaseModel):
    message: str
    intent: str = "GENERAL_QUESTION"
    action_taken: str | None = None
    action_result: dict[str, Any] | None = None
    needs_confirmation: bool = False
    confirmation_data: dict[str, Any] | None = None
    is_simulated: bool = False
    conversation_id: str = ""


# ── Trusted Contact Schemas ───────────────────────────

class TrustedContactCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    phone: str = ""
    email: str = ""
    relationship: str = ""
    is_emergency: bool = False
    notify_on_help: bool = True
    notify_on_missed_checkin: bool = True


class TrustedContactOut(BaseModel):
    id: str
    profile_id: str
    name: str
    phone: str = ""
    email: str = ""
    relationship: str = ""
    is_emergency: bool = False
    notify_on_help: bool = True
    notify_on_missed_checkin: bool = True
    created_at: str | None = None


# ── Caregiver Schemas ─────────────────────────────────

class CaregiverRelationshipRequest(BaseModel):
    senior_profile_id: str
    permissions: list[str] = Field(
        default=["view_reminders", "view_checkins", "manage_reminders"]
    )


class CaregiverRelationshipOut(BaseModel):
    id: str
    caregiver_user_id: str
    senior_profile_id: str
    status: str = "active"
    permissions: list[str] = []
    created_at: str | None = None


class CaregiverDashboardData(BaseModel):
    senior_profiles: list[SeniorProfileOut]
    relationships: list[CaregiverRelationshipOut]


# ── Notification Schemas ──────────────────────────────

class NotificationOut(BaseModel):
    id: str
    profile_id: str
    type: str  # "reminder", "checkin", "help", "escalation"
    message: str
    status: str
    is_simulated: bool = True
    recipient: str = ""
    created_at: str | None = None
    delivered_at: str | None = None


# ── Audit Event Schemas ──────────────────────────────

class AuditEventOut(BaseModel):
    id: str
    profile_id: str
    event_type: str
    description: str
    metadata: dict[str, Any] = {}
    created_at: str | None = None


# ── Common ────────────────────────────────────────────

class ErrorResponse(BaseModel):
    detail: str
    correlation_id: str = ""


class HealthCheck(BaseModel):
    status: str = "healthy"
    version: str = "0.1.0"
    database: str = "connected"
