# backend/models/user.py
"""User models for authentication"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, JSON  # ← Add JSON here
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from backend.core.database import Base


class User(Base):
    """User model for authentication"""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # Nullable for OAuth users
    github_id = Column(String(100), unique=True, nullable=True)
    github_token = Column(Text, nullable=True)  # Encrypted
    full_name = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    repositories = relationship("Repository", back_populates="user", cascade="all, delete-orphan")
    migrations = relationship("MigrationJob", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.username}>"

class UserProfile(Base):
    """User profile model"""
    
    __tablename__ = "user_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    bio = Column(Text, nullable=True)
    company = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    website = Column(String(500), nullable=True)
    twitter_handle = Column(String(100), nullable=True)
    github_username = Column(String(100), nullable=True)
    preferences = Column(JSON, default={})  # JSON settings
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="profile")
    
    def __repr__(self):
        return f"<UserProfile {self.user_id}>"