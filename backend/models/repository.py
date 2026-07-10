# backend/models/repository.py
"""Repository models for GitHub integration"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Integer, JSON, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from backend.core.database import Base

class Repository(Base):
    __tablename__ = "repositories"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    github_id = Column(BigInteger, nullable=True)
    name = Column(String(255), nullable=False)
    full_name = Column(String(500), nullable=False)
    clone_url = Column(String(500))
    html_url = Column(String(500))
    description = Column(Text, nullable=True)
    language = Column(String(100), nullable=True)
    framework = Column(String(100), nullable=True)
    dependencies = Column(JSON, default={})
    file_count = Column(Integer, default=0)
    is_imported = Column(Boolean, default=False)
    last_analyzed = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ✅ Comment out relationships for now
    # user = relationship("User", back_populates="repositories")
    # migrations = relationship("MigrationJob", back_populates="repository", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Repository {self.full_name}>"

class MigrationJob(Base):
    __tablename__ = "migration_jobs"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    framework = Column(String(100))
    from_version = Column(String(50))
    to_version = Column(String(50))
    status = Column(String(50), default="queued")
    progress = Column(Integer, default=0)
    files_modified = Column(Integer, default=0)
    tests_passed = Column(Integer, default=0)
    tests_failed = Column(Integer, default=0)
    build_success = Column(Boolean, default=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration = Column(Integer, default=0)
    report_path = Column(String(500), nullable=True)
    report_data = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ✅ Comment out relationships for now
    # repository = relationship("Repository", back_populates="migrations")
    # user = relationship("User", back_populates="migrations")

    def __repr__(self):
        return f"<MigrationJob {self.id} - {self.status}>"
