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
import sys
from typing import Any, AsyncIterator, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

from .config import config
from .planfix_api import PlanfixAPI, PlanfixError
from .utils import (
    format_date,
    format_error,
    format_task_list,
)

# Configure logging
logging.basicConfig(level=logging.DEBUG if config.debug else logging.INFO)
logger = logging.getLogger(__name__)
api: Optional[PlanfixAPI] = None
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

# Removed create_task - read-only scope

@mcp.tool()
async def search_tasks(
    query: str = "",
    project_id: Optional[int] = None,
    assignee_id: Optional[int] = None,
    status: str = "active",
    limit: int = 20
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
        logger.info(f"Поиск задач: query='{query}', status='{status}'")
        
        # Search tasks via API
        if api is None:
            return "❌ API не инициализирован"
            
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
            
        logger.info(f"Найдено задач: {len(tasks)}")
        return result
        
    except PlanfixError as e:
        error_msg = format_error(e, "поиске задач")
        logger.error(f"Ошибка поиска задач: {e}")
        return error_msg
    except Exception as e:
        error_msg = format_error(e, "поиске задач")
        logger.error(f"Unexpected error searching tasks: {e}")
        return error_msg

# Removed update_task_status, add_task_comment, create_project, add_contact, get_analytics_report - read-only scope

# ============================================================================
# РЕСУРСЫ (RESOURCES) - Данные для чтения LLM
# ============================================================================

@mcp.resource("dashboard://summary")
async def get_dashboard_summary() -> str:
    """Сводка по рабочему пространству Planfix."""
    try:
        if api is None:
            return "❌ API не инициализирован"
            
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
        if api is None:
            return "❌ API не инициализирован"
            
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
        if api is None:
            return "❌ API не инициализирован"
            
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
        if api is None:
            return "❌ API не инициализирован"
            
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
    """Шаблон для анализа состояния проекта (только просмотр данных)."""
    return f"""Проанализируй текущее состояние проекта "{project_name}" в Planfix:

🔍 **АНАЛИЗ ПРОЕКТА (ПРОСМОТР ДАННЫХ):**
1. Найди проект по названию используя поиск
2. Получи список всех задач проекта
3. Проанализируй статусы и сроки задач
4. Оцени распределение нагрузки
5. Выяви потенциальные проблемы

📊 **ДОСТУПНЫЕ ДАННЫЕ:**
• Список задач и их статусы
• Информация о проектах
• Детали по конкретным задачам
• Контакты и исполнители

⚠️ **ОСОБОЕ ВНИМАНИЕ:**
• Просроченные задачи
• Задачи без исполнителей
• Задачи с высоким приоритетом
• Длительные задачи без обновлений

📋 **РЕЗУЛЬТАТ:**
Подготовь аналитический отчёт на основе доступных данных:
• Общая статистика по проекту
• Выявленные проблемы
• Рекомендации на основе анализа
• Предложения по мониторингу"""

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
def analyze_sprint_readiness(sprint_duration: int = 14) -> str:
    """Шаблон для анализа готовности к спринту (только анализ данных)."""
    return f"""Проанализируй готовность к спринту продолжительностью {sprint_duration} дней на основе данных Planfix:

🔍 **АНАЛИЗ ТЕКУЩЕГО СОСТОЯНИЯ:**
1. Получи список активных задач команды
2. Проанализируй загрузку участников
3. Оцени количество незавершённых задач
4. Изучи статистику выполнения задач

📊 **ДАННЫЕ ДЛЯ АНАЛИЗА:**
• Активные задачи и их статусы
• Просроченные задачи
• Распределение задач по исполнителям
• Проекты в работе

⚠️ **РИСКИ И ПРЕПЯТСТВИЯ:**
• Перегруженные участники команды
• Много просроченных задач
• Задачи без четких исполнителей
• Блокирующие задачи

📋 **РЕКОМЕНДАЦИИ:**
На основе анализа данных подготовь:
• Оценку готовности команды к спринту
• Выявленные риски и проблемы
• Рекомендации по планированию нагрузки
• Предложения по приоритизации задач

💡 **ВАЖНО:** Этот анализ основан только на просмотре данных Planfix. 
Для создания задач и изменения статусов используйте интерфейс Planfix."""

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
