#!/usr/bin/env python3
"""
Mock test for the Dynamic Governance Engine (No API keys required).

This demonstrates the complete pipeline with mock data to show
how the system would work with real Notion/Linear content.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_with_mock_data():
    """Test the governance pipeline with mock data."""
    print("Testing Dynamic Governance Engine with Mock Data")
    print("=" * 55)

    # Mock governance data that would come from Notion/Linear + LLM
    mock_governance_data = {
        "ALLOWED_TECH_STACK": "Python 3.10+, pip, mcp, notion-client, httpx, python-dotenv, colorama",
        "FORBIDDEN_LIBRARIES": "Unknown/Detect from Codebase",
        "AUTH_PROVIDER": "Unknown/Detect from Codebase",
        "STRICTNESS_LEVEL": "HIGH",
        "active_tasks_context": "- ENG-10: Implement Dynamic Governance Engine (Semantic Adapter) (In Progress)\n- ENG-6: Gaining 5 Alpha Users (In Progress)",
        "generation_timestamp": datetime.now().isoformat()
    }

    print("Mock data extracted:")
    for key, value in mock_governance_data.items():
        print(f"  {key}: {value}")

    # Step 1: Test template rendering
    print("\n1. Testing template rendering...")
    from config.governance_template import get_governance_template

    template = get_governance_template()
    formatted_data = {
        "ALLOWED_TECH_STACK": mock_governance_data.get("ALLOWED_TECH_STACK", "Unknown/Detect from Codebase"),
        "FORBIDDEN_LIBRARIES": mock_governance_data.get("FORBIDDEN_LIBRARIES", "Unknown/Detect from Codebase"),
        "AUTH_PROVIDER": mock_governance_data.get("AUTH_PROVIDER", "Unknown/Detect from Codebase"),
        "SECURITY_LEVEL": mock_governance_data.get("STRICTNESS_LEVEL", "Unknown/Detect from Codebase"),
        "ACTIVE_TASKS_CONTEXT": mock_governance_data.get("active_tasks_context", "- No active tasks found"),
        "GENERATION_TIMESTAMP": mock_governance_data.get("generation_timestamp", "Unknown")
    }

    final_rules = template.format(**formatted_data)
    print("SUCCESS: Template rendering completed!")
    print(f"Generated rules length: {len(final_rules)} characters")

    # Step 2: Test file writing
    print("\n2. Testing file writing...")
    test_dir = project_root / "test_output"
    test_dir.mkdir(exist_ok=True)
    test_rules_path = test_dir / "founder-os-governance.mdc"

    with open(test_rules_path, "w", encoding="utf-8") as f:
        f.write(final_rules)

    print("SUCCESS: File writing completed!")
    print(f"Test rules written to: {test_rules_path}")

    # Step 3: Show sample output
    print("\n3. Sample of generated rules:")
    print("-" * 40)
    lines = final_rules.split('\n')

    # Show the key sections
    in_important_section = False
    for line in lines:
        if line.startswith('# 🚫 STRICTLY BOUND BY THESE RULES'):
            in_important_section = True
        elif line.startswith('## 🛠️ ALLOWED TECH STACK'):
            print(f"   {line}")
            # Show next few lines
            continue
        elif line.startswith('## 📋 ACTIVE TASKS CONTEXT'):
            in_important_section = False

        if in_important_section and line.strip():
            print(f"   {line}")

        # Stop after showing key sections
        if line.startswith('## 🛠️ AVAILABLE TOOLS'):
            break

    print(f"\n   ... ({len(lines)} total lines)")

    # Step 4: Verify the rules contain expected content
    print("\n4. Verification checks:")
    checks = [
        ("Contains tech stack rules", "Python 3.10+" in final_rules),
        ("Contains forbidden libs section", "FORBIDDEN_LIBRARIES" in final_rules),
        ("Contains auth provider section", "AUTH_PROVIDER" in final_rules),
        ("Contains security level", "STRICTNESS_LEVEL" in final_rules),
        ("Contains active tasks", "ENG-10" in final_rules),
        ("Contains generation timestamp", "generation_timestamp" in final_rules),
        ("Contains tool references", "search_notion" in final_rules),
    ]

    for check_name, passed in checks:
        status = "PASS" if passed else "FAIL"
        print(f"   {status}: {check_name}")

    all_passed = all(passed for _, passed in checks)
    print(f"\n{'ALL CHECKS PASSED!' if all_passed else 'SOME CHECKS FAILED!'}")

    return all_passed

def show_setup_instructions():
    """Show instructions for setting up real API keys."""
    print("\n" + "="*60)
    print("SETUP INSTRUCTIONS FOR LIVE TESTING")
    print("="*60)

    print("""
To test with real Notion and Linear data, set these environment variables:

1. Create a .env file in the project root with:
   NOTION_API_KEY=your_notion_api_key_here
   LINEAR_API_KEY=your_linear_api_key_here  (optional)
   OPENAI_API_KEY=your_openai_api_key_here

2. Get API keys:
   - Notion: https://developers.notion.com/
   - Linear: https://linear.app/settings/api
   - OpenAI: https://platform.openai.com/api-keys

3. Run the real test:
   python test_governance.py

4. Test MCP tools directly:
   python -c "from server import *; print('Server imports OK')"

5. Test bootstrap in a real project:
   # In Cursor, use the bootstrap_project tool
   bootstrap_project("/path/to/your/project")
""")

if __name__ == "__main__":
    success = test_with_mock_data()
    show_setup_instructions()
    sys.exit(0 if success else 1)
