"""
Environment validation utilities for pre-flight API key checks.

This module provides validation functions to ensure API keys are valid
before the server starts accepting requests, preventing cryptic errors
deep in the application logic.
"""

import os
import requests
from typing import Tuple
from dotenv import load_dotenv
from notion_client import Client, APIResponseError
from config.auth_config import load_auth_config
from src.utils.logger import logger


def validate_environment() -> Tuple[bool, str]:
    """
    Validates API connectivity for Notion and Linear before server startup.
    
    Performs minimal API requests to verify that API keys are valid and
    the services are reachable. Uses short timeouts to prevent hanging
    if the system is offline.
    
    Returns:
        Tuple of (is_valid: bool, error_message: str)
        - Success: (True, "")
        - Failure: (False, "Human readable error message")
    """
    errors = []
    
    # Validate Notion API
    logger.debug("Validating Notion API connectivity...")
    try:
        # Check if .env file exists first
        import os.path
        env_exists = os.path.exists(".env")
        
        config = load_auth_config()
        notion = Client(auth=config.notion_api_key)
        
        # Minimal request: get current user info
        # This is lightweight and validates the API key
        notion.users.me()
        logger.debug("Notion API validation successful")
    except ValueError as e:
        # This means NOTION_API_KEY is missing from .env
        import os.path
        if not os.path.exists(".env"):
            logger.error("Notion API validation failed: .env file is missing")
            errors.append(
                "❌ Error: .env file is missing.\n"
                "   Please create a .env file in the project root with:\n"
                "   NOTION_API_KEY=your_notion_api_key_here\n\n"
                "   Run 'python install_script.py' to set up your environment, or\n"
                "   create .env manually with your Notion API key."
            )
        else:
            logger.error("Notion API validation failed: NOTION_API_KEY missing from .env")
            errors.append(
                "❌ Error: NOTION_API_KEY is missing from .env file.\n"
                "   Please add: NOTION_API_KEY=your_notion_api_key_here\n"
                "   to your .env file in the project root."
            )
    except APIResponseError as e:
        # API key is present but invalid or unauthorized
        logger.error(f"Notion API validation failed: APIResponseError - {str(e)}")
        errors.append(
            "❌ Error: Unable to connect to Notion. Please check if your 'NOTION_API_KEY' in the .env file is correct."
        )
    except requests.exceptions.RequestException as e:
        # Network/connection error
        logger.error(f"Notion API validation failed: RequestException - {str(e)}")
        errors.append(
            "❌ Error: Unable to connect to Notion. Please check if your 'NOTION_API_KEY' in the .env file is correct."
        )
    except Exception as e:
        # Catch-all for any other errors
        logger.exception("Notion API validation failed with unexpected error")
        errors.append(
            "❌ Error: Unable to connect to Notion. Please check if your 'NOTION_API_KEY' in the .env file is correct."
        )
    
    # Validate Linear API (optional - only if key is present)
    # Ensure .env is loaded (load_auth_config() already does this, but be explicit)
    load_dotenv()
    linear_api_key = os.getenv("LINEAR_API_KEY")
    if linear_api_key:
        logger.debug("Validating Linear API connectivity...")
        try:
            # Minimal GraphQL query: just get viewer id
            # This validates the API key without fetching large amounts of data
            query = """
            query {
              viewer {
                id
              }
            }
            """
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": linear_api_key
            }
            
            response = requests.post(
                "https://api.linear.app/graphql",
                json={"query": query},
                headers=headers,
                timeout=5  # Short timeout to fail fast
            )
            
            # Check for HTTP errors
            if not response.ok:
                logger.error(f"Linear API validation failed: HTTP {response.status_code}")
                errors.append(
                    "❌ Error: Unable to connect to Linear. Please check your 'LINEAR_API_KEY'."
                )
            else:
                # Check for GraphQL errors
                data = response.json()
                if "errors" in data:
                    logger.error(f"Linear API validation failed: GraphQL errors - {data['errors']}")
                    errors.append(
                        "❌ Error: Unable to connect to Linear. Please check your 'LINEAR_API_KEY'."
                    )
                else:
                    logger.debug("Linear API validation successful")
        except requests.exceptions.Timeout:
            logger.error("Linear API validation failed: Request timeout")
            errors.append(
                "❌ Error: Unable to connect to Linear. Please check your 'LINEAR_API_KEY'."
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Linear API validation failed: RequestException - {str(e)}")
            errors.append(
                "❌ Error: Unable to connect to Linear. Please check your 'LINEAR_API_KEY'."
            )
        except Exception as e:
            # Catch-all for any other errors
            logger.exception("Linear API validation failed with unexpected error")
            errors.append(
                "❌ Error: Unable to connect to Linear. Please check your 'LINEAR_API_KEY'."
            )
    else:
        logger.debug("Linear API key not found, skipping Linear validation")
    
    # Return results
    if errors:
        error_message = "\n".join(errors)
        logger.error("Environment validation failed")
        return (False, error_message)
    else:
        logger.info("Environment validation successful")
        return (True, "")

