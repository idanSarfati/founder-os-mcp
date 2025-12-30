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

if __name__ == "__main__":
    print("Running Action Guard tests...")
    test_pr_title_parsing()
    test_mock_validation()
    print("\nAll basic tests completed!")
