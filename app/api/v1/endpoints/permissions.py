"""
Permission Management API Endpoints
Provides comprehensive permission and role management capabilities
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import structlog

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.permission_middleware import require_permission, SystemTypeRequired
from app.core.permission_engine import SystemType
from app.services.permission_service import PermissionService
from app.models.user import User

logger = structlog.get_logger()
router = APIRouter()

# Pydantic Models for API
class PermissionUpdateRequest(BaseModel):
    """Request model for updating role permissions"""
    permissions: List[str] = Field(..., description="List of permission names")
    
    class Config:
        json_schema_extra = {
            "example": {
                "permissions": [
                    "license.application.create",
                    "license.application.read",
                    "person.create",
                    "person.read"
                ]
            }
        }

class PermissionImpactAnalysisRequest(BaseModel):
    """Request model for permission impact analysis"""
    role_type: str = Field(..., description="Role type: system, region, office")
    role_name: str = Field(..., description="Role name")
    new_permissions: List[str] = Field(..., description="Proposed new permissions")

class SystemTypeResponse(BaseModel):
    """Response model for system types"""
    type_code: str
    display_name: str
    description: str
    permissions: List[str]
    permission_count: int
    is_active: bool
    created_at: str
    updated_at: str
    updated_by: str

class RegionRoleResponse(BaseModel):
    """Response model for region roles"""
    role_name: str
    display_name: str
    description: str
    permissions: List[str]
    permission_count: int
    is_active: bool
    created_at: str
    updated_at: str
    updated_by: str

class OfficeRoleResponse(BaseModel):
    """Response model for office roles"""
    role_name: str
    display_name: str
    description: str
    permissions: List[str]
    permission_count: int
    is_active: bool
    created_at: str
    updated_at: str
    updated_by: str

# System Type Management Endpoints
@router.get("/system-types", response_model=List[SystemTypeResponse])
async def get_system_types(
    current_user: User = Depends(SystemTypeRequired(SystemType.SUPER_ADMIN, SystemType.NATIONAL_HELP_DESK)),
    db: Session = Depends(get_db)
):
    """
    Get all system types with their permissions
    
    Requires Super Admin or National Help Desk access
    """
    try:
        logger.info("Getting system types", requested_by=current_user.username)
        
        permission_service = PermissionService(db)
        system_types = await permission_service.get_system_types()
        
        return system_types
        
    except Exception as e:
        logger.error("Error getting system types", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system types"
        )

@router.put("/system-types/{type_code}/permissions")
async def update_system_type_permissions(
    type_code: str,
    request: PermissionUpdateRequest,
    current_user: User = Depends(SystemTypeRequired(SystemType.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Update permissions for a system type
    
    Requires Super Admin access
    """
    try:
        logger.info("Updating system type permissions", 
                   type_code=type_code,
                   permission_count=len(request.permissions),
                   updated_by=current_user.username)
        
        permission_service = PermissionService(db)
        success = await permission_service.update_system_type_permissions(
            type_code, request.permissions, current_user.username
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update system type permissions"
            )
        
        return {
            "message": "System type permissions updated successfully",
            "type_code": type_code,
            "permission_count": len(request.permissions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating system type permissions", 
                    type_code=type_code, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update system type permissions"
        )

# Region Role Management Endpoints
@router.get("/region-roles", response_model=List[RegionRoleResponse])
async def get_region_roles(
    current_user: User = Depends(require_permission("admin.permission.manage")),
    db: Session = Depends(get_db)
):
    """
    Get all region roles with their permissions
    
    Requires admin.permission.manage permission
    """
    try:
        logger.info("Getting region roles", requested_by=current_user.username)
        
        permission_service = PermissionService(db)
        region_roles = await permission_service.get_region_roles()
        
        return region_roles
        
    except Exception as e:
        logger.error("Error getting region roles", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve region roles"
        )

@router.put("/region-roles/{role_name}/permissions")
async def update_region_role_permissions(
    role_name: str,
    request: PermissionUpdateRequest,
    current_user: User = Depends(require_permission("admin.permission.manage")),
    db: Session = Depends(get_db)
):
    """
    Update permissions for a region role
    
    Requires admin.permission.manage permission
    """
    try:
        logger.info("Updating region role permissions", 
                   role_name=role_name,
                   permission_count=len(request.permissions),
                   updated_by=current_user.username)
        
        permission_service = PermissionService(db)
        success = await permission_service.update_region_role_permissions(
            role_name, request.permissions, current_user.username
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update region role permissions"
            )
        
        return {
            "message": "Region role permissions updated successfully",
            "role_name": role_name,
            "permission_count": len(request.permissions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating region role permissions", 
                    role_name=role_name, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update region role permissions"
        )

# Office Role Management Endpoints
@router.get("/office-roles", response_model=List[OfficeRoleResponse])
async def get_office_roles(
    current_user: User = Depends(require_permission("admin.permission.manage")),
    db: Session = Depends(get_db)
):
    """
    Get all office roles with their permissions
    
    Requires admin.permission.manage permission
    """
    try:
        logger.info("Getting office roles", requested_by=current_user.username)
        
        permission_service = PermissionService(db)
        office_roles = await permission_service.get_office_roles()
        
        return office_roles
        
    except Exception as e:
        logger.error("Error getting office roles", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve office roles"
        )

@router.put("/office-roles/{role_name}/permissions")
async def update_office_role_permissions(
    role_name: str,
    request: PermissionUpdateRequest,
    current_user: User = Depends(require_permission("admin.permission.manage")),
    db: Session = Depends(get_db)
):
    """
    Update permissions for an office role
    
    Requires admin.permission.manage permission
    """
    try:
        logger.info("Updating office role permissions", 
                   role_name=role_name,
                   permission_count=len(request.permissions),
                   updated_by=current_user.username)
        
        permission_service = PermissionService(db)
        success = await permission_service.update_office_role_permissions(
            role_name, request.permissions, current_user.username
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update office role permissions"
            )
        
        return {
            "message": "Office role permissions updated successfully",
            "role_name": role_name,
            "permission_count": len(request.permissions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating office role permissions", 
                    role_name=role_name, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update office role permissions"
        )

# Available Permissions Endpoint
@router.get("/available-permissions")
async def get_available_permissions(
    current_user: User = Depends(require_permission("admin.permission.manage")),
    db: Session = Depends(get_db)
):
    """
    Get all available permissions organized by category
    
    Requires admin.permission.manage permission
    """
    try:
        logger.info("Getting available permissions", requested_by=current_user.username)
        
        permission_service = PermissionService(db)
        permissions = await permission_service.get_available_permissions()
        
        return permissions
        
    except Exception as e:
        logger.error("Error getting available permissions", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available permissions"
        )

# Permission Impact Analysis
@router.post("/analyze-impact")
async def analyze_permission_impact(
    request: PermissionImpactAnalysisRequest,
    current_user: User = Depends(require_permission("admin.permission.manage")),
    db: Session = Depends(get_db)
):
    """
    Analyze the impact of changing role permissions
    
    Shows what users will be affected and what permissions will change
    Requires admin.permission.manage permission
    """
    try:
        logger.info("Analyzing permission impact", 
                   role_type=request.role_type,
                   role_name=request.role_name,
                   requested_by=current_user.username)
        
        permission_service = PermissionService(db)
        impact_analysis = await permission_service.analyze_permission_impact(
            request.role_type, request.role_name, request.new_permissions
        )
        
        return impact_analysis
        
    except Exception as e:
        logger.error("Error analyzing permission impact", 
                    role_type=request.role_type,
                    role_name=request.role_name,
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze permission impact"
        )

# User Permission Analysis
@router.get("/users/{user_id}/permissions")
async def get_user_permission_summary(
    user_id: str,
    current_user: User = Depends(require_permission("admin.user.read")),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive permission summary for a specific user
    
    Shows all permission sources and final compiled permissions
    Requires admin.user.read permission
    """
    try:
        logger.info("Getting user permission summary", 
                   target_user_id=user_id,
                   requested_by=current_user.username)
        
        permission_service = PermissionService(db)
        summary = await permission_service.get_user_permission_summary(user_id)
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting user permission summary", 
                    user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user permission summary"
        )

# Permission Audit History
@router.get("/audit-history")
async def get_permission_audit_history(
    role_type: Optional[str] = Query(None, description="Filter by role type"),
    role_name: Optional[str] = Query(None, description="Filter by role name"),
    limit: int = Query(50, ge=1, le=200, description="Number of records to return"),
    current_user: User = Depends(require_permission("admin.audit.read")),
    db: Session = Depends(get_db)
):
    """
    Get permission change audit history
    
    Shows history of permission changes with details
    Requires admin.audit.read permission
    """
    try:
        logger.info("Getting permission audit history", 
                   role_type=role_type,
                   role_name=role_name,
                   limit=limit,
                   requested_by=current_user.username)
        
        permission_service = PermissionService(db)
        audit_history = await permission_service.get_permission_audit_history(
            role_type, role_name, limit
        )
        
        return {
            "audit_history": audit_history,
            "total_records": len(audit_history),
            "filters": {
                "role_type": role_type,
                "role_name": role_name,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error("Error getting permission audit history", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve permission audit history"
        )

# Permission Cache Management
@router.post("/cache/invalidate/user/{user_id}")
async def invalidate_user_permission_cache(
    user_id: str,
    current_user: User = Depends(require_permission("admin.system.config")),
    db: Session = Depends(get_db)
):
    """
    Invalidate permission cache for a specific user
    
    Forces recompilation of user permissions on next access
    Requires admin.system.config permission
    """
    try:
        logger.info("Invalidating user permission cache", 
                   target_user_id=user_id,
                   requested_by=current_user.username)
        
        from app.core.permission_engine import get_permission_engine
        engine = get_permission_engine(db)
        success = await engine.invalidate_user_permissions(user_id)
        
        if success:
            return {
                "message": "User permission cache invalidated successfully",
                "user_id": user_id
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to invalidate user permission cache"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error invalidating user permission cache", 
                    user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to invalidate user permission cache"
        )

@router.post("/cache/invalidate/role")
async def invalidate_role_permission_cache(
    role_type: str = Query(..., description="Role type: system, region, office"),
    role_name: str = Query(..., description="Role name"),
    current_user: User = Depends(require_permission("admin.system.config")),
    db: Session = Depends(get_db)
):
    """
    Invalidate permission cache for all users with a specific role
    
    Forces recompilation of permissions for all affected users
    Requires admin.system.config permission
    """
    try:
        logger.info("Invalidating role permission cache", 
                   role_type=role_type,
                   role_name=role_name,
                   requested_by=current_user.username)
        
        from app.core.permission_engine import get_permission_engine
        engine = get_permission_engine(db)
        success = await engine.invalidate_role_permissions(role_type, role_name)
        
        if success:
            return {
                "message": "Role permission cache invalidated successfully",
                "role_type": role_type,
                "role_name": role_name
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to invalidate role permission cache"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error invalidating role permission cache", 
                    role_type=role_type,
                    role_name=role_name,
                    error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to invalidate role permission cache"
        )