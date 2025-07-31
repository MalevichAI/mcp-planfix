#!/usr/bin/env python3
"""
Продвинутые сценарии использования Planfix MCP Server.

Этот файл демонстрирует сложные бизнес-процессы и автоматизацию
с использованием Planfix API.
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Добавляем путь к модулям проекта
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.planfix_api import PlanfixAPI, Task, Project, Contact


class PlanfixWorkflowAutomator:
    """Автоматизатор рабочих процессов Planfix."""
    
    def __init__(self):
        self.api = PlanfixAPI()
    
    async def create_project_with_tasks(
        self, 
        project_name: str, 
        project_description: str,
        task_templates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Создать проект с набором задач по шаблону."""
        
        print(f"🎯 Создание проекта: {project_name}")
        
        # 1. Создаём проект
        project = await self.api.create_project(
            name=project_name,
            description=project_description
        )
        
        print(f"   ✅ Проект создан: ID {project.id}")
        
        # 2. Создаём задачи в проекте
        created_tasks = []
        
        for i, task_template in enumerate(task_templates, 1):
            print(f"   📋 Создание задачи {i}/{len(task_templates)}: {task_template['name']}")
            
            # Вычисляем срок выполнения
            deadline = None
            if task_template.get('days_from_start'):
                deadline = (datetime.now() + timedelta(days=task_template['days_from_start'])).strftime("%Y-%m-%d")
            
            task = await self.api.create_task(
                name=task_template['name'],
                description=task_template.get('description', ''),
                project_id=project.id,
                priority=task_template.get('priority', 'NORMAL'),
                deadline=deadline
            )
            
            created_tasks.append(task)
        
        print(f"   ✅ Создано задач: {len(created_tasks)}")
        
        return {
            'project': project,
            'tasks': created_tasks,
            'summary': f"Проект '{project_name}' создан с {len(created_tasks)} задачами"
        }
    
    async def setup_marketing_campaign(self, campaign_name: str) -> Dict[str, Any]:
        """Настройка маркетинговой кампании с полным циклом задач."""
        
        print(f"📢 Настройка маркетинговой кампании: {campaign_name}")
        
        # Шаблон задач для маркетинговой кампании
        marketing_tasks = [
            {
                'name': 'Исследование целевой аудитории',
                'description': 'Провести анализ целевой аудитории и конкурентов',
                'priority': 'HIGH',
                'days_from_start': 3
            },
            {
                'name': 'Разработка креативной концепции',
                'description': 'Создать креативную концепцию и основные месседжи',
                'priority': 'HIGH',
                'days_from_start': 7
            },
            {
                'name': 'Создание рекламных материалов',
                'description': 'Разработать баннеры, тексты, видеоматериалы',
                'priority': 'NORMAL',
                'days_from_start': 14
            },
            {
                'name': 'Настройка рекламных кампаний',
                'description': 'Настроить кампании в Google Ads, Яндекс.Директ, соцсетях',
                'priority': 'HIGH',
                'days_from_start': 18
            },
            {
                'name': 'Запуск кампании',
                'description': 'Запустить рекламные кампании и начать мониторинг',
                'priority': 'CRITICAL',
                'days_from_start': 21
            },
            {
                'name': 'Мониторинг и оптимизация',
                'description': 'Ежедневный мониторинг показателей и оптимизация',
                'priority': 'HIGH',
                'days_from_start': 22
            },
            {
                'name': 'Анализ результатов',
                'description': 'Подготовка отчёта по результатам кампании',
                'priority': 'NORMAL',
                'days_from_start': 35
            }
        ]
        
        return await self.create_project_with_tasks(
            project_name=f"Маркетинговая кампания: {campaign_name}",
            project_description=f"Полный цикл маркетинговой кампании '{campaign_name}' от исследования до анализа результатов",
            task_templates=marketing_tasks
        )
    
    async def setup_product_development(self, product_name: str) -> Dict[str, Any]:
        """Настройка проекта разработки продукта."""
        
        print(f"🚀 Настройка разработки продукта: {product_name}")
        
        # Шаблон задач для разработки продукта
        development_tasks = [
            {
                'name': 'Сбор и анализ требований',
                'description': 'Провести интервью с заказчиками и проанализировать требования',
                'priority': 'CRITICAL',
                'days_from_start': 5
            },
            {
                'name': 'Техническое планирование',
                'description': 'Создать техническую архитектуру и план разработки',
                'priority': 'HIGH',
                'days_from_start': 10
            },
            {
                'name': 'UI/UX дизайн',
                'description': 'Разработать пользовательский интерфейс и прототипы',
                'priority': 'HIGH',
                'days_from_start': 15
            },
            {
                'name': 'Разработка MVP',
                'description': 'Создать минимально жизнеспособный продукт',
                'priority': 'CRITICAL',
                'days_from_start': 45
            },
            {
                'name': 'Тестирование MVP',
                'description': 'Провести функциональное и нагрузочное тестирование',
                'priority': 'HIGH',
                'days_from_start': 50
            },
            {
                'name': 'Альфа-тестирование',
                'description': 'Провести внутреннее тестирование с командой',
                'priority': 'HIGH',
                'days_from_start': 55
            },
            {
                'name': 'Бета-тестирование',
                'description': 'Запустить бета-тестирование с внешними пользователями',
                'priority': 'HIGH',
                'days_from_start': 65
            },
            {
                'name': 'Доработка по feedback',
                'description': 'Внести изменения на основе отзывов бета-тестеров',
                'priority': 'NORMAL',
                'days_from_start': 75
            },
            {
                'name': 'Подготовка к релизу',
                'description': 'Финальное тестирование и подготовка релиза',
                'priority': 'CRITICAL',
                'days_from_start': 85
            },
            {
                'name': 'Релиз продукта',
                'description': 'Выпуск продукта в продакшн',
                'priority': 'CRITICAL',
                'days_from_start': 90
            }
        ]
        
        return await self.create_project_with_tasks(
            project_name=f"Разработка продукта: {product_name}",
            project_description=f"Полный цикл разработки продукта '{product_name}' от идеи до релиза",
            task_templates=development_tasks
        )
    
    async def client_onboarding_workflow(self, client_name: str, client_email: str) -> Dict[str, Any]:
        """Автоматизированный процесс онбординга клиента."""
        
        print(f"👋 Запуск онбординга клиента: {client_name}")
        
        # 1. Создаём контакт клиента
        contact = await self.api.add_contact(
            name=client_name,
            email=client_email,
            company=f"Компания {client_name}",
            position="Клиент"
        )
        
        print(f"   ✅ Контакт создан: {contact.name}")
        
        # 2. Создаём проект онбординга
        onboarding_tasks = [
            {
                'name': 'Первичный звонок клиенту',
                'description': f'Провести вводный звонок с {client_name} для знакомства',
                'priority': 'HIGH',
                'days_from_start': 1
            },
            {
                'name': 'Анализ потребностей клиента',
                'description': 'Детально изучить потребности и цели клиента',
                'priority': 'HIGH',
                'days_from_start': 2
            },
            {
                'name': 'Подготовка коммерческого предложения',
                'description': 'Создать персонализированное КП для клиента',
                'priority': 'HIGH',
                'days_from_start': 5
            },
            {
                'name': 'Презентация решения',
                'description': 'Провести презентацию предлагаемого решения',
                'priority': 'HIGH',
                'days_from_start': 7
            },
            {
                'name': 'Согласование договора',
                'description': 'Согласовать условия сотрудничества и подписать договор',
                'priority': 'CRITICAL',
                'days_from_start': 10
            },
            {
                'name': 'Техническая интеграция',
                'description': 'Настроить техническую интеграцию и доступы',
                'priority': 'HIGH',
                'days_from_start': 12
            },
            {
                'name': 'Обучение команды клиента',
                'description': 'Провести обучение сотрудников клиента',
                'priority': 'NORMAL',
                'days_from_start': 15
            },
            {
                'name': 'Запуск сотрудничества',
                'description': 'Официально запустить проект с клиентом',
                'priority': 'HIGH',
                'days_from_start': 17
            }
        ]
        
        project_result = await self.create_project_with_tasks(
            project_name=f"Онбординг клиента: {client_name}",
            project_description=f"Процесс введения в работу нового клиента {client_name} ({client_email})",
            task_templates=onboarding_tasks
        )
        
        return {
            'contact': contact,
            'project': project_result['project'],
            'tasks': project_result['tasks'],
            'summary': f"Онбординг клиента '{client_name}' настроен с {len(project_result['tasks'])} задачами"
        }
    
    async def weekly_reporting_automation(self) -> Dict[str, Any]:
        """Автоматизация еженедельной отчётности."""
        
        print("📊 Генерация еженедельного отчёта...")
        
        # Определяем период отчёта (последние 7 дней)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        date_from = start_date.strftime("%Y-%m-%d")
        date_to = end_date.strftime("%Y-%m-%d")
        
        report_data = {}
        
        try:
            # 1. Собираем данные по задачам
            all_tasks = await self.api.search_tasks(status="all")
            active_tasks = await self.api.search_tasks(status="active")
            completed_tasks = await self.api.search_tasks(status="completed")
            
            report_data['tasks'] = {
                'total': len(all_tasks),
                'active': len(active_tasks),
                'completed': len(completed_tasks),
                'completion_rate': round((len(completed_tasks) / len(all_tasks)) * 100, 1) if all_tasks else 0
            }
            
            # 2. Собираем данные по проектам
            projects = await self.api.get_projects()
            active_projects = [p for p in projects if p.status != "COMPLETED"]
            
            report_data['projects'] = {
                'total': len(projects),
                'active': len(active_projects)
            }
            
            # 3. Получаем аналитику по времени
            try:
                time_report = await self.api.get_analytics_report(
                    report_type="time",
                    date_from=date_from,
                    date_to=date_to,
                    group_by="user"
                )
                report_data['time_analytics'] = time_report
            except Exception as e:
                print(f"   ⚠️  Не удалось получить аналитику по времени: {e}")
                report_data['time_analytics'] = None
            
            # 4. Формируем итоговый отчёт
            report_summary = self._format_weekly_report(report_data, date_from, date_to)
            
            print("   ✅ Еженедельный отчёт сформирован")
            return {
                'period': f"{date_from} - {date_to}",
                'data': report_data,
                'summary': report_summary
            }
            
        except Exception as e:
            print(f"   ❌ Ошибка генерации отчёта: {e}")
            return {'error': str(e)}
    
    def _format_weekly_report(self, data: Dict[str, Any], date_from: str, date_to: str) -> str:
        """Форматирование еженедельного отчёта."""
        
        report = f"""
📊 ЕЖЕНЕДЕЛЬНЫЙ ОТЧЁТ
Период: {date_from} - {date_to}

📋 ЗАДАЧИ:
   • Всего задач: {data['tasks']['total']}
   • Активные: {data['tasks']['active']}
   • Завершённые: {data['tasks']['completed']}
   • Процент завершения: {data['tasks']['completion_rate']}%

🎯 ПРОЕКТЫ:
   • Всего проектов: {data['projects']['total']}
   • Активные: {data['projects']['active']}
"""
        
        if data.get('time_analytics'):
            report += "\n⏱️ ВРЕМЯ:\n"
            if data['time_analytics'].get('summary'):
                for key, value in data['time_analytics']['summary'].items():
                    report += f"   • {key}: {value}\n"
        
        return report.strip()
    
    async def handle_overdue_tasks(self) -> Dict[str, Any]:
        """Обработка просроченных задач."""
        
        print("⚠️  Поиск и обработка просроченных задач...")
        
        # Получаем все активные задачи
        active_tasks = await self.api.search_tasks(status="active")
        
        # Находим просроченные задачи
        today = datetime.now().strftime("%Y-%m-%d")
        overdue_tasks = []
        
        for task in active_tasks:
            if task.deadline and task.deadline < today:
                overdue_tasks.append(task)
        
        print(f"   📋 Найдено просроченных задач: {len(overdue_tasks)}")
        
        # Обрабатываем просроченные задачи
        processed_tasks = []
        
        for task in overdue_tasks[:5]:  # Обрабатываем первые 5
            try:
                # Добавляем комментарий о просрочке
                await self.api.add_task_comment(
                    task.id,
                    f"⚠️ ВНИМАНИЕ: Задача просрочена! Срок выполнения был: {task.deadline}"
                )
                
                processed_tasks.append({
                    'task': task,
                    'action': 'comment_added',
                    'message': 'Добавлен комментарий о просрочке'
                })
                
                print(f"   ✅ Обработана задача #{task.id}: {task.name}")
                
            except Exception as e:
                print(f"   ❌ Ошибка обработки задачи #{task.id}: {e}")
        
        return {
            'total_overdue': len(overdue_tasks),
            'processed': len(processed_tasks),
            'tasks': processed_tasks
        }


async def demo_marketing_campaign():
    """Демонстрация настройки маркетинговой кампании."""
    automator = PlanfixWorkflowAutomator()
    
    result = await automator.setup_marketing_campaign("Летняя распродажа 2024")
    print(f"\n✅ {result['summary']}")
    
    return result


async def demo_product_development():
    """Демонстрация настройки разработки продукта."""
    automator = PlanfixWorkflowAutomator()
    
    result = await automator.setup_product_development("CRM система v2.0")
    print(f"\n✅ {result['summary']}")
    
    return result


async def demo_client_onboarding():
    """Демонстрация онбординга клиента."""
    automator = PlanfixWorkflowAutomator()
    
    result = await automator.client_onboarding_workflow(
        client_name="ТехноИнновации",
        client_email="info@technoinnovations.ru"
    )
    print(f"\n✅ {result['summary']}")
    
    return result


async def demo_reporting():
    """Демонстрация автоматической отчётности."""
    automator = PlanfixWorkflowAutomator()
    
    result = await automator.weekly_reporting_automation()
    
    if 'error' not in result:
        print(f"\n📊 Отчёт за период {result['period']}:")
        print(result['summary'])
    
    return result


async def demo_overdue_handling():
    """Демонстрация обработки просроченных задач."""
    automator = PlanfixWorkflowAutomator()
    
    result = await automator.handle_overdue_tasks()
    print(f"\n⚠️  Обработка просроченных задач:")
    print(f"   • Найдено: {result['total_overdue']}")
    print(f"   • Обработано: {result['processed']}")
    
    return result


async def main():
    """Главная функция с продвинутыми примерами."""
    print("🚀 ПРОДВИНУТЫЕ СЦЕНАРИИ PLANFIX MCP SERVER\n")
    print("=" * 70)
    
    # Проверяем наличие необходимых переменных окружения
    required_vars = ["PLANFIX_ACCOUNT", "PLANFIX_API_KEY", "PLANFIX_USER_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Отсутствуют необходимые переменные окружения:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nПожалуйста, настройте .env файл.")
        return
    
    try:
        # Тестируем подключение
        api = PlanfixAPI()
        connection_ok = await api.test_connection()
        
        if not connection_ok:
            print("❌ Не удалось подключиться к Planfix API")
            return
        
        print("✅ Подключение к Planfix API успешно!\n")
        
        # Запускаем продвинутые примеры
        print("📢 1. МАРКЕТИНГОВАЯ КАМПАНИЯ")
        await demo_marketing_campaign()
        
        print("\n" + "─" * 50)
        print("\n🚀 2. РАЗРАБОТКА ПРОДУКТА")
        await demo_product_development()
        
        print("\n" + "─" * 50)
        print("\n👋 3. ОНБОРДИНГ КЛИЕНТА")
        await demo_client_onboarding()
        
        print("\n" + "─" * 50)
        print("\n📊 4. АВТОМАТИЧЕСКАЯ ОТЧЁТНОСТЬ")
        await demo_reporting()
        
        print("\n" + "─" * 50)
        print("\n⚠️  5. ОБРАБОТКА ПРОСРОЧЕННЫХ ЗАДАЧ")
        await demo_overdue_handling()
        
        print("\n" + "=" * 70)
        print("🎉 ВСЕ ПРОДВИНУТЫЕ СЦЕНАРИИ ВЫПОЛНЕНЫ!")
        print("\n💡 Эти примеры показывают, как автоматизировать:")
        print("   • Создание типовых проектов")
        print("   • Бизнес-процессы компании")
        print("   • Отчётность и аналитику")
        print("   • Мониторинг и контроль")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")


if __name__ == "__main__":
    # Загружаем переменные окружения
    from dotenv import load_dotenv
    load_dotenv()
    
    # Запускаем продвинутые примеры
    asyncio.run(main())