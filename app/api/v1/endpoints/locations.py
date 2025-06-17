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
from app.core.permissions import require_permission, require_any_permission
from app.crud.location import location, location_create, location_update, location_delete
from app.schemas.location import (
    LocationCreate,
    LocationCreateNested, 
    LocationUpdate, 
    LocationResponse, 
    LocationListFilter,
    LocationStatistics,
    UserLocationAssignmentCreate,
    UserLocationAssignmentUpdate,
    UserLocationAssignmentResponse
)
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
def create_location(
    *,
    db: Session = Depends(get_db),
    location_in: LocationCreateNested,
    current_user: User = Depends(require_permission("location_create"))
):
    """
    Create new location with nested address support.
    
    Requires location_create permission.
    """
    
    # Check if location code already exists
    if location.check_code_exists(db, location_in.location_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Location code already exists"
        )
    
    # Convert nested address structure to flat structure for database storage
    flat_location_data = location_in.to_flat_location_create()
    
    # Create LocationCreate object with flat structure and add required fields
    location_create_data = LocationCreate(
        user_group_id=location_in.user_group_id,
        office_id=location_in.office_id,
        **flat_location_data.dict()
    )
    
    # Create location
    db_location = location_create(
        db=db, 
        obj_in=location_create_data, 
        created_by=current_user.username
    )
    
    return db_location

@router.get("/", response_model=List[LocationResponse])
def read_locations(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("location_read")),
    skip: int = 0,
    limit: int = 100
):
    """
    Retrieve locations with optional filtering.
    
    Requires location_read permission.
    """
    
    locations = location.get_multi(db=db, skip=skip, limit=limit)
    return locations

@router.get("/statistics", response_model=LocationStatistics)
def get_location_statistics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("location_read"))
):
    """
    Get location statistics.
    
    Requires location_read permission.
    """
    
    stats = location.get_statistics(db=db)
    return stats

@router.get("/{location_id}", response_model=LocationResponse)
def read_location(
    *,
    db: Session = Depends(get_db),
    location_id: UUID,
    current_user: User = Depends(require_permission("location_read"))
):
    """
    Get location by ID.
    
    Requires location_read permission.
    """
    
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
    current_user: User = Depends(require_permission("location_update"))
):
    """
    Update location.
    
    Requires location_update permission.
    """
    
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
    
    updated_location = location_update(
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
    current_user: User = Depends(require_permission("location_delete"))
):
    """
    Delete location (soft delete).
    
    Requires location_delete permission.
    """
    
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
    
    deleted_location = location_delete(db=db, id=location_id)
    return deleted_location

@router.get("/by-province/{province_code}", response_model=List[LocationResponse])
def get_locations_by_province(
    *,
    db: Session = Depends(get_db),
    province_code: str,
    current_user: User = Depends(require_permission("location_read"))
):
    """
    Get all locations in a specific province.
    
    Requires location_read permission.
    """
    
    # Check if user can access this province
    if not current_user.can_access_province(province_code):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access locations in this province"
        )
    
    locations = location.get_by_province(db=db, province_code=province_code)
    return locations

@router.get("/type/dltc", response_model=List[LocationResponse])
def get_dltc_locations(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("location_read"))
):
    """
    Get all DLTC locations.
    
    Requires location_read permission.
    """
    
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
    current_user: User = Depends(require_permission("location_read"))
):
    """
    Get all printing locations.
    
    Requires location_read permission.
    """
    
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
    current_user: User = Depends(require_permission("location_read"))
):
    """
    Get all operationally active locations.
    
    Requires location_read permission.
    """
    
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
    current_user: User = Depends(require_permission("location_read"))
):
    """
    Get all public-facing locations.
    
    Requires location_read permission.
    """
    
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
    current_user: User = Depends(require_permission("location_read")),
    min_capacity: int = Query(1, description="Minimum available capacity")
):
    """
    Get locations with available capacity.
    
    Requires location_read permission.
    """
    
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
    current_user: User = Depends(require_permission("location_update"))
):
    """
    Update location's current load.
    
    Requires location_update permission.
    """
    
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
    
    updated_location = location_update_load(db=db, location_id=location_id, new_load=new_load)
    return updated_location

@router.get("/validate-code/{location_code}", response_model=dict)
def validate_location_code(
    *,
    db: Session = Depends(get_db),
    location_code: str,
    current_user: User = Depends(require_permission("location_create"))
):
    """
    Check if location code is available.
    
    Requires location_create permission.
    """
    
    exists = location.check_code_exists(db=db, location_code=location_code)
    
    return {
        "location_code": location_code,
        "exists": exists,
        "available": not exists
    }

# Staff Assignment Endpoints (as per development standards)
@router.post("/{location_id}/staff", response_model=UserLocationAssignmentResponse, status_code=status.HTTP_201_CREATED)
def assign_staff_to_location(
    *,
    db: Session = Depends(get_db),
    location_id: UUID,
    assignment_in: UserLocationAssignmentCreate,
    current_user: User = Depends(require_any_permission("location_create", "user_group_update"))
):
    """
    Assign staff to location.
    
    Requires location_create or user_group_update permission.
    """
    
    # Verify location exists
    db_location = location.get(db=db, id=location_id)
    if not db_location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    
    # Set location_id from URL parameter
    assignment_in.location_id = str(location_id)
    
    # Create staff assignment
    from app.crud.user_location_assignment import user_location_assignment_create
    db_assignment = user_location_assignment_create(
        db=db, 
        obj_in=assignment_in,
        created_by=current_user.username
    )
    
    return db_assignment

@router.get("/{location_id}/staff", response_model=List[UserLocationAssignmentResponse])
def get_location_staff(
    *,
    db: Session = Depends(get_db),
    location_id: UUID,
    current_user: User = Depends(require_permission("location_read"))
):
    """
    Get staff assignments for location.
    
    Requires location_read permission.
    """
    
    # Verify location exists
    db_location = location.get(db=db, id=location_id)
    if not db_location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    
    # Get staff assignments
    from app.crud.user_location_assignment import user_location_assignment
    assignments = user_location_assignment.get_by_location(db=db, location_id=location_id)
    
    return assignments

@router.put("/{location_id}/staff/{assignment_id}", response_model=UserLocationAssignmentResponse)
def update_staff_assignment(
    *,
    db: Session = Depends(get_db),
    location_id: UUID,
    assignment_id: UUID,
    assignment_in: UserLocationAssignmentUpdate,
    current_user: User = Depends(require_any_permission("location_update", "user_group_update"))
):
    """
    Update staff assignment.
    
    Requires location_update or user_group_update permission.
    """
    
    # Get assignment
    from app.crud.user_location_assignment import user_location_assignment, user_location_assignment_update
    db_assignment = user_location_assignment.get(db=db, id=assignment_id)
    if not db_assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff assignment not found"
        )
    
    # Verify assignment belongs to this location
    if str(db_assignment.location_id) != str(location_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignment does not belong to this location"
        )
    
    # Update assignment
    updated_assignment = user_location_assignment_update(
        db=db,
        db_obj=db_assignment,
        obj_in=assignment_in,
        updated_by=current_user.username
    )
    
    return updated_assignment

@router.delete("/{location_id}/staff/{assignment_id}", response_model=UserLocationAssignmentResponse)
def remove_staff_assignment(
    *,
    db: Session = Depends(get_db),
    location_id: UUID,
    assignment_id: UUID,
    current_user: User = Depends(require_any_permission("location_delete", "user_group_update"))
):
    """
    Remove staff assignment from location.
    
    Requires location_delete or user_group_update permission.
    """
    
    # Get assignment
    from app.crud.user_location_assignment import user_location_assignment, user_location_assignment_delete
    db_assignment = user_location_assignment.get(db=db, id=assignment_id)
    if not db_assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff assignment not found"
        )
    
    # Verify assignment belongs to this location
    if str(db_assignment.location_id) != str(location_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignment does not belong to this location"
        )
    
    # Delete assignment
    deleted_assignment = user_location_assignment_delete(db=db, id=assignment_id)
    
    return deleted_assignment 
