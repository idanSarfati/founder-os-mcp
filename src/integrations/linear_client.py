"""
Linear API client for fetching and formatting tasks.

This module provides a clean interface to Linear's GraphQL API,
encapsulating task retrieval and formatting for LLM consumption.
"""

import os
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv, find_dotenv

from config.auth_config import load_auth_config
from src.utils.logger import logger


class LinearClient:
    """
    Handles communication with Linear GraphQL API.
    
    Encapsulates task retrieval and formatting for LLM consumption.
    Provides methods to fetch active tasks (assigned + team issues)
    and detailed task information.
    """

    def __init__(self):
        """
        Initialize Linear client with API key from environment.

        Uses centralized auth configuration loader to ensure all
        required secrets are available before making API calls.
        """
        # Centralized config loading (kept for backward compatibility
        # with existing auth setup and .env handling)
        load_auth_config()
        # Use find_dotenv() to locate .env file relative to project root
        env_path = find_dotenv()
        if env_path:
            load_dotenv(dotenv_path=env_path)
        else:
            # Fallback: try loading from project root relative to this file
            project_root = Path(__file__).parent.parent.parent
            env_file = project_root / ".env"
            if env_file.exists():
                load_dotenv(dotenv_path=str(env_file))
            else:
                load_dotenv()

        self.api_key = os.getenv("LINEAR_API_KEY")
        self.endpoint = "https://api.linear.app/graphql"

        if not self.api_key:
            raise ValueError("LINEAR_API_KEY missing in environment.")

    def _execute_query(self, query: str, variables: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL query against Linear API.
        
        Args:
            query: GraphQL query string
            variables: Optional query variables
            
        Returns:
            Parsed JSON response data
            
        Raises:
            RuntimeError: If API request fails or GraphQL returns errors
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": self.api_key
        }
        
        # Log query type (extract operation name from query for better logging)
        query_type = query.strip().split()[1] if query.strip().startswith("query") else "mutation"
        logger.debug(f"Executing Linear GraphQL {query_type} query")
        
        try:
            response = requests.post(
                self.endpoint,
                json={"query": query, "variables": variables},
                headers=headers,
                timeout=10
            )
            
            # Try to parse response JSON even if status is not 200
            try:
                data = response.json()
            except:
                data = {}
            
            # Check for HTTP errors and include response body in error message
            if not response.ok:
                error_msg = f"HTTP {response.status_code}: {response.reason}"
                if data and "errors" in data:
                    error_msg += f" - GraphQL Errors: {data['errors']}"
                elif response.text:
                    error_msg += f" - Response: {response.text[:500]}"
                logger.error(f"Linear API HTTP error: {error_msg}")
                raise RuntimeError(f"Linear API Error: {error_msg}")
            
            if "errors" in data:
                logger.error(f"Linear GraphQL errors: {data['errors']}")
                raise RuntimeError(f"Linear GraphQL Error: {data['errors']}")
            
            logger.debug(f"Linear GraphQL query completed successfully")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.exception("Linear API connection failed")
            raise RuntimeError(f"Linear Connection Failed: {str(e)}")
        except RuntimeError:
            # Re-raise RuntimeError as-is (already formatted)
            raise
        except Exception as e:
            logger.exception("Unexpected error in Linear API query")
            raise RuntimeError(f"Unexpected error: {str(e)}")

    def get_active_tasks(self) -> str:
        """
        Fetches and formats active issues for the current viewer.
        
        Includes both assigned issues and all team issues (not just assigned to user).
        Filters out "Done" and "Canceled" states at the API level for efficiency.
        
        Returns:
            Formatted string with active tasks for LLM consumption
        """
        query = """
        query {
          viewer {
            name
            assignedIssues(
              filter: { 
                state: { 
                  name: { nin: ["Done", "Canceled"] } 
                } 
              }
            ) {
              nodes {
                identifier
                title
                description
                priorityLabel
                state {
                  name
                }
                team {
                  key
                  name
                }
              }
            }
            teams {
              nodes {
                key
                name
                issues(
                  filter: { 
                    state: { 
                      name: { nin: ["Done", "Canceled"] } 
                    } 
                  }
                ) {
                  nodes {
                    identifier
                    title
                    description
                    priorityLabel
                    state {
                      name
                    }
                    team {
                      key
                      name
                    }
                  }
                }
              }
            }
          }
        }
        """
        
        data = self._execute_query(query)
        viewer = data["data"]["viewer"]
        
        logger.debug(f"Fetching active tasks for user: {viewer.get('name', 'Unknown')}")
        
        # Collect all issues: start with assigned issues
        all_issues = {}
        assigned_issues = viewer.get("assignedIssues", {}).get("nodes", [])
        logger.debug(f"Found {len(assigned_issues)} assigned issues")
        
        for issue in assigned_issues:
            all_issues[issue["identifier"]] = issue
        
        # Add team issues (deduplicate by identifier)
        teams = viewer.get("teams", {}).get("nodes", [])
        logger.debug(f"Processing {len(teams)} teams")
        
        for team in teams:
            team_issues = team.get("issues", {}).get("nodes", [])
            for issue in team_issues:
                if issue["identifier"] not in all_issues:
                    all_issues[issue["identifier"]] = issue
        
        # Convert back to list
        issues = list(all_issues.values())
        logger.info(f"Retrieved {len(issues)} total active tasks (deduplicated)")
        
        if not issues:
            logger.info("No active tasks found")
            return f"User {viewer['name']} has no active tasks in their teams."

        # Format output for LLM consumption
        output = [f"📋 Linear Tasks for {viewer['name']}:", "=" * 40]
        
        for issue in issues:
            # Get team name if available
            team_name = ""
            if issue.get('team') and issue['team'].get('name'):
                team_name = f" ({issue['team']['name']})"
            
            # Truncate description for compact output
            desc = issue.get('description') or ""
            if desc:
                desc = desc[:100].replace("\n", " ")
                if len(issue.get('description', '')) > 100:
                    desc += "..."
                desc = f" | {desc}"
            
            output.append(
                f"📌 [{issue['identifier']}] {issue['title']}{team_name}\n"
                f"   • Status: {issue['state']['name']} | Priority: {issue['priorityLabel']}{desc}"
            )
        
        return "\n".join(output)

    def get_task_details(self, task_identifier: str) -> str:
        """
        Fetches full details for a specific task using its human identifier.

        This uses an indirection layer via the `issues` connection with a
        filter on `identifier` (e.g., "IDA-6") instead of relying on the
        `issue(identifier: ...)` field, which is not supported on all
        Linear API schemas.

        Args:
            task_identifier: Linear issue identifier (e.g., "IDA-8", "LIN-101").

        Returns:
            Formatted string with detailed task information and semantic guidance.
        """
        logger.info(f"Fetching task details for identifier: {task_identifier}")
        
        # Normalize identifier for robustness (Linear identifiers are typically uppercase)
        normalized_identifier = task_identifier.upper().strip()

        # Linear identifiers are typically of the form TEAMKEY-123 (e.g., "IDA-6").
        # The Linear GraphQL schema for IssueFilter does NOT support `identifier`,
        # but it DOES support filtering by `number` and `team.key`. We therefore:
        #   1) Parse the human identifier into (team_key, number)
        #   2) Filter issues by these fields.
        if "-" not in normalized_identifier:
            logger.warning(f"Invalid Linear task format: {task_identifier}")
            return (
                f"⚠️ Task '{task_identifier}' is not in a valid Linear format. "
                f"Expected something like 'IDA-6' (TEAMKEY-NUMBER)."
            )

        team_key, number_str = normalized_identifier.split("-", 1)
        try:
            issue_number = int(number_str)
        except ValueError:
            logger.warning(f"Invalid numeric part in task identifier: {task_identifier}")
            return (
                f"⚠️ Task '{task_identifier}' has an invalid numeric part. "
                f"Expected something like 'IDA-6' where '6' is a number."
            )
        
        logger.debug(f"Parsed task identifier: team_key={team_key}, number={issue_number}")

        # Single-query approach: filter issues by team key + number and return the first match
        query = """
        query($teamKey: String!, $number: Float!) {
          issues(
            filter: {
              number: { eq: $number }
              team: { key: { eq: $teamKey } }
            }
            first: 1
          ) {
            nodes {
              identifier
              title
              description
              priorityLabel
              state {
                name
              }
              labels {
                nodes {
                  name
                }
              }
              team {
                name
              }
            }
          }
        }
        """

        data = self._execute_query(
            query,
            {
                "teamKey": team_key,
                "number": issue_number,
            },
        )

        # Defensive extraction and validation to prevent AI retry loops
        issues = data.get("data", {}).get("issues", {}).get("nodes", [])
        if not issues:
            logger.warning(f"Task not found in Linear: {task_identifier}")
            return (
                f"⚠️ Task '{task_identifier}' not found in Linear. "
                f"Please verify the ID (e.g., 'IDA-6') and try again."
            )

        issue = issues[0]
        logger.info(f"Successfully retrieved task details for {task_identifier}: {issue.get('title', 'Untitled')}")

        desc = issue.get("description") or "No description provided."
        labels_nodes = issue.get("labels", {}).get("nodes", []) or []
        labels = [label.get("name", "") for label in labels_nodes if label.get("name")]
        team_name = issue.get("team", {}).get("name", "Unknown Team")

        # Format with semantic bridge to Notion search
        output = [
            f"🔍 DETAILS FOR {issue['identifier']}",
            f"Title: {issue['title']}",
            f"Team: {team_name}",
            f"Status: {issue['state']['name']} ({issue['priorityLabel']})",
            f"Labels: {', '.join(labels) if labels else 'None'}",
            f"\nDescription:\n{desc}",
            (
                "\n💡 SYSTEM NOTE: Use the title, labels, and keywords from the "
                "description above to search_notion for related technical "
                "specifications, architectural constraints, or implementation "
                "guidelines."
            ),
        ]

        return "\n".join(output)

