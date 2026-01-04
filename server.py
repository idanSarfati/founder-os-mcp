import sys
from mcp.server.fastmcp import FastMCP
from config.auth_config import load_auth_config

# Import modular tools
from src.tools.notion_context import search_notion, fetch_project_context, append_to_page
from src.tools.fs import list_directory
from src.tools.project_ops import bootstrap_project, refresh_governance_rules
# Import health check utilities
# Import module directly to avoid Python import reference issues with global variables
from src.utils import health
from src.utils.health import is_update_available, get_update_notice  # Keep these for tool functions
# Import environment validation
from src.utils.validation import validate_environment
# Import logger
from src.utils.logger import logger

# Pre-flight validation: Check API connectivity before starting server
# Configure stdout for Windows Unicode support
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        # Python < 3.7 or reconfigure failed, use ASCII fallback
        pass

logger.info("🔍 Validating environment...")
is_valid, error_msg = validate_environment()

if not is_valid:
    logger.error(f"Configuration error: {error_msg}")
    sys.exit(1)  # Exit cleanly, don't crash

logger.info("✅ Environment looks good! Starting server...")

# 1. Validate Auth on Startup
try:
    config = load_auth_config()
    logger.info(f"Notion key loaded: {bool(config.notion_api_key)}")
except ValueError as e:
    logger.warning(f"Auth error: {e}")
    logger.warning("Run 'python -m config.setup_full' for credentials")

# 2. Initialize Linear Client (Optional - graceful degradation if missing)
linear_client = None
try:
    from src.integrations.linear_client import LinearClient
    linear_client = LinearClient()
    logger.info("Linear Client initialized.")
except (ValueError, ImportError) as e:
    logger.info(f"Linear disabled: {e}")
    logger.info("Add LINEAR_API_KEY to enable Linear tools")

# 3. Initialize Server
mcp = FastMCP("Founder OS")
logger.info("MCP server initialized: Founder OS")

# 4. Register Core Tools (Always Available)
mcp.add_tool(search_notion)
mcp.add_tool(fetch_project_context)
mcp.add_tool(append_to_page)
mcp.add_tool(list_directory)
logger.info("Core tools registered")

# 5. Register Linear Tools (Conditional - only if client is available)
if linear_client:
    logger.info("Linear tools registered")
    
    @mcp.tool()
    def list_linear_tasks() -> str:
        """
        List all active tasks assigned to the current user in Linear, including team issues.
        
        Returns tasks that are not "Done" or "Canceled". Use this to understand current priorities
        and get an overview of work items.
        """
        try:
            logger.info("Processing list_linear_tasks")
            response_text = linear_client.get_active_tasks()

            if is_update_available():
                response_text = get_update_notice() + response_text

            logger.success("list_linear_tasks completed")
            return response_text
        except Exception as e:
            logger.exception("Failed to fetch Linear tasks")
            error_msg = f"❌ Error fetching Linear tasks: {str(e)}"
            if is_update_available():
                error_msg = get_update_notice() + error_msg
            return error_msg

    @mcp.tool()
    def update_linear_task_status(task_id: str, new_status: str) -> str:
        """
        Update the status of a specific Linear task (e.g., 'LIN-101' or 'IDA-8').

        Args:
            task_id: Linear issue identifier (e.g., 'IDA-8', 'LIN-101')
            new_status: New status name (e.g., 'Done', 'In Progress', 'Backlog')

        Returns:
            Success message or error details
        """
        try:
            logger.info(f"Processing update_linear_task_status: {task_id} -> {new_status}")
            response_text = linear_client.update_task_status(task_id, new_status)

            if is_update_available():
                response_text = get_update_notice() + response_text

            logger.success("update_linear_task_status completed")
            return response_text
        except Exception as e:
            logger.exception(f"Failed to update Linear task status for {task_id}")
            error_msg = f"❌ Error updating Linear task status: {str(e)}"
            if is_update_available():
                error_msg = get_update_notice() + error_msg
            return error_msg

    @mcp.tool()
    def get_linear_task_details(task_id: str) -> str:
        """
        Fetch full description and metadata for a specific Linear task (e.g., 'LIN-101' or 'IDA-8').
        
        Returns detailed information including description, labels, status, and priority.
        
        INSTRUCTION: After receiving task details, use relevant keywords from the title, labels,
        and description to search_notion for related technical specifications, architectural
        constraints, or implementation guidelines. This creates a semantic bridge between the
        "Action Layer" (Linear tasks) and the "Source of Truth" (Notion specs).
        """
        try:
            logger.info(f"Processing get_linear_task_details: {task_id}")
            response_text = linear_client.get_task_details(task_id)

            if is_update_available():
                response_text = get_update_notice() + response_text

            logger.success("get_linear_task_details completed")
            return response_text
        except Exception as e:
            logger.exception(f"Failed to fetch Linear task details for {task_id}")
            error_msg = f"❌ Error fetching task details: {str(e)}"
            if is_update_available():
                error_msg = get_update_notice() + error_msg
            return error_msg

# 6. Register Bootstrap Tools
mcp.add_tool(bootstrap_project)
mcp.add_tool(refresh_governance_rules)
logger.info("Bootstrap tools registered: bootstrap_project, refresh_governance_rules")

# 7. Check for Updates on Startup and Set Global State
# IMPORTANT: This must run BEFORE mcp.run() to set the global flag
logger.debug("===== SERVER STARTUP: Update Check =====")

try:
    logger.debug("Starting update check...")
    
    has_updates = health.check_for_updates()  # This sets UPDATE_AVAILABLE global flag
    logger.debug(f"check_for_updates() returned: {has_updates}")
    logger.debug(f"health.UPDATE_AVAILABLE after check: {health.UPDATE_AVAILABLE}")
    logger.debug(f"is_update_available() after check: {health.is_update_available()}")
    
    if has_updates:
        logger.info("Update available detected")
        health.print_update_banner()
    else:
        logger.debug("No updates available")
except Exception as e:
    # Don't fail server startup if update check fails
    logger.warning(f"Update check failed: {e}")
    logger.exception("Update check exception details")

if __name__ == "__main__":
    logger.success("Server ready")
    mcp.run()