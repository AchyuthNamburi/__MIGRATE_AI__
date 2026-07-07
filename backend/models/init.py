# backend/models/__init__.py
"""Database models package"""

from backend.models.user import User, UserProfile

__all__ = ["User", "UserProfile"]