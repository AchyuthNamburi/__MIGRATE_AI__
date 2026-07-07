# backend/services/auth_service.py
"""Authentication service business logic"""

from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime
import httpx
import logging
from typing import Optional, Dict, Any
import uuid

from backend.models.user import User, UserProfile
from backend.schemas.auth import UserCreate, UserUpdate, TokenResponse
from backend.core.security import security

logger = logging.getLogger(__name__)

class AuthService:
    """Authentication service"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def register_user(self, user_data: UserCreate) -> User:
        """
        Register a new user
        
        Args:
            user_data: User creation data
        
        Returns:
            User: Created user
        
        Raises:
            ValueError: If email or username already exists
        """
        # Check if user exists
        existing_user = self.db.query(User).filter(
            or_(User.email == user_data.email, User.username == user_data.username)
        ).first()
        
        if existing_user:
            if existing_user.email == user_data.email:
                raise ValueError("Email already registered")
            else:
                raise ValueError("Username already taken")
        
        # ✅ CRITICAL FIX: Truncate password to 72 bytes for bcrypt
        # Bcrypt has a 72-byte limit - this is a hard limit
        password = user_data.password[:72]
        
        # Create user
        user = User(
            email=user_data.email,
            username=user_data.username.lower(),
            password_hash=security.hash_password(password),  # Pass truncated password
            full_name=user_data.full_name,
            is_active=True,
            is_verified=False
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        # Create user profile
        profile = UserProfile(
            user_id=user.id,
            preferences={}
        )
        self.db.add(profile)
        self.db.commit()
        
        return user
    
    async def authenticate_user(self, email: str, password: str) -> Dict[str, str]:
        """
        Authenticate user and generate tokens
        
        Args:
            email: User email
            password: User password
        
        Returns:
            Dict: Access and refresh tokens
        
        Raises:
            ValueError: If authentication fails
        """
        # Get user
        user = self.db.query(User).filter(User.email == email).first()
        
        if not user:
            raise ValueError("Invalid email or password")
        
        if not user.is_active:
            raise ValueError("Account is disabled")
        
        # ✅ CRITICAL FIX: Truncate password to 72 bytes for bcrypt
        password = password[:72]
        
        # Verify password
        if not security.verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")
        
        # Update last login
        user.last_login = datetime.utcnow()
        self.db.commit()
        
        # Generate tokens
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "username": user.username
        }
        
        access_token = security.create_access_token(token_data)
        refresh_token = security.create_refresh_token(token_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 30 * 60  # 30 minutes
        }
    
    async def refresh_tokens(self, refresh_token: str) -> Dict[str, str]:
        """
        Refresh access token
        
        Args:
            refresh_token: Refresh token
        
        Returns:
            Dict: New access and refresh tokens
        
        Raises:
            ValueError: If token is invalid
        """
        try:
            # Verify refresh token
            payload = security.verify_token(refresh_token, token_type="refresh")
            
            user_id = payload.get("sub")
            if not user_id:
                raise ValueError("Invalid token payload")
            
            user = self.db.query(User).filter(User.id == uuid.UUID(user_id)).first()
            if not user or not user.is_active:
                raise ValueError("User not found or inactive")
            
            # Generate new tokens
            token_data = {
                "sub": str(user.id),
                "email": user.email,
                "username": user.username
            }
            
            new_access_token = security.create_access_token(token_data)
            new_refresh_token = security.create_refresh_token(token_data)
            
            return {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
                "expires_in": 30 * 60
            }
            
        except ValueError as e:
            raise ValueError(f"Invalid refresh token: {str(e)}")
    
    async def update_user(self, user_id: uuid.UUID, update_data: UserUpdate) -> User:
        """
        Update user profile
        
        Args:
            user_id: User ID
            update_data: Update data
        
        Returns:
            User: Updated user
        
        Raises:
            ValueError: If user not found
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Update user fields
        if update_data.full_name is not None:
            user.full_name = update_data.full_name
        
        user.updated_at = datetime.utcnow()
        
        # Update profile
        if any([update_data.bio, update_data.company, update_data.location, 
                update_data.website, update_data.preferences]):
            
            profile = user.profile
            if not profile:
                profile = UserProfile(user_id=user.id)
                self.db.add(profile)
            
            if update_data.bio is not None:
                profile.bio = update_data.bio
            if update_data.company is not None:
                profile.company = update_data.company
            if update_data.location is not None:
                profile.location = update_data.location
            if update_data.website is not None:
                profile.website = update_data.website
            if update_data.preferences is not None:
                profile.preferences = update_data.preferences
            
            profile.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    async def github_oauth_callback(self, code: str) -> Dict[str, str]:
        """
        Handle GitHub OAuth callback
        
        Args:
            code: OAuth code
        
        Returns:
            Dict: Access and refresh tokens
        
        Raises:
            ValueError: If GitHub authentication fails
        """
        from backend.config import settings
        
        # Exchange code for access token
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": settings.GITHUB_REDIRECT_URI
                }
            )
            
            if response.status_code != 200:
                raise ValueError("Failed to get access token from GitHub")
            
            token_data = response.json()
            if "error" in token_data:
                raise ValueError(f"GitHub error: {token_data['error']}")
            
            access_token = token_data["access_token"]
        
        # Get GitHub user info
        async with httpx.AsyncClient() as client:
            user_response = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"token {access_token}"}
            )
            
            if user_response.status_code != 200:
                raise ValueError("Failed to get user info from GitHub")
            
            github_user = user_response.json()
            
            # Get user emails
            email_response = await client.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"token {access_token}"}
            )
            emails = email_response.json()
            
            # Get primary email
            primary_email = next(
                (e["email"] for e in emails if e["primary"]), 
                emails[0]["email"] if emails else None
            )
        
        # Find or create user
        user = self.db.query(User).filter(User.github_id == str(github_user["id"])).first()
        
        if not user and primary_email:
            user = self.db.query(User).filter(User.email == primary_email).first()
        
        if not user:
            # Create new user
            username = github_user.get("login", f"gh_{github_user['id']}")
            email = primary_email or f"{github_user['id']}@github.user"
            
            user = User(
                email=email,
                username=username,
                github_id=str(github_user["id"]),
                github_token=security.encrypt_data(access_token),
                full_name=github_user.get("name", username),
                avatar_url=github_user.get("avatar_url"),
                is_active=True,
                is_verified=True,
                last_login=datetime.utcnow()
            )
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            # Create profile
            profile = UserProfile(
                user_id=user.id,
                github_username=username,
                preferences={}
            )
            self.db.add(profile)
            self.db.commit()
        else:
            # Update existing user
            user.github_id = str(github_user["id"])
            user.github_token = security.encrypt_data(access_token)
            user.full_name = github_user.get("name", user.full_name)
            user.avatar_url = github_user.get("avatar_url", user.avatar_url)
            user.last_login = datetime.utcnow()
            user.is_verified = True
            
            if user.profile:
                user.profile.github_username = github_user.get("login")
            
            self.db.commit()
            self.db.refresh(user)
        
        # Generate tokens
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "username": user.username
        }
        
        return {
            "access_token": security.create_access_token(token_data),
            "refresh_token": security.create_refresh_token(token_data),
            "token_type": "bearer",
            "expires_in": 30 * 60
        }
    
    def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()