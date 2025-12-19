"""
Simple Supabase connectivity verifier for Founder OS.

This module can be run as a script to verify that Supabase credentials are
configured correctly and that the MCP server can reach the Supabase backend.

Usage:
    python -m src.tools.verify_db
"""

from __future__ import annotations

import sys
from typing import NoReturn

from config.supabase_client import get_supabase_client


def verify_supabase_connection() -> bool:
    """
    Verifies that a Supabase client can be created and perform a simple request.

    This function uses the shared Supabase client and executes a lightweight
    operation (`storage.list_buckets()`) as a "ping" to confirm connectivity
    and credential correctness.

    Returns:
        True if the verification succeeds, False otherwise.
    """
    supabase = get_supabase_client()

    # A minimal server-side operation that does not depend on any user tables.
    # If credentials or network are misconfigured, this will raise an error
    # or return an error payload.
    response = supabase.storage.list_buckets()

    # `list_buckets` returns a list on success; on error, the SDK typically
    # raises or returns an object with an `error` attribute.
    if isinstance(response, list):
        return True

    # Fallback: handle non-list responses defensively.
    error = getattr(response, "error", None)
    if error:
        raise RuntimeError(f"Supabase error during verification: {error}")

    return True


def main() -> NoReturn:
    """
    Entry point for running the verification as a script.

    Prints a clear success or failure message and exits with an appropriate
    status code.
    """
    try:
        ok = verify_supabase_connection()
        if ok:
            print("✅ Connection Successful: Supabase is reachable and credentials look valid.")
            sys.exit(0)
        print("❌ Connection Failed: Verification returned a negative result.")
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print("❌ Connection Failed: An exception occurred during verification.")
        print(f"   Details: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()



