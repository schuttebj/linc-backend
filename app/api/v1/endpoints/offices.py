"""
Office Management API Endpoints
RESTful API for managing physical offices, facilities, and resources
Merged from Location model - represents physical offices where services are provided
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.permission_middleware import require_permission, require_any_permission
from app.crud.office import office, office_create, office_update, office_delete
from app.schemas.office import (
    OfficeCreate,
    OfficeCreateNested, 
    OfficeUpdate, 
    OfficeResponse, 
    OfficeListFilter,
    OfficeStatistics,
    UserOfficeAssignmentCreate,
    UserOfficeAssignmentUpdate,
    UserOfficeAssignmentResponse
)
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=OfficeResponse, status_code=status.HTTP_201_CREATED)
def create_office(
    *,
    db: Session = Depends(get_db),
    office_in: OfficeCreateNested,
    current_user: User = Depends(require_permission("office.create"))
):
    """
    Create new office with nested address support.
    
    Requires office.create permission.
    """
    
    # Check if office code already exists within the region
    if office.check_code_exists(db, office_in.region_id, office_in.office_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Office code already exists in this region"
        )
    
    # Convert nested address structure to flat structure for database storage
    flat_office_data = office_in.to_flat_office_create()
    
    # Create OfficeCreate object with flat structure and add required fields
    office_create_data = OfficeCreate(
        region_id=office_in.region_id,
        **flat_office_data.dict()
    )
    
    # Create office
    db_office = office_create(
        db=db, 
        obj_in=office_create_data, 
        created_by=current_user.username
    )
    
    return db_office

@router.get("/", response_model=List[OfficeResponse])
def read_offices(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("office.read")),
    skip: int = 0,
    limit: int = 100
):
    """
    Retrieve offices with optional filtering.
    
    Requires office.read permission.
    """
    
    offices = office.get_multi(db=db, skip=skip, limit=limit)
    return offices

@router.get("/statistics", response_model=OfficeStatistics)
def get_office_statistics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("office.read"))
):
    """
    Get office statistics.
    
    Requires office.read permission.
    """
    
    stats = office.get_statistics(db=db)
    return stats

@router.get("/{office_id}", response_model=OfficeResponse)
def read_office(
    *,
    db: Session = Depends(get_db),
    office_id: UUID,
    current_user: User = Depends(require_permission("office.read"))
):
    """
    Get office by ID.
    
    Requires office.read permission.
    """
    
    db_office = office.get(db=db, id=office_id)
    if not db_office:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Office not found"
        )
    
    # Check if user can access this office
    if not current_user.can_access_office(str(office_id)):
        if not current_user.can_access_province(db_office.province_code):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to access this office"
            )
    
    return db_office

@router.put("/{office_id}", response_model=OfficeResponse)
def update_office(
    *,
    db: Session = Depends(get_db),
    office_id: UUID,
    office_in: OfficeUpdate,
    current_user: User = Depends(require_permission("office.update"))
):
    """
    Update office.
    
    Requires office.update permission.
    """
    
    db_office = office.get(db=db, id=office_id)
    if not db_office:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Office not found"
        )
    
    # Check if user can access this office
    if not current_user.can_access_office(str(office_id)):
        if not current_user.can_access_province(db_office.province_code):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to update this office"
            )
    
    updated_office = office_update(
        db=db, 
        db_obj=db_office, 
        obj_in=office_in,
        updated_by=current_user.username
    )
    
    return updated_office

@router.delete("/{office_id}", response_model=OfficeResponse)
def delete_office(
    *,
    db: Session = Depends(get_db),
    office_id: UUID,
    current_user: User = Depends(require_permission("office.delete"))
):
    """
    Delete office (soft delete).
    
    Requires office.delete permission.
    """
    
    db_office = office.get(db=db, id=office_id)
    if not db_office:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Office not found"
        )
    
    # Check if user can access this office
    if not current_user.can_access_office(str(office_id)):
        if not current_user.can_access_province(db_office.province_code):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to delete this office"
            )
    
    deleted_office = office_delete(db=db, id=office_id)
    return deleted_office

@router.get("/by-province/{province_code}", response_model=List[OfficeResponse])
def get_offices_by_province(
    *,
    db: Session = Depends(get_db),
    province_code: str,
    current_user: User = Depends(require_permission("office.read"))
):
    """
    Get offices by province code.
    
    Requires office.read permission.
    """
    
    # Check if user can access this province
    if not current_user.can_access_province(province_code):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access offices in this province"
        )
    
    offices = office.get_by_province(db=db, province_code=province_code)
    return offices

@router.get("/by-region/{region_id}", response_model=List[OfficeResponse])
def get_offices_by_region(
    *,
    db: Session = Depends(get_db),
    region_id: UUID,
    current_user: User = Depends(require_permission("office.read"))
):
    """
    Get offices by region ID.
    
    Requires office.read permission.
    """
    
    offices = office.get_by_region(db=db, region_id=region_id)
    return offices

@router.get("/type/dltc", response_model=List[OfficeResponse])
def get_dltc_offices(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("office.read"))
):
    """
    Get all DLTC offices (Fixed and Mobile).
    
    Requires office.read permission.
    """
    
    offices = office.get_by_infrastructure_type(
        db=db, 
        infrastructure_types=["10", "11"]  # Fixed DLTC, Mobile DLTC
    )
    return offices

@router.get("/type/printing", response_model=List[OfficeResponse])
def get_printing_offices(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("office.read"))
):
    """
    Get all printing facilities.
    
    Requires office.read permission.
    """
    
    offices = office.get_by_infrastructure_type(
        db=db, 
        infrastructure_types=["12", "13"]  # Printing Center, Combined Center
    )
    return offices

@router.get("/operational", response_model=List[OfficeResponse])
def get_operational_offices(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("office.read"))
):
    """
    Get all operational offices.
    
    Requires office.read permission.
    """
    
    offices = office.get_operational(db=db)
    return offices

@router.get("/public", response_model=List[OfficeResponse])
def get_public_offices(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("office.read"))
):
    """
    Get all public-facing offices.
    
    Requires office.read permission.
    """
    
    offices = office.get_public(db=db)
    return offices

@router.get("/with-capacity", response_model=List[OfficeResponse])
def get_offices_with_capacity(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("office.read")),
    min_capacity: int = Query(1, description="Minimum available capacity")
):
    """
    Get offices with available capacity.
    
    Requires office.read permission.
    """
    
    offices = office.get_with_capacity(db=db, min_capacity=min_capacity)
    return offices

@router.put("/{office_id}/load", response_model=OfficeResponse)
def update_office_load(
    *,
    db: Session = Depends(get_db),
    office_id: UUID,
    new_load: int = Query(..., description="New load value"),
    current_user: User = Depends(require_permission("office.update"))
):
    """
    Update office current load.
    
    Requires office.update permission.
    """
    
    db_office = office.get(db=db, id=office_id)
    if not db_office:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Office not found"
        )
    
    # Check if user can access this office
    if not current_user.can_access_office(str(office_id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this office"
        )
    
    updated_office = office.update_load(db=db, office_id=office_id, new_load=new_load)
    return updated_office

@router.get("/validate-code/{region_id}/{office_code}", response_model=dict)
def validate_office_code(
    *,
    db: Session = Depends(get_db),
    region_id: UUID,
    office_code: str,
    current_user: User = Depends(require_permission("office.create"))
):
    """
    Validate if office code is available in the region.
    
    Requires office.create permission.
    """
    
    is_available = not office.check_code_exists(db, region_id, office_code)
    
    return {
        "office_code": office_code,
        "region_id": str(region_id),
        "available": is_available
    }

@router.post("/{office_id}/staff", response_model=UserOfficeAssignmentResponse, status_code=status.HTTP_201_CREATED)
def assign_staff_to_office(
    *,
    db: Session = Depends(get_db),
    office_id: UUID,
    assignment_in: UserOfficeAssignmentCreate,
    current_user: User = Depends(require_any_permission("office.create", "region.update"))
):
    """
    Assign staff member to office.
    
    Requires office.create or region.update permission.
    """
    
    from app.crud.user_location_assignment import user_location_assignment_create
    
    # Verify office exists
    db_office = office.get(db=db, id=office_id)
    if not db_office:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Office not found"
        )
    
    # Create assignment with office_id instead of location_id
    assignment_data = assignment_in.dict()
    assignment_data["office_id"] = office_id
    
    assignment = user_location_assignment_create(
        db=db,
        obj_in=assignment_data,
        created_by=current_user.username
    )
    
    return assignment

@router.get("/{office_id}/staff", response_model=List[UserOfficeAssignmentResponse])
def get_office_staff(
    *,
    db: Session = Depends(get_db),
    office_id: UUID,
    current_user: User = Depends(require_permission("office.read"))
):
    """
    Get staff assignments for office.
    
    Requires office.read permission.
    """
    
    from app.crud.user_location_assignment import user_location_assignment
    
    # Verify office exists
    db_office = office.get(db=db, id=office_id)
    if not db_office:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Office not found"
        )
    
    assignments = user_location_assignment.get_by_office(db=db, office_id=office_id)
    return assignments

@router.put("/{office_id}/staff/{assignment_id}", response_model=UserOfficeAssignmentResponse)
def update_staff_assignment(
    *,
    db: Session = Depends(get_db),
    office_id: UUID,
    assignment_id: UUID,
    assignment_in: UserOfficeAssignmentUpdate,
    current_user: User = Depends(require_any_permission("office.update", "region.update"))
):
    """
    Update staff assignment.
    
    Requires office.update or region.update permission.
    """
    
    from app.crud.user_location_assignment import user_location_assignment, user_location_assignment_update
    
    # Verify assignment exists and belongs to office
    db_assignment = user_location_assignment.get(db=db, id=assignment_id)
    if not db_assignment or str(db_assignment.office_id) != str(office_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    updated_assignment = user_location_assignment_update(
        db=db,
        db_obj=db_assignment,
        obj_in=assignment_in,
        updated_by=current_user.username
    )
    
    return updated_assignment

@router.delete("/{office_id}/staff/{assignment_id}", response_model=UserOfficeAssignmentResponse)
def remove_staff_assignment(
    *,
    db: Session = Depends(get_db),
    office_id: UUID,
    assignment_id: UUID,
    current_user: User = Depends(require_any_permission("office.delete", "region.update"))
):
    """
    Remove staff assignment from office.
    
    Requires office.delete or region.update permission.
    """
    
    from app.crud.user_location_assignment import user_location_assignment, user_location_assignment_delete
    
    # Verify assignment exists and belongs to office
    db_assignment = user_location_assignment.get(db=db, id=assignment_id)
    if not db_assignment or str(db_assignment.office_id) != str(office_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    deleted_assignment = user_location_assignment_delete(db=db, id=assignment_id)
    return deleted_assignment 