"""Utility functions and helpers for the Planfix MCP server."""

from datetime import datetime
from typing import Any, Dict, Optional

from .config import config

# Configure logging
import logging
logger = logging.getLogger(__name__)


def format_date(date_input: Optional[Any]) -> str:
    """Format date string or TimePoint object for display."""
    if not date_input:
        return "N/A"
    
    # Handle string input
    if isinstance(date_input, str):
        try:
            # Try to parse ISO format
            if 'T' in date_input:
                dt = datetime.fromisoformat(date_input.replace('Z', '+00:00'))
                return dt.strftime("%Y-%m-%d %H:%M")
            
            # Try to parse date only
            dt = datetime.strptime(date_input, "%Y-%m-%d")
            return dt.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            return date_input
    
    # Handle TimePoint object from new models
    if hasattr(date_input, 'datetime') and date_input.datetime:
        return format_date(date_input.datetime)
    elif hasattr(date_input, 'date') and date_input.date:
        return format_date(date_input.date)
    
    return str(date_input)


def format_error(error: Exception, context: str = "") -> str:
    """Format error message for display."""
    error_type = type(error).__name__
    error_msg = str(error)
    
    if context:
        return f"Error in {context}: {error_type}: {error_msg}"
    else:
        return f"Error: {error_type}: {error_msg}"


def log_api_call(method: str, endpoint: str, response_code: Optional[int] = None) -> None:
    """Log API call for debugging."""
    if config.debug:
        if response_code:
            logger.debug(f"API call: {method} {endpoint} -> {response_code}")
        else:
            logger.debug(f"API call: {method} {endpoint}")


def safe_get(data: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Safely get nested values from a dictionary."""
    current: Any = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current