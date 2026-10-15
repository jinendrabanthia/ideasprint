Product Requirements Document (PRD)
AI_FOR_ELDERS --- Voice AI Companion for Senior Daily Care
Document status: Hackathon MVP specification
Version: 1.0
Date: 15 October 2026
Product type: Voice-first elder-care companion
Primary objective: Help older adults manage everyday routines and
feel supported through a simple, accessible, safety-aware voice
interface.

1. Executive Summary
AI_FOR_ELDERS is a voice-first AI companion designed to support older
adults with everyday routines, medication reminders, wellness check-ins,
simple information requests, and connection to a trusted caregiver when
help may be needed. It should feel calm, respectful, predictable, and
easy to use without requiring a senior to navigate complex menus or
type.
The product is not a doctor, emergency service, diagnostic tool, or
substitute for human care. It can remind, listen, guide users through
approved everyday workflows, and help contact a configured caregiver. It
must clearly communicate uncertainty and escalate potentially urgent
situations rather than inventing medical advice.
The hackathon MVP should demonstrate one coherent end-to-end journey: a
senior speaks naturally, the system understands the request, performs a
safe action (such as setting or confirming a reminder), responds in
voice, and records the event. A configured safety workflow should
demonstrate how a concerning statement triggers a clear escalation path.
2. Problem Statement
Many older adults face friction with daily routines because of complex
interfaces, forgetfulness, isolation, low digital confidence, language
barriers, or difficulty typing and reading small text. Family members
and caregivers may also lack a simple way to configure reminders and
understand whether routine check-ins have been completed.
Current voice assistants are general-purpose and may not provide an
elder-care-focused experience with accessible interaction,
caregiver-configured routines, explicit safety boundaries, and a
traceable escalation workflow.
3. Product Vision
A dependable, respectful voice companion that makes everyday care
easier while keeping older adults in control.
Product principles
4. Voice first, not voice only: voice is the primary path; large,
   simple on-screen controls provide a fallback.
5. Safety over fluency: a confident-sounding answer is not
   necessarily a safe answer.
6. Respect and autonomy: support seniors without infantilizing them
   or silently sharing more data than needed.
7. Predictable actions: confirm important changes and clearly state
   what has and has not happened.
8. Human connection: use configured caregiver escalation when
   appropriate; do not imply that AI replaces people.
9. Accessible by default: clear speech, short responses, high
   contrast, large text, and forgiving interaction.
10. Goals and Non-Goals
4.1 Goals

- Enable seniors to interact using natural spoken language.
- Create, review, and acknowledge routine reminders.
- Provide configurable daily wellness check-ins.
- Offer simple conversational assistance with safe fallback behavior.
- Allow a trusted caregiver to configure the senior profile,
  reminders, and escalation contact with consent.
- Demonstrate a deterministic safety/escalation workflow for
  concerning statements.
- Keep an auditable record of reminder actions and escalation
  attempts.
- Support a small, demonstrable MVP that can be tested live during a
  hackathon.
4.2 Non-goals for the MVP
- Medical diagnosis, treatment recommendations, or medication dosage
  decisions.
- Replacing doctors, nurses, emergency services, or in-person
  caregivers.
- Continuous passive surveillance or always-on recording.
- Automatic emergency-service dispatch unless a separately validated,
  authorized integration exists.
- Fall detection from camera/wearable sensors.
- Payment, insurance, clinical-record, or hospital-system
  integrations.
- Claims of clinical validation or guaranteed detection of
  emergencies.

5. Target Users and Personas
Primary: Older adult / senior

- May have limited experience with apps or typing.
- Wants reminders and conversation without navigating multiple
  screens.
- Needs calm, clear responses and an easy way to repeat or cancel an
  action.
Secondary: Family member / trusted caregiver
- Configures contact details and agreed reminders.
- Wants a simple view of routine completion and escalation status.
- Must only access the senior profile they are authorized to manage.
Optional: Care coordinator
- Reviews consented routine summaries and follow-up tasks.
- Not included as a separate role in the MVP unless time permits.

6. Core User Journeys
Journey A --- First-time setup
1. Senior or authorized caregiver opens the app.
1. App explains what it does, what it does not do, and what information
   may be shared.
1. Senior gives informed consent; caregiver relationship and
   permissions are verified for the prototype.
1. User selects preferred language, speech rate, wake/interaction
   method, and accessibility settings.
1. User optionally configures a trusted contact and notification
   channel.
1. App tests microphone, speaker, and a sample reminder.
1. The system confirms setup and explains how to get help.
Journey B --- Create a reminder by voice
1. Senior says: "Remind me to take my prescribed medicine at eight
   tonight."
1. App transcribes speech and extracts the reminder intent, time, and
   optional label.
1. If the time or intent is ambiguous, the app asks a short
   clarification.
1. App reads back the proposed reminder.
1. Senior confirms or cancels.
1. App saves the reminder and speaks a confirmation.
1. At the scheduled time, app delivers the reminder and records
   delivery status.
Safety constraint: the app may remind a user about a schedule
supplied by the user/caregiver, but must not recommend or alter
medication, dosage, or timing based on medical judgment.
Journey C --- Daily check-in
1. At a configured time, the app asks a short check-in question.
1. Senior answers using voice or a simple on-screen response.
1. The app records only the minimum necessary status.
1. If the answer indicates a possible immediate danger or urgent need,
   the safety flow takes priority.
1. Otherwise, the app closes with a supportive, non-judgmental
   response.
Journey D --- Request for help
1. Senior says something such as "I need help" or "I feel very unwell."
1. The system classifies the request using explicit safety rules plus
   language understanding.
1. It asks only essential clarifying questions when safe to do so.
1. It states the next action plainly.
1. Where configured and consented, it attempts to notify the trusted
   contact and records success/failure.
1. It instructs the user to contact local emergency services for
   immediate danger; it must not falsely claim emergency services have
   been contacted.
Journey E --- Caregiver setup and review
1. Authorized caregiver signs in.
1. Caregiver selects only the senior profile they are permitted to
   manage.
1. Caregiver configures reminders, check-in schedule, language, and
   trusted contact.
1. Caregiver views recent reminder delivery and check-in status.
1. Access and changes are logged.
1. Functional Requirements
Priority definitions: P0 = essential for demo/MVP; P1 = valuable
if time permits; P2 = future release.
  ID               Requirement                   Priority Acceptance criteria
  FR-01            Voice input                         P0 User can start/stop
                                                          listening
                                                          intentionally;
                                                          visible listening
                                                          state is shown;
                                                          failures offer retry
                                                          or text/tap fallback.
  FR-02            Speech                              P0 Spoken request is
                   transcription                          converted to text;
                                                          the UI can show the
                                                          interpreted text for
                                                          confirmation when
                                                          appropriate.
  FR-03            Intent and                          P0 At minimum, identify
                   entity                                 reminder
                   extraction                             create/list/cancel,
                                                          check-in response,
                                                          general question, and
                                                          help request.
  FR-04            Reminder                            P0 Reminder is saved
                   creation                               only after
                                                          confirmation;
                                                          ambiguous times
                                                          trigger
                                                          clarification.
  FR-05            Reminder                            P0 Due reminders are
                   delivery                               surfaced with a clear
                                                          spoken and visual
                                                          prompt; delivery
                                                          status is recorded.
  FR-06            Voice response                      P0 Response is spoken in
                                                          the selected
                                                          supported
                                                          language/voice; a
                                                          text transcript is
                                                          available.
  FR-07            Safety routing                      P0 High-risk
                                                          phrases/intent route
                                                          to the safety
                                                          workflow before
                                                          ordinary LLM response
                                                          generation.
  FR-08            Trusted contact   P0 for demo / P1 for When configured,
                   notification                production consented, and an
                                                          escalation rule
                                                          fires, the system
                                                          attempts notification
                                                          and records delivery
                                                          status; never claims
                                                          success without
                                                          provider
                                                          confirmation.
  FR-09            Senior profile                      P0 Store language,
                   and preferences                        accessibility
                                                          preferences,
                                                          timezone, and consent
                                                          state.
  FR-10            Caregiver access                    P0 Caregiver can access
                   control                                only explicitly
                                                          authorized senior
                                                          profiles;
                                                          unauthorized requests
                                                          are denied
                                                          server-side.
  FR-11            Check-ins                           P1 Configured check-in
                                                          prompts can be
                                                          acknowledged,
                                                          skipped, or marked
                                                          "need help."
  FR-12            Event/audit log                     P0 Reminder changes,
                                                          notification
                                                          attempts, consent
                                                          changes, and safety
                                                          escalations record
                                                          timestamp, actor, and
                                                          outcome.
  FR-13            Repeat/slow down                    P1 Senior can ask to
                                                          repeat or slow down
                                                          the spoken response.
  FR-14            Multilingual                        P1 At least one language
                   experience                             is fully supported
                                                          for the MVP;
                                                          additional languages
                                                          are enabled only
                                                          after speech and
                                                          safety behavior are
                                                          tested.
  FR-15            Offline or                          P2 If connectivity
                   degraded mode                          fails, app clearly
                                                          explains what still
                                                          works and queues only
                                                          safe, non-urgent
                                                      operations.
1. Safety and Trust Requirements

- The assistant must not diagnose, prescribe, change medication
  dosage, or advise stopping prescribed treatment.
- For symptoms that could indicate an emergency, it must recommend
  immediate human/emergency assistance and avoid extended
  conversational troubleshooting.
- The app must clearly distinguish "notification attempted,"
  "notification sent," and "notification delivery confirmed."
- If the model is uncertain about a potentially serious request, it
  must choose a safe fallback and encourage human help.
- No hidden always-on recording. Listening must be intentional and
  clearly indicated unless a separately consented, documented feature
  is implemented.
- The assistant must not claim that a caregiver, doctor, ambulance, or
  emergency service has been contacted unless the integration confirms
  it.
- Provide a clear way to stop speaking, cancel a pending action, and
  request a human.
- The system should not use shame, pressure, infantilizing language,
  or manipulative emotional attachment.
- Safety phrases, routing rules, and escalation outcomes must be
  testable and versioned.

9. Privacy, Consent, and Access

- Collect only data required for reminders, preferences, and agreed
  care workflows.
- Explain what is stored and what may be shared with a caregiver
  before enabling sharing.
- Separate senior accounts and profiles at the server/database
  authorization layer.
- Enforce ownership/relationship checks on every protected API
  request; never rely only on hidden UI controls.
- Do not expose one senior's data in another senior's response, logs,
  cache, search results, or generated context.
- Avoid storing raw audio by default. If audio retention is needed for
  debugging, make it opt-in, time-limited, access-restricted, and
  documented.
- Encrypt traffic in transit and use platform encryption at rest.
- Provide a way to revoke caregiver access and delete or export user
  data where feasible.
- Maintain audit logs for access-sensitive events without
  unnecessarily duplicating health-related content.
 1. Accessibility and UX Requirements

- Large text and touch targets; high contrast; uncluttered home
  screen.
- One prominent action to start speaking and one clear way to
  stop/cancel.
- Short spoken responses, plain language, and no jargon unless
  requested.
- Repeat, slower speech, and "I didn't understand" recovery.
- Visible state indicators: ready, listening, processing, speaking,
  reminder due, offline, and help requested.
- Never depend on color alone to convey status.
- Allow keyboard/tap fallback for noisy environments or
  speech-recognition failures.
- Test with varied accents, speech rates, background noise, and
  hearing/vision accessibility needs.

11. MVP Scope and Demo Definition
Must demonstrate
1. Senior profile setup and consent explanation.
1. Voice request to create a reminder.
1. Confirmation before saving.
1. Reminder list and delivery simulation or real scheduler.
1. One configured daily check-in.
1. A help-request phrase routed to a safety workflow.
1. A trusted-contact notification in a sandbox/test channel or clearly
   labeled simulation.
1. Event log showing what happened and its result.
1. Account/profile isolation test showing that one user cannot access
   another user's data.
Suggested demo script
1. "Remind me at 8 PM to take my prescribed medicine."
1. Confirm the parsed time and save the reminder.
1. Ask: "What reminders do I have today?"
1. Trigger a check-in and answer "I'm okay."
1. Trigger the help flow with a test phrase and show the escalation
   status.
1. Sign in as a different test user and prove the first user's data is
   inaccessible.
1. Success Metrics
Hackathon metrics should be measured on a defined test set, not
presented as clinical performance.

- Task completion rate: percentage of supported voice tasks
  completed correctly.
- Intent accuracy: correct classification for the supported intent
  set.
- Reminder integrity: no duplicate or silently modified reminders
  in test cases.
- Clarification rate: ambiguous requests prompt clarification
  rather than guessing.
- Safety routing recall: percentage of seeded high-risk test
  utterances routed to the safety workflow.
- False escalation rate: benign utterances incorrectly escalated.
- Notification truthfulness: 100% of status messages match the
  provider/test adapter result.
- Authorization pass rate: all cross-user access attempts in the
  security test suite are denied.
- Accessibility task completion: representative testers can start,
  stop, repeat, and cancel without assistance.
- Latency: track end-to-end response latency and report measured
  results rather than promising a fixed value before testing.
 1. Risks and Mitigations
  Risk                    Impact                  Mitigation
  Speech recognition      Incorrect reminder or   Read back critical
  mishears a time or      missed need             fields and require
  request                                         confirmation.
  LLM gives unsafe        User harm               Safety routing before
  medical advice                                  generation, constrained
                                                  response templates,
                                                  test suite, human
                                                  escalation.
  False reassurance       Delayed care            Clear emergency
  during emergency                                guidance; never imply
                                                  the AI can assess or
                                                  guarantee safety.
  Notification provider   Caregiver not informed  Show failure, retry
  fails                                           under bounded policy,
                                                  provide an alternate
                                                  explicit instruction.
  Unauthorized profile    Privacy breach          Server-side
  access                                          object-level
                                                  authorization,
                                                  tenant-scoped queries,
                                                  negative security
                                                  tests.
  Poor performance for    Exclusion or            Retry, slower speech,
  accents/noise           frustration             typed/tap fallback,
                                                  support only tested
                                                  languages.
  Internet/model outage   Core flow interruption  Graceful error handling
                                                  and local access to
                                                  saved reminder list
                                                  where feasible.
  Over-scoping for        Incomplete demo         Prioritize one
  hackathon                                       end-to-end vertical
                                                  slice; defer passive
                                                  sensing and advanced
                                              analytics.
 2. Release Plan
Phase 1 --- Hackathon MVP
Voice interaction, reminder create/list/cancel, confirmation, check-in,
safety routing, test notification adapter, profile isolation, audit log.
Phase 2 --- Pilot hardening
Usability testing with seniors and caregivers, multilingual validation,
real notification providers, consent/revocation workflows, reliability
and security review.
Phase 3 --- Expanded care support
Care-team workflows, carefully governed integrations, optional sensor
integrations only with explicit consent and validation.
 3. Open Decisions

- Which language(s) will be supported in the demo?
- Will the demo use browser speech APIs, a hosted speech service, or a
  local speech model?
- Which notification channel will be used: email, SMS, or a sandbox
  adapter?
- Will authentication be email/password, OTP, or a managed identity
  provider?
- Which jurisdiction and data-protection requirements apply to any
  real-world pilot?
- What is the final deployment target and available budget?
Release gate: Do not describe the MVP as medically validated or
production-ready until clinical, privacy, security, accessibility, and
reliability reviews have been completed.
