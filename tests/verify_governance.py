#!/usr/bin/env python3
"""
Quick verification that the Dynamic Governance Engine is working.
"""

import os
from pathlib import Path

def main():
    print("Dynamic Governance Engine Verification")
    print("=" * 40)

    # Check if test file was created
    test_file = Path("test_output/founder-os-governance.mdc")
    if test_file.exists():
        print("✓ Test governance rules file created successfully")

        # Read and check key sections
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()

        checks = [
            ("Contains tech stack rules", "Python 3.10+" in content),
            ("Contains active tasks", "ENG-10" in content),
            ("Contains security level", "HIGH" in content),
            ("Contains tool references", "search_notion" in content),
            ("Contains timestamp", "2026-01-04" in content),
        ]

        print("\nContent verification:")
        for check_name, passed in checks:
            status = "✓" if passed else "✗"
            print(f"  {status} {check_name}")

        print(f"\nFile size: {len(content)} characters")
        print(f"Location: {test_file.absolute()}")

    else:
        print("✗ Test file not found")

    # Check if all modules can be imported
    print("\nModule imports:")
    try:
        import config.governance_template
        print("✓ config.governance_template")
    except ImportError as e:
        print(f"✗ config.governance_template: {e}")

    try:
        import src.tools.governance_extraction
        print("✓ src.tools.governance_extraction")
    except ImportError as e:
        print(f"✗ src.tools.governance_extraction: {e}")

    try:
        import src.utils.llm_client
        print("✓ src.utils.llm_client")
    except ImportError as e:
        print(f"✗ src.utils.llm_client: {e}")

    try:
        import src.tools.project_ops
        print("✓ src.tools.project_ops")
    except ImportError as e:
        print(f"✗ src.tools.project_ops: {e}")

    print("\nNext Steps:")
    print("1. Set environment variables: NOTION_API_KEY, LINEAR_API_KEY (optional), OPENAI_API_KEY")
    print("2. Run: python test_governance.py")
    print("3. Test in Cursor: Use bootstrap_project tool")
    print("4. Test refresh: Use refresh_governance_rules tool")

if __name__ == "__main__":
    main()
