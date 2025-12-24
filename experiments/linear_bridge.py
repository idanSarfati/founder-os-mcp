import os
import requests
import json
import sys
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
LINEAR_API_KEY: Optional[str] = os.getenv("LINEAR_API_KEY")
ENDPOINT: str = "https://api.linear.app/graphql"


def fetch_my_issues() -> Optional[Dict[str, Any]]:
    """
    Fetches active issues from user's assigned issues AND team issues.
    
    Why: We filter at the API level (Graphql) to reduce data over the wire 
    and avoid O(n) filtering in Python[cite: 8, 9].
    Includes both assigned issues and all team issues (not just assigned to user).
    """
    # Security Check: Early return if key is missing [cite: 5, 59]
    if not LINEAR_API_KEY:
        print("❌ Error: LINEAR_API_KEY not found in .env. Please add it to run this POC.")
        sys.exit(1)

    headers = {
        "Content-Type": "application/json",
        "Authorization": LINEAR_API_KEY
    }

    # Query: Viewer -> Assigned Issues + Team Issues
    # Optimization: Filter out "Done" AND "Canceled" at the source using 'nin' (Not In)
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

    try:
        response = requests.post(ENDPOINT, json={"query": query}, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        # Basic validation to ensure we didn't get a 200 OK with a GraphQL error
        if "errors" in data:
            print(f"❌ GraphQL Error: {data['errors']}")
            return None
            
        return data

    except requests.exceptions.RequestException as e:
        # Operational Error handling [cite: 40]
        print(f"❌ API Request Failed: {e}")
        return None


def _format_for_llm(data: Dict[str, Any]) -> str:
    """
    Parses raw GraphQL response into a high-density context string for AI.
    
    Why: LLMs require concise context. We strip unnecessary JSON syntax 
    and handle null values gracefully[cite: 13].
    Merges assigned issues and team issues, deduplicating by identifier.
    """
    # Edge Case: Handle null/empty data [cite: 13, 14]
    if not data or "data" not in data or not data["data"]["viewer"]:
        return "No data available or invalid response structure."

    viewer = data["data"]["viewer"]
    
    # Collect all issues: start with assigned issues
    all_issues = {}
    assigned_issues = viewer.get("assignedIssues", {}).get("nodes", [])
    for issue in assigned_issues:
        all_issues[issue["identifier"]] = issue
    
    # Add team issues (will overwrite duplicates with same identifier, keeping team context)
    teams = viewer.get("teams", {}).get("nodes", [])
    for team in teams:
        team_issues = team.get("issues", {}).get("nodes", [])
        for issue in team_issues:
            # Only add if not already present (or update with team info)
            if issue["identifier"] not in all_issues:
                all_issues[issue["identifier"]] = issue
    
    # Convert back to list
    issues = list(all_issues.values())
    
    if not issues:
        return f"User {viewer['name']} has no active issues in their teams."

    # Header
    formatted_output = f"📋 Active Tasks for {viewer['name']}:\n"
    formatted_output += "=" * 40 + "\n"

    for issue in issues:
        # Edge Case: Description might be None (null) or empty string 
        raw_desc = issue.get('description') or "No description provided."
        
        # Sanitize: Truncate and remove newlines for token density
        clean_desc = raw_desc[:200].replace("\n", " ")
        if len(raw_desc) > 200:
            clean_desc += "..."

        # Get team name if available
        team_name = ""
        if issue.get('team') and issue['team'].get('name'):
            team_name = f" ({issue['team']['name']})"

        # Format: High density block
        formatted_output += f"📌 [{issue['identifier']}] {issue['title']}{team_name}\n"
        formatted_output += f"   • Status: {issue['state']['name']}\n"
        formatted_output += f"   • Priority: {issue['priorityLabel']}\n"
        formatted_output += f"   • Context: {clean_desc}\n"
        formatted_output += "-" * 40 + "\n"
        
    return formatted_output


if __name__ == "__main__":
    print("🚀 Starting Linear Bridge POC...")
    
    # 1. Fetch
    raw_data = fetch_my_issues()
    
    # 2. Process & Output
    if raw_data:
        print("\n🔍 [DEBUG] Raw JSON Response (Partial):")
        # Careful not to dump huge data in production logs, keeping it minimal here
        try:
            viewer = raw_data['data']['viewer']
            assigned_count = len(viewer.get('assignedIssues', {}).get('nodes', []))
            
            # Count team issues
            team_issues_count = 0
            for team in viewer.get('teams', {}).get('nodes', []):
                team_issues_count += len(team.get('issues', {}).get('nodes', []))
            
            # Deduplicate count (simple estimate)
            print(f"Found {assigned_count} assigned issues and {team_issues_count} team issues.")
        except KeyError:
            print("Invalid structure received.")

        print("\n🤖 [AI CONTEXT] Formatted Output:")
        ai_context = _format_for_llm(raw_data)
        print(ai_context)

