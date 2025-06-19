"""
Region Management API Endpoints
RESTful API for managing regions and authorities
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.permission_middleware import require_permission
from app.crud.region import region, region_create, region_update, region_delete
from app.schemas.location import (
    RegionCreate, 
    RegionUpdate, 
    RegionResponse, 
    RegionListFilter,
    RegionStatistics
)
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=RegionResponse, status_code=status.HTTP_201_CREATED)
def create_region(
    *,
    db: Session = Depends(get_db),
    region_in: RegionCreate,
    current_user: User = Depends(require_permission("region.create"))
):
    """
    Create new region.
    
    Requires region.create permission.
    """
    
    # Check if region code already exists
    if region.check_code_exists(db, region_in.user_group_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Region code already exists"
        )
    
    # Create region
    db_region = region_create(
        db=db, 
        obj_in=region_in, 
        created_by=current_user.username
    )
    
    return db_region

@router.get("/", response_model=List[RegionResponse])
def read_regions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("region.read")),
    skip: int = 0,
    limit: int = 100,
    province_code: Optional[str] = Query(None, description="Filter by province code"),
    region_type: Optional[str] = Query(None, description="Filter by region type"),
    registration_status: Optional[str] = Query(None, description="Filter by registration status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search regions")
):
    """
    Retrieve regions with optional filtering.
    
    Requires region.read permission.
    """
    
    # Create filter object
    filters = RegionListFilter(
        province_code=province_code,
        region_type=region_type,
        registration_status=registration_status,
        is_active=is_active,
        search=search
    )
    
    # Apply province filtering based on user permissions
    if not current_user.can_access_province("all"):
        if current_user.province:
            filters.province_code = current_user.province
    
    regions = region.get_multi(
        db=db, 
        skip=skip, 
        limit=limit, 
        filters=filters
    )
    
    return regions

@router.get("/statistics", response_model=RegionStatistics)
def get_region_statistics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("region.read"))
):
    """
    Get region statistics.
    
    Requires region.read permission.
    """
    
    stats = region.get_statistics(db=db)
    return stats

@router.get("/{region_id}", response_model=RegionResponse)
def read_region(
    *,
    db: Session = Depends(get_db),
    region_id: UUID,
    current_user: User = Depends(require_permission("region.read"))
):
    """
    Get region by ID.
    
    Requires region.read permission.
    """
    
    db_region = region.get(db=db, id=region_id)
    if not db_region:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Region not found"
        )
    
    # Check if user can access this region
    if not current_user.can_access_province(db_region.province_code):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this region"
        )
    
    return db_region

@router.put("/{region_id}", response_model=RegionResponse)
def update_region(
    *,
    db: Session = Depends(get_db),
    region_id: UUID,
    region_in: RegionUpdate,
    current_user: User = Depends(require_permission("region.update"))
):
    """
    Update region.
    
    Requires region.update permission.
    """
    
    db_region = region.get(db=db, id=region_id)
    if not db_region:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Region not found"
        )
    
    # Check if user can manage this region
    if not current_user.can_manage_region(db_region.user_group_code):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this region"
        )
    
    updated_region = region_update(
        db=db, 
        db_obj=db_region, 
        obj_in=region_in,
        updated_by=current_user.username
    )
    
    return updated_region

@router.delete("/{region_id}", response_model=RegionResponse)
def delete_region(
    *,
    db: Session = Depends(get_db),
    region_id: UUID,
    current_user: User = Depends(require_permission("region.delete"))
):
    """
    Delete region (soft delete).
    
    Requires region.delete permission.
    """
    
    db_region = region.get(db=db, id=region_id)
    if not db_region:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Region not found"
        )
    
    # Check if user can manage this region
    if not current_user.can_manage_region(db_region.user_group_code):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this region"
        )
    
    deleted_region = region_delete(db=db, id=region_id)
    return deleted_region

@router.get("/by-province/{province_code}", response_model=List[RegionResponse])
def get_regions_by_province(
    *,
    db: Session = Depends(get_db),
    province_code: str,
    current_user: User = Depends(require_permission("region.read"))
):
    """
    Get all regions in a province.
    
    Requires region.read permission.
    """
    
    # Check if user can access this province
    if not current_user.can_access_province(province_code):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this province"
        )
    
    regions = region.get_by_province(db=db, province_code=province_code)
    return regions

@router.get("/type/dltc", response_model=List[RegionResponse])
def get_dltc_regions(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("region.read"))
):
    """
    Get all DLTC regions.
    
    Requires region.read permission.
    """
    
    dltc_regions = region.get_dltc_regions(db=db)
    
    # Filter by user's accessible provinces if not super admin
    if not current_user.can_access_province("all"):
        dltc_regions = [
            r for r in dltc_regions 
            if current_user.can_access_province(r.province_code)
        ]
    
    return dltc_regions

@router.get("/type/help-desk", response_model=List[RegionResponse])
def get_help_desk_regions(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("region.read"))
):
    """
    Get all help desk regions.
    
    Requires region.read permission.
    """
    
    help_desk_regions = region.get_help_desk_regions(db=db)
    
    # Filter by user's accessible provinces if not super admin
    if not current_user.can_access_province("all"):
        help_desk_regions = [
            r for r in help_desk_regions 
            if current_user.can_access_province(r.province_code)
        ]
    
    return help_desk_regions

@router.get("/validate-code/{region_code}", response_model=dict)
def validate_region_code(
    *,
    db: Session = Depends(get_db),
    region_code: str,
    current_user: User = Depends(require_permission("region.create"))
):
    """
    Validate if region code is available.
    
    Requires region.create permission.
    """
    
    exists = region.check_code_exists(db=db, region_code=region_code)
    
    return {
        "region_code": region_code,
        "is_available": not exists,
        "message": "Region code is available" if not exists else "Region code already exists"
    } 
