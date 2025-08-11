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
        self.base_url = f"https://{config.planfix_account}.planfix.ru/rest"
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

    async def get_project(self, project_id: int, fields: Optional[Union[str, List[str]]] = None) -> ProjectResponse:
        """Get project by ID. Returns all known fields by default."""
        default_fields = (
            "id,template,name,description,owner,client,isDeleted,startDate,endDate,"
            "createdDate,dateOfLastUpdate,sourceObjectId,sourceDataVersion"
        )
        if isinstance(fields, list):
            fields_param = ",".join(fields)
        elif isinstance(fields, str) and fields.strip():
            fields_param = fields
        else:
            fields_param = default_fields
        params = {"fields": fields_param}
        result = await self._request("GET", f"project/{project_id}", params=params)
        return self._validate_response(result, ProjectResponse, "project")
    
    async def list_tasks(
        self,
        project_id: Optional[int] = None,
        assignee_id: Optional[int] = None,
        status: str = "active",
        limit: int = 20,
        offset: int = 0
    ) -> List[TaskResponse]:
        """List tasks with filters using proper API endpoint."""
        data = {
            "offset": offset,
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

    async def get_contact_details(
        self,
        contact_id: Union[int, str],
        fields: Optional[Union[str, List[str]]] = None
    ) -> ContactResponse:
        """Get full contact details by ID.

        By default returns all documented fields. You can override the returned
        fields by providing a comma-separated string or a list of field names.
        """
        # All known system fields for contact entity
        all_fields = (
            "id,template,name,midname,lastname,gender,description,address,site,email,"
            "additionalEmailAddresses,skype,telegramId,telegram,facebook,instagram,vk,"
            "position,group,isCompany,isDeleted,birthDate,createdDate,dateOfLastUpdate,"
            "supervisors,phones,companies,contacts,files,dataTags,sourceObjectId,sourceDataVersion"
        )

        if isinstance(fields, list):
            fields_param = ",".join(fields)
        elif isinstance(fields, str) and fields.strip():
            fields_param = fields
        else:
            fields_param = all_fields

        params = {"fields": fields_param}
        result = await self._request("GET", f"contact/{contact_id}", params=params)
        return self._validate_response(result, ContactResponse, "contact")

    async def get_comment(self, comment_id: int, fields: Optional[Union[str, List[str]]] = None) -> CommentResponse:
        """Get comment by ID. Returns all known fields by default."""
        default_fields = (
            "id,sourceObjectId,sourceDataVersion,dateTime,type,fromType,description,contact,project,"
            "owner,isDeleted,isPinned,isHidden,isNotRead,recipients,reminders,dataTags,files"
        )
        if isinstance(fields, list):
            fields_param = ",".join(fields)
        elif isinstance(fields, str) and fields.strip():
            fields_param = fields
        else:
            fields_param = default_fields
        params = {"fields": fields_param}
        result = await self._request("GET", f"comment/{comment_id}", params=params)
        return self._validate_response(result, CommentResponse, "comment")

    async def get_file(self, file_id: int, fields: Optional[Union[str, List[str]]] = None) -> FileResponse:
        """Get file by ID. Returns all known fields by default."""
        default_fields = "id,name,size,downloadUrl"
        if isinstance(fields, list):
            fields_param = ",".join(fields)
        elif isinstance(fields, str) and fields.strip():
            fields_param = fields
        else:
            fields_param = default_fields
        params = {"fields": fields_param}
        result = await self._request("GET", f"file/{file_id}", params=params)
        return self._validate_response(result, FileResponse, "file")

    async def get_user(self, user_id: Union[int, str], fields: Optional[Union[str, List[str]]] = None) -> UserResponse:
        """Get user by ID. Returns all known fields by default."""
        default_fields = "id, name, midname, lastname, gender, isDeleted, birthDate, groups, role, login, email, secondaryEmails, telegramId, telegram, status, phones, customFieldData, languageCode, position"
        if isinstance(fields, list):
            fields_param = ",".join(fields)
        elif isinstance(fields, str) and fields.strip():
            fields_param = fields
        else:
            fields_param = default_fields
        params = {"fields": fields_param}
        result = await self._request("GET", f"user/{user_id}", params=params)
        return self._validate_response(result, UserResponse, "user")
    
    async def list_contacts(self, limit: int = 20, offset: int = 0, is_company: bool = False) -> List[ContactResponse]:
        """List contacts using proper API endpoint."""
        data = {
            "offset": offset,
            "pageSize": limit,
            "isCompany": is_company,
            "fields": "id,name,midname,lastname,email,phones,position,description,isCompany,createdDate"
        }

        result = await self._request("POST", "contact/list", data=data)
        return self._validate_list_response(result, ContactResponse, "contacts")

    
    # Project operations  
    async def list_projects(self, limit: int = 20, offset: int = 0) -> List[ProjectResponse]:
        """Get list of projects."""
        data = {
            "offset": offset,
            "pageSize": limit,
            "fields": "id,name,description,owner,client,startDate,endDate,isDeleted"
        }
        
        result = await self._request("POST", "project/list", data=data)
        return self._validate_list_response(result, ProjectResponse, "projects")
    
    # Employee operations
    async def list_employees(self, limit: int = 20, offset: int = 0) -> List[UserResponse]:
        """List employees/users."""
        data = {
            "offset": offset,
            "pageSize": limit,
            "fields": "id,name,email,position"
        }
        
        result = await self._request("POST", "user/list", data=data)
        return self._validate_list_response(result, UserResponse, "users")
    
    # File operations
    async def list_files(self, limit: int = 20, offset: int = 0, task_id: Optional[int] = None, project_id: Optional[int] = None) -> List[FileResponse]:
        """List files."""
        data = {"pageSize": limit, "offset": offset}
        if task_id:
            data["taskId"] = task_id
        if project_id:
            data["projectId"] = project_id
            
        result = await self._request("POST", "file/list", data=data)
        return self._validate_list_response(result, FileResponse, "files")
    
    # Comment operations  
    async def list_comments(self, limit: int = 20, offset: int = 0, task_id: Optional[int] = None, project_id: Optional[int] = None) -> List[CommentResponse]:
        """List comments."""
        data = {
            "offset": offset,
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
    
    
    # Report operations
    async def list_reports(self, limit: int = 20, offset: int = 0) -> List[Report]:
        """List reports."""
        data = {"pageSize": limit, "offset": offset}
        result = await self._request("POST", "report/list", data=data)
        return self._validate_list_response(result, Report, "reports")
    
    # Process operations
    async def list_processes(self, limit: int = 20, offset: int = 0) -> List[Process]:
        """List processes."""
        data = {"pageSize": limit, "offset": offset}
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

