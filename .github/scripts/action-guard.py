#!/usr/bin/env python3
"""
GitHub Action Guard - CI/CD Spec Validation

This script validates that PR changes comply with the Notion specification
linked to the Linear issue referenced in the PR title.
"""

import os
import sys
import re
import json
import requests
import subprocess
import time
from typing import Optional, Dict, Any

try:
    import google.genai as genai
    USE_NEW_PACKAGE = True
except ImportError:
    try:
        import google.generativeai as genai
        USE_NEW_PACKAGE = False
    except ImportError:
        print("❌ Neither google.genai nor google.generativeai packages are available")
        sys.exit(1)


class ActionGuard:
    def __init__(self):
        self.pr_title = os.getenv('PR_TITLE', '')
        self.pr_number = os.getenv('PR_NUMBER', '')
        self.github_token = os.getenv('GITHUB_TOKEN', '')
        self.notion_token = os.getenv('NOTION_TOKEN', '')
        self.linear_api_key = os.getenv('LINEAR_API_KEY', '')

        if not all([self.notion_token, self.linear_api_key, self.github_token]):
            print("❌ Missing required environment variables")
            sys.exit(1)

        # Configure Gemini
        api_key = os.getenv('GEMINI_API_KEY', '')
        if not api_key:
            print("⚠️  GEMINI_API_KEY environment variable not set")
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
            print(f"❌ Failed to initialize Google AI client: {e}")
            print("   Please check your GEMINI_API_KEY and package installation")
            sys.exit(1)

    def get_pr_title(self) -> str:
        """Get PR title from GitHub API"""
        try:
            # Get PR info from environment (set by GitHub Actions)
            repo = os.getenv('GITHUB_REPOSITORY')
            pr_number = os.getenv('PR_NUMBER')

            if not repo or not pr_number:
                print("❌ Could not determine PR details from environment")
                sys.exit(1)

            url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
            headers = {'Authorization': f'token {self.github_token}'}

            response = requests.get(url, headers=headers)
            response.raise_for_status()

            return response.json()['title']
        except Exception as e:
            print(f"❌ Failed to get PR title: {e}")
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
            'readme', 'documentation', 'chore', 'refactor', 'test'
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
            print("❌ Could not extract Linear issue ID from PR title")
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
            print(f"🔍 Making Linear API request for issue: {issue_id}")
            print(f"📡 Headers: Content-Type={headers.get('Content-Type')}, Auth starts with: {headers.get('Authorization', '')[:10]}...")

            response = requests.post(url, json={'query': query, 'variables': {'issueId': issue_id}}, headers=headers)

            # Debug: Print full response details
            print(f"📡 Response Status: {response.status_code}")
            print(f"📡 Response Headers: {dict(response.headers)}")

            if response.status_code != 200:
                print(f"❌ Full Response Body: {response.text}")
                print("❌ Linear API request failed - check authentication and request format")
                return None

            data = response.json()
            if data.get('data', {}).get('issue'):
                issue = data['data']['issue']
                print(f"✅ Found Linear issue: {issue.get('title', 'Unknown')}")
                return issue
            else:
                print(f"❌ Linear issue {issue_id} not found in response")
                print(f"Response data: {data}")
                return None

        except Exception as e:
            print(f"❌ Failed to query Linear API: {e}")
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

        print(f"🔍 Searching for Notion link in description: '{description}'")

        # Search for sequence of 32 hex characters (a-f, 0-9)
        # that comes after notion.so/ and optionally after text and dash
        # Example: notion.so/some-title-1234567890abcdef1234567890abcdef

        # Search all occurrences of notion.so and find the ID at the end of the path
        # This regex captures the last 32 characters before question mark (query params) or end of line
        match = re.search(r"notion\.so/(?:[^/]+/)*?([a-zA-Z0-9-]*?)([a-fA-F0-9]{32})(?:\?|$|\s|/)", description)

        if match:
            # group(2) is the ID itself (32 characters)
            page_id = match.group(2)
            print(f"✅ Found Notion page ID: {page_id}")
            return page_id

        print("❌ No Notion page ID found in description")
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
            print(f"❌ Failed to fetch Notion page: {e}")
            return None

    def get_git_diff(self):
        """
        Retrieves git diff looking at the merge commit parents.
        Best for GitHub Actions pull_request events.
        """
        print("🔍 Getting git diff...")

        try:
            # אופציה 1: השיטה הקלאסית ל-GitHub Actions (השוואה מול ה-Base של המיזוג)
            # HEAD^1 = המצב של main לפני המיזוג
            # HEAD = המצב אחרי המיזוג (כולל השינויים שלך)
            print("⚖️ Attempting diff against merge parent (HEAD^1)...")

            # אנחנו מוסיפים --no-color כדי להקל על העיבוד
            cmd = ["git", "diff", "HEAD^1", "HEAD"]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )

            if result.returncode == 0 and result.stdout.strip():
                print(f"✅ Found diff using HEAD^1 ({len(result.stdout)} chars)")
                return result.stdout

            # אופציה 2: גיבוי למקרה שאנחנו לא ב-Merge Commit (למשל Rebase)
            print("⚠️ HEAD^1 failed or empty, falling back to origin/main...")
            subprocess.run(["git", "fetch", "origin", "main"], check=False)
            cmd_fallback = ["git", "diff", "origin/main", "HEAD"]

            result_fallback = subprocess.run(
                cmd_fallback,
                capture_output=True,
                text=True
            )

            diff_out = result_fallback.stdout.strip()
            if diff_out:
                print(f"✅ Found diff using origin/main ({len(diff_out)} chars)")
                return diff_out

            print("⚠️ Git diff is truly empty (checked both methods)")
            return ""

        except Exception as e:
            print(f"❌ Error getting git diff: {e}")
            return None

    def validate_with_llm(self, spec_content: str, git_diff: str) -> bool:
        """
        Validates code changes against specification using Gemini API.
        Includes Retry logic for Rate Limits (429).
        """
        print("🔍 Analyzing code changes...")

        # Skip LLM validation if no API key was provided
        if self.client is None and self.model is None:
            print("⚠️  Skipping LLM validation (no API key configured)")
            return True

        # Use the available model from the debug output
        model_name = "gemini-2.0-flash"

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
                    print("✅ AI Validation Passed")
                    print(f"   Comments: {parsed.get('comments', '')}")
                    return True
                else:
                    print("❌ AI Validation Failed:")
                    print(f"   Reason: {parsed.get('comments', '')}")
                    print(f"   Issues: {parsed.get('critical_issues', [])}")
                    return False

            except Exception as e:
                error_str = str(e)
                print(f"⚠️  Attempt {attempt + 1}/{max_retries} failed: {error_str[:200]}...")

                # אם זה Rate Limit (429), נחכה וננסה שוב
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    wait_time = 20
                    print(f"⏳ Hit rate limit. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    # אם זו שגיאה אחרת, נחכה קצת ונסה שוב
                    time.sleep(2)

        print("❌ LLM validation failed after all retries.")
        # Write failure result
        with open('validation_result.txt', 'w') as f:
            f.write(json.dumps({"approved": False, "comments": "AI validation failed after retries", "critical_issues": ["Validation system error"]}, indent=2))
        return False  # חשוב מאוד! מחזירים False כדי לחסום את ה-PR במקרה של כישלון

    def run(self):
        """Main execution flow"""
        print("🔍 Starting Action Guard validation...")

        # Get PR title if not set in environment
        if not self.pr_title:
            self.pr_title = self.get_pr_title()

        # Check if this PR should skip Linear validation
        if self.should_skip_validation(self.pr_title):
            print(f"⚠️  Skipping Linear validation for infrastructure change")
            print(f"   PR Title: {self.pr_title}")
            print("✅ Allowing PR to proceed without specification validation")
            return

        # Step 1: Extract Linear Issue ID from PR title
        issue_id = self.extract_linear_issue_id(self.pr_title)
        if not issue_id:
            print("❌ Could not extract Linear issue ID from PR title")
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
            print("❌ Could not find Notion page link in Linear issue description")
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
            print("⚠️  No git diff found, assuming compliance")
            return

        print("🔍 Analyzing code changes...")

        # Step 6: Validate with LLM
        is_compliant = self.validate_with_llm(spec_content, git_diff)

        if not is_compliant:
            print("🚫 PR blocked due to spec violation")
            sys.exit(1)
        else:
            print("✅ PR approved - changes comply with specification")


if __name__ == "__main__":
    guard = ActionGuard()
    guard.run()
