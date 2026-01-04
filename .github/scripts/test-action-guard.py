#!/usr/bin/env python3
"""
Simple test for Action Guard parsing functionality
"""

import re
import os
import sys

# Add the scripts directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

def test_pr_title_parsing():
    """Test Linear issue ID extraction from PR titles"""
    test_cases = [
        ("feat: implement login [ENG-5]", "ENG-5"),
        ("fix: button color [FOS-101]", "FOS-101"),
        ("chore: update deps", None),
        ("[BUG-123] fix critical issue", "BUG-123"),
    ]

    for title, expected in test_cases:
        match = re.search(r'\[([A-Z]+-\d+)\]', title)
        result = match.group(1) if match else None
        status = "PASS" if result == expected else "FAIL"
        print(f"{status}: '{title}' -> {result} (expected: {expected})")

def test_mock_validation():
    """Test basic validation logic"""
    print("\nTesting basic validation...")

    # Mock spec and diff
    spec = "The login button must be purple."
    diff = """
    diff --git a/styles.css b/styles.css
    index 123456..789012 100644
    --- a/styles.css
    +++ b/styles.css
    @@ -1,3 +1,3 @@
     .login-button {
    -  color: blue;
    +  color: purple;
     }
    """

    print("Spec:", spec[:50] + "...")
    print("Diff preview:", diff[:100] + "...")
    print("Mock validation test completed")

def test_governance_enforcement():
    """Test governance enforcement logic"""
    print("\nTesting governance enforcement...")

    # Mock governance rules
    governance_rules = {
        "ALLOWED_TECH_STACK": "Vue.js 3, Python 3.10+, FastAPI",
        "FORBIDDEN_LIBRARIES": "React, jQuery, Bootstrap, Axios",
        "AUTH_PROVIDER": "Supabase Auth",
        "STRICTNESS_LEVEL": "MAXIMUM"
    }

    # Test diff with forbidden libraries
    test_diff = """
    diff --git a/package.json b/package.json
    index 123456..789012 100644
    --- a/package.json
    +++ b/package.json
    @@ -1,5 +1,6 @@
     {
       "dependencies": {
    +    "jquery": "^3.6.0",
         "vue": "^3.0.0"
       }
     }
    """

    print("Testing forbidden library detection...")
    violations = []

    forbidden_libs = governance_rules.get('FORBIDDEN_LIBRARIES', '')
    if forbidden_libs:
        forbidden_list = [lib.strip().lower() for lib in forbidden_libs.split(',') if lib.strip()]

        for lib in forbidden_list:
            # Check for actual package references in package.json or import statements
            if lib in test_diff.lower():
                # More precise patterns for dependency detection
                dep_patterns = [
                    f'"{lib}":',  # "jquery": "version"
                    f"'{lib}':",  # 'jquery': 'version'
                    f'{lib}@',    # jquery@version
                    f'{lib}:'     # jquery: version
                ]

                for pattern in dep_patterns:
                    if pattern in test_diff.lower():
                        violations.append(f"Forbidden library used: {lib}")
                        break

    if violations:
        print("VIOLATIONS detected:")
        for v in violations:
            print(f"   {v}")
    else:
        print("No violations detected")

    print("Governance enforcement test completed")

if __name__ == "__main__":
    print("Running Action Guard tests...")
    test_pr_title_parsing()
    test_mock_validation()
    test_governance_enforcement()
    print("\nAll tests completed!")
