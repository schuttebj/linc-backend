"""
Standardized Permission Management
Provides consistent permission checking across all API endpoints
"""

from typing import Callable
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User


def require_permission(permission_name: str) -> Callable:
    """
    Standardized permission checker dependency
    
    Usage:
        @router.post("/")
        async def create_resource(
            data: ResourceCreate,
            current_user: User = Depends(require_permission("resource_create"))
        ):
            ...
    
    Args:
        permission_name: The exact permission name from database (e.g., "user_group_create")
        
    Returns:
        FastAPI dependency function that checks permission and returns current user
    """
    def check_permission(current_user: User = Depends(get_current_user)) -> User:
        # Superuser has all permissions
        if current_user.is_superuser:
            return current_user
            
        # Check specific permission
        if not current_user.has_permission(permission_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission_name}"
            )
        
        return current_user
    
    return check_permission


def require_any_permission(*permission_names: str) -> Callable:
    """
    Check if user has ANY of the specified permissions
    
    Usage:
        @router.get("/")
        async def read_resource(
            current_user: User = Depends(require_any_permission("resource_read", "admin_read"))
        ):
            ...
    """
    def check_permissions(current_user: User = Depends(get_current_user)) -> User:
        # Superuser has all permissions
        if current_user.is_superuser:
            return current_user
            
        # Check if user has any of the specified permissions
        for permission_name in permission_names:
            if current_user.has_permission(permission_name):
                return current_user
        
        permission_list = ", ".join(permission_names)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"At least one of these permissions required: {permission_list}"
        )
    
    return check_permissions


def require_all_permissions(*permission_names: str) -> Callable:
    """
    Check if user has ALL of the specified permissions
    
    Usage:
        @router.post("/admin/")
        async def admin_action(
            current_user: User = Depends(require_all_permissions("admin_read", "admin_write"))
        ):
            ...
    """
    def check_permissions(current_user: User = Depends(get_current_user)) -> User:
        # Superuser has all permissions
        if current_user.is_superuser:
            return current_user
            
        # Check if user has all specified permissions
        missing_permissions = []
        for permission_name in permission_names:
            if not current_user.has_permission(permission_name):
                missing_permissions.append(permission_name)
        
        if missing_permissions:
            permission_list = ", ".join(missing_permissions)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permissions: {permission_list}"
            )
        
        return current_user
    
    return check_permissions


# Legacy compatibility for existing code
def require_admin_permission(permission: str) -> Callable:
    """
    Legacy compatibility function for users module
    Maps to the new standardized require_permission function
    """
    return require_permission(permission) 