# backend/models/repository.py
"""Repository models for GitHub integration"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Integer, JSON, BigInteger  # ✅ Add BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from backend.core.database import Base

class Repository(Base):
    """Repository model"""
    
    __tablename__ = "repositories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    
    # GitHub info
    github_id = Column(BigInteger, unique=True)  # GitHub repo ID
    name = Column(String(255), nullable=False)
    full_name = Column(String(500), nullable=False)  # username/repo
    clone_url = Column(String(500))
    html_url = Column(String(500))
    description = Column(Text, nullable=True)
    
    # Analysis results
    language = Column(String(100), nullable=True)  # Primary language
    framework = Column(String(100), nullable=True)  # Detected framework
    dependencies = Column(JSON, default={})  # Parsed dependencies
    file_count = Column(Integer, default=0)
    
    # Status
    is_imported = Column(Boolean, default=False)
    last_analyzed = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="repositories")
    migrations = relationship("MigrationJob", back_populates="repository", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Repository {self.full_name}>"

class MigrationJob(Base):
    """Migration job model"""
    
    __tablename__ = "migration_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    
    # Migration details
    framework = Column(String(100))
    from_version = Column(String(50))
    to_version = Column(String(50))
    
    # Status
    status = Column(String(50), default="queued")  # queued, running, completed, failed
    progress = Column(Integer, default=0)
    
    # Results
    files_modified = Column(Integer, default=0)
    tests_passed = Column(Integer, default=0)
    tests_failed = Column(Integer, default=0)
    build_success = Column(Boolean, default=False)
    
    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration = Column(Integer, default=0)  # seconds
    
    # Report
    report_path = Column(String(500), nullable=True)
    report_data = Column(JSON, default={})
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    repository = relationship("Repository", back_populates="migrations")
    user = relationship("User", back_populates="migrations")
    
    def __repr__(self):
        return f"<MigrationJob {self.id} - {self.status}>"