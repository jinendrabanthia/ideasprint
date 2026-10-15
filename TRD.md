Technical Requirements Document (TRD)
AI_FOR_ELDERS --- Voice AI Companion for Senior Daily Care
Document status: Hackathon implementation specification
Version: 1.0
Date: 15 October 2026
Companion document: PRD_AI_FOR_ELDERS.md

1. Technical Summary
AI_FOR_ELDERS is a voice-first application with a backend that
coordinates speech input, intent extraction, reminder workflows, safety
routing, text-to-speech, caregiver notifications, and audit events.
The architecture must keep deterministic application logic in
control. A language model may help interpret a request or generate a
short response, but it must not independently execute database changes,
contact caregivers, make medical decisions, or bypass authorization and
safety checks.
Recommended hackathon stack

- Frontend: React + TypeScript + Vite; accessible responsive UI.
- Backend API: Python 3.11+ with FastAPI and Pydantic.
- Database: PostgreSQL for a multi-user deployment; SQLite only
  for a local demo with explicit limitations.
- ORM/migrations: SQLAlchemy 2.x + Alembic.
- Voice: browser speech APIs for fastest prototype, or a
  replaceable STT/TTS provider adapter. Browser support and language
  coverage must be verified on the target demo device.
- LLM: provider-agnostic adapter for intent parsing and
  constrained conversational responses. Keep model calls behind
  backend interfaces.
- Scheduling: APScheduler for a single-instance demo; use a
  durable queue/managed scheduler for production.
- Notifications: adapter interface with a sandbox/mock
  implementation first; integrate email/SMS only after credentials and
  consent are configured.
- Testing: pytest, FastAPI TestClient/httpx, frontend unit tests,
  Playwright for critical journeys.
- Deployment: Vercel or equivalent for frontend; a Python-capable
  host for API; managed PostgreSQL for shared multi-user demo.
This is a recommended default, not a requirement to use every service.
Keep integrations replaceable to avoid vendor lock-in.

2. Architecture
Senior / Caregiver
        |
        v
Accessible React UI

- push-to-talk
- transcript / confirmation
- reminder and check-in views
        |
        v
FastAPI API Gateway
- authentication
- authorization / profile scope
- request validation
        |
        v
Application Services
  |          |             |
  v          v             v
Safety    Intent &       Reminder /
Router    Response       Check-in Service
  |       Adapter          |
  |          |             v
  |          |          PostgreSQL
  |          |
  v          v
Escalation   STT/TTS Adapter
Service         |
  |             v
  v          Spoken Response
Notification Adapter
  |
  v
Email/SMS/Test Sandbox

All significant actions -> Audit Event Service
Architectural rules

1. All data access occurs through backend services; the browser never
   connects directly to the database.
2. Authentication identifies the actor. Authorization independently
   verifies access to the requested senior profile.
3. The safety router runs before general conversational generation for
   every incoming utterance.
4. LLM output is treated as untrusted data and validated against a
   schema.
5. Reminder creation, cancellation, notification sending, and profile
   changes use explicit application commands.
6. External integrations are wrapped in adapters with timeouts, retries
   where appropriate, and normalized outcomes.
7. Audit events are written for security-sensitive actions and
   escalation attempts.
8. A provider timeout must not be reported as success.
9. Runtime and Environment

- Python: 3.11 or newer supported version.
- Node.js: current LTS version compatible with the selected frontend
  tooling.
- Database: PostgreSQL 15+ recommended for hosted/shared use.
- All timestamps stored in UTC; each profile stores an IANA timezone
  such as Asia/Kolkata.
- Environment-specific configuration must be provided through
  environment variables or a secrets manager.
- Secrets must never be committed to Git, embedded in frontend
  bundles, or written to application logs.
- Pin dependencies with a lockfile and use reproducible setup
  instructions.
- Separate development, test, and production configuration.
Example repository layout:
ai-for-elders/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── features/voice/
│   │   ├── features/reminders/
│   │   ├── features/checkins/
│   │   ├── features/caregiver/
│   │   ├── lib/api.ts
│   │   └── routes/
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   │   ├── safety_router.py
│   │   │   ├── intent_service.py
│   │   │   ├── reminder_service.py
│   │   │   ├── checkin_service.py
│   │   │   ├── escalation_service.py
│   │   │   ├── notification_service.py
│   │   │   └── audit_service.py
│   │   ├── adapters/
│   │   │   ├── llm.py
│   │   │   ├── speech_to_text.py
│   │   │   ├── text_to_speech.py
│   │   │   └── notifications.py
│   │   └── workers/
│   ├── tests/
│   ├── alembic/
│   └── pyproject.toml
├── docs/
│   ├── PRD_AI_FOR_ELDERS.md
│   └── TRD_AI_FOR_ELDERS.md
├── .env.example
├── .gitignore
└── README.md

4. Core Modules
4.1 Voice interaction module
Responsibilities: - Start and stop microphone capture through explicit
user action. - Show listening, processing, speaking, error, and idle
states. - Submit transcript or audio to the selected adapter. - Allow
transcript review and correction when needed. - Offer retry, repeat,
cancel, and non-voice fallback. - Avoid storing raw audio by default.
4.2 Intent service
Supported MVP intents: - REMINDER_CREATE - REMINDER_LIST -
REMINDER_CANCEL - CHECKIN_RESPONSE - HELP_REQUEST -
GENERAL_QUESTION - UNKNOWN
Use deterministic parsing for straightforward commands where practical.
If an LLM is used, request structured JSON and validate it using
Pydantic. Never execute arbitrary code or SQL from model output.
Example normalized intent:
{
  "intent": "REMINDER_CREATE",
  "entities": {
    "label": "prescribed medicine",
    "datetime_local": "2026-10-15T20:00:00",
    "timezone": "Asia/Kolkata"
  },
  "confidence": 0.94,
  "requires_confirmation": true
}
The confidence value above is illustrative only; do not treat
model-reported confidence as a calibrated probability. Validate
date/time, timezone, required fields, and allowed intent values
independently.
4.3 Safety router
Run before normal LLM response generation.
Recommended flow: 1. Normalize transcript for matching without
discarding the original. 2. Check deterministic high-risk phrases and
configured rules. 3. Classify request into NORMAL,
NEEDS_CLARIFICATION, URGENT_HELP, or UNKNOWN_RISK. 4. If urgent,
use a controlled safety response and invoke the escalation workflow if
consent/configuration permits. 5. If uncertain, ask a short clarifying
question or advise contacting a trusted person; do not provide a
speculative medical answer. 6. Record the rule/version, route, and
action outcome without logging unnecessary sensitive transcript content.
The rules and sample phrases must be reviewed and tested. Keyword
matching alone is not a reliable medical emergency detector and must not
be marketed as one.
4.4 Reminder service

- Parse and validate local date/time.
- Require user confirmation before persistence.
- Store the timezone and canonical UTC due time.
- Support list, cancel, update, and delivered/failed states.
- Prevent duplicate reminders where retries occur by using idempotency
  keys.
- Use a durable scheduler or database polling for production;
  in-memory timers alone are not reliable across restarts.
- Never infer a medication dose or recommend a change to a prescribed
  schedule.
4.5 Check-in service
- Create check-in schedules from explicit user/caregiver settings.
- Record COMPLETED, SKIPPED, NEEDS_HELP, or MISSED.
- A missed check-in is not proof of an emergency. Apply only the
  configured escalation policy and explain its limitations.
- Avoid repeated intrusive prompts; make cadence configurable.
4.6 Escalation and notification service
- Confirm the user has configured a trusted contact and agreed to the
  sharing behavior.
- Generate a minimal notification containing only necessary
  information.
- Return normalized status: QUEUED, SENT, DELIVERED, FAILED,
  or UNKNOWN.
- Distinguish provider acceptance from confirmed delivery.
- Apply bounded retry with backoff for transient errors; avoid
  duplicate messages using idempotency keys.
- If notification fails, state the failure clearly and tell the senior
  how to contact a person or local emergency services.
- The hackathon may use a sandbox adapter, but the UI must label
  simulated notifications as simulated.
4.7 Caregiver module
- Require authenticated caregiver identity.
- Verify the relationship/permission to the senior profile on every
  request.
- Support granting and revoking access.
- Limit caregiver views to authorized profile data.
- Log access and configuration changes.
- Do not rely on client-side role checks alone.

5. Data Model
Use UUID primary keys and UTC timestamps. The following is a logical
model; adapt fields to the chosen ORM and authentication provider.
users

- id UUID primary key
- email unique nullable, or external identity-provider subject
- display_name
- role enum: SENIOR, CAREGIVER, ADMIN
- created_at, updated_at
senior_profiles
- id UUID primary key
- user_id UUID foreign key to users.id, unique for one
  senior-owned profile
- preferred_language
- timezone
- speech_rate
- accessibility_preferences JSONB
- consent_status
- created_at, updated_at
caregiver_access
- id UUID primary key
- senior_profile_id UUID foreign key
- caregiver_user_id UUID foreign key
- permission_scope JSONB or explicit permission columns
- status enum: PENDING, ACTIVE, REVOKED
- created_at, revoked_at
- Unique constraint on active relationship as appropriate
reminders
- id UUID primary key
- senior_profile_id UUID foreign key
- created_by_user_id UUID foreign key
- label
- due_at_utc
- timezone
- status enum: PENDING, DELIVERED, CANCELLED, FAILED
- confirmation_at
- idempotency_key
- created_at, updated_at
checkins
- id UUID primary key
- senior_profile_id UUID foreign key
- scheduled_at_utc
- status enum: PENDING, COMPLETED, SKIPPED, NEEDS_HELP,
  MISSED
- response_category nullable
- completed_at
trusted_contacts
- id UUID primary key
- senior_profile_id UUID foreign key
- display_name
- channel enum: EMAIL, SMS, MOCK
- destination_encrypted or protected provider reference
- consent_status
- created_at, updated_at
notification_attempts
- id UUID primary key
- senior_profile_id UUID foreign key
- event_type
- provider
- provider_message_id nullable
- status
- attempt_count
- last_error_code nullable
- created_at, updated_at
audit_events
- id UUID primary key
- actor_user_id nullable for system actions
- senior_profile_id nullable
- event_type
- resource_type, resource_id
- outcome
- correlation_id
- created_at
- Avoid storing full transcripts or secrets in audit payloads.
Data isolation requirements
- Every profile-scoped table must be queried through an authorized
  profile scope.
- The API must verify senior_profile_id access on every request,
  including reads, updates, cancels, exports, and notification
  actions.
- Use foreign keys and indexes on all scope/relationship columns.
- Consider PostgreSQL Row-Level Security as defense in depth, but do
  not substitute it for application authorization.
- Test cross-tenant IDOR attempts using IDs belonging to a different
  user.

6. API Design
Use REST JSON APIs under /api/v1. All protected endpoints require a
valid authenticated session/token. Use a consistent error envelope and
request correlation ID.
Authentication
Prefer a managed identity provider or secure server-side session
implementation. For a hackathon demo, avoid inventing custom password
storage. If passwords are implemented, use a mature password-hashing
algorithm and secure session/token handling.
Suggested endpoints
  Method                  Endpoint                                                       Purpose
  GET                   /api/v1/me                                                   Current authenticated
                                                                                         identity and permitted
                                                                                         profile summary
  GET                   /api/v1/profiles/{profile_id}                                Read an authorized
                                                                                         senior profile
  PATCH                 /api/v1/profiles/{profile_id}/preferences                    Update permitted
                                                                                         preferences
  GET                   /api/v1/profiles/{profile_id}/reminders                      List reminders for an
                                                                                         authorized profile
  POST                  /api/v1/profiles/{profile_id}/reminders/preview              Parse request and
                                                                                         return proposed
                                                                                         reminder without saving
  POST                  /api/v1/profiles/{profile_id}/reminders                      Create confirmed
                                                                                         reminder
  PATCH                 /api/v1/profiles/{profile_id}/reminders/{reminder_id}        Update/cancel an
                                                                                         authorized reminder
  POST                  /api/v1/profiles/{profile_id}/checkins                       Submit a check-in
                                                                                         result
  POST                  /api/v1/profiles/{profile_id}/assistant/turns                Submit transcript and
                                                                                         receive response/action
                                                                                         proposal
  POST                  /api/v1/profiles/{profile_id}/help                           Start controlled
                                                                                         help/escalation
                                                                                         workflow
  GET                   /api/v1/profiles/{profile_id}/events                         View permitted event
                                                                                         history
  POST                  /api/v1/profiles/{profile_id}/caregiver-access               Request or grant access
                                                                                         according to
                                                                                         authorization policy
  DELETE                /api/v1/profiles/{profile_id}/caregiver-access/{access_id}   Revoke caregiver access
For reminder creation, separate preview from commit or use an
explicit confirmation token so the model cannot create a reminder before
the user confirms. The server must revalidate all fields at commit time.
Example response
{
  "response_text": "I understood 8:00 PM today. Should I save this reminder?",
  "response_type": "CONFIRMATION_REQUIRED",
  "proposed_action": {
    "type": "REMINDER_CREATE",
    "label": "prescribed medicine",
    "due_at_local": "2026-10-15T20:00:00",
    "timezone": "Asia/Kolkata"
  },
  "correlation_id": "server-generated-id"
}
Error codes

- 400 malformed request
- 401 unauthenticated
- 403 authenticated but not authorized
- 404 resource not found or deliberately concealed under the
  security policy
- 409 conflict/idempotency conflict
- 422 invalid fields or ambiguous action
- 429 rate limit exceeded
- 502 upstream provider failure
- 503 service unavailable
Do not reveal whether another user's private resource exists. Keep error
responses consistent to reduce enumeration.

7. Voice and AI Pipeline
Push-to-talk
   -> Speech-to-text
   -> Transcript validation
   -> Safety router
   -> Intent extraction
   -> Schema validation
   -> Clarify / confirm / execute allowed command
   -> Backend authorization + domain validation
   -> Response text
   -> Text-to-speech
   -> UI transcript and action status
Model constraints

- The model may propose a structured intent, but the backend decides
  whether it is allowed.
- Validate output against a strict schema; reject extra or malformed
  fields.
- Do not pass secrets, unrelated users' records, or entire database
  dumps to the model.
- Use only the minimum profile context required for the current task.
- Do not allow prompt instructions from user speech or retrieved
  content to override system safety policies.
- Limit response length and use a controlled response template for
  safety-related outcomes.
- Keep provider/model configuration in backend environment variables.
- Log model name/version and outcome metadata where useful, but avoid
  storing raw prompts containing sensitive data by default.

8. Security Requirements
Authentication and authorization

- Authenticate every protected request.
- Enforce object-level authorization server-side for every profile,
  reminder, check-in, contact, and event.
- Deny by default; grant the minimum permission required.
- Validate both profile access and resource ownership before
  mutations.
- Rotate/revoke sessions and tokens appropriately.
- Apply rate limits to login, voice-turn, and help/escalation
  endpoints.
Application security
- HTTPS only outside local development.
- Validate and normalize all input; use ORM parameterization and no
  string-built SQL.
- Protect against XSS, CSRF where cookie sessions are used, injection,
  insecure direct object references, and mass assignment.
- Configure CORS for explicit production origins only.
- Add security headers and safe error handling.
- Never expose provider keys or database credentials to the frontend.
- Redact secrets, contact destinations, and sensitive transcript
  content from logs.
Cross-user isolation test cases

1. User A requests User B's profile: denied.
2. User A lists reminders using User B's profile ID: denied.
3. User A cancels a reminder ID owned by User B: denied.
4. User A reads User B's event log or check-in history: denied.
5. Caregiver whose access is revoked tries again: denied immediately.
6. Altering IDs in the browser/API does not bypass backend
   authorization.
7. Cache keys and generated AI context are scoped to the authenticated
   profile.
8. Notification endpoints cannot be used to contact arbitrary
   destinations without authorization.
9. Admin access is explicit, justified, and audited; avoid unrestricted
   admin shortcuts in the demo.
10. Reliability and Failure Handling

- Set timeouts for all external calls.
- Retry only transient failures, with bounded exponential backoff and
  idempotency protection.
- Do not automatically repeat a notification indefinitely.
- Persist reminders before acknowledging successful creation.
- Use a durable scheduler for production and reconcile missed jobs
  after restart.
- Expose health checks: /health/live and /health/ready.
- Provide clear UI messages for microphone denial, network loss,
  speech failure, model timeout, and notification failure.
- A reminder must not be silently marked delivered when speech
  playback fails.
- Record failure status and allow a safe retry.
- Do not queue an emergency notification silently and then imply it
  was delivered.
 1. Observability and Audit
Track: - API request count, latency, and error rate. - Speech/LLM/TTS
provider latency and failure rate. - Reminder scheduling and delivery
outcomes. - Safety-router route and escalation outcomes. - Authorization
denials and suspicious access patterns. - Notification attempts and
provider status.
Use correlation IDs across a single assistant turn. Avoid logging raw
audio, credentials, full health-related transcripts, or unnecessary
personal data. Restrict access to logs and define retention.
 2. Testing Strategy
Unit tests

- Intent parsing for supported commands.
- Date/time parsing across timezone and daylight-saving edge cases
  where applicable.
- Reminder validation and confirmation rules.
- Safety routing rules and unknown-risk fallback.
- Notification status normalization.
- Authorization policy functions.
Integration tests
- API + database persistence.
- Reminder create/list/cancel flow.
- Confirmation token expiry and replay protection.
- Scheduler behavior across restart/retry.
- Notification sandbox response handling.
- Caregiver grant/revoke behavior.
End-to-end tests
- Voice request -> transcript -> confirmation -> saved reminder.
- Ambiguous time -> clarification, no premature save.
- Help request -> safety response -> notification attempt ->
  accurate status.
- Microphone denied -> usable fallback.
- One user cannot access another user's profile or records.
Minimum acceptance gates
- All critical unit/integration tests pass.
- No known cross-user authorization test failures.
- No reminder is persisted from an unconfirmed proposal.
- No notification success is shown for failed/unknown provider
  outcomes.
- Safety test utterances route to the intended controlled workflow.
- The app clearly communicates that it is not an emergency service or
  medical provider.
 1. Performance Targets
Initial targets for the demo, to be measured under stated test
conditions: - Typical text/API requests: p95 under 1 second excluding
external AI/speech providers. - Voice turn: report measured p50 and p95
end-to-end latency; provider latency may dominate. - Reminder list: p95
under 500 ms for a small demo dataset. - No duplicate reminder creation
under retried requests using the same idempotency key.
These are engineering targets, not measured claims. Revise them after
profiling the actual deployment.
 2. Deployment and Configuration
Example environment variables
APP_ENV=development
API_BASE_URL=<http://localhost:8000>
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/ai_for_elders
AUTH_ISSUER=
AUTH_AUDIENCE=
LLM_PROVIDER=
LLM_API_KEY=
STT_PROVIDER=
TTS_PROVIDER=
NOTIFICATION_PROVIDER=mock
NOTIFICATION_API_KEY=
FRONTEND_ORIGINS=<http://localhost:5173>
LOG_LEVEL=INFO
.env.example must contain placeholders only. Do not commit .env.
Deployment checklist

- Configure HTTPS and explicit CORS origins.
- Provision database and run Alembic migrations.
- Configure identity provider and callback URLs.
- Set secrets in host secret management.
- Configure notification provider and test mode.
- Create a test senior and caregiver with limited demo data.
- Run automated test suite and cross-user authorization tests.
- Verify microphone and speaker behavior on the actual presentation
  device.
- Verify the UI labels simulated notifications clearly.
- Confirm logs do not contain secrets or raw audio.
- Prepare a fallback demo path if a third-party AI or speech service
  is unavailable.
 1. Implementation Plan
Workstream A --- Foundation

- Repository, linting, environment configuration, database migrations.
- Authentication and profile authorization.
- Shared error format and request correlation IDs.
Workstream B --- Voice vertical slice
- Push-to-talk UI and transcription adapter.
- Intent schema and deterministic reminder commands.
- Confirmation flow and TTS response.
Workstream C --- Care workflows
- Reminder persistence, list, cancel, scheduler.
- Daily check-in.
- Trusted-contact configuration and mock notification adapter.
Workstream D --- Safety and quality
- Safety router, controlled responses, audit events.
- Authorization negative tests.
- Accessibility and failure-state testing.
- Demo script and measured metrics.
Recommended order: finish one reliable end-to-end reminder journey
first, then add the help/escalation journey, then polish accessibility
and secondary features.
 1. Technical Decisions to Confirm

- Speech stack and language(s) supported in the demo.
- Authentication provider and exact caregiver authorization model.
- Whether PostgreSQL is available or a local prototype database is
  necessary.
- Hosted LLM versus local model, based on latency, cost, privacy, and
  connectivity.
- Notification provider and whether the demo uses a sandbox.
- Deployment host, expected concurrency, and budget.
- Data retention, consent wording, and applicable legal/privacy
  requirements before a real-world pilot.
 1. Definition of Done
A feature is done only when: - Its primary path works end to end. -
Inputs are validated server-side. - Authorization is enforced
server-side. - Failure states are visible and truthful. - Relevant audit
events are written. - Automated tests cover normal, invalid, and
unauthorized cases. - The user-facing behavior meets the accessibility
and safety requirements. - Setup and configuration are documented.
