"""Supabase client initialization."""
from supabase import create_client, Client
from app.core.config import settings

_client: Client | None = None


def get_supabase() -> Client:
    """Get or create the Supabase client singleton."""
    global _client
    if _client is None:
        _client = create_client(settings.supabase_url, settings.supabase_anon_key)
    return _client


def get_supabase_admin() -> Client:
    """Get a Supabase client with service role key for admin operations."""
    return create_client(settings.supabase_url, settings.supabase_service_key)
