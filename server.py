import os
from mcp.server.fastmcp import FastMCP
from config.auth_config import load_auth_config

# Import modular tools
from src.tools.notion_context import search_notion, fetch_project_context, append_to_page
from src.tools.fs import list_directory
# We import the RULES string, but NOT the install logic
from config.setup_governance import GOVERNANCE_RULES

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
            return linear_client.get_active_tasks()
        except Exception as e:
            return f"❌ Error fetching Linear tasks: {str(e)}"

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
            return linear_client.get_task_details(task_id)
        except Exception as e:
            return f"❌ Error fetching task details: {str(e)}"

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

if __name__ == "__main__":
    mcp.run()