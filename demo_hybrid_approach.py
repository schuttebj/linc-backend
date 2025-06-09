#!/usr/bin/env python3
"""
Demonstration of the Hybrid Approach for LINC Backend

This script demonstrates how the hybrid approach works in practice, using:
1. Universal enums for standardized fields (gender, validation status, etc.)
2. Country-specific configuration for variable fields (ID types, languages, etc.)

Based on the refactored documentation analysis from:
- Refactored_Screen_Field_Specifications.md
- Refactored_Business_Rules_Specification.md
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.enums import *
from app.core.country_config import country_config, COUNTRY_CONFIGURATIONS
from app.services.validation import validation_service
from app.core.config import settings
import json
from typing import Dict, Any


def demo_universal_enums():
    """Demonstrate universal enums that work across all countries"""
    print("🌍 UNIVERSAL ENUMS - Consistent across all countries")
    print("=" * 60)
    
    print("✅ Gender Codes (Universal):")
    for gender in Gender:
        print(f"   {gender.name}: {gender.value}")
    
    print("\n✅ Validation Status (Universal):")
    for status in ValidationStatus:
        print(f"   {status.name}: {status.value}")
    
    print("\n✅ Application Status (Universal):")
    for status in ApplicationStatus:
        print(f"   {status.name}: {status.value}")
    
    print("\n✅ License Status (Universal):")
    for status in LicenseStatus:
        print(f"   {status.name}: {status.value}")
    
    print("\n✅ Address Types (Universal):")
    for addr_type in AddressType:
        print(f"   {addr_type.name}: {addr_type.value}")


def demo_country_specific_config():
    """Demonstrate country-specific configuration"""
    print("\n\n🏛️ COUNTRY-SPECIFIC CONFIGURATION")
    print("=" * 60)
    
    for country_code, config in COUNTRY_CONFIGURATIONS.items():
        print(f"\n📍 {config.country_name} ({country_code}):")
        print(f"   Currency: {config.currency} ({config.currency_symbol})")
        print(f"   Default Language: {config.default_language}")
        
        print(f"   ID Types: {config.id_types}")
        print(f"   Languages: {config.languages}")
        print(f"   License Types: {config.license_types}")
        print(f"   Authorities: {config.authority_codes}")
        
        # Show ID validation rules
        print(f"   ID Validation Rules:")
        for id_type, rule in config.id_validation_rules.items():
            details = []
            if rule.length:
                details.append(f"length={rule.length}")
            if rule.numeric:
                details.append("numeric")
            if rule.alphanumeric:
                details.append("alphanumeric")
            if rule.check_digit:
                details.append("check_digit")
            print(f"     {id_type}: {', '.join(details)}")


def demo_validation_in_action():
    """Demonstrate validation using the hybrid approach"""
    print("\n\n🔍 VALIDATION DEMONSTRATION")
    print("=" * 60)
    
    # Test data for different countries
    test_cases = [
        {
            "country": "South Africa",
            "person_data": {
                "id_type": "RSA_ID",
                "id_number": "8001015009087",  # Valid RSA ID
                "first_name": "John",
                "surname": "Smith",
                "gender": "01",  # Universal enum value
                "nationality": "ZA",
                "language_preference": "EN",
                "email": "john.smith@example.com",
                "residential_address_line_1": "123 Main Street",
                "residential_postal_code": "1234",
                "residential_city": "Cape Town",
                "validation_status": "validated",  # Universal enum value
                "country_code": "ZA"
            }
        },
        {
            "country": "Kenya",
            "person_data": {
                "id_type": "NATIONAL_ID",
                "id_number": "12345678",  # Valid Kenyan ID
                "first_name": "Jane",
                "surname": "Doe",
                "gender": "02",  # Universal enum value
                "nationality": "KE",
                "language_preference": "SW",
                "email": "jane.doe@example.com",
                "postal_address_line_1": "PO Box 123",
                "postal_postal_code": "12345",
                "validation_status": "pending",  # Universal enum value
                "country_code": "KE"
            }
        },
        {
            "country": "Invalid Example",
            "person_data": {
                "id_type": "INVALID_TYPE",  # Invalid for any country
                "id_number": "123",  # Too short
                "first_name": "",  # Missing required field
                "surname": "Test",
                "gender": "99",  # Invalid universal enum value
                "nationality": "XX",  # Invalid
                "language_preference": "ZZ",  # Invalid
                "validation_status": "invalid_status",  # Invalid universal enum
                "country_code": "ZA"
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}: {test_case['country']}")
        print("-" * 40)
        
        person_data = test_case["person_data"]
        
        # Show key data
        print(f"ID Type: {person_data.get('id_type')} (Country-specific)")
        print(f"ID Number: {person_data.get('id_number')} (Country-specific validation)")
        print(f"Gender: {person_data.get('gender')} (Universal enum)")
        print(f"Language: {person_data.get('language_preference')} (Country-specific)")
        print(f"Validation Status: {person_data.get('validation_status')} (Universal enum)")
        
        # Run validation
        is_valid, errors = validation_service.validate_person(person_data)
        
        print(f"\n🔍 Validation Result: {'✅ VALID' if is_valid else '❌ INVALID'}")
        
        if errors:
            print("📝 Validation Errors:")
            for error in errors:
                severity_icon = {"error": "🚫", "warning": "⚠️", "info": "ℹ️"}.get(error.severity, "❓")
                print(f"   {severity_icon} {error.field}: {error.message} ({error.code})")
        else:
            print("✨ No validation errors!")


def demo_license_application_validation():
    """Demonstrate license application validation with hybrid approach"""
    print("\n\n🚗 LICENSE APPLICATION VALIDATION")
    print("=" * 60)
    
    # Valid South African person applying for different licenses
    person_data = {
        "id_type": "RSA_ID",
        "id_number": "8001015009087",  # 24 years old
        "first_name": "John",
        "surname": "Smith",
        "gender": "01",
        "nationality": "ZA",
        "language_preference": "EN",
        "date_of_birth": "1980-01-01",
        "validation_status": "validated",
        "residential_address_line_1": "123 Main Street",
        "residential_postal_code": "1234",
        "residential_city": "Cape Town",
        "country_code": "ZA"
    }
    
    # Test different license types
    license_types = ["A", "B", "C", "C1"]  # South African license types
    
    for license_type in license_types:
        print(f"\n📄 License Application: Type {license_type}")
        print("-" * 30)
        
        age_requirement = country_config.get_license_age_requirement(license_type)
        print(f"Age Requirement: {age_requirement} years")
        
        is_valid, errors = validation_service.validate_for_license_application(person_data, license_type)
        
        print(f"Result: {'✅ ELIGIBLE' if is_valid else '❌ NOT ELIGIBLE'}")
        
        for error in errors:
            if error.severity == "error":
                print(f"   🚫 {error.message}")
            elif error.severity == "warning":
                print(f"   ⚠️ {error.message}")


def demo_country_switching():
    """Demonstrate how the same system handles different countries"""
    print("\n\n🔄 COUNTRY SWITCHING DEMONSTRATION")
    print("=" * 60)
    
    print("💡 The same codebase handles different countries by:")
    print("   1. Using universal enums for standardized fields")
    print("   2. Using country configuration for variable fields")
    print("   3. Setting COUNTRY_CODE environment variable")
    
    print(f"\n🌍 Current Deployment Country: {settings.COUNTRY_CODE}")
    print(f"📋 Supported ID Types: {country_config.get_supported_id_types()}")
    print(f"🗣️ Supported Languages: {country_config.get_supported_languages()}")
    print(f"🚗 Supported License Types: {country_config.get_supported_license_types()}")
    
    print("\n🔧 To deploy in a different country:")
    print("   1. Set COUNTRY_CODE=KE (for Kenya) or COUNTRY_CODE=NG (for Nigeria)")
    print("   2. Set COUNTRY_NAME and CURRENCY accordingly")
    print("   3. Same code automatically uses correct validation rules!")


def main():
    """Run the complete demonstration"""
    print("🎯 LINC BACKEND - HYBRID APPROACH DEMONSTRATION")
    print("Based on Refactored Documentation Analysis")
    print("=" * 80)
    
    print(f"Current Configuration:")
    print(f"  Country: {settings.COUNTRY_CODE}")
    print(f"  Country Name: {getattr(settings, 'COUNTRY_NAME', 'Not set')}")
    print(f"  Currency: {getattr(settings, 'CURRENCY', 'Not set')}")
    
    # Run all demonstrations
    demo_universal_enums()
    demo_country_specific_config()
    demo_validation_in_action()
    demo_license_application_validation()
    demo_country_switching()
    
    print("\n\n✨ HYBRID APPROACH BENEFITS:")
    print("=" * 60)
    print("✅ Type Safety: Universal fields use enums for compile-time checking")
    print("✅ Flexibility: Country-specific fields adapt to local requirements")
    print("✅ Maintainability: Single codebase supports multiple countries")
    print("✅ Documentation-Driven: Based on comprehensive specification analysis")
    print("✅ Future-Proof: Easy to add new countries or modify existing ones")
    print("✅ Performance: Fast enum lookups for universal fields")
    print("✅ Validation: Comprehensive business rule validation")
    
    print("\n📚 Documentation References:")
    print("   - Refactored_Screen_Field_Specifications.md")
    print("   - Refactored_Business_Rules_Specification.md")
    print("   - LINC single-country deployment architecture")


if __name__ == "__main__":
    main() 