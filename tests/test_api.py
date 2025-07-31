"""Tests for Planfix API client."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import httpx

from src.planfix_api import PlanfixAPI, PlanfixError, PlanfixAuthError, PlanfixNotFoundError


class TestPlanfixAPI:
    """Test Planfix API client."""
    
    @pytest.fixture
    def api_client(self):
        """Create API client instance."""
        return PlanfixAPI()
    
    @pytest.mark.asyncio
    async def test_create_task_success(self, api_client, mock_api):
        """Test successful task creation."""
        with patch.object(api_client, '_request') as mock_request:
            mock_request.return_value = {"id": 123}
            
            task = await api_client.create_task(
                name="Test Task",
                description="Test Description",
                priority="HIGH"
            )
            
            assert task.id == 123
            assert task.name == "Test Task"
            assert task.priority == "HIGH"
            
            mock_request.assert_called_once_with(
                "POST", 
                "task",
                {
                    "name": "Test Task",
                    "description": "Test Description", 
                    "priority": "HIGH"
                }
            )
    
    @pytest.mark.asyncio
    async def test_create_task_with_all_params(self, api_client):
        """Test task creation with all parameters."""
        with patch.object(api_client, '_request') as mock_request:
            mock_request.return_value = {"id": 124}
            
            task = await api_client.create_task(
                name="Complex Task",
                description="Complex Description",
                project_id=10,
                assignee_id=20,
                priority="CRITICAL",
                deadline="2024-12-31"
            )
            
            expected_data = {
                "name": "Complex Task",
                "description": "Complex Description",
                "priority": "CRITICAL",
                "project": {"id": 10},
                "assignee": {"id": 20},
                "endDatePlan": "2024-12-31"
            }
            
            mock_request.assert_called_once_with("POST", "task", expected_data)
    
    @pytest.mark.asyncio
    async def test_search_tasks_basic(self, api_client):
        """Test basic task search."""
        with patch.object(api_client, '_request') as mock_request:
            mock_request.return_value = {
                "tasks": [
                    {
                        "id": 123,
                        "name": "Task 1",
                        "status": {"name": "В работе"},
                        "assignee": {"name": "Иван"},
                        "project": {"name": "Проект 1"}
                    }
                ]
            }
            
            tasks = await api_client.search_tasks(query="test")
            
            assert len(tasks) == 1
            assert tasks[0].id == 123
            assert tasks[0].name == "Task 1"
            assert tasks[0].status == "В работе"
    
    @pytest.mark.asyncio
    async def test_search_tasks_with_filters(self, api_client):
        """Test task search with filters."""
        with patch.object(api_client, '_request') as mock_request:
            mock_request.return_value = {"tasks": []}
            
            await api_client.search_tasks(
                query="test",
                project_id=10,
                assignee_id=20,
                status="completed"
            )
            
            expected_params = {
                "fields": "id,name,status,assignee,project,endDatePlan,priority",
                "name": "test",
                "project": 10,
                "assignee": 20,
                "status": "completed"
            }
            
            mock_request.assert_called_once_with("GET", "task/list", params=expected_params)
    
    @pytest.mark.asyncio
    async def test_get_task(self, api_client):
        """Test getting single task."""
        with patch.object(api_client, '_request') as mock_request:
            mock_request.return_value = {
                "id": 123,
                "name": "Test Task",
                "description": "Description",
                "status": {"name": "В работе"},
                "assignee": {"name": "Иван"},
                "project": {"name": "Проект"},
                "priority": "HIGH",
                "endDatePlan": "2024-12-31"
            }
            
            task = await api_client.get_task(123)
            
            assert task.id == 123
            assert task.name == "Test Task"
            assert task.status == "В работе"
            assert task.priority == "HIGH"
            
            mock_request.assert_called_once_with("GET", "task/123")
    
    @pytest.mark.asyncio
    async def test_update_task_status(self, api_client):
        """Test updating task status."""
        with patch.object(api_client, '_request') as mock_request:
            result = await api_client.update_task_status(123, "COMPLETED", "Done!")
            
            assert result is True
            
            expected_data = {
                "status": {"key": "COMPLETED"},
                "comment": "Done!"
            }
            
            mock_request.assert_called_once_with("POST", "task/123", expected_data)
    
    @pytest.mark.asyncio
    async def test_add_task_comment(self, api_client):
        """Test adding task comment."""
        with patch.object(api_client, '_request') as mock_request:
            result = await api_client.add_task_comment(123, "Test comment")
            
            assert result is True
            
            expected_data = {"comment": "Test comment"}
            mock_request.assert_called_once_with("POST", "task/123/comment", expected_data)
    
    @pytest.mark.asyncio
    async def test_create_project(self, api_client):
        """Test project creation."""
        with patch.object(api_client, '_request') as mock_request:
            mock_request.return_value = {"id": 456}
            
            project = await api_client.create_project(
                name="Test Project",
                description="Description",
                owner_id=10,
                client_id=20
            )
            
            assert project.id == 456
            assert project.name == "Test Project"
            
            expected_data = {
                "name": "Test Project",
                "description": "Description",
                "owner": {"id": 10},
                "client": {"id": 20}
            }
            
            mock_request.assert_called_once_with("POST", "project", expected_data)
    
    @pytest.mark.asyncio
    async def test_get_projects(self, api_client):
        """Test getting projects list."""
        with patch.object(api_client, '_request') as mock_request:
            mock_request.return_value = {
                "projects": [
                    {
                        "id": 456,
                        "name": "Project 1",
                        "status": {"name": "Активный"},
                        "owner": {"name": "Владелец"},
                        "taskCount": 5
                    }
                ]
            }
            
            projects = await api_client.get_projects()
            
            assert len(projects) == 1
            assert projects[0].id == 456
            assert projects[0].name == "Project 1"
            assert projects[0].task_count == 5
    
    @pytest.mark.asyncio
    async def test_add_contact(self, api_client):
        """Test adding contact."""
        with patch.object(api_client, '_request') as mock_request:
            mock_request.return_value = {"id": 789}
            
            contact = await api_client.add_contact(
                name="Test Contact",
                email="test@example.com",
                phone="+7-999-123-45-67",
                company="Company",
                position="Manager"
            )
            
            assert contact.id == 789
            assert contact.name == "Test Contact"
            assert contact.email == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_get_analytics_report(self, api_client):
        """Test getting analytics report."""
        with patch.object(api_client, '_request') as mock_request:
            mock_request.return_value = {
                "data": [{"name": "User 1", "value": "40h"}],
                "summary": {"total": "40h"}
            }
            
            report = await api_client.get_analytics_report(
                report_type="time",
                date_from="2024-01-01",
                date_to="2024-01-31",
                group_by="user"
            )
            
            assert report["report_type"] == "time"
            assert report["period"] == "2024-01-01 - 2024-01-31"
            assert len(report["data"]) == 1
    
    @pytest.mark.asyncio
    async def test_request_auth_error(self, api_client):
        """Test authentication error handling."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            
            mock_client_instance = AsyncMock()
            mock_client_instance.request.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            with pytest.raises(PlanfixAuthError):
                await api_client._request("GET", "test")
    
    @pytest.mark.asyncio
    async def test_request_not_found_error(self, api_client):
        """Test not found error handling."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = "Not Found"
            
            mock_client_instance = AsyncMock()
            mock_client_instance.request.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            with pytest.raises(PlanfixNotFoundError):
                await api_client._request("GET", "test")
    
    @pytest.mark.asyncio
    async def test_request_timeout_error(self, api_client):
        """Test timeout error handling."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.request.side_effect = httpx.TimeoutException("Timeout")
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            with pytest.raises(PlanfixError, match="Превышено время ожидания"):
                await api_client._request("GET", "test")
    
    @pytest.mark.asyncio
    async def test_request_connection_error(self, api_client):
        """Test connection error handling."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.request.side_effect = httpx.ConnectError("Connection failed")
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            with pytest.raises(PlanfixError, match="Не удалось подключиться"):
                await api_client._request("GET", "test")
    
    @pytest.mark.asyncio
    async def test_test_connection_success(self, api_client):
        """Test successful connection test."""
        with patch.object(api_client, '_request') as mock_request:
            mock_request.return_value = {"account": "test"}
            
            result = await api_client.test_connection()
            
            assert result is True
            mock_request.assert_called_once_with("GET", "account/info")
    
    @pytest.mark.asyncio
    async def test_test_connection_failure(self, api_client):
        """Test failed connection test."""
        with patch.object(api_client, '_request') as mock_request:
            mock_request.side_effect = PlanfixError("Connection failed")
            
            result = await api_client.test_connection()
            
            assert result is False