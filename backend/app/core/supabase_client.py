"""Database and Supabase client initialization.

Attempts cloud Supabase connection first; automatically falls back to local
SQLite adapter if Supabase is offline or public schema is not yet deployed.
"""
from __future__ import annotations

from typing import Any
from supabase import create_client, Client
from app.core.config import settings
from app.adapters.db_adapter import get_sqlite_client

_client: Any = None
_admin_client: Any = None
_use_sqlite: bool | None = None


def _check_supabase_available() -> bool:
    """Check if Supabase is reachable and public schema is provisioned."""
    global _use_sqlite
    if _use_sqlite is not None:
        return not _use_sqlite

    # If Supabase URL or keys are empty, immediately use SQLite
    if not settings.supabase_url or not settings.supabase_anon_key or "afcvthaddhknsdlccenv" in settings.supabase_url:
        # Check if the tables exist
        try:
            test_client = create_client(settings.supabase_url, settings.supabase_anon_key)
            test_client.table("users").select("id").limit(1).execute()
            _use_sqlite = False
            return True
        except Exception:
            _use_sqlite = True
            return False

    try:
        test_client = create_client(settings.supabase_url, settings.supabase_anon_key)
        test_client.table("users").select("id").limit(1).execute()
        _use_sqlite = False
        return True
    except Exception:
        _use_sqlite = True
        return False


def get_supabase() -> Any:
    """Get or create the Supabase or SQLite database client."""
    global _client
    if _client is None:
        if _check_supabase_available():
            try:
                _client = create_client(settings.supabase_url, settings.supabase_anon_key)
            except Exception:
                _client = get_sqlite_client()
        else:
            _client = get_sqlite_client()
    return _client


def get_supabase_admin() -> Any:
    """Get a database client with service role / admin capabilities."""
    global _admin_client
    if _admin_client is None:
        if _check_supabase_available():
            try:
                _admin_client = create_client(settings.supabase_url, settings.supabase_service_key)
            except Exception:
                _admin_client = get_sqlite_client()
        else:
            _admin_client = get_sqlite_client()
    return _admin_client
