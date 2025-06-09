"""
Person Management Schemas
Pydantic models for person registration, search, and management
Reference: Section 1.1 Person Registration/Search Screen
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


class IdentificationTypeEnum(str, Enum):
    """Valid identification document types"""
    RSA_ID = "01"
    PASSPORT = "02"
    TEMPORARY_ID = "03"
    ASYLUM_DOCUMENT = "04"
    BIRTH_CERTIFICATE = "97"


class GenderEnum(str, Enum):
    """Gender options for natural persons"""
    MALE = "01"
    FEMALE = "02"


class NationalityEnum(str, Enum):
    """Nationality codes"""
    SOUTH_AFRICAN = "01"
    FOREIGN = "02"


class PersonSearchRequest(BaseModel):
    """Search request for finding persons"""
    identification_type: Optional[IdentificationTypeEnum] = None
    identification_number: Optional[str] = None
    first_name: Optional[str] = None
    surname: Optional[str] = None
    date_of_birth: Optional[date] = None
    
    @validator('identification_number')
    def validate_id_number(cls, v, values):
        """Validate identification number based on type"""
        if v and 'identification_type' in values:
            id_type = values['identification_type']
            if id_type in ['01', '02', '04', '97'] and len(v) != 13:
                raise ValueError('Identification number must be 13 characters for this type')
            if id_type == '02' and not v.isdigit():
                raise ValueError('RSA ID number must be numeric')
        return v


class PersonCreateRequest(BaseModel):
    """Request model for creating a new person"""
    # Core Identity Fields (V00001-V00019)
    identification_type: IdentificationTypeEnum = Field(..., description="Identification document type (V00001)")
    identification_number: str = Field(..., min_length=1, max_length=13, description="Identification number (V00013)")
    first_name: str = Field(..., min_length=1, max_length=32, description="First name")
    middle_name: Optional[str] = Field(None, max_length=32, description="Middle name")
    surname: str = Field(..., min_length=1, max_length=32, description="Surname")
    initials: Optional[str] = Field(None, max_length=3, description="Initials")
    date_of_birth: date = Field(..., description="Date of birth")
    gender: GenderEnum = Field(..., description="Gender (V00485)")
    nationality: NationalityEnum = Field(..., description="Nationality")
    language_preference: Optional[str] = Field(None, description="Preferred language code")
    
    # Contact Information
    email_address: Optional[EmailStr] = Field(None, description="Email address")
    home_phone_code: Optional[str] = Field(None, max_length=10, description="Home phone area code")
    home_phone_number: Optional[str] = Field(None, max_length=10, description="Home phone number")
    work_phone_code: Optional[str] = Field(None, max_length=10, description="Work phone area code")
    work_phone_number: Optional[str] = Field(None, max_length=15, description="Work phone number")
    cell_phone: Optional[str] = Field(None, max_length=15, description="Cell phone number")
    fax_code: Optional[str] = Field(None, max_length=10, description="Fax area code")
    fax_number: Optional[str] = Field(None, max_length=10, description="Fax number")
    
    @validator('identification_number')
    def validate_identification_number(cls, v, values):
        """Implements V00013, V00017, V00018, V00019"""
        if not v:
            raise ValueError('Identification number is mandatory (V00013)')
        
        if 'identification_type' in values:
            id_type = values['identification_type']
            
            # V00018: 13 characters for specific types
            if id_type in ['01', '02', '04', '97'] and len(v) != 13:
                raise ValueError('Identification number must be 13 characters (V00018)')
            
            # V00017: Numeric validation for RSA ID
            if id_type == '02' and not v.isdigit():
                raise ValueError('RSA ID number must be numeric (V00017)')
        
        return v
    
    @validator('date_of_birth')
    def validate_birth_date(cls, v):
        """Validate birth date is not in future"""
        if v > date.today():
            raise ValueError('Birth date cannot be in the future')
        return v
    
    @validator('home_phone_code', 'home_phone_number', 'work_phone_code', 'work_phone_number', 'cell_phone', 'fax_code', 'fax_number')
    def validate_phone_numbers(cls, v):
        """Validate phone numbers are numeric"""
        if v and not v.isdigit():
            raise ValueError('Phone numbers must be numeric')
        return v


class AddressRequest(BaseModel):
    """Address information for persons"""
    address_type: str = Field(..., description="'residential' or 'postal'")
    street_address_line_1: str = Field(..., max_length=35, description="Street address line 1")
    street_address_line_2: Optional[str] = Field(None, max_length=35, description="Street address line 2")
    street_address_line_3: Optional[str] = Field(None, max_length=35, description="Street address line 3")
    street_address_line_4: Optional[str] = Field(None, max_length=35, description="Street address line 4")
    street_address_line_5: Optional[str] = Field(None, max_length=35, description="Street address line 5")
    street_postal_code: str = Field(..., min_length=4, max_length=4, description="4-digit postal code")
    postal_address_line_1: Optional[str] = Field(None, max_length=35, description="Postal address line 1")
    postal_address_line_2: Optional[str] = Field(None, max_length=35, description="Postal address line 2")
    postal_address_line_3: Optional[str] = Field(None, max_length=35, description="Postal address line 3")
    postal_address_line_4: Optional[str] = Field(None, max_length=35, description="Postal address line 4")
    postal_address_line_5: Optional[str] = Field(None, max_length=35, description="Postal address line 5")
    postal_code: Optional[str] = Field(None, min_length=4, max_length=4, description="Postal code")
    country: str = Field(..., description="Country code")
    province: str = Field(..., description="Province/state")
    city: str = Field(..., max_length=50, description="City name")
    
    @validator('street_postal_code', 'postal_code')
    def validate_postal_codes(cls, v):
        """Validate postal codes are 4-digit numeric"""
        if v and (not v.isdigit() or len(v) != 4):
            raise ValueError('Postal code must be 4-digit numeric')
        return v


class PersonResponse(BaseModel):
    """Response model for person information"""
    id: str = Field(..., description="Person UUID")
    identification_type: str
    identification_number: str
    first_name: str
    middle_name: Optional[str]
    surname: str
    initials: Optional[str]
    date_of_birth: date
    gender: str
    nationality: str
    language_preference: Optional[str]
    email_address: Optional[str]
    home_phone_code: Optional[str]
    home_phone_number: Optional[str]
    work_phone_code: Optional[str]
    work_phone_number: Optional[str]
    cell_phone: Optional[str]
    fax_code: Optional[str]
    fax_number: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PersonListResponse(BaseModel):
    """Response model for person search results"""
    persons: List[PersonResponse]
    total_count: int
    page: int = 1
    page_size: int = 20


class ValidationResult(BaseModel):
    """Validation result for business rules"""
    is_valid: bool
    code: str
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_valid": False,
                "code": "V00001",
                "message": "Identification type is mandatory"
            }
        }


class PersonValidationResponse(BaseModel):
    """Response for person validation"""
    person_id: Optional[str]
    validation_results: List[ValidationResult]
    is_valid: bool
    
    @validator('is_valid', always=True)
    def check_overall_validity(cls, v, values):
        """Check if all validations passed"""
        if 'validation_results' in values:
            return all(result.is_valid for result in values['validation_results'])
        return v 