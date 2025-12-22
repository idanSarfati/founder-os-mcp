# 🚀 Founder OS (Alpha v0.1)

Founder OS is an intelligent context bridge that connects your development environment (Cursor) directly to your "Source of Truth" (Notion) and data layer (Supabase).

It eliminates context switching by granting your AI agent real-time access to technical specifications, roadmaps, and architectural governance. With Founder OS, the AI doesn't just write code—it follows your project's "Constitution."

---

## ⚡ Quick Start (One-Click Installation)

We have automated the setup process. No manual JSON editing or path configuration is required.

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/founder-os.git
cd founder-os
```

### 2. Run the Installer

Execute the master installation script and follow the prompts:

```bash
python install_script.py
```

**What the installer handles for you:**

- ✅ **Dependencies:** Installs all required Python libraries.
- 🔑 **Authentication:** Safely captures your Notion Token and generates your `.env` file.
- 🔌 **Auto-Injection:** Automatically detects your Cursor configuration folder (`.cursor/mcp.json`) and registers the server.

### 3. Final Step: Refresh Cursor

1. Open Cursor.
2. Press `Ctrl+Shift+P` (Windows) or `Cmd+Shift+P` (Mac).
3. Type "Developer: Reload Window" and press Enter.

---

## ✅ Installation Verification

To ensure everything is connected correctly:

1. Go to **Cursor Settings** (`Ctrl+Shift+J`).
2. Navigate to **Features > MCP Servers**.
3. You should see `founder-os` with a **Green Light** 🟢.
4. If the light is red, click the "Refresh" icon or check the logs in the **Output** panel (select "MCP" from the dropdown).

---

## 🧠 Activating the AI Architect

Whenever you start a new project or a new coding session, open the Composer (`Cmd/Ctrl + I`) and type:

```
"Initialize Founder OS"
```

**How it works:**

The agent will execute the `bootstrap_project` tool, injecting a local `.cursorrules` file into your folder. From that moment, the AI will enforce your architecture constraints (e.g., "Do not use SQLite," "Follow Clean Architecture") and will refuse to implement code that violates these rules.

> 💡 **Tip:** To get the best results, share the project's main page (Root Page) with the bot, and it will automatically find all sub-pages on its own.

---

## 🛠 Core Features (MCP Tools)

| Tool | Capability |
| :--- | :--- |
| `search_notion` | Scans your Notion workspace for PRDs, Specs, and Tasks. |
| `fetch_project_context` | Reads full page content to feed the AI deep project knowledge. |
| `append_to_page` | Allows the AI to document progress or update logs in Notion. |
| `list_directory` | Scans local files to prevent duplicate code and maintain structure. |
| `bootstrap_project` | Deploys the project "Brain" (`.cursorrules`) to any directory. |

---

## 📋 Prerequisites

- **Python 3.10+**
- **Notion Integration:**
  - Create an internal integration at [Notion My Integrations](https://www.notion.so/my-integrations).
  - **Grant Access:** You MUST share each specific Notion page with your integration. On the target page: Click `...` -> `Connections` -> `Connect to` -> Select **Founder OS**.
- **Supabase:** URL and API Key (Optional for early alpha).

---

## 🔍 Troubleshooting

**Server not appearing in Settings:**

- Ensure you ran `install_script.py` and performed a "Reload Window".

**"Permission Denied" in Notion:**

- Double-check that the specific page or database is shared with your Integration Connection.

**Windows Unicode Errors:**

- If you see charmap errors, ensure your terminal supports UTF-8.

---

## 🛡 License

Internal Use Only - Founder OS Proprietary.
