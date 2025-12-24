# Linear Bridge POC - Testing Guide

## Quick Start Testing

### Step 1: Get Your Linear API Key

1. Go to [Linear Settings > API](https://linear.app/settings/api)
2. Click **"Create API Key"**
3. Give it a name (e.g., "Founder OS POC")
4. **Copy the API key** (you'll only see it once!)

### Step 2: Add API Key to `.env` File

In the project root directory, open or create `.env` file and add:

```env
LINEAR_API_KEY=your_linear_api_key_here
```

**Important:** 
- Replace `your_linear_api_key_here` with your actual key
- The key typically starts with `lin_api_` or similar
- Make sure there are no quotes around the key
- Don't commit this file to git (it should be in `.gitignore`)

### Step 3: Install Dependencies (if not already done)

```bash
pip install -r requirements.txt
```

This will install `requests` and `python-dotenv` if not already installed.

### Step 4: Run the POC

From the project root directory:

```bash
python experiments/linear_bridge.py
```

Or if you're in the `experiments` directory:

```bash
python linear_bridge.py
```

## Expected Output

### Success Case

If everything works, you should see:

```
🚀 Starting Linear Bridge POC...

🔍 [DEBUG] Raw JSON Response (Partial):
Found X issues.

🤖 [AI CONTEXT] Formatted Output:
📋 Active Tasks for [Your Name]:
========================================
📌 [PROJ-123] Task Title Here
   • Status: In Progress
   • Priority: High
   • Context: Task description here...
----------------------------------------
...
```

### Error Cases

**Missing API Key:**
```
❌ Error: LINEAR_API_KEY not found in .env. Please add it to run this POC.
```

**Invalid API Key / Authentication Error:**
```
❌ GraphQL Error: [{'message': 'Unauthorized', ...}]
```

**Network Error:**
```
❌ API Request Failed: [connection error details]
```

**No Active Issues:**
```
📋 Active Tasks for [Your Name]:
User [Your Name] has no active issues.
```

## Troubleshooting

### "LINEAR_API_KEY not found"
- Make sure `.env` file exists in the **project root** (same level as `server.py`)
- Check that the variable name is exactly `LINEAR_API_KEY` (case-sensitive)
- Ensure there are no spaces around the `=` sign

### "Unauthorized" or "Authentication Failed"
- Verify your API key is correct (copy it again from Linear Settings)
- Make sure you're using a **Personal API Key**, not an OAuth token
- Check that the key hasn't been revoked in Linear Settings

### "No issues found" (but you have issues in Linear)
- The script filters out issues with status "Done" or "Canceled"
- Make sure you have issues assigned to you with other statuses (In Progress, Todo, etc.)
- Check that the issues are in a team/project you have access to

### Network/Connection Errors
- Check your internet connection
- Verify you can access `https://api.linear.app/graphql` in a browser
- Check if you're behind a corporate firewall/proxy

## Testing Different Scenarios

### Test with No Issues
- Create a test issue in Linear, mark it as "Done"
- Run the script - it should show "no active issues"

### Test with Multiple Issues
- Create several issues with different priorities and statuses (except Done/Canceled)
- Verify all active issues are returned

### Test Edge Cases
- Issue with no description (should show "No description provided.")
- Issue with very long description (should be truncated to 200 chars)
- Empty/null response from API (should handle gracefully)

## Next Steps

Once the POC is working:
1. Review the formatted output format for LLM consumption
2. Consider integrating this as an MCP tool in `server.py`
3. Add additional filtering options (by team, project, priority, etc.)
4. Add pagination support for large result sets

