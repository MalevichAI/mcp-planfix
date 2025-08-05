"""Planfix API client."""

import logging
from typing import Any, Dict, List, Optional, Union, Type, TypeVar
from pydantic import BaseModel, ValidationError

import httpx
from .config import config
from .models import (
    # Response models
    TaskResponse, ContactResponse, ProjectResponse, CommentResponse, 
    FileResponse, UserResponse, ApiResponseError, Report,
    # Request models  
    TaskCreateRequest, TaskUpdateRequest, ContactRequest, CommentCreateRequest,
    # Legacy models for backwards compatibility
    Contact, Process
)
from .utils import log_api_call

T = TypeVar('T', bound=BaseModel)

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


class PlanfixValidationError(PlanfixError):
    """Response validation error."""
    pass


class PlanfixAPI:
    """Planfix API client with comprehensive model support."""
    
    def __init__(self):
        """Initialize API client with configuration."""
        self.base_url = f"{config.planfix_account}.planfix.ru/rest"
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
                        if "result" in error_json and error_json["result"] == "fail":
                            # Try to parse as ApiResponseError
                            try:
                                error_obj = ApiResponseError(**error_json)
                                raise PlanfixError(f"API Error {error_obj.code}: {error_obj.error}")
                            except ValidationError:
                                pass
                        error_data = error_json.get("message", error_json.get("error", error_data))
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
    
    def _validate_response(self, data: Dict[str, Any], model_class: Type[T], data_key: Optional[str] = None) -> T:
        """Validate API response against Pydantic model."""
        try:
            if data_key:
                if data_key not in data:
                    raise PlanfixValidationError(f"Expected key '{data_key}' not found in response")
                return model_class(**data[data_key])
            else:
                return model_class(**data)
        except ValidationError as e:
            logger.error(f"Response validation failed: {e}")
            raise PlanfixValidationError(f"Response validation failed: {e}")
    
    def _validate_list_response(self, data: Dict[str, Any], model_class: Type[T], data_key: str) -> List[T]:
        """Validate API list response against Pydantic model."""
        try:
            if data_key not in data:
                raise PlanfixValidationError(f"Expected key '{data_key}' not found in response")
            
            items = data[data_key]
            if not isinstance(items, list):
                raise PlanfixValidationError(f"Expected '{data_key}' to be a list")
            
            return [model_class(**item) for item in items]
        except ValidationError as e:
            logger.error(f"List response validation failed: {e}")
            raise PlanfixValidationError(f"List response validation failed: {e}")
    
    # Task operations
    async def get_task(self, task_id: int, fields: Optional[str] = None) -> TaskResponse:
        """Get task by ID using proper API endpoint."""
        params = {}
        if fields:
            params["fields"] = fields
        else:
            params["fields"] = "id,name,description,priority,status,assigner,assignees,project,startDateTime,endDateTime"
        
        result = await self._request("GET", f"task/{task_id}", params=params)
        return self._validate_response(result, TaskResponse, "task")
    
    async def search_tasks(
        self,
        query: str = "",
        project_id: Optional[int] = None,
        assignee_id: Optional[int] = None,
        status: str = "active",
        limit: int = 20
    ) -> List[TaskResponse]:
        """Search tasks with filters using proper API endpoint."""
        data = {
            "offset": 0,
            "pageSize": limit,
            "fields": "id,name,description,priority,status,assigner,assignees,project,startDateTime,endDateTime"
        }
        
        # Add filters based on parameters
        filters = []
        if project_id:
            filters.append({
                "type": 5,  # Project filter type
                "operator": "equal",
                "value": project_id
            })
        if assignee_id:
            filters.append({
                "type": 2,  # Assignee filter type
                "operator": "equal", 
                "value": f"user:{assignee_id}"
            })
        if status == "active":
            # Add active status filter if needed
            pass
        
        if filters:
            data["filters"] = filters
        
        result = await self._request("POST", "task/list", data=data)
        return self._validate_list_response(result, TaskResponse, "tasks")
    
    async def create_task(self, task_data: TaskCreateRequest) -> int:
        """Create a new task."""
        result = await self._request("POST", "task/", data=task_data.model_dump(exclude_none=True))
        return result.get("id", 0)
    
    async def update_task(self, task_id: int, task_data: TaskUpdateRequest, silent: bool = False) -> bool:
        """Update a task."""
        params = {"silent": silent} if silent else {}
        await self._request("POST", f"task/{task_id}", data=task_data.model_dump(exclude_none=True), params=params)
        return True
    
    # Contact operations
    async def get_contact(self, contact_id: Union[int, str], fields: Optional[str] = None) -> ContactResponse:
        """Get contact by ID using proper API endpoint."""
        params = {}
        if fields:
            params["fields"] = fields
        else:
            params["fields"] = "id,name,midname,lastname,email,phones,position,description,isCompany,createdDate"
        
        result = await self._request("GET", f"contact/{contact_id}", params=params)
        return self._validate_response(result, ContactResponse, "contact")
    
    async def search_contacts(self, query: str = "", limit: int = 20, is_company: bool = False) -> List[ContactResponse]:
        """Search contacts using proper API endpoint."""
        data = {
            "offset": 0,
            "pageSize": limit,
            "isCompany": is_company,
            "fields": "id,name,midname,lastname,email,phones,position,description,isCompany,createdDate"
        }
        
        # Add text search filter if query provided
        if query:
            data["filters"] = [{
                "type": 4001,  # Name search filter type
                "operator": "equal",
                "value": query
            }]
        
        result = await self._request("POST", "contact/list", data=data)
        return self._validate_list_response(result, ContactResponse, "contacts")
    
    async def create_contact(self, contact_data: ContactRequest) -> int:
        """Create a new contact."""
        result = await self._request("POST", "contact/", data=contact_data.model_dump(exclude_none=True))
        return result.get("id")
    
    async def update_contact(self, contact_id: Union[int, str], contact_data: ContactRequest, silent: bool = False) -> bool:
        """Update a contact."""
        params = {"silent": silent} if silent else {}
        await self._request("POST", f"contact/{contact_id}", data=contact_data.model_dump(exclude_none=True), params=params)
        return True
    
    # Project operations  
    async def get_projects(self, limit: int = 20) -> List[ProjectResponse]:
        """Get list of projects."""
        data = {
            "offset": 0,
            "pageSize": limit,
            "fields": "id,name,description,owner,client,startDate,endDate,isDeleted"
        }
        
        result = await self._request("POST", "project/list", data=data)
        return self._validate_list_response(result, ProjectResponse, "projects")
    
    # Employee operations
    async def list_employees(self, limit: int = 20) -> List[UserResponse]:
        """List employees/users."""
        data = {
            "offset": 0,
            "pageSize": limit,
            "fields": "id,name,email,position"
        }
        
        result = await self._request("POST", "user/list", data=data)
        return self._validate_list_response(result, UserResponse, "users")
    
    # File operations
    async def list_files(self, limit: int = 20, task_id: Optional[int] = None, project_id: Optional[int] = None) -> List[FileResponse]:
        """List files."""
        data = {"pageSize": limit}
        if task_id:
            data["taskId"] = task_id
        if project_id:
            data["projectId"] = project_id
            
        result = await self._request("POST", "file/list", data=data)
        return self._validate_list_response(result, FileResponse, "files")
    
    # Comment operations  
    async def list_comments(self, limit: int = 20, task_id: Optional[int] = None, project_id: Optional[int] = None) -> List[CommentResponse]:
        """List comments."""
        data = {
            "offset": 0,
            "pageSize": limit,
            "fields": "id,description,dateTime,owner,type"
        }
        
        # For task comments, use task-specific endpoint
        if task_id:
            result = await self._request("POST", f"task/{task_id}/comments/list", data=data)
        elif project_id:
            result = await self._request("POST", f"project/{project_id}/comments/list", data=data)
        else:
            # General comment list endpoint (if available)
            result = await self._request("POST", "comment/list", data=data)
            
        return self._validate_list_response(result, CommentResponse, "comments")
    
    async def add_comment_to_contact(self, contact_id: Union[int, str], comment_data: CommentCreateRequest) -> int:
        """Add comment to a contact."""
        result = await self._request("POST", f"contact/{contact_id}/comments/", data=comment_data.model_dump(exclude_none=True))
        return result.get("id")
    
    # Report operations
    async def list_reports(self, limit: int = 20) -> List[Report]:
        """List reports."""
        data = {"pageSize": limit}
        result = await self._request("POST", "report/list", data=data)
        return self._validate_list_response(result, Report, "reports")
    
    # Process operations
    async def list_processes(self, limit: int = 20) -> List[Process]:
        """List processes."""
        data = {"pageSize": limit}
        result = await self._request("POST", "process/list", data=data)
        
        # Map to legacy Process model for now
        processes = []
        process_list = result.get("processes", [])
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
            await self._request("POST", "contact/list", data={"pageSize": 1})
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    # Legacy methods for backwards compatibility
    async def get_contacts(self, limit: int = 20) -> List[Contact]:
        """Get recent contacts (legacy method)."""
        contacts_response = await self.search_contacts(limit=limit)
        
        # Convert to legacy Contact model
        contacts = []
        for contact_data in contacts_response:
            phone = ""
            if contact_data.phones and len(contact_data.phones) > 0:
                phone = contact_data.phones[0].number or ""
            
            contacts.append(Contact(
                id=contact_data.id or 0,
                name=contact_data.name or "",
                midname=contact_data.midname or "",
                lastname=contact_data.lastname or "",
                email=contact_data.email or "",
                phone=phone,
                company="",  # Not directly available in new model
                position=contact_data.position or "",
                description=contact_data.description or "",
                is_company=contact_data.isCompany or False,
                created_date=contact_data.createdDate.datetime if contact_data.createdDate else ""
            ))
        
        return contacts

    async def get_contact_details(self, contact_id: int) -> Contact:
        """Get contact details (legacy method)."""
        contact_response = await self.get_contact(contact_id)
        
        phone = ""
        if contact_response.phones and len(contact_response.phones) > 0:
            phone = contact_response.phones[0].number or ""
        
        return Contact(
            id=contact_response.id or 0,
            name=contact_response.name or "",
            midname=contact_response.midname or "",
            lastname=contact_response.lastname or "",
            email=contact_response.email or "",
            phone=phone,
            company="",  # Not directly available in new model
            position=contact_response.position or "",
            description=contact_response.description or "",
            is_company=contact_response.isCompany or False,
            created_date=contact_response.createdDate.datetime if contact_response.createdDate else ""
        )


