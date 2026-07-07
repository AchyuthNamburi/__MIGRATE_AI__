# backend/core/security.py
"""Security utilities for authentication and encryption"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from jose import JWTError
import secrets
import hashlib
import hmac
from cryptography.fernet import Fernet

from backend.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

class SecurityManager:
    """Security manager for authentication and encryption"""
    
    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        self.fernet = Fernet(Fernet.generate_key())
    
    # ===== Password Hashing =====
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        # ✅ Force truncation to 72 bytes for bcrypt compatibility
        if isinstance(password, str):
            # Convert to bytes, truncate, then back to string
            password_bytes = password.encode('utf-8')[:72]
            password = password_bytes.decode('utf-8', errors='ignore')
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        # ✅ Truncate to 72 bytes for bcrypt compatibility
        if isinstance(plain_password, str):
            password_bytes = plain_password.encode('utf-8')[:72]
            plain_password = password_bytes.decode('utf-8', errors='ignore')
        return pwd_context.verify(plain_password, hashed_password)
    
    # ===== JWT Tokens =====
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create a JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode and verify a JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            raise ValueError(f"Invalid token: {str(e)}")
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify a JWT token"""
        try:
            payload = self.decode_token(token)
            if payload.get("type") != token_type:
                raise ValueError(f"Invalid token type: expected {token_type}")
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.JWTError:
            raise ValueError("Invalid token")
    
    # ===== Encryption =====
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        return self.fernet.decrypt(encrypted_data.encode()).decode()
    
    # ===== API Key Generation =====
    
    def generate_api_key(self) -> str:
        """Generate a secure API key"""
        return secrets.token_urlsafe(32)
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash an API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    # ===== CSRF Token =====
    
    def generate_csrf_token(self) -> str:
        """Generate a CSRF token"""
        return secrets.token_urlsafe(32)
    
    # ===== Rate Limiting =====
    
    def get_rate_limit_key(self, user_id: str, endpoint: str) -> str:
        """Get rate limit key for a user and endpoint"""
        return f"rate_limit:{user_id}:{endpoint}"

# Create security manager instance
security = SecurityManager()