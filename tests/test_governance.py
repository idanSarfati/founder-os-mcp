#!/usr/bin/env python3
"""
Test script for the Dynamic Governance Engine.

This script tests the complete pipeline:
1. Governance data extraction from Notion and Linear
2. LLM processing of the data
3. Template injection
4. Final rules file generation
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

# Load .env file before checking environment variables
env_path = find_dotenv()
if env_path:
    load_dotenv(dotenv_path=env_path)

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_governance_pipeline():
    """Test the complete governance pipeline."""
    print("Testing Dynamic Governance Engine Pipeline")
    print("=" * 50)

    try:
        # Step 1: Test environment setup
        print("1. Checking environment setup...")
        notion_key = os.getenv("NOTION_API_KEY")
        linear_key = os.getenv("LINEAR_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")

        print(f"   NOTION_API_KEY: {'SET' if notion_key else 'NOT SET'}")
        print(f"   LINEAR_API_KEY: {'SET' if linear_key else 'NOT SET'}")
        print(f"   OPENAI_API_KEY: {'SET' if openai_key else 'NOT SET'}")

        if not notion_key:
            print("CRITICAL: NOTION_API_KEY required for testing")
            return False

        if not openai_key:
            print("WARNING: OPENAI_API_KEY not set - will use safe defaults")

        # Step 2: Test governance extraction
        print("\n2. Testing governance data extraction...")
        from src.tools.governance_extraction import extract_governance_data

        print("   Extracting data from Notion and Linear...")
        governance_data = extract_governance_data()

        print("   SUCCESS: Extraction completed!")
        print(f"   Extracted fields: {list(governance_data.keys())}")

        # Step 3: Test template rendering
        print("\n3. Testing template rendering...")
        from config.governance_template import get_governance_template

        template = get_governance_template()
        formatted_data = {
            "ALLOWED_TECH_STACK": governance_data.get("ALLOWED_TECH_STACK", "Unknown/Detect from Codebase"),
            "FORBIDDEN_LIBRARIES": governance_data.get("FORBIDDEN_LIBRARIES", "Unknown/Detect from Codebase"),
            "AUTH_PROVIDER": governance_data.get("AUTH_PROVIDER", "Unknown/Detect from Codebase"),
            "SECURITY_LEVEL": governance_data.get("STRICTNESS_LEVEL", "Unknown/Detect from Codebase"),
            "ACTIVE_TASKS_CONTEXT": governance_data.get("active_tasks_context", "- No active tasks found"),
            "GENERATION_TIMESTAMP": governance_data.get("generation_timestamp", "Unknown")
        }

        final_rules = template.format(**formatted_data)
        print("   SUCCESS: Template rendering completed!")
        print(f"   Generated rules length: {len(final_rules)} characters")

        # Step 4: Test file writing
        print("\n4. Testing file writing...")
        test_dir = project_root / "test_output"
        test_dir.mkdir(exist_ok=True)
        test_rules_path = test_dir / "founder-os-governance.mdc"

        with open(test_rules_path, "w", encoding="utf-8") as f:
            f.write(final_rules)

        print("   SUCCESS: File writing completed!")
        print(f"   Test rules written to: {test_rules_path}")

        # Step 5: Show sample output
        print("\n5. Sample of generated rules:")
        print("-" * 30)
        lines = final_rules.split('\n')
        for i, line in enumerate(lines[:20]):  # Show first 20 lines
            print(f"   {line}")
        if len(lines) > 20:
            print(f"   ... ({len(lines) - 20} more lines)")

        # Step 6: Test bootstrap_project function
        print("\n6. Testing bootstrap_project function...")
        from src.tools.project_ops import bootstrap_project

        # Create a test directory
        test_project_dir = project_root / "test_project"
        test_project_dir.mkdir(exist_ok=True)

        result = bootstrap_project(str(test_project_dir))
        print("   SUCCESS: bootstrap_project executed!")
        print(f"   Result: {result}")

        print("\nALL TESTS PASSED!")
        print("Check these files:")
        print(f"   - Test rules: {test_rules_path}")
        print(f"   - Bootstrap rules: {test_project_dir}/.cursor/rules/founder-os-governance.mdc")

        return True

    except Exception as e:
        print(f"\nTEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_governance_pipeline()
    sys.exit(0 if success else 1)
