# backend/config.py
"""Application Configuration"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "AI Migration Agent"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    SECRET_KEY: str
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis
    REDIS_URL: str
    REDIS_PASSWORD: Optional[str] = None
    
    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # GitHub OAuth
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    GITHUB_REDIRECT_URI: str
    
    # Groq API
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    
    # ✅ NEW: Fallback LLM API Keys
    GOOGLE_API_KEY: Optional[str] = None
    MISTRAL_API_KEY: Optional[str] = None
    
    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    CELERY_TASK_TIME_LIMIT: int = 1800
    CELERY_SOFT_TIME_LIMIT: int = 1500
    
    # Docker Sandbox
    DOCKER_TIMEOUT: int = 300
    DOCKER_MEMORY_LIMIT: str = "2g"
    DOCKER_CPU_LIMIT: float = 0.5
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 104857600
    TEMP_DIR: str = "/tmp/migration_agent"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Ensure temp directory exists
os.makedirs(settings.TEMP_DIR, exist_ok=True)
os.makedirs("logs", exist_ok=True)
os.makedirs("reports", exist_ok=True)
