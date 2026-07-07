# backend/middleware/__init__.py
"""Middleware package"""

from backend.middleware.auth_middleware import get_current_user, require_auth

__all__ = ["get_current_user", "require_auth"]