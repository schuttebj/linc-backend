"""
User Management API Endpoints
Administrative endpoints for managing users, roles, and permissions
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import structlog

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.permissions import require_permission, require_admin_permission
from app.services.user_service import UserService
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserListResponse, UserListFilter,
    RoleCreate, RoleUpdate, RoleResponse,
    PermissionCreate, PermissionUpdate, PermissionResponse,
    UserAuditLogResponse
)
from app.models.user import User

logger = structlog.get_logger()
router = APIRouter()

# Note: require_admin_permission is now imported from app.core.permissions

# User Management Endpoints
@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_permission("admin.user.create"))
):
    """
    Create new user account
    
    Requires admin.user.create permission
    """
    try:
        logger.info("Creating new user", 
                   username=user_data.username, 
                   created_by=current_user.username)
        
        user_service = UserService(db)
        user = await user_service.create_user(user_data, created_by=current_user.username)
        
        return UserResponse.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating user", 
                    username=user_data.username, 
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

@router.get("/", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by user status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    role: Optional[str] = Query(None, description="Filter by role name"),
    department: Optional[str] = Query(None, description="Filter by department"),
    country_code: Optional[str] = Query(None, description="Filter by country"),
    search: Optional[str] = Query(None, description="Search users"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_permission("admin.user.read"))
):
    """
    List users with filtering and pagination
    
    Requires admin.user.read permission
    """
    try:
        logger.info("Listing users", requested_by=current_user.username)
        
        user_service = UserService(db)
        
        # Build filters
        filters = UserListFilter(
            status=status_filter,
            is_active=is_active,
            role=role,
            department=department,
            country_code=country_code,
            search=search
        )
        
        users, total = await user_service.list_users(filters, page, size)
        
        return UserListResponse(
            users=[UserResponse.from_orm(user) for user in users],
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error listing users", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_permission("admin.user.read"))
):
    """
    Get user by ID
    
    Requires admin.user.read permission
    """
    try:
        logger.info("Getting user", user_id=user_id, requested_by=current_user.username)
        
        user_service = UserService(db)
        user = await user_service.get_user_by_id(user_id)
        
        return UserResponse.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting user", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_permission("admin.user.update"))
):
    """
    Update user account
    
    Requires admin.user.update permission
    """
    try:
        logger.info("Updating user", 
                   user_id=user_id, 
                   updated_by=current_user.username)
        
        user_service = UserService(db)
        user = await user_service.update_user(
            user_id, user_data, updated_by=current_user.username
        )
        
        return UserResponse.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating user", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )

@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_permission("admin.user.delete"))
):
    """
    Delete user account (soft delete - deactivate)
    
    Requires admin.user.delete permission
    """
    try:
        logger.info("Deleting user", 
                   user_id=user_id, 
                   deleted_by=current_user.username)
        
        # Prevent self-deletion
        if str(current_user.id) == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        user_service = UserService(db)
        
        # Soft delete by deactivating the user
        user_data = UserUpdate(is_active=False, status="inactive")
        await user_service.update_user(
            user_id, user_data, updated_by=current_user.username
        )
        
        return {"message": "User deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting user", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )

# Role Management Endpoints
@router.post("/roles/", response_model=RoleResponse)
async def create_role(
    role_data: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_permission("admin.role.manage"))
):
    """
    Create new role
    
    Requires admin.role.manage permission
    """
    try:
        logger.info("Creating new role", 
                   role_name=role_data.name, 
                   created_by=current_user.username)
        
        user_service = UserService(db)
        role = await user_service.create_role(role_data, created_by=current_user.username)
        
        return RoleResponse.from_orm(role)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating role", role_name=role_data.name, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create role"
        )

@router.get("/roles/", response_model=List[RoleResponse])
async def list_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_permission("admin.role.manage"))
):
    """
    List all roles
    
    Requires admin.role.manage permission
    """
    try:
        logger.info("Listing roles", requested_by=current_user.username)
        
        user_service = UserService(db)
        roles = await user_service.get_roles()
        
        return [RoleResponse.from_orm(role) for role in roles]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error listing roles", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve roles"
        )

# Permission Management Endpoints
@router.post("/permissions/", response_model=PermissionResponse)
async def create_permission(
    permission_data: PermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_permission("admin.role.manage"))
):
    """
    Create new permission
    
    Requires admin.role.manage permission
    """
    try:
        logger.info("Creating new permission", 
                   permission_name=permission_data.name, 
                   created_by=current_user.username)
        
        user_service = UserService(db)
        permission = await user_service.create_permission(
            permission_data, created_by=current_user.username
        )
        
        return PermissionResponse.from_orm(permission)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating permission", 
                    permission_name=permission_data.name, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create permission"
        )

@router.get("/permissions/", response_model=List[PermissionResponse])
async def list_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_permission("admin.role.manage"))
):
    """
    List all permissions
    
    Requires admin.role.manage permission
    """
    try:
        logger.info("Listing permissions", requested_by=current_user.username)
        
        user_service = UserService(db)
        permissions = await user_service.get_permissions()
        
        return [PermissionResponse.from_orm(permission) for permission in permissions]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error listing permissions", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve permissions"
        )

# User Activity and Audit Endpoints
@router.get("/{user_id}/audit-logs", response_model=List[UserAuditLogResponse])
async def get_user_audit_logs(
    user_id: str,
    limit: int = Query(50, ge=1, le=500, description="Number of logs to retrieve"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_permission("admin.audit.read"))
):
    """
    Get user audit logs
    
    Requires admin.audit.read permission
    """
    try:
        logger.info("Getting user audit logs", 
                   user_id=user_id, 
                   requested_by=current_user.username)
        
        from app.models.user import UserAuditLog
        
        audit_logs = db.query(UserAuditLog).filter(
            UserAuditLog.user_id == user_id
        ).order_by(UserAuditLog.created_at.desc()).limit(limit).all()
        
        return [UserAuditLogResponse.from_orm(log) for log in audit_logs]
        
    except Exception as e:
        logger.error("Error getting user audit logs", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit logs"
        )

@router.post("/{user_id}/reset-password")
async def admin_reset_password(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_permission("admin.user.update"))
):
    """
    Admin reset user password
    
    Generates a temporary password and forces password change on next login
    Requires admin.user.update permission
    """
    try:
        logger.info("Admin password reset", 
                   user_id=user_id, 
                   reset_by=current_user.username)
        
        import secrets
        import string
        
        # Generate temporary password
        temp_password = ''.join(secrets.choice(
            string.ascii_letters + string.digits + "!@#$%"
        ) for _ in range(12))
        
        user_service = UserService(db)
        
        # Get user first
        user = await user_service.get_user_by_id(user_id)
        
        # Update password and force change
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        user.password_hash = pwd_context.hash(temp_password)
        user.require_password_change = True
        user.updated_by = current_user.username
        
        db.commit()
        
        await user_service._log_audit(
            str(user.id), "password_reset_admin", "security",
            success=True, details=f"Password reset by admin: {current_user.username}"
        )
        
        return {
            "message": "Password reset successfully",
            "temporary_password": temp_password,
            "expires": "User must change password on next login"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error resetting user password", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )

@router.post("/{user_id}/unlock")
async def unlock_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_permission("admin.user.update"))
):
    """
    Unlock user account
    
    Clears failed login attempts and unlocks account
    Requires admin.user.update permission
    """
    try:
        logger.info("Unlocking user account", 
                   user_id=user_id, 
                   unlocked_by=current_user.username)
        
        user_service = UserService(db)
        user = await user_service.get_user_by_id(user_id)
        
        # Clear lock status
        user.failed_login_attempts = 0
        user.locked_until = None
        if user.status == "locked":
            user.status = "active"
        user.updated_by = current_user.username
        
        db.commit()
        
        await user_service._log_audit(
            str(user.id), "account_unlocked", "security",
            success=True, details=f"Account unlocked by admin: {current_user.username}"
        )
        
        return {"message": "User account unlocked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error unlocking user", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unlock user account"
        ) 