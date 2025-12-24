# Troubleshooting: Linear Tools Not Showing in Cursor

## Quick Fix Steps

### 1. Reload Cursor Window (Most Common Fix)

**Option A: Command Palette**
1. Press `Ctrl+Shift+P` (Windows) or `Cmd+Shift+P` (Mac)
2. Type: `Developer: Reload Window`
3. Press Enter
4. Wait for Cursor to restart

**Option B: Full Restart**
1. Close Cursor completely
2. Reopen Cursor
3. Wait for MCP servers to initialize

### 2. Check MCP Server Status

1. Open Cursor Settings: `Ctrl+Shift+J` (Windows) or `Cmd+Shift+J` (Mac)
2. Navigate to **Features > MCP Servers**
3. Find `founder-os` in the list
4. Check the status indicator:
   - 🟢 **Green** = Server is running (tools should be available)
   - 🔴 **Red** = Server has errors (check logs)
   - ⚪ **Gray** = Server not connected

### 3. Check MCP Server Logs

If the server shows red/error:
1. In Cursor, open the **Output** panel
2. Select **"MCP"** from the dropdown
3. Look for error messages about Linear client initialization

Common errors you might see:
- `LINEAR_API_KEY missing` - Add the key to `.env`
- `Import Error` - Dependencies not installed
- `Connection Failed` - Linear API unreachable

### 4. Verify Server Can Start Manually

Run this command in your terminal to test:

```bash
python server.py
```

Expected output:
```
[OK] Auth Loaded. Notion Key present: True
[OK] Linear Client initialized.
```

If you see `[INFO] Linear integration disabled`, check your `.env` file.

### 5. Verify .env File Location

The `.env` file must be in the **project root** (same directory as `server.py`).

Check the path:
```bash
# Windows PowerShell
Test-Path .env
Get-Content .env | Select-String "LINEAR_API_KEY"
```

The `.env` file should contain:
```env
NOTION_API_KEY=ntn_...
LINEAR_API_KEY=lin_api_...
```

### 6. Verify Tools Are Registered

After reloading Cursor, the tools should appear when you:
1. Open Composer (`Cmd/Ctrl + I`)
2. Start typing a command that might use Linear
3. The AI should have access to:
   - `list_linear_tasks`
   - `get_linear_task_details`

**Note:** MCP tools don't always appear in the settings UI. They're available to the AI agent, not necessarily visible in a tool list.

### 7. Test Tool Availability

In Cursor Composer, try asking:
- "List my Linear tasks"
- "What Linear tasks do I have?"
- "Get details for Linear task IDA-8"

If the AI can use these tools, they're working correctly.

## Still Not Working?

### Check Server Initialization Code

The server only registers Linear tools if:
1. `LINEAR_API_KEY` exists in environment
2. `LinearClient` can be imported
3. `LinearClient()` initializes without errors

Check the startup logs for:
```
[OK] Linear Client initialized.
```

If you see `[INFO] Linear integration disabled`, the tools won't be registered.

### Manual Server Test

Test if the Linear client works standalone:

```bash
python -c "from src.integrations.linear_client import LinearClient; client = LinearClient(); print('Success:', client.get_active_tasks()[:100])"
```

This should output your Linear tasks (first 100 chars).

### Reinstall MCP Server

If all else fails:

1. Check `~/.cursor/mcp.json` (Windows: `C:\Users\<YourName>\.cursor\mcp.json`)
2. Verify the `founder-os` entry points to the correct `server.py` path
3. If needed, re-run `python install_script.py`

## Expected Behavior

**In Cursor Settings:**
- MCP Server status should show 🟢 (green)
- Server name: `founder-os`

**In Cursor Composer:**
- AI should be able to call Linear tools
- Tools won't appear in a visible list, but AI can use them

**When working correctly:**
- AI can answer questions about your Linear tasks
- AI can fetch task details
- AI will use `search_notion` when getting task details (semantic bridge)

