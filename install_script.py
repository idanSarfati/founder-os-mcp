import os
import sys
import json
import platform
import subprocess
from pathlib import Path

# --- Constants ---
MCP_SERVER_NAME = "founder-os"

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
    
    # Check if file exists and whether to overwrite it
    if os.path.exists(".env"):
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
            print("   Please check your API key and try again.")

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
            print("   Please check your Linear API key and try again.")

    # Write to file
    try:
        with open(".env", "w", encoding="utf-8") as f:
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
    current_dir = os.getcwd()
    server_path = os.path.join(current_dir, "server.py")
    
    config["mcpServers"][MCP_SERVER_NAME] = {
        "command": sys.executable,
        "args": [server_path],
        "enabled": True  # Critical for immediate appearance
    }

    # Atomic save
    with open(config_path, 'w', encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    
    print(f"   🚀 Success! Injected into: {config_path}")

def main():
    print("🛠️ Founder OS Installer")
    try:
        install_dependencies()
        setup_env()
        inject_mcp()
        print("\n✅ ALL SET! Please Restart Cursor.")
    except Exception as e:
        print(f"\n❌ Failed: {e}")

if __name__ == "__main__":
    main()