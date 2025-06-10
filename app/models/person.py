"""
Person Management Models - CORRECTED IMPLEMENTATION
Database models for person identification, addresses, and related entities
Based on documentation requirements from Refactored_Screen_Field_Specifications.md
Implements validation codes V00001-V00019 and business rules R-ID-001 to R-ID-010
"""

from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Integer, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date
from enum import Enum as PythonEnum
import uuid

from app.core.database import Base
from app.models.base import BaseModel


class IdentificationType(PythonEnum):
    """
    Identification document types from LmIdDocTypeCd lookup
    CORRECTED MAPPING based on documentation:
    - 01 = TRN (Tax Reference Number)
    - 02 = RSA ID (South African ID Document) 
    - 03 = Foreign ID (Foreign ID Document)
    - 04 = BRN (Business Registration Number)
    - 13 = Passport
    """
    TRN = "01"              # Tax Reference Number (for organizations)
    RSA_ID = "02"           # RSA ID Document (13 digits numeric)
    FOREIGN_ID = "03"       # Foreign ID Document
    BRN = "04"              # Business Registration Number (for organizations)
    PASSPORT = "13"         # Passport


class PersonNature(PythonEnum):
    """
    Person nature classification from LmNatOfPer lookup
    CORRECTED: This should be person_nature, not person_type
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


class AddressType(PythonEnum):
    """Address type classification - matches documentation structure"""
    STREET = "street"       # Physical/residential address (PER.STREETADDR1-5)
    POSTAL = "postal"       # Postal address (PER.POSTADDR1-5)


class Person(BaseModel):
    """
    Person entity - core identity record
    Based on P00068 - Particulars of Applicant from documentation
    Implements fields exactly as specified in documentation
    """
    __tablename__ = "persons"
    
    # Core identity fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # CORRECTED: Business/family name (surname for individuals, company name for organizations)
    # Source: PER.BUSORSURNAME (32 chars, SCHAR1 format)
    business_or_surname = Column(String(32), nullable=False, comment="Business name or surname (PER.BUSORSURNAME)")
    
    # Initials for natural persons only
    # Source: PER.INITIALS (3 chars, ALPHA format)
    initials = Column(String(3), nullable=True, comment="Initials for natural persons (PER.INITIALS)")
    
    # CORRECTED: Person nature (not person_type)
    # Source: PER.NATOFPER - maps to LmNatOfPer lookup
    person_nature = Column(String(2), nullable=False, comment="Person nature from LmNatOfPer (PER.NATOFPER)")
    
    # Nationality/population group code
    # Source: PER.NATNPOPGRPCD - maps to LmNatnPopGrpCd lookup
    nationality_code = Column(String(3), nullable=False, default="ZA", comment="Nationality code (PER.NATNPOPGRPCD)")
    
    # Contact information
    # Source: NATPER.EMAILADDR (50 chars, SCHAR4 format)
    email_address = Column(String(50), nullable=True, comment="Email address (NATPER.EMAILADDR)")
    
    # Phone numbers - source: NATPER table
    home_phone_code = Column(String(10), nullable=True, comment="Home phone area code (NATPER.HTELCD)")
    home_phone_number = Column(String(10), nullable=True, comment="Home phone number (NATPER.HTELN)")
    work_phone_code = Column(String(10), nullable=True, comment="Work phone area code (NATPER.WTELCD)")
    work_phone_number = Column(String(15), nullable=True, comment="Work phone number (NATPER.WTELN)")
    cell_phone = Column(String(15), nullable=True, comment="Cell phone number (NATPER.CELLN)")
    fax_code = Column(String(10), nullable=True, comment="Fax area code (NATPER.FAXCD)")
    fax_number = Column(String(10), nullable=True, comment="Fax number (NATPER.FAXN)")
    
    # Preferences and settings
    # Source: NATPER.PREFLANGCD - maps to LmPrefLang lookup
    preferred_language = Column(String(10), nullable=True, default="en", comment="Preferred language (NATPER.PREFLANGCD)")
    
    # ADDED: Missing critical field from documentation
    # Current status alias field referenced in validation rules
    current_status_alias = Column(String(1), nullable=False, default="1", comment="Current alias status (1=Current, 2=Historical, 3=Unacceptable)")
    
    # Status and flags
    is_active = Column(Boolean, nullable=False, default=True, comment="Active status")
    
    # Audit fields - following development standards
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    
    # Relationships
    aliases = relationship("PersonAlias", back_populates="person", cascade="all, delete-orphan")
    natural_person = relationship("NaturalPerson", back_populates="person", uselist=False, cascade="all, delete-orphan")
    addresses = relationship("PersonAddress", back_populates="person", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Person(id={self.id}, name='{self.business_or_surname}', nature='{self.person_nature}')>"


class PersonAlias(BaseModel):
    """
    Person identification documents/aliases
    Supports multiple ID documents per person (current and historical)
    Implements validation rules V00001, V00013, V00016-V00019
    """
    __tablename__ = "person_aliases"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    person_id = Column(UUID(as_uuid=True), ForeignKey('persons.id'), nullable=False, index=True)
    
    # Identification document details
    # CORRECTED: Maps to ALIAS.IDDOCTYPECD - LmIdDocTypeCd lookup
    # V00001: Identification Type Mandatory
    id_document_type_code = Column(String(2), nullable=False, comment="ID document type code (ALIAS.IDDOCTYPECD)")
    
    # CORRECTED: Maps to ALIAS.IDDOCN 
    # V00013: Identification Number Mandatory
    # V00018: 13 chars for types 01,02,04,97
    # V00017: Numeric for type 02 (RSA ID)
    # V00019: Check digit validation
    id_document_number = Column(String(13), nullable=False, comment="ID document number (ALIAS.IDDOCN)")
    
    # Country of issue - maps to ALIAS.CNTRYOFISSID
    country_of_issue = Column(String(3), nullable=False, default="ZA", comment="Country of issue code (ALIAS.CNTRYOFISSID)")
    
    # Name in document - maps to ALIAS.NAMEINDOC
    name_in_document = Column(String(200), nullable=True, comment="Name as it appears in document (ALIAS.NAMEINDOC)")
    
    # Alias status and validation
    # V00016: Unacceptable Alias Check - status cannot be 3 for types ≠ 13
    # V00757: Current Alias Warning - status should be 1 for current
    alias_status = Column(String(1), nullable=False, default="1", comment="1=Current, 2=Historical, 3=Unacceptable")
    is_current = Column(Boolean, nullable=False, default=True, comment="Current/active alias")
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    
    # Relationships
    person = relationship("Person", back_populates="aliases")
    
    def __repr__(self):
        return f"<PersonAlias(id={self.id}, type='{self.id_document_type_code}', number='{self.id_document_number}')>"


class NaturalPerson(BaseModel):
    """
    Natural person specific details (individuals, not organizations)
    Based on NATPER table from documentation
    Only for person_nature 01 (Male) and 02 (Female)
    Implements validation V00485: Must be natural person
    """
    __tablename__ = "natural_persons"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    person_id = Column(UUID(as_uuid=True), ForeignKey('persons.id'), nullable=False, unique=True, index=True)
    
    # Full names from NATPER table
    # Source: NATPER.FULLNAME1 (32 chars, SCHAR1 format) - V00056: Mandatory
    full_name_1 = Column(String(32), nullable=False, comment="First name/given name (NATPER.FULLNAME1)")
    # Source: NATPER.FULLNAME2 (32 chars, SCHAR1 format) - V00059: Optional
    full_name_2 = Column(String(32), nullable=True, comment="Middle name (NATPER.FULLNAME2)")
    # Source: NATPER.FULLNAME3 (32 chars, SCHAR1 format) - V00062: Optional  
    full_name_3 = Column(String(32), nullable=True, comment="Additional name (NATPER.FULLNAME3)")
    
    # Personal details
    # Source: NATPER.BIRTHD (DTCCYYMMDD format)
    # V00065: Optional, auto-derived from RSA ID
    # V00067: Not future date
    birth_date = Column(Date, nullable=True, comment="Date of birth (NATPER.BIRTHD)")
    
    # CORRECTED: Gender should reference person.person_nature, not separate field
    # V00034: Mandatory, auto-derived from RSA ID for type 02
    # This is stored in person.person_nature (01=Male, 02=Female)
    # No separate gender field needed - use person.person_nature
    
    # Contact information specific to natural persons
    # Duplicates person.email_address for natural person specific usage
    email_address = Column(String(50), nullable=True, comment="Personal email address (NATPER.EMAILADDR)")
    
    # Language preference - duplicates person.preferred_language
    # Source: NATPER.PREFLANGCD - V00068: Mandatory
    preferred_language_code = Column(String(10), nullable=True, comment="Language preference (NATPER.PREFLANGCD)")
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    
    # Relationships
    person = relationship("Person", back_populates="natural_person")
    
    @property
    def full_name(self) -> str:
        """Get complete full name"""
        names = [self.full_name_1]
        if self.full_name_2:
            names.append(self.full_name_2)
        if self.full_name_3:
            names.append(self.full_name_3)
        return " ".join(names)
    
    @property
    def age(self) -> int:
        """Calculate current age - used for eligibility checks"""
        if not self.birth_date:
            return 0
        today = date.today()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
    
    @property
    def gender(self) -> str:
        """Get gender from person.person_nature"""
        if self.person and self.person.person_nature in ["01", "02"]:
            return "M" if self.person.person_nature == "01" else "F"
        return None
    
    def __repr__(self):
        return f"<NaturalPerson(id={self.id}, name='{self.full_name}', birth_date='{self.birth_date}')>"


class PersonAddress(BaseModel):
    """
    Person addresses - CORRECTED to match documentation structure
    Based on P00023 - Driver Address Particulars from documentation
    SEPARATE street and postal address structures as per PER.STREETADDR1-5 and PER.POSTADDR1-5
    """
    __tablename__ = "person_addresses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    person_id = Column(UUID(as_uuid=True), ForeignKey('persons.id'), nullable=False, index=True)
    
    # CORRECTED: Address type - street vs postal (not residential/postal/business)
    address_type = Column(String(10), nullable=False, comment="street or postal")
    is_primary = Column(Boolean, nullable=False, default=False, comment="Primary address of this type")
    
    # CORRECTED: Address structure matches documentation exactly
    # For STREET addresses: PER.STREETADDR1-5, PER.POSTCDSTREET
    # For POSTAL addresses: PER.POSTADDR1-5, PER.POSTCDPOST
    
    # Address line 1 - MANDATORY
    # Source: PER.STREETADDR1 or PER.POSTADDR1 (35 chars, SCHAR1 format)
    # V00095: Line 1 mandatory for postal, V00101: Optional for street
    address_line_1 = Column(String(35), nullable=False, comment="Address line 1 (PER.STREETADDR1/POSTADDR1)")
    
    # Address lines 2-5 - OPTIONAL
    # Source: PER.STREETADDR2-5 or PER.POSTADDR2-5 (35 chars, SCHAR1 format)
    address_line_2 = Column(String(35), nullable=True, comment="Address line 2 (PER.STREETADDR2/POSTADDR2)")
    address_line_3 = Column(String(35), nullable=True, comment="Address line 3 (PER.STREETADDR3/POSTADDR3)")
    address_line_4 = Column(String(35), nullable=True, comment="Address line 4 - suburb (PER.STREETADDR4/POSTADDR4)")
    address_line_5 = Column(String(35), nullable=True, comment="Address line 5 - city/town (PER.STREETADDR5/POSTADDR5)")
    
    # CORRECTED: Postal code structure
    # Source: PER.POSTCDSTREET or PER.POSTCDPOST (4 chars, NUM format)
    # V00098: Mandatory for postal, V00107: Mandatory if street address entered
    postal_code = Column(String(4), nullable=True, comment="4-digit postal code (PER.POSTCDSTREET/POSTCDPOST)")
    
    # Geographic details
    country_code = Column(String(3), nullable=False, default="ZA", comment="Country code")
    province_code = Column(String(10), nullable=True, comment="Province/state code")
    
    # ADDRCORR validation fields referenced in business rules
    # V03915-V03928: ADDRCORR validation for suburb/city matching
    suburb_validated = Column(Boolean, nullable=False, default=False, comment="Suburb validated against ADDRCORR")
    city_validated = Column(Boolean, nullable=False, default=False, comment="City validated against ADDRCORR")
    
    # Validation and verification
    is_verified = Column(Boolean, nullable=False, default=False, comment="Address verified")
    verified_date = Column(DateTime, nullable=True, comment="Date address was verified")
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    
    # Relationships
    person = relationship("Person", back_populates="addresses")
    
    @property
    def formatted_address(self) -> str:
        """Get formatted address string"""
        lines = [self.address_line_1]
        for line in [self.address_line_2, self.address_line_3, self.address_line_4, self.address_line_5]:
            if line:
                lines.append(line)
        if self.postal_code:
            lines.append(self.postal_code)
        return "\n".join(lines)
    
    def __repr__(self):
        return f"<PersonAddress(id={self.id}, type='{self.address_type}', line1='{self.address_line_1}')>"


# ADDED: Organization-specific model for business entities
class Organization(BaseModel):
    """
    Organization-specific details for business entities
    For person_nature 03-17 (non-natural persons)
    Based on organization screens from documentation
    """
    __tablename__ = "organizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    person_id = Column(UUID(as_uuid=True), ForeignKey('persons.id'), nullable=False, unique=True, index=True)
    
    # Organization details
    trading_name = Column(String(32), nullable=True, comment="Trading name if different from registered name")
    registration_date = Column(Date, nullable=True, comment="Date of registration")
    
    # Representative and proxy relationships (referenced in documentation)
    representative_person_id = Column(UUID(as_uuid=True), ForeignKey('persons.id'), nullable=True, comment="Organization representative")
    proxy_person_id = Column(UUID(as_uuid=True), ForeignKey('persons.id'), nullable=True, comment="Organization proxy")
    
    # Local authority and DCEE address (referenced in organization screens)
    local_authority_code = Column(String(10), nullable=True, comment="Local authority code (LtAutCd)")
    dcee_address = Column(String(10), nullable=True, comment="DCEE address (LmDCEEAddr)")
    resident_at_ra = Column(Boolean, nullable=False, default=True, comment="Resident at this RA")
    
    # Movement restrictions (V01768: Movement restriction validation)
    movement_restricted = Column(Boolean, nullable=False, default=False, comment="Movement between RAs restricted")
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    
    # Relationships
    person = relationship("Person", foreign_keys=[person_id])
    representative = relationship("Person", foreign_keys=[representative_person_id])
    proxy = relationship("Person", foreign_keys=[proxy_person_id])
    
    def __repr__(self):
        return f"<Organization(id={self.id}, person_id='{self.person_id}')>"


"""
Validation Code Implementation Notes:

V00001: Identification Type Mandatory - Handled by nullable=False on id_document_type_code
V00013: Identification Number Mandatory - Handled by nullable=False on id_document_number  
V00014: Person Must Exist - Handled by ForeignKey constraints and service layer validation
V00016: Unacceptable Alias Check - Handled by alias_status validation in service layer
V00017: Numeric validation for RSA ID - Handled by service layer validation
V00018: ID Number length validation - Handled by String(13) constraint and service validation
V00019: Check digit validation - Handled by service layer validation algorithm
V00485: Must be natural person - Handled by person_nature validation in service layer
V00585: XPID/TPID restriction - Handled by service layer validation

Business Rules Implementation:
R-ID-001 to R-ID-010: Implemented through model constraints and service layer validation
Address validation (V03915-V03928): ADDRCORR validation in service layer
Organization validation (V00037, V00604): Person nature validation in service layer

Country-specific validation will be handled in:
- app/core/country_config.py: Country-specific field validation rules
- app/services/validation.py: Business rule validation implementation  
- app/schemas/person.py: API input validation with Pydantic
""" 