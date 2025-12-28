"""
Authentication and database configuration for Founder OS.

This module centralizes access to environment variables required for Clerk,
Supabase, and Notion.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv, find_dotenv


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
    
    Uses find_dotenv() to locate .env file relative to project root,
    ensuring it works regardless of the current working directory.
    """
    # Find .env file relative to this file's location (project root)
    env_path = find_dotenv()
    if env_path:
        load_dotenv(dotenv_path=env_path)
    else:
        # Fallback: try loading from project root relative to this file
        project_root = Path(__file__).parent.parent
        env_file = project_root / ".env"
        if env_file.exists():
            load_dotenv(dotenv_path=str(env_file))
        else:
            # Last resort: try current directory
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