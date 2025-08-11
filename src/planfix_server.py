#!/usr/bin/env python3
"""
Planfix MCP Server

Интеграция системы управления бизнес-процессами Planfix с протоколом Model Context Protocol (MCP)
для использования с Claude и другими AI-ассистентами.

Автор: Your Name
Версия: 1.0.0
"""

import argparse
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, AsyncIterator, Dict, List, Optional, TypeVar

from mcp.server.fastmcp import FastMCP
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

class PaginationMixin(BaseModel):
    """Base pagination parameters for list operations."""
    offset: int = Field(default=0, ge=0, description="Number of records to skip for pagination (0-based)")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum number of records to return per page")
    page: Optional[int] = Field(default=None, ge=1, description="Page number (1-based, alternative to offset)")
    
    def get_offset(self) -> int:
        """Calculate offset from page number if provided, otherwise use offset directly."""
        if self.page is not None:
            return (self.page - 1) * self.limit
        return self.offset


class TaskListRequest(PaginationMixin):
    """
    Validation model for task list parameters with pagination and filters.
    """
    project_id: Optional[int] = Field(default=None, ge=1, description="Filter tasks by specific project ID")
    assignee_id: Optional[int] = Field(default=None, ge=1, description="Filter tasks by specific assignee user ID")
    status: str = Field(default="active", description="Task status filter")
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed_statuses = ['active', 'completed', 'all']
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
        return v


class ContactListRequest(PaginationMixin):
    """
    Validation model for contact list parameters with pagination.
    """
    is_company: bool = Field(default=False, description="Filter for company contacts only (excludes individuals)")


class ContactDetailsRequest(BaseModel):
    """
    Validation model for contact details request.
    
    Returns full ContactResponse with all available fields including phones,
    custom fields, companies, and detailed metadata.
    """
    contact_id: int = Field(..., ge=1, description="Unique contact identifier")

class EntityByIdRequest(BaseModel):
    """Validation model for GET-by-id requests with optional fields selection."""
    id: int = Field(..., ge=1, description="Entity ID")
    fields: Optional[str] = Field(default=None, description="Comma-separated field list")


class ListRequest(PaginationMixin):
    """
    Base validation model for simple list operations with pagination.
    
    Used for endpoints that return basic entity lists.
    Individual items contain minimal information (id, name).
    Use specific GET endpoints for detailed information.
    """
    pass


class FileListRequest(PaginationMixin):
    """
    Validation model for file list parameters with optional entity filtering.
    
    Returns FileResponse objects with basic file metadata.
    Files can be filtered by task or project association.
    """
    task_id: Optional[int] = Field(default=None, ge=1, description="Filter files attached to specific task ID")
    project_id: Optional[int] = Field(default=None, ge=1, description="Filter files attached to specific project ID")


class CommentListRequest(PaginationMixin):
    """
    Validation model for comment list parameters with optional entity filtering.
    
    Returns CommentResponse objects with comment text and basic metadata.
    Comments can be filtered by task or project association.
    """
    task_id: Optional[int] = Field(default=None, ge=1, description="Filter comments from specific task ID")
    project_id: Optional[int] = Field(default=None, ge=1, description="Filter comments from specific project ID")


# ============================================================================
# VALIDATION HELPER FUNCTIONS
# ============================================================================

T = TypeVar('T', bound=BaseModel)

def validate_input(data: Dict[str, Any], model_class: type[T]) -> T:
    """Validate input data against a Pydantic model."""
    try:
        return model_class(**data)
    except ValidationError as e:
        error_details: List[str] = []
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
    logger.info("Запуск Planfix MCP Server...")
    global api
    api = PlanfixAPI()
    # Test API connection on startup
    try:
        connection_ok = await api.test_connection()
        if not connection_ok:
            logger.error("Не удалось подключиться к Planfix API")
            raise RuntimeError("Проверьте настройки API")
        logger.info("Соединение с Planfix API установлено")
    except Exception as e:
        logger.error(f"Ошибка инициализации: {e}")
        raise
    
    # Print available tools
    try:
        tools_response = await server.list_tools()
        tools = tools_response
        if tools and len(tools) > 0:
            logger.info(f"Доступные инструменты MCP ({len(tools)} шт.):")
            for tool in tools:
                tool_name = getattr(tool, 'name', 'unknown')
                logger.info(f"   - {tool_name}")
        else:
            logger.warning("Нет зарегистрированных инструментов")
    except Exception as e:
        logger.error(f"Ошибка при получении списка инструментов: {e}")
    
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
async def list_tasks(
    project_id: Optional[int] = None,
    assignee_id: Optional[int] = None,
    status: str = "active",
    offset: int = 0,
    limit: int = 20,
    page: Optional[int] = None
) -> str:
    """
    Search for tasks in Planfix with comprehensive filtering and pagination support.
    
    This endpoint returns a list of TaskResponse objects containing basic task information.
    For complete task details including custom fields, attachments, and full assignee information,
    use the task://{task_id} resource or implement a get_task_details tool.
    
    **Response Schema (TaskResponse objects):**
    - id (int): Unique task identifier
    - name (str): Task title/name
    - description (str, optional): Task description (truncated in list view)
    - priority (str, optional): Task priority level (Low, Normal, High, Urgent)
    - status (TaskStatus, optional): Current task status with id and name
    - assigner (PersonResponse, optional): User who assigned the task
    - assignees (PeopleResponse, optional): Users and groups assigned to the task
    - project (BaseEntity, optional): Associated project reference (id and name)
    - startDateTime (TimePoint, optional): Task start date and time
    - endDateTime (TimePoint, optional): Task due date and time
    - Additional metadata fields (created date, last update, etc.)
    
    **Pagination:**
    Use either offset/limit or page/limit combinations:
    - offset=0, limit=20: Get first 20 tasks
    - offset=20, limit=20: Get next 20 tasks (items 21-40)  
    - page=1, limit=20: Get first page (same as offset=0)
    - page=2, limit=20: Get second page (same as offset=20)
    
    **Note:** This method returns only basic task information suitable for lists and overviews.
    For detailed task information including complete assignee details, custom fields, 
    attachments, and full metadata, use GET /task/{task_id} endpoint.
    
    Args:
        query (str): Search query for task name/title (supports partial matching)
        project_id (int, optional): Filter tasks belonging to specific project ID
        assignee_id (int, optional): Filter tasks assigned to specific user ID
        status (str): Task status filter - "active" (default), "completed", or "all"
        offset (int): Number of records to skip for pagination (0-based, default: 0)
        limit (int): Maximum number of records per page (1-100, default: 20)
        page (int, optional): Page number (1-based, alternative to offset)
        
    Returns:
        str: JSON-formatted array of TaskResponse objects with pagination info
        
    Examples:
        list_tasks(project_id=123, status="active") - Active tasks from project 123
        list_tasks(assignee_id=456, limit=50) - Tasks assigned to user 456, 50 results
        list_tasks(page=2, limit=10) - Second page of tasks
    
    Raises:
        PlanfixValidationError: Invalid input parameters
        PlanfixError: API communication or server error
    """
    try:
        # Validate input parameters with pagination support
        request_data = {
            "project_id": project_id,
            "assignee_id": assignee_id,
            "status": status,
            "offset": offset,
            "limit": limit,
            "page": page
        }
        validated_request = validate_input(request_data, TaskListRequest)
        
        logger.info(f"Список задач: status='{validated_request.status}', offset={validated_request.get_offset()}, limit={validated_request.limit}")
        
        if api is None:
            return "API не инициализирован"
        
        # Search tasks via API using validated parameters
        tasks = await api.list_tasks(
            project_id=validated_request.project_id,
            assignee_id=validated_request.assignee_id,
            status=validated_request.status,
            limit=validated_request.limit,
            offset=validated_request.get_offset()
        )
        
        # Format and return results
        result = json.dumps([task.model_dump() for task in tasks], indent=2, ensure_ascii=False)
        
        # Add pagination info
        if len(tasks) >= validated_request.limit:
            result += f"\n\nПоказаны {len(tasks)} результатов (лимит: {validated_request.limit})"
            if validated_request.page:
                result += f", страница {validated_request.page}"
            else:
                result += f", смещение {validated_request.get_offset()}"
            result += ". Используйте параметры offset/page для получения следующих результатов."
        else:
            result += f"\n\nВсего найдено: {len(tasks)} задач(и)"
            
        logger.info(f"Найдено задач: {len(tasks)}")
        return result
        
    except PlanfixValidationError as e:
        error_msg = f"Ошибка валидации: {str(e)}"
        logger.error(f"Ошибка валидации поиска задач: {e}")
        return error_msg
    except PlanfixError as e:
        error_msg = format_error(e, "поиске задач")
        logger.error(f"Ошибка поиска задач: {e}")
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
async def list_contacts(
    offset: int = 0,
    limit: int = 20,
    page: Optional[int] = None,
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
        list_contacts(10)
    """
    try:
        # Validate input parameters
        request_data = {
            "offset": offset,
            "limit": limit,
            "page": page,
            "is_company": is_company
        }
        validated_request = validate_input(request_data, ContactListRequest)
        
        logger.info(f"Список контактов: is_company={validated_request.is_company}")
        
        if api is None:
            return "API не инициализирован"
            
        contacts = await api.list_contacts(
            limit=validated_request.limit,
            offset=validated_request.get_offset(),
            is_company=validated_request.is_company
        )
        result = json.dumps([contact.model_dump() for contact in contacts], indent=2, ensure_ascii=False)

        # Add pagination info
        if len(contacts) >= validated_request.limit:
            result += f"\n\nПоказаны {len(contacts)} результатов (лимит: {validated_request.limit})"
            if validated_request.page:
                result += f", страница {validated_request.page}"
            else:
                result += f", смещение {validated_request.get_offset()}"
            result += ". Используйте параметры offset/page для получения следующих результатов."
        else:
            result += f"\n\nВсего найдено: {len(contacts)} контакт(ов)"

        logger.info(f"Найдено контактов: {len(contacts)}")
        return result
        
    except PlanfixValidationError as e:
        error_msg = f"Ошибка валидации: {str(e)}"
        logger.error(f"Ошибка валидации поиска контактов: {e}")
        return error_msg
    except Exception as e:
        error_msg = format_error(e, "поиске контактов")
        logger.error(f"Unexpected error searching contacts: {e}")
        return error_msg

@mcp.tool()
async def get_contact_details(contact_id: int) -> str:
    """
    Retrieve comprehensive details for a specific contact by ID.
    
    This endpoint returns complete contact information including all available fields,
    custom field data, associated companies, phone numbers, and full metadata.
    This provides significantly more detail than the basic contact information
    returned by list_contacts().
    
    **Complete ContactResponse Schema:**
    - id (int): Unique contact identifier
    - name (str): Primary contact name
    - midname (str, optional): Middle name
    - lastname (str, optional): Last name
    - email (str, optional): Primary email address  
    - additionalEmailAddresses (List[str], optional): Additional email addresses
    - phones (List[PhoneResponse], optional): Phone numbers with types and masked versions
    - position (str, optional): Job position/title
    - description (str, optional): Full contact description (not truncated)
    - address (str, optional): Physical address
    - site (str, optional): Website URL
    - gender (str, optional): Gender information
    - birthDate (TimePoint, optional): Date of birth
    - isCompany (bool): Whether this contact represents a company
    - isDeleted (bool): Deletion status
    - group (GroupResponse, optional): Contact group association
    - companies (List[CompanyEntity], optional): Associated companies
    - contacts (List[PersonResponse], optional): Related contacts
    - supervisors (PeopleResponse, optional): Supervisor information
    - files (List[FileResponse], optional): Attached files
    - customFieldData (List[CustomFieldValueResponse], optional): Custom field values
    - dataTags (List[DataTagEntryResponse], optional): Data tag associations
    - createdDate (TimePoint, optional): Contact creation timestamp
    - dateOfLastUpdate (TimePoint, optional): Last modification timestamp
    - Social media fields: skype, telegram, facebook, instagram, vk, etc.
    
    **Difference from search_contacts():**
    - list_contacts(): Returns basic contact info suitable for lists (id, name, email, position)
    - get_contact_details(): Returns complete contact record with all fields and relationships
    
    Args:
        contact_id (int): Unique contact identifier (must be > 0)
        
    Returns:
        str: Human-readable formatted contact details with all available information
        
    Examples:
        get_contact_details(123) - Get full details for contact ID 123
        get_contact_details(456) - Retrieve complete contact record for ID 456
    
    Raises:
        PlanfixValidationError: Invalid contact_id parameter
        PlanfixNotFoundError: Contact with specified ID not found
        PlanfixError: API communication or server error
    """
    try:
        # Validate input parameters
        request_data = {"contact_id": contact_id}
        validated_request = validate_input(request_data, ContactDetailsRequest)
        
        logger.info(f"Получение деталей контакта: {validated_request.contact_id}")
        
        if api is None:
            return "API не инициализирован"
            
        contact = await api.get_contact_details(validated_request.contact_id)
        
        # Format single contact as detailed view
        name = contact.name or "Без имени"
        midname = contact.midname or ""
        lastname = contact.lastname or ""
        full_name = f"{name} {midname} {lastname}".strip()
        
        result = f"Контакт #{contact.id}\n\n"
        result += f"Имя: {full_name}\n"
        
        if contact.email:
            result += f"Email: {contact.email}\n"
        if contact.phone:
            result += f"Телефон: {contact.phone}\n"
        if contact.company:
            result += f"Компания: {contact.company}\n"
        if contact.position:
            result += f"Должность: {contact.position}\n"
        if contact.description:
            result += f"Описание: {contact.description}\n"  # Full description, not truncated
        if contact.is_company:
            result += f"Тип: Компания\n"
        if contact.created_date:
            result += f"Создан: {format_date(contact.created_date)}\n"
        
        result += f"\nПолная детальная информация о контакте ID {contact.id}"
        return result
        
    except PlanfixValidationError as e:
        error_msg = f"{str(e)}"
        logger.error(f"Ошибка валидации получения контакта: {e}")
        return error_msg
    except Exception as e:
        error_msg = format_error(e, "получении контакта")
        logger.error(f"Unexpected error getting contact: {e}")
        return error_msg

@mcp.tool()
async def get_comment(comment_id: int, fields: Optional[str] = None) -> str:
    """Get a comment by ID with optional fields selection."""
    try:
        request_data = {"id": comment_id, "fields": fields}
        validated = validate_input(request_data, EntityByIdRequest)
        if api is None:
            return "API не инициализирован"
        comment = await api.get_comment(validated.id, validated.fields)
        return json.dumps(comment.model_dump(), indent=2, ensure_ascii=False)
    except Exception as e:
        return format_error(e, "получении комментария")

@mcp.tool()
async def get_file(file_id: int, fields: Optional[str] = None) -> str:
    """Get a file by ID with optional fields selection."""
    try:
        request_data = {"id": file_id, "fields": fields}
        validated = validate_input(request_data, EntityByIdRequest)
        if api is None:
            return "API не инициализирован"
        file = await api.get_file(validated.id, validated.fields)
        return json.dumps(file.model_dump(), indent=2, ensure_ascii=False)
    except Exception as e:
        return format_error(e, "получении файла")

@mcp.tool()
async def get_project(project_id: int, fields: Optional[str] = None) -> str:
    """Get a project by ID with optional fields selection."""
    try:
        request_data = {"id": project_id, "fields": fields}
        validated = validate_input(request_data, EntityByIdRequest)
        if api is None:
            return "API не инициализирован"
        project = await api.get_project(validated.id, validated.fields)
        return json.dumps(project.model_dump(), indent=2, ensure_ascii=False)
    except Exception as e:
        return format_error(e, "получении проекта")

@mcp.tool()
async def get_user(user_id: int, fields: Optional[str] = None) -> str:
    """Get a user by ID with optional fields selection."""
    try:
        request_data = {"id": user_id, "fields": fields}
        validated = validate_input(request_data, EntityByIdRequest)
        if api is None:
            return "API не инициализирован"
        user = await api.get_user(validated.id, validated.fields)
        return json.dumps(user.model_dump(), indent=2, ensure_ascii=False)
    except Exception as e:
        return format_error(e, "получении пользователя")

@mcp.tool()
async def list_employees(
    offset: int = 0,
    limit: int = 20,
    page: Optional[int] = None
) -> str:
    """
    List employees/users in the Planfix system with pagination support.
    
    This endpoint returns basic employee information suitable for user selection,
    team lists, and assignee dropdowns. Returns minimal user data focused on
    identification and contact information.
    
    **Response Schema (UserResponse objects):**
    - id (int|str): Unique user identifier
    - name (str): Full user name
    - email (str, optional): User email address
    - position (str, optional): Job position/title
    - Additional basic user metadata
    
    **Pagination:**
    Use either offset/limit or page/limit combinations:
    - offset=0, limit=20: Get first 20 employees
    - offset=20, limit=20: Get employees 21-40
    - page=1, limit=20: Get first page (same as offset=0)
    - page=2, limit=20: Get second page (same as offset=20)
    
    **Note:** This method returns basic employee information (id, name, email, position).
    For detailed employee information including permissions, groups, custom fields,
    and full metadata, use GET /user/{user_id} endpoint if available.
    
    Args:
        offset (int): Number of records to skip for pagination (0-based, default: 0)
        limit (int): Maximum number of records per page (1-100, default: 20)
        page (int, optional): Page number (1-based, alternative to offset)
        
    Returns:
        str: JSON-formatted array of UserResponse objects with pagination info
        
    Examples:
        list_employees() - Get first 20 employees
        list_employees(limit=50) - Get first 50 employees
        list_employees(offset=10, limit=5) - Get employees 11-15
        list_employees(page=2, limit=25) - Get second page with 25 employees per page
    
    Raises:
        PlanfixValidationError: Invalid input parameters
        PlanfixError: API communication or server error
    """
    try:
        # Validate input parameters
        request_data = {
            "offset": offset,
            "limit": limit,
            "page": page
        }
        validated_request = validate_input(request_data, ListRequest)
        
        logger.info(f"Получение списка сотрудников: offset={validated_request.get_offset()}, limit={validated_request.limit}")
        
        if api is None:
            return "API не инициализирован"
            
        employees = await api.list_employees(limit=validated_request.limit, offset=validated_request.get_offset())
        result = json.dumps([employee.model_dump() for employee in employees], indent=2, ensure_ascii=False)
        
        # Add pagination info
        if len(employees) >= validated_request.limit:
            result += f"\n\nПоказаны {len(employees)} результатов (лимит: {validated_request.limit})"
            if validated_request.page:
                result += f", страница {validated_request.page}"
            else:
                result += f", смещение {validated_request.get_offset()}"
            result += ". Используйте параметры offset/page для получения следующих результатов."
        else:
            result += f"\n\nВсего найдено: {len(employees)} сотрудник(ов)"
        
        logger.info(f"Найдено сотрудников: {len(employees)}")
        return result
        
    except PlanfixValidationError as e:
        error_msg = f"{str(e)}"
        logger.error(f"Ошибка валидации получения сотрудников: {e}")
        return error_msg
    except Exception as e:
        error_msg = format_error(e, "получении сотрудников")
        logger.error(f"Unexpected error listing employees: {e}")
        return error_msg

@mcp.tool()
async def list_files(
    offset: int = 0,
    limit: int = 20,
    page: Optional[int] = None,
    task_id: Optional[int] = None,
    project_id: Optional[int] = None
) -> str:
    """
    List files in the Planfix system with optional filtering and pagination.
    
    This endpoint returns basic file metadata including file names, sizes, and creation info.
    Files can be filtered by task or project association. Returns minimal file information
    suitable for file lists and attachment overviews.
    
    **Response Schema (FileResponse objects):**
    - id (int): Unique file identifier
    - name (str): File name with extension
    - size (int, optional): File size in bytes
    - created_date (str, optional): File upload timestamp
    - author (str, optional): User who uploaded the file
    - Additional basic file metadata
    
    **Pagination:**
    Use either offset/limit or page/limit combinations:
    - offset=0, limit=20: Get first 20 files
    - offset=20, limit=20: Get files 21-40
    - page=1, limit=20: Get first page (same as offset=0)
    - page=2, limit=20: Get second page (same as offset=20)
    
    **Filtering:**
    - No filters: Returns all files user has access to
    - task_id only: Returns files attached to specific task
    - project_id only: Returns files from specific project
    - Both filters: Returns files attached to specified task within specified project
    
    **Note:** This method returns basic file metadata (id, name, size, author).
    For file download or detailed file information including custom fields and full metadata,
    use GET /file/{file_id} endpoint if available.
    
    Args:
        offset (int): Number of records to skip for pagination (0-based, default: 0)
        limit (int): Maximum number of records per page (1-100, default: 20)
        page (int, optional): Page number (1-based, alternative to offset)
        task_id (int, optional): Filter files attached to specific task ID
        project_id (int, optional): Filter files from specific project ID
        
    Returns:
        str: JSON-formatted array of FileResponse objects with pagination info
        
    Examples:
        list_files() - Get first 20 files from all accessible sources
        list_files(task_id=123) - Get files attached to task 123
        list_files(project_id=456, limit=50) - Get first 50 files from project 456
        list_files(task_id=123, project_id=456) - Get files from task 123 in project 456
        list_files(page=2, limit=10) - Get second page with 10 files per page
    
    Raises:
        PlanfixValidationError: Invalid input parameters
        PlanfixError: API communication or server error
    """
    try:
        # Validate input parameters
        request_data = {
            "offset": offset,
            "limit": limit,
            "page": page,
            "task_id": task_id,
            "project_id": project_id
        }
        validated_request = validate_input(request_data, FileListRequest)
        
        logger.info(f"Получение списка файлов: offset={validated_request.get_offset()}, limit={validated_request.limit}, task_id={validated_request.task_id}, project_id={validated_request.project_id}")
        
        if api is None:
            return "API не инициализирован"
            
        files = await api.list_files(
            limit=validated_request.limit,
            offset=validated_request.get_offset(),
            task_id=validated_request.task_id,
            project_id=validated_request.project_id
        )
        result = json.dumps([file.model_dump() for file in files], indent=2, ensure_ascii=False)
        
        # Add pagination and filtering info
        filter_info = []
        if validated_request.task_id:
            filter_info.append(f"задача {validated_request.task_id}")
        if validated_request.project_id:
            filter_info.append(f"проект {validated_request.project_id}")
        filter_str = f" ({', '.join(filter_info)})" if filter_info else ""
        
        if len(files) >= validated_request.limit:
            result += f"\n\nПоказаны {len(files)} результатов{filter_str} (лимит: {validated_request.limit})"
            if validated_request.page:
                result += f", страница {validated_request.page}"
            else:
                result += f", смещение {validated_request.get_offset()}"
            result += ". Используйте параметры offset/page для получения следующих результатов."
        else:
            result += f"\n\nВсего найдено: {len(files)} файл(ов){filter_str}"
        
        logger.info(f"Найдено файлов: {len(files)}")
        return result
        
    except PlanfixValidationError as e:
        error_msg = f"{str(e)}"
        logger.error(f"Ошибка валидации получения файлов: {e}")
        return error_msg
    except Exception as e:
        error_msg = format_error(e, "получении файлов")
        logger.error(f"Unexpected error listing files: {e}")
        return error_msg

@mcp.tool()
async def list_comments(
    offset: int = 0,
    limit: int = 20,
    page: Optional[int] = None,
    task_id: Optional[int] = None,
    project_id: Optional[int] = None
) -> str:
    """
    List comments in the Planfix system with optional filtering and pagination.
    
    This endpoint returns basic comment information including comment text and author details.
    Comments can be filtered by task or project association. Returns minimal comment data
    suitable for comment lists and activity feeds.
    
    **Response Schema (CommentResponse objects):**
    - id (int): Unique comment identifier
    - description (str): Comment text content
    - dateTime (TimePoint): Comment creation timestamp
    - owner (PersonResponse): User who created the comment
    - type (str, optional): Comment type
    - isPinned (bool, optional): Whether comment is pinned
    - isHidden (bool, optional): Whether comment is hidden
    - project (BaseEntity, optional): Associated project reference
    - contact (BaseEntity, optional): Associated contact reference
    - Additional basic comment metadata
    
    **Pagination:**
    Use either offset/limit or page/limit combinations:
    - offset=0, limit=20: Get first 20 comments
    - offset=20, limit=20: Get comments 21-40
    - page=1, limit=20: Get first page (same as offset=0)
    - page=2, limit=20: Get second page (same as offset=20)
    
    **Filtering:**
    - No filters: Returns all comments user has access to
    - task_id only: Returns comments from specific task
    - project_id only: Returns comments from specific project  
    - Both filters: Returns task comments within specified project
    
    **Note:** This method returns basic comment information (id, text, author, date).
    For detailed comment information including attachments, recipients, reminders,
    and full metadata, use GET /comment/{comment_id} endpoint if available.
    
    Args:
        offset (int): Number of records to skip for pagination (0-based, default: 0)
        limit (int): Maximum number of records per page (1-100, default: 20)
        page (int, optional): Page number (1-based, alternative to offset)
        task_id (int, optional): Filter comments from specific task ID
        project_id (int, optional): Filter comments from specific project ID
        
    Returns:
        str: JSON-formatted array of CommentResponse objects with pagination info
        
    Examples:
        list_comments() - Get first 20 comments from all accessible sources
        list_comments(task_id=123) - Get comments from task 123
        list_comments(project_id=456, limit=50) - Get first 50 comments from project 456
        list_comments(task_id=123, project_id=456) - Get task 123 comments in project 456
        list_comments(page=2, limit=15) - Get second page with 15 comments per page
    
    Raises:
        PlanfixValidationError: Invalid input parameters
        PlanfixError: API communication or server error
    """
    try:
        # Validate input parameters
        request_data = {
            "offset": offset,
            "limit": limit,
            "page": page,
            "task_id": task_id,
            "project_id": project_id
        }
        validated_request = validate_input(request_data, CommentListRequest)
        
        logger.info(f"Получение списка комментариев: offset={validated_request.get_offset()}, limit={validated_request.limit}, task_id={validated_request.task_id}, project_id={validated_request.project_id}")
        
        if api is None:
            return "API не инициализирован"
            
        comments = await api.list_comments(
            limit=validated_request.limit,
            offset=validated_request.get_offset(),
            task_id=validated_request.task_id,
            project_id=validated_request.project_id
        )
        result = json.dumps([comment.model_dump() for comment in comments], indent=2, ensure_ascii=False)
        
        # Add pagination and filtering info
        filter_info = []
        if validated_request.task_id:
            filter_info.append(f"задача {validated_request.task_id}")
        if validated_request.project_id:
            filter_info.append(f"проект {validated_request.project_id}")
        filter_str = f" ({', '.join(filter_info)})" if filter_info else ""
        
        if len(comments) >= validated_request.limit:
            result += f"\n\nПоказаны {len(comments)} результатов{filter_str} (лимит: {validated_request.limit})"
            if validated_request.page:
                result += f", страница {validated_request.page}"
            else:
                result += f", смещение {validated_request.get_offset()}"
            result += ". Используйте параметры offset/page для получения следующих результатов."
        else:
            result += f"\n\nВсего найдено: {len(comments)} комментар(иев){filter_str}"
        
        logger.info(f"Найдено комментариев: {len(comments)}")
        return result
        
    except PlanfixValidationError as e:
        error_msg = f"{str(e)}"
        logger.error(f"Ошибка валидации получения комментариев: {e}")
        return error_msg
    except Exception as e:
        error_msg = format_error(e, "получении комментариев")
        logger.error(f"Unexpected error listing comments: {e}")
        return error_msg

@mcp.tool()
async def list_reports(
    offset: int = 0,
    limit: int = 20,
    page: Optional[int] = None
) -> str:
    """
    List available reports in the Planfix system with pagination support.
    
    This endpoint returns basic report information including report names and descriptions.
    Returns minimal report metadata suitable for report selection and overview displays.
    
    **Response Schema (Report objects):**
    - id (int): Unique report identifier
    - name (str): Report name/title
    - description (str, optional): Report description
    - fields (List[ReportField], optional): Available report fields
    - Additional basic report metadata
    
    **Pagination:**
    Use either offset/limit or page/limit combinations:
    - offset=0, limit=20: Get first 20 reports
    - offset=20, limit=20: Get reports 21-40
    - page=1, limit=20: Get first page (same as offset=0)
    - page=2, limit=20: Get second page (same as offset=20)
    
    **Note:** This method returns basic report information (id, name, description).
    For detailed report information including field definitions, data, and execution results,
    use GET /report/{report_id} endpoint if available.
    
    Args:
        offset (int): Number of records to skip for pagination (0-based, default: 0)
        limit (int): Maximum number of records per page (1-100, default: 20)
        page (int, optional): Page number (1-based, alternative to offset)
        
    Returns:
        str: JSON-formatted array of Report objects with pagination info
        
    Examples:
        list_reports() - Get first 20 available reports
        list_reports(limit=50) - Get first 50 reports
        list_reports(page=2, limit=10) - Get second page with 10 reports per page
    
    Raises:
        PlanfixValidationError: Invalid input parameters
        PlanfixError: API communication or server error
    """
    try:
        # Validate input parameters
        request_data = {
            "offset": offset,
            "limit": limit,
            "page": page
        }
        validated_request = validate_input(request_data, ListRequest)
        
        logger.info(f"Получение списка отчётов: offset={validated_request.get_offset()}, limit={validated_request.limit}")
        
        if api is None:
            return "API не инициализирован"
            
        reports = await api.list_reports(limit=validated_request.limit, offset=validated_request.get_offset())
        result = json.dumps([report.model_dump() for report in reports], indent=2, ensure_ascii=False)
        
        # Add pagination info
        if len(reports) >= validated_request.limit:
            result += f"\n\nПоказаны {len(reports)} результатов (лимит: {validated_request.limit})"
            if validated_request.page:
                result += f", страница {validated_request.page}"
            else:
                result += f", смещение {validated_request.get_offset()}"
            result += ". Используйте параметры offset/page для получения следующих результатов."
        else:
            result += f"\n\nВсего найдено: {len(reports)} отчёт(ов)"
        
        logger.info(f"Найдено отчётов: {len(reports)}")
        return result
        
    except PlanfixValidationError as e:
        error_msg = f"{str(e)}"
        logger.error(f"Ошибка валидации получения отчётов: {e}")
        return error_msg
    except Exception as e:
        error_msg = format_error(e, "получении отчётов")
        logger.error(f"Unexpected error listing reports: {e}")
        return error_msg

@mcp.tool()
async def list_processes(
    offset: int = 0,
    limit: int = 20,
    page: Optional[int] = None
) -> str:
    """
    List business processes in the Planfix system with pagination support.
    
    This endpoint returns basic process information including process names and status.
    Returns minimal process metadata suitable for process selection and workflow overviews.
    
    **Response Schema (Process objects):**
    - id (int): Unique process identifier
    - name (str): Process name/title
    - description (str, optional): Process description
    - status (str, optional): Current process status
    - created_date (str, optional): Process creation timestamp
    - Additional basic process metadata
    
    **Pagination:**
    Use either offset/limit or page/limit combinations:
    - offset=0, limit=20: Get first 20 processes
    - offset=20, limit=20: Get processes 21-40
    - page=1, limit=20: Get first page (same as offset=0)
    - page=2, limit=20: Get second page (same as offset=20)
    
    **Note:** This method returns basic process information (id, name, status).
    For detailed process information including workflow steps, automation rules,
    and configuration details, use GET /process/{process_id} endpoint if available.
    
    Args:
        offset (int): Number of records to skip for pagination (0-based, default: 0)
        limit (int): Maximum number of records per page (1-100, default: 20)
        page (int, optional): Page number (1-based, alternative to offset)
        
    Returns:
        str: JSON-formatted array of Process objects with pagination info
        
    Examples:
        list_processes() - Get first 20 business processes
        list_processes(limit=50) - Get first 50 processes
        list_processes(page=2, limit=15) - Get second page with 15 processes per page
    
    Raises:
        PlanfixValidationError: Invalid input parameters
        PlanfixError: API communication or server error
    """
    try:
        # Validate input parameters
        request_data = {
            "offset": offset,
            "limit": limit,
            "page": page
        }
        validated_request = validate_input(request_data, ListRequest)
        
        logger.info(f"Получение списка процессов: offset={validated_request.get_offset()}, limit={validated_request.limit}")
        
        if api is None:
            return "API не инициализирован"
            
        processes = await api.list_processes(limit=validated_request.limit, offset=validated_request.get_offset())
        result = json.dumps([process.model_dump() for process in processes], indent=2, ensure_ascii=False)
        
        # Add pagination info
        if len(processes) >= validated_request.limit:
            result += f"\n\nПоказаны {len(processes)} результатов (лимит: {validated_request.limit})"
            if validated_request.page:
                result += f", страница {validated_request.page}"
            else:
                result += f", смещение {validated_request.get_offset()}"
            result += ". Используйте параметры offset/page для получения следующих результатов."
        else:
            result += f"\n\nВсего найдено: {len(processes)} процесс(ов)"
        
        logger.info(f"Найдено процессов: {len(processes)}")
        return result
        
    except PlanfixValidationError as e:
        error_msg = f"{str(e)}"
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
        active_tasks = await api.list_tasks(status="active")
        projects = await api.list_projects()
        
        # Calculate stats
        active_count = len(active_tasks)
        overdue_count = sum(1 for task in active_tasks 
                          if hasattr(task, 'deadline') and task.deadline and task.deadline < datetime.now().strftime("%Y-%m-%d"))
        
        # Get completed tasks today (mock data for now)
        completed_today = 8  # This would be a real API call
        
        result = f"Сводка Planfix на {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        
        result += "ЗАДАЧИ:\n"
        result += f"- Активные: {active_count}\n"
        result += f"- Просрочены: {overdue_count}\n"
        result += f"- Завершены сегодня: {completed_today}\n\n"
        
        result += "ПРОЕКТЫ:\n"
        result += f"- Всего проектов: {len(projects)}\n"
        active_projects = [p for p in projects if hasattr(p, 'status') and p.status != "COMPLETED"]
        result += f"- Активные: {len(active_projects)}\n\n"
        
        result += "АКТИВНОСТЬ:\n"
        result += f"- Средняя загрузка: 78%\n"  # Mock data
        result += f"- Обновлено: {datetime.now().strftime('%H:%M')}\n"
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting dashboard: {e}")
        return f"Ошибка получения сводки: {format_error(e)}"

@mcp.resource("projects://list")
async def get_projects_list() -> str:
    """Список всех проектов."""
    try:
        projects = await api.list_projects()
        
        if not projects:
            return "Проекты не найдены."
        
        result = f"Проекты ({len(projects)} шт.)\n\n"
        
        for i, project in enumerate(projects, 1):
            result += f"{i}. {project.name} (#{project.id})\n"
            if hasattr(project, 'status') and project.status:
                result += f"- Статус: {project.status}\n"
            if hasattr(project, 'owner') and project.owner:
                result += f"- Владелец: {project.owner}\n"
            if hasattr(project, 'task_count') and project.task_count:
                result += f"- Задач: {project.task_count}\n"
            result += "\n"
        
        return result.strip()
        
    except Exception as e:
        logger.error(f"Error getting projects: {e}")
        return f"Ошибка получения проектов: {format_error(e)}"

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
            return f"Неверный ID задачи: {task_id}"
        
        task = await api.get_task(task_id_int)
        
        result = f"Задача #{task.id}\n\n"
        result += f"Название: {task.name}\n"
        
        if hasattr(task, 'description') and task.description:
            result += f"Описание: {task.description[:200]}{'...' if len(task.description) > 200 else ''}\n"
        
        if hasattr(task, 'status') and task.status:
            result += f"Статус: {task.status}\n"
        
        # Handle both TaskResponse and legacy Task models for assignee
        assignee = None
        if hasattr(task, 'assigner') and task.assigner:
            assignee = getattr(task.assigner, 'name', None)
        elif hasattr(task, 'assignees') and task.assignees and task.assignees.users:
            assignee = task.assignees.users[0].name if task.assignees.users[0].name else "Assigned"
        elif hasattr(task, 'assignee') and task.assignee:
            assignee = task.assignee
        
        if assignee:
            result += f"Исполнитель: {assignee}\n"
        
        if hasattr(task, 'project') and task.project:
            result += f"Проект: {task.project}\n"
        
        if hasattr(task, 'priority') and task.priority:
            result += f"Приоритет: {task.priority}\n"
        
        if hasattr(task, 'deadline') and task.deadline:
            result += f"Срок: {format_date(task.deadline)}\n"
        
        result += f"\nОбновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting task {task_id}: {e}")
        return f"Ошибка получения задачи: {format_error(e)}"

@mcp.resource("contacts://recent")
async def get_recent_contacts() -> str:
    """Список недавно добавленных контактов."""
    try:
        contacts = await api.list_contacts(limit=10)
        
        if not contacts:
            return "Контакты не найдены."
        
        result = f"Недавние контакты ({len(contacts)} шт.)\n\n"

        for i, contact in enumerate(contacts, 1):
            contact_id = getattr(contact, 'id', None) or 0
            contact_name = getattr(contact, 'name', None) or "Без имени"
            result += f"{i}. {contact_name} (#{contact_id})\n"

            email = getattr(contact, 'email', None)
            if email:
                result += f"- Email: {email}\n"

            phone = None
            phones = getattr(contact, 'phones', None)
            if phones and len(phones) > 0 and getattr(phones[0], 'number', None):
                phone = phones[0].number
            if phone:
                result += f"- Телефон: {phone}\n"

            companies = getattr(contact, 'companies', None)
            if companies:
                company_names = [c.name for c in companies if getattr(c, 'name', None)]
                if company_names:
                    result += f"- Компания: {', '.join(company_names)}\n"

            position = getattr(contact, 'position', None)
            if position:
                result += f"- Должность: {position}\n"

            result += "\n"
        
        return result.strip()
        
    except Exception as e:
        logger.error(f"Error getting contacts: {e}")
        return f"Ошибка получения контактов: {format_error(e)}"

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

МЕТРИКИ ДЛЯ ОЦЕНКИ::
• Процент выполненных задач в срок
• Среднее время выполнения задач
• Количество просроченных задач
• Распределение нагрузки по сотрудникам
• Соответствие бюджету (если доступно)

ОСОБОЕ ВНИМАНИЕ:
• Просроченные задачи и их влияние на проект
• Перегруженные сотрудники
• Задачи с высоким приоритетом
• Зависимости между задачами

РЕЗУЛЬТАТ::
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

ПОКАЗАТЕЛИ НЕДЕЛИ::
• Количество завершённых задач
• Количество созданных задач
• Среднее время выполнения задач
• Процент задач, выполненных в срок
• Загрузка сотрудников по проектам
• Общее затраченное время

ДОСТИЖЕНИЯ::
• Основные результаты недели
• Завершённые проекты/этапы
• Решённые проблемы
• Превышенные ожидания

ПРОБЛЕМЫ И РИСКИ:
• Просроченные задачи и их причины
• Перегруженные сотрудники  
• Проблемные проекты
• Технические сложности
• Ресурсные ограничения

ТРЕНДЫ И АНАЛИЗ::
• Сравнение с предыдущей неделей
• Динамика производительности
• Качественные изменения в работе

ПЛАНЫ НА СЛЕДУЮЩУЮ НЕДЕЛЮ::
• Приоритетные задачи и проекты
• Распределение нагрузки
• Необходимые ресурсы
• Планируемые результаты
• Профилактические меры"""

@mcp.prompt()
def plan_sprint(sprint_duration: int = 14) -> str:
    """Шаблон для планирования спринта."""
    return f"""Спланируй спринт продолжительностью {sprint_duration} дней:

ЦЕЛИ СПРИНТА::
1. Определи основные цели и результаты спринта
2. Установи критерии успеха
3. Выяви ключевые метрики для отслеживания

ПЛАНИРОВАНИЕ ЗАДАЧ::
• Проанализируй беклог задач
• Оцени сложность и приоритет каждой задачи
• Распредели задачи между участниками команды
• Учти доступность и загрузку сотрудников
• Определи зависимости между задачами

ВРЕМЕННОЕ ПЛАНИРОВАНИЕ::
• Разбей спринт на итерации (если нужно)
• Запланируй ключевые milestone'ы
• Оставь буферное время для непредвиденных задач
• Учти праздники и отпуска команды

ПРОЦЕССЫ И РИТУАЛЫ::
• Запланируй регулярные синки команды
• Определи процедуры отчётности
• Настрой автоматические уведомления
• Подготовь шаблоны для статус-репортов

МОНИТОРИНГ И КОНТРОЛЬ::
• Определи KPI для отслеживания прогресса
• Настрой дашборды и отчёты
• Запланируй контрольные точки
• Подготовь план корректирующих действий

ИТОГОВЫЙ ПЛАН::
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
    parser = argparse.ArgumentParser(
        description="Planfix MCP Server - интеграция Planfix с Model Context Protocol",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s --account mycompany --api-key abc123
  %(prog)s --debug
  %(prog)s --help

Переменные окружения:
  PLANFIX_ACCOUNT     Название аккаунта Planfix
  PLANFIX_API_KEY     API ключ Planfix
  DEBUG               Включить отладочные логи
        """
    )
    
    parser.add_argument(
        "--account",
        type=str,
        help="Название аккаунта Planfix (можно также задать через PLANFIX_ACCOUNT)"
    )
    
    parser.add_argument(
        "--api-key",
        type=str,
        help="API ключ Planfix (можно также задать через PLANFIX_API_KEY)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Включить отладочные логи"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="Planfix MCP Server 1.0.1"
    )
    
    args = parser.parse_args()
    
    # Применяем аргументы командной строки к конфигурации
    if args.account:
        config.planfix_account = args.account
    if args.api_key:
        config.planfix_api_key = args.api_key
    if args.debug:
        config.debug = True
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        logger.info("Запуск Planfix MCP Server...")
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("Сервер остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise

if __name__ == "__main__":
    main()
