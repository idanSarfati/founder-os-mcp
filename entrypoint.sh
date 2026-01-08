#!/bin/bash
set -euo pipefail

# Founder OS Action Guard - Entrypoint Script
# This script provides a clean, auditable interface to action-guard.py
# No complex logic here - just parameter validation and environment setup

echo "🔍 Starting Founder OS Action Guard validation..."

# Validate required environment variables
if [[ -z "${NOTION_TOKEN:-}" ]]; then
    echo "❌ Error: NOTION_TOKEN environment variable is required"
    exit 1
fi

if [[ -z "${GEMINI_API_KEY:-}" ]]; then
    echo "❌ Error: GEMINI_API_KEY environment variable is required"
    exit 1
fi

if [[ -z "${PR_TITLE:-}" ]]; then
    echo "❌ Error: PR_TITLE environment variable is required"
    exit 1
fi

if [[ -z "${PR_NUMBER:-}" ]]; then
    echo "❌ Error: PR_NUMBER environment variable is required"
    exit 1
fi

if [[ -z "${GITHUB_REPOSITORY:-}" ]]; then
    echo "❌ Error: GITHUB_REPOSITORY environment variable is required"
    exit 1
fi

# Set default validation mode if not provided
export VALIDATION_MODE="${VALIDATION_MODE:-dual}"

echo "✅ Environment validation passed"
echo "🚀 Executing action-guard.py..."

# Execute the Python validation script
# All logic is contained within action-guard.py - this script is purely an interface
exec python .github/scripts/action-guard.py
