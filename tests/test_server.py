"""Tests for Planfix MCP Server."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

# Import server functions (we'll need to adjust imports based on actual structure)
with patch.dict('sys.modules', {'src.planfix_api': Mock()}):
    from src.planfix_server import (
        create_task, search_tasks, update_task_status, add_task_comment,
        create_project, add_contact, get_analytics_report,
        get_dashboard_summary, get_projects_list, get_task_details,
        analyze_project_status, create_weekly_report, plan_sprint
    )

class TestMCPTools:
    """Test MCP tool functions."""
    
    @pytest.mark.asyncio
    async def test_create_task_success(self, mock_api, sample_task_data):
        """Test successful task creation."""
        with patch('src.planfix_server.api', mock_api):
            # Mock context
            mock_ctx = Mock()
            mock_ctx.info = Mock()
            mock_ctx.error = Mock()
            
            result = await create_task(
                name=sample_task_data["name"],
                description=sample_task_data["description"],
                priority=sample_task_data["priority"],
                deadline=sample_task_data["deadline"],
                ctx=mock_ctx
            )
            
            assert "✅ **Задача создана успешно!**" in result
            assert "Test Task" in result
            assert "123" in result
            
            mock_ctx.info.assert_called()
            mock_api.create_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_task_with_project_and_assignee(self, mock_api):
        """Test task creation with project and assignee."""
        with patch('src.planfix_server.api', mock_api):
            mock_ctx = Mock()
            mock_ctx.info = Mock()
            
            result = await create_task(
                name="Project Task",
                project_id=10,
                assignee_id=20,
                ctx=mock_ctx
            )
            
            assert "Проект: ID 10" in result
            assert "Исполнитель: ID 20" in result
            
            mock_api.create_task.assert_called_once_with(
                name="Project Task",
                description="",
                project_id=10,
                assignee_id=20,
                priority="NORMAL",
                deadline=None
            )
    
    @pytest.mark.asyncio
    async def test_create_task_error(self, mock_api):
        """Test task creation error handling."""
        with patch('src.planfix_server.api', mock_api):
            from src.planfix_api import PlanfixError
            mock_api.create_task.side_effect = PlanfixError("API Error")
            
            mock_ctx = Mock()
            mock_ctx.info = Mock()
            mock_ctx.error = Mock()
            
            result = await create_task(
                name="Error Task",
                ctx=mock_ctx
            )
            
            assert "❌" in result
            assert "ошибка" in result.lower()
            mock_ctx.error.assert_called()
    
    @pytest.mark.asyncio
    async def test_search_tasks_success(self, mock_api):
        """Test successful task search."""
        with patch('src.planfix_server.api', mock_api):
            mock_ctx = Mock()
            mock_ctx.info = Mock()
            
            result = await search_tasks(
                query="test",
                status="active",
                ctx=mock_ctx
            )
            
            assert "📋 Найдено задач: 2" in result
            assert "Test Task 1" in result
            assert "Test Task 2" in result
            
            mock_api.search_tasks.assert_called_once_with(
                query="test",
                project_id=None,
                assignee_id=None,
                status="active"
            )
    
    @pytest.mark.asyncio
    async def test_search_tasks_with_limit(self, mock_api):
        """Test task search with limit."""
        with patch('src.planfix_server.api', mock_api):
            # Create more tasks than limit
            mock_api.search_tasks.return_value = [Mock()] * 25
            
            mock_ctx = Mock()
            mock_ctx.info = Mock()
            
            result = await search_tasks(
                query="many",
                limit=10,
                ctx=mock_ctx
            )
            
            assert "Показаны первые 10 результатов" in result
    
    @pytest.mark.asyncio
    async def test_update_task_status_success(self, mock_api):
        """Test successful status update."""
        with patch('src.planfix_server.api', mock_api):
            mock_ctx = Mock()
            mock_ctx.info = Mock()
            
            result = await update_task_status(
                task_id=123,
                status="COMPLETED",
                comment="All done!",
                ctx=mock_ctx
            )
            
            assert "✅ **Статус задачи обновлён!**" in result
            assert "123" in result
            assert "COMPLETED" in result
            assert "All done!" in result
            
            mock_api.update_task_status.assert_called_once_with(
                123, "COMPLETED", "All done!"
            )
    
    @pytest.mark.asyncio
    async def test_add_task_comment_success(self, mock_api):
        """Test adding task comment."""
        with patch('src.planfix_server.api', mock_api):
            mock_ctx = Mock()
            mock_ctx.info = Mock()
            
            result = await add_task_comment(
                task_id=123,
                comment="Great progress!",
                ctx=mock_ctx
            )
            
            assert "✅ **Комментарий добавлен!**" in result
            assert "123" in result
            assert "Great progress!" in result
    
    @pytest.mark.asyncio
    async def test_create_project_success(self, mock_api, sample_project_data):
        """Test successful project creation."""
        with patch('src.planfix_server.api', mock_api):
            mock_ctx = Mock()
            mock_ctx.info = Mock()
            
            result = await create_project(
                name=sample_project_data["name"],
                description=sample_project_data["description"],
                owner_id=sample_project_data["owner_id"],
                client_id=sample_project_data["client_id"],
                ctx=mock_ctx
            )
            
            assert "✅ **Проект создан успешно!**" in result
            assert "Test Project" in result
            assert "456" in result
    
    @pytest.mark.asyncio
    async def test_add_contact_success(self, mock_api, sample_contact_data):
        """Test successful contact addition."""
        with patch('src.planfix_server.api', mock_api):
            mock_ctx = Mock()
            mock_ctx.info = Mock()
            
            result = await add_contact(
                name=sample_contact_data["name"],
                email=sample_contact_data["email"],
                phone=sample_contact_data["phone"],
                company=sample_contact_data["company"],
                position=sample_contact_data["position"],
                ctx=mock_ctx
            )
            
            assert "✅ **Контакт добавлен успешно!**" in result
            assert "Test Contact" in result
            assert "test@example.com" in result
    
    @pytest.mark.asyncio
    async def test_get_analytics_report_success(self, mock_api):
        """Test getting analytics report."""
        with patch('src.planfix_server.api', mock_api):
            mock_ctx = Mock()
            mock_ctx.info = Mock()
            
            result = await get_analytics_report(
                report_type="time",
                period_start="2024-01-01",
                period_end="2024-01-31",
                group_by="user",
                ctx=mock_ctx
            )
            
            assert "📊 **TIME**" in result
            assert "2024-01-01 - 2024-01-31" in result
            assert "Иван Петров" in result
            assert "40 часов" in result


class TestMCPResources:
    """Test MCP resource functions."""
    
    @pytest.mark.asyncio
    async def test_get_dashboard_summary(self, mock_api):
        """Test dashboard summary resource."""
        with patch('src.planfix_server.api', mock_api):
            result = await get_dashboard_summary()
            
            assert "📊 **Сводка Planfix**" in result
            assert "📋 **ЗАДАЧИ:**" in result
            assert "🎯 **ПРОЕКТЫ:**" in result
            assert "📈 **АКТИВНОСТЬ:**" in result
    
    @pytest.mark.asyncio
    async def test_get_projects_list(self, mock_api):
        """Test projects list resource."""
        with patch('src.planfix_server.api', mock_api):
            result = await get_projects_list()
            
            assert "🎯 **Проекты**" in result
            assert "Test Project 1" in result
            assert "Test Project 2" in result
    
    @pytest.mark.asyncio
    async def test_get_task_details_success(self, mock_api):
        """Test task details resource."""
        with patch('src.planfix_server.api', mock_api):
            result = await get_task_details("123")
            
            assert "📋 **Задача #123**" in result
            assert "Test Task" in result
            assert "В работе" in result
            assert "Иван Петров" in result
    
    @pytest.mark.asyncio
    async def test_get_task_details_invalid_id(self, mock_api):
        """Test task details with invalid ID."""
        with patch('src.planfix_server.api', mock_api):
            result = await get_task_details("invalid")
            
            assert "❌ Неверный ID задачи" in result


class TestMCPPrompts:
    """Test MCP prompt functions."""
    
    def test_analyze_project_status_prompt(self):
        """Test project analysis prompt."""
        result = analyze_project_status("Test Project")
        
        assert "Test Project" in result
        assert "🔍 **АНАЛИЗ ПРОЕКТА:**" in result
        assert "📊 **МЕТРИКИ ДЛЯ ОЦЕНКИ:**" in result
        assert "⚠️ **ОСОБОЕ ВНИМАНИЕ:**" in result
        assert "📋 **РЕЗУЛЬТАТ:**" in result
    
    def test_create_weekly_report_prompt(self):
        """Test weekly report prompt."""
        result = create_weekly_report("2024-01-01")
        
        assert "2024-01-01 - 2024-01-07" in result
        assert "📊 **ПОКАЗАТЕЛИ НЕДЕЛИ:**" in result
        assert "🎯 **ДОСТИЖЕНИЯ:**" in result
        assert "⚠️ **ПРОБЛЕМЫ И РИСКИ:**" in result
        assert "📋 **ПЛАНЫ НА СЛЕДУЮЩУЮ НЕДЕЛЮ:**" in result
    
    def test_plan_sprint_prompt(self):
        """Test sprint planning prompt."""
        result = plan_sprint(14)
        
        assert "14 дней" in result
        assert "🎯 **ЦЕЛИ СПРИНТА:**" in result
        assert "📋 **ПЛАНИРОВАНИЕ ЗАДАЧ:**" in result
        assert "⏰ **ВРЕМЕННОЕ ПЛАНИРОВАНИЕ:**" in result
        assert "🎯 **ИТОГОВЫЙ ПЛАН:**" in result
    
    def test_plan_sprint_custom_duration(self):
        """Test sprint planning with custom duration."""
        result = plan_sprint(21)
        
        assert "21 дней" in result