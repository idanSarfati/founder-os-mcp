import subprocess
import sys
import logging

# Basic logger setup in case Cursor misses direct prints
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("founder-os-health")

def check_for_updates():
    """
    Checks if the local git repository is behind origin/main.
    Returns True if an update is available, False otherwise.
    """
    try:
        # 1. Fetch latest data from remote (silently)
        subprocess.run(
            ["git", "fetch"], 
            check=True, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )

        # 2. Count how many commits we are behind
        output = subprocess.check_output(
            ["git", "rev-list", "--count", "HEAD..origin/main"], 
            text=True
        )
        
        commits_behind = int(output.strip())
        return commits_behind > 0

    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        return False

def print_update_banner():
    """Prints a high-visibility ASCII banner to STDERR with Force Flush."""
    script_name = "update.bat" if sys.platform == "win32" else "./update.sh"
    
    green = "\033[92m"
    reset = "\033[0m"
    
    # Method 1: Official log (will definitely appear in Cursor's Output)
    logger.warning(f"🚀 NEW VERSION AVAILABLE! Please run {script_name}")
    
    # Method 2: Visual banner with flush=True (to prevent buffer blocking)
    msg = [
        f"\n{green}",
        "╔══════════════════════════════════════════════════════════╗",
        "║                                                          ║",
        "║   🚀  NEW VERSION AVAILABLE                              ║",
        "║                                                          ║",
        f"║   Run: {script_name.ljust(46)}║",
        "║   to get the latest features & fixes.                    ║",
        "║                                                          ║",
        "╚══════════════════════════════════════════════════════════╝",
        f"{reset}\n"
    ]
    
    # Print and immediate flush
    for line in msg:
        print(line, file=sys.stderr, flush=True)
