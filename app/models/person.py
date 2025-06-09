"""
Person Database Model
Implements Person entity from Section 1.1 Person Registration/Search Screen
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, Text, Boolean, Index, CheckConstraint, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from typing import Optional
import uuid
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from enum import Enum as PythonEnum

from app.models.base import BaseModel
from app.models.enums import ValidationStatus, Gender, AddressType

Base = declarative_base()

class Person(Base):
    """
    Person entity representing individuals in the system.
    
    Uses hybrid approach based on refactored documentation analysis:
    - Universal fields (gender, validation status, address types) use enums
    - Country-specific fields (ID types, nationalities, languages) use strings with country config validation
    """
    __tablename__ = "persons"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    
    # Identity Information - Country-specific (strings with config validation)
    # Based on Screen Field Specifications: ID types vary significantly by country
    id_type = Column(String(10), nullable=False, comment="Country-specific ID document type (RSA_ID, NATIONAL_ID, etc.)")
    id_number = Column(String(50), nullable=False, unique=True, comment="ID document number with country-specific validation")
    
    # Personal Information
    # Universal fields use enums for consistency
    first_name = Column(String(100), nullable=False, comment="Given name(s)")
    middle_name = Column(String(100), nullable=True, comment="Middle name(s)")
    surname = Column(String(100), nullable=False, comment="Family name/surname")
    initials = Column(String(10), nullable=True, comment="Name initials")
    
    # Date of birth for age calculations and eligibility
    date_of_birth = Column(Date, nullable=True, comment="Birth date for age verification")
    
    # Universal gender codes (consistent across countries)
    gender = Column(Enum(Gender), nullable=False, comment="Gender using universal codes")
    
    # Country-specific fields (strings with config validation)
    # Based on documentation: these vary significantly by country
    nationality = Column(String(10), nullable=True, comment="Country-specific nationality code")
    language_preference = Column(String(10), nullable=True, comment="Country-specific language code")
    
    # Contact Information
    email = Column(String(255), nullable=True, comment="Email address")
    phone_home = Column(String(20), nullable=True, comment="Home phone number")
    phone_work = Column(String(20), nullable=True, comment="Work phone number")
    phone_mobile = Column(String(20), nullable=True, comment="Mobile phone number")
    fax = Column(String(20), nullable=True, comment="Fax number")
    
    # Address Information
    # Universal address types with country-specific address formats
    residential_address_line_1 = Column(String(100), nullable=True)
    residential_address_line_2 = Column(String(100), nullable=True)
    residential_address_line_3 = Column(String(100), nullable=True)
    residential_address_line_4 = Column(String(100), nullable=True)
    residential_address_line_5 = Column(String(100), nullable=True)
    residential_postal_code = Column(String(10), nullable=True)
    residential_city = Column(String(100), nullable=True)
    residential_province = Column(String(100), nullable=True)
    residential_country = Column(String(100), nullable=True)
    
    postal_address_line_1 = Column(String(100), nullable=True)
    postal_address_line_2 = Column(String(100), nullable=True)
    postal_address_line_3 = Column(String(100), nullable=True)
    postal_address_line_4 = Column(String(100), nullable=True)
    postal_address_line_5 = Column(String(100), nullable=True)
    postal_postal_code = Column(String(10), nullable=True)
    postal_city = Column(String(100), nullable=True)
    postal_province = Column(String(100), nullable=True)
    postal_country = Column(String(100), nullable=True)
    
    # System Status and Validation
    # Universal validation status using enum
    validation_status = Column(Enum(ValidationStatus), nullable=False, default=ValidationStatus.PENDING, 
                             comment="Person validation status")
    validation_date = Column(DateTime, nullable=True, comment="Date when validation was completed")
    validation_notes = Column(Text, nullable=True, comment="Validation notes and comments")
    
    # Administrative flags
    is_active = Column(Boolean, nullable=False, default=True, comment="Active status flag")
    has_restrictions = Column(Boolean, nullable=False, default=False, comment="Administrative restrictions flag")
    restriction_notes = Column(Text, nullable=True, comment="Details of any restrictions")
    
    # Country and Jurisdiction
    # Based on single-country deployment model
    country_code = Column(String(3), nullable=False, comment="ISO country code for this deployment")
    jurisdiction = Column(String(100), nullable=True, comment="Local jurisdiction/authority")
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="Record creation timestamp")
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment="Last update timestamp")
    created_by = Column(String(100), nullable=True, comment="User who created the record")
    updated_by = Column(String(100), nullable=True, comment="User who last updated the record")
    
    # Legacy integration fields (for transition period)
    legacy_id = Column(String(50), nullable=True, comment="Legacy system ID for migration")
    legacy_system = Column(String(50), nullable=True, comment="Source legacy system identifier")
    
    def __repr__(self):
        return f"<Person(id={self.id}, id_number='{self.id_number}', name='{self.first_name} {self.surname}', status='{self.validation_status}')>"
    
    @property
    def full_name(self) -> str:
        """Get formatted full name"""
        parts = [self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        parts.append(self.surname)
        return " ".join(parts)
    
    @property
    def display_name(self) -> str:
        """Get display name (surname, initials)"""
        if self.initials:
            return f"{self.surname}, {self.initials}"
        return f"{self.surname}, {self.first_name[0] if self.first_name else ''}"
    
    @property
    def has_valid_residential_address(self) -> bool:
        """Check if residential address is complete"""
        return bool(
            self.residential_address_line_1 
            and self.residential_postal_code 
            and self.residential_city
        )
    
    @property
    def has_valid_postal_address(self) -> bool:
        """Check if postal address is complete"""
        return bool(
            self.postal_address_line_1 
            and self.postal_postal_code
        )
    
    def get_primary_address(self) -> dict:
        """Get primary address for correspondence"""
        if self.has_valid_postal_address:
            return {
                "type": "postal",
                "line_1": self.postal_address_line_1,
                "line_2": self.postal_address_line_2,
                "line_3": self.postal_address_line_3,
                "line_4": self.postal_address_line_4,
                "line_5": self.postal_address_line_5,
                "postal_code": self.postal_postal_code,
                "city": self.postal_city,
                "province": self.postal_province,
                "country": self.postal_country,
            }
        elif self.has_valid_residential_address:
            return {
                "type": "residential",
                "line_1": self.residential_address_line_1,
                "line_2": self.residential_address_line_2,
                "line_3": self.residential_address_line_3,
                "line_4": self.residential_address_line_4,
                "line_5": self.residential_address_line_5,
                "postal_code": self.residential_postal_code,
                "city": self.residential_city,
                "province": self.residential_province,
                "country": self.residential_country,
            }
        return None


class PersonAddress(BaseModel):
    """
    Person address model
    
    Implements address entity from Section 1.2 Address Management Screen
    Source: Section 1.2 Address Management Screen
    Legacy References: PER address fields
    """
    
    # Foreign key to person
    person_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Address type
    address_type = Column(Enum(AddressType), nullable=False)
    
    # Street address fields
    street_address_line_1 = Column(String(35), nullable=True)  # PER.STREETADDR1
    street_address_line_2 = Column(String(35), nullable=True)  # PER.STREETADDR2
    street_address_line_3 = Column(String(35), nullable=True)  # PER.STREETADDR3
    street_address_line_4 = Column(String(35), nullable=True)  # PER.STREETADDR4
    street_address_line_5 = Column(String(35), nullable=True)  # PER.STREETADDR5
    street_postal_code = Column(String(4), nullable=True)  # PER.POSTCDSTREET
    
    # Postal address fields
    postal_address_line_1 = Column(String(35), nullable=True)  # PER.POSTADDR1
    postal_address_line_2 = Column(String(35), nullable=True)  # PER.POSTADDR2
    postal_address_line_3 = Column(String(35), nullable=True)  # PER.POSTADDR3
    postal_address_line_4 = Column(String(35), nullable=True)  # PER.POSTADDR4
    postal_address_line_5 = Column(String(35), nullable=True)  # PER.POSTADDR5
    postal_code = Column(String(4), nullable=True)  # PER.POSTCDPOST
    
    # Geographic information
    country = Column(String(2), nullable=False, default='ZA')
    province = Column(String(50), nullable=False)
    city = Column(String(50), nullable=False)
    
    # Define table constraints
    __table_args__ = (
        # Index for person lookup
        Index('ix_address_person', 'person_id', 'address_type'),
        
        # Check constraints
        CheckConstraint(
            "length(street_postal_code) = 4 OR street_postal_code IS NULL", 
            name='ck_street_postal_code_length'
        ),
        CheckConstraint(
            "length(postal_code) = 4 OR postal_code IS NULL", 
            name='ck_postal_code_length'
        ),
    )
    
    def __repr__(self):
        return f"<PersonAddress(person_id={self.person_id}, type={self.address_type})>" 

# Country-specific configuration validation will be handled in:
# - app/core/country_config.py: Country-specific field validation
# - app/services/validation.py: Business rule validation
# - app/schemas/person.py: API input validation

"""
Country Configuration Examples (will be implemented separately):

SOUTH_AFRICA_CONFIG = {
    "id_types": ["RSA_ID", "RSA_PASSPORT", "TEMPORARY_ID", "ASYLUM_PERMIT"],
    "nationalities": ["ZA", "Foreign"],
    "languages": ["EN", "AF", "ZU", "XH", "ST", "TN", "SS", "VE", "TS", "NR", "ND"],
    "validation_rules": {
        "RSA_ID": {"length": 13, "numeric": True, "check_digit": True},
        "RSA_PASSPORT": {"length": 9, "alphanumeric": True}
    }
}

KENYA_CONFIG = {
    "id_types": ["NATIONAL_ID", "PASSPORT", "REFUGEE_ID", "ALIEN_ID"],
    "nationalities": ["KE", "Foreign"],
    "languages": ["EN", "SW", "KI", "LU", "KA", "ME", "GU", "KU", "MA", "TU"],
    "validation_rules": {
        "NATIONAL_ID": {"length": 8, "numeric": True},
        "PASSPORT": {"length": 9, "alphanumeric": True}
    }
}

NIGERIA_CONFIG = {
    "id_types": ["NATIONAL_ID", "VOTERS_CARD", "DRIVERS_LICENSE", "PASSPORT"],
    "nationalities": ["NG", "Foreign"],
    "languages": ["EN", "HA", "IG", "YO", "FU", "IJ", "KA", "TI", "UR", "BI"],
    "validation_rules": {
        "NATIONAL_ID": {"length": 11, "numeric": True},
        "VOTERS_CARD": {"length": 19, "alphanumeric": True}
    }
}
""" 