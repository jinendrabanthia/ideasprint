"""AI For Elders — Main FastAPI Application.

A voice-first AI companion for senior daily care.

IMPORTANT DISCLAIMERS:
- This application is NOT a doctor, diagnostic system, or emergency service.
- It should NOT be treated as a replacement for human care.
- Notification simulation is clearly labeled as simulated.
- The application is a hackathon MVP, not clinically validated.
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.schemas.models import HealthCheck

# Import routers
from app.api.v1.auth import router as auth_router
from app.api.v1.profiles import router as profiles_router
from app.api.v1.reminders import router as reminders_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.checkins import router as checkins_router
from app.api.v1.contacts import router as contacts_router
from app.api.v1.caregivers import router as caregivers_router
from app.api.v1.help_notifications import router as help_router

app = FastAPI(
    title="AI For Elders",
    description="Voice-first AI companion for senior daily care",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow local dev and production frontend origins (including Vercel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "https://*.vercel.app",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global error handler ────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch unhandled exceptions — never expose internal details."""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal error occurred. Please try again.",
            "correlation_id": "",
        },
    )


# ── Health check ─────────────────────────────────────

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    db_status = "connected"
    try:
        from app.core.supabase_client import get_supabase_admin
        admin = get_supabase_admin()
        admin.table("users").select("id").limit(1).execute()
    except Exception:
        db_status = "error"

    return HealthCheck(status="healthy", version="0.1.0", database=db_status)


# ── Mount API routers ────────────────────────────────

app.include_router(auth_router, prefix="/api/v1")
app.include_router(profiles_router, prefix="/api/v1")
app.include_router(reminders_router, prefix="/api/v1")
app.include_router(conversations_router, prefix="/api/v1")
app.include_router(checkins_router, prefix="/api/v1")
app.include_router(contacts_router, prefix="/api/v1")
app.include_router(caregivers_router, prefix="/api/v1")
app.include_router(help_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "AI For Elders",
        "version": "0.1.0",
        "description": "Voice-first AI companion for senior daily care",
        "disclaimer": "This is NOT a medical device, diagnostic tool, or emergency service.",
        "docs": "/docs",
    }
