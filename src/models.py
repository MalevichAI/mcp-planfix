"""Pydantic models for Planfix entities generated from OpenAPI schemas."""

from typing import Optional, List, Union, Any, Dict
from pydantic import BaseModel, Field
from enum import Enum


class GenderEnum(str, Enum):
    """Gender enumeration."""
    NOT_DEFINED = "NotDefined"
    FEMALE = "Female"
    MALE = "Male"


class PriorityEnum(str, Enum):
    """Priority enumeration."""
    LOW = "Low"
    NORMAL = "Normal"
    HIGH = "High"
    URGENT = "Urgent"


class DurationUnitEnum(str, Enum):
    """Duration unit enumeration."""
    MINUTE = "Minute"
    HOUR = "Hour"
    DAY = "Day"
    WEEK = "Week"
    MONTH = "Month"


class DurationTypeEnum(str, Enum):
    """Duration type enumeration."""
    WORK_DAYS = "WorkDays"
    CALENDAR_DAYS = "CalendarDays"


# Base schemas
class BaseEntity(BaseModel):
    """Base entity with ID."""
    id: int = Field(..., description="Entity ID")


class ShortEntity(BaseModel):
    """Short entity reference."""
    id: Union[str, int] = Field(..., description="Entity ID")
    name: Optional[str] = Field(None, description="Entity name")


class TimePoint(BaseModel):
    """Time point representation."""
    date: Optional[str] = Field(None, description="Date in dd-MM-yyyy format")
    time: Optional[str] = Field(None, description="Time in HH:mm format")
    datetime: Optional[str] = Field(None, description="ISO format datetime")
    dateTimeUtcSeconds: Optional[str] = Field(None, description="ISO8601 format")


class ChangeDate(BaseModel):
    """Change date representation."""
    dateType: Optional[str] = Field(None, description="Date type")
    dateValue: Optional[str] = Field(None, description="Date value")
    dateFrom: Optional[str] = Field(None, description="Date from")
    dateTo: Optional[str] = Field(None, description="Date to")


# Phone related schemas
class PhoneRequest(BaseModel):
    """Phone request."""
    number: str = Field(..., description="Phone number")
    type: int = Field(..., description="Phone type")


class PhoneResponse(BaseModel):
    """Phone response."""
    number: Optional[str] = Field(None, description="Phone number")
    maskedNumber: Optional[str] = Field(None, description="Masked phone number")
    type: Optional[int] = Field(None, description="Phone type")


# Group schemas
class GroupRequest(BaseModel):
    """Group request."""
    id: int = Field(..., description="Group ID")


class GroupResponse(BaseModel):
    """Group response."""
    id: Optional[int] = Field(None, description="Group ID")
    name: Optional[str] = Field(None, description="Group name")


# People schemas
class PersonRequest(BaseModel):
    """Person request."""
    id: Union[str, int] = Field(..., description="Person ID")


class PersonResponse(BaseModel):
    """Person response."""
    id: Optional[Union[str, int]] = Field(None, description="Person ID")
    name: Optional[str] = Field(None, description="Person name")


class PeopleRequest(BaseModel):
    """People request."""
    users: Optional[List[PersonRequest]] = Field(None, description="Users list")
    groups: Optional[List[GroupRequest]] = Field(None, description="Groups list")


class PeopleResponse(BaseModel):
    """People response."""
    users: Optional[List[PersonResponse]] = Field(None, description="Users list")
    groups: Optional[List[GroupResponse]] = Field(None, description="Groups list")


class UserRequest(BaseModel):
    """User request."""
    id: Optional[Union[str, int]] = Field(None, description="User ID")


class UserResponse(BaseModel):
    """User response."""
    id: Optional[Union[str, int]] = Field(None, description="User ID")
    name: Optional[str] = Field(None, description="User name")


class NotifiedRequest(BaseModel):
    """Notified request."""
    users: Optional[List[UserRequest]] = Field(None, description="Users to notify")
    groups: Optional[List[GroupRequest]] = Field(None, description="Groups to notify")


# Company and position schemas
class CompanyEntity(BaseModel):
    """Company entity."""
    id: Optional[int] = Field(None, description="Company ID")
    name: Optional[str] = Field(None, description="Company name")


class PositionEntity(BaseModel):
    """Position entity."""
    id: Optional[int] = Field(None, description="Position ID")
    name: Optional[str] = Field(None, description="Position name")


# Custom field schemas
class CustomField(BaseModel):
    """Custom field definition."""
    id: int = Field(..., description="Field ID")
    name: Optional[str] = Field(None, description="Field name")
    type: Optional[int] = Field(None, description="Field type")
    objectType: Optional[int] = Field(None, description="Object type")
    directoryId: Optional[int] = Field(None, description="Directory ID for directory fields")


class CustomFieldValueRequest(BaseModel):
    """Custom field value request."""
    field: CustomField = Field(..., description="Field definition")
    value: Optional[Any] = Field(None, description="Field value")


class CustomFieldValueResponse(BaseModel):
    """Custom field value response."""
    field: Optional[CustomField] = Field(None, description="Field definition")
    value: Optional[Any] = Field(None, description="Field value")


# File schemas
class FileRequest(BaseModel):
    """File request."""
    id: int = Field(..., description="File ID")


class FileResponse(BaseModel):
    """File response."""
    id: Optional[int] = Field(None, description="File ID")
    name: Optional[str] = Field(None, description="File name")
    size: Optional[int] = Field(None, description="File size")
    created_date: Optional[str] = Field(None, description="Creation date")
    author: Optional[str] = Field(None, description="File author")


class FileUploadRequest(BaseModel):
    """File upload request."""
    file: bytes = Field(..., description="File content")
    filename: str = Field(..., description="File name")


# Directory schemas
class Directory(BaseModel):
    """Directory."""
    id: Optional[int] = Field(None, description="Directory ID")
    name: Optional[str] = Field(None, description="Directory name")


class DirectoryEntryRequest(BaseModel):
    """Directory entry request."""
    id: Union[str, int] = Field(..., description="Entry ID")


class DirectoryEntryResponse(BaseModel):
    """Directory entry response."""
    id: Optional[Union[str, int]] = Field(None, description="Entry ID")
    value: Optional[str] = Field(None, description="Entry value")


# Data tag schemas
class DataTag(BaseModel):
    """Data tag."""
    id: int = Field(..., description="Data tag ID")
    name: Optional[str] = Field(None, description="Data tag name")


class DataTagEntryCreateRequest(BaseModel):
    """Data tag entry create request."""
    dataTag: DataTag = Field(..., description="Data tag")
    items: List[Dict[str, Any]] = Field(..., description="Entry items")


class DataTagEntryResponse(BaseModel):
    """Data tag entry response."""
    dataTag: Optional[DataTag] = Field(None, description="Data tag")
    key: Optional[int] = Field(None, description="Entry key")


class DataTagEntryUpdateRequest(BaseModel):
    """Data tag entry update request."""
    key: int = Field(..., description="Entry key")
    customFieldData: Optional[List[CustomFieldValueRequest]] = Field(None, description="Custom field data")


# Task schemas
class TaskStatus(BaseModel):
    """Task status."""
    id: Optional[int] = Field(None, description="Status ID")
    name: Optional[str] = Field(None, description="Status name")


class Recurrence(BaseModel):
    """Task recurrence."""
    type: Optional[str] = Field(None, description="Recurrence type")
    interval: Optional[int] = Field(None, description="Recurrence interval")


class Reminder(BaseModel):
    """Task reminder."""
    id: Optional[int] = Field(None, description="Reminder ID")
    datetime: Optional[TimePoint] = Field(None, description="Reminder datetime")


class TaskCreateRequest(BaseModel):
    """Task create request."""
    template: Optional[BaseEntity] = Field(None, description="Task template")
    object: Optional[BaseEntity] = Field(None, description="Task object")
    sourceObjectId: Optional[str] = Field(None, description="Source object ID")
    sourceDataVersion: Optional[str] = Field(None, max_length=100, description="Source data version")
    name: str = Field(..., description="Task name")
    description: Optional[str] = Field(None, description="Task description")
    priority: Optional[PriorityEnum] = Field(None, description="Task priority")
    status: Optional[BaseEntity] = Field(None, description="Task status")
    processId: Optional[int] = Field(None, description="Process ID")
    resultChecking: Optional[bool] = Field(None, description="Result checking flag")
    type: Optional[str] = Field(None, description="Task type")
    assigner: Optional[PersonRequest] = Field(None, description="Task assigner")
    parent: Optional[BaseEntity] = Field(None, description="Parent task")
    project: Optional[BaseEntity] = Field(None, description="Project")
    counterparty: Optional[BaseEntity] = Field(None, description="Counterparty")
    dateTime: Optional[Union[TimePoint, str]] = Field(None, description="Task datetime")
    startDateTime: Optional[Union[TimePoint, str]] = Field(None, description="Start datetime")
    endDateTime: Optional[Union[TimePoint, str]] = Field(None, description="End datetime")
    hasStartDate: Optional[bool] = Field(None, description="Has start date flag")
    hasEndDate: Optional[bool] = Field(None, description="Has end date flag")
    hasStartTime: Optional[bool] = Field(None, description="Has start time flag")
    hasEndTime: Optional[bool] = Field(None, description="Has end time flag")
    duration: Optional[int] = Field(None, description="Task duration")
    durationUnit: Optional[DurationUnitEnum] = Field(None, description="Duration unit")
    durationType: Optional[DurationTypeEnum] = Field(None, description="Duration type")
    inFavorites: Optional[bool] = Field(None, description="In favorites flag")
    assignees: Optional[PeopleRequest] = Field(None, description="Task assignees")
    participants: Optional[PeopleRequest] = Field(None, description="Task participants")
    auditors: Optional[PeopleRequest] = Field(None, description="Task auditors")
    files: Optional[List[FileRequest]] = Field(None, description="Attached files")
    customFieldData: Optional[List[CustomFieldValueRequest]] = Field(None, description="Custom field data")


class TaskUpdateRequest(BaseModel):
    """Task update request."""
    sourceObjectId: Optional[str] = Field(None, description="Source object ID")
    sourceDataVersion: Optional[str] = Field(None, max_length=100, description="Source data version")
    name: Optional[str] = Field(None, description="Task name")
    description: Optional[str] = Field(None, description="Task description")
    priority: Optional[PriorityEnum] = Field(None, description="Task priority")
    status: Optional[BaseEntity] = Field(None, description="Task status")
    processId: Optional[int] = Field(None, description="Process ID")
    resultChecking: Optional[bool] = Field(None, description="Result checking flag")
    type: Optional[str] = Field(None, description="Task type")
    assigner: Optional[PersonRequest] = Field(None, description="Task assigner")
    parent: Optional[BaseEntity] = Field(None, description="Parent task")
    object: Optional[BaseEntity] = Field(None, description="Task object")
    template: Optional[BaseEntity] = Field(None, description="Task template")
    project: Optional[BaseEntity] = Field(None, description="Project")
    counterparty: Optional[BaseEntity] = Field(None, description="Counterparty")
    dateTime: Optional[Union[TimePoint, str]] = Field(None, description="Task datetime")
    startDateTime: Optional[Union[TimePoint, str]] = Field(None, description="Start datetime")
    endDateTime: Optional[Union[TimePoint, str]] = Field(None, description="End datetime")
    hasStartDate: Optional[bool] = Field(None, description="Has start date flag")
    hasEndDate: Optional[bool] = Field(None, description="Has end date flag")
    hasStartTime: Optional[bool] = Field(None, description="Has start time flag")
    hasEndTime: Optional[bool] = Field(None, description="Has end time flag")
    delayedTillDate: Optional[TimePoint] = Field(None, description="Delayed till date")
    duration: Optional[int] = Field(None, description="Task duration")
    durationUnit: Optional[DurationUnitEnum] = Field(None, description="Duration unit")
    durationType: Optional[DurationTypeEnum] = Field(None, description="Duration type")
    inFavorites: Optional[bool] = Field(None, description="In favorites flag")
    assignees: Optional[PeopleRequest] = Field(None, description="Task assignees")
    participants: Optional[PeopleRequest] = Field(None, description="Task participants")
    auditors: Optional[PeopleRequest] = Field(None, description="Task auditors")
    files: Optional[List[FileRequest]] = Field(None, description="Attached files")
    customFieldData: Optional[List[CustomFieldValueRequest]] = Field(None, description="Custom field data")


class TaskResponse(BaseModel):
    """Task response."""
    id: Optional[int] = Field(None, description="Task ID")
    template: Optional[BaseEntity] = Field(None, description="Task template")
    processId: Optional[int] = Field(None, description="Process ID")
    sourceObjectId: Optional[str] = Field(None, description="Source object ID")
    sourceDataVersion: Optional[str] = Field(None, description="Source data version")
    name: Optional[str] = Field(None, description="Task name")
    description: Optional[str] = Field(None, description="Task description")
    priority: Optional[str] = Field(None, description="Task priority")
    status: Optional[TaskStatus] = Field(None, description="Task status")
    resultChecking: Optional[bool] = Field(None, description="Result checking flag")
    type: Optional[str] = Field(None, description="Task type")
    assigner: Optional[PersonResponse] = Field(None, description="Task assigner")
    parent: Optional[BaseEntity] = Field(None, description="Parent task")
    object: Optional[BaseEntity] = Field(None, description="Task object")
    project: Optional[BaseEntity] = Field(None, description="Project")
    counterparty: Optional[BaseEntity] = Field(None, description="Counterparty")
    dateTime: Optional[TimePoint] = Field(None, description="Task datetime")
    startDateTime: Optional[TimePoint] = Field(None, description="Start datetime")
    endDateTime: Optional[TimePoint] = Field(None, description="End datetime")
    hasStartDate: Optional[bool] = Field(None, description="Has start date flag")
    hasEndDate: Optional[bool] = Field(None, description="Has end date flag")
    hasStartTime: Optional[bool] = Field(None, description="Has start time flag")
    hasEndTime: Optional[bool] = Field(None, description="Has end time flag")
    delayedTillDate: Optional[TimePoint] = Field(None, description="Delayed till date")
    actualCompletionDate: Optional[TimePoint] = Field(None, description="Actual completion date")
    dateOfLastUpdate: Optional[TimePoint] = Field(None, description="Last update date")
    duration: Optional[int] = Field(None, description="Task duration")
    durationUnit: Optional[str] = Field(None, description="Duration unit")
    durationType: Optional[str] = Field(None, description="Duration type")
    overdue: Optional[bool] = Field(None, description="Overdue flag")
    closeToDeadLine: Optional[bool] = Field(None, description="Close to deadline flag")
    notAcceptedInTime: Optional[bool] = Field(None, description="Not accepted in time flag")
    inFavorites: Optional[bool] = Field(None, description="In favorites flag")
    isSummary: Optional[bool] = Field(None, description="Is summary flag")
    isSequential: Optional[bool] = Field(None, description="Is sequential flag")
    assignees: Optional[PeopleResponse] = Field(None, description="Task assignees")
    participants: Optional[PeopleResponse] = Field(None, description="Task participants")
    auditors: Optional[PeopleResponse] = Field(None, description="Task auditors")
    recurrence: Optional[Recurrence] = Field(None, description="Task recurrence")
    isDeleted: Optional[bool] = Field(None, description="Is deleted flag")
    files: Optional[List[FileResponse]] = Field(None, description="Attached files")
    dataTags: Optional[List[DataTagEntryResponse]] = Field(None, description="Data tags")
    customFieldData: Optional[List[CustomFieldValueResponse]] = Field(None, description="Custom field data")


# Contact schemas
class ContactRequest(BaseModel):
    """Contact create/update request."""
    template: Optional[BaseEntity] = Field(None, description="Contact template")
    sourceObjectId: Optional[str] = Field(None, description="Source object ID")
    sourceDataVersion: Optional[str] = Field(None, max_length=100, description="Source data version")
    name: str = Field(..., description="Contact name")
    midname: Optional[str] = Field(None, description="Middle name")
    lastname: Optional[str] = Field(None, description="Last name")
    gender: Optional[GenderEnum] = Field(None, description="Gender")
    description: Optional[str] = Field(None, description="Contact description")
    address: Optional[str] = Field(None, description="Address")
    site: Optional[str] = Field(None, description="Website URL")
    email: Optional[str] = Field(None, description="Email address")
    additionalEmailAddresses: Optional[List[str]] = Field(None, description="Additional email addresses")
    skype: Optional[str] = Field(None, description="Skype username")
    telegramId: Optional[str] = Field(None, description="Telegram ID")
    telegram: Optional[str] = Field(None, description="Telegram URL")
    facebook: Optional[str] = Field(None, description="Facebook URL")
    instagram: Optional[str] = Field(None, description="Instagram URL")  
    vk: Optional[str] = Field(None, description="VK URL")
    position: Optional[str] = Field(None, description="Position")
    group: Optional[GroupRequest] = Field(None, description="Contact group")
    isCompany: Optional[bool] = Field(None, description="Is company flag")
    isDeleted: Optional[bool] = Field(None, description="Is deleted flag")
    birthDate: Optional[Union[TimePoint, str]] = Field(None, description="Birth date")
    supervisors: Optional[PeopleRequest] = Field(None, description="Supervisors")
    phones: Optional[List[PhoneRequest]] = Field(None, description="Phone numbers")
    companies: Optional[List[BaseEntity]] = Field(None, description="Companies")
    contacts: Optional[List[BaseEntity]] = Field(None, description="Contacts")
    files: Optional[List[FileRequest]] = Field(None, description="Attached files")
    customFieldData: Optional[List[CustomFieldValueRequest]] = Field(None, description="Custom field data")


class ContactResponse(BaseModel):
    """Contact response."""
    id: Optional[int] = Field(None, description="Contact ID")
    template: Optional[BaseEntity] = Field(None, description="Contact template")
    processId: Optional[int] = Field(None, description="Process ID")
    sourceObjectId: Optional[str] = Field(None, description="Source object ID")
    sourceDataVersion: Optional[str] = Field(None, description="Source data version")
    name: Optional[str] = Field(None, description="Contact name")
    midname: Optional[str] = Field(None, description="Middle name")
    lastname: Optional[str] = Field(None, description="Last name")
    gender: Optional[str] = Field(None, description="Gender")
    description: Optional[str] = Field(None, description="Contact description")
    address: Optional[str] = Field(None, description="Address")
    site: Optional[str] = Field(None, description="Website URL")
    email: Optional[str] = Field(None, description="Email address")
    additionalEmailAddresses: Optional[List[str]] = Field(None, description="Additional email addresses")
    skype: Optional[str] = Field(None, description="Skype username")
    telegramId: Optional[str] = Field(None, description="Telegram ID")
    telegram: Optional[str] = Field(None, description="Telegram URL")
    facebook: Optional[str] = Field(None, description="Facebook URL")
    instagram: Optional[str] = Field(None, description="Instagram URL")
    vk: Optional[str] = Field(None, description="VK URL")
    position: Optional[str] = Field(None, description="Position")
    group: Optional[GroupResponse] = Field(None, description="Contact group")
    isCompany: Optional[bool] = Field(None, description="Is company flag")
    isDeleted: Optional[bool] = Field(None, description="Is deleted flag")
    birthDate: Optional[TimePoint] = Field(None, description="Birth date")
    createdDate: Optional[TimePoint] = Field(None, description="Creation date")
    dateOfLastUpdate: Optional[TimePoint] = Field(None, description="Last update date")
    supervisors: Optional[PeopleResponse] = Field(None, description="Supervisors")
    phones: Optional[List[PhoneResponse]] = Field(None, description="Phone numbers")
    companies: Optional[List[CompanyEntity]] = Field(None, description="Companies")
    contacts: Optional[List[PersonResponse]] = Field(None, description="Contacts")
    files: Optional[List[FileResponse]] = Field(None, description="Attached files")
    dataTags: Optional[List[DataTagEntryResponse]] = Field(None, description="Data tags")
    customFieldData: Optional[List[CustomFieldValueResponse]] = Field(None, description="Custom field data")


# Project schemas
class ProjectRequest(BaseModel):
    """Project create request."""
    template: Optional[BaseEntity] = Field(None, description="Project template")
    sourceObjectId: Optional[str] = Field(None, description="Source object ID")
    sourceDataVersion: Optional[str] = Field(None, max_length=100, description="Source data version")
    name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    owner: Optional[PersonRequest] = Field(None, description="Project owner")
    client: Optional[BaseEntity] = Field(None, description="Project client")
    isDeleted: Optional[bool] = Field(None, description="Is deleted flag")
    startDate: Optional[Union[TimePoint, str]] = Field(None, description="Start date")
    endDate: Optional[Union[TimePoint, str]] = Field(None, description="End date")
    files: Optional[List[FileRequest]] = Field(None, description="Attached files")
    customFieldData: Optional[List[CustomFieldValueRequest]] = Field(None, description="Custom field data")


class ProjectUpdateRequest(BaseModel):
    """Project update request."""
    sourceObjectId: Optional[str] = Field(None, description="Source object ID")
    sourceDataVersion: Optional[str] = Field(None, max_length=100, description="Source data version")
    name: Optional[str] = Field(None, description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    owner: Optional[PersonRequest] = Field(None, description="Project owner")
    client: Optional[BaseEntity] = Field(None, description="Project client")
    isDeleted: Optional[bool] = Field(None, description="Is deleted flag")
    startDate: Optional[Union[TimePoint, str]] = Field(None, description="Start date")
    endDate: Optional[Union[TimePoint, str]] = Field(None, description="End date")
    files: Optional[List[FileRequest]] = Field(None, description="Attached files")
    customFieldData: Optional[List[CustomFieldValueRequest]] = Field(None, description="Custom field data")


class ProjectResponse(BaseModel):
    """Project response."""
    id: Optional[int] = Field(None, description="Project ID")
    template: Optional[BaseEntity] = Field(None, description="Project template")
    sourceObjectId: Optional[str] = Field(None, description="Source object ID")
    sourceDataVersion: Optional[str] = Field(None, description="Source data version")
    name: Optional[str] = Field(None, description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    owner: Optional[PersonResponse] = Field(None, description="Project owner")
    client: Optional[BaseEntity] = Field(None, description="Project client")
    isDeleted: Optional[bool] = Field(None, description="Is deleted flag")
    startDate: Optional[TimePoint] = Field(None, description="Start date")
    endDate: Optional[TimePoint] = Field(None, description="End date")
    createdDate: Optional[TimePoint] = Field(None, description="Creation date")
    dateOfLastUpdate: Optional[TimePoint] = Field(None, description="Last update date")
    files: Optional[List[FileResponse]] = Field(None, description="Attached files")
    dataTags: Optional[List[DataTagEntryResponse]] = Field(None, description="Data tags")
    customFieldData: Optional[List[CustomFieldValueResponse]] = Field(None, description="Custom field data")


# Comment schemas
class CommentCreateRequest(BaseModel):
    """Comment create request."""
    sourceId: Optional[str] = Field(None, description="Source ID")
    sourceObjectId: Optional[str] = Field(None, description="Source object ID")
    sourceDataVersion: Optional[str] = Field(None, max_length=100, description="Source data version")
    dateTime: Optional[Union[TimePoint, str]] = Field(None, description="Comment datetime")
    description: str = Field(..., description="Comment text")
    owner: Optional[PersonRequest] = Field(None, description="Comment owner")
    isPinned: Optional[bool] = Field(None, description="Is pinned flag")
    isHidden: Optional[bool] = Field(None, description="Is hidden flag")
    recipients: Optional[NotifiedRequest] = Field(None, description="Comment recipients")
    files: Optional[List[FileRequest]] = Field(None, description="Attached files")


class CommentUpdateRequest(BaseModel):
    """Comment update request."""
    description: Optional[str] = Field(None, description="Comment text")
    isPinned: Optional[bool] = Field(None, description="Is pinned flag")
    recipients: Optional[NotifiedRequest] = Field(None, description="Comment recipients")
    files: Optional[List[FileRequest]] = Field(None, description="Attached files")


class CommentResponse(BaseModel):
    """Comment response."""
    id: Optional[int] = Field(None, description="Comment ID")
    sourceObjectId: Optional[str] = Field(None, description="Source object ID")
    sourceDataVersion: Optional[str] = Field(None, description="Source data version")
    dateTime: Optional[TimePoint] = Field(None, description="Comment datetime")
    type: Optional[str] = Field(None, description="Comment type")
    fromType: Optional[str] = Field(None, description="From type")
    description: Optional[str] = Field(None, description="Comment text")
    contact: Optional[BaseEntity] = Field(None, description="Related contact")
    project: Optional[BaseEntity] = Field(None, description="Related project")
    owner: Optional[PersonResponse] = Field(None, description="Comment owner")
    isDeleted: Optional[bool] = Field(None, description="Is deleted flag")
    isPinned: Optional[bool] = Field(None, description="Is pinned flag")
    isHidden: Optional[bool] = Field(None, description="Is hidden flag")
    isNotRead: Optional[bool] = Field(None, description="Is not read flag")
    recipients: Optional[PeopleResponse] = Field(None, description="Comment recipients")
    reminders: Optional[List[Reminder]] = Field(None, description="Reminders")
    dataTags: Optional[List[DataTagEntryResponse]] = Field(None, description="Data tags")
    files: Optional[List[FileResponse]] = Field(None, description="Attached files")


# Report schemas
class ReportField(BaseModel):
    """Report field."""
    id: Optional[str] = Field(None, description="Field ID")
    name: Optional[str] = Field(None, description="Field name")
    type: Optional[str] = Field(None, description="Field type")


class ReportSaveDataItem(BaseModel):
    """Report save data item."""
    field: Optional[ReportField] = Field(None, description="Field definition")
    value: Optional[Any] = Field(None, description="Field value")


class ReportSaveDataRow(BaseModel):
    """Report save data row."""
    items: Optional[List[ReportSaveDataItem]] = Field(None, description="Row items")


class ReportSaveData(BaseModel):
    """Report save data."""
    rows: Optional[List[ReportSaveDataRow]] = Field(None, description="Data rows")


class ReportSave(BaseModel):
    """Report save."""
    data: Optional[ReportSaveData] = Field(None, description="Report data")


class Report(BaseModel):
    """Report."""
    id: Optional[int] = Field(None, description="Report ID")
    name: Optional[str] = Field(None, description="Report name")
    description: Optional[str] = Field(None, description="Report description")
    fields: Optional[List[ReportField]] = Field(None, description="Report fields")
    data: Optional[ReportSaveData] = Field(None, description="Report data")


# Object and checklist schemas
class ObjectResponse(BaseModel):
    """Object response."""
    id: Optional[int] = Field(None, description="Object ID")
    name: Optional[str] = Field(None, description="Object name")
    description: Optional[str] = Field(None, description="Object description")


class ChecklistItemResponse(BaseModel):
    """Checklist item response."""
    id: Optional[int] = Field(None, description="Checklist item ID")
    name: Optional[str] = Field(None, description="Item name")
    isCompleted: Optional[bool] = Field(None, description="Is completed flag")
    order: Optional[int] = Field(None, description="Item order")


# Filter schemas
class Filter(BaseModel):
    """Filter."""
    id: Optional[str] = Field(None, description="Filter ID")
    name: Optional[str] = Field(None, description="Filter name")
    owner: Optional[PersonResponse] = Field(None, description="Filter owner")


# Complex filter schemas
class ComplexContactFilter(BaseModel):
    """Complex contact filter."""
    type: int = Field(..., description="Filter type")
    operator: str = Field(..., description="Filter operator")
    value: Optional[Any] = Field(None, description="Filter value")
    field: Optional[int] = Field(None, description="Custom field ID")
    subfilter: Optional[Dict[str, Any]] = Field(None, description="Subfilter data")


class ComplexTaskFilter(BaseModel):
    """Complex task filter."""
    type: int = Field(..., description="Filter type")
    operator: str = Field(..., description="Filter operator")
    value: Optional[Any] = Field(None, description="Filter value")
    field: Optional[int] = Field(None, description="Custom field ID")
    subfilter: Optional[Dict[str, Any]] = Field(None, description="Subfilter data")


class ComplexProjectFilter(BaseModel):
    """Complex project filter."""
    type: int = Field(..., description="Filter type")
    operator: str = Field(..., description="Filter operator")
    value: Optional[Any] = Field(None, description="Filter value")
    field: Optional[int] = Field(None, description="Custom field ID")
    subfilter: Optional[Dict[str, Any]] = Field(None, description="Subfilter data")


class ComplexUserFilter(BaseModel):
    """Complex user filter."""
    type: int = Field(..., description="Filter type")
    operator: str = Field(..., description="Filter operator")
    value: Optional[Any] = Field(None, description="Filter value")
    field: Optional[int] = Field(None, description="Custom field ID")


class ComplexDirectoryFilter(BaseModel):
    """Complex directory filter."""
    type: int = Field(..., description="Filter type")
    operator: str = Field(..., description="Filter operator")
    value: Optional[Any] = Field(None, description="Filter value")
    field: Optional[int] = Field(None, description="Custom field ID")


class ComplexDataTagFilter(BaseModel):
    """Complex data tag filter."""
    type: int = Field(..., description="Filter type")
    operator: str = Field(..., description="Filter operator")
    value: Optional[Any] = Field(None, description="Filter value")
    field: Optional[int] = Field(None, description="Custom field ID")


# Error response schema
class ApiResponseError(BaseModel):
    """API error response."""
    result: str = Field(..., description="Result status")
    code: Optional[int] = Field(None, description="Error code")
    error: Optional[str] = Field(None, description="Error message")


# Legacy models for backwards compatibility
class Task(BaseModel):
    """Legacy Task model for backwards compatibility."""
    id: int
    name: str
    description: Optional[str] = None
    status: Optional[str] = None
    assignee: Optional[str] = None
    project: Optional[str] = None
    priority: Optional[str] = None
    deadline: Optional[str] = None


class Project(BaseModel):
    """Legacy Project model for backwards compatibility."""
    id: int
    name: str
    description: Optional[str] = None
    status: Optional[str] = None
    owner: Optional[str] = None
    client: Optional[str] = None
    task_count: Optional[int] = 0


class Contact(BaseModel):
    """Legacy Contact model for backwards compatibility."""
    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    midname: Optional[str] = None
    lastname: Optional[str] = None
    description: Optional[str] = None
    is_company: Optional[bool] = None
    created_date: Optional[str] = None


class Employee(BaseModel):
    """Legacy Employee model for backwards compatibility."""
    id: int
    name: str
    email: Optional[str] = None
    position: Optional[str] = None
    status: Optional[str] = None
    last_activity: Optional[str] = None


class Comment(BaseModel):
    """Legacy Comment model for backwards compatibility."""
    id: int
    text: str
    author: Optional[str] = None
    created_date: Optional[str] = None
    task_id: Optional[int] = None
    project_id: Optional[int] = None


class File(BaseModel):
    """Legacy File model for backwards compatibility."""
    id: int
    name: str
    size: Optional[int] = None
    created_date: Optional[str] = None
    author: Optional[str] = None
    task_id: Optional[int] = None
    project_id: Optional[int] = None


class Process(BaseModel):
    """Legacy Process model for backwards compatibility."""
    id: int
    name: str
    description: Optional[str] = None
    status: Optional[str] = None
    created_date: Optional[str] = None 