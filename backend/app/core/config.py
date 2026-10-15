"""Application configuration from environment variables."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings


def _find_env_file() -> str | None:
    """Walk up from this file to find a .env file."""
    current = Path(__file__).resolve().parent
    for _ in range(5):
        env_path = current / ".env"
        if env_path.exists():
            return str(env_path)
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str = ""

    # Gemini AI
    gemini_api_key: str = ""

    # Backend
    secret_key: str = "dev-secret-change-in-production"
    backend_port: int = 8000
    frontend_url: str = "http://localhost:5173"

    # Notifications
    notification_mode: str = "mock"  # "mock" or "twilio"

    model_config = {
        "env_file": _find_env_file() or ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
