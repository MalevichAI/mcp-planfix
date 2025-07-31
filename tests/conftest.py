"""Test configuration and fixtures."""

import os
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock

# Set test environment variables
os.environ["PLANFIX_ACCOUNT"] = "test-account"
os.environ["PLANFIX_API_KEY"] = "test-api-key"
os.environ["PLANFIX_USER_KEY"] = "test-user-key"
os.environ["DEBUG"] = "true"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_api():
    """Mock Planfix API client."""
    api = AsyncMock()
    
    # Mock task operations
    api.create_task.return_value = Mock(
        id=123,
        name="Test Task",
        description="Test Description",
        priority="HIGH",
        deadline="2024-12-31"
    )
    
    api.search_tasks.return_value = [
        Mock(
            id=123,
            name="Test Task 1",
            status="В работе",
            assignee="Иван Петров",
            project="Тестовый проект",
            deadline="2024-12-31"
        ),
        Mock(
            id=124,
            name="Test Task 2",
            status="Новая",
            assignee="Мария Иванова",
            project="Другой проект",
            deadline=None
        )
    ]
    
    api.get_task.return_value = Mock(
        id=123,
        name="Test Task",
        description="Detailed test description",
        status="В работе",
        assignee="Иван Петров",
        project="Тестовый проект",
        priority="HIGH",
        deadline="2024-12-31"
    )
    
    api.update_task_status.return_value = True
    api.add_task_comment.return_value = True
    
    # Mock project operations
    api.create_project.return_value = Mock(
        id=456,
        name="Test Project",
        description="Test Project Description"
    )
    
    api.get_projects.return_value = [
        Mock(
            id=456,
            name="Test Project 1",
            description="Description 1",
            status="Активный",
            owner="Руководитель",
            task_count=5
        ),
        Mock(
            id=457,
            name="Test Project 2",
            description="Description 2",
            status="Завершён",
            owner="Менеджер",
            task_count=0
        )
    ]
    
    # Mock contact operations
    api.add_contact.return_value = Mock(
        id=789,
        name="Test Contact",
        email="test@example.com",
        phone="+7-999-123-45-67",
        company="Test Company",
        position="Manager"
    )
    
    api.get_contacts.return_value = [
        Mock(
            id=789,
            name="Test Contact 1",
            email="contact1@example.com",
            phone="+7-999-111-11-11",
            company="Company 1",
            position="Manager"
        ),
        Mock(
            id=790,
            name="Test Contact 2",
            email="contact2@example.com",
            phone="+7-999-222-22-22",
            company="Company 2",
            position="Developer"
        )
    ]
    
    # Mock analytics
    api.get_analytics_report.return_value = {
        "report_type": "time",
        "period": "2024-01-01 - 2024-01-31",
        "group_by": "user",
        "data": [
            {"name": "Иван Петров", "value": "40 часов"},
            {"name": "Мария Иванова", "value": "35 часов"}
        ],
        "summary": {
            "total_time": "75 часов",
            "average_per_user": "37.5 часов"
        }
    }
    
    api.test_connection.return_value = True
    
    return api

@pytest.fixture
def sample_task_data():
    """Sample task data for tests."""
    return {
        "name": "Test Task",
        "description": "Test task description",
        "priority": "HIGH",
        "deadline": "2024-12-31"
    }

@pytest.fixture
def sample_project_data():
    """Sample project data for tests."""
    return {
        "name": "Test Project",
        "description": "Test project description",
        "owner_id": 1,
        "client_id": 2
    }

@pytest.fixture
def sample_contact_data():
    """Sample contact data for tests."""
    return {
        "name": "Test Contact",
        "email": "test@example.com",
        "phone": "+7-999-123-45-67",
        "company": "Test Company",
        "position": "Manager"
    }