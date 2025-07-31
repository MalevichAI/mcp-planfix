"""Tests for utility functions."""

import pytest
from unittest.mock import Mock
from datetime import datetime

from src.utils import (
    format_task_list, format_date, format_project_list, format_analytics_report,
    validate_priority, validate_status, safe_get, truncate_text, format_error
)


class TestFormatters:
    """Test formatting functions."""
    
    def test_format_task_list_empty(self):
        """Test formatting empty task list."""
        result = format_task_list([])
        assert result == "Задачи не найдены."
    
    def test_format_task_list_single_task(self):
        """Test formatting single task."""
        tasks = [
            {
                "id": 123,
                "name": "Test Task",
                "status": "В работе",
                "assignee": "Иван Петров",
                "project": "Тестовый проект",
                "deadline": "2024-12-31"
            }
        ]
        
        result = format_task_list(tasks)
        
        assert "📋 Найдено задач: 1" in result
        assert "**Test Task** (#123)" in result
        assert "Статус: В работе" in result
        assert "Исполнитель: Иван Петров" in result
        assert "Проект: Тестовый проект" in result
        assert "31.12.2024" in result
    
    def test_format_task_list_multiple_tasks(self):
        """Test formatting multiple tasks."""
        tasks = [
            {
                "id": 123,
                "name": "Task 1",
                "status": "Новая",
                "assignee": "Пользователь 1",
                "project": "Проект 1",
                "deadline": None
            },
            {
                "id": 124,
                "name": "Task 2",
                "status": "Завершена",
                "assignee": "Пользователь 2",
                "project": "Проект 2",
                "deadline": "2024-01-15"
            }
        ]
        
        result = format_task_list(tasks)
        
        assert "📋 Найдено задач: 2" in result
        assert "1. 📌 **Task 1**" in result
        assert "2. 📌 **Task 2**" in result
        assert "15.01.2024" in result
    
    def test_format_date_iso_with_time(self):
        """Test formatting ISO date with time."""
        result = format_date("2024-12-31T15:30:00Z")
        assert "31.12.2024 15:30" in result
    
    def test_format_date_date_only(self):
        """Test formatting date only."""
        result = format_date("2024-12-31")
        assert result == "31.12.2024"
    
    def test_format_date_none(self):
        """Test formatting None date."""
        result = format_date(None)
        assert result == "Не указано"
    
    def test_format_date_empty_string(self):
        """Test formatting empty date."""
        result = format_date("")
        assert result == "Не указано"
    
    def test_format_date_invalid(self):
        """Test formatting invalid date."""
        result = format_date("invalid-date")
        assert result == "invalid-date"
    
    def test_format_project_list_empty(self):
        """Test formatting empty project list."""
        result = format_project_list([])
        assert result == "Проекты не найдены."
    
    def test_format_project_list_with_projects(self):
        """Test formatting project list."""
        projects = [
            {
                "id": 456,
                "name": "Project 1",
                "status": "Активный",
                "taskCount": 5,
                "owner": "Руководитель"
            },
            {
                "id": 457,
                "name": "Project 2",
                "status": "Завершён",
                "taskCount": 0,
                "owner": "Менеджер"
            }
        ]
        
        result = format_project_list(projects)
        
        assert "🎯 Найдено проектов: 2" in result
        assert "**Project 1** (#456)" in result
        assert "Задач: 5" in result
        assert "Владелец: Руководитель" in result
    
    def test_format_analytics_report(self):
        """Test formatting analytics report."""
        report_data = {
            "report_type": "time",
            "period": "2024-01-01 - 2024-01-31",
            "data": [
                {"name": "Иван", "value": "40 часов"},
                {"name": "Мария", "value": "35 часов"}
            ],
            "summary": {
                "total_time": "75 часов",
                "average": "37.5 часов"
            }
        }
        
        result = format_analytics_report(report_data)
        
        assert "📊 **TIME** за период 2024-01-01 - 2024-01-31" in result
        assert "📈 **ИТОГО:**" in result
        assert "total_time: 75 часов" in result
        assert "📋 **ДЕТАЛИ:**" in result
        assert "1. Иван: 40 часов" in result
        assert "2. Мария: 35 часов" in result


class TestValidators:
    """Test validation functions."""
    
    def test_validate_priority_valid(self):
        """Test validating valid priorities."""
        assert validate_priority("LOW") == "LOW"
        assert validate_priority("normal") == "NORMAL"
        assert validate_priority("High") == "HIGH"
        assert validate_priority("CRITICAL") == "CRITICAL"
    
    def test_validate_priority_invalid(self):
        """Test validating invalid priority."""
        result = validate_priority("INVALID")
        assert result == "NORMAL"
    
    def test_validate_status_valid(self):
        """Test validating valid statuses."""
        assert validate_status("NEW") == "NEW"
        assert validate_status("in_work") == "IN_WORK"
        assert validate_status("completed") == "COMPLETED"
    
    def test_validate_status_custom(self):
        """Test validating custom status."""
        result = validate_status("CUSTOM_STATUS")
        assert result == "CUSTOM_STATUS"


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_safe_get_single_key(self):
        """Test safe_get with single key."""
        data = {"key": "value"}
        result = safe_get(data, "key")
        assert result == "value"
    
    def test_safe_get_nested_keys(self):
        """Test safe_get with nested keys."""
        data = {"level1": {"level2": {"level3": "value"}}}
        result = safe_get(data, "level1", "level2", "level3")
        assert result == "value"
    
    def test_safe_get_missing_key(self):
        """Test safe_get with missing key."""
        data = {"key": "value"}
        result = safe_get(data, "missing", default="default")
        assert result == "default"
    
    def test_safe_get_none_data(self):
        """Test safe_get with None data."""
        result = safe_get(None, "key", default="default")
        assert result == "default"
    
    def test_truncate_text_short(self):
        """Test truncating short text."""
        text = "Short text"
        result = truncate_text(text, 50)
        assert result == "Short text"
    
    def test_truncate_text_long(self):
        """Test truncating long text."""
        text = "This is a very long text that needs to be truncated"
        result = truncate_text(text, 20)
        assert result == "This is a very lo..."
        assert len(result) == 20
    
    def test_truncate_text_exact_length(self):
        """Test truncating text at exact length."""
        text = "Exactly twenty chars"
        result = truncate_text(text, 20)
        assert result == "Exactly twenty chars"


class TestErrorFormatting:
    """Test error formatting functions."""
    
    def test_format_error_auth(self):
        """Test formatting authentication error."""
        error = Exception("401 Unauthorized")
        result = format_error(error)
        assert "авторизации" in result
        assert "API ключи" in result
    
    def test_format_error_forbidden(self):
        """Test formatting forbidden error."""
        error = Exception("403 Forbidden access")
        result = format_error(error)
        assert "Доступ запрещён" in result
    
    def test_format_error_not_found(self):
        """Test formatting not found error.""" 
        error = Exception("404 Not found")
        result = format_error(error)
        assert "не найден" in result
    
    def test_format_error_timeout(self):
        """Test formatting timeout error."""
        error = Exception("Request timeout occurred")
        result = format_error(error)
        assert "время ожидания" in result
    
    def test_format_error_connection(self):
        """Test formatting connection error."""
        error = Exception("Connection failed to server")
        result = format_error(error)
        assert "соединения" in result
    
    def test_format_error_with_context(self):
        """Test formatting error with context."""
        error = Exception("Something went wrong")
        result = format_error(error, "создании задачи")
        assert "при создании задачи" in result
    
    def test_format_error_generic(self):
        """Test formatting generic error."""
        error = Exception("Generic error message")
        result = format_error(error)
        assert "❌ Произошла ошибка" in result
        assert "Generic error message" in result