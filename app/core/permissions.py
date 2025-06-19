"""
LEGACY PERMISSION FILE - TEMPORARY FOR MIGRATION
This file provides temporary legacy permission functions while we migrate to the new system.
Use app.core.permission_middleware for new code.
"""

from typing import Callable
from functools import wraps
from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user
from app.models.user import User


def require_permission(permission_name: str) -> Callable:
    """LEGACY FUNCTION - TEMPORARY FOR MIGRATION"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            print(f"WARNING: Using legacy require_permission('{permission_name}'). Migrate to new permission middleware")
            return func(*args, **kwargs)
        
        # Add dependency for current user with permission check
        async def permission_dependency(current_user: User = Depends(get_current_user)):
            if not current_user.has_permission(permission_name):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission required: {permission_name}"
                )
            return current_user
        
        # Return the dependency function that can be used with Depends()
        return permission_dependency
    
    return decorator


def require_any_permission(*permission_names: str) -> Callable:
    """LEGACY FUNCTION - TEMPORARY FOR MIGRATION"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            print(f"WARNING: Using legacy require_any_permission{permission_names}. Migrate to new permission middleware")
            return func(*args, **kwargs)
        
        async def permission_dependency(current_user: User = Depends(get_current_user)):
            has_any = any(current_user.has_permission(perm) for perm in permission_names)
            if not has_any:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"One of these permissions required: {', '.join(permission_names)}"
                )
            return current_user
        
        return permission_dependency
    
    return decorator


def require_all_permissions(*permission_names: str) -> Callable:
    """LEGACY FUNCTION - TEMPORARY FOR MIGRATION"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            print(f"WARNING: Using legacy require_all_permissions{permission_names}. Migrate to new permission middleware")
            return func(*args, **kwargs)
        
        async def permission_dependency(current_user: User = Depends(get_current_user)):
            missing_perms = [perm for perm in permission_names if not current_user.has_permission(perm)]
            if missing_perms:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing permissions: {', '.join(missing_perms)}"
                )
            return current_user
        
        return permission_dependency
    
    return decorator


# Legacy compatibility for existing code
def require_admin_permission(permission: str) -> Callable:
    """LEGACY FUNCTION - TEMPORARY FOR MIGRATION"""
    print(f"WARNING: Using legacy require_admin_permission('{permission}'). Migrate to new permission middleware")
    return require_permission(permission) 