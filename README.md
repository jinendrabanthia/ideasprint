# AI For Elders — Sahara Daily Care Companion

> **A Voice-First AI Companion for Senior Daily Care, Medication Adherence, and Caregiver Peace of Mind.**

---

## ⚠️ Important Safety & Non-Clinical Disclaimers

1. **Not a Medical Device or Diagnostic Tool**: Sahara is an assistive daily companion designed to support independent senior living, routine adherence, and social engagement. It does **not** provide clinical diagnosis, medical prescriptions, or emergency triage.
2. **Emergency Protocol & Simulation Labeling**: In any real-world emergency, users must immediately call **911** or local emergency medical services. Emergency and escalation features within this system are explicitly labeled and logged as **simulations** for demonstration and verification purposes.
3. **Transparent Senior Consent**: Caregiver dashboards operate strictly on mutual, revocable senior consent. Senior dignity, autonomy, and privacy remain the primary design priority.

---

## 🌟 Key Features

### 1. Senior Experience (Voice-First & High Accessibility)
- **Sahara Voice Companion**: Interactive voice and audio companion utilizing browser Web Speech API recognition and speech synthesis (TTS) at an elder-friendly, gentle pace (0.85x).
- **Today's Routine & Medication Tracking**: Visual and audio reminders with one-tap acknowledgment ("I took this") or 15-minute snooze.
- **Daily Wellbeing Check-In**: Visual, emoji-assisted check-in tracking mood, physical comfort, and sleep quality.
- **Accessibility System**: WCAG 2.1 AA compliant design with warm earthy tones, customizable text sizing (Default, Large, Extra Large), high-contrast mode, and large touch targets (min 48×48px).
- **5-Step Onboarding**: Friendly wizard introducing Sahara, testing audio/mic, and confirming privacy settings.

### 2. Family & Caregiver Portal
- **Caregiver Dashboard**: Real-time overview of senior check-ins, medication adherence metrics, and recent activity.
- **Privacy-Preserving Summaries**: AI-generated sentiment and conversation summaries that respect the senior's privacy without exposing raw private dialogues.
- **Consent Governance**: Bilateral relationship linkage that can be inspected and revoked at any time by either senior or caregiver.
- **Safety Alert Trail**: Transparent audit trail of triggered alerts and help request simulations.

---

## 🛠️ Architecture & Tech Stack

```
AI_FOR_ELDERS/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # REST API endpoints (Auth, Profiles, Reminders,
│   │   │                    #   Assistant, Check-ins, Contacts, Caregivers, Help)
│   │   ├── core/            # Configuration, JWT auth, Supabase client
│   │   ├── models/          # Domain models
│   │   ├── schemas/         # Pydantic schemas & response models
│   │   ├── services/        # Business logic (Safety, Reminders, Check-ins, etc.)
│   │   ├── adapters/        # AI & External integrations (Gemini, Supabase)
│   │   └── main.py          # FastAPI application & middleware
│   ├── tests/               # Pytest integration test suite
│   └── pyproject.toml       # Backend dependencies
├── frontend/
│   ├── src/
│   │   ├── components/      # Layout and reusable UI components
│   │   ├── pages/           # 7 complete screens (Auth, Onboarding, Home,
│   │   │                    #   Chat, Reminders, CheckIn, Settings, Caregiver)
│   │   ├── api.ts           # Centralized API client with error handling
│   │   ├── AuthContext.tsx  # User session & token management
│   │   ├── index.css        # Warm senior-friendly design system
│   │   └── main.tsx         # React application entry point
│   ├── package.json
│   └── vite.config.ts
├── PRD.md                   # Product Requirements Document
└── TRD.md                   # Technical Requirements Document
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1. Backend Setup
```bash
cd backend

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

# Install dependencies
pip install -e .

# Run tests
pytest tests/

# Start API server
uvicorn app.main:app --reload --port 8000
```
API Documentation will be live at: `http://localhost:8000/docs`

### 2. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Build production bundle (or run dev server)
npm run build
npm run dev
```
Frontend will be accessible at: `http://localhost:5173`

---

## 🧪 Verification & Testing

- **Backend Integration Tests**: Run `pytest tests/` in the `backend/` folder. All endpoints, health checks, schemas, and security boundaries are validated.
- **Frontend Build**: Run `npm run build` in the `frontend/` folder. TypeScript compilation and Vite bundling pass with 0 errors.

---

## 📄 License

Built for hackathon demonstration. Non-clinical assistive technology prototype.
