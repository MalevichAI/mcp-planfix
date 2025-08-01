"""Planfix API client."""

import logging
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel

from config import config
from utils import log_api_call, format_error

logger = logging.getLogger(__name__)


class PlanfixError(Exception):
    """Base exception for Planfix API errors."""
    pass


class PlanfixAuthError(PlanfixError):
    """Authentication error."""
    pass


class PlanfixNotFoundError(PlanfixError):
    """Resource not found error."""
    pass


class Task(BaseModel):
    """Task model."""
    id: int
    name: str
    description: Optional[str] = None
    status: Optional[str] = None
    assignee: Optional[str] = None
    project: Optional[str] = None
    priority: Optional[str] = None
    deadline: Optional[str] = None


class Project(BaseModel):
    """Project model."""
    id: int
    name: str
    description: Optional[str] = None
    status: Optional[str] = None
    owner: Optional[str] = None
    client: Optional[str] = None
    task_count: Optional[int] = 0


class Contact(BaseModel):
    """Contact model."""
    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None


class PlanfixAPI:
    """Planfix API client."""
    
    def __init__(self):
        """Initialize API client with configuration."""
        self.base_url = f"{config.planfix_base_url}/rest"
        self.timeout = config.request_timeout
        
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.planfix_api_key}",
            "User-Agent": "Planfix-MCP-Server/1.0.0"
        }
    
    async def _request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to Planfix API."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=data,
                    params=params
                )
                
                log_api_call(method, endpoint, response.status_code)
                
                # Handle different response codes
                if response.status_code == 401:
                    raise PlanfixAuthError("Неверные учётные данные API")
                elif response.status_code == 403:
                    raise PlanfixAuthError("Недостаточно прав доступа")
                elif response.status_code == 404:
                    raise PlanfixNotFoundError("Ресурс не найден")
                elif response.status_code >= 400:
                    error_data = response.text
                    try:
                        error_json = response.json()
                        error_data = error_json.get("message", error_data)
                    except:
                        pass
                    raise PlanfixError(f"HTTP {response.status_code}: {error_data}")
                
                return response.json()
                
        except httpx.TimeoutException:
            raise PlanfixError("Превышено время ожидания запроса")
        except httpx.ConnectError:
            raise PlanfixError("Не удалось подключиться к Planfix API")
        except Exception as e:
            logger.error(f"API request failed: {e}")
            raise PlanfixError(f"Ошибка API запроса: {e}")
    
    # Task operations
    async def create_task(
        self,
        name: str,
        description: str = "",
        project_id: Optional[int] = None,
        assignee_id: Optional[int] = None,
        priority: str = "NORMAL",
        deadline: Optional[str] = None
    ) -> Task:
        """Create a new task."""
        data = {
            "name": name,
            "description": description,
            "priority": priority
        }
        
        if project_id:
            data["project"] = {"id": project_id}
        if assignee_id:
            data["assignee"] = {"id": assignee_id}
        if deadline:
            data["endDatePlan"] = deadline
        
        result = await self._request("POST", "task", data)
        
        task_data = result.get("task", result)
        return Task(
            id=task_data["id"],
            name=name,
            description=description,
            priority=priority,
            deadline=deadline
        )
    
    async def get_task(self, task_id: int) -> Task:
        """Get task by ID."""
        result = await self._request("POST", f"task/{task_id}")
        
        task_data = result.get("task", result)
        return Task(
            id=task_data["id"],
            name=task_data.get("name", ""),
            description=task_data.get("description", ""),
            status=task_data.get("status", {}).get("name"),
            assignee=task_data.get("assignee", {}).get("name"),
            project=task_data.get("project", {}).get("name"),
            priority=task_data.get("priority"),
            deadline=task_data.get("endDatePlan")
        )
    
    async def search_tasks(
        self,
        query: str = "",
        project_id: Optional[int] = None,
        assignee_id: Optional[int] = None,
        status: str = "active"
    ) -> List[Task]:
        """Search tasks with filters."""
        params = {"fields": "id,name,status,assignee,project,endDatePlan,priority"}
        
        if query:
            params["name"] = query
        if project_id:
            params["project"] = project_id
        if assignee_id:
            params["assignee"] = assignee_id
        if status != "all":
            params["status"] = status
        
        result = await self._request("POST", "task/list", params)
        
        tasks = []
        task_list = result.get("tasks", result.get("data", []))
        for task_data in task_list:
            tasks.append(Task(
                id=task_data["id"],
                name=task_data.get("name", ""),
                status=task_data.get("status", {}).get("name"),
                assignee=task_data.get("assignee", {}).get("name"),
                project=task_data.get("project", {}).get("name"),
                priority=task_data.get("priority"),
                deadline=task_data.get("endDatePlan")
            ))
        
        return tasks
    
    async def update_task_status(
        self, 
        task_id: int, 
        status: str, 
        comment: str = ""
    ) -> bool:
        """Update task status."""
        data = {"status": {"key": status}}
        if comment:
            data["comment"] = comment
        
        await self._request("POST", f"task/{task_id}", data)
        return True
    
    async def add_task_comment(self, task_id: int, comment: str) -> bool:
        """Add comment to task."""
        data = {"comment": comment}
        await self._request("POST", f"task/{task_id}/comment", data)
        return True
    
    # Project operations
    async def create_project(
        self,
        name: str,
        description: str = "",
        owner_id: Optional[int] = None,
        client_id: Optional[int] = None
    ) -> Project:
        """Create a new project."""
        data = {
            "name": name,
            "description": description
        }
        
        if owner_id:
            data["owner"] = {"id": owner_id}
        if client_id:
            data["client"] = {"id": client_id}
        
        result = await self._request("POST", "project", data)
        
        project_data = result.get("project", result)
        return Project(
            id=project_data["id"],
            name=name,
            description=description
        )
    
    async def get_projects(self) -> List[Project]:
        """Get list of projects."""
        result = await self._request("POST", "project/list")
        
        projects = []
        project_list = result.get("projects", result.get("data", []))
        for project_data in project_list:
            projects.append(Project(
                id=project_data["id"],
                name=project_data.get("name", ""),
                description=project_data.get("description", ""),
                status=project_data.get("status", {}).get("name"),
                owner=project_data.get("owner", {}).get("name"),
                task_count=project_data.get("taskCount", 0)
            ))
        
        return projects
    
    # Contact operations
    async def add_contact(
        self,
        name: str,
        email: str = "",
        phone: str = "",
        company: str = "",
        position: str = ""
    ) -> Contact:
        """Add a new contact."""
        data = {
            "name": name,
            "email": email,
            "phone": phone,
            "company": company,
            "position": position
        }
        
        result = await self._request("POST", "contact", data)
        
        contact_data = result.get("contact", result)
        return Contact(
            id=contact_data["id"],
            name=name,
            email=email,
            phone=phone,
            company=company,
            position=position
        )
    
    async def get_contacts(self, limit: int = 20) -> List[Contact]:
        """Get recent contacts."""
        params = {"limit": limit, "orderBy": "dateCreate", "order": "desc"}
        result = await self._request("POST", "contact/list", params)
        
        contacts = []
        contact_list = result.get("contacts", result.get("data", []))
        for contact_data in contact_list:
            contacts.append(Contact(
                id=contact_data["id"],
                name=contact_data.get("name", ""),
                email=contact_data.get("email", ""),
                phone=contact_data.get("phone", ""),
                company=contact_data.get("company", ""),
                position=contact_data.get("position", "")
            ))
        
        return contacts
    
    # Analytics operations
    async def get_analytics_report(
        self,
        report_type: str,
        date_from: str,
        date_to: str,
        group_by: str = "user"
    ) -> Dict[str, Any]:
        """Get analytics report."""
        params = {
            "type": report_type,
            "dateFrom": date_from,
            "dateTo": date_to,
            "groupBy": group_by
        }
        
        result = await self._request("POST", "analytics/report", params)
        
        return {
            "report_type": report_type,
            "period": f"{date_from} - {date_to}",
            "group_by": group_by,
            "data": result.get("data", []),
            "summary": result.get("summary", {})
        }
    
    # Test connection
    async def test_connection(self) -> bool:
        """Test API connection."""
        try:
            await self._request("POST", "contact/list")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False


# Global API instance
api = PlanfixAPI()