"""
Project operations and bootstrap functionality for Founder OS.

This module handles project initialization tasks, including installing
the Founder OS 'Brain' (.cursor/rules/founder-os-governance.mdc) into target directories.
Supports Cursor Rules V2 structure with dynamic governance extraction.
"""

import os
from typing import Dict, Any
from config.governance_template import get_governance_template
from src.tools.governance_extraction import extract_governance_data
from src.utils.llm_client import get_llm_client
from src.utils.logger import logger


def bootstrap_project(target_dir: str) -> str:
    """
    INITIALIZE COMMAND: Installs the Founder OS 'Brain' (.cursor/rules/founder-os-governance.mdc) into the specified project folder.
    Supports Cursor Rules V2 structure with dynamic governance extraction from Notion and Linear.

    This function:
    1. Extracts governance data from Notion pages and Linear tasks
    2. Uses LLM to normalize unstructured data into structured rules
    3. Injects the data into a governance template
    4. Writes the final rules file

    Args:
        target_dir: The target directory where the rules should be installed.

    Returns:
        Success or error message string.
    """
    try:
        logger.info(f"Received request for tool: bootstrap_project. Target directory: {target_dir}")

        # Clean the path and set up new structure
        abs_target_dir = os.path.abspath(target_dir)
        rules_dir = os.path.join(abs_target_dir, ".cursor", "rules")
        target_path = os.path.join(rules_dir, "founder-os-governance.mdc")

        # Check for legacy .cursorrules file in project directory
        legacy_path = os.path.join(abs_target_dir, ".cursorrules")
        migrated_legacy = False

        if os.path.exists(legacy_path) and not os.path.exists(target_path):
            logger.info(f"Found legacy .cursorrules in project directory, will migrate to new structure")
            migrated_legacy = True

        # Check if new rules already exist
        if os.path.exists(target_path) and not migrated_legacy:
            logger.info(f"Bootstrap skipped: rules already exist at {target_path}")
            return f"ℹ️ Skipped: Cursor Rules V2 already exist at {target_path}"

        # Create the rules directory
        os.makedirs(rules_dir, exist_ok=True)

        # Step 1: Extract governance data from Notion and Linear
        logger.info("Extracting governance data from Notion and Linear...")
        governance_data = extract_governance_data()

        # Step 2: Get the LLM client for formatting
        llm_client = get_llm_client()

        # Step 3: Format data for template injection
        formatted_data = {
            "ALLOWED_TECH_STACK": llm_client.format_tech_stack(governance_data.get("ALLOWED_TECH_STACK", "Unknown/Detect from Codebase")),
            "FORBIDDEN_LIBRARIES": llm_client.format_forbidden_libs(governance_data.get("FORBIDDEN_LIBRARIES", "Unknown/Detect from Codebase")),
            "AUTH_PROVIDER": governance_data.get("AUTH_PROVIDER", "Unknown/Detect from Codebase"),
            "SECURITY_LEVEL": governance_data.get("STRICTNESS_LEVEL", "Unknown/Detect from Codebase"),
            "ACTIVE_TASKS_CONTEXT": governance_data.get("active_tasks_context", "- No active tasks found"),
            "GENERATION_TIMESTAMP": governance_data.get("generation_timestamp", "Unknown")
        }

        # Step 4: Load and render the template
        template = get_governance_template()
        final_rules = template.format(**formatted_data)

        # Step 5: Write the governance rules
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(final_rules)

        # If we migrated from legacy, remove the old file
        if migrated_legacy:
            try:
                os.remove(legacy_path)
                logger.info(f"Migrated legacy .cursorrules to new structure and removed old file")
            except Exception as e:
                logger.warning(f"Could not remove legacy .cursorrules file: {e}")

        # Generate success message with active rules
        active_rules = []
        if governance_data.get("ALLOWED_TECH_STACK") and governance_data["ALLOWED_TECH_STACK"] != "Unknown/Detect from Codebase":
            active_rules.append("Enforcing approved tech stack")
        if governance_data.get("FORBIDDEN_LIBRARIES") and governance_data["FORBIDDEN_LIBRARIES"] != "Unknown/Detect from Codebase":
            active_rules.append("Blocking forbidden libraries")

        rules_summary = " | ".join(active_rules) if active_rules else "Safe defaults applied (ask user for clarification)"

        logger.info(f"Bootstrap completed successfully. Installed at: {target_path}")
        action = "migrated and installed" if migrated_legacy else "installed"
        return f"✅ Governance Active: {rules_summary}. Founder OS 'Brain' {action} at: {target_path}"
    except Exception as e:
        logger.exception(f"Failed to bootstrap project at {target_dir}")
        return f"❌ Error initializing: {str(e)}"


def refresh_governance_rules(target_dir: str) -> str:
    """
    REFRESH COMMAND: Updates the existing governance rules file with fresh data from Notion and Linear.

    This function re-extracts governance data and regenerates the rules file.
    Useful when project specifications or active tasks have changed.

    Args:
        target_dir: The project directory containing the existing governance rules.

    Returns:
        Success or error message string.
    """
    try:
        logger.info(f"Received request for tool: refresh_governance_rules. Target directory: {target_dir}")

        # Clean the path and locate existing rules
        abs_target_dir = os.path.abspath(target_dir)
        rules_dir = os.path.join(abs_target_dir, ".cursor", "rules")
        target_path = os.path.join(rules_dir, "founder-os-governance.mdc")

        # Check if rules file exists
        if not os.path.exists(target_path):
            logger.warning(f"Governance rules not found at {target_path}")
            return f"❌ Error: No governance rules found at {target_path}. Run bootstrap_project first."

        # Step 1: Extract fresh governance data
        logger.info("Refreshing governance data from Notion and Linear...")
        governance_data = extract_governance_data()

        # Step 2: Get the LLM client for formatting
        llm_client = get_llm_client()

        # Step 3: Format data for template injection
        formatted_data = {
            "ALLOWED_TECH_STACK": llm_client.format_tech_stack(governance_data.get("ALLOWED_TECH_STACK", "Unknown/Detect from Codebase")),
            "FORBIDDEN_LIBRARIES": llm_client.format_forbidden_libs(governance_data.get("FORBIDDEN_LIBRARIES", "Unknown/Detect from Codebase")),
            "AUTH_PROVIDER": governance_data.get("AUTH_PROVIDER", "Unknown/Detect from Codebase"),
            "SECURITY_LEVEL": governance_data.get("STRICTNESS_LEVEL", "Unknown/Detect from Codebase"),
            "ACTIVE_TASKS_CONTEXT": governance_data.get("active_tasks_context", "- No active tasks found"),
            "GENERATION_TIMESTAMP": governance_data.get("generation_timestamp", "Unknown")
        }

        # Step 4: Load and render the template
        template = get_governance_template()
        final_rules = template.format(**formatted_data)

        # Step 5: Overwrite the existing rules file
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(final_rules)

        # Generate success message with updated rules
        active_rules = []
        if governance_data.get("allowed_tech") and governance_data["allowed_tech"][0] != "Unknown/Detect from Codebase":
            active_rules.append(f"Enforcing {len(governance_data['allowed_tech'])} approved technologies")
        if governance_data.get("forbidden_libs") and governance_data["forbidden_libs"][0] != "Unknown/Detect from Codebase":
            active_rules.append(f"Blocking {len(governance_data['forbidden_libs'])} forbidden libraries")

        rules_summary = " | ".join(active_rules) if active_rules else "Safe defaults applied (ask user for clarification)"

        logger.info(f"Governance rules refreshed successfully at: {target_path}")
        return f"🔄 Governance Refreshed: {rules_summary}. Rules updated at: {target_path}"
    except Exception as e:
        logger.exception(f"Failed to refresh governance rules at {target_dir}")
        return f"❌ Error refreshing rules: {str(e)}"

