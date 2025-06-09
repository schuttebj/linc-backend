#!/usr/bin/env python3
"""
LINC Test Data Creation Script

This script creates sample test data for the LINC system including:
- Sample persons
- Test centers
- License applications
- Sample payments

Usage:
    python create_test_data.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime, date, timedelta
from decimal import Decimal
import uuid

# Add the app directory to the Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from app.core.database import get_db_context
from app.models.person import Person
from app.models.license import (
    LicenseApplication, 
    LicenseCard, 
    ApplicationPayment, 
    TestCenter,
    ApplicationStatus,
    LicenseType
)
from app.models.enums import Gender, ValidationStatus
import structlog

logger = structlog.get_logger()


def create_test_persons():
    """Create sample persons for testing"""
    test_persons = [
        {
            "id_type": "RSA_ID",
            "id_number": "9001015009087",
            "first_name": "John",
            "surname": "Smith",
            "date_of_birth": date(1990, 1, 1),
            "gender": Gender.MALE,
            "nationality": "ZA",
            "email": "john.smith@example.com",
            "phone_mobile": "+27821234567",
            "residential_address_line_1": "123 Main Street",
            "residential_city": "Cape Town",
            "residential_province": "Western Cape",
            "residential_postal_code": "8001",
            "country_code": "ZA"
        },
        {
            "id_type": "RSA_ID", 
            "id_number": "8505125008088",
            "first_name": "Sarah",
            "surname": "Johnson",
            "date_of_birth": date(1985, 5, 12),
            "gender": Gender.FEMALE,
            "nationality": "ZA",
            "email": "sarah.johnson@example.com",
            "phone_mobile": "+27827654321",
            "residential_address_line_1": "456 Oak Avenue",
            "residential_city": "Johannesburg",
            "residential_province": "Gauteng",
            "residential_postal_code": "2001",
            "country_code": "ZA"
        },
        {
            "id_type": "RSA_ID",
            "id_number": "7803201234567",
            "first_name": "Michael",
            "surname": "Brown",
            "date_of_birth": date(1978, 3, 20),
            "gender": Gender.MALE,
            "nationality": "ZA",
            "email": "michael.brown@example.com",
            "phone_mobile": "+27831234567",
            "residential_address_line_1": "789 Pine Road",
            "residential_city": "Durban",
            "residential_province": "KwaZulu-Natal",
            "residential_postal_code": "4001",
            "country_code": "ZA"
        }
    ]
    
    created_persons = []
    
    with get_db_context() as db:
        for person_data in test_persons:
            # Check if person already exists
            existing = db.query(Person).filter(
                Person.id_number == person_data["id_number"]
            ).first()
            
            if existing:
                logger.info(f"Person {person_data['id_number']} already exists, skipping")
                created_persons.append(existing)
                continue
            
            person = Person(
                **person_data,
                validation_status=ValidationStatus.VALIDATED,
                validation_date=datetime.utcnow(),
                is_active=True
            )
            
            db.add(person)
            created_persons.append(person)
            logger.info(f"Created person: {person.first_name} {person.surname}")
        
        db.commit()
    
    return created_persons


def create_test_centers():
    """Create sample test centers"""
    test_centers = [
        {
            "center_code": "CPT001",
            "center_name": "Cape Town Central Test Center",
            "address_line_1": "100 Government Avenue",
            "city": "Cape Town",
            "province": "Western Cape",
            "postal_code": "8001",
            "phone_number": "+27214567890",
            "email_address": "cpt.testing@linc.gov.za",
            "capacity_per_day": 100,
            "country_code": "ZA",
            "operating_hours": {
                "monday": "08:00-16:00",
                "tuesday": "08:00-16:00", 
                "wednesday": "08:00-16:00",
                "thursday": "08:00-16:00",
                "friday": "08:00-16:00",
                "saturday": "08:00-12:00",
                "sunday": "closed"
            },
            "test_types_supported": ["LEARNER", "DRIVING", "PROFESSIONAL"]
        },
        {
            "center_code": "JHB001",
            "center_name": "Johannesburg Main Test Center",
            "address_line_1": "200 Commissioner Street",
            "city": "Johannesburg",
            "province": "Gauteng",
            "postal_code": "2001",
            "phone_number": "+27115551234",
            "email_address": "jhb.testing@linc.gov.za",
            "capacity_per_day": 150,
            "country_code": "ZA",
            "operating_hours": {
                "monday": "07:30-16:30",
                "tuesday": "07:30-16:30",
                "wednesday": "07:30-16:30", 
                "thursday": "07:30-16:30",
                "friday": "07:30-16:30",
                "saturday": "08:00-13:00",
                "sunday": "closed"
            },
            "test_types_supported": ["LEARNER", "DRIVING", "PROFESSIONAL"]
        },
        {
            "center_code": "DBN001",
            "center_name": "Durban Coastal Test Center",
            "address_line_1": "300 Smith Street",
            "city": "Durban",
            "province": "KwaZulu-Natal",
            "postal_code": "4001",
            "phone_number": "+27315559876",
            "email_address": "dbn.testing@linc.gov.za",
            "capacity_per_day": 80,
            "country_code": "ZA",
            "operating_hours": {
                "monday": "08:00-16:00",
                "tuesday": "08:00-16:00",
                "wednesday": "08:00-16:00",
                "thursday": "08:00-16:00",
                "friday": "08:00-16:00",
                "saturday": "08:00-12:00",
                "sunday": "closed"
            },
            "test_types_supported": ["LEARNER", "DRIVING", "PROFESSIONAL"]
        }
    ]
    
    created_centers = []
    
    with get_db_context() as db:
        for center_data in test_centers:
            # Check if center already exists
            existing = db.query(TestCenter).filter(
                TestCenter.center_code == center_data["center_code"]
            ).first()
            
            if existing:
                logger.info(f"Test center {center_data['center_code']} already exists, skipping")
                created_centers.append(existing)
                continue
            
            center = TestCenter(
                **center_data,
                is_active=True,
                created_by=str(uuid.uuid4()),
                updated_by=str(uuid.uuid4())
            )
            
            db.add(center)
            created_centers.append(center)
            logger.info(f"Created test center: {center.center_name}")
        
        db.commit()
    
    return created_centers


def create_test_applications(persons, test_centers):
    """Create sample license applications"""
    if not persons or not test_centers:
        logger.warning("No persons or test centers available for creating applications")
        return []
    
    # Create applications for each person
    applications_data = [
        {
            "person": persons[0],  # John Smith
            "license_type": LicenseType.LEARNER_B,
            "application_type": "NEW",
            "status": ApplicationStatus.SUBMITTED,
            "test_center": test_centers[0]  # Cape Town
        },
        {
            "person": persons[1],  # Sarah Johnson
            "license_type": LicenseType.B,
            "application_type": "NEW", 
            "status": ApplicationStatus.APPROVED,
            "test_center": test_centers[1]  # Johannesburg
        },
        {
            "person": persons[2],  # Michael Brown
            "license_type": LicenseType.C,
            "application_type": "UPGRADE",
            "status": ApplicationStatus.UNDER_REVIEW,
            "test_center": test_centers[2]  # Durban
        }
    ]
    
    created_applications = []
    
    with get_db_context() as db:
        for i, app_data in enumerate(applications_data):
            # Generate application number
            year = datetime.now().year
            app_number = f"ZA{year}{i+1:06d}"
            
            # Calculate fees based on license type
            fee_map = {
                LicenseType.LEARNER_B: Decimal("50.00"),
                LicenseType.B: Decimal("200.00"),
                LicenseType.C: Decimal("400.00")
            }
            
            total_fees = fee_map.get(app_data["license_type"], Decimal("200.00"))
            
            application = LicenseApplication(
                application_number=app_number,
                person_id=app_data["person"].id,
                license_type=app_data["license_type"],
                application_type=app_data["application_type"],
                status=app_data["status"],
                test_required=True,
                medical_required=app_data["license_type"] in [LicenseType.C],
                age_verified=True,
                outstanding_fees_cleared=True,
                suspension_check_passed=True,
                total_fees=total_fees,
                fees_paid=total_fees if app_data["status"] in [ApplicationStatus.APPROVED] else Decimal("0.00"),
                processing_location_id=app_data["test_center"].id,
                test_center_id=app_data["test_center"].id,
                validation_codes=["V00874", "V00880"],
                business_rules_applied=["R-APP-003", "R-APP-005"],
                country_code="ZA",
                created_by=str(uuid.uuid4()),
                updated_by=str(uuid.uuid4())
            )
            
            # Set dates based on status
            if app_data["status"] in [ApplicationStatus.SUBMITTED, ApplicationStatus.UNDER_REVIEW, ApplicationStatus.APPROVED]:
                application.submitted_date = datetime.utcnow() - timedelta(days=i+1)
            
            if app_data["status"] == ApplicationStatus.APPROVED:
                application.approved_date = datetime.utcnow() - timedelta(hours=i+1)
                application.test_result = "PASS"
                application.test_score = 85 + i
            
            db.add(application)
            created_applications.append(application)
            logger.info(f"Created application: {app_number} for {app_data['person'].first_name} {app_data['person'].surname}")
        
        db.commit()
    
    return created_applications


def create_test_payments(applications):
    """Create sample payments for applications"""
    if not applications:
        logger.warning("No applications available for creating payments")
        return []
    
    created_payments = []
    
    with get_db_context() as db:
        for i, application in enumerate(applications):
            if application.fees_paid > 0:  # Only create payments for paid applications
                payment_ref = f"PAY{datetime.now().year}{i+1:06d}"
                
                payment = ApplicationPayment(
                    payment_reference=payment_ref,
                    application_id=application.id,
                    amount=application.total_fees,
                    payment_method="CARD",
                    payment_status="CONFIRMED",
                    processed_date=datetime.utcnow() - timedelta(hours=i+1),
                    processor_reference=f"BANK_REF_{i+1:06d}",
                    fee_breakdown={
                        "base_fee": float(application.total_fees * Decimal("0.9")),
                        "processing_fee": float(application.total_fees * Decimal("0.1"))
                    },
                    country_code="ZA",
                    created_by=str(uuid.uuid4()),
                    updated_by=str(uuid.uuid4())
                )
                
                db.add(payment)
                created_payments.append(payment)
                logger.info(f"Created payment: {payment_ref} for application {application.application_number}")
        
        db.commit()
    
    return created_payments


def main():
    """Create all test data"""
    try:
        logger.info("Starting test data creation...")
        
        # Create test persons
        logger.info("Creating test persons...")
        persons = create_test_persons()
        logger.info(f"Created {len(persons)} persons")
        
        # Create test centers
        logger.info("Creating test centers...")
        test_centers = create_test_centers()
        logger.info(f"Created {len(test_centers)} test centers")
        
        # Create test applications
        logger.info("Creating test applications...")
        applications = create_test_applications(persons, test_centers)
        logger.info(f"Created {len(applications)} applications")
        
        # Create test payments
        logger.info("Creating test payments...")
        payments = create_test_payments(applications)
        logger.info(f"Created {len(payments)} payments")
        
        print("\n✅ Test data created successfully!")
        print(f"\nCreated:")
        print(f"- {len(persons)} test persons")
        print(f"- {len(test_centers)} test centers")
        print(f"- {len(applications)} license applications")
        print(f"- {len(payments)} payments")
        
        print("\nSample data includes:")
        print("- John Smith (Learner's license application)")
        print("- Sarah Johnson (Full license - approved)")
        print("- Michael Brown (Heavy vehicle upgrade)")
        
        print("\nYou can now:")
        print("1. Start the server: uvicorn app.main:app --reload")
        print("2. View API docs: http://localhost:8000/docs")
        print("3. Test the license application endpoints")
        
    except Exception as e:
        logger.error(f"Failed to create test data: {e}")
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
