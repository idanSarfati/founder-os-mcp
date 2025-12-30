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
from typing import Optional, Dict, Any
import google.generativeai as genai


class ActionGuard:
    def __init__(self):
        self.notion_token = os.getenv('NOTION_TOKEN')
        self.linear_api_key = os.getenv('LINEAR_API_KEY')
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.pr_title = os.getenv('PR_TITLE') or self.get_pr_title()
        self.pr_number = os.getenv('PR_NUMBER') or self.get_pr_number()

        if not all([self.notion_token, self.linear_api_key, self.github_token]):
            print("❌ Missing required environment variables")
            sys.exit(1)

        # Configure Gemini
        genai.configure(api_key=os.getenv('GEMINI_API_KEY', ''))
        self.model = genai.GenerativeModel('gemini-pro')

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

    def get_pr_number(self) -> str:
        """Get PR number from GitHub Actions environment"""
        pr_number = os.getenv('GITHUB_REF', '').split('/')[-2]
        if not pr_number.isdigit():
            print("❌ Could not determine PR number")
            sys.exit(1)
        return pr_number

    def extract_linear_issue_id(self, pr_title: str) -> Optional[str]:
        """Extract Linear issue ID from PR title (e.g., [FOS-101])"""
        match = re.search(r'\[([A-Z]+-\d+)\]', pr_title)
        return match.group(1) if match else None

    def query_linear_issue(self, issue_id: str) -> Optional[Dict[str, Any]]:
        """Query Linear API for issue details"""
        try:
            query = """
            query GetIssue($issueId: String!) {
                issue(id: $issueId) {
                    id
                    title
                    description
                    team {
                        name
                    }
                    labels {
                        name
                    }
                    project {
                        name
                    }
                }
            }
            """

            url = "https://api.linear.app/graphql"
            headers = {
                'Authorization': self.linear_api_key,
                'Content-Type': 'application/json'
            }

            response = requests.post(url, json={'query': query, 'variables': {'issueId': issue_id}}, headers=headers)
            response.raise_for_status()

            data = response.json()
            if data.get('data', {}).get('issue'):
                return data['data']['issue']
            else:
                print(f"❌ Linear issue {issue_id} not found")
                return None

        except Exception as e:
            print(f"❌ Failed to query Linear API: {e}")
            return None

    def extract_notion_page_id(self, issue_description: str) -> Optional[str]:
        """Extract Notion page ID from issue description"""
        # Look for Notion URLs in the description
        notion_pattern = r'notion\.so/([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})'
        match = re.search(notion_pattern, issue_description)
        return match.group(1) if match else None

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

    def get_git_diff(self) -> str:
        """Get git diff for the PR"""
        try:
            # Get the diff between the target branch and the PR branch
            result = subprocess.run(
                ['git', 'diff', '--no-pager', 'HEAD~1'],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )

            if result.returncode == 0:
                return result.stdout
            else:
                print("❌ Failed to get git diff")
                return ""

        except Exception as e:
            print(f"❌ Error getting git diff: {e}")
            return ""

    def validate_with_llm(self, spec_content: str, git_diff: str) -> bool:
        """Use LLM to validate if changes violate the spec"""
        try:
            prompt = f"""
            You are a code reviewer validating that code changes comply with business requirements.

            SPECIFICATION:
            {spec_content}

            CODE CHANGES (GIT DIFF):
            {git_diff}

            TASK: Analyze the code changes and determine if they violate any requirements in the specification.

            IMPORTANT: Respond with ONLY "YES" if the changes violate the spec, or "NO" if they comply.
            If violations are found, briefly explain why in the next line (max 100 words).
            """

            response = self.model.generate_content(prompt)
            result = response.text.strip()

            # Write result to file for workflow to read
            with open('validation_result.txt', 'w') as f:
                f.write(result)

            if result.upper().startswith('YES'):
                print(f"🚫 SPEC VIOLATION DETECTED: {result}")
                return False
            else:
                print("✅ Changes comply with specification")
                return True

        except Exception as e:
            print(f"❌ LLM validation failed: {e}")
            # Write error to file
            with open('validation_result.txt', 'w') as f:
                f.write(f"LLM validation failed: {str(e)}")
            return True  # Default to allowing if LLM fails

    def run(self):
        """Main execution flow"""
        print("🔍 Starting Action Guard validation...")

        # Step 1: Extract Linear Issue ID from PR title
        issue_id = self.extract_linear_issue_id(self.pr_title)
        if not issue_id:
            print("❌ Could not extract Linear issue ID from PR title")
            print(f"   PR Title: {self.pr_title}")
            print("   Expected format: [ISSUE-ID] in title")
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
