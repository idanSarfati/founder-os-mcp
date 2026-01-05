"""
Semantic Data Extraction for Founder OS Governance Engine.

Extracts and normalizes unstructured architectural data from Notion and Linear
to generate dynamic governance rules.
"""

import os
from datetime import datetime
from typing import Dict, Any, List, Optional
try:
    from tools.notion_context import search_notion, fetch_project_context
    from utils.llm_client import get_llm_client
    from utils.logger import logger

    # Try to import Linear client (graceful degradation if not available)
    try:
        from integrations.linear_client import LinearClient
        LINEAR_AVAILABLE = True
    except (ImportError, ValueError):
        LINEAR_AVAILABLE = False
        logger.info("Linear integration not available for governance extraction")
except ImportError:
    # Fallback for when running from different directory
    from src.tools.notion_context import search_notion, fetch_project_context
    from src.utils.llm_client import get_llm_client
    from src.utils.logger import logger

    # Try to import Linear client (graceful degradation if not available)
    try:
        from src.integrations.linear_client import LinearClient
        LINEAR_AVAILABLE = True
    except (ImportError, ValueError):
        LINEAR_AVAILABLE = False
        logger.info("Linear integration not available for governance extraction")


class GovernanceExtractor:
    """
    Extracts governance data from Notion and Linear sources.

    Uses semantic search to find relevant documentation and tasks,
    then normalizes the data using LLM processing.
    """

    def __init__(self):
        """Initialize the governance extractor."""
        self.llm_client = None  # Lazy initialization
        self.linear_client = LinearClient() if LINEAR_AVAILABLE else None

    def _get_llm_client(self):
        """Get LLM client with lazy initialization."""
        if self.llm_client is None:
            try:
                self.llm_client = get_llm_client()
            except ValueError as e:
                logger.warning(f"LLM client initialization failed: {e}")
                self.llm_client = None  # Keep as None to indicate failure
        return self.llm_client

    def extract_governance_data(self) -> Dict[str, Any]:
        """
        Extract and normalize governance data from all available sources.

        Returns:
            Dictionary containing:
            - allowed_tech: List of approved technologies
            - forbidden_libs: List of prohibited libraries
            - auth_strategy: Authentication approach
            - strictness: Security level
            - active_tasks_context: Summary of active Linear tasks
            - generation_timestamp: When this data was extracted
        """
        logger.info("Starting governance data extraction")

        # Check if we can even attempt extraction (dependencies available)
        try:
            import tools.notion_context  # Test if notion_context can be imported
            import integrations.linear_client  # Test if linear_client can be imported
            import utils.llm_client  # Test if llm_client can be imported
        except ImportError as e:
            logger.warning(f"External dependencies not available: {e}")
            logger.info("Using hardcoded governance fallback (CI Mode)")
            return self._get_hardcoded_fallback_data()

        try:
            # Step 1: Extract context from Notion
            notion_context = self._extract_notion_context()
            logger.debug(f"Extracted {len(notion_context)} chars from Notion")

            # Step 2: Extract context from Linear (if available)
            linear_context = self._extract_linear_context() if self.linear_client else ""
            logger.debug(f"Extracted {len(linear_context)} chars from Linear")

            # Step 3: Combine contexts
            combined_context = f"NOTION CONTEXT:\n{notion_context}\n\nLINEAR CONTEXT:\n{linear_context}"
            logger.debug(f"Combined context: {len(combined_context)} chars")

            # Step 4: Use LLM to normalize data (or fallback if no API key)
            llm_client = self._get_llm_client()
            if llm_client:
                try:
                    governance_data = llm_client.extract_governance_data(combined_context)
                except Exception as e:
                    logger.warning(f"LLM extraction failed, using fallback data: {e}")
                    governance_data = self._get_fallback_data()
            else:
                logger.info("LLM client not available, using fallback data")
                governance_data = self._get_fallback_data()

            # Step 5: Add metadata and task context
            governance_data.update({
                "active_tasks_context": self._format_active_tasks_context(),
                "generation_timestamp": datetime.now().isoformat()
            })

            logger.info("Governance data extraction completed successfully")
            return governance_data

        except Exception as e:
            logger.exception(f"Governance extraction failed: {e}")
            # Use hardcoded fallback rules for CI/CD environments
            return self._get_hardcoded_fallback_data()

    def _extract_notion_context(self) -> str:
        """
        Extract relevant architectural context from Notion.

        Uses broad search with architectural keywords to find relevant pages,
        then concatenates their content.

        Returns:
            Concatenated text from relevant Notion pages
        """
        # Search for architectural and technical documentation (aligned with Notion spec)
        search_terms = [
            "Architecture", "Tech Stack", "Constraints",
            "Spec", "Specification", "Requirements"
        ]

        all_content = []
        processed_page_ids = set()

        for term in search_terms:
            try:
                logger.debug(f"Searching Notion for: {term}")
                search_result = search_notion(term)

                # Extract page IDs from search results
                # The search result format is: "- [object_type] title (ID: page_id)"
                lines = search_result.split('\n')
                for line in lines:
                    if '(ID: ' in line and ']' in line:
                        try:
                            # Extract page ID from format like: "- [page] Architecture Overview (ID: abc123)"
                            id_start = line.find('(ID: ') + 5
                            id_end = line.find(')', id_start)
                            if id_start > 4 and id_end > id_start:
                                page_id = line[id_start:id_end].strip()
                                if page_id and page_id not in processed_page_ids:
                                    processed_page_ids.add(page_id)

                                    # Fetch the actual content
                                    logger.debug(f"Fetching content for page: {page_id}")
                                    page_content = fetch_project_context(page_id)

                                    # Skip error messages and empty content
                                    if not page_content.startswith("Error:") and len(page_content.strip()) > 50:
                                        all_content.append(f"=== PAGE: {page_id} ===\n{page_content}")

                        except (ValueError, IndexError):
                            continue

            except Exception as e:
                logger.warning(f"Notion search failed for term '{term}': {e}")
                continue

        # Limit to top 3 most relevant pages to avoid token limits
        combined_content = "\n\n".join(all_content[:3])

        if not combined_content.strip():
            logger.warning("No usable Notion content found")
            combined_content = "No architectural documentation found in Notion."

        return combined_content

    def _extract_linear_context(self) -> str:
        """
        Extract relevant task context from Linear.

        Gets active tasks and their descriptions to understand current
        technical priorities and constraints.

        Returns:
            Formatted string of active task information
        """
        if not self.linear_client:
            return "Linear integration not available."

        try:
            logger.debug("Fetching active Linear tasks")
            tasks_text = self.linear_client.get_active_tasks()

            # Extract task details for more context
            task_details = []
            lines = tasks_text.split('\n')

            for line in lines:
                if '📌 [' in line and ']' in line:
                    # Extract task ID from format like: "📌 [IDA-6] Task Title"
                    try:
                        id_start = line.find('[') + 1
                        id_end = line.find(']', id_start)
                        if id_start > 0 and id_end > id_start:
                            task_id = line[id_start:id_end].strip()
                            if task_id and '-' in task_id:
                                logger.debug(f"Fetching details for task: {task_id}")
                                details = self.linear_client.get_task_details(task_id)
                                if not details.startswith("⚠️"):
                                    task_details.append(details)
                    except (ValueError, IndexError):
                        continue

            # Combine task overview with details
            detailed_context = f"{tasks_text}\n\nDETAILED TASK INFORMATION:\n" + "\n\n".join(task_details[:3])

            return detailed_context

        except Exception as e:
            logger.exception(f"Linear context extraction failed: {e}")
            return f"Linear context unavailable: {str(e)}"

    def _format_active_tasks_context(self) -> str:
        """
        Format active tasks for inclusion in governance rules.

        Returns:
            Formatted summary of current active tasks
        """
        if not self.linear_client:
            return "- Linear integration not configured"

        try:
            tasks_text = self.linear_client.get_active_tasks()

            # Extract just the task summaries for the template
            task_lines = []
            lines = tasks_text.split('\n')

            for line in lines:
                if '📌 [' in line:
                    # Clean up the task line for the template
                    task_lines.append(f"- {line.strip('📌 ')}")

            if task_lines:
                return "\n".join(task_lines[:5])  # Limit to 5 tasks
            else:
                return "- No active tasks found"

        except Exception as e:
            logger.warning(f"Failed to format active tasks: {e}")
            return "- Unable to retrieve active tasks"

    def _get_hardcoded_fallback_data(self) -> Dict[str, Any]:
        """
        Return hardcoded governance rules for CI/CD environments.

        This provides actual enforcement rules even when APIs are unavailable.
        Used as a fallback when external dependencies fail to load.

        Returns:
            Hardcoded governance settings based on project requirements
        """
        logger.warning("Using hardcoded governance fallback data")

        return {
            "ALLOWED_TECH_STACK": "Vue.js 3, Nuxt 3, Python 3.10+, FastAPI, PostgreSQL, Supabase",
            "FORBIDDEN_LIBRARIES": "React, jQuery, Bootstrap, Axios, Lodash, Moment.js",
            "AUTH_PROVIDER": "Supabase Auth",
            "STRICTNESS_LEVEL": "MAXIMUM",
            "active_tasks_context": "- Governance enforcement active",
            "generation_timestamp": datetime.now().isoformat()
        }

    def _get_fallback_data(self) -> Dict[str, Any]:
        """
        Return safe fallback data when extraction fails.

        Returns:
            Conservative default governance settings
        """
        logger.warning("Using fallback governance data")

        return {
            "ALLOWED_TECH_STACK": "Unknown/Detect from Codebase",
            "FORBIDDEN_LIBRARIES": "Unknown/Detect from Codebase",
            "AUTH_PROVIDER": "Unknown/Detect from Codebase",
            "STRICTNESS_LEVEL": "MEDIUM",
            "active_tasks_context": "- Unable to retrieve active tasks",
            "generation_timestamp": datetime.now().isoformat()
        }


# Global instance for easy access
_governance_extractor = None

def get_governance_extractor() -> GovernanceExtractor:
    """Get or create the global governance extractor instance."""
    global _governance_extractor
    if _governance_extractor is None:
        try:
            _governance_extractor = GovernanceExtractor()
        except Exception as e:
            logger.warning(f"Governance extractor initialization failed: {e}")
            raise
    return _governance_extractor

def extract_governance_data() -> Dict[str, Any]:
    """
    Convenience function to extract governance data.

    Returns:
        Extracted and normalized governance data dictionary
    """
    extractor = get_governance_extractor()
    return extractor.extract_governance_data()
