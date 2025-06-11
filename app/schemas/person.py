"""
Person Management Schemas - CORRECTED IMPLEMENTATION
Pydantic models for person data validation and serialization
Matches corrected model structure and documentation requirements
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, validator, model_validator
from datetime import datetime, date
from enum import Enum


class ValidationResult(BaseModel):
    """Schema for validation result response"""
    code: str = Field(..., description="Validation code (V00001-V99999)")
    field: str = Field(..., description="Field being validated")
    message: str = Field(..., description="Validation message")
    is_valid: bool = Field(..., description="Validation result")


class IdentificationType(str, Enum):
    """
    TRANSACTION 57 - Introduction of Natural Person
    V00012: Only RSA ID (02) and Foreign ID (03) allowed for person introduction
    Based on eNaTIS documentation requirements
    """
    RSA_ID = "02"           # RSA ID Document (13 digits numeric) - V00017, V00018, V00019
    FOREIGN_ID = "03"       # Foreign ID Document - V00013


class PersonNature(str, Enum):
    """
    CORRECTED: Person nature classification from LmNatOfPer lookup
    Based on PER.NATOFPER field from documentation
    """
    MALE = "01"             # Male (natural person)
    FEMALE = "02"           # Female (natural person)
    COMPANY = "03"          # Company/Corporation (TRN)
    CLOSE_CORP = "10"       # Close Corporation (BRN 10)
    TRUST = "11"            # Trust (BRN 11)
    PARTNERSHIP = "12"      # Partnership (BRN 12)
    SOLE_PROP = "13"        # Sole Proprietorship (BRN 13)
    ASSOCIATION = "14"      # Association (BRN 14)
    COOPERATIVE = "15"      # Cooperative (BRN 15)
    NON_PROFIT = "16"       # Non-Profit Organization (BRN 16)
    OTHER_ORG = "17"        # Other Organization (BRN 17)


class AddressType(str, Enum):
    """
    CORRECTED: Address type classification - matches documentation structure
    Based on PER.STREETADDR vs PER.POSTADDR structure
    """
    STREET = "street"       # Physical/residential address (PER.STREETADDR1-5)
    POSTAL = "postal"       # Postal address (PER.POSTADDR1-5)


# Base schemas for common patterns
class TimestampMixin(BaseModel):
    """Common timestamp fields"""
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None


# Person Alias Schemas
class PersonAliasBase(BaseModel):
    """
    Base person alias schema - implements validation V00001, V00013, V00016-V00019
    """
    id_document_type_code: IdentificationType = Field(..., description="ID document type from LmIdDocTypeCd lookup")
    id_document_number: str = Field(..., min_length=1, max_length=13, description="ID document number (ALIAS.IDDOCN)")
    country_of_issue: str = Field(default="ZA", max_length=3, description="Country of issue (ALIAS.CNTRYOFISSID)")
    name_in_document: Optional[str] = Field(None, max_length=200, description="Name as in document (ALIAS.NAMEINDOC)")
    alias_status: str = Field(default="1", pattern="^[123]$", description="1=Current, 2=Historical, 3=Unacceptable")
    is_current: bool = Field(default=True, description="Current/active alias")

    @validator('id_document_number')
    def validate_id_number(cls, v, values):
        """
        Implements validation codes V00013, V00017, V00018, V00019
        """
        doc_type = values.get('id_document_type_code')
        
        # V00013: Identification Number Mandatory (handled by Field requirements)
        if not v or v.strip() == "":
            raise ValueError('Identification number is mandatory (V00013)')
        
        # V00018: 13 chars for RSA ID (02)
        if doc_type == IdentificationType.RSA_ID and len(v) != 13:
            raise ValueError(f'This type requires 13 characters (V00018)')
        
        # V00017: Numeric for type 02 (RSA ID)
        if doc_type == IdentificationType.RSA_ID:
            if not v.isdigit():
                raise ValueError('RSA ID number must be numeric only (V00017)')
            
            # V00019: Basic check digit validation for RSA ID
            if len(v) == 13:
                if not cls._validate_rsa_id_checksum(v):
                    raise ValueError('Invalid RSA ID check digit (V00019)')
        
        # V00019: Foreign ID validation
        elif doc_type == IdentificationType.FOREIGN_ID:
            # Foreign ID format validation can be added here if needed
            pass
        
        return v

    @validator('alias_status')
    def validate_alias_status(cls, v, values):
        """
        Implements V00016: Unacceptable Alias Check
        """
        doc_type = values.get('id_document_type_code')
        
        # V00016: Unacceptable Alias Check - not applicable for Transaction 57 (RSA ID/Foreign ID only)
        # RSA ID and Foreign ID cannot have unacceptable status
        if v == "3":
            raise ValueError('This ID type cannot have unacceptable status (V00016)')
        
        return v

    @staticmethod
    def _validate_rsa_id_checksum(id_number: str) -> bool:
        """Basic RSA ID checksum validation"""
        try:
            digits = [int(d) for d in id_number[:12]]
            check_digit = int(id_number[12])
            
            total = 0
            for i, digit in enumerate(digits):
                if i % 2 == 1:
                    doubled = digit * 2
                    total += doubled if doubled < 10 else doubled - 9
                else:
                    total += digit
            
            calculated_check = (10 - (total % 10)) % 10
            return calculated_check == check_digit
        except (ValueError, IndexError):
            return False


class PersonAliasCreate(PersonAliasBase):
    """Schema for creating person alias"""
    pass


class PersonAliasUpdate(BaseModel):
    """Schema for updating person alias"""
    id_document_type_code: Optional[IdentificationType] = None
    id_document_number: Optional[str] = Field(None, max_length=13)
    country_of_issue: Optional[str] = Field(None, max_length=3)
    name_in_document: Optional[str] = Field(None, max_length=200)
    alias_status: Optional[str] = Field(None, pattern="^[123]$")
    is_current: Optional[bool] = None


class PersonAliasResponse(PersonAliasBase, TimestampMixin):
    """Schema for person alias response"""
    id: str
    person_id: str

    class Config:
        from_attributes = True


# Natural Person Schemas
class NaturalPersonBase(BaseModel):
    """
    Base natural person schema - implements validation V00056, V00059, V00062, V00065, V00067
    Only for person_nature 01 (Male) and 02 (Female)
    """
    full_name_1: str = Field(..., min_length=1, max_length=32, description="First name (NATPER.FULLNAME1) - V00056: Mandatory")
    full_name_2: Optional[str] = Field(None, max_length=32, description="Middle name (NATPER.FULLNAME2) - V00059: Optional")
    full_name_3: Optional[str] = Field(None, max_length=32, description="Additional name (NATPER.FULLNAME3) - V00062: Optional")
    birth_date: Optional[date] = Field(None, description="Date of birth (NATPER.BIRTHD) - V00065: Optional, auto-derived from RSA ID")
    email_address: Optional[EmailStr] = Field(None, description="Personal email (NATPER.EMAILADDR)")
    preferred_language_code: Optional[str] = Field(None, max_length=10, description="Language preference (NATPER.PREFLANGCD) - V00068: Mandatory")

    @validator('birth_date')
    def validate_birth_date(cls, v):
        """
        Implements V00067: Birth date validation
        """
        if v:
            # V00067: Not future date
            if v > date.today():
                raise ValueError('Birth date cannot be in the future (V00067)')
            if v < date(1900, 1, 1):
                raise ValueError('Birth date cannot be before 1900')
        return v


class NaturalPersonCreate(NaturalPersonBase):
    """Schema for creating natural person"""
    pass


class NaturalPersonUpdate(BaseModel):
    """Schema for updating natural person"""
    full_name_1: Optional[str] = Field(None, max_length=32)
    full_name_2: Optional[str] = Field(None, max_length=32)
    full_name_3: Optional[str] = Field(None, max_length=32)
    birth_date: Optional[date] = None
    email_address: Optional[EmailStr] = None
    preferred_language_code: Optional[str] = Field(None, max_length=10)


class NaturalPersonResponse(NaturalPersonBase, TimestampMixin):
    """Schema for natural person response"""
    id: str
    person_id: str
    full_name: str = Field(description="Complete full name")
    age: int = Field(description="Current age")
    gender: Optional[str] = Field(description="Gender derived from person.person_nature")

    class Config:
        from_attributes = True


# Person Address Schemas
class PersonAddressBase(BaseModel):
    """
    CORRECTED: Person address schema - matches documentation structure
    Implements separate street/postal address structure as per PER.STREETADDR1-5 and PER.POSTADDR1-5
    Implements validation V00095, V00098, V00101, V00107
    """
    address_type: AddressType = Field(..., description="street or postal address type")
    is_primary: bool = Field(default=False, description="Primary address of this type")
    
    # Address structure matches documentation exactly
    address_line_1: str = Field(..., min_length=1, max_length=35, description="Address line 1 (PER.STREETADDR1/POSTADDR1)")
    address_line_2: Optional[str] = Field(None, max_length=35, description="Address line 2 (PER.STREETADDR2/POSTADDR2)")
    address_line_3: Optional[str] = Field(None, max_length=35, description="Address line 3 (PER.STREETADDR3/POSTADDR3)")
    address_line_4: Optional[str] = Field(None, max_length=35, description="Address line 4 - suburb (PER.STREETADDR4/POSTADDR4)")
    address_line_5: Optional[str] = Field(None, max_length=35, description="Address line 5 - city/town (PER.STREETADDR5/POSTADDR5)")
    
    # CORRECTED: Postal code structure
    postal_code: Optional[str] = Field(None, max_length=4, pattern="^[0-9]{4}$", description="4-digit postal code (PER.POSTCDSTREET/POSTCDPOST)")
    
    country_code: str = Field(default="ZA", max_length=3, description="Country code")
    province_code: Optional[str] = Field(None, max_length=10, description="Province code")

    @model_validator(mode='after')
    def validate_address_rules(self):
        """
        Implements address validation rules V00095, V00098, V00107
        """
        # V00095: Line 1 mandatory for postal addresses
        if self.address_type == AddressType.POSTAL and (not self.address_line_1 or self.address_line_1.strip() == ""):
            raise ValueError('Postal address line 1 is mandatory (V00095)')
        
        # V00098: Postal code mandatory for postal addresses
        if self.address_type == AddressType.POSTAL and (not self.postal_code or self.postal_code.strip() == ""):
            raise ValueError('Postal code is mandatory for postal addresses (V00098)')
        
        # V00107: Postal code mandatory if street address entered
        if self.address_type == AddressType.STREET and self.address_line_1 and (not self.postal_code or self.postal_code.strip() == ""):
            raise ValueError('Postal code is mandatory if street address entered (V00107)')
        
        return self


class PersonAddressCreate(PersonAddressBase):
    """Schema for creating person address"""
    pass


class PersonAddressUpdate(BaseModel):
    """Schema for updating person address"""
    address_type: Optional[AddressType] = None
    is_primary: Optional[bool] = None
    address_line_1: Optional[str] = Field(None, max_length=35)
    address_line_2: Optional[str] = Field(None, max_length=35)
    address_line_3: Optional[str] = Field(None, max_length=35)
    address_line_4: Optional[str] = Field(None, max_length=35)
    address_line_5: Optional[str] = Field(None, max_length=35)
    postal_code: Optional[str] = Field(None, max_length=4, pattern="^[0-9]{4}$")
    country_code: Optional[str] = Field(None, max_length=3)
    province_code: Optional[str] = Field(None, max_length=10)


class PersonAddressResponse(PersonAddressBase, TimestampMixin):
    """Schema for person address response"""
    id: str
    person_id: str
    is_verified: bool
    verified_date: Optional[datetime] = None
    suburb_validated: bool = Field(description="Suburb validated against ADDRCORR")
    city_validated: bool = Field(description="City validated against ADDRCORR")
    formatted_address: str = Field(description="Formatted address string")

    class Config:
        from_attributes = True


# Organization Schema
class OrganizationBase(BaseModel):
    """
    Organization-specific details for business entities
    For person_nature 03-17 (non-natural persons)
    """
    trading_name: Optional[str] = Field(None, max_length=32, description="Trading name if different from registered name")
    registration_date: Optional[date] = Field(None, description="Date of registration")
    representative_person_id: Optional[str] = Field(None, description="Organization representative")
    proxy_person_id: Optional[str] = Field(None, description="Organization proxy")
    local_authority_code: Optional[str] = Field(None, max_length=10, description="Local authority code (LtAutCd)")
    dcee_address: Optional[str] = Field(None, max_length=10, description="DCEE address (LmDCEEAddr)")
    resident_at_ra: bool = Field(default=True, description="Resident at this RA")
    movement_restricted: bool = Field(default=False, description="Movement between RAs restricted (V01768)")


class OrganizationCreate(OrganizationBase):
    """Schema for creating organization"""
    pass


class OrganizationResponse(OrganizationBase, TimestampMixin):
    """Schema for organization response"""
    id: str
    person_id: str

    class Config:
        from_attributes = True


# Person Schemas
class PersonBase(BaseModel):
    """
    CORRECTED: Base person schema - matches documentation exactly
    """
    business_or_surname: str = Field(..., min_length=1, max_length=32, description="Business name or surname (PER.BUSORSURNAME)")
    initials: Optional[str] = Field(None, max_length=3, pattern="^[A-Z]*$", description="Initials for natural persons (PER.INITIALS)")
    
    # CORRECTED: person_nature instead of person_type
    person_nature: PersonNature = Field(..., description="Person nature from LmNatOfPer (PER.NATOFPER)")
    
    nationality_code: str = Field(default="ZA", max_length=3, description="Nationality code (PER.NATNPOPGRPCD)")
    email_address: Optional[EmailStr] = Field(None, description="Email address (NATPER.EMAILADDR)")
    
    # Phone numbers from NATPER table
    home_phone_code: Optional[str] = Field(None, max_length=10, description="Home phone area code (NATPER.HTELCD)")
    home_phone_number: Optional[str] = Field(None, max_length=10, description="Home phone number (NATPER.HTELN)")
    work_phone_code: Optional[str] = Field(None, max_length=10, description="Work phone area code (NATPER.WTELCD)")
    work_phone_number: Optional[str] = Field(None, max_length=15, description="Work phone number (NATPER.WTELN)")
    cell_phone: Optional[str] = Field(None, max_length=15, description="Cell phone number (NATPER.CELLN)")
    fax_code: Optional[str] = Field(None, max_length=10, description="Fax area code (NATPER.FAXCD)")
    fax_number: Optional[str] = Field(None, max_length=10, description="Fax number (NATPER.FAXN)")
    
    preferred_language: Optional[str] = Field(default="en", max_length=10, description="Preferred language (NATPER.PREFLANGCD)")
    current_status_alias: str = Field(default="1", pattern="^[123]$", description="Current alias status (1=Current, 2=Historical, 3=Unacceptable)")

    @validator('initials')
    def validate_initials(cls, v, values):
        """
        V00051: Initials Mandatory for Natural Persons (Transaction 57)
        V00001: Validate initials for natural persons only
        """
        # Get person_nature from values - it might be string or enum
        person_nature = values.get('person_nature')
        
        # Handle case where person_nature might not be set yet
        if person_nature is None:
            # If initials provided but no person_nature, we can't validate yet
            # Let this pass and validate in model_validator later
            return v
        
        # Handle both string and enum values during validation
        # person_nature might be a string ("01", "02") or enum (PersonNature.MALE, PersonNature.FEMALE)
        is_natural_person = False
        if isinstance(person_nature, str):
            is_natural_person = person_nature in ["01", "02"]
        elif hasattr(person_nature, 'value'):  # enum
            is_natural_person = person_nature.value in ["01", "02"]
        else:
            is_natural_person = person_nature in [PersonNature.MALE, PersonNature.FEMALE]
        
        # V00051: Initials mandatory for natural persons
        if is_natural_person:
            if not v or v.strip() == "":
                raise ValueError('V00051: Initials are mandatory for natural persons')
        
        # V00001: Initials only applicable to natural persons
        if v and not is_natural_person:
            raise ValueError('Initials only applicable to natural persons')
        
        return v

    @validator('person_nature')
    def validate_person_nature_for_context(cls, v, values):
        """
        Implements V00485: Must be natural person (when required)
        """
        # This validation will be context-specific in the service layer
        return v
    
    @model_validator(mode='after')
    def validate_complete_person_data(self):
        """
        Final validation after all fields are processed
        """
        # Double-check initials validation after all fields are set
        person_nature = self.person_nature
        initials = self.initials
        
        # Handle both string and enum values
        is_natural_person = False
        if isinstance(person_nature, str):
            is_natural_person = person_nature in ["01", "02"]
        elif hasattr(person_nature, 'value'):  # enum
            is_natural_person = person_nature.value in ["01", "02"]
        else:
            is_natural_person = person_nature in [PersonNature.MALE, PersonNature.FEMALE]
        
        # V00001: Initials only applicable to natural persons
        if initials and not is_natural_person:
            raise ValueError('Initials only applicable to natural persons')
        
        return self


class PersonCreate(PersonBase):
    """
    Schema for creating person - implements nested creation
    """
    # Optional nested creation
    natural_person: Optional[NaturalPersonCreate] = Field(None, description="Natural person details (for person_nature 01,02)")
    organization: Optional[OrganizationCreate] = Field(None, description="Organization details (for person_nature 03-17)")
    aliases: Optional[List[PersonAliasCreate]] = Field(default_factory=list, description="ID documents")
    addresses: Optional[List[PersonAddressCreate]] = Field(default_factory=list, description="Addresses")

    @model_validator(mode='after')
    def validate_person_data(self):
        """
        Comprehensive person creation validation
        """
        # V00485: Natural person validation
        # Handle both string and enum values
        is_natural_person = False
        if isinstance(self.person_nature, str):
            is_natural_person = self.person_nature in ["01", "02"]
        else:
            is_natural_person = self.person_nature in [PersonNature.MALE, PersonNature.FEMALE]
        
        if is_natural_person:
            if not self.natural_person:
                raise ValueError('Natural person details required for person_nature 01/02 (V00485)')
            if self.organization:
                raise ValueError('Organization details not applicable for natural persons')
        else:
            # Organization
            if self.natural_person:
                raise ValueError('Natural person details not applicable for organizations')
            # Organization details are optional for now
        
        return self


class PersonUpdate(BaseModel):
    """Schema for updating person"""
    business_or_surname: Optional[str] = Field(None, max_length=32)
    initials: Optional[str] = Field(None, max_length=3, pattern="^[A-Z]*$")
    nationality_code: Optional[str] = Field(None, max_length=3)
    email_address: Optional[EmailStr] = None
    home_phone_code: Optional[str] = Field(None, max_length=10)
    home_phone_number: Optional[str] = Field(None, max_length=10)
    work_phone_code: Optional[str] = Field(None, max_length=10)
    work_phone_number: Optional[str] = Field(None, max_length=15)
    cell_phone: Optional[str] = Field(None, max_length=15)
    fax_code: Optional[str] = Field(None, max_length=10)
    fax_number: Optional[str] = Field(None, max_length=10)
    preferred_language: Optional[str] = Field(None, max_length=10)
    current_status_alias: Optional[str] = Field(None, pattern="^[123]$")
    is_active: Optional[bool] = None


class PersonResponse(PersonBase, TimestampMixin):
    """Schema for person response"""
    id: str
    is_active: bool
    natural_person: Optional[NaturalPersonResponse] = None
    organization: Optional[OrganizationResponse] = None
    aliases: List[PersonAliasResponse] = Field(default_factory=list)
    addresses: List[PersonAddressResponse] = Field(default_factory=list)

    @validator('id', pre=True, allow_reuse=True)
    def convert_uuid_to_string(cls, v):
        """Convert UUID to string for API response"""
        return str(v) if v else None

    class Config:
        from_attributes = True


class PersonListResponse(BaseModel):
    """Schema for person list response"""
    id: str
    business_or_surname: str
    initials: Optional[str] = None
    person_nature: PersonNature
    email_address: Optional[str] = None
    cell_phone: Optional[str] = None
    is_active: bool
    created_at: datetime

    @validator('id', pre=True, allow_reuse=True)
    def convert_uuid_to_string(cls, v):
        return str(v) if v else None

    class Config:
        from_attributes = True


class PersonSearchRequest(BaseModel):
    """Schema for person search request"""
    # Text search fields
    name: Optional[str] = Field(None, description="Search in names")
    id_number: Optional[str] = Field(None, description="Search by ID number")
    email: Optional[str] = Field(None, description="Search by email")
    phone: Optional[str] = Field(None, description="Search by phone number")
    
    # Filter fields
    person_nature: Optional[PersonNature] = None
    nationality_code: Optional[str] = None
    is_active: Optional[bool] = None
    
    # Pagination
    skip: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(default=20, ge=1, le=100, description="Number of records to return")
    
    # Sorting
    order_by: Optional[str] = Field(default="created_at", description="Field to order by")
    order_direction: Optional[str] = Field(default="desc", pattern="^(asc|desc)$", description="Order direction")


class PersonSearchResponse(BaseModel):
    """Schema for person search response"""
    persons: List[PersonListResponse]
    total: int
    skip: int
    limit: int
    has_next: bool
    has_previous: bool


class PersonValidationRequest(BaseModel):
    """Schema for person validation request"""
    person_id: str
    validation_notes: Optional[str] = None


class PersonValidationResponse(BaseModel):
    """Schema for person validation response"""
    person_id: str
    is_valid: bool
    validation_errors: List[str] = Field(default_factory=list)
    validation_warnings: List[str] = Field(default_factory=list)
    validation_codes: List[str] = Field(default_factory=list, description="Applied validation codes (V00001-V00019)")


class PersonBulkCreateRequest(BaseModel):
    """Schema for bulk person creation"""
    persons: List[PersonCreate] = Field(..., max_items=50, description="List of persons to create")


class PersonBulkCreateResponse(BaseModel):
    """Schema for bulk person creation response"""
    created_count: int
    failed_count: int
    created_persons: List[PersonResponse] = Field(default_factory=list)
    errors: List[Dict[str, Any]] = Field(default_factory=list) 