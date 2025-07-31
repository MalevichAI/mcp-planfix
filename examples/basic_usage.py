#!/usr/bin/env python3
"""
Базовые примеры использования Planfix MCP Server.

Этот файл демонстрирует основные возможности интеграции с Planfix API
через MCP сервер.
"""

import asyncio
import os
from datetime import datetime, timedelta

# Добавляем путь к модулям проекта
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.planfix_api import PlanfixAPI


async def basic_task_operations():
    """Базовые операции с задачами."""
    print("=== БАЗОВЫЕ ОПЕРАЦИИ С ЗАДАЧАМИ ===\n")
    
    api = PlanfixAPI()
    
    try:
        # 1. Создание новой задачи
        print("1. Создание задачи...")
        task = await api.create_task(
            name="Подготовить квартальный отчёт",
            description="Собрать данные за Q4 2024 и подготовить презентацию для руководства",
            priority="HIGH",
            deadline=(datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        )
        print(f"   ✅ Создана задача ID {task.id}: {task.name}")
        
        # 2. Поиск задач
        print("\n2. Поиск активных задач...")
        tasks = await api.search_tasks(status="active")
        print(f"   📋 Найдено активных задач: {len(tasks)}")
        
        for i, task in enumerate(tasks[:3], 1):  # Показываем первые 3
            print(f"   {i}. {task.name} (#{task.id}) - {task.status}")
        
        # 3. Получение детальной информации о задаче
        if tasks:
            print(f"\n3. Детали задачи #{tasks[0].id}...")
            task_details = await api.get_task(tasks[0].id)
            print(f"   📝 Название: {task_details.name}")
            print(f"   🔄 Статус: {task_details.status}")
            print(f"   👤 Исполнитель: {task_details.assignee or 'Не назначен'}")
            print(f"   🎯 Проект: {task_details.project or 'Без проекта'}")
        
        # 4. Обновление статуса задачи
        if tasks:
            print(f"\n4. Обновление статуса задачи #{tasks[0].id}...")
            success = await api.update_task_status(
                tasks[0].id, 
                "IN_WORK", 
                "Начал работу над задачей"
            )
            if success:
                print("   ✅ Статус обновлён успешно")
        
        # 5. Добавление комментария
        if tasks:
            print(f"\n5. Добавление комментария к задаче #{tasks[0].id}...")
            success = await api.add_task_comment(
                tasks[0].id,
                "Собрал первичные данные, приступаю к анализу"
            )
            if success:
                print("   ✅ Комментарий добавлен")
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")


async def project_management_example():
    """Пример управления проектами."""
    print("\n\n=== УПРАВЛЕНИЕ ПРОЕКТАМИ ===\n")
    
    api = PlanfixAPI()
    
    try:
        # 1. Создание нового проекта
        print("1. Создание проекта...")
        project = await api.create_project(
            name="Запуск мобильного приложения",
            description="Разработка и запуск мобильного приложения для клиентов компании"
        )
        print(f"   ✅ Создан проект ID {project.id}: {project.name}")
        
        # 2. Получение списка проектов
        print("\n2. Список всех проектов...")
        projects = await api.get_projects()
        print(f"   🎯 Всего проектов: {len(projects)}")
        
        for i, project in enumerate(projects[:5], 1):  # Показываем первые 5
            print(f"   {i}. {project.name} (#{project.id})")
            print(f"      └─ Статус: {project.status or 'Не указан'}")
            print(f"      └─ Задач: {project.task_count}")
        
        # 3. Создание задач в рамках проекта
        if projects:
            project_id = projects[0].id
            print(f"\n3. Создание задач для проекта #{project_id}...")
            
            # Создаём несколько задач для проекта
            tasks_to_create = [
                {
                    "name": "Анализ требований",
                    "description": "Провести анализ требований к мобильному приложению",
                    "priority": "HIGH"
                },
                {
                    "name": "Дизайн интерфейса",
                    "description": "Создать дизайн пользовательского интерфейса",
                    "priority": "NORMAL"
                },
                {
                    "name": "Разработка MVP",
                    "description": "Разработать минимально жизнеспособный продукт",
                    "priority": "HIGH"
                }
            ]
            
            for task_info in tasks_to_create:
                task = await api.create_task(
                    name=task_info["name"],
                    description=task_info["description"],
                    project_id=project_id,
                    priority=task_info["priority"]
                )
                print(f"   ✅ Создана задача: {task.name}")
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")


async def contact_management_example():
    """Пример управления контактами."""
    print("\n\n=== УПРАВЛЕНИЕ КОНТАКТАМИ ===\n")
    
    api = PlanfixAPI()
    
    try:
        # 1. Добавление новых контактов
        print("1. Добавление контактов...")
        
        contacts_to_add = [
            {
                "name": "Анна Смирнова",
                "email": "anna.smirnova@company.ru",
                "phone": "+7-495-123-45-67",
                "company": "ООО «Инновационные решения»",
                "position": "Руководитель проектов"
            },
            {
                "name": "Петр Козлов",
                "email": "p.kozlov@techstart.com",
                "phone": "+7-812-987-65-43",
                "company": "ТехСтарт",
                "position": "CTO"
            },
            {
                "name": "Елена Морозова",
                "email": "elena.morozova@consulting.ru",
                "phone": "+7-903-555-66-77",
                "company": "БизнесКонсалт",
                "position": "Бизнес-аналитик"
            }
        ]
        
        for contact_info in contacts_to_add:
            contact = await api.add_contact(
                name=contact_info["name"],
                email=contact_info["email"],
                phone=contact_info["phone"],
                company=contact_info["company"],
                position=contact_info["position"]
            )
            print(f"   ✅ Добавлен контакт: {contact.name} ({contact.company})")
        
        # 2. Получение списка контактов
        print("\n2. Недавно добавленные контакты...")
        contacts = await api.get_contacts(limit=10)
        print(f"   👥 Загружено контактов: {len(contacts)}")
        
        for i, contact in enumerate(contacts, 1):
            print(f"   {i}. {contact.name}")
            if contact.email:
                print(f"      └─ 📧 {contact.email}")
            if contact.company:
                print(f"      └─ 🏢 {contact.company}")
            if contact.position:
                print(f"      └─ 💼 {contact.position}")
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")


async def analytics_example():
    """Пример работы с аналитикой."""
    print("\n\n=== АНАЛИТИКА И ОТЧЁТЫ ===\n")
    
    api = PlanfixAPI()
    
    try:
        # Подготавливаем даты для отчётов
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        date_from = start_date.strftime("%Y-%m-%d")
        date_to = end_date.strftime("%Y-%m-%d")
        
        # 1. Отчёт по времени
        print("1. Получение отчёта по времени...")
        time_report = await api.get_analytics_report(
            report_type="time",
            date_from=date_from,
            date_to=date_to,
            group_by="user"
        )
        
        print(f"   📊 Отчёт по времени за период {time_report['period']}")
        print(f"   📈 Группировка: {time_report['group_by']}")
        
        if time_report.get('summary'):
            print("   💡 Итоговые показатели:")
            for key, value in time_report['summary'].items():
                print(f"      └─ {key}: {value}")
        
        if time_report.get('data'):
            print("   📋 Детальные данные:")
            for i, item in enumerate(time_report['data'][:5], 1):
                print(f"      {i}. {item.get('name', 'N/A')}: {item.get('value', 'N/A')}")
        
        # 2. Отчёт по задачам
        print(f"\n2. Получение отчёта по задачам...")
        tasks_report = await api.get_analytics_report(
            report_type="tasks",
            date_from=date_from,
            date_to=date_to,
            group_by="project"
        )
        
        print(f"   📊 Отчёт по задачам за период {tasks_report['period']}")
        
        if tasks_report.get('data'):
            print("   📋 Задачи по проектам:")
            for i, item in enumerate(tasks_report['data'][:5], 1):
                print(f"      {i}. {item.get('name', 'N/A')}: {item.get('value', 'N/A')}")
                
    except Exception as e:
        print(f"❌ Ошибка получения аналитики: {e}")


async def search_and_filter_example():
    """Пример поиска и фильтрации."""
    print("\n\n=== ПОИСК И ФИЛЬТРАЦИЯ ===\n")
    
    api = PlanfixAPI()
    
    try:
        # 1. Поиск задач по ключевым словам
        print("1. Поиск задач по названию...")
        search_queries = ["отчёт", "анализ", "презентация"]
        
        for query in search_queries:
            tasks = await api.search_tasks(query=query, status="all")
            print(f"   🔍 По запросу '{query}': найдено {len(tasks)} задач")
            
            for task in tasks[:2]:  # Показываем первые 2
                print(f"      └─ {task.name} (#{task.id})")
        
        # 2. Фильтрация по статусу
        print("\n2. Фильтрация задач по статусу...")
        statuses = ["active", "completed"]
        
        for status in statuses:
            tasks = await api.search_tasks(status=status)
            print(f"   📊 Задач со статусом '{status}': {len(tasks)}")
        
        # 3. Комбинированный поиск
        print("\n3. Комбинированный поиск...")
        projects = await api.get_projects()
        
        if projects:
            project_id = projects[0].id
            tasks = await api.search_tasks(
                query="",
                project_id=project_id,
                status="active"
            )
            print(f"   🎯 Активных задач в проекте #{project_id}: {len(tasks)}")
            
            for task in tasks[:3]:
                print(f"      └─ {task.name}")
                print(f"         Исполнитель: {task.assignee or 'Не назначен'}")
                print(f"         Приоритет: {task.priority or 'Обычный'}")
                
    except Exception as e:
        print(f"❌ Ошибка поиска: {e}")


async def main():
    """Главная функция с примерами."""
    print("🚀 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ PLANFIX MCP SERVER\n")
    print("=" * 60)
    
    # Проверяем наличие необходимых переменных окружения
    required_vars = ["PLANFIX_ACCOUNT", "PLANFIX_API_KEY", "PLANFIX_USER_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Отсутствуют необходимые переменные окружения:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nПожалуйста, настройте .env файл или переменные окружения.")
        return
    
    try:
        # Тестируем подключение
        api = PlanfixAPI()
        connection_ok = await api.test_connection()
        
        if not connection_ok:
            print("❌ Не удалось подключиться к Planfix API")
            print("Проверьте настройки в .env файле")
            return
        
        print("✅ Подключение к Planfix API успешно!\n")
        
        # Запускаем примеры
        await basic_task_operations()
        await project_management_example()
        await contact_management_example()
        await analytics_example()
        await search_and_filter_example()
        
        print("\n" + "=" * 60)
        print("🎉 ВСЕ ПРИМЕРЫ ВЫПОЛНЕНЫ УСПЕШНО!")
        print("\n💡 Советы:")
        print("   • Используйте эти примеры как основу для своих скриптов")
        print("   • Адаптируйте под свои бизнес-процессы")
        print("   • Добавляйте обработку ошибок для продакшена")
        print("   • Изучите документацию Planfix API для дополнительных возможностей")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")


if __name__ == "__main__":
    # Загружаем переменные окружения
    from dotenv import load_dotenv
    load_dotenv()
    
    # Запускаем примеры
    asyncio.run(main())