"""
Location Management API Endpoints
RESTful API for managing physical locations, offices, and resources
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.crud.location import location
from app.schemas.location import (
    LocationCreate, 
    LocationUpdate, 
    LocationResponse, 
    LocationListFilter,
    LocationStatistics
)
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
def create_location(
    *,
    db: Session = Depends(get_db),
    location_in: LocationCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create new location.
    
    Requires appropriate permissions for location management.
    """
    # Check if user can create locations
    if not current_user.has_permission("location.create"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to create locations"
        )
    
    # Check if location code already exists
    if location.check_code_exists(db, location_in.location_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Location code already exists"
        )
    
    # Create location
    db_location = location.create(
        db=db, 
        obj_in=location_in, 
        created_by=current_user.username
    )
    
    return db_location

@router.get("/", response_model=List[LocationResponse])
def read_locations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """
    Retrieve locations with optional filtering.
    
    Users can only see locations they have permission to access.
    """
    if not current_user.has_permission("location.read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to read locations"
        )
    
    locations = location.get_multi(db=db, skip=skip, limit=limit)
    return locations

@router.get("/{location_id}", response_model=LocationResponse)
def read_location(
    *,
    db: Session = Depends(get_db),
    location_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """
    Get location by ID.
    """
    if not current_user.has_permission("location.read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to read locations"
        )
    
    db_location = location.get(db=db, id=location_id)
    if not db_location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    
    # Check if user can access this location
    if not current_user.can_access_location(str(location_id)):
        if not current_user.can_access_province(db_location.province_code):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to access this location"
            )
    
    return db_location

@router.put("/{location_id}", response_model=LocationResponse)
def update_location(
    *,
    db: Session = Depends(get_db),
    location_id: UUID,
    location_in: LocationUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Update location.
    """
    if not current_user.has_permission("location.update"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update locations"
        )
    
    db_location = location.get(db=db, id=location_id)
    if not db_location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    
    # Check if user can access this location
    if not current_user.can_access_location(str(location_id)):
        if not current_user.can_access_province(db_location.province_code):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to update this location"
            )
    
    updated_location = location.update(
        db=db, 
        db_obj=db_location, 
        obj_in=location_in,
        updated_by=current_user.username
    )
    
    return updated_location

@router.delete("/{location_id}", response_model=LocationResponse)
def delete_location(
    *,
    db: Session = Depends(get_db),
    location_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """
    Delete location (soft delete).
    """
    if not current_user.has_permission("location.delete"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete locations"
        )
    
    db_location = location.get(db=db, id=location_id)
    if not db_location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    
    # Check if user can access this location
    if not current_user.can_access_location(str(location_id)):
        if not current_user.can_access_province(db_location.province_code):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to delete this location"
            )
    
    deleted_location = location.delete(db=db, id=location_id)
    return deleted_location

@router.get("/by-province/{province_code}", response_model=List[LocationResponse])
def get_locations_by_province(
    *,
    db: Session = Depends(get_db),
    province_code: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get all locations in a specific province.
    """
    if not current_user.has_permission("location.read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to read locations"
        )
    
    # Check if user can access this province
    if not current_user.can_access_province(province_code):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this province"
        )
    
    locations = location.get_by_province(db=db, province_code=province_code)
    return locations

@router.get("/type/dltc", response_model=List[LocationResponse])
def get_dltc_locations(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all DLTC locations.
    """
    if not current_user.has_permission("location.read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to read locations"
        )
    
    locations = location.get_dltc_locations(db=db)
    
    # Filter by user's province access if needed
    if not current_user.can_access_province("all"):
        locations = [
            loc for loc in locations 
            if current_user.can_access_province(loc.province_code)
        ]
    
    return locations

@router.get("/type/printing", response_model=List[LocationResponse])
def get_printing_locations(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all printing locations.
    """
    if not current_user.has_permission("location.read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to read locations"
        )
    
    locations = location.get_printing_locations(db=db)
    
    # Filter by user's province access if needed
    if not current_user.can_access_province("all"):
        locations = [
            loc for loc in locations 
            if current_user.can_access_province(loc.province_code)
        ]
    
    return locations

@router.get("/operational", response_model=List[LocationResponse])
def get_operational_locations(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all operationally active locations.
    """
    if not current_user.has_permission("location.read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to read locations"
        )
    
    locations = location.get_operational_locations(db=db)
    
    # Filter by user's province access if needed
    if not current_user.can_access_province("all"):
        locations = [
            loc for loc in locations 
            if current_user.can_access_province(loc.province_code)
        ]
    
    return locations

@router.get("/public", response_model=List[LocationResponse])
def get_public_locations(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all public-facing locations.
    """
    if not current_user.has_permission("location.read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to read locations"
        )
    
    locations = location.get_public_locations(db=db)
    
    # Filter by user's province access if needed
    if not current_user.can_access_province("all"):
        locations = [
            loc for loc in locations 
            if current_user.can_access_province(loc.province_code)
        ]
    
    return locations

@router.get("/with-capacity", response_model=List[LocationResponse])
def get_locations_with_capacity(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    min_capacity: int = Query(1, description="Minimum available capacity")
):
    """
    Get locations with available capacity.
    """
    if not current_user.has_permission("location.read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to read locations"
        )
    
    locations = location.get_locations_with_capacity(db=db, min_capacity=min_capacity)
    
    # Filter by user's province access if needed
    if not current_user.can_access_province("all"):
        locations = [
            loc for loc in locations 
            if current_user.can_access_province(loc.province_code)
        ]
    
    return locations

@router.put("/{location_id}/load", response_model=LocationResponse)
def update_location_load(
    *,
    db: Session = Depends(get_db),
    location_id: UUID,
    new_load: int = Query(..., description="New load value"),
    current_user: User = Depends(get_current_user)
):
    """
    Update location's current load.
    """
    if not current_user.has_permission("location.update"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update location load"
        )
    
    db_location = location.get(db=db, id=location_id)
    if not db_location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    
    # Check if user can access this location
    if not current_user.can_access_location(str(location_id)):
        if not current_user.can_access_province(db_location.province_code):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to update this location"
            )
    
    updated_location = location.update_load(db=db, location_id=location_id, new_load=new_load)
    return updated_location

@router.get("/statistics", response_model=LocationStatistics)
def get_location_statistics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get location statistics.
    """
    if not current_user.has_permission("location.read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to read location statistics"
        )
    
    stats = location.get_statistics(db=db)
    return stats

@router.get("/validate-code/{location_code}", response_model=dict)
def validate_location_code(
    *,
    db: Session = Depends(get_db),
    location_code: str,
    current_user: User = Depends(get_current_user)
):
    """
    Check if location code is available.
    """
    if not current_user.has_permission("location.create"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to validate location codes"
        )
    
    exists = location.check_code_exists(db=db, location_code=location_code)
    
    return {
        "location_code": location_code,
        "exists": exists,
        "available": not exists
    } 