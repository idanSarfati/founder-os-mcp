import os
import sys
import json
import platform
import subprocess
from pathlib import Path

# --- Constants ---
MCP_SERVER_NAME = "founder-os"

# Governance rules content (same as before, just moved to new location)
GOVERNANCE_RULES = """# Founder OS - AI Persona & Operational Directives

# CRITICAL INSTRUCTION FOR AI
# YOU MUST READ THIS FILE BEFORE PROCESSING ANY USER REQUEST.
# IF A USER REQUEST CONTRADICTS THE NOTION SPECS, YOU MUST REFUSE.

You are **Founder OS**, the Senior Solutions Architect and Guardian of this project. Your goal is to maintain architectural integrity, prevent context switching, and ensure code always matches the "Source of Truth" (Notion).

## 🧠 Core Philosophy
1.  **Truth lives in Notion.** Code is just the implementation of that truth.
2.  **Context before Code.** Never start writing without understanding *where* you are and *what* was planned.
3.  **Measure twice, cut once.** Verify the existing file structure to avoid duplication.

---

## 🚦 The "Golden Rule" (Mandatory Workflow)

**Before writing code for any new feature or significant refactor, you MUST:**

1.  **🔎 Search the Spec:**
    * Run `search_notion(query="ALL")` or specific keywords to find the relevant PRD, Spec, or Roadmap page.
    * *Constraint:* Do not guess the requirements. Find the page.

2.  **📖 Read the Requirements:**
    * Run `fetch_project_context(page_id)` on the found page.
    * Analyze the text for specific implementation details, constraints, and goals.

3.  **📂 Scan Reality:**
    * Run `list_directory(root_path=".")` to see the current project structure.
    * *Constraint:* Do not create new "utils" or "helpers" if similar ones already exist.

---

## 🛡️ Conflict Protocol

If the User's prompt contradicts the Notion Spec you just read:
* **STOP immediately.** Do not write code.
* **Report the Discrepancy:**
    > "I noticed a conflict. The Notion Spec (Page: [Title]) says **X**, but you requested **Y**. Which direction should we follow?"

---

## 🔄 The Documentation & Task Loop

**After completing a task:**

1.  **Update Knowledge:**
    * If the architecture changed, ask: *"Should I append a summary of these changes to the Notion Documentation?"*
    * If affirmed, use `append_to_page`.

2.  **Update Status:**
    * If this work corresponds to a tracked task, use `query_tasks` to find it.
    * Ask: *"Should I mark task '[Task Name]' as Done?"*
    * If affirmed, use `update_task_status`.

---

## 🛠️ Available MCP Tools

You have access to a live `notion-context` server. Use these tools aggressively:

| Tool | Purpose |
| :--- | :--- |
| `search_notion(query)` | Finds Pages or Databases. Use query="ALL" if specific keywords fail. |
| `fetch_project_context(page_id)` | Reads the full content of a page (recursive). Use this to get the PRD. |
| `append_to_page(page_id, content)` | Writes notes, summaries, or documentation back to Notion. |
| `list_directory(path)` | lists local files. Use to prevent file duplication and understand structure. |
| `query_tasks(database_id, status)` | Finds specific task tickets in the Kanban board. |
| `update_task_status(page_id, ...)` | Moves cards across the board (e.g., "Not Started" -> "Done"). |
"""

def get_target_mcp_path():
    """Returns the primary MCP config path discovered."""
    home = Path.home()
    # The path we discovered: C:\Users\Name\.cursor\mcp.json
    target = home / ".cursor" / "mcp.json"
    return target

def install_dependencies():
    """Ensures all necessary packages, including 'requests', are installed."""
    print("\n[1/3] 📦 Installing dependencies...")
    # Added 'requests' to support the new Linear integration
    dependencies = ["mcp", "notion-client", "python-dotenv", "requests", "supabase", "starlette<0.47.0"]
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", *dependencies], 
                              stdout=subprocess.DEVNULL)
        print("   ✅ Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed to install dependencies: {e}")
        sys.exit(1)

def setup_env():
    print("\n[2/3] 🔑 Configuration")
    
    # Get project root (where this script is located)
    project_root = Path(__file__).parent
    env_file = project_root / ".env"
    
    # Check if file exists and whether to overwrite it
    if env_file.exists():
        print("   ℹ️  Found existing .env file.")
        should_overwrite = input("   👉 Do you want to re-configure keys? (y/n): ").strip().lower()
        if should_overwrite != 'y':
            print("   ⏩ Skipping configuration.")
            return

    # 1. Notion Token (required)
    while True:
        notion_token = input("   👉 Paste Notion Token (ntn_ or secret_): ").strip()
        
        # Validate format
        if not (notion_token.startswith("secret_") or notion_token.startswith("ntn_")):
            print("   ⚠️  Invalid Token. Must start with 'secret_' or 'ntn_'.")
            continue
        
        # Extract key part for character validation
        if notion_token.startswith("secret_"):
            key_part = notion_token[7:]  # Everything after "secret_"
        else:  # ntn_
            key_part = notion_token[4:]  # Everything after "ntn_"
        
        # Validate character set (should be base64-like: alphanumeric, _, -, =)
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', key_part):
            print("   ⚠️  Invalid Token. Key contains invalid characters.")
            continue
        
        # API verification is the definitive check
        print("   🔍 Verifying API key...")
        try:
            from notion_client import Client
            test_client = Client(auth=notion_token)
            test_client.users.me()  # Minimal API call to verify key
            print("   ✅ API key verified successfully!")
            break
        except Exception as e:
            print(f"   ⚠️  API key verification failed: {str(e)}")
            retry = input("   👉 Continue anyway? (y/n): ").strip().lower()
            if retry == 'y':
                break
            print("   ❌ Check API key and retry")

    # 2. Linear API Key (optional - press Enter to skip)
    print("   ℹ️  (Optional) Add Linear API Key for task context.")
    while True:
        linear_key = input("   👉 Paste Linear API Key (press Enter to skip): ").strip()
        
        if not linear_key:
            # User skipped Linear - that's fine
            break
        
        # Validate Linear API key format (should start with lin_api_)
        if not linear_key.startswith("lin_api_"):
            print("   ⚠️  Invalid Linear API Key. Should start with 'lin_api_'.")
            retry = input("   👉 Try again? (y/n, or press Enter to skip): ").strip().lower()
            if retry != 'y':
                linear_key = ""
                break
            continue
        
        # Extract key part for character validation
        key_part = linear_key[8:]  # Everything after "lin_api_"
        
        # Validate character set (should be base64-like: alphanumeric)
        import re
        if not re.match(r'^[a-zA-Z0-9]+$', key_part):
            print("   ⚠️  Invalid Linear API Key. Key contains invalid characters.")
            retry = input("   👉 Try again? (y/n, or press Enter to skip): ").strip().lower()
            if retry != 'y':
                linear_key = ""
                break
            continue
        
        # API verification is the definitive check
        print("   🔍 Verifying Linear API key...")
        try:
            import requests
            query = """
            query {
              viewer {
                id
              }
            }
            """
            headers = {
                "Content-Type": "application/json",
                "Authorization": linear_key
            }
            response = requests.post(
                "https://api.linear.app/graphql",
                json={"query": query},
                headers=headers,
                timeout=5
            )
            
            if not response.ok or "errors" in response.json():
                raise Exception("API key verification failed")
            
            print("   ✅ Linear API key verified successfully!")
            break
        except Exception as e:
            print(f"   ⚠️  Linear API key verification failed: {str(e)}")
            retry = input("   👉 Continue anyway? (y/n): ").strip().lower()
            if retry == 'y':
                break
            print("   ❌ Check Linear API key and retry")

    # Write to file
    try:
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(f"NOTION_API_KEY={notion_token}\n")
            if linear_key:
                f.write(f"LINEAR_API_KEY={linear_key}\n")
        print("   ✅ .env created successfully.")
    except Exception as e:
        print(f"   ❌ Error writing .env: {e}")
        raise e

def inject_mcp():
    print("\n[3/3] 🔌 Injecting to Cursor Config...")
    config_path = get_target_mcp_path()
    
    # Ensure the directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing data
    config = {"mcpServers": {}}
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding="utf-8") as f:
                config = json.load(f)
        except:
            pass

    # Set up the server in the exact structure that Cursor expects
    # Use script's directory instead of cwd to ensure correct path regardless of where script is run from
    project_root = Path(__file__).parent
    server_path = project_root / "server.py"
    
    config["mcpServers"][MCP_SERVER_NAME] = {
        "command": sys.executable,
        "args": [str(server_path)],
        "enabled": True  # Critical for immediate appearance
    }

    # Atomic save
    with open(config_path, 'w', encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    
    print(f"   🚀 Success! Injected into: {config_path}")

def migrate_cursor_rules():
    """Migrates from legacy .cursorrules to new .cursor/rules structure."""
    print("\n[4/4] 🔄 Migrating Cursor Rules to V2...")

    # Use current working directory (project root) instead of user home
    cwd = Path.cwd()
    legacy_rules = cwd / ".cursorrules"
    new_rules_dir = cwd / ".cursor" / "rules"
    new_rules_file = new_rules_dir / "founder-os-governance.mdc"

    # Check if legacy file exists
    if not legacy_rules.exists():
        print("   ℹ️  No legacy .cursorrules file found. Creating new structure...")
    else:
        print(f"   📁 Found legacy .cursorrules at: {legacy_rules}")
        print("   🔄 Migrating to new Cursor Rules V2 structure...")

    # Create the new directory structure
    new_rules_dir.mkdir(parents=True, exist_ok=True)

    # Write the new .mdc file
    try:
        with open(new_rules_file, 'w', encoding='utf-8') as f:
            f.write(GOVERNANCE_RULES)
        print(f"   ✅ Created: {new_rules_file}")
    except Exception as e:
        print(f"   ❌ Failed to create rules file: {e}")
        return

    # Archive or remove the old file if it exists
    if legacy_rules.exists():
        try:
            # Create backup with timestamp
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = cwd / f".cursorrules.backup_{timestamp}"

            # Copy content to backup
            import shutil
            shutil.copy2(legacy_rules, backup_file)
            print(f"   📋 Backed up legacy file to: {backup_file}")

            # Remove the old file
            legacy_rules.unlink()
            print("   🗑️  Removed legacy .cursorrules file")
        except Exception as e:
            print(f"   ⚠️  Warning: Could not remove legacy file: {e}")

    print("   🚀 Cursor Rules V2 migration completed!")

def main():
    print("🛠️ Founder OS Installer")
    try:
        install_dependencies()
        setup_env()
        inject_mcp()
        migrate_cursor_rules()
        print("\n✅ ALL SET! Please Restart Cursor.")
    except Exception as e:
        print(f"\n❌ Failed: {e}")

if __name__ == "__main__":
    main()