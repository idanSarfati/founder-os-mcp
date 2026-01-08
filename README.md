

# 🚀 Founder OS (Beta v1.0)

Founder OS is an intelligent context bridge that connects your development environment (Cursor) directly to your "Source of Truth" (Notion) and data layer (Supabase).

It eliminates context switching by granting your AI agent real-time access to technical specifications, roadmaps, and architectural governance. With Founder OS, the AI doesn't just write code—it follows your project's "Constitution."

---

## ⚡ Dual-Track Installation (Choose Your Path)

Founder OS supports two installation methods based on your security and compliance requirements.

### Option A: Quick Start (Marketplace Installation)
*For small teams and individual developers*

```bash
# Coming Soon: One-click marketplace installation
# Visit: https://github.com/marketplace/founder-os
```

**Benefits:**
- ⚡ Zero setup time
- 🔄 Automatic updates
- 🛡️ Marketplace security guarantees

---

### Option B: Enterprise Installation (Fork-to-Own)
*For SOC2-compliant enterprises and security-conscious teams*

#### Step 1: Fork & Audit

```bash
# Fork this repository to your organization
git clone https://github.com/YOUR-ORG/founder-os-mcp.git
cd founder-os-mcp

# Run security audit before installation
./audit_check.sh
```

#### Step 2: Manual Installation

```bash
# Install dependencies securely
pip install -r requirements.txt

# Configure environment (create .env file)
cp .env.example .env
# Edit .env with your API keys
```

#### Step 3: Verify & Connect

```bash
# Run health check
python -c "from src.utils.health import run_health_check; run_health_check()"

# Register with Cursor
python install_script.py
```

**Enterprise Benefits:**
- 🔍 **Full Code Audit**: Review every line before deployment
- 🛡️ **Supply Chain Security**: Dependencies pinned with SHA256 hashes
- 🔒 **Air-Gapped Ready**: No external dependencies required
- 📋 **Self-Verification**: Built-in audit tools confirm security boundaries

---

## 🔒 Privacy & Data Policy

**We do not store your code. We only transmit logic metadata to OpenAI for reasoning. Zero logs retained.**

### Data Handling Guarantee
- **No Code Storage**: Your source code never leaves your environment
- **Metadata Only**: Only structural information (function names, imports, patterns) is analyzed
- **Zero Retention**: No conversation logs or analysis results are stored
- **Local Processing**: All governance rules are processed locally when possible

### Network Communications
Founder OS communicates only with declared APIs:
- **Linear API**: Task context and project priorities
- **Notion API**: Technical specifications and governance rules
- **OpenAI/Gemini API**: AI-powered code analysis (logic metadata only)
- **Git Operations**: Local subprocess calls for code analysis

### Enterprise Security
For SOC2-compliant deployments, use Option B (Fork-to-Own) installation:
- Run `./audit_check.sh` to verify network boundaries
- Audit all dependencies in `requirements.txt`
- Review source code for security compliance
- Self-host if required for air-gapped environments

---

## 🛡️ **Trust Engine: Intelligent Governance**

Founder OS implements **intelligent governance** through a dual-layer protection system that balances **security** with **development velocity**:

### **Phase A: Local Intelligence (Cursor Rules)**
- AI reads `.cursor/rules/founder-os-governance.mdc` before every interaction
- **Suggests** compliance but can be bypassed by determined developers
- **Speed bump** that catches accidental violations

### **Phase B: Trust Engine (GitHub Actions)**
- **Smart scoring** with 0-100 confidence levels instead of binary blocking
- **Contextual enforcement** based on violation severity and business needs
- **Emergency overrides** with full audit trails for justified exceptions
- **Adaptive thresholds:** Critical violations blocked, suspicious code flagged for review

**Why This Works:**
- ✅ **Critical violations:** Automatically blocked (maintains security)
- ✅ **Suspicious code:** Warned with override options (preserves velocity)
- ✅ **Emergency fixes:** Override mechanisms with audit logging (business continuity)
- ✅ **Zero blind blocking:** AI-powered risk assessment prevents false positives

### **Technical Implementation:**

**Phase A (Local Intelligence):**
- Cursor Rules V2 structure: `.cursor/rules/founder-os-governance.mdc`
- Dynamic rule injection via `bootstrap_project` MCP tool
- Real-time AI guidance during development
- Speed bump preventing accidental violations

**Phase B (Trust Engine):**
- GitHub Actions workflow: `.github/workflows/action-guard.yml`
- Python validation script: `.github/scripts/action-guard.py`
- **Trust Scoring:** 0-100 confidence levels with smart thresholds
- **Override System:** Label and text-based emergency bypass mechanisms
- **Audit Logging:** Automatic Linear ticket creation for governance events
- **AI Analysis:** Gemini API for nuanced risk assessment
- **Smart Enforcement:** Blocks critical violations, warns on suspicious code

### **Trust Engine Configuration**

The Trust Engine runs automatically on PRs with intelligent scoring and override capabilities:

```yaml
# Set in GitHub repository variables
VALIDATION_MODE: dual  # Run both spec + governance validation (default)
# VALIDATION_MODE: spec_only    # Only PR-specific spec validation
# VALIDATION_MODE: governance_only  # Only global governance rules
```

#### **Trust Scoring Thresholds:**
- **0-50:** 🚫 **Critical** - Hard block (security violations, forbidden libraries)
- **51-80:** ⚠️ **Suspicious** - Soft block with override option
- **81-100:** ✅ **Safe** - Auto-approve

#### **Override Mechanisms:**
- **Label Override:** Add `governance-override` label to PR
- **Text Override:** Include `[override: detailed reason]` in PR description
- **Audit Trail:** All overrides create Linear tickets for CTO review

**Required Secrets:**
- `NOTION_TOKEN` - For accessing governance specifications
- `LINEAR_API_KEY` - For task context and priorities
- `OPENAI_API_KEY` - For governance rule extraction and normalization
- `GEMINI_API_KEY` - For CI/CD PR validation analysis
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

## ✅ Trust & Verification

### GitHub Verified Creator Program
Founder OS is committed to security and transparency. We have applied for GitHub's Verified Creator program to provide additional trust signals:

- **Application Status**: Submitted and under review
- **Verification Benefits**: Official badges and enhanced security guarantees
- **Timeline**: 2-4 weeks for initial review

### Self-Verification Tools
Run our built-in audit tools to verify security compliance:

```bash
# Security audit and trust verification
./audit_check.sh

# Health check and connectivity validation
python -c "from src.utils.health import run_health_check; run_health_check()"
```

### Enterprise Compliance
- **SOC2 Ready**: Designed for SOC2 Type II compliance
- **Supply Chain Security**: All dependencies pinned with SHA256 hashes
- **Code Transparency**: 100% open source with no obfuscation
- **Audit Trail**: Built-in governance logging and override mechanisms

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

The system **dynamically extracts** governance rules from your Notion workspace and Linear tasks, ensuring enforcement stays current with your evolving technical specifications.

### **Dynamic Rule Extraction:**
The CI/CD system queries your "Source of Truth" to extract:
- **Approved Tech Stack**: Only libraries and frameworks from your Notion specs
- **Forbidden Libraries**: Any libraries explicitly prohibited in your governance docs
- **Security Requirements**: Authentication strategies, validation rules, security standards
- **Architecture Patterns**: Dependency injection, code organization, design principles

### **Fallback Protection System:**

**Billion-Dollar Resilience:** The system maintains full enforcement even when external services fail:

**API Failure Scenarios:**
- Network outages or API rate limits
- Invalid or expired API keys
- Service maintenance or downtime
- Missing environment variables

**Automatic Fallback Logic:**
- **Primary**: Extract rules from Notion + Linear APIs (real-time)
- **Secondary**: Use cached governance data (if available)
- **Tertiary**: Enforce hardcoded baseline rules (never fails)

**Baseline Enforcement (Always Active):**
- **Forbidden Libraries**: React, jQuery, Bootstrap, Axios, Lodash, Moment.js
- **Database Restrictions**: SQLite, MongoDB (Redis allowed for cache only)
- **Security Violations**: Missing validation, XSS protection, CSRF tokens
- **Architecture Violations**: Non-compliant patterns, missing dependency injection

**Why This Matters:** Even if Notion, Linear, or the AI APIs go down, your codebase remains protected by the Trust Engine's intelligent governance.

### **Dual-LLM Architecture:**

Founder OS uses two AI models for maximum reliability and specialized capabilities:

**🤖 OpenAI (GPT Models):**
- **Purpose:** Governance rule extraction and normalization
- **When Used:** Bootstrap project, refresh governance rules
- **Task:** Convert unstructured Notion/Linear data into structured governance rules
- **Fallback:** Safe defaults when API unavailable

**🤖 Gemini (Flash Models):**
- **Purpose:** Real-time code validation and compliance checking
- **When Used:** CI/CD PR validation, architectural violation detection
- **Task:** Analyze git diffs against specifications, detect forbidden patterns
- **Fallback:** Conservative blocking when API unavailable

### **Trust Engine Flow:**
1. **PR opened** → GitHub Action triggers
2. **Extract governance rules** from Notion + Linear
3. **Check for override conditions** (label or text override)
4. **If override found** → Log to Linear + approve with audit trail
5. **If no override** → Run dual validation with trust scoring
6. **Apply thresholds:** Block critical (0-50), warn suspicious (51-80), pass safe (81-100)
7. **Post PR comments** with guidance and next steps

### **Override Options:**
- **Emergency Override:** Add `governance-override` label (requires justification)
- **Text Override:** Include `[override: detailed reason]` in PR description
- **Audit Logging:** All overrides create Linear tickets for CTO review

### **Legacy Options:**
- `[SKIP]` in PR title - Skip validation (infrastructure changes only)
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
* **AI API Keys:** Add `OPENAI_API_KEY` and `GEMINI_API_KEY` to `.env` for full AI-powered governance.

---

## 🛡 License

Internal Use Only - Founder OS Proprietary.

