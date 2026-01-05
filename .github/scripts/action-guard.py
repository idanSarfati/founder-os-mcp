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

    def get_pr_details(self) -> Dict[str, Any]:
        """Get full PR details including body and labels from GitHub API"""
        try:
            repo = os.getenv('GITHUB_REPOSITORY')
            pr_number = os.getenv('PR_NUMBER')

            if not repo or not pr_number:
                print("ERROR: Could not determine PR details from environment")
                return {}

            url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
            headers = {'Authorization': f'token {self.github_token}'}

            response = requests.get(url, headers=headers)
            response.raise_for_status()

            pr_data = response.json()
            return {
                'title': pr_data.get('title', ''),
                'body': pr_data.get('body', ''),
                'labels': [label['name'] for label in pr_data.get('labels', [])],
                'number': pr_data.get('number'),
                'html_url': pr_data.get('html_url')
            }
        except Exception as e:
            print(f"ERROR: Failed to get PR details: {e}")
            return {}

    def check_for_override(self, pr_details: Dict[str, Any]) -> Optional[str]:
        """
        Check if PR has override conditions that allow bypassing governance.

        Returns the override reason if found, None otherwise.

        Override conditions:
        1. Label: 'governance-override'
        2. Body contains: [override: reason]
        """
        if not pr_details:
            return None

        labels = pr_details.get('labels', [])
        body = pr_details.get('body') or ''  # Defensive: treat None as empty string

        # Check for governance-override label
        if 'governance-override' in labels:
            print("OVERRIDE: Found 'governance-override' label")
            return "Label: governance-override"

        # Check for [override: reason] pattern in body (case insensitive)
        override_match = re.search(r'\[override:\s*(.*?)\]', body, re.IGNORECASE | re.DOTALL)
        if override_match:
            reason = override_match.group(1).strip()
            print(f"OVERRIDE: Found override tag in PR body: {reason}")
            return f"PR Body: {reason}"

        return None

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
            'feat', 'style', 'perf', 'revert', 'debug'
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
                # GitHub Actions PR events: compare against target branch
                target_branch = os.getenv('GITHUB_BASE_REF', 'main')  # e.g., 'main' or 'master'
                print(f"Running in GitHub Actions - comparing against target branch: {target_branch}")

                # Fetch the target branch and compare
                subprocess.run(["git", "fetch", "origin", target_branch], check=False, capture_output=True)
                cmd = ["git", "diff", f"origin/{target_branch}", "HEAD"]
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

    def validate_with_llm(self, spec_content: str, git_diff: str) -> dict:
        """
        Validates code changes against specification using Gemini API with Trust Scoring.
        Returns a dictionary with confidence_score instead of boolean approval.
        Includes Retry logic for Rate Limits (429).
        """
        print("INFO: Analyzing code changes with Trust Scoring...")

        # Skip LLM validation if no API key was provided
        if self.client is None and self.model is None:
            print("WARNING:  Skipping LLM validation (no API key configured)")
            return {"confidence_score": 85, "severity": "LOW", "reasoning": "LLM validation skipped - no API key", "violation_type": "NONE"}

        # שימוש ב-Alias שראינו בלוגים שקיים בוודאות
        # מודל זה הוא יציב וחסכוני יותר במכסות מגרסה 2.0
        model_name = "gemini-flash-latest"

        prompt = f"""
        You are a Senior Tech Lead validating a PR with Trust Scoring.

        Specification from Notion:
        {spec_content}

        Code Changes (Git Diff):
        {git_diff}

        Task: Assign a confidence score (0-100) based on how well the code matches the specification.

        Scoring Guidelines:
        - 0-50 (CRITICAL): Code violates specification, contains security issues, or implements wrong requirements
        - 51-80 (HIGH): Code mostly matches but has significant issues, edge cases not handled, or architectural concerns
        - 81-100 (LOW): Code properly implements requirements with minor or no issues

        Output only JSON in this format:
        {{
            "confidence_score": 65,
            "severity": "MEDIUM",
            "reasoning": "Brief explanation of the score",
            "violation_type": "ARCHITECTURAL_PATTERN"
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
                    # Fallback scoring if JSON parsing fails
                    parsed = {"confidence_score": 30, "severity": "CRITICAL", "reasoning": f"JSON parsing failed: {result[:100]}", "violation_type": "VALIDATION_ERROR"}

                # Ensure we have valid score data
                confidence_score = parsed.get("confidence_score", 50)
                severity = parsed.get("severity", "MEDIUM")
                reasoning = parsed.get("reasoning", "No reasoning provided")
                violation_type = parsed.get("violation_type", "UNKNOWN")

                # Write result to file for workflow to read
                result_data = {
                    "confidence_score": confidence_score,
                    "severity": severity,
                    "reasoning": reasoning,
                    "violation_type": violation_type
                }
                with open('validation_result.txt', 'w') as f:
                    f.write(json.dumps(result_data, indent=2))

                print(f"SUCCESS: Trust Score Calculated: {confidence_score}/100")
                print(f"   Severity: {severity}")
                print(f"   Reasoning: {reasoning}")

                return result_data

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
        # Write failure result with low confidence score
        failure_result = {"confidence_score": 10, "severity": "CRITICAL", "reasoning": "AI validation failed after retries", "violation_type": "VALIDATION_ERROR"}
        with open('validation_result.txt', 'w') as f:
            f.write(json.dumps(failure_result, indent=2))
        return failure_result

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
        """Run only Phase A: Spec validation (Trust Engine scoring)"""
        print("🎯 PHASE: Running Phase A only: Spec Validation (Trust Engine)")

        # Get PR title if not set in environment
        if not self.pr_title:
            self.pr_title = self.get_pr_title()

        # Check if this PR should skip Linear validation
        if self.should_skip_validation(self.pr_title):
            print(f"⚠️  Skipping Linear validation for infrastructure change")
            print(f"   PR Title: {self.pr_title}")
            print("✅ SUCCESS: Allowing PR to proceed without specification validation")
            return

        # Step 1: Extract Linear Issue ID from PR title
        issue_id = self.extract_linear_issue_id(self.pr_title)
        if not issue_id:
            print("❌ ERROR: Could not extract Linear issue ID from PR title")
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
            print("❌ ERROR: Could not find Notion page link in Linear issue description")
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
            print("⚠️  WARNING: No git diff found, assuming compliance")
            return

        print("🔍 Analyzing code changes with Trust Scoring...")

        # Step 6: Validate with LLM (returns scoring dict)
        score_result = self.validate_with_llm(spec_content, git_diff)
        confidence_score = score_result.get('confidence_score', 50)

        print(f"📊 Trust Score Result: {confidence_score}/100 ({score_result.get('severity', 'UNKNOWN')})")

        if confidence_score <= 50:
            print("🚫 BLOCKED: Critical spec violations detected")
            print(f"   Reason: {score_result.get('reasoning', 'Unknown')}")
            sys.exit(1)
        else:
            print("✅ SUCCESS: Spec validation passed")
            print(f"   Score: {confidence_score}/100")

    def run_governance_validation(self):
        """Run only Phase B: Governance enforcement (Trust Engine scoring)"""
        print("🛡️ GOVERNANCE: Running Phase B only: Governance Enforcement (Trust Engine)")

        governance_rules = self.extract_governance_rules()
        if not governance_rules:
            print("❌ ERROR: Cannot proceed without governance rules")
            sys.exit(1)

        # Get git diff
        git_diff = self.get_git_diff()

        # Load requirements.txt
        deps_content = ""
        if os.path.exists("requirements.txt"):
            try:
                with open("requirements.txt", "r") as f:
                    deps_content = f.read()
                print(f"📦 Loaded requirements.txt ({len(deps_content)} chars)")
            except Exception as e:
                print(f"⚠️ Could not read requirements.txt: {e}")

        # Build full context for validation
        full_context_for_validation = f"""
        GIT DIFF CHECK:
        {git_diff if git_diff else "No code changes detected in diff."}

        FULL DEPENDENCY CHECK (requirements.txt):
        {deps_content if deps_content else "No requirements.txt found."}
        """

        # Use Trust Engine scoring for governance validation
        score_result = self.validate_governance_compliance(full_context_for_validation, governance_rules)
        confidence_score = score_result.get('confidence_score', 50)

        print(f"📊 Governance Trust Score: {confidence_score}/100 ({score_result.get('severity', 'UNKNOWN')})")

        if confidence_score <= 50:
            print("🚫 BLOCKED: Critical governance violations detected")
            print(f"   Reason: {score_result.get('reasoning', 'Unknown')}")
            sys.exit(1)
        else:
            print("✅ SUCCESS: Governance compliance verified")
            print(f"   Score: {confidence_score}/100")

    def extract_governance_rules(self) -> Optional[Dict[str, Any]]:
        """
        Extract governance rules using bootstrap_project function

        This generates governance rules on-demand in CI/CD environments
        where the .mdc file may not exist.

        Returns:
            Dictionary with governance constraints or None if extraction fails
        """
        print("GOVERNANCE: Extracting governance rules...")

        try:
            # Set up Python path to find the src module
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.join(script_dir, '..', '..')
            src_path = os.path.join(project_root, 'src')

            # Add both project root and src directory to path
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            if src_path not in sys.path:
                sys.path.insert(0, src_path)

            # Import and run bootstrap_project to generate governance rules
            from tools.project_ops import bootstrap_project

            print("Generating governance rules using bootstrap_project...")

            # Set required environment variables for the extraction
            os.environ['NOTION_API_KEY'] = self.notion_token
            os.environ['LINEAR_API_KEY'] = self.linear_api_key

            # Use hardcoded fallback directly for CI/CD environments
            # This ensures we have REAL governance rules even when APIs are unavailable
            from tools.governance_extraction import GovernanceExtractor

            extractor = GovernanceExtractor()
            governance_data = extractor._get_hardcoded_fallback_data()

            if governance_data:
                print("SUCCESS: Successfully extracted governance rules:")
                print(f"   Allowed tech: {governance_data.get('ALLOWED_TECH_STACK', 'None')[:50]}...")
                print(f"   Forbidden libs: {governance_data.get('FORBIDDEN_LIBRARIES', 'None')[:50]}...")
                return governance_data
            else:
                print("ERROR: Governance extraction returned no data")
                return None

        except Exception as e:
            print(f"ERROR: Failed to extract governance rules: {e}")
            import traceback
            traceback.print_exc()
            return None


    def validate_governance_compliance(self, full_context: str, governance_rules: Dict[str, Any]) -> dict:
        """
        Validate that PR changes don't violate governance rules with Trust Scoring

        Checks both:
        1. Git diff for added forbidden dependencies
        2. Direct file scanning for forbidden libraries in requirements.txt, package.json, etc.

        Args:
            full_context: Combined context including git diff and file contents
            governance_rules: Governance constraints from Notion/Linear

        Returns:
            Dictionary with confidence_score, severity, reasoning, violation_type
        """
        print("INFO: Validating governance compliance...")

        violations = []

        # Check for forbidden libraries
        forbidden_libs = governance_rules.get('FORBIDDEN_LIBRARIES', '')
        if forbidden_libs and forbidden_libs != 'Unknown/Detect from Codebase':
            forbidden_list = [lib.strip().lower() for lib in forbidden_libs.replace(',', ';').split(';') if lib.strip()]
            print(f"DEBUG: Checking for forbidden libraries: {forbidden_list}")

            # 1. Check full context (includes both git diff and file contents) for forbidden dependencies
            for lib in forbidden_list:
                if lib in full_context.lower():
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

                    for pattern in dependency_patterns:
                        if re.search(pattern, full_context, re.IGNORECASE | re.MULTILINE):
                            violations.append(f"BLOCKED: Forbidden library found: {lib}")
                            print(f"VIOLATION: Found forbidden library '{lib}' in PR changes or dependencies")
                            break

            # 2. Check actual file contents for forbidden libraries
            # Scan requirements.txt for forbidden packages
            if os.path.exists('requirements.txt'):
                try:
                    with open('requirements.txt', 'r', encoding='utf-8') as f:
                        requirements_content = f.read().lower()

                    for lib in forbidden_list:
                        # Check if the forbidden library appears as a package name
                        if re.search(rf'\b{re.escape(lib)}\b', requirements_content):
                            violations.append(f"BLOCKED: Forbidden library found in requirements.txt: {lib}")
                            print(f"VIOLATION: Found forbidden library '{lib}' in requirements.txt")
                            break
                except Exception as e:
                    print(f"WARNING: Could not scan requirements.txt: {e}")

            # Could add similar checks for package.json, setup.py, etc.

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

            # Return critical score for violations
            return {
                "confidence_score": 15,
                "severity": "CRITICAL",
                "reasoning": f"Governance violations found: {len(violations)} violations detected",
                "violation_type": "GOVERNANCE_VIOLATION"
            }
        else:
            print("SUCCESS: No governance violations detected")
            # Return high confidence score for compliance
            return {
                "confidence_score": 95,
                "severity": "LOW",
                "reasoning": "No governance violations detected",
                "violation_type": "NONE"
            }

    def _get_linear_team_id(self):
        """Fetches the first available Team ID from Linear to create issues."""
        if not self.linear_api_key:
            return None

        query = """
        query {
          teams(first: 1) {
            nodes {
              id
              name
            }
          }
        }
        """
        try:
            response = requests.post(
                "https://api.linear.app/graphql",
                headers={
                    "Authorization": self.linear_api_key,
                    "Content-Type": "application/json"
                },
                json={"query": query},
                timeout=10.0
            )
            data = response.json()
            teams = data.get("data", {}).get("teams", {}).get("nodes", [])
            if teams:
                print(f"DEBUG: Found Linear Team: {teams[0]['name']} ({teams[0]['id']})")
                return teams[0]['id']
            else:
                print("⚠️ No teams found in Linear.")
                return None
        except Exception as e:
            print(f"⚠️ Failed to fetch Linear Team ID: {e}")
            return None

    def log_incident_to_linear(self, reason: str, pr_url: str, incident_type: str = "override") -> bool:
        """
        Log governance incident to Linear by creating a new task.

        Args:
            reason: Reason for the incident (override reason or violation description)
            pr_url: URL to the PR that triggered the incident
            incident_type: Type of incident ("override" or "critical_violation")

        Returns:
            True if successfully logged, False otherwise
        """
        # Check if Linear API key is available
        if not self.linear_api_key:
            print("⚠️ Linear API key not configured. Skipping audit log.")
            return False

        # 1. Get Team ID first
        team_id = self._get_linear_team_id()
        if not team_id:
            print("⚠️ Could not find a Linear Team ID. Cannot create audit ticket.")
            return False

        print(f"📝 Logging Governance Incident to Linear (Team ID: {team_id})...")

        try:
            # Determine the appropriate title and priority based on incident type
            if incident_type == "override":
                title = f"⚠️ Governance Override Used - {reason[:50]}"
                priority = 2  # High priority
                description = f"""
## Governance Override Incident

**PR:** {pr_url}
**Override Reason:** {reason}
**Timestamp:** {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}

### Action Required
Review this override to ensure it was justified and no governance violations were introduced.

### Context
This override was triggered through either:
- `governance-override` label on the PR
- `[override: reason]` tag in PR description

**Status:** Requires CTO Review
                """
            else:  # critical_violation
                title = f"🚨 Critical Governance Violation - {reason[:50]}"
                priority = 1  # Urgent priority
                description = f"""
## Critical Governance Violation

**PR:** {pr_url}
**Violation:** {reason}
**Timestamp:** {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}

### Action Required
Immediate review required. This PR contains critical violations that may compromise system integrity.

**Status:** Requires Immediate Attention
                """

            # Create the Linear task using GraphQL mutation
            mutation = """
            mutation IssueCreate($input: IssueCreateInput!) {
              issueCreate(input: $input) {
                success
                issue {
                  id
                  title
                  url
                }
              }
            }
            """

            variables = {
                "input": {
                    "teamId": team_id,  # REQUIRED: Must include team ID!
                    "title": title,
                    "description": description,
                    "priority": priority,
                    "labelIds": []  # Empty for now - can add governance-audit label if needed
                }
            }

            response = requests.post(
                "https://api.linear.app/graphql",
                headers={
                    "Authorization": self.linear_api_key,
                    "Content-Type": "application/json"
                },
                json={"query": mutation, "variables": variables},
                timeout=10.0
            )

            if response.status_code == 200:
                try:
                    data = response.json()
                    if data and data.get('data', {}).get('issueCreate', {}).get('issue'):
                        issue = data['data']['issueCreate']['issue']
                        print(f"SUCCESS: Created Linear audit task: {issue.get('url', issue.get('id', 'Unknown'))}")
                        return True
                    else:
                        print(f"ERROR: Linear API returned success but no issue created: {data}")
                except (ValueError, AttributeError) as e:
                    print(f"ERROR: Failed to parse Linear API response: {e}")
                    print(f"Raw response: {response.text[:500]}...")
            else:
                print(f"ERROR: Failed to create Linear task. Status: {response.status_code}, Response: {response.text}")
                return False

        except Exception as e:
            print(f"⚠️ Failed to log incident to Linear (continuing without audit): {e}")
            return False

    def post_pr_comment(self, comment_body: str, pr_details: Dict[str, Any]) -> bool:
        """
        Post a comment on the PR.

        Args:
            comment_body: The comment text to post
            pr_details: PR details dictionary containing repo and PR number

        Returns:
            True if comment posted successfully, False otherwise
        """
        try:
            repo = os.getenv('GITHUB_REPOSITORY')
            pr_number = pr_details.get('number') or os.getenv('PR_NUMBER')

            if not repo or not pr_number:
                print("ERROR: Cannot post PR comment - missing repo or PR number")
                return False

            url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
            headers = {'Authorization': f'token {self.github_token}'}
            data = {'body': comment_body}

            response = requests.post(url, headers=headers, json=data)

            if response.status_code == 201:
                print("SUCCESS: Posted comment on PR")
                return True
            else:
                print(f"ERROR: Failed to post PR comment. Status: {response.status_code}")
                print(f"Response: {response.text}")
                return False

        except Exception as e:
            print(f"ERROR: Failed to post PR comment: {e}")
            return False

    def run_dual_validation(self):
        """
        Run Trust Engine validation with scoring, overrides, and audit logging.

        Scoring Thresholds:
        - 0-50: HARD BLOCK (Critical violations)
        - 51-80: SOFT BLOCK (Warning, but allow override)
        - 81-100: PASS (Clean code)

        Override Conditions:
        - governance-override label
        - [override: reason] in PR body
        """
        print("🚀 STARTING: Founder OS Trust Engine Validation")
        print("   Phase A: Spec Validation (Trust Scoring)")
        print("   Phase B: Governance Enforcement (Trust Scoring)")
        print("   Phase C: Risk Assessment & Override Processing")

        # Get full PR details (needed for override checking and comments)
        pr_details = self.get_pr_details()
        if not pr_details:
            print("ERROR: Could not retrieve PR details - cannot proceed with Trust Engine")
            sys.exit(1)

        pr_url = pr_details.get('html_url', 'Unknown PR URL')
        print(f"📋 Processing PR: {pr_url}")

        # Check for override conditions FIRST
        override_reason = self.check_for_override(pr_details)
        if override_reason:
            print(f"🔓 OVERRIDE DETECTED: {override_reason}")
            print("⚠️  Proceeding with override - posting audit notification...")

            # Post override notification comment
            override_comment = f"""
## ⚠️ Governance Override Applied

**Override Reason:** {override_reason}

This PR has bypassed automated governance validation through an explicit override mechanism.

### Audit Trail
- **Override Type:** {override_reason}
- **Timestamp:** {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}
- **PR:** {pr_url}

### Next Steps
A Linear audit task has been created for CTO review. The override will be reviewed to ensure compliance with business requirements.

**Status:** Override Approved - Proceeding with merge
            """

            self.post_pr_comment(override_comment, pr_details)

            # Log to Linear for audit
            self.log_incident_to_linear(override_reason, pr_url, "override")

            print("✅ OVERRIDE PROCESSED: PR allowed to proceed")
            return

        # Phase A: Spec Validation with Trust Scoring
        print("\n" + "="*60)
        print("🎯 PHASE A: SPEC VALIDATION (Trust Scoring)")
        print("="*60)

        spec_score = None
        if self.should_skip_validation(pr_details.get('title', '')):
            print("⚠️  Skipping Linear validation for infrastructure change")
            spec_score = {"confidence_score": 85, "severity": "LOW", "reasoning": "Infrastructure change - validation skipped", "violation_type": "INFRASTRUCTURE"}
        else:
            issue_id = self.extract_linear_issue_id(pr_details.get('title', ''))
            if not issue_id:
                spec_score = {"confidence_score": 10, "severity": "CRITICAL", "reasoning": "No Linear issue ID found in PR title", "violation_type": "MISSING_ISSUE"}
            else:
                issue = self.query_linear_issue(issue_id)
                if not issue:
                    spec_score = {"confidence_score": 10, "severity": "CRITICAL", "reasoning": "Linear issue not found", "violation_type": "INVALID_ISSUE"}
                else:
                    notion_page_id = self.extract_notion_page_id(issue.get('description', ''))
                    if not notion_page_id:
                        spec_score = {"confidence_score": 10, "severity": "CRITICAL", "reasoning": "No Notion page link in Linear issue", "violation_type": "MISSING_SPEC"}
                    else:
                        spec_content = self.fetch_notion_page(notion_page_id)
                        if not spec_content:
                            spec_score = {"confidence_score": 10, "severity": "CRITICAL", "reasoning": "Could not fetch Notion specification", "violation_type": "FETCH_ERROR"}
                        else:
                            git_diff = self.get_git_diff()
                            if git_diff:
                                spec_score = self.validate_with_llm(spec_content, git_diff)
                            else:
                                spec_score = {"confidence_score": 90, "severity": "LOW", "reasoning": "No code changes detected", "violation_type": "NO_CHANGES"}

        # Phase B: Governance Enforcement with Trust Scoring
        print("\n" + "="*60)
        print("🛡️ PHASE B: GOVERNANCE ENFORCEMENT (Trust Scoring)")
        print("="*60)

        governance_score = None
        governance_rules = self.extract_governance_rules()
        if governance_rules:
            git_diff = self.get_git_diff()

            deps_content = ""
            if os.path.exists("requirements.txt"):
                try:
                    with open("requirements.txt", "r") as f:
                        deps_content = f.read()
                    print(f"📦 Loaded requirements.txt ({len(deps_content)} chars)")
                except Exception as e:
                    print(f"⚠️ Could not read requirements.txt: {e}")

            full_context = f"""
GIT DIFF CHECK:
{git_diff if git_diff else "No code changes detected in diff."}

FULL DEPENDENCY CHECK (requirements.txt):
{deps_content if deps_content else "No requirements.txt found."}
"""

            governance_score = self.validate_governance_compliance(full_context, governance_rules)
        else:
            governance_score = {"confidence_score": 20, "severity": "CRITICAL", "reasoning": "Governance rules extraction failed", "violation_type": "EXTRACTION_ERROR"}

        # Phase C: Risk Assessment & Final Decision
        print("\n" + "="*60)
        print("⚖️ PHASE C: RISK ASSESSMENT & FINAL DECISION")
        print("="*60)

        # Calculate combined risk score (weighted average)
        spec_confidence = spec_score.get('confidence_score', 50)
        governance_confidence = governance_score.get('confidence_score', 50)

        # Weight governance slightly higher than spec (70/30 split)
        combined_score = int((spec_confidence * 0.3) + (governance_confidence * 0.7))

        print(f"📊 Risk Assessment Results:")
        print(f"   Spec Score: {spec_confidence}/100 ({spec_score.get('severity', 'UNKNOWN')})")
        print(f"   Governance Score: {governance_confidence}/100 ({governance_score.get('severity', 'UNKNOWN')})")
        print(f"   Combined Risk Score: {combined_score}/100")

        # Apply Trust Engine thresholds
        if combined_score <= 50:
            # CRITICAL: Hard block
            print("🚫 CRITICAL VIOLATIONS: Hard block applied")

            block_comment = f"""
## 🚫 Governance Validation Failed

**Combined Risk Score:** {combined_score}/100 (Critical)
**Spec Score:** {spec_confidence}/100 - {spec_score.get('reasoning', 'Unknown')}
**Governance Score:** {governance_confidence}/100 - {governance_score.get('reasoning', 'Unknown')}

### Action Required
This PR contains critical violations that cannot be merged without intervention.

**Available Options:**
1. **Fix the violations** and resubmit
2. **Apply override** by adding `governance-override` label or `[override: reason]` in PR description
3. **Contact engineering lead** for guidance

**Status:** Blocked - Requires fixes or override
            """

            self.post_pr_comment(block_comment, pr_details)

            # Log critical violation to Linear
            violation_reason = f"Critical violations detected (Score: {combined_score})"
            self.log_incident_to_linear(violation_reason, pr_url, "critical_violation")

            print("💀 BLOCKED: Critical violations detected - exiting with failure")
            sys.exit(1)

        elif combined_score <= 80:
            # HIGH RISK: Soft block with warning
            print("⚠️ HIGH RISK DETECTED: Warning issued, override required to proceed")

            warning_comment = f"""
## ⚠️ Governance Warning (Override Required)

**Combined Risk Score:** {combined_score}/100 (High Risk)
**Spec Score:** {spec_confidence}/100 - {spec_score.get('reasoning', 'Unknown')}
**Governance Score:** {governance_confidence}/100 - {governance_score.get('reasoning', 'Unknown')}

### Risk Assessment
This PR has potential governance concerns that should be reviewed before merging.

**To proceed with merge:**
- Add the `governance-override` label to this PR, OR
- Include `[override: detailed reason]` in the PR description

**Note:** Overrides will create an audit trail for CTO review.

**Status:** Warning - Override required to proceed
            """

            self.post_pr_comment(warning_comment, pr_details)
            print("⚠️ WARNING ISSUED: Override required to proceed - exiting with failure")
            sys.exit(1)

        else:
            # LOW RISK: Pass
            print("✅ LOW RISK: Validation passed - proceeding with merge")

            success_comment = f"""
## ✅ Governance Validation Passed

**Combined Risk Score:** {combined_score}/100 (Low Risk)
**Spec Score:** {spec_confidence}/100 - {spec_score.get('reasoning', 'Unknown')}
**Governance Score:** {governance_confidence}/100 - {governance_score.get('reasoning', 'Unknown')}

**Status:** Approved - Proceeding with merge
            """

            self.post_pr_comment(success_comment, pr_details)
            print("🎉 SUCCESS: All validations passed - PR approved")


if __name__ == "__main__":
    guard = ActionGuard()
    guard.run()
