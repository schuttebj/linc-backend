"""
Person Database Model
Implements Person entity from Section 1.1 Person Registration/Search Screen
"""

from sqlalchemy import Column, String, Date, DateTime, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from typing import Optional
import uuid

from app.models.base import BaseModel


class Person(BaseModel):
    """
    Person entity model
    
    Implements Person entity from specification Section 1.1
    Source: Section 1.1 Person Registration/Search Screen
    Legacy References: NATPER, PER tables
    """
    
    # Core Identity Fields (V00001-V00019)
    identification_type = Column(String(3), nullable=False, index=True)  # V00001: Mandatory
    identification_number = Column(String(13), nullable=False, index=True)  # V00013: Mandatory
    first_name = Column(String(32), nullable=False)  # NATPER.FULLNAME1
    middle_name = Column(String(32), nullable=True)  # NATPER.FULLNAME2
    surname = Column(String(32), nullable=False)  # PER.BUSORSURNAME
    initials = Column(String(3), nullable=True)  # PER.INITIALS
    date_of_birth = Column(Date, nullable=False, index=True)  # NATPER.BIRTHD
    gender = Column(String(2), nullable=False)  # PER.NATOFPER - V00485: Must be natural person
    nationality = Column(String(2), nullable=False)  # PER.NATNPOPGRPCD
    language_preference = Column(String(2), nullable=True)  # NATPER.PREFLANGCD
    
    # Contact Information Fields
    email_address = Column(String(50), nullable=True)  # NATPER.EMAILADDR
    home_phone_code = Column(String(10), nullable=True)  # NATPER.HTELCD
    home_phone_number = Column(String(10), nullable=True)  # NATPER.HTELN
    work_phone_code = Column(String(10), nullable=True)  # NATPER.WTELCD
    work_phone_number = Column(String(15), nullable=True)  # NATPER.WTELN
    cell_phone = Column(String(15), nullable=True)  # NATPER.CELLN
    fax_code = Column(String(10), nullable=True)  # NATPER.FAXCD
    fax_number = Column(String(10), nullable=True)  # NATPER.FAXN
    
    # Additional audit and tracking fields
    alias_check_date = Column(DateTime, nullable=True)  # V00016: Unacceptable alias check
    last_validation_date = Column(DateTime, nullable=True)  # Last business rule validation
    validation_status = Column(String(20), default='pending', nullable=False)  # pending, valid, invalid
    
    # Define table constraints
    __table_args__ = (
        # Unique constraint on identification within country
        Index('ix_person_unique_id', 'country_code', 'identification_type', 'identification_number', unique=True),
        
        # Composite index for search performance
        Index('ix_person_search', 'country_code', 'surname', 'first_name', 'date_of_birth'),
        
        # Check constraints for data integrity
        CheckConstraint(
            "identification_type IN ('01', '02', '03', '04', '97')", 
            name='ck_person_id_type'
        ),
        CheckConstraint(
            "gender IN ('01', '02')", 
            name='ck_person_gender'
        ),
        CheckConstraint(
            "nationality IN ('01', '02')", 
            name='ck_person_nationality'
        ),
        CheckConstraint(
            "validation_status IN ('pending', 'valid', 'invalid', 'expired')", 
            name='ck_person_validation_status'
        ),
        
        # Data integrity constraints
        CheckConstraint(
            "length(identification_number) <= 13", 
            name='ck_person_id_length'
        ),
        CheckConstraint(
            "date_of_birth <= CURRENT_DATE", 
            name='ck_person_birth_date'
        ),
    )
    
    def __repr__(self):
        return f"<Person(id={self.id}, id_number={self.identification_number}, name={self.first_name} {self.surname})>"
    
    @property
    def full_name(self) -> str:
        """Get full name"""
        names = [self.first_name]
        if self.middle_name:
            names.append(self.middle_name)
        names.append(self.surname)
        return " ".join(names)
    
    @property
    def display_name(self) -> str:
        """Get display name with initials"""
        if self.initials:
            return f"{self.initials} {self.surname}"
        return f"{self.first_name} {self.surname}"
    
    def validate_identification_number(self) -> list:
        """
        Validate identification number based on business rules
        Implements V00013, V00017, V00018, V00019
        """
        validation_errors = []
        
        # V00013: Identification Number Mandatory
        if not self.identification_number:
            validation_errors.append({
                'code': 'V00013',
                'message': 'Identification number is mandatory'
            })
            return validation_errors
        
        # V00018: ID Number Length Validation
        if self.identification_type in ['01', '02', '04', '97']:
            if len(self.identification_number) != 13:
                validation_errors.append({
                    'code': 'V00018',
                    'message': 'Identification number must be 13 characters for this type'
                })
        
        # V00017: Numeric Validation for SA ID
        if self.identification_type == '02':  # RSA ID
            if not self.identification_number.isdigit():
                validation_errors.append({
                    'code': 'V00017',
                    'message': 'RSA ID number must be numeric'
                })
        
        # V00019: Check Digit Validation (simplified)
        if self.identification_type == '02' and len(self.identification_number) == 13:
            # Implement Luhn algorithm for RSA ID validation
            if not self._validate_rsa_id_checksum():
                validation_errors.append({
                    'code': 'V00019',
                    'message': 'Invalid RSA ID number check digit'
                })
        
        return validation_errors
    
    def _validate_rsa_id_checksum(self) -> bool:
        """
        Validate RSA ID checksum using simplified algorithm
        Note: This is a simplified version. Full implementation would use 
        the official RSA ID validation algorithm
        """
        if len(self.identification_number) != 13 or not self.identification_number.isdigit():
            return False
        
        # Simplified checksum validation - replace with official algorithm
        digits = [int(d) for d in self.identification_number]
        checksum = sum(digits[:-1]) % 10
        return checksum == digits[-1]
    
    def get_age(self) -> int:
        """Calculate current age"""
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    def is_eligible_for_license_type(self, license_type: str) -> bool:
        """Check if person meets age requirements for license type"""
        age_requirements = {
            'A': 16,    # Motorcycle
            'B': 18,    # Light vehicle
            'C': 21,    # Heavy vehicle
            'D': 24,    # Bus/taxi
            'EB': 18,   # Light vehicle with trailer
            'EC': 21    # Heavy vehicle with trailer
        }
        
        required_age = age_requirements.get(license_type, 18)
        return self.get_age() >= required_age


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
    address_type = Column(String(20), nullable=False)  # 'residential' or 'postal'
    
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
            "address_type IN ('residential', 'postal')", 
            name='ck_address_type'
        ),
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