# backend/models/migration.py
"""Migration models for tracking migration jobs"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Integer, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from backend.core.database import Base

class MigrationJob(Base):
    """Migration job model"""
    __tablename__ = "migration_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    
    repo_url = Column(String(500), nullable=False)
    repo_name = Column(String(255))
    framework = Column(String(100))
    from_version = Column(String(50))
    to_version = Column(String(50))
    
    status = Column(String(50), default="queued")
    progress = Column(Integer, default=0)
    confidence_score = Column(Float, default=0.0)
    
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration = Column(Integer, default=0)
    
    files_modified = Column(Integer, default=0)
    tests_passed = Column(Integer, default=0)
    tests_failed = Column(Integer, default=0)
    test_coverage = Column(Float, default=0.0)
    
    output_path = Column(String(500))
    report_path = Column(String(500))
    diff_path = Column(String(500))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="migrations")
    files = relationship("MigrationFile", back_populates="migration", cascade="all, delete-orphan")
    reviews = relationship("MigrationReview", back_populates="migration", cascade="all, delete-orphan")
    history = relationship("MigrationHistory", back_populates="migration", cascade="all, delete-orphan")

class MigrationFile(Base):
    """Per-file migration tracking"""
    __tablename__ = "migration_files"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    migration_id = Column(UUID(as_uuid=True), ForeignKey("migration_jobs.id", ondelete="CASCADE"))
    
    file_path = Column(String(500))
    file_type = Column(String(50))
    status = Column(String(50), default="pending")
    changes_made = Column(Text)
    old_content = Column(Text)
    new_content = Column(Text)
    confidence = Column(Float, default=0.0)
    error_message = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    migration = relationship("MigrationJob", back_populates="files")

class MigrationReview(Base):
    """HITL review tracking"""
    __tablename__ = "migration_reviews"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    migration_id = Column(UUID(as_uuid=True), ForeignKey("migration_jobs.id", ondelete="CASCADE"))
    file_id = Column(UUID(as_uuid=True), ForeignKey("migration_files.id", ondelete="CASCADE"))
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    
    decision = Column(String(50))  # approved, rejected, modified
    comments = Column(Text)
    reviewed_at = Column(DateTime, default=datetime.utcnow)
    
    migration = relationship("MigrationJob", back_populates="reviews")

class MigrationHistory(Base):
    """Audit log for migration jobs"""
    __tablename__ = "migration_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    migration_id = Column(UUID(as_uuid=True), ForeignKey("migration_jobs.id", ondelete="CASCADE"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    
    action = Column(String(100))
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    migration = relationship("MigrationJob", back_populates="history")