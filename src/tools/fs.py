import os
from mcp.server.fastmcp import FastMCP
from src.utils.health import is_update_available, get_update_notice
from src.utils.logger import logger

# Note: We don't need the mcp object here, just the function logic
# unless we use decorators differently. For this pattern, we define functions
# and register them in server.py

def list_directory(root_path: str = ".", max_depth: int = 3) -> str:
    """Lists file structure, ignoring noise."""
    try:
        logger.info(f"Received request for tool: list_directory. Root path: {root_path}, Max depth: {max_depth}")
        
        IGNORE_LIST = {'node_modules', '.git', '__pycache__', 'venv', '.venv', 'env', '.DS_Store', 'dist', 'build', 'target', '.idea', '.vscode', '__pycache__'}
        output = []
        abs_root = os.path.abspath(root_path)
        
        if not os.path.exists(abs_root):
            logger.warning(f"Path does not exist: {abs_root}")
            error_msg = "Error: Path does not exist."
            if is_update_available():
                error_msg = get_update_notice() + error_msg
            return error_msg

        def walk(directory: str, prefix: str = "", current_depth: int = 0):
            if current_depth >= max_depth:
                output.append(f"{prefix}└── ... (max depth {max_depth} reached)")
                return
            try:
                entries = sorted([e for e in os.listdir(directory) if e not in IGNORE_LIST])
                for i, entry in enumerate(entries):
                    is_last = (i == len(entries) - 1)
                    connector = "└── " if is_last else "├── "
                    output.append(f"{prefix}{connector}{entry}")
                    if os.path.isdir(os.path.join(directory, entry)):
                        walk(os.path.join(directory, entry), prefix + ("    " if is_last else "│   "), current_depth + 1)
            except Exception as e:
                logger.debug(f"Access denied for directory: {directory}")
                output.append(f"{prefix}└── ⚠️ [Access Denied]")

        walk(abs_root)
        response_text = "\n".join(output)
        
        logger.info(f"Listed {len(output)} entries from directory structure")
        
        # Inject update notice if available
        if is_update_available():
            logger.debug("Injecting update notice into list_directory response")
            response_text = get_update_notice() + response_text
        
        logger.info(f"list_directory completed successfully. Response length: {len(response_text)} chars")
        return response_text
    except Exception as e:
        logger.exception(f"Failed to list directory: {root_path}")
        error_msg = f"Error: {str(e)}"
        if is_update_available():
            error_msg = get_update_notice() + error_msg
        return error_msg