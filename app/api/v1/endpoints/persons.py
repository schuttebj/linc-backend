"""
Person Management API Endpoints - CORRECTED IMPLEMENTATION
RESTful API for person CRUD operations, search, and validation
Matches corrected model structure and implements business rules
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.person_service import PersonService
from app.schemas.person import (
    PersonCreate, PersonUpdate, PersonResponse, PersonListResponse,
    PersonSearchRequest, PersonSearchResponse,
    PersonAliasCreate, PersonAliasUpdate, PersonAliasResponse,
    NaturalPersonCreate, NaturalPersonUpdate, NaturalPersonResponse,
    PersonAddressCreate, PersonAddressUpdate, PersonAddressResponse,
    OrganizationCreate, OrganizationResponse,
    PersonValidationRequest, PersonValidationResponse,
    PersonBulkCreateRequest, PersonBulkCreateResponse,
    PersonNature, IdentificationType, AddressType  # CORRECTED: PersonNature instead of PersonType
)

logger = logging.getLogger(__name__)

router = APIRouter()

# ============================================================================
# CORE PERSON ENDPOINTS - CORRECTED
# ============================================================================

@router.post("/", response_model=PersonResponse, status_code=status.HTTP_201_CREATED)
async def create_person(
    person_data: PersonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new person with optional related entities (aliases, addresses, natural person/organization details).
    
    CORRECTED: This endpoint allows for comprehensive person creation including:
    - Basic person information with person_nature (01-17)
    - Natural person details (for person_nature 01-02: Male/Female)
    - Organization details (for person_nature 03-17: Various business entity types)
    - ID documents/aliases with validation codes V00001-V00019
    - Multiple addresses (street, postal) with validation V00095-V00107
    
    Implements validation codes:
    - V00001: Identification Type Mandatory
    - V00013: Identification Number Mandatory
    - V00485: Must be natural person (when applicable)
    - And all other business rules R-ID-001 to R-ID-010
    
    Requires 'person:create' permission.
    """
    logger.info(f"Creating person: {person_data.business_or_surname} (nature: {person_data.person_nature})")
    
    service = PersonService(db)
    return service.create_person(person_data, created_by=current_user.username)


@router.get("/{person_id}", response_model=PersonResponse)
async def get_person(
    person_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get person by ID with all related data.
    
    CORRECTED: Returns complete person information including:
    - Basic person details with person_nature
    - Natural person information (if person_nature 01-02)
    - Organization information (if person_nature 03-17)
    - All ID documents/aliases with current_status_alias
    - All addresses (street and postal types)
    
    Requires 'person:read' permission.
    """
    service = PersonService(db)
    return service.get_person(person_id)


@router.put("/{person_id}", response_model=PersonResponse)
async def update_person(
    person_id: str,
    person_data: PersonUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update person information.
    
    Updates only the fields provided in the request.
    For updating related entities (aliases, addresses), use specific endpoints.
    
    Requires 'person:update' permission.
    """
    logger.info(f"Updating person: {person_id}")
    
    service = PersonService(db)
    return service.update_person(person_id, person_data, updated_by=current_user.username)


@router.delete("/{person_id}")
async def delete_person(
    person_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Soft delete person (deactivate).
    
    Sets is_active to False rather than physically deleting the record.
    This preserves data integrity for related records.
    
    Requires 'person:delete' permission.
    """
    logger.info(f"Deactivating person: {person_id}")
    
    service = PersonService(db)
    return service.delete_person(person_id)


# ============================================================================
# SEARCH AND LISTING ENDPOINTS - CORRECTED for person_nature
# ============================================================================

@router.post("/search", response_model=PersonSearchResponse)
async def search_persons(
    search_request: PersonSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Advanced person search with filtering, sorting, and pagination.
    
    CORRECTED: Search capabilities:
    - Text search in names, email, phone numbers
    - ID number search (searches across all aliases)
    - Filter by person_nature (01-17), nationality, active status
    - Sorting by various fields
    - Pagination support
    
    Person nature values:
    - 01: Male (natural person)
    - 02: Female (natural person)  
    - 03-17: Various organization types
    
    Requires 'person:read' permission.
    """
    service = PersonService(db)
    return service.search_persons(search_request)


@router.get("/", response_model=List[PersonListResponse])
async def list_persons(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    person_nature: PersonNature = Query(None, description="Filter by person nature (01-17)"),  # CORRECTED
    is_active: bool = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List persons with basic filtering and pagination.
    
    CORRECTED: Simple listing endpoint for quick access.
    Filter by person_nature instead of person_type.
    For advanced search, use the /search endpoint.
    
    Requires 'person:read' permission.
    """
    search_request = PersonSearchRequest(
        skip=skip,
        limit=limit,
        person_nature=person_nature,  # CORRECTED
        is_active=is_active
    )
    
    service = PersonService(db)
    result = service.search_persons(search_request)
    return result.persons


@router.get("/statistics/summary", response_model=Dict[str, Any])
async def get_person_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get person management statistics.
    
    CORRECTED: Returns summary statistics including:
    - Total and active person counts
    - Breakdown by person_nature (01-17)
    - Breakdown by nationality  
    - Recent registration trends
    - Address statistics (street vs postal)
    - Alias statistics by ID document type
    
    Requires 'person:read' permission.
    """
    service = PersonService(db)
    return service.get_person_statistics()


# ============================================================================
# ALIAS/ID DOCUMENT MANAGEMENT - CORRECTED validation
# ============================================================================

@router.post("/{person_id}/aliases", response_model=PersonAliasResponse, status_code=status.HTTP_201_CREATED)
async def add_person_alias(
    person_id: str,
    alias_data: PersonAliasCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add new ID document/alias to person.
    
    CORRECTED: Implements validation codes:
    - V00001: Identification Type Mandatory
    - V00013: Identification Number Mandatory
    - V00016: Unacceptable Alias Check
    - V00017: Numeric validation for RSA ID
    - V00018: ID Number length validation (13 chars for types 01,02,04)
    - V00019: Check digit validation
    
    ID Document Types:
    - 01: TRN (Tax Reference Number)
    - 02: RSA ID (South African ID Document)
    - 03: Foreign ID Document  
    - 04: BRN (Business Registration Number)
    - 13: Passport
    
    Requires 'person:update' permission.
    """
    logger.info(f"Adding alias to person {person_id}: {alias_data.id_document_type_code}")
    
    service = PersonService(db)
    return service.add_person_alias(person_id, alias_data, created_by=current_user.username)


@router.put("/aliases/{alias_id}", response_model=PersonAliasResponse)
async def update_person_alias(
    alias_id: str,
    alias_data: PersonAliasUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update person alias/ID document.
    
    Updates alias information with validation.
    Cannot change core identification numbers for audit purposes.
    
    Requires 'person:update' permission.
    """
    logger.info(f"Updating alias: {alias_id}")
    
    service = PersonService(db)
    return service.update_person_alias(alias_id, alias_data, updated_by=current_user.username)


# ============================================================================
# ADDRESS MANAGEMENT - CORRECTED for street/postal structure  
# ============================================================================

@router.post("/{person_id}/addresses", response_model=PersonAddressResponse, status_code=status.HTTP_201_CREATED)
async def add_person_address(
    person_id: str,
    address_data: PersonAddressCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add new address to person.
    
    CORRECTED: Implements address validation:
    - V00095: Postal address line 1 mandatory
    - V00098: Postal code mandatory for postal addresses
    - V00107: Postal code mandatory if street address entered
    
    Address Types:
    - street: Physical/residential address (PER.STREETADDR1-5)
    - postal: Postal address (PER.POSTADDR1-5)
    
    Address validation includes ADDRCORR validation for suburb/city matching.
    
    Requires 'person:update' permission.
    """
    logger.info(f"Adding {address_data.address_type} address to person {person_id}")
    
    service = PersonService(db)
    return service.add_person_address(person_id, address_data, created_by=current_user.username)


# ============================================================================
# VALIDATION ENDPOINTS - CORRECTED implementation
# ============================================================================

@router.post("/validate", response_model=PersonValidationResponse)
async def validate_person(
    validation_request: PersonValidationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Comprehensive person validation.
    
    CORRECTED: Validates person data against all business rules and returns:
    - Applied validation codes (V00001-V00019)
    - Validation errors and warnings
    - Business rule compliance check
    
    Validation includes:
    - Person nature validation (V00485: Must be natural person when required)
    - ID document validation (V00001-V00019)
    - Address validation (V00095-V00107)
    - Business rule compliance (R-ID-001 to R-ID-010)
    
    Requires 'person:read' permission.
    """
    service = PersonService(db)
    return service.validate_person(validation_request)


@router.get("/{person_id}/validate", response_model=PersonValidationResponse)
async def validate_person_by_id(
    person_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Validate person by ID.
    
    Convenience endpoint that creates validation request from person ID.
    Returns comprehensive validation results with all applicable codes.
    
    Requires 'person:read' permission.
    """
    validation_request = PersonValidationRequest(person_id=person_id)
    service = PersonService(db)
    return service.validate_person(validation_request)


# ============================================================================
# BULK OPERATIONS
# ============================================================================

@router.post("/bulk", response_model=PersonBulkCreateResponse, status_code=status.HTTP_201_CREATED)
async def bulk_create_persons(
    bulk_request: PersonBulkCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Bulk create multiple persons.
    
    Creates multiple persons in a single request.
    Continues processing even if some fail.
    Returns details on successful and failed creations.
    
    Each person is validated according to all business rules.
    Maximum 50 persons per bulk request.
    
    Requires 'person:create' permission.
    """
    logger.info(f"Bulk creating {len(bulk_request.persons)} persons")
    
    service = PersonService(db)
    return service.bulk_create_persons(bulk_request, created_by=current_user.username)


# ============================================================================
# UTILITY ENDPOINTS - CORRECTED
# ============================================================================

@router.post("/{person_id}/reactivate")
async def reactivate_person(
    person_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reactivate a deactivated person.
    
    Sets is_active to True for a previously deactivated person.
    Useful for correcting accidental deletions.
    
    Requires 'person:update' permission.
    """
    logger.info(f"Reactivating person: {person_id}")
    
    service = PersonService(db)
    person = service.get_person(person_id)
    
    if person.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Person is already active"
        )
    
    update_data = PersonUpdate(is_active=True)
    return service.update_person(person_id, update_data, updated_by=current_user.username)


@router.get("/search/by-id-number/{id_number}", response_model=List[PersonResponse])
async def search_by_id_number(
    id_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search persons by ID number.
    
    CORRECTED: Searches across all alias types:
    - TRN (01), RSA ID (02), Foreign ID (03), BRN (04), Passport (13)
    
    Returns all persons with matching ID number.
    Useful for duplicate checking and cross-referencing.
    
    Requires 'person:read' permission.
    """
    search_request = PersonSearchRequest(
        id_number=id_number,
        limit=100  # Allow more results for ID searches
    )
    
    service = PersonService(db)
    result = service.search_persons(search_request)
    
    # Return full person details for ID searches
    person_ids = [p.id for p in result.persons]
    return service.get_persons_by_ids(person_ids)


@router.get("/search/by-name/{name}", response_model=List[PersonListResponse])
async def search_by_name(
    name: str,
    limit: int = Query(20, ge=1, le=100, description="Number of results to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search persons by name.
    
    Searches in business_or_surname and initials fields.
    Returns basic person information for quick selection.
    
    Requires 'person:read' permission.
    """
    search_request = PersonSearchRequest(
        name=name,
        limit=limit
    )
    
    service = PersonService(db)
    result = service.search_persons(search_request)
    return result.persons


# ============================================================================
# LOOKUP ENDPOINTS - NEW for validation assistance
# ============================================================================

@router.get("/lookups/person-natures", response_model=List[Dict[str, str]])
async def get_person_natures():
    """
    Get available person nature types.
    
    Returns all valid person_nature values with descriptions:
    - 01-02: Natural persons (Male/Female)
    - 03-17: Organization types
    
    Useful for form dropdowns and validation.
    """
    return [
        {"code": nature.value, "name": nature.name, "description": {
            "01": "Male (Natural Person)",
            "02": "Female (Natural Person)", 
            "03": "Company/Corporation",
            "10": "Close Corporation",
            "11": "Trust",
            "12": "Partnership", 
            "13": "Sole Proprietorship",
            "14": "Association",
            "15": "Cooperative",
            "16": "Non-Profit Organization",
            "17": "Other Organization"
        }.get(nature.value, nature.name)}
        for nature in PersonNature
    ]


@router.get("/lookups/id-document-types", response_model=List[Dict[str, str]])
async def get_id_document_types():
    """
    Get available ID document types.
    
    CORRECTED: Returns valid LmIdDocTypeCd lookup values:
    - 01: TRN (Tax Reference Number)
    - 02: RSA ID (South African ID Document)
    - 03: Foreign ID Document
    - 04: BRN (Business Registration Number)
    - 13: Passport
    
    Useful for form dropdowns and validation.
    """
    return [
        {"code": doc_type.value, "name": doc_type.name, "description": {
            "01": "Tax Reference Number (TRN)",
            "02": "RSA ID Document (13 digits numeric)",
            "03": "Foreign ID Document", 
            "04": "Business Registration Number (BRN)",
            "13": "Passport"
        }.get(doc_type.value, doc_type.name)}
        for doc_type in IdentificationType
    ]


@router.get("/lookups/address-types", response_model=List[Dict[str, str]])
async def get_address_types():
    """
    Get available address types.
    
    CORRECTED: Returns address types matching documentation structure:
    - street: Physical/residential address (PER.STREETADDR1-5)
    - postal: Postal address (PER.POSTADDR1-5)
    
    Useful for form dropdowns and validation.
    """
    return [
        {"code": addr_type.value, "name": addr_type.name, "description": {
            "street": "Physical/Residential Address (PER.STREETADDR1-5)",
            "postal": "Postal Address (PER.POSTADDR1-5)"
        }.get(addr_type.value, addr_type.name)}
        for addr_type in AddressType
    ] 