"""
Validation Service
Business rule validation for person management
Implements validation codes V00001-V00019, V00485, V00585
"""

from typing import List
from datetime import date, datetime
import re
from sqlalchemy.orm import Session
import structlog

from app.schemas.person import PersonCreate, ValidationResult
from app.models.person import Person
from app.core.config import settings

logger = structlog.get_logger()


class ValidationService:
    """Service class for business rule validation"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def validate_person_creation(self, person_data: PersonCreate) -> List[ValidationResult]:
        """
        Validate person creation against all business rules
        Returns list of validation results
        """
        results = []
        
        # Basic validation for corrected schema structure
        # V00001: Business name/surname is required
        results.append(self._validate_business_or_surname(person_data.business_or_surname))
        
        # V00007: Nationality is required
        results.append(self._validate_nationality(person_data.nationality_code))
        
        # V00008: Email format validation (if provided)
        if person_data.email_address:
            results.append(self._validate_email_format(person_data.email_address))
        
        # V00009: Phone number format validation (if provided)
        if person_data.cell_phone:
            results.append(self._validate_phone_number(person_data.cell_phone))
        
        # Validate aliases if provided
        if person_data.aliases:
            for alias in person_data.aliases:
                results.append(self._validate_id_document(alias.id_document_type_code, alias.id_document_number))
        
        # V00485: Natural person validation
        if person_data.person_nature in ["01", "02"] and not person_data.natural_person:
            results.append(ValidationResult(
                code="V00485",
                field="natural_person",
                message="Natural person details required for person_nature 01/02",
                is_valid=False
            ))
        
        return [r for r in results if r is not None]
    
    def _validate_business_or_surname(self, business_or_surname: str) -> ValidationResult:
        """V00001: Business name or surname validation"""
        if not business_or_surname or business_or_surname.strip() == "":
            return ValidationResult(
                code="V00001",
                field="business_or_surname",
                message="Business name or surname is required",
                is_valid=False
            )
        
        if len(business_or_surname.strip()) < 2:
            return ValidationResult(
                code="V00001",
                field="business_or_surname", 
                message="Business name or surname must be at least 2 characters",
                is_valid=False
            )
            
        return ValidationResult(
            code="V00001",
            field="business_or_surname",
            message="Business name or surname is valid",
            is_valid=True
        )
    
    def _validate_surname(self, surname: str) -> ValidationResult:
        """V00002: Surname validation"""
        if not surname or surname.strip() == "":
            return ValidationResult(
                code="V00002",
                field="surname",
                message="Surname is required",
                is_valid=False
            )
        
        if len(surname.strip()) < 2:
            return ValidationResult(
                code="V00002",
                field="surname",
                message="Surname must be at least 2 characters", 
                is_valid=False
            )
            
        return ValidationResult(
            code="V00002",
            field="surname",
            message="Surname is valid",
            is_valid=True
        )
    
    def _validate_date_of_birth(self, date_of_birth: date) -> ValidationResult:
        """V00003: Date of birth validation"""
        if not date_of_birth:
            return ValidationResult(
                code="V00003",
                field="date_of_birth",
                message="Date of birth is required",
                is_valid=False
            )
        
        if date_of_birth >= date.today():
            return ValidationResult(
                code="V00003",
                field="date_of_birth",
                message="Date of birth cannot be in the future",
                is_valid=False
            )
            
        return ValidationResult(
            code="V00003",
            field="date_of_birth",
            message="Date of birth is valid",
            is_valid=True
        )
    
    def _validate_gender(self, gender: str) -> ValidationResult:
        """V00004: Gender validation"""
        valid_genders = ["M", "F", "Male", "Female"]
        
        if not gender or gender not in valid_genders:
            return ValidationResult(
                code="V00004",
                field="gender",
                message=f"Gender must be one of: {', '.join(valid_genders)}",
                is_valid=False
            )
            
        return ValidationResult(
            code="V00004",
            field="gender",
            message="Gender is valid",
            is_valid=True
        )
    
    def _validate_identification_type(self, identification_type: str) -> ValidationResult:
        """V00005: Identification type validation"""
        valid_types = ["RSA_ID", "Passport", "Temporary_ID", "Asylum_Document"]
        
        if not identification_type or identification_type not in valid_types:
            return ValidationResult(
                code="V00005",
                field="identification_type",
                message=f"Identification type must be one of: {', '.join(valid_types)}",
                is_valid=False
            )
            
        return ValidationResult(
            code="V00005",
            field="identification_type",
            message="Identification type is valid",
            is_valid=True
        )
    
    def _validate_identification_number(self, identification_type: str, identification_number: str) -> ValidationResult:
        """V00006: Identification number format validation"""
        if not identification_number or identification_number.strip() == "":
            return ValidationResult(
                code="V00006",
                field="identification_number",
                message="Identification number is required",
                is_valid=False
            )
        
        # South African ID number validation
        if identification_type == "RSA_ID" and settings.COUNTRY_CODE == "ZA":
            if not re.match(r'^\d{13}$', identification_number):
                return ValidationResult(
                    code="V00006",
                    field="identification_number", 
                    message="South African ID number must be 13 digits",
                    is_valid=False
                )
        
        # Passport validation
        if identification_type == "Passport":
            if len(identification_number) < 6 or len(identification_number) > 20:
                return ValidationResult(
                    code="V00006",
                    field="identification_number",
                    message="Passport number must be between 6 and 20 characters",
                    is_valid=False
                )
        
        return ValidationResult(
            code="V00006",
            field="identification_number",
            message="Identification number is valid",
            is_valid=True
        )
    
    def _validate_nationality(self, nationality: str) -> ValidationResult:
        """V00007: Nationality validation"""
        valid_nationalities = ["South African", "Zimbabwean", "Nigerian", "Kenyan", "Other"]
        
        if not nationality or nationality not in valid_nationalities:
            return ValidationResult(
                code="V00007",
                field="nationality",
                message=f"Nationality must be one of: {', '.join(valid_nationalities)}",
                is_valid=False
            )
            
        return ValidationResult(
            code="V00007",
            field="nationality",
            message="Nationality is valid",
            is_valid=True
        )
    
    def _validate_email_format(self, email: str) -> ValidationResult:
        """V00008: Email format validation"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email):
            return ValidationResult(
                code="V00008",
                field="email_address",
                message="Invalid email format",
                is_valid=False
            )
            
        return ValidationResult(
            code="V00008",
            field="email_address",
            message="Email format is valid",
            is_valid=True
        )
    
    def _validate_phone_number(self, phone_number: str) -> ValidationResult:
        """V00009: Phone number validation"""
        # South African phone number format
        phone_pattern = r'^(\+27|0)[0-9]{9}$'
        
        if not re.match(phone_pattern, phone_number):
            return ValidationResult(
                code="V00009",
                field="phone_number",
                message="Invalid phone number format (use +27xxxxxxxxx or 0xxxxxxxxx)",
                is_valid=False
            )
            
        return ValidationResult(
            code="V00009",
            field="phone_number",
            message="Phone number format is valid",
            is_valid=True
        )
    
    def _validate_minimum_age(self, date_of_birth: date) -> ValidationResult:
        """V00010: Minimum age validation"""
        today = date.today()
        age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
        
        min_age = 16  # Minimum age for learner's license
        
        if age < min_age:
            return ValidationResult(
                code="V00010",
                field="date_of_birth",
                message=f"Minimum age is {min_age} years",
                is_valid=False
            )
            
        return ValidationResult(
            code="V00010",
            field="date_of_birth",
            message="Age meets minimum requirement",
            is_valid=True
        )
    
    def _validate_maximum_age(self, date_of_birth: date) -> ValidationResult:
        """V00011: Maximum age validation"""
        today = date.today()
        age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
        
        max_age = 120  # Maximum reasonable age
        
        if age > max_age:
            return ValidationResult(
                code="V00011",
                field="date_of_birth",
                message=f"Maximum age is {max_age} years",
                is_valid=False
            )
            
        return ValidationResult(
            code="V00011",
            field="date_of_birth",
            message="Age is within valid range",
            is_valid=True
        )
    
    def _validate_name_format(self, name: str, field_name: str) -> ValidationResult:
        """V00012: Name format validation"""
        if not name:
            return None
            
        # Names should only contain letters, spaces, hyphens, and apostrophes
        name_pattern = r"^[a-zA-Z\s\-']+$"
        
        if not re.match(name_pattern, name):
            return ValidationResult(
                code="V00012",
                field=field_name,
                message="Name can only contain letters, spaces, hyphens, and apostrophes",
                is_valid=False
            )
            
        return ValidationResult(
            code="V00012",
            field=field_name,
            message="Name format is valid",
            is_valid=True
        )
    
    def _validate_name_characters(self, name: str, field_name: str) -> ValidationResult:
        """V00013: Name character validation"""
        if not name:
            return None
            
        if len(name) > 50:
            return ValidationResult(
                code="V00013",
                field=field_name,
                message="Name cannot exceed 50 characters",
                is_valid=False
            )
            
        return ValidationResult(
            code="V00013",
            field=field_name,
            message="Name length is valid",
            is_valid=True
        )
    
    def _validate_id_document(self, doc_type: str, doc_number: str) -> ValidationResult:
        """Validate ID document type and number"""
        if not doc_type or not doc_number:
            return ValidationResult(
                code="V00013",
                field="identification",
                message="Identification type and number are required",
                is_valid=False
            )
        
        return ValidationResult(
            code="V00013",
            field="identification",
            message="Identification is valid",
            is_valid=True
        )
    
    def _validate_data_completeness(self, person_data: PersonCreate) -> ValidationResult:
        """V00015: Data completeness validation"""
        required_fields = [
            person_data.business_or_surname,
            person_data.person_nature,
            person_data.nationality_code
        ]
        
        if not all(field is not None and str(field).strip() != "" for field in required_fields):
            return ValidationResult(
                code="V00015",
                field="general",
                message="All required fields must be completed",
                is_valid=False
            )
            
        return ValidationResult(
            code="V00015",
            field="general",
            message="Data completeness is valid",
            is_valid=True
        ) 