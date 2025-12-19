from mcp.server.fastmcp import FastMCP
from config.auth_config import load_auth_config

# Import modular tools
from src.tools.notion_context import search_notion, fetch_project_context, append_to_page
from src.tools.fs import list_directory
from config.setup_governance import install_rules as _install_rules_logic

# 1. Validate Auth on Startup
try:
    config = load_auth_config()
    print(f"[OK] Auth Loaded. Notion Key present: {bool(config.notion_api_key)}")
except ValueError as e:
    print(f"[WARN] Startup Warning: {e}")
    print("Run 'python -m config.setup_full' to configure credentials.")

# 2. Initialize Server
mcp = FastMCP("Founder OS")

# 3. Register Tools
mcp.add_tool(search_notion)
mcp.add_tool(fetch_project_context)
mcp.add_tool(append_to_page)
mcp.add_tool(list_directory)

# --- NEW: The "Initialize" Tool ---
@mcp.tool()
def bootstrap_project() -> str:
    """
    INITIALIZE COMMAND: Installs the Founder OS 'Brain' (.cursorrules) into the current project.
    Use this when the user says 'Initialize Founder OS' or 'Setup Project'.
    """
    try:
        # We reuse the logic from our setup script
        _install_rules_logic()
        return "✅ Success: Founder OS 'Brain' (.cursorrules) has been installed. The strict architecture rules are now active."
    except Exception as e:
        return f"❌ Error initializing: {str(e)}"

if __name__ == "__main__":
    mcp.run()