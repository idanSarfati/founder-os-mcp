"""
Authentication and database configuration for Founder OS.

This module centralizes access to environment variables required for Clerk,
Supabase, and Notion.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Optional

from dotenv import load_dotenv


@dataclass
class AuthConfig:
    """
    Holds authentication and database configuration for the MCP server.
    """
    notion_api_key: str  # <--- ADDED THIS (Required)
    clerk_publishable_key: Optional[str]
    clerk_secret_key: Optional[str]
    supabase_url: Optional[str]
    supabase_anon_key: Optional[str]
    supabase_service_role_key: Optional[str]


def load_auth_config() -> AuthConfig:
    """
    Loads configuration from environment variables.
    Raises ValueError if required keys (like Notion) are missing.
    """
    load_dotenv()

    notion_key = os.getenv("NOTION_API_KEY")
    if not notion_key:
        raise ValueError("CRITICAL: NOTION_API_KEY is missing from .env")

    return AuthConfig(
        notion_api_key=notion_key,  # <--- LOAD IT HERE
        clerk_publishable_key=os.getenv("CLERK_PUBLISHABLE_KEY"),
        clerk_secret_key=os.getenv("CLERK_SECRET_KEY"),
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_anon_key=os.getenv("SUPABASE_ANON_KEY"),
        supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
    )


__all__ = ["AuthConfig", "load_auth_config"]