# backend/routes/auth.py
"""Authentication routes"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from backend.core.database import get_db
from backend.services.auth_service import AuthService
from backend.schemas.auth import (
    UserCreate, UserLogin, UserUpdate, 
    TokenResponse, UserResponse, RefreshTokenRequest
)
from backend.middleware.auth_middleware import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

# ===== User Registration =====

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user
    
    Args:
        user_data: User registration data
        db: Database session
    
    Returns:
        UserResponse: Created user data
    """
    try:
        auth_service = AuthService(db)
        user = await auth_service.register_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

# ===== User Login =====

@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login user and return tokens
    
    Args:
        credentials: Login credentials
        db: Database session
    
    Returns:
        TokenResponse: Access and refresh tokens
    """
    try:
        auth_service = AuthService(db)
        tokens = await auth_service.authenticate_user(
            email=credentials.email,
            password=credentials.password
        )
        return tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

# ===== Token Refresh =====

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token
    
    Args:
        refresh_data: Refresh token
        db: Database session
    
    Returns:
        TokenResponse: New access and refresh tokens
    """
    try:
        auth_service = AuthService(db)
        tokens = await auth_service.refresh_tokens(refresh_data.refresh_token)
        return tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

# ===== Get Current User =====

@router.get("/me", response_model=UserResponse)
async def get_current_user_endpoint(
    current_user = Depends(get_current_user)
):
    """
    Get current authenticated user
    
    Args:
        current_user: Current user from token
    
    Returns:
        UserResponse: Current user data
    """
    return current_user

# ===== Update User Profile =====

@router.put("/profile", response_model=UserResponse)
async def update_profile(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Update current user profile
    
    Args:
        user_update: User update data
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        UserResponse: Updated user data
    """
    try:
        auth_service = AuthService(db)
        updated_user = await auth_service.update_user(
            user_id=current_user.id,
            update_data=user_update
        )
        return updated_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Profile update error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )

# ===== Logout =====

@router.post("/logout")
async def logout(
    current_user = Depends(get_current_user)
):
    """
    Logout current user
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        dict: Logout success message
    """
    # In JWT-based auth, logout is client-side
    # We just return success
    return {"message": "Successfully logged out"}

# ===== GitHub OAuth =====

@router.get("/github/login")
async def github_login():
    """
    Redirect to GitHub OAuth
    """
    from backend.config import settings
    from urllib.parse import urlencode
    
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": settings.GITHUB_REDIRECT_URI,
        "scope": "repo,user:email",
        "allow_signup": "true"
    }
    
    auth_url = "https://github.com/login/oauth/authorize?" + urlencode(params)
    return RedirectResponse(url=auth_url)

@router.get("/github/callback")
async def github_callback(
    code: str,
    state: str = None,
    db: Session = Depends(get_db)
):
    """
    GitHub OAuth callback handler
    
    Args:
        code: OAuth code from GitHub
        state: OAuth state
        db: Database session
    
    Returns:
        RedirectResponse: Redirect to frontend with tokens
    """
    try:
        auth_service = AuthService(db)
        tokens = await auth_service.github_oauth_callback(code)
        
        # Redirect to frontend with tokens
        redirect_url = f"http://localhost:3000/auth/callback?access_token={tokens['access_token']}&refresh_token={tokens['refresh_token']}"
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        logger.error(f"GitHub OAuth error: {str(e)}")
        return RedirectResponse(url="http://localhost:3000/login?error=oauth_failed")