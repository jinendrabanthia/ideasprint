"""AI adapter — provider-independent LLM interface using Google Gemini.

Handles:
- Intent extraction from natural language
- Structured output validation
- Response generation
- Fallback behavior when the model is unavailable

IMPORTANT: The LLM assists with natural language understanding. It does NOT
execute arbitrary commands, generate SQL, or act as an unrestricted controller.
All extracted intents are validated against a strict schema before execution.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone

from app.core.config import settings
from app.schemas.models import IntentType, ParsedIntent


# System prompt for the elder care companion
SYSTEM_PROMPT = """You are a kind, patient AI companion helping an older adult with their daily routine. 
You are NOT a doctor, emergency service, or medical professional. Never diagnose conditions or provide medical advice.

Your capabilities:
1. REMINDER_CREATE - Help create reminders (medication schedules they or caregivers have entered, appointments, tasks)
2. REMINDER_LIST - Show upcoming reminders
3. REMINDER_CANCEL - Cancel a specific reminder
4. CHECKIN_RESPONSE - Respond to a daily wellness check-in
5. HELP_REQUEST - The person needs help or assistance
6. GENERAL_QUESTION - General conversation or questions

When responding:
- Use simple, clear language
- Be warm but not condescending
- Keep responses brief
- If asked about medications, remind them of their schedule but NEVER prescribe, recommend doses, or change schedules
- If someone seems to be in distress, prioritize connecting them with help

For intent extraction, respond ONLY with valid JSON in this exact format:
{
  "intent": "INTENT_TYPE",
  "confidence": 0.0-1.0,
  "entities": {},
  "needs_clarification": false,
  "clarification_question": ""
}

For REMINDER_CREATE entities, extract:
- "label": description of the reminder
- "date": YYYY-MM-DD format (use today's date context)
- "time": HH:MM in 24h format
- "is_medication": true/false
- "recurrence": "none", "daily", or "weekly"

For REMINDER_CANCEL entities, extract:
- "label": what reminder to cancel (partial match is ok)

For CHECKIN_RESPONSE entities, extract:
- "response": "okay", "skip", or "need_help"
- "notes": any additional context

Today's date is: {today}
"""


def _get_gemini_client():
    """Initialize and return the Gemini client."""
    try:
        from google import genai
        client = genai.Client(api_key=settings.gemini_api_key)
        return client
    except Exception:
        return None


def extract_intent(text: str) -> ParsedIntent:
    """Extract intent from user text using Gemini, with deterministic fallback.

    First attempts rule-based extraction for simple commands,
    then falls back to LLM for natural language understanding.
    """
    # Try deterministic extraction first for simple commands
    deterministic = _deterministic_intent(text)
    if deterministic and deterministic.confidence > 0.8:
        return deterministic

    # Try LLM extraction
    try:
        client = _get_gemini_client()
        if client is None:
            return deterministic or ParsedIntent(
                intent=IntentType.UNKNOWN,
                raw_text=text,
                confidence=0.0,
            )

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        prompt = SYSTEM_PROMPT.format(today=today)

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                {"role": "user", "parts": [{"text": f"{prompt}\n\nUser says: \"{text}\"\n\nExtract the intent as JSON only."}]},
            ],
        )

        if response and response.text:
            return _parse_llm_response(response.text, text)

    except Exception as e:
        # LLM unavailable — use deterministic fallback
        pass

    return deterministic or ParsedIntent(
        intent=IntentType.GENERAL_QUESTION,
        raw_text=text,
        confidence=0.3,
    )


def generate_response(
    message: str,
    intent: ParsedIntent,
    action_result: dict | None = None,
    conversation_history: list[dict] | None = None,
) -> str:
    """Generate a conversational response using Gemini."""
    try:
        client = _get_gemini_client()
        if client is None:
            return _fallback_response(intent, action_result)

        context = f"""You are a warm, patient AI companion for an older adult.
You are NOT a doctor or emergency service. Keep responses brief, clear, and friendly.
Do not use complicated words. Speak naturally.

The user said: "{message}"
Detected intent: {intent.intent.value}
"""
        if action_result:
            context += f"\nAction result: {json.dumps(action_result, default=str)}"

        if intent.intent == IntentType.REMINDER_CREATE and action_result:
            context += "\nConfirm the reminder was created successfully. Mention the label, date, and time."
        elif intent.intent == IntentType.REMINDER_LIST and action_result:
            context += "\nList the reminders in a friendly way. If empty, mention there are none."
        elif intent.intent == IntentType.REMINDER_CANCEL and action_result:
            context += "\nConfirm the reminder was cancelled."
        elif intent.intent == IntentType.HELP_REQUEST:
            context += "\nExpress concern and mention what actions were taken. Be honest about limitations."

        context += "\n\nRespond naturally in 1-3 sentences. Do not use markdown."

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                {"role": "user", "parts": [{"text": context}]},
            ],
        )

        if response and response.text:
            return response.text.strip()

    except Exception:
        pass

    return _fallback_response(intent, action_result)


def _deterministic_intent(text: str) -> ParsedIntent | None:
    """Rule-based intent extraction for simple, unambiguous commands."""
    text_lower = text.lower().strip()

    # Help requests
    help_phrases = ["help", "i need help", "help me", "please help", "call for help"]
    for phrase in help_phrases:
        if phrase in text_lower:
            return ParsedIntent(
                intent=IntentType.HELP_REQUEST,
                confidence=0.9,
                raw_text=text,
                entities={"message": text},
            )

    # Reminder list
    list_phrases = [
        "show my reminders", "list reminders", "what are my reminders",
        "upcoming reminders", "my reminders", "show reminders",
        "what reminders do i have", "today's reminders",
    ]
    for phrase in list_phrases:
        if phrase in text_lower:
            return ParsedIntent(
                intent=IntentType.REMINDER_LIST,
                confidence=0.95,
                raw_text=text,
            )

    # Reminder creation (simple patterns)
    create_phrases = ["remind me", "set a reminder", "create a reminder", "add a reminder", "new reminder"]
    for phrase in create_phrases:
        if phrase in text_lower:
            return ParsedIntent(
                intent=IntentType.REMINDER_CREATE,
                confidence=0.7,
                raw_text=text,
                needs_clarification=True,
                clarification_question="What would you like to be reminded about, and when?",
            )

    # Reminder cancellation
    cancel_phrases = ["cancel reminder", "remove reminder", "delete reminder", "stop reminder"]
    for phrase in cancel_phrases:
        if phrase in text_lower:
            return ParsedIntent(
                intent=IntentType.REMINDER_CANCEL,
                confidence=0.7,
                raw_text=text,
                needs_clarification=True,
                clarification_question="Which reminder would you like to cancel?",
            )

    # Check-in responses
    checkin_phrases = {
        "i'm okay": "okay", "im okay": "okay", "i am okay": "okay",
        "i'm fine": "okay", "im fine": "okay", "doing well": "okay",
        "feeling good": "okay", "i'm good": "okay",
        "skip": "skip", "not now": "skip",
        "need help": "need_help", "not feeling well": "need_help",
    }
    for phrase, response in checkin_phrases.items():
        if phrase in text_lower:
            return ParsedIntent(
                intent=IntentType.CHECKIN_RESPONSE,
                confidence=0.85,
                raw_text=text,
                entities={"response": response},
            )

    return None


def _parse_llm_response(response_text: str, original_text: str) -> ParsedIntent:
    """Parse the LLM JSON response into a validated ParsedIntent."""
    try:
        # Extract JSON from response (it may be wrapped in markdown code blocks)
        json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
        if not json_match:
            return ParsedIntent(
                intent=IntentType.GENERAL_QUESTION,
                raw_text=original_text,
                confidence=0.3,
            )

        data = json.loads(json_match.group())

        intent_str = data.get("intent", "UNKNOWN")
        try:
            intent = IntentType(intent_str)
        except ValueError:
            intent = IntentType.UNKNOWN

        return ParsedIntent(
            intent=intent,
            confidence=float(data.get("confidence", 0.5)),
            entities=data.get("entities", {}),
            raw_text=original_text,
            needs_clarification=data.get("needs_clarification", False),
            clarification_question=data.get("clarification_question", ""),
        )

    except (json.JSONDecodeError, KeyError, TypeError):
        return ParsedIntent(
            intent=IntentType.GENERAL_QUESTION,
            raw_text=original_text,
            confidence=0.3,
        )


def _fallback_response(intent: ParsedIntent, action_result: dict | None = None) -> str:
    """Generate a simple response when LLM is unavailable."""
    responses = {
        IntentType.REMINDER_CREATE: "Your reminder has been created successfully.",
        IntentType.REMINDER_LIST: "Here are your upcoming reminders.",
        IntentType.REMINDER_CANCEL: "The reminder has been cancelled.",
        IntentType.CHECKIN_RESPONSE: "Thank you for checking in! Your response has been recorded.",
        IntentType.HELP_REQUEST: "I've recorded your help request and will try to notify your trusted contacts.",
        IntentType.GENERAL_QUESTION: "I'm here to help with reminders, check-ins, and daily care. What can I do for you?",
        IntentType.UNKNOWN: "I'm not sure I understood that. Could you try saying it differently?",
    }

    base = responses.get(intent.intent, responses[IntentType.UNKNOWN])

    if action_result and intent.intent == IntentType.REMINDER_LIST:
        reminders = action_result.get("reminders", [])
        if not reminders:
            return "You don't have any upcoming reminders right now."
        count = len(reminders)
        return f"You have {count} reminder{'s' if count != 1 else ''} coming up."

    return base
