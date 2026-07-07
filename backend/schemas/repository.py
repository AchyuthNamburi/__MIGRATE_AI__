# backend/schemas/repository.py
"""Repository schemas for request/response validation"""

from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Dict, List
from datetime import datetime
import uuid

class RepositoryImport(BaseModel):
    """Repository import request"""
    url: str = Field(..., description="GitHub repository URL")
    branch: Optional[str] = Field("main", description="Branch to clone")

class RepositoryResponse(BaseModel):
    """Repository response"""
    id: uuid.UUID
    name: str
    full_name: str
    language: Optional[str]
    framework: Optional[str]
    file_count: int
    is_imported: bool
    status: Optional[str] = "Ready"
    created_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class RepositoryDetailResponse(RepositoryResponse):
    """Repository detail response"""
    dependencies: Optional[Dict] = {}
    clone_url: Optional[str]
    html_url: Optional[str]
    description: Optional[str]
    last_analyzed: Optional[datetime]