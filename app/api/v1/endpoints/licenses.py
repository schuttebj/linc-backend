from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from uuid import UUID

from ....core.database import get_db
from ....core.security import get_current_user
from ....models.license import ApplicationStatus, LicenseType
from ....schemas.license import (
    LicenseApplicationCreate,
    LicenseApplicationUpdate,
    LicenseApplicationResponse,
    LicenseApplicationValidation,
    LicenseApplicationSummary,
    LicenseCardCreate,
    LicenseCardResponse,
    ApplicationPaymentCreate,
    ApplicationPaymentResponse,
    TestCenterCreate,
    TestCenterResponse
)
from ....services.license_service import LicenseApplicationService
from ....services.validation import ValidationOrchestrator

router = APIRouter()


@router.post("/applications", response_model=LicenseApplicationResponse)
async def create_license_application(
    application_data: LicenseApplicationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new license application
    
    Reference: Section 2.1 License Application Form
    Business Rules: R-APP-001 to R-APP-009
    """
    try:
        service = LicenseApplicationService(db, application_data.country_code)
        application, validation_result = service.create_application(
            application_data, 
            current_user["user_id"]
        )
        
        return LicenseApplicationResponse.from_orm(application)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create application: {str(e)}")


@router.get("/applications/{application_id}", response_model=LicenseApplicationResponse)
async def get_license_application(
    application_id: str = Path(..., description="Application UUID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific license application by ID
    """
    try:
        # Extract country code from user context or application
        country_code = current_user.get("country_code", "ZA")
        service = LicenseApplicationService(db, country_code)
        
        application = service.get_application_by_id(application_id)
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        return LicenseApplicationResponse.from_orm(application)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve application: {str(e)}")


@router.put("/applications/{application_id}", response_model=LicenseApplicationResponse)
async def update_license_application(
    application_id: str = Path(..., description="Application UUID"),
    update_data: LicenseApplicationUpdate = ...,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update an existing license application
    """
    try:
        country_code = current_user.get("country_code", "ZA")
        service = LicenseApplicationService(db, country_code)
        
        application = service.update_application(
            application_id, 
            update_data, 
            current_user["user_id"]
        )
        
        return LicenseApplicationResponse.from_orm(application)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update application: {str(e)}")


@router.post("/applications/{application_id}/submit", response_model=LicenseApplicationResponse)
async def submit_license_application(
    application_id: str = Path(..., description="Application UUID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Submit a license application for processing
    
    Business Rule: R-APP-001 (State Transition: DRAFT → SUBMITTED)
    """
    try:
        country_code = current_user.get("country_code", "ZA")
        service = LicenseApplicationService(db, country_code)
        
        application = service.submit_application(application_id, current_user["user_id"])
        
        return LicenseApplicationResponse.from_orm(application)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit application: {str(e)}")


@router.post("/applications/validate", response_model=LicenseApplicationValidation)
async def validate_license_application(
    application_data: LicenseApplicationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Validate a license application without creating it
    
    Useful for frontend validation and pre-submission checks
    Business Rules: R-APP-003 to R-APP-008
    """
    try:
        service = LicenseApplicationService(db, application_data.country_code)
        validation_result = service.validate_application(application_data)
        
        return validation_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.get("/applications", response_model=List[LicenseApplicationSummary])
async def list_license_applications(
    status: Optional[ApplicationStatus] = Query(None, description="Filter by application status"),
    license_type: Optional[LicenseType] = Query(None, description="Filter by license type"),
    person_id: Optional[str] = Query(None, description="Filter by person UUID"),
    limit: int = Query(50, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List license applications with filtering and pagination
    """
    try:
        country_code = current_user.get("country_code", "ZA")
        service = LicenseApplicationService(db, country_code)
        
        if person_id:
            applications = service.get_applications_by_person(person_id)
        elif status:
            applications = service.get_applications_by_status(status)
        else:
            # Get all applications for the country (implement pagination)
            applications = service.get_applications_by_status(None)  # This would need to be implemented
        
        # Apply additional filters
        if license_type:
            applications = [app for app in applications if app.license_type == license_type]
        
        # Apply pagination
        applications = applications[offset:offset + limit]
        
        # Convert to summary format
        summaries = []
        for app in applications:
            person_name = f"{app.person.first_name} {app.person.surname}" if app.person else "Unknown"
            summaries.append(LicenseApplicationSummary(
                id=str(app.id),
                application_number=app.application_number,
                person_name=person_name,
                license_type=app.license_type,
                status=app.status,
                application_date=app.application_date,
                total_fees=app.total_fees,
                fees_paid=app.fees_paid
            ))
        
        return summaries
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list applications: {str(e)}")


@router.get("/applications/person/{person_id}", response_model=List[LicenseApplicationResponse])
async def get_person_applications(
    person_id: str = Path(..., description="Person UUID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all license applications for a specific person
    """
    try:
        country_code = current_user.get("country_code", "ZA")
        service = LicenseApplicationService(db, country_code)
        
        applications = service.get_applications_by_person(person_id)
        
        return [LicenseApplicationResponse.from_orm(app) for app in applications]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve person applications: {str(e)}")


@router.post("/cards", response_model=LicenseCardResponse)
async def create_license_card(
    card_data: LicenseCardCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a license card for production
    
    Reference: Section 2.2 Card Ordering System
    """
    try:
        # This would integrate with card production service
        # For now, return a placeholder response
        raise HTTPException(status_code=501, detail="Card production service not yet implemented")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create card: {str(e)}")


@router.get("/cards/{card_id}", response_model=LicenseCardResponse)
async def get_license_card(
    card_id: str = Path(..., description="Card UUID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get license card details
    """
    try:
        # This would retrieve card from database
        raise HTTPException(status_code=501, detail="Card retrieval service not yet implemented")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve card: {str(e)}")


@router.post("/payments", response_model=ApplicationPaymentResponse)
async def create_application_payment(
    payment_data: ApplicationPaymentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a payment for a license application
    
    Reference: Section 4.1 Fee Calculation System
    """
    try:
        # This would integrate with payment processing service
        raise HTTPException(status_code=501, detail="Payment processing service not yet implemented")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process payment: {str(e)}")


@router.get("/test-centers", response_model=List[TestCenterResponse])
async def list_test_centers(
    country_code: str = Query(..., description="Country code"),
    active_only: bool = Query(True, description="Return only active test centers"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List available test centers for a country
    """
    try:
        # This would retrieve test centers from database
        raise HTTPException(status_code=501, detail="Test center service not yet implemented")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list test centers: {str(e)}")


@router.post("/test-centers", response_model=TestCenterResponse)
async def create_test_center(
    center_data: TestCenterCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new test center
    
    Requires administrative privileges
    """
    try:
        # Check if user has admin privileges
        if not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Administrative privileges required")
        
        # This would create test center in database
        raise HTTPException(status_code=501, detail="Test center creation service not yet implemented")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create test center: {str(e)}")


@router.get("/license-types", response_model=List[dict])
async def get_available_license_types(
    country_code: str = Query(..., description="Country code"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get available license types for a country
    
    Returns license types with their requirements and fees
    """
    try:
        # This would be configurable per country
        license_types = []
        
        for license_type in LicenseType:
            # Get age requirements
            age_requirements = {
                LicenseType.LEARNER_A: 16,
                LicenseType.LEARNER_B: 16,
                LicenseType.A: 16,
                LicenseType.B: 18,
                LicenseType.C1: 18,
                LicenseType.C: 21,
                LicenseType.D1: 21,
                LicenseType.D: 24,
                LicenseType.EB: 21,
                LicenseType.EC1: 21,
                LicenseType.EC: 21
            }
            
            # Get prerequisites
            prerequisites = {
                LicenseType.C: ["B"],
                LicenseType.D: ["C", "B"],
                LicenseType.EB: ["C", "B"],
                LicenseType.EC1: ["C1", "B"],
                LicenseType.EC: ["C", "B"]
            }
            
            license_types.append({
                "code": license_type.value,
                "name": license_type.name,
                "description": f"{license_type.value} License",
                "minimum_age": age_requirements.get(license_type, 18),
                "prerequisites": prerequisites.get(license_type, []),
                "test_required": True,
                "medical_required": license_type in [
                    LicenseType.C, LicenseType.C1, LicenseType.D, 
                    LicenseType.D1, LicenseType.EB, LicenseType.EC, LicenseType.EC1
                ]
            })
        
        return license_types
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve license types: {str(e)}")


@router.get("/application-statuses", response_model=List[dict])
async def get_application_statuses():
    """
    Get all possible application statuses
    
    Reference: R-APP-001 Application State Management
    """
    try:
        statuses = []
        
        for status in ApplicationStatus:
            statuses.append({
                "code": status.value,
                "name": status.name,
                "description": status.value.replace("_", " ").title()
            })
        
        return statuses
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve statuses: {str(e)}")


@router.get("/applications/{application_id}/validation-history", response_model=List[dict])
async def get_application_validation_history(
    application_id: str = Path(..., description="Application UUID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get validation history for an application
    
    Shows all validation codes and business rules applied
    """
    try:
        country_code = current_user.get("country_code", "ZA")
        service = LicenseApplicationService(db, country_code)
        
        application = service.get_application_by_id(application_id)
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        return {
            "validation_codes": application.validation_codes or [],
            "business_rules_applied": application.business_rules_applied or [],
            "last_validation": application.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve validation history: {str(e)}") 