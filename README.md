# Founder OS (Alpha v0.1)

**Founder OS** is an intelligent context bridge that connects your development environment (Cursor) directly to your knowledge base (Notion) and data layer (Supabase). It prevents context switching by giving your AI agent real-time access to specs, roadmaps, and architectural rules.

---

## 🛠 Prerequisites

Before running the system, ensure you have:

1.  **Python 3.10+** installed.
2.  **Notion Integration Token:**
    * Create an internal integration at [Notion My Integrations](https://www.notion.so/my-integrations).
    * Share your target pages (Roadmap, Architecture) with this integration connection.
3.  **Supabase Project:**
    * You will need your project URL and `service_role` (or `anon`) key.
4.  **Clerk Account:**
    * For authentication services (Publishable Key & Secret Key).

---

## 📦 Installation

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/your-org/founder-os.git](https://github.com/your-org/founder-os.git)
    cd founder-os
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment**
    We have included a setup utility to generate your configuration safely. Run:
    ```bash
    python -m config.setup_auth
    ```
    * This will check for a `.env` file.
    * It will verify if all required keys (`NOTION_API_KEY`, `SUPABASE_URL`, etc.) are present.
    * If missing, it will add placeholders for you to fill in.

4.  **Verify Configuration**
    Open `.env` and confirm all values are filled in.

---

## 🖱️ Cursor MCP Configuration

To enable the AI "Brain," you must register the MCP server in Cursor.

1.  Open **Cursor Settings** (`Cmd/Ctrl` + `Shift` + `J`).
2.  Navigate to **Features** > **MCP Servers**.
3.  Click **+ Add New MCP Server**.
4.  Enter the following details:

| Field | Value |
| :--- | :--- |
| **Name** | `founder-os` |
| **Type** | `stdio` |
| **Command** | `python` |
| **Arguments** | `[ABSOLUTE_PATH_TO_REPO]/server.py` |

> **Note:** Replace `[ABSOLUTE_PATH_TO_REPO]` with the full path to your cloned folder (e.g., `/Users/idan/projects/founder-os/server.py`).

---

## ✅ Verification

Before asking the AI to write code, verify your "Engine Room" is connected.

1.  **Run the Smoke Test:**
    Open your terminal and run:
    ```bash
    python -m src.tools.verify_db
    ```
    * **Success:** You should see `✅ Connection Successful`.
    * **Failure:** If it fails, check your `.env` keys.

2.  **Test the Brain:**
    * Restart Cursor.
    * Open a new Chat (`Cmd/Ctrl` + `L`).
    * Type: *"What is the status of the Founder OS project?"*
    * **Success:** The AI should call `search_notion` or `list_directory` automatically.
---

## 🔧 Troubleshooting

* **Error: "Notion page not found"**
    * Ensure you have clicked `...` > `Connections` > `Connect to` on the specific Notion page and selected your integration.
* **Error: "Conflict Protocol Triggered"**
    * This is a feature, not a bug. If the AI refuses to write code (e.g., "I cannot use SQLite"), it means the `INSTRUCTIONS.md` or `.cursorrules` file is successfully enforcing your architecture.
* **MCP Server Light is Red**
    * Check the "Output" tab in Cursor and select "MCP Log" to see the Python traceback.
    * Verify your absolute path in the MCP settings is correct.