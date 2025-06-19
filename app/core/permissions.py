"""
LEGACY PERMISSION FILE - REPLACED WITH NEW SYSTEM
This file is deprecated. Use app.core.permission_middleware instead.
"""

from typing import Callable
from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user
from app.models.user import User


def require_permission(permission_name: str) -> Callable:
    """LEGACY FUNCTION - REMOVED TO FORCE MIGRATION"""
    raise NotImplementedError(
        f"Legacy permission system removed. Use new permission middleware instead.\n"
        f"Replace: from app.core.permissions import require_permission\n"
        f"With: from app.core.permission_middleware import require_permission\n"
        f"Update permission name '{permission_name}' to dot notation (e.g., 'person.register')\n"
        f"See cursor rules for permission mapping."
    )


def require_any_permission(*permission_names: str) -> Callable:
    """LEGACY FUNCTION - REMOVED TO FORCE MIGRATION"""
    raise NotImplementedError(
        f"Legacy permission system removed. Use new permission middleware instead.\n"
        f"Replace: from app.core.permissions import require_any_permission\n"
        f"With: from app.core.permission_middleware import require_any_permission\n"
        f"Update permission names to dot notation and see cursor rules for mapping."
    )


def require_all_permissions(*permission_names: str) -> Callable:
    """LEGACY FUNCTION - REMOVED TO FORCE MIGRATION"""
    raise NotImplementedError(
        f"Legacy permission system removed. Use new permission middleware instead.\n"
        f"Replace: from app.core.permissions import require_all_permissions\n"
        f"With: from app.core.permission_middleware import require_all_permissions\n"
        f"Update permission names to dot notation and see cursor rules for mapping."
    )


# Legacy compatibility for existing code
def require_admin_permission(permission: str) -> Callable:
    """LEGACY FUNCTION - REMOVED TO FORCE MIGRATION"""
    raise NotImplementedError(
        f"Legacy permission system removed. Use new permission middleware instead.\n"
        f"Replace: from app.core.permissions import require_admin_permission\n"
        f"With: from app.core.permission_middleware import require_permission\n"
        f"Update permission name '{permission}' to dot notation and see cursor rules for mapping."
    ) 