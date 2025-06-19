"""
User Group Management API Endpoints
RESTful API for managing user groups and authorities
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.permission_middleware import require_permission
from app.crud.user_group import user_group, user_group_create, user_group_update, user_group_delete
from app.schemas.location import (
    UserGroupCreate, 
    UserGroupUpdate, 
    UserGroupResponse, 
    UserGroupListFilter,
    UserGroupStatistics
)
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=UserGroupResponse, status_code=status.HTTP_201_CREATED)
def create_user_group(
    *,
    db: Session = Depends(get_db),
    user_group_in: UserGroupCreate,
    current_user: User = Depends(require_permission("user_group.create"))
):
    """
    Create new user group.
    
    Requires user_group_create permission.
    """
    
    # Check if user group code already exists
    if user_group.check_code_exists(db, user_group_in.user_group_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User group code already exists"
        )
    
    # Create user group
    db_user_group = user_group_create(
        db=db, 
        obj_in=user_group_in, 
        created_by=current_user.username
    )
    
    return db_user_group

@router.get("/", response_model=List[UserGroupResponse])
def read_user_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user_group.read")),
    skip: int = 0,
    limit: int = 100,
    province_code: Optional[str] = Query(None, description="Filter by province code"),
    user_group_type: Optional[str] = Query(None, description="Filter by user group type"),
    registration_status: Optional[str] = Query(None, description="Filter by registration status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search user groups")
):
    """
    Retrieve user groups with optional filtering.
    
    Requires user_group_read permission.
    """
    
    # Create filter object
    filters = UserGroupListFilter(
        province_code=province_code,
        user_group_type=user_group_type,
        registration_status=registration_status,
        is_active=is_active,
        search=search
    )
    
    # Apply province filtering based on user permissions
    if not current_user.can_access_province("all"):
        if current_user.province:
            filters.province_code = current_user.province
    
    user_groups = user_group.get_multi(
        db=db, 
        skip=skip, 
        limit=limit, 
        filters=filters
    )
    
    return user_groups

@router.get("/statistics", response_model=UserGroupStatistics)
def get_user_group_statistics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get user group statistics.
    """
    if not current_user.has_permission("user_group.read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to read user group statistics"
        )
    
    stats = user_group.get_statistics(db=db)
    return stats

@router.get("/{user_group_id}", response_model=UserGroupResponse)
def read_user_group(
    *,
    db: Session = Depends(get_db),
    user_group_id: UUID,
    current_user: User = Depends(require_permission("user_group.read"))
):
    """
    Get user group by ID.
    
    Requires user_group_read permission.
    """
    
    db_user_group = user_group.get(db=db, id=user_group_id)
    if not db_user_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User group not found"
        )
    
    # Check if user can access this user group
    if not current_user.can_access_province(db_user_group.province_code):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this user group"
        )
    
    return db_user_group

@router.put("/{user_group_id}", response_model=UserGroupResponse)
def update_user_group(
    *,
    db: Session = Depends(get_db),
    user_group_id: UUID,
    user_group_in: UserGroupUpdate,
    current_user: User = Depends(require_permission("user_group.update"))
):
    """
    Update user group.
    
    Requires user_group_update permission.
    """
    
    db_user_group = user_group.get(db=db, id=user_group_id)
    if not db_user_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User group not found"
        )
    
    # Check if user can manage this user group
    if not current_user.can_manage_user_group(db_user_group.user_group_code):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this user group"
        )
    
    updated_user_group = user_group_update(
        db=db, 
        db_obj=db_user_group, 
        obj_in=user_group_in,
        updated_by=current_user.username
    )
    
    return updated_user_group

@router.delete("/{user_group_id}", response_model=UserGroupResponse)
def delete_user_group(
    *,
    db: Session = Depends(get_db),
    user_group_id: UUID,
    current_user: User = Depends(require_permission("user_group.delete"))
):
    """
    Delete user group (soft delete).
    
    Requires user_group_delete permission.
    """
    
    db_user_group = user_group.get(db=db, id=user_group_id)
    if not db_user_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User group not found"
        )
    
    # Check if user can manage this user group
    if not current_user.can_manage_user_group(db_user_group.user_group_code):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this user group"
        )
    
    deleted_user_group = user_group_delete(db=db, id=user_group_id)
    return deleted_user_group

@router.get("/by-province/{province_code}", response_model=List[UserGroupResponse])
def get_user_groups_by_province(
    *,
    db: Session = Depends(get_db),
    province_code: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get all user groups in a specific province.
    """
    if not current_user.has_permission("user_group.read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to read user groups"
        )
    
    # Check if user can access this province
    if not current_user.can_access_province(province_code):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this province"
        )
    
    user_groups = user_group.get_by_province(db=db, province_code=province_code)
    return user_groups

@router.get("/type/dltc", response_model=List[UserGroupResponse])
def get_dltc_user_groups(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all DLTC user groups.
    """
    if not current_user.has_permission("user_group.read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to read user groups"
        )
    
    user_groups = user_group.get_dltc_groups(db=db)
    
    # Filter by user's province access if needed
    if not current_user.can_access_province("all"):
        user_groups = [
            ug for ug in user_groups 
            if current_user.can_access_province(ug.province_code)
        ]
    
    return user_groups

@router.get("/type/help-desk", response_model=List[UserGroupResponse])
def get_help_desk_user_groups(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all help desk user groups.
    """
    if not current_user.has_permission("user_group.read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to read user groups"
        )
    
    user_groups = user_group.get_help_desk_groups(db=db)
    
    # Filter by user's province access if needed
    if not current_user.can_access_province("all"):
        user_groups = [
            ug for ug in user_groups 
            if current_user.can_access_province(ug.province_code)
        ]
    
    return user_groups

@router.get("/validate-code/{user_group_code}", response_model=dict)
def validate_user_group_code(
    *,
    db: Session = Depends(get_db),
    user_group_code: str,
    current_user: User = Depends(get_current_user)
):
    """
    Check if user group code is available.
    """
    if not current_user.has_permission("user_group.create"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to validate user group codes"
        )
    
    exists = user_group.check_code_exists(db=db, user_group_code=user_group_code)
    
    return {
        "user_group_code": user_group_code,
        "exists": exists,
        "available": not exists
    } 
