

# 🚀 Founder OS (Alpha v0.1)

Founder OS is an intelligent context bridge that connects your development environment (Cursor) directly to your "Source of Truth" (Notion) and data layer (Supabase).

It eliminates context switching by granting your AI agent real-time access to technical specifications, roadmaps, and architectural governance. With Founder OS, the AI doesn't just write code—it follows your project's "Constitution."

---

## ⚡ Quick Start (Zero Friction Setup)

We have automated the setup process. No manual JSON editing or path configuration is required.

### 1. Clone the Repository

```bash
git clone https://github.com/IdanSarfati/founder-os-mcp.git
cd founder-os-mcp

```

### 2. Run the Installer

Execute the master installation script. It will create your environment and check your connections.

```bash
python install_script.py

```

**What the installer does:**

* ✅ **Dependencies:** Installs all Python libraries.
* 🔑 **Authentication:** Generates your `.env` file securely.
* 🩺 **Health Check:** Validates your API Keys immediately.
* 🔌 **Auto-Injection:** Registers the server in `.cursor/mcp.json`.

### 3. Final Step: Refresh & Verify

1. Open Cursor.
2. Press `Ctrl+Shift+P` (Windows) or `Cmd+Shift+P` (Mac).
3. Type "Developer: Reload Window" and press Enter.

**Verification:**
Go to **Cursor Settings** (`Ctrl+Shift+J`) > **Features** > **MCP Servers**.
You should see `founder-os` with a **Green Light** 🟢.

---

## 🔄 Updates & Maintenance

The system includes a **"Heartbeat"** mechanism. If a new version is released, the AI will notify you directly in the chat with a `🚨 UPDATE AVAILABLE` alert.

**To update, simply run:**

**Windows:**
Double-click `update.bat` in the project folder.

**Mac / Linux:**
Run this in your terminal:

```bash
./update.sh

```

*(This automatically pulls the latest code and updates dependencies).*

---

## 🧠 Activating the AI Architect

Whenever you start a new coding session, open the Composer (`Cmd/Ctrl + I`) and type:

```
"Initialize Founder OS"

```

**How it works:**
The agent will execute the `bootstrap_project` tool, injecting a local `.cursorrules` file into your folder. From that moment, the AI will enforce your architecture constraints (e.g., "Do not use SQLite," "Follow Clean Architecture").

---

## 🛠 Core Features (MCP Tools)

| Tool | Capability |
| --- | --- |
| `search_notion` | Scans your Notion workspace for PRDs, Specs, and Tasks. |
| `fetch_project_context` | Reads full page content to feed the AI deep project knowledge. |
| `append_to_page` | Allows the AI to document progress or update logs in Notion. |
| `list_directory` | Scans local files to prevent duplicate code and maintain structure. |
| `list_linear_tasks` | Lists active issues (assigned + team). |
| `get_linear_task_details` | Fetches rich details for a specific Linear task (e.g., `IDA-6`). |
| `bootstrap_project` | Deploys the project "Brain" (`.cursorrules`). |

---

## 🔗 Using the Linear Integration

If you added your Linear API Key, you can manage tasks directly from the chat:

* **See your tasks:** Ask *"List my Linear tasks"* (The AI will show status, priority, and ID).
* **Start working:** Ask *"Get details for task IDA-6"* (The AI will read the ticket description and search Notion for relevant specs).

---

## 🔍 Troubleshooting (Flight Recorder)

If the system ignores your context or behaves unexpectedly, we have a built-in logging system.

1. **Don't panic.** The system records its decision-making process.
2. Locate the file `founder_os.log` in the project root folder.
3. Send this file to the support team.
* *Note: API Keys and sensitive tokens are automatically masked in the logs for your privacy.*



---

## 📋 Prerequisites

* **Python 3.10+**
* **Notion Integration:**
* Create an internal integration at [Notion My Integrations](https://www.notion.so/my-integrations).
* **Grant Access:** You MUST share each specific Notion page with your integration (`...` -> `Connections` -> `Connect to` -> `Founder OS`).


* **Linear API Key:** (Optional) Add to `.env` to enable task management.

---

## 🛡 License

Internal Use Only - Founder OS Proprietary.

