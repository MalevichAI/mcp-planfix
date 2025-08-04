"""Utility functions and helpers for the Planfix MCP server."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .config import config
from .models import Task, Project, Contact, Employee, Comment, File, Report, Process

# Configure logging
import logging
logger = logging.getLogger(__name__)


def format_task_list(tasks: List[Task]) -> str:
    """Format a list of tasks for display."""
    if not tasks:
        return "No tasks found."
    
    result = f"Found {len(tasks)} tasks:\n\n"
    
    for i, task in enumerate(tasks, 1):
        task_id = task.id or "N/A"
        name = task.name or "No name"
        status = task.status or "Unknown"
        assignee = task.assignee or "Unassigned"
        project = task.project or "No project"
        deadline = task.deadline
        
        result += f"{i}. Task #{task_id}: {name}\n"
        result += f"   Status: {status}\n"
        result += f"   Assignee: {assignee}\n"
        result += f"   Project: {project}\n"
        
        if deadline:
            result += f"   Deadline: {format_date(deadline)}\n"
        
        result += "\n"
    
    return result.strip()


def format_contact_list(contacts: List[Contact]) -> str:
    """Format a list of contacts for display."""
    if not contacts:
        return "No contacts found."
    
    result = f"Found {len(contacts)} contacts:\n\n"
    
    for i, contact in enumerate(contacts, 1):
        name = contact.name or "No name"
        midname = contact.midname or ""
        lastname = contact.lastname or ""
        full_name = f"{name} {midname} {lastname}".strip()
        
        result += f"{i}. Contact #{contact.id}: {full_name}\n"
        
        if contact.email:
            result += f"   Email: {contact.email}\n"
        if contact.phone:
            result += f"   Phone: {contact.phone}\n"
        if contact.company:
            result += f"   Company: {contact.company}\n"
        if contact.position:
            result += f"   Position: {contact.position}\n"
        
        result += "\n"
    
    return result.strip()


def format_employee_list(employees: List[Employee]) -> str:
    """Format a list of employees for display."""
    if not employees:
        return "No employees found."
    
    result = f"Found {len(employees)} employees:\n\n"
    
    for i, employee in enumerate(employees, 1):
        name = employee.name or "No name"
        result += f"{i}. Employee #{employee.id}: {name}\n"
        
        if employee.email:
            result += f"   Email: {employee.email}\n"
        if employee.position:
            result += f"   Position: {employee.position}\n"
        if employee.status:
            result += f"   Status: {employee.status}\n"
        if employee.last_activity:
            result += f"   Last activity: {format_date(employee.last_activity)}\n"
        
        result += "\n"
    
    return result.strip()


def format_comment_list(comments: List[Comment]) -> str:
    """Format a list of comments for display."""
    if not comments:
        return "No comments found."
    
    result = f"Found {len(comments)} comments:\n\n"
    
    for i, comment in enumerate(comments, 1):
        text = comment.text or "No text"
        result += f"{i}. Comment #{comment.id}\n"
        result += f"   Text: {text[:100]}{'...' if len(text) > 100 else ''}\n"
        
        if comment.author:
            result += f"   Author: {comment.author}\n"
        if comment.created_date:
            result += f"   Created: {format_date(comment.created_date)}\n"
        if comment.task_id:
            result += f"   Task: #{comment.task_id}\n"
        if comment.project_id:
            result += f"   Project: #{comment.project_id}\n"
        
        result += "\n"
    
    return result.strip()


def format_file_list(files: List[File]) -> str:
    """Format a list of files for display."""
    if not files:
        return "No files found."
    
    result = f"Found {len(files)} files:\n\n"
    
    for i, file in enumerate(files, 1):
        name = file.name or "No name"
        result += f"{i}. File #{file.id}: {name}\n"
        
        if file.size:
            size_mb = file.size / (1024 * 1024)
            result += f"   Size: {size_mb:.2f} MB\n"
        if file.author:
            result += f"   Author: {file.author}\n"
        if file.created_date:
            result += f"   Created: {format_date(file.created_date)}\n"
        if file.task_id:
            result += f"   Task: #{file.task_id}\n"
        if file.project_id:
            result += f"   Project: #{file.project_id}\n"
        
        result += "\n"
    
    return result.strip()


def format_report_list(reports: List[Report]) -> str:
    """Format a list of reports for display."""
    if not reports:
        return "No reports found."
    
    result = f"Found {len(reports)} reports:\n\n"
    
    for i, report in enumerate(reports, 1):
        name = report.name or "No name"
        result += f"{i}. Report #{report.id}: {name}\n"
        
        if report.description:
            result += f"   Description: {report.description[:100]}{'...' if len(report.description) > 100 else ''}\n"
        if report.created_date:
            result += f"   Created: {format_date(report.created_date)}\n"
        
        result += "\n"
    
    return result.strip()


def format_process_list(processes: List[Process]) -> str:
    """Format a list of processes for display."""
    if not processes:
        return "No processes found."
    
    result = f"Found {len(processes)} processes:\n\n"
    
    for i, process in enumerate(processes, 1):
        name = process.name or "No name"
        result += f"{i}. Process #{process.id}: {name}\n"
        
        if process.status:
            result += f"   Status: {process.status}\n"
        if process.description:
            result += f"   Description: {process.description[:100]}{'...' if len(process.description) > 100 else ''}\n"
        if process.created_date:
            result += f"   Created: {format_date(process.created_date)}\n"
        
        result += "\n"
    
    return result.strip()


def format_date(date_str: Optional[str]) -> str:
    """Format date string for display."""
    if not date_str:
        return "N/A"
    
    try:
        # Try to parse ISO format
        if 'T' in date_str:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M")
        
        # Try to parse date only
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return date_str


def format_error(error: Exception, context: str = "") -> str:
    """Format error message for display."""
    error_type = type(error).__name__
    error_msg = str(error)
    
    if context:
        return f"Error in {context}: {error_type}: {error_msg}"
    else:
        return f"Error: {error_type}: {error_msg}"


def log_api_call(method: str, endpoint: str, response_time: float = None) -> None:
    """Log API call for debugging."""
    if config.debug:
        if response_time:
            logger.debug(f"API call: {method} {endpoint} (took {response_time:.3f}s)")
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