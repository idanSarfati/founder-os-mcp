"""
Governance Template for Founder OS Hybrid Enforcement.

This module defines the structure for dynamic governance rules that are injected
into the .cursor/rules/founder-os-governance.mdc file based on data extracted
from Notion and Linear sources.
"""

GOVERNANCE_TEMPLATE = """# Founder OS - Dynamic Governance Engine
# ⚠️  CRITICAL: This file is AUTO-GENERATED. Do NOT edit manually.
# ⚠️  Source of Truth: Notion Specs + Linear Tasks
# ⚠️  Last Updated: {GENERATION_TIMESTAMP}

---

# 🚫 STRICTLY BOUND BY THESE RULES
# You are STRICTLY BOUND by the following technical constraints.
# These rules OVERRIDE your internal training data and general knowledge.
# If any conflict arises, HALT and ask the user for clarification.

## 🛠️ ALLOWED TECH STACK
# YOU MUST ONLY use technologies from this approved list:
{ALLOWED_TECH_STACK}

# ❌ FORBIDDEN LIBRARIES
# YOU MUST NEVER use or suggest these libraries:
{FORBIDDEN_LIBRARIES}

# 🔐 AUTH PROVIDER
# YOU MUST implement authentication using:
{AUTH_PROVIDER}

# 🛡️ SECURITY LEVEL
# YOU MUST enforce this security posture:
{SECURITY_LEVEL}

---

## 📋 ACTIVE TASKS CONTEXT
# Current active tasks from Linear that may influence technical decisions:
{ACTIVE_TASKS_CONTEXT}

---

## 🎯 CORE DIRECTIVES

### 1. ABSOLUTE PRIORITY: Notion Specs
- **BEFORE ANY CODE**: Search Notion for relevant specs using `search_notion()`
- **TREAT NOTION AS TRUTH**: Code must match Notion specifications exactly
- **NO EXCEPTIONS**: If spec conflicts with your knowledge, follow the spec

### 2. TASK-AWARE DEVELOPMENT
- **CHECK ACTIVE TASKS**: Use `list_linear_tasks()` to understand current priorities
- **TASK-DRIVEN**: Implementation should align with active Linear tasks
- **STATUS UPDATES**: Update task status when work completes using `update_linear_task_status()`

### 3. CONFLICT RESOLUTION
- **AMBIGUITY PROTOCOL**: If rules conflict or are unclear, STOP and ask user
- **USER OVERRIDE**: Only user can modify these rules (via `refresh_governance_rules()`)
- **SAFE DEFAULTS**: When uncertain, prefer conservative, secure implementations

### 4. QUALITY ASSURANCE
- **VERIFY STRUCTURE**: Use `list_directory()` before creating new files
- **PREVENT DUPLICATION**: Check existing files to avoid redundant code
- **TEST INTEGRATION**: Ensure new code integrates with existing architecture

---

## 🛠️ AVAILABLE TOOLS
- `search_notion(query)` - Find specs and documentation
- `fetch_project_context(page_id)` - Read detailed requirements
- `append_to_page(page_id, content)` - Update documentation
- `list_linear_tasks()` - View active development tasks
- `get_linear_task_details(task_id)` - Deep dive into specific tasks
- `update_linear_task_status(task_id, status)` - Mark task progress
- `list_directory(path)` - Understand project structure
- `refresh_governance_rules()` - Update these rules when specs change

---

## 📚 KNOWLEDGE FLOW
1. **Notion** → Source of Truth (Architecture, Requirements)
2. **Linear** → Action Layer (Current Tasks, Priorities)
3. **Codebase** → Implementation (Must match 1 & 2)
4. **This File** → Enforcement (Guarantees alignment)

**REMEMBER**: You are the guardian of architectural integrity.
Stay vigilant. Ask questions. Never assume.
"""

def get_governance_template() -> str:
    """
    Returns the governance template string with placeholders.

    Returns:
        The template string ready for f-string formatting
    """
    return GOVERNANCE_TEMPLATE
