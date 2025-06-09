"""
Person validation service implementing the hybrid approach.

This service demonstrates how universal enums and country-specific configuration
work together to provide comprehensive validation based on the refactored documentation.

Universal fields use enums for consistency.
Country-specific fields use country configuration for flexibility.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import date, datetime
from app.models.enums import ValidationStatus, Gender, AddressType
from app.core.country_config import country_config
from app.models.person import Person


class ValidationError:
    """Validation error details"""
    def __init__(self, field: str, code: str, message: str, severity: str = "error"):
        self.field = field
        self.code = code
        self.message = message
        self.severity = severity  # error, warning, info
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "code": self.code,
            "message": self.message,
            "severity": self.severity
        }


class PersonValidationService:
    """
    Person validation service implementing hybrid approach.
    
    Validates both universal fields (using enums) and country-specific fields 
    (using country configuration) based on the refactored documentation analysis.
    """
    
    def __init__(self):
        self.country_config = country_config
    
    def validate_person(self, person_data: Dict[str, Any]) -> Tuple[bool, List[ValidationError]]:
        """
        Comprehensive person validation using hybrid approach.
        
        Args:
            person_data: Dictionary containing person information
            
        Returns:
            Tuple of (is_valid, validation_errors)
        """
        errors = []
        
        # Universal field validation (using enums)
        errors.extend(self._validate_universal_fields(person_data))
        
        # Country-specific field validation (using country config)
        errors.extend(self._validate_country_specific_fields(person_data))
        
        # Business rules validation
        errors.extend(self._validate_business_rules(person_data))
        
        # Cross-field validation
        errors.extend(self._validate_cross_field_dependencies(person_data))
        
        is_valid = not any(error.severity == "error" for error in errors)
        return is_valid, errors
    
    def _validate_universal_fields(self, person_data: Dict[str, Any]) -> List[ValidationError]:
        """Validate universal fields using enums"""
        errors = []
        
        # Gender validation - universal enum
        gender = person_data.get("gender")
        if gender:
            try:
                Gender(gender)
            except ValueError:
                errors.append(ValidationError(
                    field="gender",
                    code="V00485",
                    message=f"Invalid gender code '{gender}'. Must be one of: {[g.value for g in Gender]}"
                ))
        else:
            errors.append(ValidationError(
                field="gender",
                code="V00485",
                message="Gender is mandatory"
            ))
        
        # Validation status - universal enum
        validation_status = person_data.get("validation_status", ValidationStatus.PENDING.value)
        try:
            ValidationStatus(validation_status)
        except ValueError:
            errors.append(ValidationError(
                field="validation_status",
                code="V00001",
                message=f"Invalid validation status '{validation_status}'. Must be one of: {[s.value for s in ValidationStatus]}"
            ))
        
        # Name validations - universal requirements
        first_name = person_data.get("first_name")
        if not first_name or not first_name.strip():
            errors.append(ValidationError(
                field="first_name",
                code="V00056",
                message="First name is mandatory"
            ))
        elif len(first_name) > 100:
            errors.append(ValidationError(
                field="first_name",
                code="V00056",
                message="First name cannot exceed 100 characters"
            ))
        
        surname = person_data.get("surname")
        if not surname or not surname.strip():
            errors.append(ValidationError(
                field="surname",
                code="V00043",
                message="Surname is mandatory"
            ))
        elif len(surname) > 100:
            errors.append(ValidationError(
                field="surname",
                code="V00043",
                message="Surname cannot exceed 100 characters"
            ))
        
        return errors
    
    def _validate_country_specific_fields(self, person_data: Dict[str, Any]) -> List[ValidationError]:
        """Validate country-specific fields using country configuration"""
        errors = []
        
        # ID Type validation - country-specific
        id_type = person_data.get("id_type")
        if not id_type:
            errors.append(ValidationError(
                field="id_type",
                code="V00001",
                message="Identification type is mandatory"
            ))
        elif id_type not in self.country_config.get_supported_id_types():
            errors.append(ValidationError(
                field="id_type",
                code="V00001",
                message=f"Invalid ID type '{id_type}' for {self.country_config.config.country_name}. "
                       f"Supported types: {self.country_config.get_supported_id_types()}"
            ))
        
        # ID Number validation - country-specific rules
        id_number = person_data.get("id_number")
        if not id_number:
            errors.append(ValidationError(
                field="id_number",
                code="V00013",
                message="Identification number is mandatory"
            ))
        elif id_type:
            is_valid, error_message = self.country_config.validate_id_number(id_type, id_number)
            if not is_valid:
                errors.append(ValidationError(
                    field="id_number",
                    code="V00019",
                    message=error_message
                ))
        
        # Nationality validation - country-specific
        nationality = person_data.get("nationality")
        if nationality and not self.country_config.validate_nationality(nationality):
            errors.append(ValidationError(
                field="nationality",
                code="V00040",
                message=f"Invalid nationality '{nationality}' for {self.country_config.config.country_name}. "
                       f"Supported nationalities: {self.country_config.config.nationalities}"
            ))
        
        # Language validation - country-specific
        language = person_data.get("language_preference")
        if language and not self.country_config.validate_language(language):
            errors.append(ValidationError(
                field="language_preference",
                code="V00068",
                message=f"Invalid language '{language}' for {self.country_config.config.country_name}. "
                       f"Supported languages: {self.country_config.get_supported_languages()}"
            ))
        
        # Postal code validation - country-specific format
        postal_codes = [
            ("residential_postal_code", person_data.get("residential_postal_code")),
            ("postal_postal_code", person_data.get("postal_postal_code"))
        ]
        
        for field_name, postal_code in postal_codes:
            if postal_code and not self.country_config.validate_postal_code(postal_code):
                errors.append(ValidationError(
                    field=field_name,
                    code="V00098",
                    message=f"Invalid postal code format '{postal_code}' for {self.country_config.config.country_name}"
                ))
        
        return errors
    
    def _validate_business_rules(self, person_data: Dict[str, Any]) -> List[ValidationError]:
        """Validate business rules from the refactored documentation"""
        errors = []
        
        # Date of birth validation
        date_of_birth = person_data.get("date_of_birth")
        if date_of_birth:
            if isinstance(date_of_birth, str):
                try:
                    date_of_birth = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
                except ValueError:
                    errors.append(ValidationError(
                        field="date_of_birth",
                        code="V00067",
                        message="Invalid date format. Use YYYY-MM-DD"
                    ))
                    return errors
            
            if date_of_birth > date.today():
                errors.append(ValidationError(
                    field="date_of_birth",
                    code="V00067",
                    message="Date of birth cannot be in the future"
                ))
            
            # Age calculation for various business rules
            age = self._calculate_age(date_of_birth)
            if age < 0:
                errors.append(ValidationError(
                    field="date_of_birth",
                    code="V00067",
                    message="Invalid date of birth"
                ))
        
        # Email validation if provided
        email = person_data.get("email")
        if email:
            if not self._is_valid_email(email):
                errors.append(ValidationError(
                    field="email",
                    code="V00071",
                    message="Invalid email format"
                ))
        
        return errors
    
    def _validate_cross_field_dependencies(self, person_data: Dict[str, Any]) -> List[ValidationError]:
        """Validate cross-field dependencies and business logic"""
        errors = []
        
        # Address completeness validation
        res_line1 = person_data.get("residential_address_line_1")
        res_postal = person_data.get("residential_postal_code")
        res_city = person_data.get("residential_city")
        
        post_line1 = person_data.get("postal_address_line_1")
        post_postal = person_data.get("postal_postal_code")
        
        # At least one address must be complete
        has_complete_residential = bool(res_line1 and res_postal and res_city)
        has_complete_postal = bool(post_line1 and post_postal)
        
        if not has_complete_residential and not has_complete_postal:
            errors.append(ValidationError(
                field="address",
                code="V00095",
                message="Either residential or postal address must be complete"
            ))
        
        # Country code consistency
        country_code = person_data.get("country_code")
        if country_code and country_code != self.country_config.config.country_code:
            errors.append(ValidationError(
                field="country_code",
                code="V00001",
                message=f"Country code '{country_code}' does not match deployment country '{self.country_config.config.country_code}'"
            ))
        
        return errors
    
    def _calculate_age(self, birth_date: date) -> int:
        """Calculate age from birth date"""
        today = date.today()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    
    def _is_valid_email(self, email: str) -> bool:
        """Basic email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def validate_for_license_application(self, person_data: Dict[str, Any], license_type: str) -> Tuple[bool, List[ValidationError]]:
        """
        Validate person for license application eligibility.
        Demonstrates how the hybrid approach supports complex business rules.
        """
        # First validate basic person data
        is_valid, errors = self.validate_person(person_data)
        
        # Then check license-specific requirements
        if license_type not in self.country_config.get_supported_license_types():
            errors.append(ValidationError(
                field="license_type",
                code="R-APP-001",
                message=f"Invalid license type '{license_type}' for {self.country_config.config.country_name}"
            ))
            return False, errors
        
        # Age requirement validation
        date_of_birth = person_data.get("date_of_birth")
        if date_of_birth:
            if isinstance(date_of_birth, str):
                try:
                    date_of_birth = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
                except ValueError:
                    pass
            
            if isinstance(date_of_birth, date):
                age = self._calculate_age(date_of_birth)
                required_age = self.country_config.get_license_age_requirement(license_type)
                
                if required_age and age < required_age:
                    errors.append(ValidationError(
                        field="age",
                        code="R-APP-003",
                        message=f"Minimum age for license type '{license_type}' is {required_age} years. Current age: {age}"
                    ))
        
        # Validation status must be validated for license application
        validation_status = person_data.get("validation_status", ValidationStatus.PENDING.value)
        if validation_status != ValidationStatus.VALIDATED.value:
            errors.append(ValidationError(
                field="validation_status",
                code="R-APP-002",
                message="Person must have validated status before applying for license",
                severity="warning"
            ))
        
        final_is_valid = not any(error.severity == "error" for error in errors)
        return final_is_valid, errors


# Global validation service instance
validation_service = PersonValidationService() 