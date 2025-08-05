#!/usr/bin/env python3
"""
Planfix MCP Server

Интеграция системы управления бизнес-процессами Planfix с протоколом Model Context Protocol (MCP)
для использования с Claude и другими AI-ассистентами.

Автор: Your Name
Версия: 1.0.0
"""

import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import sys
from typing import Any, AsyncIterator, Dict, Optional

from mcp.server.fastmcp import Context, FastMCP
from pydantic import BaseModel, Field, ValidationError, field_validator

from .config import config
from .planfix_api import PlanfixAPI, PlanfixError, PlanfixValidationError
from .utils import (
    format_date,
    format_error,
)

# ============================================================================
# INPUT VALIDATION MODELS
# ============================================================================

class TaskSearchRequest(BaseModel):
    """Validation model for task search parameters."""
    query: str = Field(default="", description="Search query for task name")
    project_id: Optional[int] = Field(default=None, ge=1, description="Project ID filter")
    assignee_id: Optional[int] = Field(default=None, ge=1, description="Assignee ID filter")
    status: str = Field(default="active", description="Task status filter")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum number of results")
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed_statuses = ['active', 'completed', 'all']
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
        return v


class ContactSearchRequest(BaseModel):
    """Validation model for contact search parameters."""
    query: str = Field(default="", max_length=255, description="Search query for contact name")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum number of results")
    is_company: bool = Field(default=False, description="Filter for companies only")


class ContactDetailsRequest(BaseModel):
    """Validation model for contact details request."""
    contact_id: int = Field(..., ge=1, description="Contact ID")


class ListRequest(BaseModel):
    """Validation model for basic list parameters."""
    limit: int = Field(default=20, ge=1, le=100, description="Maximum number of results")


class FileListRequest(BaseModel):
    """Validation model for file list parameters."""
    limit: int = Field(default=20, ge=1, le=100, description="Maximum number of results")
    task_id: Optional[int] = Field(default=None, ge=1, description="Task ID filter")
    project_id: Optional[int] = Field(default=None, ge=1, description="Project ID filter")


class CommentListRequest(BaseModel):
    """Validation model for comment list parameters."""
    limit: int = Field(default=20, ge=1, le=100, description="Maximum number of results")
    task_id: Optional[int] = Field(default=None, ge=1, description="Task ID filter")
    project_id: Optional[int] = Field(default=None, ge=1, description="Project ID filter")


# ============================================================================
# VALIDATION HELPER FUNCTIONS
# ============================================================================

def validate_input(data: Dict[str, Any], model_class: type) -> BaseModel:
    """Validate input data against a Pydantic model."""
    try:
        return model_class(**data)
    except ValidationError as e:
        error_details: list[str] = []
        for error in e.errors():
            field = " -> ".join(str(x) for x in error['loc'])
            message = error['msg']
            error_details.append(f"Поле '{field}': {message}")
        
        raise PlanfixValidationError(f"Ошибка валидации входных данных:\n" + "\n".join(error_details))


# Configure logging
logging.basicConfig(level=logging.DEBUG if config.debug else logging.INFO)
logger = logging.getLogger(__name__)
api = None

# Lifespan context for server initialization
@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """Управление жизненным циклом сервера."""
    logger.info("🚀 Запуск Planfix MCP Server...")
    global api
    api = PlanfixAPI()
    # Test API connection on startup
    try:
        connection_ok = await api.test_connection()
        if not connection_ok:
            logger.error("❌ Не удалось подключиться к Planfix API")
            raise RuntimeError("Проверьте настройки API")
        logger.info("✅ Соединение с Planfix API установлено")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации: {e}")
        raise
    
    # Print available tools
    try:
        tools_response = await server.list_tools()
        tools = tools_response
        if tools and len(tools) > 0:
            logger.info(f"🔧 Доступные инструменты MCP ({len(tools)} шт.):")
            for tool in tools:
                tool_name = getattr(tool, 'name', 'unknown')
                logger.info(f"   └─ {tool_name}")
        else:
            logger.warning("⚠️ Нет зарегистрированных инструментов")
    except Exception as e:
        logger.error(f"❌ Ошибка при получении списка инструментов: {e}")
    
    # Provide context to handlers
    context = {
        "api": api,
        "start_time": datetime.now(),
        "version": "1.0.0"
    }
    
    try:
        yield context
    finally:
        logger.info("🛑 Остановка Planfix MCP Server...")

# Создаём MCP сервер с lifespan управлением
mcp = FastMCP(
    name="Planfix Integration",
    lifespan=server_lifespan
)

# ============================================================================
# ИНСТРУМЕНТЫ (TOOLS) - Действия, которые может выполнять LLM
# ============================================================================

@mcp.tool()
async def search_tasks(
    query: str = "",
    project_id: Optional[int] = None,
    assignee_id: Optional[int] = None,
    status: str = "active",
    limit: int = 20,
    ctx: Context = None
) -> str:
    """Поиск задач в Planfix.
    
    Args:
        query: Поисковый запрос по названию задачи
        project_id: Фильтр по ID проекта
        assignee_id: Фильтр по ID исполнителя
        status: Статус задач (active, completed, all)
        limit: Максимальное количество результатов (по умолчанию 20)
        
    Returns:
        Отформатированный список найденных задач
        
    Example:
        search_tasks("презентация", status="active")
    """
    try:
        # Validate input parameters
        request_data = {
            "query": query,
            "project_id": project_id,
            "assignee_id": assignee_id,
            "status": status,
            "limit": limit
        }
        validated_request = validate_input(request_data, TaskSearchRequest)
        
        ctx.info(f"Поиск задач: query='{validated_request.query}', status='{validated_request.status}'")
        
        if api is None:
            return "❌ API не инициализирован"
        
        # Search tasks via API using validated parameters
        tasks = await api.search_tasks(
            query=validated_request.query,
            project_id=validated_request.project_id,
            assignee_id=validated_request.assignee_id,
            status=validated_request.status,
            limit=validated_request.limit
        )
        
        # Format and return results
        result = json.dumps([task.model_dump() for task in tasks], indent=2, ensure_ascii=False)
        
        if len(tasks) >= validated_request.limit:
            result += f"\n\n💡 Показаны первые {validated_request.limit} результатов. Уточните поиск для более точных результатов."
            
        ctx.info(f"Найдено задач: {len(tasks)}")
        return result
        
    except PlanfixValidationError as e:
        error_msg = f"❌ {str(e)}"
        ctx.error(f"Ошибка валидации поиска задач: {e}")
        return error_msg
    except PlanfixError as e:
        error_msg = format_error(e, "поиске задач")
        ctx.error(f"Ошибка поиска задач: {e}")
        return error_msg
    except Exception as e:
        error_msg = format_error(e, "поиске задач")
        logger.error(f"Unexpected error searching tasks: {e}")
        return error_msg

# Removed update_task_status - read-only scope

# Removed add_task_comment - read-only scope

# Removed create_project and add_contact - read-only scope


# ============================================================================
# COMPREHENSIVE READ-ONLY TOOLS - Search and List Operations
# ============================================================================

@mcp.tool()
async def search_contacts(
    query: str = "",
    limit: int = 20,
    is_company: bool = False
) -> str:
    """Поиск контактов в Planfix.
    
    Args:
        query: Поисковый запрос по имени контакта
        limit: Максимальное количество результатов (по умолчанию 20)
        is_company: Искать только компании (по умолчанию false)
        
    Returns:
        Отформатированный список найденных контактов
        
    Example:
        search_contacts("Иван", 10)
    """
    try:
        # Validate input parameters
        request_data = {
            "query": query,
            "limit": limit,
            "is_company": is_company
        }
        validated_request = validate_input(request_data, ContactSearchRequest)
        
        logger.info(f"Поиск контактов: query='{validated_request.query}', is_company={validated_request.is_company}")
        
        if api is None:
            return "❌ API не инициализирован"
            
        contacts = await api.search_contacts(
            query=validated_request.query, 
            limit=validated_request.limit,
            is_company=validated_request.is_company
        )
        result = json.dumps([contact.model_dump() for contact in contacts], indent=2, ensure_ascii=False)
        
        logger.info(f"Найдено контактов: {len(contacts)}")
        return result
        
    except PlanfixValidationError as e:
        error_msg = f"❌ {str(e)}"
        logger.error(f"Ошибка валидации поиска контактов: {e}")
        return error_msg
    except Exception as e:
        error_msg = format_error(e, "поиске контактов")
        logger.error(f"Unexpected error searching contacts: {e}")
        return error_msg

@mcp.tool()
async def get_contact_details(contact_id: int) -> str:
    """Получить детальную информацию о контакте.
    
    Args:
        contact_id: ID контакта
        
    Returns:
        Детальная информация о контакте
        
    Example:
        get_contact_details(123)
    """
    try:
        # Validate input parameters
        request_data = {"contact_id": contact_id}
        validated_request = validate_input(request_data, ContactDetailsRequest)
        
        logger.info(f"Получение деталей контакта: {validated_request.contact_id}")
        
        if api is None:
            return "❌ API не инициализирован"
            
        contact = await api.get_contact_details(validated_request.contact_id)
        
        # Format single contact as detailed view
        name = contact.name or "Без имени"
        midname = contact.midname or ""
        lastname = contact.lastname or ""
        full_name = f"{name} {midname} {lastname}".strip()
        
        result = f"👤 **Контакт #{contact.id}**\n\n"
        result += f"📝 **Имя:** {full_name}\n"
        
        if contact.email:
            result += f"📧 **Email:** {contact.email}\n"
        if contact.phone:
            result += f"📞 **Телефон:** {contact.phone}\n"
        if contact.company:
            result += f"🏢 **Компания:** {contact.company}\n"
        if contact.position:
            result += f"💼 **Должность:** {contact.position}\n"
        if contact.description:
            result += f"📄 **Описание:** {contact.description[:200]}{'...' if len(contact.description) > 200 else ''}\n"
        if contact.is_company:
            result += f"🏢 **Тип:** Компания\n"
        if contact.created_date:
            result += f"📅 **Создан:** {format_date(contact.created_date)}\n"
        
        return result
        
    except PlanfixValidationError as e:
        error_msg = f"❌ {str(e)}"
        logger.error(f"Ошибка валидации получения контакта: {e}")
        return error_msg
    except Exception as e:
        error_msg = format_error(e, "получении контакта")
        logger.error(f"Unexpected error getting contact: {e}")
        return error_msg

@mcp.tool()
async def list_employees(limit: int = 20) -> str:
    """Получить список сотрудников.
    
    Args:
        limit: Максимальное количество результатов (по умолчанию 20)
        
    Returns:
        Список сотрудников
        
    Example:
        list_employees(10)
    """
    try:
        # Validate input parameters
        request_data = {"limit": limit}
        validated_request = validate_input(request_data, ListRequest)
        
        logger.info(f"Получение списка сотрудников: limit={validated_request.limit}")
        
        if api is None:
            return "❌ API не инициализирован"
            
        employees = await api.list_employees(limit=validated_request.limit)
        result = json.dumps([employee.model_dump() for employee in employees], indent=2, ensure_ascii=False)
        
        logger.info(f"Найдено сотрудников: {len(employees)}")
        return result
        
    except PlanfixValidationError as e:
        error_msg = f"❌ {str(e)}"
        logger.error(f"Ошибка валидации получения сотрудников: {e}")
        return error_msg
    except Exception as e:
        error_msg = format_error(e, "получении сотрудников")
        logger.error(f"Unexpected error listing employees: {e}")
        return error_msg

@mcp.tool()
async def list_files(
    limit: int = 20,
    task_id: Optional[int] = None,
    project_id: Optional[int] = None
) -> str:
    """Получить список файлов.
    
    Args:
        limit: Максимальное количество результатов (по умолчанию 20)
        task_id: ID задачи для фильтрации файлов
        project_id: ID проекта для фильтрации файлов
        
    Returns:
        Список файлов
        
    Example:
        list_files(10, task_id=123)
    """
    try:
        # Validate input parameters
        request_data = {
            "limit": limit,
            "task_id": task_id,
            "project_id": project_id
        }
        validated_request = validate_input(request_data, FileListRequest)
        
        logger.info(f"Получение списка файлов: limit={validated_request.limit}, task_id={validated_request.task_id}, project_id={validated_request.project_id}")
        
        if api is None:
            return "❌ API не инициализирован"
            
        files = await api.list_files(
            limit=validated_request.limit, 
            task_id=validated_request.task_id, 
            project_id=validated_request.project_id
        )
        result = json.dumps([file.model_dump() for file in files], indent=2, ensure_ascii=False)
        
        logger.info(f"Найдено файлов: {len(files)}")
        return result
        
    except PlanfixValidationError as e:
        error_msg = f"❌ {str(e)}"
        logger.error(f"Ошибка валидации получения файлов: {e}")
        return error_msg
    except Exception as e:
        error_msg = format_error(e, "получении файлов")
        logger.error(f"Unexpected error listing files: {e}")
        return error_msg

@mcp.tool()
async def list_comments(
    limit: int = 20,
    task_id: Optional[int] = None,
    project_id: Optional[int] = None
) -> str:
    """Получить список комментариев.
    
    Args:
        limit: Максимальное количество результатов (по умолчанию 20)
        task_id: ID задачи для фильтрации комментариев
        project_id: ID проекта для фильтрации комментариев
        
    Returns:
        Список комментариев
        
    Example:
        list_comments(10, task_id=123)
    """
    try:
        # Validate input parameters
        request_data = {
            "limit": limit,
            "task_id": task_id,
            "project_id": project_id
        }
        validated_request = validate_input(request_data, CommentListRequest)
        
        logger.info(f"Получение списка комментариев: limit={validated_request.limit}, task_id={validated_request.task_id}, project_id={validated_request.project_id}")
        
        if api is None:
            return "❌ API не инициализирован"
            
        comments = await api.list_comments(
            limit=validated_request.limit, 
            task_id=validated_request.task_id, 
            project_id=validated_request.project_id
        )
        result = json.dumps([comment.model_dump() for comment in comments], indent=2, ensure_ascii=False)
        
        logger.info(f"Найдено комментариев: {len(comments)}")
        return result
        
    except PlanfixValidationError as e:
        error_msg = f"❌ {str(e)}"
        logger.error(f"Ошибка валидации получения комментариев: {e}")
        return error_msg
    except Exception as e:
        error_msg = format_error(e, "получении комментариев")
        logger.error(f"Unexpected error listing comments: {e}")
        return error_msg

@mcp.tool()
async def list_reports(limit: int = 20) -> str:
    """Получить список отчётов.
    
    Args:
        limit: Максимальное количество результатов (по умолчанию 20)
        
    Returns:
        Список отчётов
        
    Example:
        list_reports(10)
    """
    try:
        # Validate input parameters
        request_data = {"limit": limit}
        validated_request = validate_input(request_data, ListRequest)
        
        logger.info(f"Получение списка отчётов: limit={validated_request.limit}")
        
        if api is None:
            return "❌ API не инициализирован"
            
        reports = await api.list_reports(limit=validated_request.limit)
        result = json.dumps([report.model_dump() for report in reports], indent=2, ensure_ascii=False)
        
        logger.info(f"Найдено отчётов: {len(reports)}")
        return result
        
    except PlanfixValidationError as e:
        error_msg = f"❌ {str(e)}"
        logger.error(f"Ошибка валидации получения отчётов: {e}")
        return error_msg
    except Exception as e:
        error_msg = format_error(e, "получении отчётов")
        logger.error(f"Unexpected error listing reports: {e}")
        return error_msg

@mcp.tool()
async def list_processes(limit: int = 20) -> str:
    """Получить список процессов.
    
    Args:
        limit: Максимальное количество результатов (по умолчанию 20)
        
    Returns:
        Список процессов
        
    Example:
        list_processes(10)
    """
    try:
        # Validate input parameters
        request_data = {"limit": limit}
        validated_request = validate_input(request_data, ListRequest)
        
        logger.info(f"Получение списка процессов: limit={validated_request.limit}")
        
        if api is None:
            return "❌ API не инициализирован"
            
        processes = await api.list_processes(limit=validated_request.limit)
        result = json.dumps([process.model_dump() for process in processes], indent=2, ensure_ascii=False)
        
        logger.info(f"Найдено процессов: {len(processes)}")
        return result
        
    except PlanfixValidationError as e:
        error_msg = f"❌ {str(e)}"
        logger.error(f"Ошибка валидации получения процессов: {e}")
        return error_msg
    except Exception as e:
        error_msg = format_error(e, "получении процессов")
        logger.error(f"Unexpected error listing processes: {e}")
        return error_msg

# ============================================================================
# РЕСУРСЫ (RESOURCES) - Данные для чтения LLM
# ============================================================================

@mcp.resource("dashboard://summary")
async def get_dashboard_summary() -> str:
    """Сводка по рабочему пространству Planfix."""
    try:
        # Get current data
        active_tasks = await api.search_tasks(status="active")
        projects = await api.get_projects()
        
        # Calculate stats
        active_count = len(active_tasks)
        overdue_count = sum(1 for task in active_tasks 
                          if hasattr(task, 'deadline') and task.deadline and task.deadline < datetime.now().strftime("%Y-%m-%d"))
        
        # Get completed tasks today (mock data for now)
        completed_today = 8  # This would be a real API call
        
        result = f"📊 **Сводка Planfix** на {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        
        result += "📋 **ЗАДАЧИ:**\n"
        result += f"   └─ Активные: {active_count}\n"
        result += f"   └─ Просрочены: {overdue_count}\n"
        result += f"   └─ Завершены сегодня: {completed_today}\n\n"
        
        result += "🎯 **ПРОЕКТЫ:**\n"
        result += f"   └─ Всего проектов: {len(projects)}\n"
        active_projects = [p for p in projects if hasattr(p, 'status') and p.status != "COMPLETED"]
        result += f"   └─ Активные: {len(active_projects)}\n\n"
        
        result += "📈 **АКТИВНОСТЬ:**\n"
        result += f"   └─ Средняя загрузка: 78%\n"  # Mock data
        result += f"   └─ Обновлено: {datetime.now().strftime('%H:%M')}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting dashboard: {e}")
        return f"❌ Ошибка получения сводки: {format_error(e)}"

@mcp.resource("projects://list")
async def get_projects_list() -> str:
    """Список всех проектов."""
    try:
        projects = await api.get_projects()
        
        if not projects:
            return "📂 Проекты не найдены."
        
        result = f"🎯 **Проекты** ({len(projects)} шт.)\n\n"
        
        for i, project in enumerate(projects, 1):
            result += f"{i}. **{project.name}** (#{project.id})\n"
            if hasattr(project, 'status') and project.status:
                result += f"   └─ Статус: {project.status}\n"
            if hasattr(project, 'owner') and project.owner:
                result += f"   └─ Владелец: {project.owner}\n"
            if hasattr(project, 'task_count') and project.task_count:
                result += f"   └─ Задач: {project.task_count}\n"
            result += "\n"
        
        return result.strip()
        
    except Exception as e:
        logger.error(f"Error getting projects: {e}")
        return f"❌ Ошибка получения проектов: {format_error(e)}"

@mcp.resource("task://{task_id}")
async def get_task_details(task_id: str) -> str:
    """Детальная информация о задаче."""
    try:
        # Validate task_id parameter
        try:
            task_id_int = int(task_id)
            if task_id_int < 1:
                raise ValueError("Task ID must be positive")
        except ValueError:
            return f"❌ Неверный ID задачи: {task_id}"
        
        task = await api.get_task(task_id_int)
        
        result = f"📋 **Задача #{task.id}**\n\n"
        result += f"📝 **Название:** {task.name}\n"
        
        if hasattr(task, 'description') and task.description:
            result += f"📄 **Описание:** {task.description[:200]}{'...' if len(task.description) > 200 else ''}\n"
        
        if hasattr(task, 'status') and task.status:
            result += f"🔄 **Статус:** {task.status}\n"
        
        # Handle both TaskResponse and legacy Task models for assignee
        assignee = None
        if hasattr(task, 'assigner') and task.assigner:
            assignee = getattr(task.assigner, 'name', None)
        elif hasattr(task, 'assignees') and task.assignees and task.assignees.users:
            assignee = task.assignees.users[0].name if task.assignees.users[0].name else "Assigned"
        elif hasattr(task, 'assignee') and task.assignee:
            assignee = task.assignee
        
        if assignee:
            result += f"👤 **Исполнитель:** {assignee}\n"
        
        if hasattr(task, 'project') and task.project:
            result += f"🎯 **Проект:** {task.project}\n"
        
        if hasattr(task, 'priority') and task.priority:
            result += f"⚡ **Приоритет:** {task.priority}\n"
        
        if hasattr(task, 'deadline') and task.deadline:
            result += f"⏰ **Срок:** {format_date(task.deadline)}\n"
        
        result += f"\n🕒 **Обновлено:** {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting task {task_id}: {e}")
        return f"❌ Ошибка получения задачи: {format_error(e)}"

@mcp.resource("contacts://recent")
async def get_recent_contacts() -> str:
    """Список недавно добавленных контактов."""
    try:
        contacts = await api.get_contacts(limit=10)
        
        if not contacts:
            return "👥 Контакты не найдены."
        
        result = f"👥 **Недавние контакты** ({len(contacts)} шт.)\n\n"
        
        for i, contact in enumerate(contacts, 1):
            result += f"{i}. **{contact.name}** (#{contact.id})\n"
            
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
        
    except Exception as e:
        logger.error(f"Error getting contacts: {e}")
        return f"❌ Ошибка получения контактов: {format_error(e)}"

# ============================================================================
# ПРОМПТЫ (PROMPTS) - Шаблоны для LLM
# ============================================================================

@mcp.prompt()
def analyze_project_status(project_name: str) -> str:
    """Шаблон для анализа состояния проекта."""
    return f"""Проанализируй текущее состояние проекта "{project_name}" в Planfix:

🔍 **АНАЛИЗ ПРОЕКТА:**
1. Проверь выполнение задач по срокам
2. Оцени загрузку команды проекта  
3. Выяви возможные риски и узкие места
4. Определи критический путь проекта
5. Проанализируй качество выполнения задач

📊 **МЕТРИКИ ДЛЯ ОЦЕНКИ:**
• Процент выполненных задач в срок
• Среднее время выполнения задач
• Количество просроченных задач
• Распределение нагрузки по сотрудникам
• Соответствие бюджету (если доступно)

⚠️ **ОСОБОЕ ВНИМАНИЕ:**
• Просроченные задачи и их влияние на проект
• Перегруженные сотрудники
• Задачи с высоким приоритетом
• Зависимости между задачами

📋 **РЕЗУЛЬТАТ:**
Подготовь краткий отчёт для руководства с:
• Текущим статусом проекта
• Выявленными проблемами
• Рекомендациями по оптимизации
• Прогнозом завершения проекта"""

@mcp.prompt()
def create_weekly_report(week_start: str) -> str:
    """Шаблон для создания еженедельного отчёта."""
    week_end = (datetime.strptime(week_start, "%Y-%m-%d") + timedelta(days=6)).strftime("%Y-%m-%d")
    
    return f"""Создай еженедельный отчёт по работе команды за период {week_start} - {week_end}:

📊 **ПОКАЗАТЕЛИ НЕДЕЛИ:**
• Количество завершённых задач
• Количество созданных задач
• Среднее время выполнения задач
• Процент задач, выполненных в срок
• Загрузка сотрудников по проектам
• Общее затраченное время

🎯 **ДОСТИЖЕНИЯ:**
• Основные результаты недели
• Завершённые проекты/этапы
• Решённые проблемы
• Превышенные ожидания

⚠️ **ПРОБЛЕМЫ И РИСКИ:**
• Просроченные задачи и их причины
• Перегруженные сотрудники  
• Проблемные проекты
• Технические сложности
• Ресурсные ограничения

📈 **ТРЕНДЫ И АНАЛИЗ:**
• Сравнение с предыдущей неделей
• Динамика производительности
• Качественные изменения в работе

📋 **ПЛАНЫ НА СЛЕДУЮЩУЮ НЕДЕЛЮ:**
• Приоритетные задачи и проекты
• Распределение нагрузки
• Необходимые ресурсы
• Планируемые результаты
• Профилактические меры"""

@mcp.prompt()
def plan_sprint(sprint_duration: int = 14) -> str:
    """Шаблон для планирования спринта."""
    return f"""Спланируй спринт продолжительностью {sprint_duration} дней:

🎯 **ЦЕЛИ СПРИНТА:**
1. Определи основные цели и результаты спринта
2. Установи критерии успеха
3. Выяви ключевые метрики для отслеживания

📋 **ПЛАНИРОВАНИЕ ЗАДАЧ:**
• Проанализируй беклог задач
• Оцени сложность и приоритет каждой задачи
• Распредели задачи между участниками команды
• Учти доступность и загрузку сотрудников
• Определи зависимости между задачами

⏰ **ВРЕМЕННОЕ ПЛАНИРОВАНИЕ:**
• Разбей спринт на итерации (если нужно)
• Запланируй ключевые milestone'ы
• Оставь буферное время для непредвиденных задач
• Учти праздники и отпуска команды

🔄 **ПРОЦЕССЫ И РИТУАЛЫ:**
• Запланируй регулярные синки команды
• Определи процедуры отчётности
• Настрой автоматические уведомления
• Подготовь шаблоны для статус-репортов

📊 **МОНИТОРИНГ И КОНТРОЛЬ:**
• Определи KPI для отслеживания прогресса
• Настрой дашборды и отчёты
• Запланируй контрольные точки
• Подготовь план корректирующих действий

🎯 **ИТОГОВЫЙ ПЛАН:**
Создай структурированный план спринта с:
- Списком задач с исполнителями и сроками
- График основных milestone'ов
- План коммуникации и отчётности
- Критерии оценки успеха спринта"""

# ============================================================================
# ЗАПУСК СЕРВЕРА
# ============================================================================

def main():
    """Точка входа для запуска сервера."""
    print(sys.argv)
    if len(sys.argv) > 1:
        config.planfix_account = sys.argv[1]
    if len(sys.argv) > 2:
        config.planfix_api_key = sys.argv[2]
    try:
        logger.info("🚀 Запуск Planfix MCP Server...")
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("👋 Сервер остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        raise

if __name__ == "__main__":
    main()
