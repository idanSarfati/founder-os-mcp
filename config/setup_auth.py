"""
Basic setup script for authentication-related configuration.

Usage:
    python -m config.setup_auth

This script will:
    - Ensure a `.env` file exists at the project root.
    - Populate it with commented placeholders for Clerk and Supabase keys
      if they are missing.
    - Print a short checklist for finishing auth setup.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List


ENV_TEMPLATE_HEADER = (
    "# Founder OS MCP - Authentication & Database Configuration\n"
    "# Fill in the values below with your real credentials.\n"
    "# DO NOT commit this file to version control.\n\n"
)

ENV_KEYS: List[str] = [
    "NOTION_API_KEY",
    "CLERK_PUBLISHABLE_KEY",
    "CLERK_SECRET_KEY",
    "SUPABASE_URL",
    "SUPABASE_ANON_KEY",
    "SUPABASE_SERVICE_ROLE_KEY",
]


def _append_missing_keys(env_path: Path) -> None:
    """
    Appends any missing auth-related keys to the given `.env` file
    as commented placeholders.
    """
    existing = set()  # type: ignore[var-annotated]
    if env_path.exists():
        with env_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key = line.split("=", 1)[0].strip()
                existing.add(key)

    missing = [key for key in ENV_KEYS if key not in existing]
    if not missing:
        return

    with env_path.open("a", encoding="utf-8") as f:
        if env_path.stat().st_size > 0:
            f.write("\n")
        for key in missing:
            f.write(f"# {key}=YOUR_VALUE_HERE\n")


def ensure_env_file() -> Path:
    """
    Ensures a `.env` file exists at the project root and contains
    placeholders for all required authentication keys.

    Returns:
        The path to the `.env` file.
    """
    project_root = Path(__file__).resolve().parents[1]
    env_path = project_root / ".env"

    if not env_path.exists():
        with env_path.open("w", encoding="utf-8") as f:
            f.write(ENV_TEMPLATE_HEADER)

    _append_missing_keys(env_path)
    return env_path


def main() -> None:
    """
    Entry point for the setup script.

    Creates or updates the `.env` file and prints a short checklist.
    """
    env_path = ensure_env_file()

    print(f".env checked/updated at: {env_path}")
    print("\nNext steps:")
    print("  1. Open the .env file and replace placeholder values with:")
    print("     - NOTION_API_KEY (already in use by server.py)")
    print("     - CLERK_PUBLISHABLE_KEY / CLERK_SECRET_KEY")
    print("     - SUPABASE_URL / SUPABASE_ANON_KEY / SUPABASE_SERVICE_ROLE_KEY")
    print("  2. Restart the MCP server after updating the values.")


if __name__ == "__main__":
    main()


