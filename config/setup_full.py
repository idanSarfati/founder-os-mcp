import sys
import os
import json
import platform
import subprocess
from pathlib import Path

# --- Configuration ---
MCP_SERVER_NAME = "founder-os"
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER_SCRIPT = os.path.join(REPO_ROOT, "server.py")

# --- Helpers ---

def get_cursor_settings_path():
    """Attempts to locate the Cursor MCP settings file based on OS."""
    system = platform.system()
    home = Path.home()
    
    # Common paths where Cursor/VS Code store global state
    # Note: 'cursor.mcp-manager' is the specific extension ID folder
    
    if system == "Windows":
        base = home / "AppData" / "Roaming" / "Cursor" / "User" / "globalStorage"
    elif system == "Darwin": # macOS
        base = home / "Library" / "Application Support" / "Cursor" / "User" / "globalStorage"
    elif system == "Linux":
        base = home / ".config" / "Cursor" / "User" / "globalStorage"
    else:
        return None

    # The specific path to MCP config
    # Note: This path is based on reverse-engineering Cursor's behavior. 
    # It might change in future versions, hence the try/catch later.
    return base / "cursor.mcp-manager" / "mcp.json"

def install_dependencies():
    print(f"\n[1/4] 📦 Installing Python Dependencies...")
    try:
        req_path = os.path.join(REPO_ROOT, "requirements.txt")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_path])
        print("   ✅ Dependencies installed.")
    except Exception as e:
        print(f"   ❌ Failed to install dependencies: {e}")
        sys.exit(1)

def run_sub_setups():
    print(f"\n[2/4] 🔐 Configuring Auth & Governance...")
    try:
        # Run setup_auth
        from config.setup_auth import main as setup_auth
        setup_auth()
        
        # Run setup_governance
        from config.setup_governance import install_rules
        install_rules()
        print("   ✅ Configuration complete.")
    except Exception as e:
        print(f"   ⚠️ Warning during sub-setup: {e}")

def register_mcp_server():
    print(f"\n[3/4] 🔌 Auto-Registering MCP Server...")
    
    settings_path = get_cursor_settings_path()
    if not settings_path:
        print("   ⚠️ Could not detect OS specific path. Skipping auto-registration.")
        return

    print(f"   🔎 Searching for Cursor config at: {settings_path}")
    
    # Create dir if needed (rare)
    if not settings_path.parent.exists():
        try:
            settings_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            print("   ⚠️ Could not create config directory. Skipping.")
            return

    # Load existing or create new
    config = {"mcpServers": {}}
    if settings_path.exists():
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    config = json.loads(content)
        except Exception as e:
            print(f"   ⚠️ Error reading existing config: {e}. Starting fresh.")

    # Inject our server
    # We use sys.executable to ensure we use the SAME python environment that is running this script
    config.setdefault("mcpServers", {})[MCP_SERVER_NAME] = {
        "command": sys.executable,
        "args": [SERVER_SCRIPT],
        "env": {}, # We rely on .env loading inside the script, or we could inject here
        "disabled": False,
        "autoApprove": []
    }

    # Save
    try:
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        print(f"   ✅ Successfully registered '{MCP_SERVER_NAME}' in Cursor!")
    except Exception as e:
        print(f"   ❌ Failed to write config: {e}")
        print(f"   👉 Manual Add Required: Command='python', Args='{SERVER_SCRIPT}'")

# --- Main ---

def main():
    print(f"🚀 Founder OS Installer (v0.1)")
    print(f"📂 Target Repo: {REPO_ROOT}")
    
    install_dependencies()
    run_sub_setups()
    register_mcp_server()
    
    print("\n" + "="*50)
    print("✅ INSTALLATION COMPLETE")
    print("👉 Please RESTART Cursor to load the new MCP server.")
    print("="*50)

if __name__ == "__main__":
    main()