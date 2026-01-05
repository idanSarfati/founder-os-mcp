"""
LLM Client for Founder OS Governance Engine.

Provides a clean interface for LLM-powered text normalization and data extraction
used in the dynamic governance system.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

# ✅ Defensive Import: מונע קריסה אם python-dotenv חסר (כמו ב-CI)
try:
    from dotenv import load_dotenv, find_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

# ✅ Defensive Import: מונע קריסה אם openai חסר
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

try:
    from utils.logger import logger
except ImportError:
    try:
        from src.utils.logger import logger
    except ImportError:
        logger = logging.getLogger(__name__)

# Load .env file before accessing environment variables
env_path = find_dotenv()
if env_path:
    load_dotenv(dotenv_path=env_path)


class LLMClient:
    """
    Client for interacting with LLM services to normalize unstructured data.

    Used by the governance engine to extract structured constraints from
    messy Notion and Linear data.
    """

    def __init__(self):
        """Initialize the LLM client with API key from environment."""
        if not OPENAI_AVAILABLE:
            logger.warning("⚠️ OpenAI client not available. Using fallback mode.")
            self.client = None
            self.model = None
            return

        # Load environment variables if dotenv is available
        if DOTENV_AVAILABLE:
            try:
                env_path = find_dotenv()
                if env_path:
                    load_dotenv(env_path)
            except Exception as e:
                logger.debug(f"Could not load .env file: {e}")

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable required")

        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # Use smaller model for efficiency

    def extract_governance_data(self, context_text: str) -> Dict[str, Any]:
        """
        Extract structured governance data from unstructured text.

        Args:
            context_text: Concatenated text from Notion pages and Linear tasks

        Returns:
            Dictionary with extracted governance fields:
            - allowed_tech: List of approved technologies
            - forbidden_libs: List of prohibited libraries
            - auth_strategy: Authentication approach
            - strictness: Security/enforcement level
        """
        prompt = f"""
You are a technical specification analyzer. Extract governance constraints from the following messy project documentation and task data.

INPUT TEXT:
{context_text}

TASK: Extract the following technical constraints into a clean JSON format. If information is not available, use "Unknown/Detect from Codebase" as the value. Do NOT hallucinate or make assumptions.

REQUIRED FIELDS:
- ALLOWED_TECH_STACK: String describing approved technologies (e.g., "Next.js 14, Tailwind, Supabase")
- FORBIDDEN_LIBRARIES: String describing prohibited libraries (e.g., "jQuery, Bootstrap, Axios")
- AUTH_PROVIDER: Authentication provider (e.g., "Clerk")
- STRICTNESS_LEVEL: Security enforcement level ("HIGH", "MEDIUM", "LOW")

OUTPUT: Valid JSON only, no markdown or explanation.
"""

        # Check if OpenAI client is available
        if self.client is None:
            logger.info("OpenAI client not available, using safe defaults")
            return self._get_safe_defaults()

        try:
            logger.info("Calling LLM to extract governance data")
            logger.debug(f"Input text length: {len(context_text)} characters")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a technical specification analyzer. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.1  # Low temperature for consistent extraction
            )

            result_text = response.choices[0].message.content.strip()
            logger.debug(f"LLM response: {result_text}")

            # Parse JSON response
            try:
                parsed = json.loads(result_text)
                logger.info("Successfully parsed LLM response")

                # Validate required fields
                required_fields = ["ALLOWED_TECH_STACK", "FORBIDDEN_LIBRARIES", "AUTH_PROVIDER", "STRICTNESS_LEVEL"]
                for field in required_fields:
                    if field not in parsed:
                        parsed[field] = "Unknown/Detect from Codebase"

                return parsed

            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse LLM JSON response: {e}")
                logger.warning(f"Raw response: {result_text}")
                return self._get_safe_defaults()

        except Exception as e:
            logger.exception(f"LLM extraction failed: {e}")
            return self._get_safe_defaults()

    def _get_safe_defaults(self) -> Dict[str, Any]:
        """
        Return safe default values when LLM extraction fails.

        Returns:
            Dictionary with conservative default governance settings
        """
        logger.warning("Using safe default governance settings")
        return {
            "ALLOWED_TECH_STACK": "Unknown/Detect from Codebase",
            "FORBIDDEN_LIBRARIES": "Unknown/Detect from Codebase",
            "AUTH_PROVIDER": "Unknown/Detect from Codebase",
            "STRICTNESS_LEVEL": "MEDIUM"
        }

    def format_tech_stack(self, tech_stack: str) -> str:
        """
        Format a technology stack string for inclusion in governance rules.

        Args:
            tech_stack: Technology stack description string

        Returns:
            Formatted string for template insertion
        """
        if not tech_stack or tech_stack == "Unknown/Detect from Codebase":
            return "- Unknown/Detect from Codebase (Ask user for clarification)"

        return tech_stack

    def format_forbidden_libs(self, forbidden_libs: str) -> str:
        """
        Format a forbidden libraries string for inclusion in governance rules.

        Args:
            forbidden_libs: Forbidden libraries description string

        Returns:
            Formatted string for template insertion
        """
        if not forbidden_libs or forbidden_libs == "Unknown/Detect from Codebase":
            return "- Unknown/Detect from Codebase (Ask user for clarification)"

        return forbidden_libs


# Global instance for easy access
_llm_client = None

def get_llm_client() -> LLMClient:
    """Get or create the global LLM client instance."""
    global _llm_client
    if _llm_client is None:
        try:
            _llm_client = LLMClient()
        except ValueError as e:
            logger.warning(f"LLM client initialization failed: {e}")
            raise
    return _llm_client
