"""
Project operations and bootstrap functionality for Founder OS.

This module handles project initialization tasks, including installing
the Founder OS 'Brain' (.cursorrules) file into target directories.
"""

import os
from config.setup_governance import GOVERNANCE_RULES
from src.utils.logger import logger


def bootstrap_project(target_dir: str) -> str:
    """
    INITIALIZE COMMAND: Installs the Founder OS 'Brain' (.cursorrules) into the specified project folder.
    The AI should provide the absolute path to the current project root.
    
    Args:
        target_dir: The target directory where .cursorrules should be installed.
        
    Returns:
        Success or error message string.
    """
    try:
        logger.info(f"Received request for tool: bootstrap_project. Target directory: {target_dir}")
        
        # Clean the path
        target_path = os.path.join(os.path.abspath(target_dir), ".cursorrules")
        
        if os.path.exists(target_path):
            logger.info(f"Bootstrap skipped: .cursorrules already exists at {target_path}")
            return f"ℹ️ Skipped: .cursorrules already exists at {target_path}"

        with open(target_path, "w", encoding="utf-8") as f:
            f.write(GOVERNANCE_RULES)
        
        logger.info(f"Bootstrap completed successfully. Installed at: {target_path}")
        return f"✅ Success: Founder OS 'Brain' installed at: {target_path}"
    except Exception as e:
        logger.exception(f"Failed to bootstrap project at {target_dir}")
        return f"❌ Error initializing: {str(e)}"

