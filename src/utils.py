"""Utility functions for Planfix MCP Server."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .config import config
from .models import Task, Project, Contact, Employee, Comment, File, Report, Process

# Configure logging
logger = logging.getLogger(__name__)

if config.debug:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)


def format_task_list(tasks: List[Task]) -> str:
    """Format a list of tasks for display."""
    if not tasks:
        return "Задачи не найдены."
    
    result = f"📋 Найдено задач: {len(tasks)}\n\n"
    
    for i, task in enumerate(tasks, 1):
        # Task object
        task_id = task.id or "N/A"
        name = task.name or "Без названия"
        status = task.status or "Неизвестно"
        assignee = task.assignee or "Не назначен"
        project = task.project or "Без проекта"
        deadline = task.deadline
        
        result += f"{i}. 📌 **{name}** (#{task_id})\n"
        result += f"   └─ Статус: {status}\n"
        result += f"   └─ Исполнитель: {assignee}\n"
        result += f"   └─ Проект: {project}\n"
        
        if deadline:
            result += f"   └─ ⏰ Срок: {format_date(deadline)}\n"
        
        result += "\n"
    
    return result.strip()


def format_contact_list(contacts: List[Contact]) -> str:
    """Format a list of contacts for display."""
    if not contacts:
        return "Контакты не найдены."
    
    result = f"👥 Найдено контактов: {len(contacts)}\n\n"
    
    for i, contact in enumerate(contacts, 1):
        name = contact.name or "Без имени"
        midname = contact.midname or ""
        lastname = contact.lastname or ""
        full_name = f"{name} {midname} {lastname}".strip()
        
        result += f"{i}. 👤 **{full_name}** (#{contact.id})\n"
        
        if contact.email:
            result += f"   └─ 📧 {contact.email}\n"
        if contact.phone:
            result += f"   └─ 📞 {contact.phone}\n"
        if contact.company:
            result += f"   └─ 🏢 {contact.company}\n"
        if contact.position:
            result += f"   └─ 💼 {contact.position}\n"
        
        result += "\n"
    
    return result.strip()


def format_employee_list(employees: List[Employee]) -> str:
    """Format a list of employees for display."""
    if not employees:
        return "Сотрудники не найдены."
    
    result = f"👨‍💼 Найдено сотрудников: {len(employees)}\n\n"
    
    for i, employee in enumerate(employees, 1):
        name = employee.name or "Без имени"
        result += f"{i}. 👨‍💼 **{name}** (#{employee.id})\n"
        
        if employee.email:
            result += f"   └─ 📧 {employee.email}\n"
        if employee.position:
            result += f"   └─ 💼 {employee.position}\n"
        if employee.status:
            result += f"   └─ 🔄 {employee.status}\n"
        if employee.last_activity:
            result += f"   └─ ⏰ Последняя активность: {format_date(employee.last_activity)}\n"
        
        result += "\n"
    
    return result.strip()


def format_comment_list(comments: List[Comment]) -> str:
    """Format a list of comments for display."""
    if not comments:
        return "Комментарии не найдены."
    
    result = f"💬 Найдено комментариев: {len(comments)}\n\n"
    
    for i, comment in enumerate(comments, 1):
        text = comment.text or "Без текста"
        result += f"{i}. 💬 **Комментарий #{comment.id}**\n"
        result += f"   └─ 📝 {text[:100]}{'...' if len(text) > 100 else ''}\n"
        
        if comment.author:
            result += f"   └─ 👤 Автор: {comment.author}\n"
        if comment.created_date:
            result += f"   └─ 📅 Создан: {format_date(comment.created_date)}\n"
        if comment.task_id:
            result += f"   └─ 📋 Задача: #{comment.task_id}\n"
        if comment.project_id:
            result += f"   └─ 🎯 Проект: #{comment.project_id}\n"
        
        result += "\n"
    
    return result.strip()


def format_file_list(files: List[File]) -> str:
    """Format a list of files for display."""
    if not files:
        return "Файлы не найдены."
    
    result = f"📁 Найдено файлов: {len(files)}\n\n"
    
    for i, file in enumerate(files, 1):
        name = file.name or "Без названия"
        result += f"{i}. 📄 **{name}** (#{file.id})\n"
        
        if file.size:
            size_mb = file.size / (1024 * 1024)
            result += f"   └─ 📊 Размер: {size_mb:.2f} MB\n"
        if file.author:
            result += f"   └─ 👤 Автор: {file.author}\n"
        if file.created_date:
            result += f"   └─ 📅 Создан: {format_date(file.created_date)}\n"
        if file.task_id:
            result += f"   └─ 📋 Задача: #{file.task_id}\n"
        if file.project_id:
            result += f"   └─ 🎯 Проект: #{file.project_id}\n"
        
        result += "\n"
    
    return result.strip()


def format_report_list(reports: List[Report]) -> str:
    """Format a list of reports for display."""
    if not reports:
        return "Отчёты не найдены."
    
    result = f"📊 Найдено отчётов: {len(reports)}\n\n"
    
    for i, report in enumerate(reports, 1):
        name = report.name or "Без названия"
        result += f"{i}. 📊 **{name}** (#{report.id})\n"
        
        if report.description:
            result += f"   └─ 📄 {report.description[:100]}{'...' if len(report.description) > 100 else ''}\n"
        if report.created_date:
            result += f"   └─ 📅 Создан: {format_date(report.created_date)}\n"
        
        result += "\n"
    
    return result.strip()


def format_process_list(processes: List[Process]) -> str:
    """Format a list of processes for display."""
    if not processes:
        return "Процессы не найдены."
    
    result = f"⚙️ Найдено процессов: {len(processes)}\n\n"
    
    for i, process in enumerate(processes, 1):
        name = process.name or "Без названия"
        result += f"{i}. ⚙️ **{name}** (#{process.id})\n"
        
        if process.status:
            result += f"   └─ 🔄 Статус: {process.status}\n"
        if process.description:
            result += f"   └─ 📄 {process.description[:100]}{'...' if len(process.description) > 100 else ''}\n"
        if process.created_date:
            result += f"   └─ 📅 Создан: {format_date(process.created_date)}\n"
        
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


def format_project_list(projects: List[Project]) -> str:
    """Format a list of projects for display."""
    if not projects:
        return "Проекты не найдены."
    
    result = f"🎯 Найдено проектов: {len(projects)}\n\n"
    
    for i, project in enumerate(projects, 1):
        # Project object
        project_id = project.id or "N/A"
        name = project.name or "Без названия"
        status = project.status or "Активный"
        task_count = project.task_count or 0
        owner = project.owner or "Не назначен"
        
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
    current: Any = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


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