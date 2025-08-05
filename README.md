# Planfix MCP Server

Интеграция системы управления бизнес-процессами [Planfix](https://planfix.com/ru/) с протоколом Model Context Protocol (MCP) для использования с Claude и другими AI-ассистентами.

## Возможности

### 🛠️ Инструменты (Tools)
- **Управление задачами**: создание, поиск, обновление статусов
- **Управление проектами**: создание новых проектов
- **Контакты**: добавление новых контактов в CRM
- **Аналитика**: получение отчётов по времени, финансам, задачам
- **Комментарии**: добавление комментариев к задачам

### 📊 Ресурсы (Resources)
- **Список проектов**: активные проекты с количеством задач
- **Сводка дашборда**: текущее состояние рабочего пространства
- **Детали задач**: подробная информация по конкретной задаче
- **Недавние контакты**: последние добавленные контакты
- **Отчёты**: предварительно сформированные отчёты

### 💡 Промпты (Prompts)
- **Анализ проектов**: шаблон для анализа состояния проекта
- **Еженедельные отчёты**: шаблон для создания отчётов
- **Планирование спринта**: шаблон для планирования задач

## Установка

### Требования
- Python 3.8+
- uv (рекомендуется) или pip
- Аккаунт Planfix с API доступом

### 1. Клонирование и установка зависимостей

```bash
git clone <repository-url>
cd planfix-mcp-server

# С использованием uv (рекомендуется)
uv sync

# Или с pip
pip install -r requirements.txt
```

### 2. Настройка API ключей

Получите API ключи в вашем аккаунте Planfix:
1. Перейдите в Настройки → API
2. Создайте новый API ключ
3. Получите User Key

Создайте файл `.env`:

```bash
cp .env.example .env
```

Заполните `.env` файл:

```env
PLANFIX_ACCOUNT=your-account-name
PLANFIX_API_KEY=your-api-key
PLANFIX_USER_KEY=your-user-key
```

### 3. Тестирование

```bash
# Запуск в режиме разработки
в

# Или прямой запуск
python src/planfix_server.py
```

### 4. Установка в Claude Desktop

```bash
# Автоматическая установка
uv run mcp install src/planfix_server.py --name "Planfix Integration" -f .env

# Или ручная настройка в claude_desktop_config.json
```

## Использование

После установки в Claude Desktop вы сможете:

### Создание задач
```
Создай задачу "Подготовить презентацию" с описанием "Презентация для клиента XYZ" и приоритетом HIGH
```

### Поиск информации
```
Найди все задачи по проекту "Разработка сайта"
```

### Получение аналитики
```
Покажи отчёт по времени за последний месяц
```

### Управление проектами
```
Создай проект "Новая маркетинговая кампания" с описанием "Q1 2024 кампания"
```

## Конфигурация

### Переменные окружения

| Переменная | Описание | Обязательная |
|------------|----------|--------------|
| `PLANFIX_ACCOUNT` | Название вашего аккаунта Planfix | ✅ |
| `PLANFIX_API_KEY` | API ключ | ✅ |
| `PLANFIX_USER_KEY` | Пользовательский ключ | ✅ |
| `PLANFIX_BASE_URL` | Базовый URL (по умолчанию: https://{account}.planfix.ru) | ❌ |
| `DEBUG` | Включить отладочные логи | ❌ |

### Настройка в Claude Desktop

Добавьте в `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "planfix": {
      "command": "python",
      "args": ["/path/to/planfix-mcp-server/src/planfix_server.py"],
      "env": {
        "PLANFIX_ACCOUNT": "your-account",
        "PLANFIX_API_KEY": "your-api-key",
        "PLANFIX_USER_KEY": "your-user-key"
      }
    }
  }
}
```

### Настройка в Cursor

Cursor поддерживает MCP серверы начиная с версии 0.42+. Для подключения:

1. **Откройте настройки Cursor**: `Cmd/Ctrl + ,`

2. **Найдите раздел "MCP Servers"** или добавьте конфигурацию в файл настроек

3. **Добавьте конфигурацию сервера**:

```json

```

4. **Альтернативный способ через .cursorrules**:

Создайте файл `.cursorrules` в корне вашего проекта:

```
MCP Server: Planfix Integration

This project uses a Planfix MCP server for task and project management.

Available tools:
- search_tasks: Find tasks by query, project, assignee, or status
- search_contacts: Search for contacts and companies  
- get_contact_details: Get detailed information about a contact
- list_employees: Get list of employees
- list_files: Get files associated with tasks/projects
- list_comments: Get comments for tasks/projects
- list_reports: Get available reports
- list_processes: Get business processes

Server configuration:
- Command: python /path/to/planfix-mcp/src/planfix_server.py
- Requires PLANFIX_ACCOUNT, PLANFIX_API_KEY, PLANFIX_USER_KEY environment variables

Use these tools to help with project management, task tracking, and CRM operations.
```

5. **Перезапустите Cursor** для применения изменений

6. **Проверьте подключение**: В чате Cursor должны появиться доступные инструменты Planfix

#### Использование в Cursor

После настройки вы можете использовать Planfix прямо в чате Cursor:

```
Найди все активные задачи по проекту "Разработка сайта"
```

```
Покажи детали контакта с ID 123
```

```
Создай отчет по всем просроченным задачам
```

#### Устранение проблем в Cursor

- **Проверьте пути**: Используйте абсолютные пути к файлам
- **Переменные окружения**: Убедитесь, что все API ключи указаны корректно
- **Логи**: Проверьте вывод в консоли разработчика Cursor (`Cmd/Ctrl + Shift + I`)
- **Версия**: Убедитесь, что используете Cursor 0.42 или новее

## Разработка

### Структура проекта

```
planfix-mcp-server/
├── src/
│   ├── planfix_server.py          # Основной MCP сервер
│   ├── planfix_api.py             # API клиент для Planfix
│   ├── config.py                  # Конфигурация
│   └── utils.py                   # Вспомогательные функции
├── tests/
│   ├── test_server.py             # Тесты сервера
│   ├── test_api.py                # Тесты API
│   └── conftest.py                # Конфигурация pytest
├── examples/
│   ├── basic_usage.py             # Примеры использования
│   └── advanced_workflows.py     # Сложные сценарии
├── docs/
│   ├── api_reference.md           # Справочник по API
│   └── troubleshooting.md         # Решение проблем
├── .env.example                   # Пример конфигурации
├── requirements.txt               # Зависимости
├── pyproject.toml                # Конфигурация проекта
└── README.md                      # Документация
```

### Запуск тестов

```bash
# Все тесты
uv run pytest

# С покрытием кода
uv run pytest --cov=src

# Только быстрые тесты
uv run pytest -m "not slow"
```

### Линтинг и форматирование

```bash
# Форматирование кода
uv run ruff format

# Проверка стиля
uv run ruff check

# Проверка типов
uv run mypy src/
```

## Примеры использования

### Автоматизация рабочих процессов

```python
# Создание еженедельного планирования
tasks = await search_tasks(status="active", assignee_id=123)
report = await get_analytics_report("time", "2024-01-01", "2024-01-07")
```

### Интеграция с другими системами

```python
# Синхронизация с внешними сервисами
contact = await add_contact("Новый клиент", "client@example.com")
project = await create_project(f"Проект для {contact.name}")
```

## API Reference

Подробная документация по всем доступным инструментам, ресурсам и промптам находится в [docs/api_reference.md](docs/api_reference.md).

## Устранение неполадок

Общие проблемы и их решения описаны в [docs/troubleshooting.md](docs/troubleshooting.md).

## Лицензия

MIT License - см. [LICENSE](LICENSE) файл.

## Поддержка

- GitHub Issues: для сообщений об ошибках и запросов функций
- MCP Documentation: https://modelcontextprotocol.io/

## Changelog

### v1.0.0 (2024-12-23)
- Первый релиз
- Базовые операции с задачами и проектами
- Интеграция с аналитикой Planfix
- Поддержка управления контактами