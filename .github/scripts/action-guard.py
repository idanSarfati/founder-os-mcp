#!/usr/bin/env python3
"""
GitHub Action Guard - Dual Validation System

Phase A: Spec Validation - Validates PR changes against the specific Notion spec linked to the Linear issue
Phase B: Governance Enforcement - Validates PR changes against global governance rules (forbidden libraries, etc.)

This script runs both validations to ensure code compliance at multiple levels.
"""

import os
import sys
import re
import json
import requests
import subprocess
import time
from typing import Optional, Dict, Any, List

try:
    import google.genai as genai
    USE_NEW_PACKAGE = True
except ImportError:
    try:
        import google.generativeai as genai
        USE_NEW_PACKAGE = False
    except ImportError:
        print("ERROR: Neither google.genai nor google.generativeai packages are available")
        sys.exit(1)


class ActionGuard:
    def __init__(self):
        self.pr_title = os.getenv('PR_TITLE', '')
        self.pr_number = os.getenv('PR_NUMBER', '')
        self.github_token = os.getenv('GITHUB_TOKEN', '')
        self.notion_token = os.getenv('NOTION_TOKEN', '')
        self.linear_api_key = os.getenv('LINEAR_API_KEY', '')

        # Allow testing without API keys for local development
        test_mode = os.getenv('TEST_MODE', '').lower() == 'true'

        if not test_mode and not all([self.notion_token, self.linear_api_key, self.github_token]):
            print("ERROR: Missing required environment variables")
            print("Required: NOTION_TOKEN, LINEAR_API_KEY, GITHUB_TOKEN")
            print("Optional: GEMINI_API_KEY (for AI validation)")
            print("For testing, set TEST_MODE=true to skip API requirements")
            sys.exit(1)

        if test_mode:
            print("TEST MODE: Running without API requirements")

        # Configure Gemini
        api_key = os.getenv('GEMINI_API_KEY', '')
        if not api_key:
            print("WARNING: GEMINI_API_KEY environment variable not set")
            print("   LLM validation will be skipped for this run")
            self.client = None
            self.model = None
            return

        try:
            if USE_NEW_PACKAGE:
                self.client = genai.Client(api_key=api_key)
            else:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-pro')
        except Exception as e:
            print(f"ERROR: Failed to initialize Google AI client: {e}")
            print("   Please check your GEMINI_API_KEY and package installation")
            sys.exit(1)

    def get_pr_title(self) -> str:
        """Get PR title from GitHub API"""
        try:
            # Get PR info from environment (set by GitHub Actions)
            repo = os.getenv('GITHUB_REPOSITORY')
            pr_number = os.getenv('PR_NUMBER')

            if not repo or not pr_number:
                print("ERROR: Could not determine PR details from environment")
                sys.exit(1)

            url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
            headers = {'Authorization': f'token {self.github_token}'}

            response = requests.get(url, headers=headers)
            response.raise_for_status()

            return response.json()['title']
        except Exception as e:
            print(f"ERROR: Failed to get PR title: {e}")
            sys.exit(1)

    def should_skip_validation(self, pr_title: str) -> bool:
        """Check if PR should skip Linear validation (for infra/setup changes)"""
        import re

        # Check for explicit [SKIP] tag
        if '[SKIP]' in pr_title.upper():
            return True

        # Check for explicit [FORCE] tag (overrides skip)
        if '[FORCE]' in pr_title.upper():
            return False

        # Check for infrastructure keywords (whole word match only)
        skip_keywords = [
            'infra', 'ci', 'workflow', 'github action', 'permissions',
            'dependencies', 'setup', 'config', 'build', 'lint', 'docker',
            'readme', 'documentation', 'chore', 'refactor', 'test', 'fix',
            'feat', 'style', 'perf', 'revert'
        ]

        title_lower = pr_title.lower()
        # Use word boundaries to avoid substring matches like "ci" in "specification"
        return any(re.search(r'\b' + re.escape(keyword) + r'\b', title_lower) for keyword in skip_keywords)

    def extract_linear_issue_id(self, pr_title: str) -> Optional[str]:
        """Extract Linear issue ID from PR title (e.g., [FOS-101])"""
        match = re.search(r'\[([A-Z]+-\d+)\]', pr_title)
        if match:
            return match.group(1)
        else:
            print("ERROR: Could not extract Linear issue ID from PR title")
            print(f"   PR Title: {pr_title}")
            print("   Expected format: [ISSUE-ID] in title (e.g., [ENG-5], [FOS-101])")
            print("   Or use infrastructure keywords to skip validation")
            return None

    def query_linear_issue(self, issue_id: str) -> Optional[Dict[str, Any]]:
        """Query Linear API for issue details"""
        try:
            query = """
            query GetIssue($issueId: String!) {
                issue(id: $issueId) {
                    id
                    title
                    description
                    state {
                        name
                    }
                    labels {
                        nodes {
                            name
                        }
                    }
                    assignee {
                        name
                    }
                }
            }
            """

            url = "https://api.linear.app/graphql"
            headers = {
                'Authorization': self.linear_api_key,
                'Content-Type': 'application/json',
                'x-apollo-operation-name': 'GetIssue'
            }

            # Debug: Print request details
            print(f"INFO: Making Linear API request for issue: {issue_id}")
            print(f"DEBUG: Headers: Content-Type={headers.get('Content-Type')}, Auth starts with: {headers.get('Authorization', '')[:10]}...")

            response = requests.post(url, json={'query': query, 'variables': {'issueId': issue_id}}, headers=headers)

            # Debug: Print full response details
            print(f"DEBUG: Response Status: {response.status_code}")
            print(f"DEBUG: Response Headers: {dict(response.headers)}")

            if response.status_code != 200:
                print(f"ERROR: Full Response Body: {response.text}")
                print("ERROR: Linear API request failed - check authentication and request format")
                return None

            data = response.json()
            if data.get('data', {}).get('issue'):
                issue = data['data']['issue']
                print(f"SUCCESS: Found Linear issue: {issue.get('title', 'Unknown')}")
                return issue
            else:
                print(f"ERROR: Linear issue {issue_id} not found in response")
                print(f"Response data: {data}")
                return None

        except Exception as e:
            print(f"ERROR: Failed to query Linear API: {e}")
            return None

    def extract_notion_page_id(self, description):
        """
        Extracts Notion page ID from text.
        Supports formats:
        - https://notion.so/page-name-32charID
        - https://notion.so/32charID
        """
        if not description:
            return None

        print(f"INFO: Searching for Notion link in description: '{description}'")

        # Search for sequence of 32 hex characters (a-f, 0-9)
        # that comes after notion.so/ and optionally after text and dash
        # Example: notion.so/some-title-1234567890abcdef1234567890abcdef

        # Search all occurrences of notion.so and find the ID at the end of the path
        # This regex captures the last 32 characters before question mark (query params) or end of line
        match = re.search(r"notion\.so/(?:[^/]+/)*?([a-zA-Z0-9-]*?)([a-fA-F0-9]{32})(?:\?|$|\s|/)", description)

        if match:
            # group(2) is the ID itself (32 characters)
            page_id = match.group(2)
            print(f"SUCCESS: Found Notion page ID: {page_id}")
            return page_id

        print("ERROR: No Notion page ID found in description")
        print("💡 Expected format: https://www.notion.so/page-name-PAGE_ID")

        # Debug: Let's see what the pattern finds
        print("🔧 Debug: Checking all notion.so occurrences...")
        all_matches = re.findall(r'notion\.so/[^?\s]+', description)
        if all_matches:
            print(f"🔧 Found URLs: {all_matches}")
        else:
            print("🔧 No notion.so URLs found at all")

        return None

    def fetch_notion_page(self, page_id: str) -> Optional[str]:
        """Fetch Notion page content"""
        try:
            url = f"https://api.notion.com/v1/pages/{page_id}"
            headers = {
                'Authorization': f'Bearer {self.notion_token}',
                'Notion-Version': '2022-06-28'
            }

            response = requests.get(url, headers=headers)
            response.raise_for_status()

            page_data = response.json()

            # Get page content (this is a simplified version - real implementation would need to handle blocks)
            content_url = f"https://api.notion.com/v1/blocks/{page_id}/children"
            content_response = requests.get(content_url, headers=headers)
            content_response.raise_for_status()

            blocks = content_response.json()['results']

            # Extract text content from blocks
            content = ""
            for block in blocks:
                if block['type'] == 'paragraph':
                    for text_item in block['paragraph']['rich_text']:
                        content += text_item['plain_text'] + " "

            return content.strip()

        except Exception as e:
            print(f"ERROR: Failed to fetch Notion page: {e}")
            return None

    def get_git_diff(self):
        """
        Retrieves git diff for PR validation.
        Handles both local testing and GitHub Actions environments.
        """
        print("INFO: Getting git diff...")

        try:
            # Check if we're in GitHub Actions (has GITHUB_ACTIONS env var)
            is_github_actions = os.getenv('GITHUB_ACTIONS') == 'true'

            if is_github_actions:
                # GitHub Actions PR environment: use merge commit logic
                print("Running in GitHub Actions - using merge commit diff...")
                cmd = ["git", "diff", "HEAD^1", "HEAD"]
            else:
                # Local testing: fetch and compare against origin/main
                print("Running locally - fetching origin/main...")
                subprocess.run(["git", "fetch", "origin", "main"], check=False, capture_output=True)
                cmd = ["git", "diff", "origin/main", "HEAD"]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                diff_content = result.stdout.strip()
                if diff_content:
                    print(f"SUCCESS: Found diff ({len(diff_content)} chars)")
                    return diff_content
                else:
                    print("INFO: No diff found (no changes)")
                    return ""
            else:
                print(f"WARNING: Git diff command failed: {result.stderr}")
                return ""

        except Exception as e:
            print(f"ERROR: Error getting git diff: {e}")
            return None

    def validate_with_llm(self, spec_content: str, git_diff: str) -> bool:
        """
        Validates code changes against specification using Gemini API.
        Includes Retry logic for Rate Limits (429).
        """
        print("INFO: Analyzing code changes...")

        # Skip LLM validation if no API key was provided
        if self.client is None and self.model is None:
            print("WARNING:  Skipping LLM validation (no API key configured)")
            return True

        # שימוש ב-Alias שראינו בלוגים שקיים בוודאות
        # מודל זה הוא יציב וחסכוני יותר במכסות מגרסה 2.0
        model_name = "gemini-flash-latest"

        prompt = f"""
        You are a Senior Tech Lead validating a PR.

        Specification from Notion:
        {spec_content}

        Code Changes (Git Diff):
        {git_diff}

        Task:
        1. Check if the code implements the requirements in the specification.
        2. Look for logical bugs or security issues.
        3. Verify that the implementation matches the design.

        Output only JSON in this format:
        {{
            "approved": boolean,
            "comments": "explanation of decision",
            "critical_issues": ["list", "of", "blockers"]
        }}
        """

        max_retries = 3
        for attempt in range(max_retries):
            try:
                if USE_NEW_PACKAGE:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )
                    result = response.text.strip()
                else:
                    # For old package, switch to stable model
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(prompt)
                    result = response.text.strip()

                # Parse JSON response
                # Remove markdown code blocks if present
                result = result.replace('```json', '').replace('```', '').strip()
                try:
                    parsed = json.loads(result)
                except json.JSONDecodeError:
                    # Fallback to simple text analysis if JSON parsing fails
                    parsed = {"approved": "NO" not in result.upper(), "comments": result[:200], "critical_issues": []}

                # Write result to file for workflow to read
                with open('validation_result.txt', 'w') as f:
                    f.write(json.dumps(parsed, indent=2))

                if parsed.get("approved", False):
                    print("SUCCESS: AI Validation Passed")
                    print(f"   Comments: {parsed.get('comments', '')}")
                    return True
                else:
                    print("ERROR: AI Validation Failed:")
                    print(f"   Reason: {parsed.get('comments', '')}")
                    print(f"   Issues: {parsed.get('critical_issues', [])}")
                    return False

            except Exception as e:
                error_str = str(e)
                print(f"WARNING:  Attempt {attempt + 1}/{max_retries} failed: {error_str[:200]}...")

                # אם זה Rate Limit (429), נחכה וננסה שוב
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    wait_time = 60  # נחכה דקה שלמה, זה CI, יש לו סבלנות
                    print(f"⏳ Hit rate limit. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    # אם זו שגיאה אחרת, נחכה קצת ונסה שוב
                    time.sleep(2)

        print("ERROR: LLM validation failed after all retries.")
        # Write failure result
        with open('validation_result.txt', 'w') as f:
            f.write(json.dumps({"approved": False, "comments": "AI validation failed after retries", "critical_issues": ["Validation system error"]}, indent=2))
        return False  # חשוב מאוד! מחזירים False כדי לחסום את ה-PR במקרה של כישלון

    def run(self):
        """Main execution flow - now supports dual validation"""
        print("INFO: Starting Action Guard validation...")

        # Check if we should run dual validation (Phase A + Phase B)
        # Default to dual validation, but allow override via environment
        validation_mode = os.getenv('VALIDATION_MODE', 'dual').lower()

        if validation_mode == 'spec_only':
            # Original spec-only validation
            self.run_spec_validation()
        elif validation_mode == 'governance_only':
            # Governance-only validation
            self.run_governance_validation()
        else:
            # Default: Dual validation (Phase A + Phase B)
            self.run_dual_validation()

    def run_spec_validation(self):
        """Run only Phase A: Spec validation (original functionality)"""
        print("PHASE: Running Phase A only: Spec Validation")

        # Get PR title if not set in environment
        if not self.pr_title:
            self.pr_title = self.get_pr_title()

        # Check if this PR should skip Linear validation
        if self.should_skip_validation(self.pr_title):
            print(f"WARNING:  Skipping Linear validation for infrastructure change")
            print(f"   PR Title: {self.pr_title}")
            print("SUCCESS: Allowing PR to proceed without specification validation")
            return

        # Step 1: Extract Linear Issue ID from PR title
        issue_id = self.extract_linear_issue_id(self.pr_title)
        if not issue_id:
            print("ERROR: Could not extract Linear issue ID from PR title")
            print(f"   PR Title: {self.pr_title}")
            print("   Expected format: [ISSUE-ID] in title (e.g., [ENG-5], [FOS-101])")
            print("   Or add infrastructure keywords to skip validation")
            sys.exit(1)

        print(f"📋 Found Linear issue: {issue_id}")

        # Step 2: Query Linear for issue details
        issue = self.query_linear_issue(issue_id)
        if not issue:
            sys.exit(1)

        print(f"📝 Issue Title: {issue['title']}")

        # Step 3: Extract Notion page ID from issue description
        notion_page_id = self.extract_notion_page_id(issue.get('description', ''))
        if not notion_page_id:
            print("ERROR: Could not find Notion page link in Linear issue description")
            sys.exit(1)

        print(f"📄 Notion Page ID: {notion_page_id}")

        # Step 4: Fetch Notion page content
        spec_content = self.fetch_notion_page(notion_page_id)
        if not spec_content:
            sys.exit(1)

        print("📖 Successfully fetched Notion specification")

        # Step 5: Get git diff
        git_diff = self.get_git_diff()
        if not git_diff:
            print("WARNING:  No git diff found, assuming compliance")
            return

        print("INFO: Analyzing code changes...")

        # Step 6: Validate with LLM
        is_compliant = self.validate_with_llm(spec_content, git_diff)

        if not is_compliant:
            print("BLOCKED: PR blocked due to spec violation")
            sys.exit(1)
        else:
            print("SUCCESS: PR approved - changes comply with specification")

    def run_governance_validation(self):
        """Run only Phase B: Governance enforcement"""
        print("GOVERNANCE: Running Phase B only: Governance Enforcement")

        governance_rules = self.extract_governance_rules()
        if not governance_rules:
            print("ERROR: Cannot proceed without governance rules")
            sys.exit(1)

        git_diff = self.get_git_diff()
        if not git_diff:
            print("WARNING:  No git diff found, assuming compliance")
            return

        is_compliant = self.validate_governance_compliance(git_diff, governance_rules)

        if not is_compliant:
            print("BLOCKED: PR blocked due to governance violation")
            sys.exit(1)
        else:
            print("SUCCESS: PR approved - governance compliance verified")

    def extract_governance_rules(self) -> Optional[Dict[str, Any]]:
        """
        Extract governance rules from existing .mdc file or Notion/Linear APIs

        Priority:
        1. Read from existing .cursor/rules/founder-os-governance.mdc file (fastest)
        2. Extract from Notion and Linear using governance_extraction.py (fallback)

        Returns:
            Dictionary with governance constraints or None if extraction fails
        """
        print("GOVERNANCE: Extracting governance rules...")

        # First, try to read from existing governance rules file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.join(script_dir, '..', '..')
        rules_file = os.path.join(project_root, '.cursor', 'rules', 'founder-os-governance.mdc')

        if os.path.exists(rules_file):
            try:
                print(f"Reading existing governance rules from .mdc file: {rules_file}")
                with open(rules_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                print(f"DEBUG: .mdc file content length: {len(content)} chars")
                print(f"DEBUG: .mdc file content preview: {content[:200]}...")

                # Parse the .mdc file to extract governance rules
                governance_data = self._parse_governance_mdc(content)

                if governance_data:
                    print("SUCCESS: Successfully read governance rules from .mdc file:")
                    print(f"   Allowed tech: {governance_data.get('ALLOWED_TECH_STACK', 'None')[:50]}...")
                    print(f"   Forbidden libs: {governance_data.get('FORBIDDEN_LIBRARIES', 'None')[:50]}...")
                    return governance_data
                else:
                    print("Could not parse governance rules from .mdc file, falling back to API extraction")

            except Exception as e:
                print(f"Failed to read .mdc file: {e}, falling back to API extraction")

        # Fallback: Extract from Notion and Linear APIs
        try:
            print("Falling back to API extraction from Notion and Linear...")

            # Set up Python path to find the src module
            src_path = os.path.join(project_root, 'src')

            # Add both project root and src directory to path
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            if src_path not in sys.path:
                sys.path.insert(0, src_path)

            from tools.governance_extraction import extract_governance_data

            # Set required environment variables for the extraction
            os.environ['NOTION_API_KEY'] = self.notion_token
            os.environ['LINEAR_API_KEY'] = self.linear_api_key

            governance_data = extract_governance_data()

            print("SUCCESS: Successfully extracted governance rules from APIs:")
            print(f"   Allowed tech: {governance_data.get('ALLOWED_TECH_STACK', 'None')[:50]}...")
            print(f"   Forbidden libs: {governance_data.get('FORBIDDEN_LIBRARIES', 'None')[:50]}...")

            return governance_data

        except Exception as e:
            print(f"ERROR: Failed to extract governance rules from APIs: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _parse_governance_mdc(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Parse governance rules from the .mdc file content

        Args:
            content: The content of the founder-os-governance.mdc file

        Returns:
            Dictionary with parsed governance rules
        """
        try:
            governance_data = {}

            # Extract allowed tech stack
            if "ALLOWED TECH STACK" in content:
                lines = content.split('\n')
                in_section = False
                for line in lines:
                    if "ALLOWED TECH STACK" in line:
                        in_section = True
                        continue
                    elif in_section and (line.startswith("## ") or line.startswith("# ❌")):
                        break  # Next section started
                    elif in_section and line.strip() and not line.startswith("#"):
                        # Extract the tech stack line
                        tech_line = line.strip()
                        if tech_line and tech_line != "Unknown/Detect from Codebase (Ask user for clarification)":
                            governance_data['ALLOWED_TECH_STACK'] = tech_line
                            break

            # Extract forbidden libraries
            if "FORBIDDEN LIBRARIES" in content:
                lines = content.split('\n')
                in_section = False
                for line in lines:
                    if "FORBIDDEN LIBRARIES" in line:
                        in_section = True
                        continue
                    elif in_section and (line.startswith("## ") or line.startswith("# 🔐")):
                        break  # Next section started
                    elif in_section and line.strip() and not line.startswith("#"):
                        # Extract the forbidden libs line
                        libs_line = line.strip()
                        if libs_line and libs_line != "Unknown/Detect from Codebase (Ask user for clarification)":
                            governance_data['FORBIDDEN_LIBRARIES'] = libs_line
                            break

            # Extract security level
            if "SECURITY LEVEL" in content:
                lines = content.split('\n')
                in_section = False
                for line in lines:
                    if "SECURITY LEVEL" in line:
                        in_section = True
                        continue
                    elif in_section and line.startswith("## "):
                        break  # Next section started
                    elif in_section and line.strip() and not line.startswith("#"):
                        # Extract the security level line
                        security_line = line.strip()
                        if security_line:
                            governance_data['STRICTNESS_LEVEL'] = security_line
                            break

            # Set defaults if not found
            if 'ALLOWED_TECH_STACK' not in governance_data:
                governance_data['ALLOWED_TECH_STACK'] = "Unknown/Detect from Codebase"
            if 'FORBIDDEN_LIBRARIES' not in governance_data:
                governance_data['FORBIDDEN_LIBRARIES'] = "Unknown/Detect from Codebase"
            if 'STRICTNESS_LEVEL' not in governance_data:
                governance_data['STRICTNESS_LEVEL'] = "MEDIUM"

            return governance_data

        except Exception as e:
            print(f"Failed to parse .mdc content: {e}")
            return None

    def validate_governance_compliance(self, git_diff: str, governance_rules: Dict[str, Any]) -> bool:
        """
        Validate that git diff doesn't violate governance rules

        Args:
            git_diff: The git diff content
            governance_rules: Governance constraints from Notion/Linear

        Returns:
            True if compliant, False if violations found
        """
        print("INFO: Validating governance compliance...")
        print(f"DEBUG: Governance rules received: {governance_rules}")
        print(f"DEBUG: Git diff preview (first 500 chars): {git_diff[:500]}...")

        violations = []

        # Check for forbidden libraries
        forbidden_libs = governance_rules.get('FORBIDDEN_LIBRARIES', '')
        print(f"DEBUG: Forbidden libs string: '{forbidden_libs}'")
        if forbidden_libs and forbidden_libs != 'Unknown/Detect from Codebase':
            forbidden_list = [lib.strip().lower() for lib in forbidden_libs.replace(',', ';').split(';') if lib.strip()]
            print(f"DEBUG: Forbidden list: {forbidden_list}")

            for lib in forbidden_list:
                if lib in git_diff.lower():
                    # Check for dependency additions in package files
                    dependency_patterns = [
                        f'^{lib}$',  # Just the library name (like in requirements.txt)
                        f'^{lib}@',  # library@version
                        f'^{lib}:',  # library: version
                        f'"{lib}"',  # "library"
                        f"'{lib}'",  # 'library'
                        f'\\+{lib}$',  # +library (git diff format)
                        f'\\+{lib}@',  # +library@version
                        f'\\+{lib}:',  # +library: version
                    ]

                    # Check for import statements
                    import_patterns = [
                        f'import {lib}',
                        f'from {lib}',
                        f'require.*{lib}',
                        f'const.*=.*require.*{lib}',
                        f'import.*from.*{lib}'
                    ]

                    # Check both dependency and import patterns
                    found_violation = False
                    all_patterns = dependency_patterns + import_patterns
                    print(f"DEBUG: Checking library '{lib}' with patterns: {all_patterns}")

                    for pattern in all_patterns:
                        if re.search(pattern, git_diff, re.IGNORECASE | re.MULTILINE):
                            print(f"DEBUG: MATCH FOUND for pattern '{pattern}'")
                            violations.append(f"BLOCKED: Forbidden library used: {lib}")
                            found_violation = True
                            break
                        else:
                            print(f"DEBUG: No match for pattern '{pattern}'")

                    if found_violation:
                        break

        # Check for allowed tech stack compliance (basic check)
        allowed_tech = governance_rules.get('ALLOWED_TECH_STACK', '')
        if allowed_tech and allowed_tech != 'Unknown/Detect from Codebase':
            # This is more complex - we'd need to analyze the tech stack used
            # For now, just log that we have constraints
            print(f"Tech stack constraints active: {allowed_tech[:50]}...")

        # Check security level
        security_level = governance_rules.get('STRICTNESS_LEVEL', 'MEDIUM')
        print(f"Security level: {security_level}")

        if violations:
            print("ERROR: Governance violations found:")
            for violation in violations:
                print(f"   {violation}")

            # Write violations to file for workflow to read
            with open('governance_violations.txt', 'w') as f:
                f.write('\n'.join(violations))

            return False
        else:
            print("SUCCESS: No governance violations detected")
            return True

    def run_dual_validation(self):
        """
        Run both spec validation (Phase A) and governance enforcement (Phase B)
        """
        print("STARTING: Starting Dual Validation System...")
        print("   Phase A: Spec Validation (PR-specific requirements)")
        print("   Phase B: Governance Enforcement (Global architecture rules)")

        # Get PR title
        if not self.pr_title:
            self.pr_title = self.get_pr_title()

        # Phase A: Spec Validation (existing logic)
        print("\n" + "="*60)
        print("PHASE: PHASE A: SPEC VALIDATION")
        print("="*60)

        if self.should_skip_validation(self.pr_title):
            print("WARNING:  Skipping Linear validation for infrastructure change")
            spec_passed = True
        else:
            # Run existing spec validation logic
            issue_id = self.extract_linear_issue_id(self.pr_title)
            if not issue_id:
                print("ERROR: Spec validation failed: No Linear issue ID")
                spec_passed = False
            else:
                issue = self.query_linear_issue(issue_id)
                if not issue:
                    spec_passed = False
                else:
                    notion_page_id = self.extract_notion_page_id(issue.get('description', ''))
                    if not notion_page_id:
                        spec_passed = False
                    else:
                        spec_content = self.fetch_notion_page(notion_page_id)
                        if not spec_content:
                            spec_passed = False
                        else:
                            git_diff = self.get_git_diff()
                            if git_diff:
                                spec_passed = self.validate_with_llm(spec_content, git_diff)
                            else:
                                spec_passed = True  # No changes = compliant

        # Phase B: Governance Enforcement (new logic)
        print("\n" + "="*60)
        print("GOVERNANCE: PHASE B: GOVERNANCE ENFORCEMENT")
        print("="*60)

        governance_rules = self.extract_governance_rules()
        if governance_rules:
            git_diff = self.get_git_diff()
            if git_diff:
                governance_passed = self.validate_governance_compliance(git_diff, governance_rules)
            else:
                governance_passed = True  # No changes = compliant
        else:
            print("ERROR: Governance extraction failed - cannot enforce rules")
            governance_passed = False

        # Final decision
        print("\n" + "="*60)
        print("RESULTS: VALIDATION RESULTS")
        print("="*60)
        print(f"Phase A (Spec): {'SUCCESS: PASSED' if spec_passed else 'ERROR: FAILED'}")
        print(f"Phase B (Governance): {'SUCCESS: PASSED' if governance_passed else 'ERROR: FAILED'}")

        if spec_passed and governance_passed:
            print("🎉 ALL VALIDATIONS PASSED - PR can proceed!")
            return
        else:
            print("BLOCKED: VALIDATION FAILED - Blocking PR")
            if not spec_passed:
                print("   Reason: Spec validation failed")
            if not governance_passed:
                print("   Reason: Governance violations detected")
            sys.exit(1)


if __name__ == "__main__":
    guard = ActionGuard()
    guard.run()
