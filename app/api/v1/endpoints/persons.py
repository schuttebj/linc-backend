"""
Person Management Endpoints
CRUD operations for person registration, search, and management
Reference: Section 1.1 Person Registration/Search Screen
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
import structlog
from datetime import date, datetime

from app.core.database import get_db
from app.schemas.person import (
    PersonCreateRequest, PersonSearchRequest, PersonResponse, 
    PersonListResponse, PersonValidationResponse, ValidationResult
)
from app.models.person import Person, PersonAddress
from app.services.person_service import PersonService
from app.services.validation_service import ValidationService

router = APIRouter()
logger = structlog.get_logger()


@router.post("/", response_model=PersonResponse, status_code=status.HTTP_201_CREATED)
async def create_person(
    country: str = Path(..., description="Country code"),
    person_data: PersonCreateRequest = ...,
    db: Session = Depends(get_db)
) -> PersonResponse:
    """
    Create a new person record
    
    Implements Section 1.1 Person Registration/Search Screen
    Applies business rules V00001-V00019, V00485, V00585
    """
    country_code = country.upper()
    
    # Initialize services
    person_service = PersonService(db, country_code)
    validation_service = ValidationService(db, country_code)
    
    try:
        # Validate business rules
        validation_results = await validation_service.validate_person_creation(person_data)
        
        # Check if validation passed
        if not all(result.is_valid for result in validation_results):
            failed_validations = [r for r in validation_results if not r.is_valid]
            logger.warning(
                "Person creation validation failed",
                validation_errors=[r.dict() for r in failed_validations],
                country=country_code
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "message": "Validation failed",
                    "validation_errors": [r.dict() for r in failed_validations]
                }
            )
        
        # Check if person already exists (V00014)
        existing_person = await person_service.find_by_identification(
            person_data.identification_type,
            person_data.identification_number
        )
        
        if existing_person:
            logger.warning(
                "Attempt to create duplicate person",
                existing_person_id=str(existing_person.id),
                identification_number=person_data.identification_number,
                country=country_code
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "Person with this identification already exists",
                    "validation_code": "V00014",
                    "existing_person_id": str(existing_person.id)
                }
            )
        
        # Create person
        person = await person_service.create_person(person_data)
        
        logger.info(
            "Person created successfully",
            person_id=str(person.id),
            identification_number=person.identification_number,
            name=person.full_name,
            country=country_code
        )
        
        return PersonResponse.from_orm(person)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error creating person",
            error=str(e),
            country=country_code,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during person creation"
        )


@router.get("/search", response_model=PersonListResponse)
async def search_persons(
    country: str = Path(..., description="Country code"),
    identification_type: Optional[str] = Query(None, description="Identification document type"),
    identification_number: Optional[str] = Query(None, description="Identification number"),
    first_name: Optional[str] = Query(None, description="First name"),
    surname: Optional[str] = Query(None, description="Surname"),
    date_of_birth: Optional[date] = Query(None, description="Date of birth"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db)
) -> PersonListResponse:
    """
    Search for persons with various criteria
    
    Implements person search functionality from Section 1.1
    """
    country_code = country.upper()
    
    try:
        person_service = PersonService(db, country_code)
        
        # Build search criteria
        search_request = PersonSearchRequest(
            identification_type=identification_type,
            identification_number=identification_number,
            first_name=first_name,
            surname=surname,
            date_of_birth=date_of_birth
        )
        
        # Perform search
        persons, total_count = await person_service.search_persons(
            search_request, page, page_size
        )
        
        logger.info(
            "Person search performed",
            search_criteria=search_request.dict(exclude_none=True),
            results_count=len(persons),
            total_count=total_count,
            country=country_code
        )
        
        return PersonListResponse(
            persons=[PersonResponse.from_orm(person) for person in persons],
            total_count=total_count,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(
            "Error searching persons",
            error=str(e),
            country=country_code,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during person search"
        )


@router.get("/{person_id}", response_model=PersonResponse)
async def get_person(
    country: str = Path(..., description="Country code"),
    person_id: str = Path(..., description="Person UUID"),
    db: Session = Depends(get_db)
) -> PersonResponse:
    """Get person by ID"""
    country_code = country.upper()
    
    try:
        person_service = PersonService(db, country_code)
        person = await person_service.get_by_id(person_id)
        
        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Person with ID {person_id} not found"
            )
        
        logger.info(
            "Person retrieved",
            person_id=person_id,
            country=country_code
        )
        
        return PersonResponse.from_orm(person)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error retrieving person",
            error=str(e),
            person_id=person_id,
            country=country_code,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during person retrieval"
        )


@router.put("/{person_id}", response_model=PersonResponse)
async def update_person(
    country: str = Path(..., description="Country code"),
    person_id: str = Path(..., description="Person UUID"),
    person_data: PersonCreateRequest = ...,
    db: Session = Depends(get_db)
) -> PersonResponse:
    """Update person information"""
    country_code = country.upper()
    
    try:
        person_service = PersonService(db, country_code)
        validation_service = ValidationService(db, country_code)
        
        # Check if person exists
        existing_person = await person_service.get_by_id(person_id)
        if not existing_person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Person with ID {person_id} not found"
            )
        
        # Validate business rules for updates
        validation_results = await validation_service.validate_person_update(
            person_id, person_data
        )
        
        if not all(result.is_valid for result in validation_results):
            failed_validations = [r for r in validation_results if not r.is_valid]
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "message": "Validation failed",
                    "validation_errors": [r.dict() for r in failed_validations]
                }
            )
        
        # Update person
        updated_person = await person_service.update_person(person_id, person_data)
        
        logger.info(
            "Person updated successfully",
            person_id=person_id,
            country=country_code
        )
        
        return PersonResponse.from_orm(updated_person)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error updating person",
            error=str(e),
            person_id=person_id,
            country=country_code,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during person update"
        )


@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person(
    country: str = Path(..., description="Country code"),
    person_id: str = Path(..., description="Person UUID"),
    db: Session = Depends(get_db)
):
    """Soft delete a person record"""
    country_code = country.upper()
    
    try:
        person_service = PersonService(db, country_code)
        
        # Check if person exists
        person = await person_service.get_by_id(person_id)
        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Person with ID {person_id} not found"
            )
        
        # Perform soft delete
        await person_service.soft_delete_person(person_id)
        
        logger.info(
            "Person soft deleted",
            person_id=person_id,
            country=country_code
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error deleting person",
            error=str(e),
            person_id=person_id,
            country=country_code,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during person deletion"
        )


@router.post("/validate", response_model=PersonValidationResponse)
async def validate_person(
    country: str = Path(..., description="Country code"),
    person_data: PersonCreateRequest = ...,
    db: Session = Depends(get_db)
) -> PersonValidationResponse:
    """
    Validate person data against business rules without creating
    
    Useful for frontend validation and form checking
    Implements all validation rules V00001-V00019, V00485, V00585
    """
    country_code = country.upper()
    
    try:
        validation_service = ValidationService(db, country_code)
        
        # Run all validation rules
        validation_results = await validation_service.validate_person_creation(person_data)
        
        # Check if person already exists
        person_service = PersonService(db, country_code)
        existing_person = await person_service.find_by_identification(
            person_data.identification_type,
            person_data.identification_number
        )
        
        if existing_person:
            validation_results.append(ValidationResult(
                is_valid=False,
                code="V00014",
                message="Person with this identification already exists"
            ))
        
        is_valid = all(result.is_valid for result in validation_results)
        
        logger.info(
            "Person validation performed",
            is_valid=is_valid,
            validation_count=len(validation_results),
            country=country_code
        )
        
        return PersonValidationResponse(
            person_id=str(existing_person.id) if existing_person else None,
            validation_results=validation_results,
            is_valid=is_valid
        )
        
    except Exception as e:
        logger.error(
            "Error validating person",
            error=str(e),
            country=country_code,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during person validation"
        )


@router.get("/{person_id}/eligibility/{license_type}")
async def check_license_eligibility(
    country: str = Path(..., description="Country code"),
    person_id: str = Path(..., description="Person UUID"),
    license_type: str = Path(..., description="License type (A, B, C, D, EB, EC)"),
    db: Session = Depends(get_db)
) -> dict:
    """Check if person is eligible for specific license type"""
    country_code = country.upper()
    
    try:
        person_service = PersonService(db, country_code)
        person = await person_service.get_by_id(person_id)
        
        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Person with ID {person_id} not found"
            )
        
        # Check age eligibility
        is_eligible = person.is_eligible_for_license_type(license_type)
        current_age = person.get_age()
        
        # Get age requirement for license type
        age_requirements = {
            'A': 16, 'B': 18, 'C': 21, 'D': 24, 'EB': 18, 'EC': 21
        }
        required_age = age_requirements.get(license_type, 18)
        
        return {
            "person_id": person_id,
            "license_type": license_type,
            "is_eligible": is_eligible,
            "current_age": current_age,
            "required_age": required_age,
            "eligibility_reason": "Age requirement met" if is_eligible else f"Must be at least {required_age} years old"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error checking license eligibility",
            error=str(e),
            person_id=person_id,
            license_type=license_type,
            country=country_code,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during eligibility check"
        )


@router.get("/search")
async def search_persons(
    country: str = Path(..., description="Country code"),
    identification_number: Optional[str] = Query(None),
    surname: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Search for persons"""
    
    return {
        "persons": [],
        "total_count": 0,
        "message": "Search functionality will be implemented"
    } 