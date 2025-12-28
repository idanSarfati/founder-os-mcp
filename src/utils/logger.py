"""
Flight Recorder: Centralized logging system for Founder OS MCP Server.

This module provides a configured logger that writes to both:
1. File: founder_os.log (in project root) - for persistent debugging
2. Console: stdout - for real-time visibility

Privacy Rules:
- DO NOT log full API keys or tokens
- DO NOT log full content of user documents (log metadata only)
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def _sanitize_message(message: str) -> str:
    """
    Sanitize log messages to prevent accidental logging of sensitive data.
    
    Removes or masks API keys, tokens, and other sensitive information.
    """
    import re
    
    sanitized = message
    
    # Pattern 1: Mask API keys in environment variable format (NOTION_API_KEY=secret123)
    sanitized = re.sub(
        r'(NOTION_API_KEY|LINEAR_API_KEY)=([^\s]+)',
        r'\1=***',
        sanitized
    )
    
    # Pattern 2: Mask Authorization headers (Authorization: Bearer token123 or Authorization: token123)
    sanitized = re.sub(
        r'Authorization:\s*(Bearer\s+)?([^\s]+)',
        r'Authorization: ***',
        sanitized
    )
    
    # Pattern 3: Mask any remaining Bearer tokens
    sanitized = re.sub(
        r'Bearer\s+([^\s]+)',
        r'Bearer ***',
        sanitized
    )
    
    return sanitized


def setup_logger(name: str = "founder-os") -> logging.Logger:
    """
    Configure and return a logger instance for Founder OS.
    
    Args:
        name: Logger name (default: "founder-os")
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Prevent duplicate handlers if logger is already configured
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Format: [YYYY-MM-DD HH:MM:SS] [LEVEL] Message
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler 1: File output (founder_os.log in project root)
    # Get project root (where server.py is located)
    project_root = Path(__file__).parent.parent.parent
    log_file = project_root / "founder_os.log"
    
    # Rotating file handler: max 5MB per file, keep 3 backup files
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    # Handler 2: Console output (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# Create module-level logger instance
logger = setup_logger()

# Override logger methods to sanitize messages
_original_info = logger.info
_original_error = logger.error
_original_warning = logger.warning
_original_debug = logger.debug
_original_exception = logger.exception


def _wrap_log_method(original_method):
    """Wrapper to sanitize log messages before logging."""
    def wrapper(message, *args, **kwargs):
        if isinstance(message, str):
            message = _sanitize_message(message)
        return original_method(message, *args, **kwargs)
    return wrapper


logger.info = _wrap_log_method(_original_info)
logger.error = _wrap_log_method(_original_error)
logger.warning = _wrap_log_method(_original_warning)
logger.debug = _wrap_log_method(_original_debug)
logger.exception = lambda msg, *args, **kwargs: _original_exception(_sanitize_message(msg) if isinstance(msg, str) else msg, *args, **kwargs)

