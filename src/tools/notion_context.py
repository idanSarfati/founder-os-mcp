import sys
from typing import List, Optional, Dict, Any
import logging

# ✅ Defensive Import: מונע קריסה אם הספרייה חסרה
try:
    from notion_client import Client, APIResponseError
    NOTION_AVAILABLE = True
except ImportError:
    Client = None
    APIResponseError = None
    NOTION_AVAILABLE = False

# Import utilities with proper fallback handling
try:
    from config.auth_config import load_auth_config
except ImportError:
    try:
        from src.config.auth_config import load_auth_config
    except ImportError:
        load_auth_config = None

# Lazy-loaded health utilities with fallback
class _HealthProxy:
    """Proxy for health utilities with lazy loading."""
    def __init__(self):
        self._is_update_available = None
        self._get_update_notice = None

    def _load_functions(self):
        if self._is_update_available is None:
            try:
                from src.utils.health import is_update_available, get_update_notice
                self._is_update_available = is_update_available
                self._get_update_notice = get_update_notice
            except ImportError:
                try:
                    from utils.health import is_update_available, get_update_notice
                    self._is_update_available = is_update_available
                    self._get_update_notice = get_update_notice
                except ImportError:
                    self._is_update_available = lambda: False
                    self._get_update_notice = lambda: ""

    def is_update_available(self):
        self._load_functions()
        return self._is_update_available()

    def get_update_notice(self):
        self._load_functions()
        return self._get_update_notice()

_health_proxy = _HealthProxy()

try:
    from src.utils.logger import logger
except ImportError:
    try:
        from utils.logger import logger
    except ImportError:
        # Last resort fallback
        logger = logging.getLogger(__name__)

# Lazy initialization: Load config and client only when needed
# This allows validation to run before these are initialized
_config = None
_notion_client = None

def _get_notion_client():
    """Lazy initialization of Notion client with defensive handling."""
    global _config, _notion_client
    if _notion_client is None:
        if not NOTION_AVAILABLE:
            logger.warning("⚠️ Notion client not available. Using fallback mode.")
            _notion_client = None
        else:
            try:
                _config = load_auth_config()
                _notion_client = Client(auth=_config.notion_api_key)
            except Exception as e:
                logger.warning(f"Failed to create Notion client: {e}")
                _notion_client = None
    return _notion_client

# Create a module-level notion object that delegates to the lazy loader
class _NotionProxy:
    """Proxy object that lazily loads the Notion client."""
    def __getattr__(self, name):
        return getattr(_get_notion_client(), name)

notion = _NotionProxy()
# --- Helpers ---

def _extract_title_from_item(item: Dict[str, Any]) -> str:
    try:
        properties = item.get("properties", {})
        for prop_name, prop_value in properties.items():
            if prop_value.get("type") == "title":
                title_array = prop_value.get("title", [])
                if title_array: return "".join([t.get("plain_text", "") for t in title_array])
        if "title" in item:
            title_array = item.get("title", [])
            if title_array: return "".join([t.get("plain_text", "") for t in title_array])
    except Exception:
        pass
    return "Untitled"

def _extract_text_from_block(block: Dict[str, Any]) -> Optional[str]:
    block_type = block.get("type")
    prefixes = {"heading_1": "# ", "heading_2": "## ", "heading_3": "### ", "bulleted_list_item": "- ", "numbered_list_item": "1. ", "quote": "> ", "callout": "💡 ", "toggle": "> "}
    
    content_obj = block.get(block_type, {})
    rich_text = content_obj.get("rich_text", [])
    plain_text = "".join([t.get("plain_text", "") for t in rich_text]) if rich_text else ""

    if block_type == "to_do":
        checked = content_obj.get("checked", False)
        return f"[x] {plain_text}" if checked else f"[ ] {plain_text}"
    if block_type in prefixes:
        return f"{prefixes[block_type]}{plain_text}"
    if block_type == "paragraph":
        return plain_text
    return None

def _fetch_all_blocks(block_id: str, depth: int = 0) -> List[str]:
    if depth > 3: return []
    lines = []
    try:
        response = notion.blocks.children.list(block_id=block_id)
        for block in response.get("results", []):
            text = _extract_text_from_block(block)
            if text: lines.append(("  " * depth) + text)
            if block.get("has_children", False):
                lines.extend(_fetch_all_blocks(block["id"], depth + 1))
    except APIResponseError:
        pass
    return lines

# --- Tools ---

def search_notion(query: str) -> str:
    """Enhanced search with automatic keyword simplification fallback."""
    if not NOTION_AVAILABLE or _get_notion_client() is None:
        logger.warning("⚠️ Notion client not available. Skipping Notion search.")
        return "- [page] No Notion search available (client not installed)"

    try:
        logger.info(f"Received request for tool: search_notion. Query: {query}")

        # 1. Try the full query first
        logger.debug(f"Search attempt 1 with '{query}'")
        response = notion.search(query=query, page_size=5)
        items = response.get("results", [])

        # 2. If it fails, take the FIRST WORD only (The "Aggressive" Fallback)
        if not items and " " in query:
            simple_query = query.split(" ")[0]
            logger.debug(f"Search attempt 2 with '{simple_query}' (fallback)")
            response = notion.search(query=simple_query, page_size=10)
            items = response.get("results", [])

        # 3. If still nothing, get the 10 most recent pages (The "Nuclear" Fallback)
        if not items:
            logger.debug("Final fallback - fetching recent pages")
            response = notion.search(query="", sort={"direction": "descending", "timestamp": "last_edited_time"}, page_size=10)
            items = response.get("results", [])

        results = []
        for item in items:
            title = _extract_title_from_item(item)
            results.append(f"- [{item.get('object')}] {title} (ID: {item.get('id')})")
        
        logger.info(f"Found {len(results)} documents matching query")
        
        response_text = "I couldn't find an exact match, but here are the most relevant pages:\n" + "\n".join(results)
        
        # Inject update notice if available
        if _health_proxy.is_update_available():
            logger.debug("Injecting update notice into search response")
            notice = _health_proxy.get_update_notice()
            response_text = notice + response_text
            logger.debug(f"Notice injected, response length: {len(response_text)} chars")
            
        logger.info(f"search_notion completed successfully. Response length: {len(response_text)} chars")
        return response_text
    except Exception as e:
        logger.exception("Failed to search Notion")
        error_msg = f"Search Error: {str(e)}"
        if _health_proxy.is_update_available():
            error_msg = _health_proxy.get_update_notice() + error_msg
        return error_msg

def fetch_project_context(page_id: str) -> str:
    """Recursively fetches title and content from a Notion page."""
    if not page_id:
        logger.warning("fetch_project_context called without page_id")
        error_msg = "Error: page_id required."
        if _health_proxy.is_update_available():
            error_msg = _health_proxy.get_update_notice() + error_msg
        return error_msg
    
    try:
        logger.info(f"Received request for tool: fetch_project_context. Page ID: {page_id}")
        
        page = notion.pages.retrieve(page_id=page_id)
        title = _extract_title_from_item(page)
        logger.info(f"Fetched Notion Spec: {title}")
        
        content = _fetch_all_blocks(page_id)
        content_length = sum(len(line) for line in content)
        logger.info(f"Fetched content length: {content_length} chars, {len(content)} blocks")
        
        response_text = f"Title: {title}\n\n" + "\n".join(content)
        
        # Inject update notice if available
        if _health_proxy.is_update_available():
            logger.debug("Injecting update notice into fetch response")
            response_text = _health_proxy.get_update_notice() + response_text
        
        logger.info(f"fetch_project_context completed successfully. Response length: {len(response_text)} chars")
        return response_text
    except Exception as e:
        logger.exception(f"Failed to fetch project context for page {page_id}")
        error_msg = f"Error: {str(e)}"
        if _health_proxy.is_update_available():
            error_msg = _health_proxy.get_update_notice() + error_msg
        return error_msg

def append_to_page(page_id: str, content: str) -> str:
    """Appends a new paragraph block to a Notion page."""
    if not page_id or not content:
        logger.warning("append_to_page called without page_id or content")
        return "Error: page_id and content required."
    try:
        logger.info(f"Received request for tool: append_to_page. Page ID: {page_id}, Content length: {len(content)} chars")
        
        notion.blocks.children.append(
            block_id=page_id,
            children=[{"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": content}}]}}]
        )
        
        logger.info("append_to_page completed successfully")
        return "Success."
    except Exception as e:
        logger.exception(f"Failed to append to page {page_id}")
        return f"Error: {str(e)}"