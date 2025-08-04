"""Pydantic models for Planfix entities."""

from typing import Optional
from pydantic import BaseModel


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
    midname: Optional[str] = None
    lastname: Optional[str] = None
    description: Optional[str] = None
    is_company: Optional[bool] = None
    created_date: Optional[str] = None


class Employee(BaseModel):
    """Employee model."""
    id: int
    name: str
    email: Optional[str] = None
    position: Optional[str] = None
    status: Optional[str] = None
    last_activity: Optional[str] = None


class Comment(BaseModel):
    """Comment model."""
    id: int
    text: str
    author: Optional[str] = None
    created_date: Optional[str] = None
    task_id: Optional[int] = None
    project_id: Optional[int] = None


class File(BaseModel):
    """File model."""
    id: int
    name: str
    size: Optional[int] = None
    created_date: Optional[str] = None
    author: Optional[str] = None
    task_id: Optional[int] = None
    project_id: Optional[int] = None


class Report(BaseModel):
    """Report model."""
    id: int
    name: str
    description: Optional[str] = None
    created_date: Optional[str] = None


class Process(BaseModel):
    """Process model."""
    id: int
    name: str
    description: Optional[str] = None
    status: Optional[str] = None
    created_date: Optional[str] = None 