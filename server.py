import os
import sys
from mcp.server.fastmcp import FastMCP
from config.auth_config import load_auth_config

# Import modular tools
from src.tools.notion_context import search_notion, fetch_project_context, append_to_page
from src.tools.fs import list_directory
# We import the RULES string, but NOT the install logic
from config.setup_governance import GOVERNANCE_RULES
# Import health check utilities
# Import module directly to avoid Python import reference issues with global variables
from src.utils import health
from src.utils.health import is_update_available, get_update_notice  # Keep these for tool functions
# Import environment validation
from src.utils.validation import validate_environment

# Pre-flight validation: Check API connectivity before starting server
# Configure stdout for Windows Unicode support
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        # Python < 3.7 or reconfigure failed, use ASCII fallback
        pass

print("🔍 Validating environment...")
is_valid, error_msg = validate_environment()

if not is_valid:
    print("\n" + "="*40)
    print(error_msg)
    print("="*40 + "\n")
    print("The server cannot start due to configuration errors.")
    sys.exit(1)  # Exit cleanly, don't crash

print("✅ Environment looks good! Starting server...")

# 1. Validate Auth on Startup
try:
    config = load_auth_config()
    print(f"[OK] Auth Loaded. Notion Key present: {bool(config.notion_api_key)}")
except ValueError as e:
    print(f"[WARN] Startup Warning: {e}")
    print("Run 'python -m config.setup_full' to configure credentials.")

# 2. Initialize Linear Client (Optional - graceful degradation if missing)
linear_client = None
try:
    from src.integrations.linear_client import LinearClient
    linear_client = LinearClient()
    print(f"[OK] Linear Client initialized.")
except (ValueError, ImportError) as e:
    print(f"[INFO] Linear integration disabled: {e}")
    print("     Add LINEAR_API_KEY to .env to enable Linear tools.")

# 3. Initialize Server
mcp = FastMCP("Founder OS")

# 4. Register Core Tools (Always Available)
mcp.add_tool(search_notion)
mcp.add_tool(fetch_project_context)
mcp.add_tool(append_to_page)
mcp.add_tool(list_directory)

# 5. Register Linear Tools (Conditional - only if client is available)
if linear_client:
    @mcp.tool()
    def list_linear_tasks() -> str:
        """
        List all active tasks assigned to the current user in Linear, including team issues.
        
        Returns tasks that are not "Done" or "Canceled". Use this to understand current priorities
        and get an overview of work items.
        """
        try:
            import sys
            sys.stderr.write(f"[DEBUG] list_linear_tasks called\n")
            sys.stderr.write(f"[DEBUG] is_update_available() in tool: {is_update_available()}\n")
            sys.stderr.flush()
            
            response_text = linear_client.get_active_tasks()
            
            if is_update_available():
                sys.stderr.write("[DEBUG] Injecting update notice into Linear tasks response\n")
                notice = get_update_notice()
                sys.stderr.write(f"[DEBUG] Notice length: {len(notice)}, first 100 chars: {repr(notice[:100])}\n")
                sys.stderr.write(f"[DEBUG] Response text length before: {len(response_text)}, first 100 chars: {repr(response_text[:100])}\n")
                response_text = notice + response_text
                sys.stderr.write(f"[DEBUG] Response text length after: {len(response_text)}, first 150 chars: {repr(response_text[:150])}\n")
                sys.stderr.flush()
            else:
                sys.stderr.write("[DEBUG] No update available, skipping notice injection\n")
                sys.stderr.flush()
            
            return response_text
        except Exception as e:
            error_msg = f"❌ Error fetching Linear tasks: {str(e)}"
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
            response_text = linear_client.get_task_details(task_id)
            if is_update_available():
                response_text = get_update_notice() + response_text
            return response_text
        except Exception as e:
            error_msg = f"❌ Error fetching task details: {str(e)}"
            if is_update_available():
                error_msg = get_update_notice() + error_msg
            return error_msg

# 6. Register Bootstrap Tool
@mcp.tool()
def bootstrap_project(target_dir: str) -> str:
    """
    INITIALIZE COMMAND: Installs the Founder OS 'Brain' (.cursorrules) into the specified project folder.
    The AI should provide the absolute path to the current project root.
    """
    try:
        # Clean the path
        target_path = os.path.join(os.path.abspath(target_dir), ".cursorrules")
        
        if os.path.exists(target_path):
             return f"ℹ️ Skipped: .cursorrules already exists at {target_path}"

        with open(target_path, "w", encoding="utf-8") as f:
            f.write(GOVERNANCE_RULES)
            
        return f"✅ Success: Founder OS 'Brain' installed at: {target_path}"
    except Exception as e:
        return f"❌ Error initializing: {str(e)}"

# 7. Check for Updates on Startup and Set Global State
# IMPORTANT: This must run BEFORE mcp.run() to set the global flag
import sys
sys.stderr.write("[DEBUG] ===== SERVER STARTUP: Update Check =====\n")
sys.stderr.flush()

try:
    sys.stderr.write("[DEBUG] Starting update check...\n")
    sys.stderr.flush()
    
    has_updates = health.check_for_updates()  # This sets UPDATE_AVAILABLE global flag
    sys.stderr.write(f"[DEBUG] check_for_updates() returned: {has_updates}\n")
    sys.stderr.write(f"[DEBUG] health.UPDATE_AVAILABLE after check: {health.UPDATE_AVAILABLE}\n")
    sys.stderr.write(f"[DEBUG] is_update_available() after check: {health.is_update_available()}\n")
    sys.stderr.flush()
    
    if has_updates:
        health.print_update_banner()
except Exception as e:
    # Don't fail server startup if update check fails
    sys.stderr.write(f"[WARN] Update check failed: {e}\n")
    import traceback
    sys.stderr.write(traceback.format_exc())
    sys.stderr.flush()

if __name__ == "__main__":
    mcp.run()