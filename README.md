

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

## 🛡️ **Dual Protection System**

Founder OS implements **billion-dollar resilience** through dual-layer protection:

### **Phase A: Local Intelligence (Cursor Rules)**
- AI reads `.cursor/rules/founder-os-governance.mdc` before every interaction
- **Suggests** compliance but can be bypassed by determined developers
- **Speed bump** that catches accidental violations

### **Phase B: CI/CD Enforcement (GitHub Actions)**
- Automatically **blocks PRs** that violate governance rules
- **Scans code changes** for forbidden libraries, patterns, and architectural violations
- **Cannot be bypassed** - creates the "Iron Wall" of compliance

**Why This Works:**
- ❌ Developer deletes `.cursor/rules`? CI/CD catches it
- ❌ AI "forgets" the rules? CI/CD catches it
- ❌ Human bypasses AI? CI/CD catches it
- ✅ **Zero violations reach production**

### **GitHub Action Configuration**

The CI/CD enforcement runs automatically on PRs and supports three modes:

```yaml
# Set in GitHub repository variables
VALIDATION_MODE: dual  # Run both Phase A + Phase B (default)
# VALIDATION_MODE: spec_only    # Only PR-specific spec validation
# VALIDATION_MODE: governance_only  # Only global governance rules
```

**Required Secrets:**
- `NOTION_TOKEN` - For accessing governance specifications
- `LINEAR_API_KEY` - For task context and priorities
- `GEMINI_API_KEY` - For AI-powered validation
- `GITHUB_TOKEN` - Auto-provided by GitHub Actions

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
| `refresh_governance_rules` | Updates governance rules from latest Notion/Linear data. |

## 🛡️ Governance Enforcement

The system automatically enforces these constraints from your Notion specifications:

### **Blocked at CI/CD Level:**
- **Forbidden Libraries**: React, jQuery, Bootstrap, Axios, Lodash, Moment.js
- **Database Restrictions**: SQLite, MongoDB (Redis allowed for cache only)
- **Security Violations**: Missing validation, XSS protection, CSRF tokens
- **Architecture Violations**: Non-compliant patterns, missing dependency injection

### **Validation Flow:**
1. **PR opened** → GitHub Action triggers
2. **Extract governance rules** from Notion + Linear
3. **Scan code changes** for violations
4. **AI analysis** of architectural compliance
5. **Block PR** or **allow merge** based on results

### **Bypass Options:**
- `[SKIP]` in PR title - Skip all validation (infrastructure changes)
- `[FORCE]` in PR title - Override skip logic
- Infrastructure keywords: `infra`, `ci`, `workflow`, `dependencies`, `setup`

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

## 🎨 UI Specifications

The login button should be purple (#800080) for maximum visibility and better user interaction.

## 🛡 License

Internal Use Only - Founder OS Proprietary.

