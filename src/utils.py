"""Utility functions for Planfix MCP Server."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from .config import config

# Configure logging
logger = logging.getLogger(__name__)

if config.debug:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)


def format_task_list(tasks: List[Any]) -> str:
    """Format a list of tasks for display."""
    if not tasks:
        return "Задачи не найдены."
    
    result = f"📋 Найдено задач: {len(tasks)}\n\n"
    
    for i, task in enumerate(tasks, 1):
        # Handle both dict and Task object formats
        if hasattr(task, 'id'):
            # Task object
            task_id = task.id or "N/A"
            name = task.name or "Без названия"
            status = task.status or "Неизвестно"
            assignee = task.assignee or "Не назначен"
            project = task.project or "Без проекта"
            deadline = task.deadline
        else:
            # Dict format
            task_id = task.get("id", "N/A")
            name = task.get("name", "Без названия")
            status = task.get("status", "Неизвестно")
            assignee = task.get("assignee", "Не назначен")
            project = task.get("project", "Без проекта")
            deadline = task.get("deadline")
        
        result += f"{i}. 📌 **{name}** (#{task_id})\n"
        result += f"   └─ Статус: {status}\n"
        result += f"   └─ Исполнитель: {assignee}\n"
        result += f"   └─ Проект: {project}\n"
        
        if deadline:
            result += f"   └─ ⏰ Срок: {format_date(deadline)}\n"
        
        result += "\n"
    
    return result.strip()


def format_date(date_str: Optional[str]) -> str:
    """Format date string for display."""
    if not date_str:
        return "Не указано"
    
    try:
        # Try to parse ISO format
        if "T" in date_str:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.strftime("%d.%m.%Y %H:%M")
        else:
            # Assume date only
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.strftime("%d.%m.%Y")
    except (ValueError, TypeError):
        return date_str


def format_project_list(projects: List[Any]) -> str:
    """Format a list of projects for display."""
    if not projects:
        return "Проекты не найдены."
    
    result = f"🎯 Найдено проектов: {len(projects)}\n\n"
    
    for i, project in enumerate(projects, 1):
        # Handle both dict and Project object formats
        if hasattr(project, 'id'):
            # Project object
            project_id = project.id or "N/A"
            name = project.name or "Без названия"
            status = project.status or "Активный"
            task_count = project.task_count or 0
            owner = project.owner or "Не назначен"
        else:
            # Dict format
            project_id = project.get("id", "N/A")
            name = project.get("name", "Без названия")
            status = project.get("status", "Активный")
            task_count = project.get("taskCount", 0)
            owner = project.get("owner", "Не назначен")
        
        result += f"{i}. 🎯 **{name}** (#{project_id})\n"
        result += f"   └─ Статус: {status}\n"
        result += f"   └─ Задач: {task_count}\n"
        result += f"   └─ Владелец: {owner}\n\n"
    
    return result.strip()


def format_analytics_report(report_data: Dict[str, Any]) -> str:
    """Format analytics report for display."""
    report_type = report_data.get("report_type", "Отчёт")
    period = report_data.get("period", "")
    data = report_data.get("data", [])
    summary = report_data.get("summary", {})
    
    result = f"📊 **{report_type.upper()}** за период {period}\n\n"
    
    # Summary section
    if summary:
        result += "📈 **ИТОГО:**\n"
        for key, value in summary.items():
            result += f"   └─ {key}: {value}\n"
        result += "\n"
    
    # Detailed data
    if data:
        result += "📋 **ДЕТАЛИ:**\n"
        for i, item in enumerate(data, 1):
            name = item.get("name", f"Элемент {i}")
            value = item.get("value", "N/A")
            result += f"{i}. {name}: {value}\n"
    
    return result.strip()


def validate_priority(priority: str) -> str:
    """Validate and normalize task priority."""
    valid_priorities = ["LOW", "NORMAL", "HIGH", "CRITICAL"]
    priority_upper = priority.upper()
    
    if priority_upper not in valid_priorities:
        logger.warning(f"Invalid priority '{priority}', using NORMAL")
        return "NORMAL"
    
    return priority_upper


def validate_status(status: str) -> str:
    """Validate and normalize task status."""
    valid_statuses = ["NEW", "IN_WORK", "COMPLETED", "REJECTED", "PAUSED"]
    status_upper = status.upper()
    
    if status_upper not in valid_statuses:
        logger.warning(f"Invalid status '{status}', available: {valid_statuses}")
        return status_upper  # Return as-is for custom statuses
    
    return status_upper


def safe_get(data: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Safely get nested dictionary value."""
    for key in keys:
        if isinstance(data, dict) and key in data:
            data = data[key]
        else:
            return default
    return data


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def format_error(error: Exception, context: str = "") -> str:
    """Format error message for user display."""
    error_msg = str(error)
    
    if "401" in error_msg or "unauthorized" in error_msg.lower():
        return "❌ Ошибка авторизации. Проверьте API ключи Planfix."
    elif "403" in error_msg or "forbidden" in error_msg.lower():
        return "❌ Доступ запрещён. Недостаточно прав для выполнения операции."
    elif "404" in error_msg or "not found" in error_msg.lower():
        return "❌ Объект не найден. Проверьте ID и попробуйте снова."
    elif "timeout" in error_msg.lower():
        return "❌ Превышено время ожидания. Попробуйте позже."
    elif "connection" in error_msg.lower():
        return "❌ Ошибка соединения с Planfix. Проверьте интернет-подключение."
    
    # Generic error with context
    if context:
        return f"❌ Ошибка при {context}: {error_msg}"
    
    return f"❌ Произошла ошибка: {error_msg}"


def log_api_call(method: str, endpoint: str, status_code: Optional[int] = None) -> None:
    """Log API call for debugging."""
    if config.debug:
        logger.debug(f"API Call: {method} {endpoint} -> {status_code or 'Unknown'}")