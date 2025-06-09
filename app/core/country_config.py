"""
Country-specific configuration management system.

Based on the refactored documentation analysis, this module handles country-specific
field validation and configuration for the LINC system. The system supports different
countries with their own ID types, validation rules, and system parameters.

Reference: Refactored_Screen_Field_Specifications.md and Refactored_Business_Rules_Specification.md
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, validator
import re
from app.core.config import settings


class IDValidationRule(BaseModel):
    """Validation rules for ID document types"""
    length: Optional[int] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    numeric: bool = False
    alphanumeric: bool = False
    check_digit: bool = False
    pattern: Optional[str] = None
    description: str = ""


class CountryConfig(BaseModel):
    """Country-specific configuration"""
    country_code: str
    country_name: str
    currency: str
    
    # ID Document Types - Country-specific
    id_types: List[str]
    id_validation_rules: Dict[str, IDValidationRule]
    
    # Nationality Codes - Country-specific
    nationalities: List[str]
    
    # Language Codes - Country-specific
    languages: List[str]
    
    # License Types - Country-specific  
    license_types: List[str]
    license_age_requirements: Dict[str, int]
    
    # Authority/Jurisdiction Codes - Country-specific
    authority_codes: List[str]
    
    # Address Configuration
    postal_code_pattern: Optional[str] = None
    postal_code_length: Optional[int] = None
    
    # System Parameters
    default_language: str
    date_format: str = "YYYY-MM-DD"
    currency_symbol: str
    
    class Config:
        arbitrary_types_allowed = True


# Country-specific configurations based on refactored documentation
COUNTRY_CONFIGURATIONS = {
    "ZA": CountryConfig(
        country_code="ZA",
        country_name="South Africa",
        currency="ZAR",
        
        # South African ID Types from Screen Field Specifications
        id_types=["RSA_ID", "RSA_PASSPORT", "TEMPORARY_ID", "ASYLUM_PERMIT", "FOREIGN_PASSPORT"],
        id_validation_rules={
            "RSA_ID": IDValidationRule(
                length=13,
                numeric=True,
                check_digit=True,
                description="South African ID Number (13 digits with check digit)"
            ),
            "RSA_PASSPORT": IDValidationRule(
                length=9,
                alphanumeric=True,
                description="South African Passport (9 characters)"
            ),
            "TEMPORARY_ID": IDValidationRule(
                min_length=8,
                max_length=13,
                alphanumeric=True,
                description="Temporary Identity Certificate"
            ),
            "ASYLUM_PERMIT": IDValidationRule(
                min_length=8,
                max_length=15,
                alphanumeric=True,
                description="Asylum Seeker Permit"
            ),
            "FOREIGN_PASSPORT": IDValidationRule(
                min_length=6,
                max_length=12,
                alphanumeric=True,
                description="Foreign Passport"
            )
        },
        
        # South African Nationalities
        nationalities=["ZA", "Foreign"],
        
        # South African Languages (11 official languages)
        languages=["EN", "AF", "ZU", "XH", "ST", "TN", "SS", "VE", "TS", "NR", "ND"],
        
        # South African License Types from Business Rules
        license_types=["A", "A1", "B", "C", "C1", "EB", "EC", "EC1"],
        license_age_requirements={
            "A": 16,    # Motorcycle
            "A1": 16,   # Light motorcycle  
            "B": 18,    # Light vehicle
            "C": 21,    # Heavy vehicle
            "C1": 18,   # Medium vehicle
            "EB": 18,   # Light vehicle with trailer
            "EC": 21,   # Heavy vehicle with trailer
            "EC1": 18   # Medium vehicle with trailer
        },
        
        # South African Authority Codes
        authority_codes=["DLTC", "DTLC", "RA", "METRO"],
        
        # Address Configuration
        postal_code_pattern=r"^\d{4}$",
        postal_code_length=4,
        
        # System Parameters
        default_language="EN",
        currency_symbol="R",
    ),
    
    "KE": CountryConfig(
        country_code="KE",
        country_name="Kenya",
        currency="KES",
        
        # Kenyan ID Types
        id_types=["NATIONAL_ID", "PASSPORT", "REFUGEE_ID", "ALIEN_ID", "WORK_PERMIT"],
        id_validation_rules={
            "NATIONAL_ID": IDValidationRule(
                length=8,
                numeric=True,
                description="Kenyan National ID (8 digits)"
            ),
            "PASSPORT": IDValidationRule(
                length=9,
                alphanumeric=True,
                description="Kenyan Passport (9 characters)"
            ),
            "REFUGEE_ID": IDValidationRule(
                min_length=8,
                max_length=12,
                alphanumeric=True,
                description="Refugee Identity Document"
            ),
            "ALIEN_ID": IDValidationRule(
                min_length=8,
                max_length=12,
                alphanumeric=True,
                description="Alien Registration Certificate"
            ),
            "WORK_PERMIT": IDValidationRule(
                min_length=8,
                max_length=15,
                alphanumeric=True,
                description="Work Permit"
            )
        },
        
        # Kenyan Nationalities
        nationalities=["KE", "Foreign"],
        
        # Kenyan Languages
        languages=["EN", "SW", "KI", "LU", "KA", "ME", "GU", "KU", "MA", "TU"],
        
        # Kenyan License Types
        license_types=["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K"],
        license_age_requirements={
            "A": 16,    # Motorcycle
            "B": 18,    # Light vehicle
            "C": 21,    # Medium vehicle
            "D": 21,    # Heavy vehicle
            "E": 21,    # Bus/Matatu
            "F": 18,    # Tractor
            "G": 21,    # Special vehicle
            "H": 18,    # Forklift
            "I": 21,    # Road roller
            "J": 21,    # Grader
            "K": 21     # Special machinery
        },
        
        # Kenyan Authority Codes
        authority_codes=["NTSA", "DLT", "COUNTY"],
        
        # Address Configuration  
        postal_code_pattern=r"^\d{5}$",
        postal_code_length=5,
        
        # System Parameters
        default_language="EN",
        currency_symbol="KSh",
    ),
    
    "NG": CountryConfig(
        country_code="NG",
        country_name="Nigeria",
        currency="NGN",
        
        # Nigerian ID Types
        id_types=["NATIONAL_ID", "VOTERS_CARD", "DRIVERS_LICENSE", "PASSPORT", "BVN"],
        id_validation_rules={
            "NATIONAL_ID": IDValidationRule(
                length=11,
                numeric=True,
                description="Nigerian National Identification Number (11 digits)"
            ),
            "VOTERS_CARD": IDValidationRule(
                length=19,
                alphanumeric=True,
                pattern=r"^[A-Z0-9]{19}$",
                description="Permanent Voter Card (19 characters)"
            ),
            "DRIVERS_LICENSE": IDValidationRule(
                min_length=10,
                max_length=12,
                alphanumeric=True,
                description="Nigerian Driver's License"
            ),
            "PASSPORT": IDValidationRule(
                length=9,
                alphanumeric=True,
                pattern=r"^[A-Z]\d{8}$",
                description="Nigerian Passport (A + 8 digits)"
            ),
            "BVN": IDValidationRule(
                length=11,
                numeric=True,
                description="Bank Verification Number (11 digits)"
            )
        },
        
        # Nigerian Nationalities
        nationalities=["NG", "Foreign"],
        
        # Nigerian Languages
        languages=["EN", "HA", "IG", "YO", "FU", "IJ", "KA", "TI", "UR", "BI"],
        
        # Nigerian License Types
        license_types=["A", "B", "C", "D", "E", "F"],
        license_age_requirements={
            "A": 17,    # Motorcycle
            "B": 18,    # Light vehicle
            "C": 21,    # Medium vehicle
            "D": 21,    # Heavy vehicle
            "E": 21,    # Bus/Commercial
            "F": 18     # Agricultural/Special
        },
        
        # Nigerian Authority Codes
        authority_codes=["FRSC", "VIO", "STATE"],
        
        # Address Configuration
        postal_code_pattern=r"^\d{6}$",
        postal_code_length=6,
        
        # System Parameters
        default_language="EN",
        currency_symbol="₦",
    )
}


class CountryConfigManager:
    """Manager for country-specific configurations"""
    
    def __init__(self):
        self.current_country = settings.COUNTRY_CODE
        self.config = COUNTRY_CONFIGURATIONS.get(self.current_country)
        
        if not self.config:
            raise ValueError(f"Country configuration not found for: {self.current_country}")
    
    def get_config(self) -> CountryConfig:
        """Get current country configuration"""
        return self.config
    
    def validate_id_number(self, id_type: str, id_number: str) -> tuple[bool, str]:
        """
        Validate ID number based on country-specific rules
        Returns: (is_valid, error_message)
        """
        if id_type not in self.config.id_types:
            return False, f"Invalid ID type '{id_type}' for {self.config.country_name}"
        
        rule = self.config.id_validation_rules.get(id_type)
        if not rule:
            return False, f"No validation rule found for ID type '{id_type}'"
        
        # Length validation
        if rule.length and len(id_number) != rule.length:
            return False, f"ID number must be exactly {rule.length} characters"
        
        if rule.min_length and len(id_number) < rule.min_length:
            return False, f"ID number must be at least {rule.min_length} characters"
        
        if rule.max_length and len(id_number) > rule.max_length:
            return False, f"ID number must be at most {rule.max_length} characters"
        
        # Format validation
        if rule.numeric and not id_number.isdigit():
            return False, "ID number must contain only digits"
        
        if rule.alphanumeric and not id_number.isalnum():
            return False, "ID number must contain only letters and digits"
        
        if rule.pattern and not re.match(rule.pattern, id_number):
            return False, f"ID number format is invalid"
        
        # Check digit validation (for supported types)
        if rule.check_digit:
            if id_type == "RSA_ID":
                if not self._validate_rsa_id_checksum(id_number):
                    return False, "Invalid RSA ID check digit"
        
        return True, ""
    
    def _validate_rsa_id_checksum(self, id_number: str) -> bool:
        """Validate RSA ID checksum using Luhn algorithm"""
        if len(id_number) != 13 or not id_number.isdigit():
            return False
        
        # Luhn algorithm for RSA ID validation
        digits = [int(d) for d in id_number]
        checksum = 0
        
        # Process first 12 digits
        for i in range(12):
            digit = digits[i]
            if i % 2 == 1:  # Every second digit
                digit *= 2
                if digit > 9:
                    digit = digit // 10 + digit % 10
            checksum += digit
        
        # Check digit should make total divisible by 10
        calculated_check = (10 - (checksum % 10)) % 10
        return calculated_check == digits[12]
    
    def validate_nationality(self, nationality: str) -> bool:
        """Validate nationality code"""
        return nationality in self.config.nationalities
    
    def validate_language(self, language: str) -> bool:
        """Validate language code"""
        return language in self.config.languages
    
    def validate_license_type(self, license_type: str) -> bool:
        """Validate license type"""
        return license_type in self.config.license_types
    
    def get_license_age_requirement(self, license_type: str) -> Optional[int]:
        """Get minimum age requirement for license type"""
        return self.config.license_age_requirements.get(license_type)
    
    def validate_postal_code(self, postal_code: str) -> bool:
        """Validate postal code format"""
        if self.config.postal_code_pattern:
            return bool(re.match(self.config.postal_code_pattern, postal_code))
        return True
    
    def get_supported_id_types(self) -> List[str]:
        """Get list of supported ID types for current country"""
        return self.config.id_types
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages for current country"""
        return self.config.languages
    
    def get_supported_license_types(self) -> List[str]:
        """Get list of supported license types for current country"""
        return self.config.license_types


# Global country config manager instance
country_config = CountryConfigManager() 