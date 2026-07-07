# backend/schemas/auth.py
"""Authentication schemas for request/response validation"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
import uuid

# ===== Request Schemas =====

class UserCreate(BaseModel):
    """User registration schema"""
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=8, max_length=72, description="Password")
    full_name: Optional[str] = Field(None, max_length=100, description="Full name")
    

    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        # ✅ First check: length
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if len(v) > 72:
            raise ValueError('Password must be 72 characters or less')
        
        # ✅ Check requirements
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        
        # ✅ Password must contain at least one special character (optional but recommended)
        # if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?/~`' for c in v):
        #     raise ValueError('Password must contain at least one special character')
        
        return v

class UserLogin(BaseModel):
    """User login schema"""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="Password")

class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str = Field(..., description="Refresh token")

class UserUpdate(BaseModel):
    """User update schema"""
    full_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    company: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=200)
    preferences: Optional[dict] = None

# ===== Response Schemas =====

class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")

class TokenData(BaseModel):
    """Token data schema"""
    user_id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="User email")
    exp: int = Field(..., description="Expiration timestamp")

class UserResponse(BaseModel):
    """User response schema"""
    id: uuid.UUID = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    username: str = Field(..., description="Username")
    full_name: Optional[str] = Field(None, description="Full name")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    github_id: Optional[str] = Field(None, description="GitHub user ID")
    is_active: bool = Field(..., description="Is user active")
    is_verified: bool = Field(..., description="Is user verified")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    created_at: datetime = Field(..., description="Account creation timestamp")
    
    class Config:
        """Pydantic config"""
        from_attributes = True

class ProfileResponse(BaseModel):
    """User profile response"""
    id: uuid.UUID
    user_id: uuid.UUID
    bio: Optional[str]
    company: Optional[str]
    location: Optional[str]
    website: Optional[str]
    github_username: Optional[str]
    preferences: dict
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class AuthResponse(BaseModel):
    """Authentication response"""
    user: UserResponse
    tokens: TokenResponse