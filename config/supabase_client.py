"""
Supabase client initialization for Founder OS.

This module centralizes creation of a Supabase client using configuration
loaded from `auth_config`. Other parts of the application should import
`get_supabase_client` instead of creating their own clients.
"""

from __future__ import annotations

from typing import Any

from supabase import create_client, Client  # type: ignore[import]

from .auth_config import load_auth_config


_supabase_client: Client | None = None


def get_supabase_client() -> Client:
    """
    Returns a singleton Supabase client configured via environment variables.

    The configuration values are loaded via `load_auth_config`, which expects
    the following environment variables to be set (or present in `.env`):
        - SUPABASE_URL
        - SUPABASE_ANON_KEY
        - SUPABASE_SERVICE_ROLE_KEY

    Raises:
        RuntimeError: If required Supabase configuration values are missing.
    """
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    config = load_auth_config()

    if not config.supabase_url:
        raise RuntimeError("SUPABASE_URL is not configured.")
    if not config.supabase_service_role_key:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is not configured.")

    # For server-side operations we use the service role key.
    client: Client = create_client(config.supabase_url, config.supabase_service_role_key)
    _supabase_client = client
    return client


__all__ = ["get_supabase_client"]



