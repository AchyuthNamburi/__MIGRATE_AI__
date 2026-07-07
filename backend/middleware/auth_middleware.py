# backend/middleware/auth_middleware.py
"""Authentication middleware for protected routes"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
import uuid
import logging

from backend.core.database import get_db
from backend.core.security import security
from backend.models.user import User
from backend.schemas.auth import UserResponse

logger = logging.getLogger(__name__)

# Security scheme
security_scheme = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token
    
    Args:
        credentials: HTTP Bearer credentials
        db: Database session
    
    Returns:
        User: Current authenticated user
    
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Get token
        token = credentials.credentials
        
        # Verify token
        payload = security.verify_token(token)
        
        # Extract user ID
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Get user
        user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return user
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"}
        )

async def require_auth(request: Request):
    """
    Dependency for routes that require authentication but don't need user data
    
    Args:
        request: FastAPI request
    
    Returns:
        bool: True if authenticated
    """
    # Get token from header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = auth_header.split(" ")[1]
    
    try:
        # Verify token
        payload = security.verify_token(token)
        request.state.user_id = payload.get("sub")
        return True
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )