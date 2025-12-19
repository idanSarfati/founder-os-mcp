import os
from mcp.server.fastmcp import FastMCP

# Note: We don't need the mcp object here, just the function logic
# unless we use decorators differently. For this pattern, we define functions
# and register them in server.py

def list_directory(root_path: str = ".", max_depth: int = 3) -> str:
    """Lists file structure, ignoring noise."""
    IGNORE_LIST = {'node_modules', '.git', '__pycache__', 'venv', '.venv', 'env', '.DS_Store', 'dist', 'build', 'target', '.idea', '.vscode', '__pycache__'}
    output = []
    abs_root = os.path.abspath(root_path)
    if not os.path.exists(abs_root): return "Error: Path does not exist."

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
        except Exception:
            output.append(f"{prefix}└── ⚠️ [Access Denied]")

    walk(abs_root)
    return "\n".join(output)