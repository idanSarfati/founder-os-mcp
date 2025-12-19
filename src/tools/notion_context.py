import sys
from typing import List, Optional, Dict, Any
from notion_client import Client, APIResponseError
from config.auth_config import load_auth_config

# Load credentials once
config = load_auth_config()

# 🔴 OLD (Bug): notion = Client(auth=config["NOTION_API_KEY"])
# 🟢 NEW (Fix): Use dot notation
notion = Client(auth=config.notion_api_key)
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
    """Searches Notion. Auto-falls back to recent pages if no exact match."""
    print(f"DEBUG: Searching for '{query}'", file=sys.stderr)
    try:
        # 1. Primary Search
        response = notion.search(
            query=query, page_size=10, 
            sort={"direction": "descending", "timestamp": "last_edited_time"}
        )
        items = response.get("results", [])

        # 2. Fallback
        fallback_msg = ""
        if not items and query.strip().upper() != "ALL":
            fallback_msg = f"No exact matches for '{query}'. Showing most recent pages:\n"
            response = notion.search(query="", page_size=20, sort={"direction": "descending", "timestamp": "last_edited_time"})
            items = response.get("results", [])

        results = []
        for item in items:
            title = _extract_title_from_item(item)
            results.append(f"- [{item.get('object')}] {title} (ID: {item.get('id')})")
            
        if not results: return "No pages found."
        return (fallback_msg or f"Found {len(results)} matches:\n") + "\n".join(results)
    except Exception as e:
        return f"Search Error: {str(e)}"

def fetch_project_context(page_id: str) -> str:
    """Recursively fetches title and content from a Notion page."""
    if not page_id: return "Error: page_id required."
    try:
        page = notion.pages.retrieve(page_id=page_id)
        title = _extract_title_from_item(page)
        content = _fetch_all_blocks(page_id)
        return f"Title: {title}\n\n" + "\n".join(content)
    except Exception as e:
        return f"Error: {str(e)}"

def append_to_page(page_id: str, content: str) -> str:
    """Appends a new paragraph block to a Notion page."""
    if not page_id or not content: return "Error: page_id and content required."
    try:
        notion.blocks.children.append(
            block_id=page_id,
            children=[{"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": content}}]}}]
        )
        return "Success."
    except Exception as e:
        return f"Error: {str(e)}"