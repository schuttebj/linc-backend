#!/usr/bin/env python3
"""
Test script for new lookup endpoints and enhanced person creation
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "https://linc-backend-ucer.onrender.com"  # Your deployed backend
# BASE_URL = "http://localhost:8000"  # Uncomment for local testing

def test_lookup_endpoints():
    """Test the new lookup endpoints"""
    print("🔍 Testing Lookup Endpoints...")
    
    # Test provinces endpoint
    try:
        response = requests.get(f"{BASE_URL}/api/v1/lookups/provinces")
        print(f"✅ Provinces endpoint: {response.status_code}")
        if response.status_code == 200:
            provinces = response.json()
            print(f"   Found {len(provinces)} provinces")
            for province in provinces[:3]:  # Show first 3
                print(f"   - {province['code']}: {province['name']}")
    except Exception as e:
        print(f"❌ Provinces endpoint failed: {e}")
    
    # Test phone codes endpoint
    try:
        response = requests.get(f"{BASE_URL}/api/v1/lookups/phone-codes")
        print(f"✅ Phone codes endpoint: {response.status_code}")
        if response.status_code == 200:
            phone_codes = response.json()
            print(f"   Found {len(phone_codes)} phone codes")
            for code in phone_codes[:3]:  # Show first 3
                print(f"   - {code['country_code']}: {code['phone_code']} ({code['country_name']})")
    except Exception as e:
        print(f"❌ Phone codes endpoint failed: {e}")
    
    # Test all lookups endpoint
    try:
        response = requests.get(f"{BASE_URL}/api/v1/lookups/all")
        print(f"✅ All lookups endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Provinces: {len(data['provinces'])}, Phone codes: {len(data['phone_codes'])}")
    except Exception as e:
        print(f"❌ All lookups endpoint failed: {e}")

def test_phone_validation():
    """Test phone validation endpoint"""
    print("\n📞 Testing Phone Validation...")
    
    test_cases = [
        {"+27": "821234567"},  # Valid SA number
        {"+1": "5551234567"},   # Valid US number
        {"+27": "12345"},       # Invalid SA number
    ]
    
    for case in test_cases:
        for country_code, phone_number in case.items():
            try:
                payload = {
                    "country_code": country_code,
                    "phone_number": phone_number
                }
                response = requests.post(f"{BASE_URL}/api/v1/lookups/validate-phone", json=payload)
                result = response.json()
                status = "✅" if result.get("is_valid") else "❌"
                print(f"   {status} {country_code} {phone_number}: {result.get('formatted_number', 'Invalid')}")
            except Exception as e:
                print(f"   ❌ Validation failed for {country_code} {phone_number}: {e}")

def test_enhanced_person_creation():
    """Test person creation with new fields"""
    print("\n👤 Testing Enhanced Person Creation...")
    
    # Test data with new fields
    person_data = {
        "business_or_surname": "TESTUSER",
        "initials": "JD",
        "person_nature": "01",  # Male natural person
        "nationality_code": "ZA",
        "email_address": "john.doe@example.com",
        "home_phone": "011-123-4567",
        "work_phone": "011-987-6543",
        "cell_phone_country_code": "+27",
        "cell_phone": "821234567",
        "fax_phone": "011-555-0123",
        "natural_person": {
            "full_name_1": "JOHN",
            "full_name_2": "DAVID",
            "birth_date": "1990-05-15"
        },
        "aliases": [{
            "id_document_type_code": "02",
            "id_document_number": "9005155555555",
            "country_of_issue": "ZA",
            "alias_status": "1",
            "is_current": True
        }],
        "addresses": [{
            "address_type": "street",
            "address_line_1": "123 TEST STREET",
            "address_line_4": "SANDTON",
            "address_line_5": "JOHANNESBURG",
            "postal_code": "2196",
            "country_code": "ZA",
            "province_code": "GP",
            "is_primary": True
        }]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/persons", json=person_data)
        print(f"✅ Person creation: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            print(f"   Created person ID: {result.get('id')}")
            print(f"   Name: {result.get('business_or_surname')} {result.get('initials')}")
            print(f"   Cell phone: {result.get('cell_phone_country_code', '')} {result.get('cell_phone', '')}")
            print(f"   Province: {result.get('addresses', [{}])[0].get('province_code', 'N/A')}")
            
            # Test with foreign ID and expiry date
            print("\n🌍 Testing Foreign ID with Expiry Date...")
            foreign_person_data = person_data.copy()
            foreign_person_data["business_or_surname"] = "FOREIGNUSER"
            foreign_person_data["aliases"] = [{
                "id_document_type_code": "03",
                "id_document_number": "FOREIGN123456",
                "country_of_issue": "US",
                "alias_status": "1",
                "is_current": True,
                "id_document_expiry_date": (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
            }]
            
            response2 = requests.post(f"{BASE_URL}/api/v1/persons", json=foreign_person_data)
            print(f"✅ Foreign person creation: {response2.status_code}")
            
            if response2.status_code == 201:
                result2 = response2.json()
                print(f"   Created foreign person ID: {result2.get('id')}")
                expiry = result2.get('aliases', [{}])[0].get('id_document_expiry_date')
                print(f"   ID expiry date: {expiry}")
            else:
                print(f"   ❌ Error: {response2.text}")
                
        else:
            print(f"   ❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Person creation failed: {e}")

def main():
    """Run all tests"""
    print("🚀 Testing Enhanced LINC Backend Features")
    print("=" * 50)
    
    test_lookup_endpoints()
    test_phone_validation()
    test_enhanced_person_creation()
    
    print("\n" + "=" * 50)
    print("✨ Testing Complete!")

if __name__ == "__main__":
    main() 