"""
Project operations and bootstrap functionality for Founder OS.

This module handles project initialization tasks, including installing
the Founder OS 'Brain' (.cursor/rules/founder-os-governance.mdc) into target directories.
Supports Cursor Rules V2 structure.
"""

import os
from config.setup_governance import GOVERNANCE_RULES
from src.utils.logger import logger


def bootstrap_project(target_dir: str) -> str:
    """
    INITIALIZE COMMAND: Installs the Founder OS 'Brain' (.cursor/rules/founder-os-governance.mdc) into the specified project folder.
    Supports Cursor Rules V2 structure.
    The AI should provide the absolute path to the current project root.

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

        # Write the governance rules
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(GOVERNANCE_RULES)

        # If we migrated from legacy, remove the old file
        if migrated_legacy:
            try:
                os.remove(legacy_path)
                logger.info(f"Migrated legacy .cursorrules to new structure and removed old file")
            except Exception as e:
                logger.warning(f"Could not remove legacy .cursorrules file: {e}")

        logger.info(f"Bootstrap completed successfully. Installed at: {target_path}")
        action = "migrated and installed" if migrated_legacy else "installed"
        return f"✅ Success: Founder OS 'Brain' {action} at: {target_path}"
    except Exception as e:
        logger.exception(f"Failed to bootstrap project at {target_dir}")
        return f"❌ Error initializing: {str(e)}"

