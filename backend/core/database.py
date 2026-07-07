# backend/core/database.py
"""Database configuration and session management"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/migration_db")

# Create database engine
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=True  # Set to False in production
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency
    
    Yields:
        Session: Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database - create all tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise