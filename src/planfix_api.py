"""Planfix API client."""

import logging
from typing import Any, Dict, List, Optional

import httpx
from .config import config
from .models import Task, Project, Contact, Employee, Comment, File, Report, Process
from .utils import log_api_call, format_error

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


# Models imported from models.py


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
    
    # Enhanced contact operations
    async def get_contact(self, contact_id: int) -> Contact:
        """Get contact by ID."""
        result = await self._request("GET", f"contact/{contact_id}")
        
        contact_data = result.get("contact", result)
        return Contact(
            id=contact_data["id"],
            name=contact_data.get("name", ""),
            midname=contact_data.get("midname", ""),
            lastname=contact_data.get("lastname", ""),
            email=contact_data.get("email", ""),
            phone=contact_data.get("phones", [{}])[0].get("number", "") if contact_data.get("phones") else "",
            company=contact_data.get("company", ""),
            position=contact_data.get("position", ""),
            description=contact_data.get("description", ""),
            is_company=contact_data.get("isCompany", False),
            created_date=contact_data.get("createdDate", {}).get("datetime", "")
        )
    
    async def search_contacts(self, query: str = "", limit: int = 20) -> List[Contact]:
        """Search contacts by name or other criteria."""
        params = {"limit": limit}
        if query:
            params["query"] = query
            
        result = await self._request("POST", "contact/list", params)
        
        contacts = []
        contact_list = result.get("contacts", result.get("data", []))
        for contact_data in contact_list:
            contacts.append(Contact(
                id=contact_data["id"],
                name=contact_data.get("name", ""),
                midname=contact_data.get("midname", ""),
                lastname=contact_data.get("lastname", ""),
                email=contact_data.get("email", ""),
                phone=contact_data.get("phones", [{}])[0].get("number", "") if contact_data.get("phones") else "",
                company=contact_data.get("company", ""),
                position=contact_data.get("position", ""),
                description=contact_data.get("description", ""),
                is_company=contact_data.get("isCompany", False),
                created_date=contact_data.get("createdDate", {}).get("datetime", "")
            ))
        
        return contacts
    
    # Employee operations
    async def list_employees(self, limit: int = 20) -> List[Employee]:
        """List employees."""
        result = await self._request("POST", "user/list", {"limit": limit})
        
        employees = []
        employee_list = result.get("users", result.get("data", []))
        for employee_data in employee_list:
            employees.append(Employee(
                id=employee_data["id"],
                name=employee_data.get("name", ""),
                email=employee_data.get("email", ""),
                position=employee_data.get("position", ""),
                status=employee_data.get("status", {}).get("name", ""),
                last_activity=employee_data.get("lastActivity", {}).get("datetime", "")
            ))
        
        return employees
    
    # File operations
    async def list_files(self, limit: int = 20, task_id: Optional[int] = None, project_id: Optional[int] = None) -> List[File]:
        """List files."""
        data = {"limit": limit}
        if task_id:
            data["taskId"] = task_id
        if project_id:
            data["projectId"] = project_id
            
        result = await self._request("POST", "file/list", data)
        
        files = []
        file_list = result.get("files", result.get("data", []))
        for file_data in file_list:
            files.append(File(
                id=file_data["id"],
                name=file_data.get("name", ""),
                size=file_data.get("size", 0),
                created_date=file_data.get("createdDate", {}).get("datetime", ""),
                author=file_data.get("author", {}).get("name", ""),
                task_id=file_data.get("taskId"),
                project_id=file_data.get("projectId")
            ))
        
        return files
    
    # Comment operations  
    async def list_comments(self, limit: int = 20, task_id: Optional[int] = None, project_id: Optional[int] = None) -> List[Comment]:
        """List comments."""
        data = {"limit": limit}
        if task_id:
            data["taskId"] = task_id
        if project_id:
            data["projectId"] = project_id
            
        result = await self._request("POST", "comment/list", data)
        
        comments = []
        comment_list = result.get("comments", result.get("data", []))
        for comment_data in comment_list:
            comments.append(Comment(
                id=comment_data["id"],
                text=comment_data.get("text", ""),
                author=comment_data.get("author", {}).get("name", ""),
                created_date=comment_data.get("createdDate", {}).get("datetime", ""),
                task_id=comment_data.get("taskId"),
                project_id=comment_data.get("projectId")
            ))
        
        return comments
    
    # Report operations
    async def list_reports(self, limit: int = 20) -> List[Report]:
        """List reports."""
        result = await self._request("POST", "report/list", {"limit": limit})
        
        reports = []
        report_list = result.get("reports", result.get("data", []))
        for report_data in report_list:
            reports.append(Report(
                id=report_data["id"],
                name=report_data.get("name", ""),
                description=report_data.get("description", ""),
                created_date=report_data.get("createdDate", {}).get("datetime", "")
            ))
        
        return reports
    
    # Process operations
    async def list_processes(self, limit: int = 20) -> List[Process]:
        """List processes."""
        result = await self._request("POST", "process/list", {"limit": limit})
        
        processes = []
        process_list = result.get("processes", result.get("data", []))
        for process_data in process_list:
            processes.append(Process(
                id=process_data["id"],
                name=process_data.get("name", ""),
                description=process_data.get("description", ""),
                status=process_data.get("status", {}).get("name", ""),
                created_date=process_data.get("createdDate", {}).get("datetime", "")
            ))
        
        return processes

    # Test connection
    async def test_connection(self) -> bool:
        """Test API connection."""
        try:
            await self._request("POST", "contact/list")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False


