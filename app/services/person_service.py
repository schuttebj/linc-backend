"""
Person Management Service - CORRECTED IMPLEMENTATION
Handles CRUD operations, search, validation for person entities
Matches corrected model structure and implements business rules
"""

from typing import Optional, List, Dict, Any, Union
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
import logging
from datetime import datetime, date

from app.models.person import Person, PersonAlias, NaturalPerson, PersonAddress, Organization
from app.schemas.person import (
    PersonCreate, PersonUpdate, PersonResponse, PersonListResponse,
    PersonSearchRequest, PersonSearchResponse,
    PersonAliasCreate, PersonAliasUpdate, PersonAliasResponse,
    NaturalPersonCreate, NaturalPersonUpdate, NaturalPersonResponse,
    PersonAddressCreate, PersonAddressUpdate, PersonAddressResponse,
    OrganizationCreate, OrganizationResponse,
    PersonValidationRequest, PersonValidationResponse,
    PersonBulkCreateRequest, PersonBulkCreateResponse,
    PersonNature, IdentificationType, AddressType
)
from app.services.validation import PersonValidationService, ValidationResult, ValidationOrchestrator, validate_business_rules

logger = logging.getLogger(__name__)


class PersonService:
    """
    Person management service with comprehensive business logic
    Implements corrected model structure and validation rules
    """

    def __init__(self, db: Session):
        self.db = db
        self.validation_service = PersonValidationService(db)
        self.validation_orchestrator = ValidationOrchestrator(self.validation_service)

    # ============================================================================
    # CORE PERSON CRUD OPERATIONS - ENHANCED WITH ORCHESTRATOR
    # ============================================================================

    @validate_business_rules("person_creation")
    def create_person(self, person_data: PersonCreate, created_by: str = None) -> PersonResponse:
        """
        Create a new person with related entities - ENHANCED WITH VALIDATION ORCHESTRATOR
        Validation is now IMPOSSIBLE to miss or bypass
        """
        try:
            # STEP 1: MANDATORY Validation using orchestrator - CANNOT BE SKIPPED
            validation_summary = self.validation_orchestrator.validate_person_operation(
                "person_creation", 
                person_data.dict()
            )
            
            if not validation_summary.is_valid:
                # Format validation errors with codes
                error_messages = [f"{r.code}: {r.message}" for r in validation_summary.errors]
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Validation failed: {'; '.join(error_messages)}"
                )
            
            # Log warnings if any
            if validation_summary.warnings:
                warning_messages = [f"{r.code}: {r.message}" for r in validation_summary.warnings]
                logger.warning(f"Person creation warnings: {'; '.join(warning_messages)}")
            
            # STEP 2: Auto-derive data from RSA ID if provided
            derived_data = self._auto_derive_from_id(person_data)
            
            # STEP 3: Create main person record
            db_person = Person(
                business_or_surname=person_data.business_or_surname,
                initials=person_data.initials,
                person_nature=person_data.person_nature.value,
                nationality_code=person_data.nationality_code,
                email_address=person_data.email_address,
                home_phone_code=person_data.home_phone_code,
                home_phone_number=person_data.home_phone_number,
                work_phone_code=person_data.work_phone_code,
                work_phone_number=person_data.work_phone_number,
                cell_phone=person_data.cell_phone,
                fax_code=person_data.fax_code,
                fax_number=person_data.fax_number,
                preferred_language=person_data.preferred_language,
                current_status_alias=person_data.current_status_alias,
                created_by=created_by,
                updated_by=created_by
            )
            
            self.db.add(db_person)
            self.db.flush()  # Get the person ID
            
            # STEP 4: Create natural person record if applicable (person_nature 01/02)
            if person_data.person_nature in [PersonNature.MALE, PersonNature.FEMALE]:
                if not person_data.natural_person:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Natural person details required for person_nature 01/02 (V00485)"
                    )
                
                natural_person = NaturalPerson(
                    person_id=db_person.id,
                    full_name_1=person_data.natural_person.full_name_1,
                    full_name_2=person_data.natural_person.full_name_2,
                    full_name_3=person_data.natural_person.full_name_3,
                    birth_date=derived_data.get('birth_date') or person_data.natural_person.birth_date,
                    email_address=person_data.natural_person.email_address,
                    preferred_language_code=person_data.natural_person.preferred_language_code,
                    created_by=created_by,
                    updated_by=created_by
                )
                self.db.add(natural_person)
            
            # STEP 5: Create organization record if applicable (person_nature 03-17)
            elif person_data.organization:
                organization = Organization(
                    person_id=db_person.id,
                    trading_name=person_data.organization.trading_name,
                    registration_date=person_data.organization.registration_date,
                    representative_person_id=person_data.organization.representative_person_id,
                    proxy_person_id=person_data.organization.proxy_person_id,
                    local_authority_code=person_data.organization.local_authority_code,
                    dcee_address=person_data.organization.dcee_address,
                    resident_at_ra=person_data.organization.resident_at_ra,
                    movement_restricted=person_data.organization.movement_restricted,
                    created_by=created_by,
                    updated_by=created_by
                )
                self.db.add(organization)
            
            # STEP 6: Create aliases if provided
            if person_data.aliases:
                for alias_data in person_data.aliases:
                    alias = PersonAlias(
                        person_id=db_person.id,
                        id_document_type_code=alias_data.id_document_type_code.value,
                        id_document_number=alias_data.id_document_number,
                        country_of_issue=alias_data.country_of_issue,
                        name_in_document=alias_data.name_in_document,
                        alias_status=alias_data.alias_status,
                        is_current=alias_data.is_current,
                        created_by=created_by
                    )
                    self.db.add(alias)
            
            # STEP 7: Create addresses if provided
            if person_data.addresses:
                for addr_data in person_data.addresses:
                    address = PersonAddress(
                        person_id=db_person.id,
                        address_type=addr_data.address_type.value,
                        is_primary=addr_data.is_primary,
                        address_line_1=addr_data.address_line_1,
                        address_line_2=addr_data.address_line_2,
                        address_line_3=addr_data.address_line_3,
                        address_line_4=addr_data.address_line_4,
                        address_line_5=addr_data.address_line_5,
                        postal_code=addr_data.postal_code,
                        country_code=addr_data.country_code,
                        province_code=addr_data.province_code,
                        suburb_validated=False,  # Will be validated in background
                        city_validated=False,   # Will be validated in background
                        created_by=created_by,
                        updated_by=created_by
                    )
                    self.db.add(address)
            
            self.db.commit()
            
            # STEP 8: Log validation summary for audit
            logger.info(f"Person created successfully with {len(validation_summary.validation_codes)} validations: {validation_summary.validation_codes}")
            
            # Return full person with relationships
            return self.get_person(db_person.id)
            
        except HTTPException:
            self.db.rollback()
            raise
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to create person: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Person creation failed due to data constraints"
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error creating person: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal error creating person"
            )

    def get_person(self, person_id: str) -> PersonResponse:
        """Get person by ID with all related data - CORRECTED relationships"""
        person = self.db.query(Person).options(
            selectinload(Person.natural_person),
            selectinload(Person.aliases),
            selectinload(Person.addresses)
        ).filter(Person.id == person_id).first()
        
        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Person with ID {person_id} not found"
            )
        
        return PersonResponse.from_orm(person)

    def update_person(self, person_id: str, person_data: PersonUpdate, updated_by: str = None) -> PersonResponse:
        """Update person details - CORRECTED field names"""
        person = self.db.query(Person).filter(Person.id == person_id).first()
        
        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Person with ID {person_id} not found"
            )
        
        try:
            # Update fields that are provided
            update_data = person_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(person, field):
                    setattr(person, field, value)
            
            person.updated_by = updated_by
            person.updated_at = datetime.utcnow()
            
            self.db.commit()
            return self.get_person(person_id)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update person {person_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update person"
            )

    def delete_person(self, person_id: str) -> Dict[str, str]:
        """Soft delete person (set is_active to False)"""
        person = self.db.query(Person).filter(Person.id == person_id).first()
        
        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Person with ID {person_id} not found"
            )
        
        person.is_active = False
        person.updated_at = datetime.utcnow()
        self.db.commit()
        
        return {"message": f"Person {person_id} has been deactivated"}

    # ============================================================================
    # SEARCH AND QUERY OPERATIONS - CORRECTED for person_nature
    # ============================================================================

    def search_persons(self, search_request: PersonSearchRequest) -> PersonSearchResponse:
        """
        Advanced person search with filters and pagination
        CORRECTED to use person_nature instead of person_type
        """
        query = self.db.query(Person).filter(Person.is_active == True)
        
        # Text search filters
        if search_request.name:
            name_filter = or_(
                Person.business_or_surname.ilike(f"%{search_request.name}%"),
                Person.initials.ilike(f"%{search_request.name}%")
            )
            query = query.filter(name_filter)
        
        if search_request.id_number:
            # Join with aliases to search by ID number
            query = query.join(PersonAlias).filter(
                PersonAlias.id_document_number.ilike(f"%{search_request.id_number}%")
            )
        
        if search_request.email:
            query = query.filter(Person.email_address.ilike(f"%{search_request.email}%"))
        
        if search_request.phone:
            phone_filter = or_(
                Person.home_phone_number.ilike(f"%{search_request.phone}%"),
                Person.work_phone_number.ilike(f"%{search_request.phone}%"),
                Person.cell_phone.ilike(f"%{search_request.phone}%")
            )
            query = query.filter(phone_filter)
        
        # Filter by person nature (CORRECTED)
        if search_request.person_nature:
            query = query.filter(Person.person_nature == search_request.person_nature.value)
        
        if search_request.nationality_code:
            query = query.filter(Person.nationality_code == search_request.nationality_code)
        
        if search_request.is_active is not None:
            query = query.filter(Person.is_active == search_request.is_active)
        
        # Get total count before pagination
        total = query.count()
        
        # Sorting
        if search_request.order_by:
            if hasattr(Person, search_request.order_by):
                order_field = getattr(Person, search_request.order_by)
                if search_request.order_direction == "desc":
                    query = query.order_by(desc(order_field))
                else:
                    query = query.order_by(asc(order_field))
        
        # Pagination
        persons = query.offset(search_request.skip).limit(search_request.limit).all()
        
        # Calculate pagination info
        has_next = (search_request.skip + search_request.limit) < total
        has_previous = search_request.skip > 0
        
        return PersonSearchResponse(
            persons=[PersonListResponse.from_orm(p) for p in persons],
            total=total,
            skip=search_request.skip,
            limit=search_request.limit,
            has_next=has_next,
            has_previous=has_previous
        )

    def get_persons_by_ids(self, person_ids: List[str]) -> List[PersonResponse]:
        """Get multiple persons by IDs"""
        persons = self.db.query(Person).options(
            selectinload(Person.natural_person),
            selectinload(Person.aliases),
            selectinload(Person.addresses)
        ).filter(Person.id.in_(person_ids)).all()
        
        return [PersonResponse.from_orm(person) for person in persons]

    # ============================================================================
    # ALIAS MANAGEMENT - CORRECTED validation
    # ============================================================================

    def add_person_alias(self, person_id: str, alias_data: PersonAliasCreate, created_by: str = None) -> PersonAliasResponse:
        """Add new alias to person with validation"""
        person = self.db.query(Person).filter(Person.id == person_id).first()
        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Person with ID {person_id} not found"
            )
        
        try:
            # Validate alias creation
            alias_validation = self._validate_alias_creation(alias_data, person.person_nature)
            if not alias_validation.is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Alias validation failed: {alias_validation.code}: {alias_validation.message}"
                )
            
            # Check for duplicate alias
            existing_alias = self.db.query(PersonAlias).filter(
                and_(
                    PersonAlias.id_document_type_code == alias_data.id_document_type_code.value,
                    PersonAlias.id_document_number == alias_data.id_document_number
                )
            ).first()
            
            if existing_alias:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Alias with this ID type and number already exists"
                )
            
            alias = PersonAlias(
                person_id=person_id,
                id_document_type_code=alias_data.id_document_type_code.value,
                id_document_number=alias_data.id_document_number,
                country_of_issue=alias_data.country_of_issue,
                name_in_document=alias_data.name_in_document,
                alias_status=alias_data.alias_status,
                is_current=alias_data.is_current,
                created_by=created_by
            )
            
            self.db.add(alias)
            self.db.commit()
            
            return PersonAliasResponse.from_orm(alias)
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to add alias for person {person_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add person alias"
            )

    def update_person_alias(self, alias_id: str, alias_data: PersonAliasUpdate, updated_by: str = None) -> PersonAliasResponse:
        """Update person alias"""
        alias = self.db.query(PersonAlias).filter(PersonAlias.id == alias_id).first()
        
        if not alias:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alias with ID {alias_id} not found"
            )
        
        try:
            update_data = alias_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                if field == 'id_document_type_code' and value:
                    setattr(alias, field, value.value)
                elif hasattr(alias, field):
                    setattr(alias, field, value)
            
            alias.updated_at = datetime.utcnow()
            self.db.commit()
            
            return PersonAliasResponse.from_orm(alias)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update alias {alias_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update alias"
            )

    # ============================================================================
    # ADDRESS MANAGEMENT - CORRECTED validation
    # ============================================================================

    def add_person_address(self, person_id: str, address_data: PersonAddressCreate, created_by: str = None) -> PersonAddressResponse:
        """Add new address to person with validation"""
        person = self.db.query(Person).filter(Person.id == person_id).first()
        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Person with ID {person_id} not found"
            )
        
        try:
            # Validate address data
            addr_validation = self.validation_service.validate_address_creation(address_data.dict())
            addr_failed = [r for r in addr_validation if not r.is_valid]
            if addr_failed:
                error_msg = '; '.join([f"{r.code}: {r.message}" for r in addr_failed])
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Address validation failed: {error_msg}"
                )
            
            address = PersonAddress(
                person_id=person_id,
                address_type=address_data.address_type.value,
                is_primary=address_data.is_primary,
                address_line_1=address_data.address_line_1,
                address_line_2=address_data.address_line_2,
                address_line_3=address_data.address_line_3,
                address_line_4=address_data.address_line_4,
                address_line_5=address_data.address_line_5,
                postal_code=address_data.postal_code,
                country_code=address_data.country_code,
                province_code=address_data.province_code,
                suburb_validated=False,
                city_validated=False,
                created_by=created_by,
                updated_by=created_by
            )
            
            self.db.add(address)
            self.db.commit()
            
            return PersonAddressResponse.from_orm(address)
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to add address for person {person_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add person address"
            )

    # ============================================================================
    # VALIDATION AND BUSINESS RULES - CORRECTED implementation
    # ============================================================================

    def validate_person(self, validation_request: PersonValidationRequest) -> PersonValidationResponse:
        """
        Comprehensive person validation implementing all business rules
        Returns validation codes V00001-V00019 applied
        """
        person = self.db.query(Person).options(
            selectinload(Person.natural_person),
            selectinload(Person.aliases),
            selectinload(Person.addresses)
        ).filter(Person.id == validation_request.person_id).first()
        
        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Person with ID {validation_request.person_id} not found"
            )
        
        validation_errors = []
        validation_warnings = []
        validation_codes = []
        
        try:
            # Validate person data
            person_data = {
                'person_nature': person.person_nature,
                'business_or_surname': person.business_or_surname,
                'initials': person.initials,
                'nationality_code': person.nationality_code,
                'preferred_language': person.preferred_language,
                'current_status_alias': person.current_status_alias,
                'is_natural_person': person.person_nature in ['01', '02']
            }
            
            # Add natural person data if applicable
            if person.natural_person:
                person_data.update({
                    'full_name_1': person.natural_person.full_name_1,
                    'birth_date': person.natural_person.birth_date,
                    'preferred_language': person.natural_person.preferred_language_code
                })
            
            # Validate using validation service
            validation_results = self.validation_service.validate_person_creation(person_data)
            
            for result in validation_results:
                validation_codes.append(result.code)
                if not result.is_valid:
                    validation_errors.append(f"{result.code}: {result.message}")
                elif result.message:  # Warnings
                    validation_warnings.append(f"{result.code}: {result.message}")
            
            # Validate aliases
            for alias in person.aliases:
                alias_validation = self._validate_alias_creation(alias, person.person_nature)
                validation_codes.append(alias_validation.code)
                if not alias_validation.is_valid:
                    validation_errors.append(f"Alias {alias.id_document_number}: {alias_validation.message}")
            
            # Validate addresses
            for address in person.addresses:
                addr_validation = self.validation_service.validate_address_creation({
                    'address_type': address.address_type,
                    'address_line_1': address.address_line_1,
                    'postal_code': address.postal_code
                })
                for result in addr_validation:
                    validation_codes.append(result.code)
                    if not result.is_valid:
                        validation_errors.append(f"Address {address.address_type}: {result.message}")
            
            is_valid = len(validation_errors) == 0
            
            return PersonValidationResponse(
                person_id=validation_request.person_id,
                is_valid=is_valid,
                validation_errors=validation_errors,
                validation_warnings=validation_warnings,
                validation_codes=list(set(validation_codes))  # Remove duplicates
            )
            
        except Exception as e:
            logger.error(f"Validation error for person {validation_request.person_id}: {str(e)}")
            return PersonValidationResponse(
                person_id=validation_request.person_id,
                is_valid=False,
                validation_errors=[f"Validation system error: {str(e)}"],
                validation_warnings=[],
                validation_codes=[]
            )

    # ============================================================================
    # STATISTICS AND REPORTING - CORRECTED for person_nature
    # ============================================================================

    def get_person_statistics(self) -> Dict[str, Any]:
        """Get person management statistics"""
        try:
            # Total counts by person nature (CORRECTED)
            person_counts = {}
            for nature in PersonNature:
                count = self.db.query(Person).filter(
                    and_(Person.person_nature == nature.value, Person.is_active == True)
                ).count()
                person_counts[nature.name] = count
            
            # Active vs inactive
            active_count = self.db.query(Person).filter(Person.is_active == True).count()
            inactive_count = self.db.query(Person).filter(Person.is_active == False).count()
            
            # Recent registrations (last 30 days)
            thirty_days_ago = datetime.utcnow().date() - datetime.timedelta(days=30)
            recent_count = self.db.query(Person).filter(
                and_(Person.created_at >= thirty_days_ago, Person.is_active == True)
            ).count()
            
            # Address statistics
            street_addresses = self.db.query(PersonAddress).filter(
                PersonAddress.address_type == 'street'
            ).count()
            postal_addresses = self.db.query(PersonAddress).filter(
                PersonAddress.address_type == 'postal'
            ).count()
            
            # Alias statistics by document type
            alias_counts = {}
            for id_type in IdentificationType:
                count = self.db.query(PersonAlias).filter(
                    PersonAlias.id_document_type_code == id_type.value
                ).count()
                alias_counts[id_type.name] = count
            
            return {
                "person_counts_by_nature": person_counts,
                "total_active": active_count,
                "total_inactive": inactive_count,
                "recent_registrations_30_days": recent_count,
                "address_statistics": {
                    "street_addresses": street_addresses,
                    "postal_addresses": postal_addresses
                },
                "alias_statistics": alias_counts,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating person statistics: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate statistics"
            )

    # ============================================================================
    # BULK OPERATIONS
    # ============================================================================

    def bulk_create_persons(self, bulk_request: PersonBulkCreateRequest, created_by: str = None) -> PersonBulkCreateResponse:
        """Create multiple persons in bulk"""
        created_persons = []
        errors = []
        
        for i, person_data in enumerate(bulk_request.persons):
            try:
                person = self.create_person(person_data, created_by)
                created_persons.append(person)
            except Exception as e:
                errors.append({
                    "index": i,
                    "person_data": person_data.dict(),
                    "error": str(e)
                })
        
        return PersonBulkCreateResponse(
            created_count=len(created_persons),
            failed_count=len(errors),
            created_persons=created_persons,
            errors=errors
        )

    # ============================================================================
    # PRIVATE HELPER METHODS
    # ============================================================================

    def _auto_derive_from_id(self, person_data: PersonCreate) -> Dict[str, Any]:
        """
        Auto-derive data from ID numbers (business rule implementation)
        Implements auto-derivation for RSA ID numbers
        """
        derived_data = {}
        
        if person_data.aliases:
            for alias in person_data.aliases:
                if alias.id_document_type_code == IdentificationType.RSA_ID:
                    # Auto-derive birth date
                    birth_date = self.validation_service.derive_birth_date_from_rsa_id(alias.id_document_number)
                    if birth_date:
                        derived_data['birth_date'] = birth_date
                    
                    # Auto-derive gender (person nature)
                    gender = self.validation_service.derive_gender_from_rsa_id(alias.id_document_number)
                    if gender and not person_data.person_nature:
                        derived_data['person_nature'] = gender
        
        return derived_data

    def _validate_alias_creation(self, alias_data: Union[PersonAliasCreate, PersonAlias], person_nature: str) -> ValidationResult:
        """
        Validate alias creation with business rules
        Implements validation codes and business rules
        """
        # Get values from alias_data
        if isinstance(alias_data, PersonAliasCreate):
            id_type = alias_data.id_document_type_code.value
            id_number = alias_data.id_document_number
            alias_status = alias_data.alias_status
        else:
            id_type = alias_data.id_document_type_code
            id_number = alias_data.id_document_number
            alias_status = alias_data.alias_status
        
        # V00001: Identification Type Mandatory
        validation = self.validation_service.validate_identification_type(id_type)
        if not validation.is_valid:
            return validation
        
        # V00013: Identification Number Mandatory
        validation = self.validation_service.validate_identification_number(id_number, id_type)
        if not validation.is_valid:
            return validation
        
        # V00017: Numeric validation for RSA ID
        validation = self.validation_service.validate_numeric_for_rsa_id(id_number, id_type)
        if not validation.is_valid:
            return validation
        
        # V00018: ID Number length validation
        validation = self.validation_service.validate_id_number_length(id_number, id_type)
        if not validation.is_valid:
            return validation
        
        # V00019: Check digit validation
        validation = self.validation_service.validate_check_digit(id_number, id_type)
        if not validation.is_valid:
            return validation
        
        # V00016: Unacceptable alias check
        validation = self.validation_service.validate_unacceptable_alias(id_type, alias_status)
        if not validation.is_valid:
            return validation
        
        # V00485: Natural person check (Transaction 57)
        if person_nature in ['01', '02']:  # Natural persons
            # V00012: Only RSA ID (02) and Foreign ID (03) allowed for Transaction 57
            if id_type not in ['02', '03']:
                return ValidationResult(
                    is_valid=False,
                    code="V00012",
                    message="V00012: Only RSA ID (02) and Foreign ID (03) allowed for person introduction",
                    field="id_document_type_code"
                )
        
        return ValidationResult(is_valid=True) 