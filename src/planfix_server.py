#!/usr/bin/env python3
"""
Planfix MCP Server

Интеграция системы управления бизнес-процессами Planfix с протоколом Model Context Protocol (MCP)
для использования с Claude и другими AI-ассистентами.

Автор: Your Name
Версия: 1.0.0
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, AsyncIterator, Dict, List, Optional

from mcp.server.fastmcp import Context, FastMCP

from .config import config
from .planfix_api import PlanfixError, api
from .utils import (
    format_analytics_report,
    format_date,
    format_error,
    format_task_list,
    validate_priority,
    validate_status,
)

# Configure logging
logging.basicConfig(level=logging.DEBUG if config.debug else logging.INFO)
logger = logging.getLogger(__name__)

# Lifespan context for server initialization
@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """Управление жизненным циклом сервера."""
    logger.info("🚀 Запуск Planfix MCP Server...")
    
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
async def create_task(
    name: str,
    description: str = "",
    project_id: Optional[int] = None,
    assignee_id: Optional[int] = None,
    priority: str = "NORMAL",
    deadline: Optional[str] = None,
    ctx: Context = None
) -> str:
    """Создать новую задачу в Planfix.
    
    Args:
        name: Название задачи (обязательно)
        description: Подробное описание задачи
        project_id: ID проекта для привязки задачи
        assignee_id: ID сотрудника-исполнителя
        priority: Приоритет задачи (LOW, NORMAL, HIGH, CRITICAL)
        deadline: Срок выполнения в формате YYYY-MM-DD
        
    Returns:
        Сообщение о результате создания задачи
        
    Example:
        create_task("Подготовить презентацию", "Презентация для клиента XYZ", priority="HIGH")
    """
    try:
        ctx.info(f"Создание задачи: {name}")
        
        # Validate priority
        priority = validate_priority(priority)
        
        # Create task via API
        task = await api.create_task(
            name=name,
            description=description,
            project_id=project_id,
            assignee_id=assignee_id,
            priority=priority,
            deadline=deadline
        )
        
        result = f"✅ **Задача создана успешно!**\n\n"
        result += f"📋 **ID:** {task.id}\n"
        result += f"📝 **Название:** {task.name}\n"
        result += f"⚡ **Приоритет:** {task.priority}\n"
        
        if task.deadline:
            result += f"⏰ **Срок:** {format_date(task.deadline)}\n"
        
        if project_id:
            result += f"🎯 **Проект:** ID {project_id}\n"
            
        if assignee_id:
            result += f"👤 **Исполнитель:** ID {assignee_id}\n"
            
        ctx.info(f"Задача {task.id} создана успешно")
        return result
        
    except PlanfixError as e:
        error_msg = format_error(e, "создании задачи")
        ctx.error(f"Ошибка создания задачи: {e}")
        return error_msg
    except Exception as e:
        error_msg = format_error(e, "создании задачи")
        logger.error(f"Unexpected error creating task: {e}")
        return error_msg

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
        ctx.info(f"Поиск задач: query='{query}', status='{status}'")
        
        # Search tasks via API
        tasks = await api.search_tasks(
            query=query,
            project_id=project_id,
            assignee_id=assignee_id,
            status=status
        )
        
        # Limit results
        if limit and len(tasks) > limit:
            tasks = tasks[:limit]
        
        # Format and return results
        result = format_task_list(tasks)
        
        if len(tasks) >= limit:
            result += f"\n\n💡 Показаны первые {limit} результатов. Уточните поиск для более точных результатов."
            
        ctx.info(f"Найдено задач: {len(tasks)}")
        return result
        
    except PlanfixError as e:
        error_msg = format_error(e, "поиске задач")
        ctx.error(f"Ошибка поиска задач: {e}")
        return error_msg
    except Exception as e:
        error_msg = format_error(e, "поиске задач")
        logger.error(f"Unexpected error searching tasks: {e}")
        return error_msg

@mcp.tool()
async def update_task_status(
    task_id: int,
    status: str,
    comment: str = "",
    ctx: Context = None
) -> str:
    """Обновить статус задачи.
    
    Args:
        task_id: ID задачи для обновления
        status: Новый статус (NEW, IN_WORK, COMPLETED, REJECTED, PAUSED)
        comment: Комментарий к изменению статуса
        
    Returns:
        Сообщение о результате обновления
        
    Example:
        update_task_status(123, "COMPLETED", "Задача выполнена в срок")
    """
    try:
        ctx.info(f"Обновление статуса задачи {task_id}: {status}")
        
        # Validate status
        status = validate_status(status)
        
        # Update via API
        success = await api.update_task_status(task_id, status, comment)
        
        if success:
            result = f"✅ **Статус задачи обновлён!**\n\n"
            result += f"📋 **Задача ID:** {task_id}\n"
            result += f"🔄 **Новый статус:** {status}\n"
            
            if comment:
                result += f"💬 **Комментарий:** {comment}\n"
                
            ctx.info(f"Статус задачи {task_id} обновлён на {status}")
            return result
        else:
            return f"❌ Не удалось обновить статус задачи {task_id}"
            
    except PlanfixError as e:
        error_msg = format_error(e, "обновлении статуса задачи")
        ctx.error(f"Ошибка обновления статуса: {e}")
        return error_msg
    except Exception as e:
        error_msg = format_error(e, "обновлении статуса задачи")
        logger.error(f"Unexpected error updating task status: {e}")
        return error_msg

@mcp.tool()
async def add_task_comment(
    task_id: int,
    comment: str,
    ctx: Context = None
) -> str:
    """Добавить комментарий к задаче.
    
    Args:
        task_id: ID задачи
        comment: Текст комментария
        
    Returns:
        Сообщение о результате
        
    Example:
        add_task_comment(123, "Обновил техническое задание")
    """
    try:
        ctx.info(f"Добавление комментария к задаче {task_id}")
        
        success = await api.add_task_comment(task_id, comment)
        
        if success:
            result = f"✅ **Комментарий добавлен!**\n\n"
            result += f"📋 **Задача ID:** {task_id}\n"
            result += f"💬 **Комментарий:** {comment[:100]}{'...' if len(comment) > 100 else ''}\n"
            
            ctx.info(f"Комментарий добавлен к задаче {task_id}")
            return result
        else:
            return f"❌ Не удалось добавить комментарий к задаче {task_id}"
            
    except PlanfixError as e:
        error_msg = format_error(e, "добавлении комментария")
        ctx.error(f"Ошибка добавления комментария: {e}")
        return error_msg
    except Exception as e:
        error_msg = format_error(e, "добавлении комментария")
        logger.error(f"Unexpected error adding comment: {e}")
        return error_msg

@mcp.tool()
async def create_project(
    name: str,
    description: str = "",
    owner_id: Optional[int] = None,
    client_id: Optional[int] = None,
    ctx: Context = None
) -> str:
    """Создать новый проект в Planfix.
    
    Args:
        name: Название проекта (обязательно)
        description: Описание проекта
        owner_id: ID владельца проекта
        client_id: ID клиента
        
    Returns:
        Сообщение о результате создания проекта
        
    Example:
        create_project("Новая маркетинговая кампания", "Q1 2024 кампания")
    """
    try:
        ctx.info(f"Создание проекта: {name}")
        
        # Create project via API
        project = await api.create_project(
            name=name,
            description=description,
            owner_id=owner_id,
            client_id=client_id
        )
        
        result = f"✅ **Проект создан успешно!**\n\n"
        result += f"🎯 **ID:** {project.id}\n"
        result += f"📝 **Название:** {project.name}\n"
        
        if description:
            result += f"📄 **Описание:** {description[:100]}{'...' if len(description) > 100 else ''}\n"
            
        if owner_id:
            result += f"👤 **Владелец:** ID {owner_id}\n"
            
        if client_id:
            result += f"🏢 **Клиент:** ID {client_id}\n"
            
        ctx.info(f"Проект {project.id} создан успешно")
        return result
        
    except PlanfixError as e:
        error_msg = format_error(e, "создании проекта")
        ctx.error(f"Ошибка создания проекта: {e}")
        return error_msg
    except Exception as e:
        error_msg = format_error(e, "создании проекта")
        logger.error(f"Unexpected error creating project: {e}")
        return error_msg

@mcp.tool()
async def add_contact(
    name: str,
    email: str = "",
    phone: str = "",
    company: str = "",
    position: str = "",
    ctx: Context = None
) -> str:
    """Добавить новый контакт в Planfix.
    
    Args:
        name: Имя контакта (обязательно)
        email: Email адрес
        phone: Номер телефона
        company: Название компании
        position: Должность
        
    Returns:
        Сообщение о результате
        
    Example:
        add_contact("Иван Петров", "ivan@company.com", "+7-999-123-45-67", "ООО Компания", "Менеджер")
    """
    try:
        ctx.info(f"Добавление контакта: {name}")
        
        # Add contact via API
        contact = await api.add_contact(
            name=name,
            email=email,
            phone=phone,
            company=company,
            position=position
        )
        
        result = f"✅ **Контакт добавлен успешно!**\n\n"
        result += f"👤 **ID:** {contact.id}\n"
        result += f"📝 **Имя:** {contact.name}\n"
        
        if email:
            result += f"📧 **Email:** {email}\n"
        if phone:
            result += f"📞 **Телефон:** {phone}\n"
        if company:
            result += f"🏢 **Компания:** {company}\n"
        if position:
            result += f"💼 **Должность:** {position}\n"
            
        ctx.info(f"Контакт {contact.id} добавлен успешно")
        return result
        
    except PlanfixError as e:
        error_msg = format_error(e, "добавлении контакта")
        ctx.error(f"Ошибка добавления контакта: {e}")
        return error_msg
    except Exception as e:
        error_msg = format_error(e, "добавлении контакта")
        logger.error(f"Unexpected error adding contact: {e}")
        return error_msg

@mcp.tool()
async def get_analytics_report(
    report_type: str,
    period_start: str,
    period_end: str,
    group_by: str = "user",
    ctx: Context = None
) -> str:
    """Получить аналитический отчёт из Planfix.
    
    Args:
        report_type: Тип отчёта (time, finance, tasks)
        period_start: Начало периода в формате YYYY-MM-DD
        period_end: Конец периода в формате YYYY-MM-DD
        group_by: Группировка данных (user, project, task_type)
        
    Returns:
        Отформатированный аналитический отчёт
        
    Example:
        get_analytics_report("time", "2024-01-01", "2024-01-31", "user")
    """
    try:
        ctx.info(f"Получение отчёта: {report_type} за {period_start} - {period_end}")
        
        # Get report via API
        report_data = await api.get_analytics_report(
            report_type=report_type,
            date_from=period_start,
            date_to=period_end,
            group_by=group_by
        )
        
        # Format report
        result = format_analytics_report(report_data)
        
        ctx.info(f"Отчёт {report_type} сформирован")
        return result
        
    except PlanfixError as e:
        error_msg = format_error(e, "получении отчёта")
        ctx.error(f"Ошибка получения отчёта: {e}")
        return error_msg
    except Exception as e:
        error_msg = format_error(e, "получении отчёта")
        logger.error(f"Unexpected error getting report: {e}")
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
                          if task.deadline and task.deadline < datetime.now().strftime("%Y-%m-%d"))
        
        # Get completed tasks today (mock data for now)
        completed_today = 8  # This would be a real API call
        
        result = f"📊 **Сводка Planfix** на {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        
        result += "📋 **ЗАДАЧИ:**\n"
        result += f"   └─ Активные: {active_count}\n"
        result += f"   └─ Просрочены: {overdue_count}\n"
        result += f"   └─ Завершены сегодня: {completed_today}\n\n"
        
        result += "🎯 **ПРОЕКТЫ:**\n"
        result += f"   └─ Всего проектов: {len(projects)}\n"
        active_projects = [p for p in projects if p.status != "COMPLETED"]
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
            if project.status:
                result += f"   └─ Статус: {project.status}\n"
            if project.owner:
                result += f"   └─ Владелец: {project.owner}\n"
            if project.task_count:
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
        task_id_int = int(task_id)
        task = await api.get_task(task_id_int)
        
        result = f"📋 **Задача #{task.id}**\n\n"
        result += f"📝 **Название:** {task.name}\n"
        
        if task.description:
            result += f"📄 **Описание:** {task.description[:200]}{'...' if len(task.description) > 200 else ''}\n"
        
        if task.status:
            result += f"🔄 **Статус:** {task.status}\n"
        
        if task.assignee:
            result += f"👤 **Исполнитель:** {task.assignee}\n"
        
        if task.project:
            result += f"🎯 **Проект:** {task.project}\n"
        
        if task.priority:
            result += f"⚡ **Приоритет:** {task.priority}\n"
        
        if task.deadline:
            result += f"⏰ **Срок:** {format_date(task.deadline)}\n"
        
        result += f"\n🕒 **Обновлено:** {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        
        return result
        
    except ValueError:
        return f"❌ Неверный ID задачи: {task_id}"
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
    try:
        logger.info("🚀 Запуск Planfix MCP Server...")
        mcp.run()
    except KeyboardInterrupt:
        logger.info("👋 Сервер остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        raise

if __name__ == "__main__":
    main()