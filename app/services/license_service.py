from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import uuid

from ..models.license import (
    LicenseApplication, 
    LicenseCard, 
    ApplicationPayment, 
    TestCenter,
    ApplicationStatus,
    LicenseType
)
from ..models.person import PersonModel
from ..schemas.license import (
    LicenseApplicationCreate,
    LicenseApplicationUpdate,
    LicenseApplicationValidation,
    LicenseCardCreate,
    ApplicationPaymentCreate
)
from .validation_service import ValidationService
from .person_service import PersonService


class LicenseApplicationService:
    """
    License Application Service implementing business rules from documentation
    Reference: Section 2.1 License Application Form
    Business Rules: R-APP-001 to R-APP-009
    """
    
    def __init__(self, db: Session, country_code: str):
        self.db = db
        self.country_code = country_code
        self.validation_service = ValidationService(db, country_code)
        self.person_service = PersonService(db, country_code)
    
    def create_application(
        self, 
        application_data: LicenseApplicationCreate,
        created_by: str
    ) -> Tuple[LicenseApplication, LicenseApplicationValidation]:
        """
        Create a new license application with comprehensive validation
        
        Business Rules Applied:
        - R-APP-001: Application State Management
        - R-APP-002: Duplicate Application Prevention
        - R-APP-003: Age Eligibility Check
        - R-APP-004: Medical Certificate Requirements
        - R-APP-005: Prerequisite License Check
        - R-APP-006: Outstanding Fees Check
        - R-APP-007: Suspension History Check
        - R-APP-008: Blacklist Check
        """
        
        # Step 1: Validate the application
        validation_result = self.validate_application(application_data)
        
        if not validation_result.is_valid:
            raise ValueError(f"Application validation failed: {validation_result.errors}")
        
        # Step 2: Check for duplicate applications (R-APP-002)
        existing_application = self.db.query(LicenseApplication).filter(
            and_(
                LicenseApplication.person_id == application_data.person_id,
                LicenseApplication.license_type == application_data.license_type,
                LicenseApplication.status.in_([
                    ApplicationStatus.DRAFT,
                    ApplicationStatus.SUBMITTED,
                    ApplicationStatus.UNDER_REVIEW,
                    ApplicationStatus.PAYMENT_PENDING,
                    ApplicationStatus.PAYMENT_CONFIRMED,
                    ApplicationStatus.APPROVED
                ])
            )
        ).first()
        
        if existing_application:
            raise ValueError(f"Active application already exists: {existing_application.application_number}")
        
        # Step 3: Generate application number
        application_number = self._generate_application_number()
        
        # Step 4: Calculate fees
        total_fees = self._calculate_application_fees(
            application_data.license_type,
            application_data.application_type
        )
        
        # Step 5: Determine prerequisite license
        prerequisite_license_id = self._get_prerequisite_license(
            application_data.person_id,
            application_data.license_type
        )
        
        # Step 6: Create the application
        application = LicenseApplication(
            application_number=application_number,
            person_id=application_data.person_id,
            license_type=application_data.license_type,
            application_type=application_data.application_type,
            status=ApplicationStatus.DRAFT,
            test_required=application_data.test_required,
            medical_required=application_data.medical_required,
            prerequisite_license_id=prerequisite_license_id,
            age_verified=validation_result.age_eligible,
            outstanding_fees_cleared=validation_result.outstanding_fees_cleared,
            suspension_check_passed=validation_result.suspension_check_passed,
            total_fees=total_fees,
            processing_location_id=application_data.processing_location_id,
            test_center_id=application_data.test_center_id,
            medical_certificate_number=application_data.medical_certificate_number,
            medical_certificate_date=application_data.medical_certificate_date,
            validation_codes=validation_result.validation_codes,
            business_rules_applied=validation_result.business_rules,
            notes=application_data.notes,
            country_code=self.country_code,
            created_by=created_by,
            updated_by=created_by
        )
        
        self.db.add(application)
        self.db.commit()
        self.db.refresh(application)
        
        return application, validation_result
    
    def validate_application(self, application_data: LicenseApplicationCreate) -> LicenseApplicationValidation:
        """
        Comprehensive application validation implementing all business rules
        """
        validation_codes = []
        business_rules = []
        errors = []
        warnings = []
        
        # Get person details
        person = self.person_service.get_person_by_id(application_data.person_id)
        if not person:
            errors.append("Person not found")
            return LicenseApplicationValidation(
                is_valid=False,
                validation_codes=["V00014"],
                business_rules=["R-ID-006"],
                errors=errors,
                warnings=warnings,
                age_eligible=False,
                prerequisites_met=False,
                outstanding_fees_cleared=False,
                suspension_check_passed=False,
                medical_requirements_met=False
            )
        
        # R-APP-003: Age Eligibility Check
        age_eligible, age_validation = self._check_age_eligibility(person, application_data.license_type)
        validation_codes.extend(age_validation.get("codes", []))
        business_rules.append("R-APP-003")
        
        if not age_eligible:
            errors.extend(age_validation.get("errors", []))
        
        # R-APP-005: Prerequisite License Check
        prerequisites_met, prereq_validation = self._check_prerequisites(
            application_data.person_id, 
            application_data.license_type
        )
        validation_codes.extend(prereq_validation.get("codes", []))
        business_rules.append("R-APP-005")
        
        if not prerequisites_met:
            errors.extend(prereq_validation.get("errors", []))
        
        # R-APP-006: Outstanding Fees Check
        outstanding_fees_cleared, fees_validation = self._check_outstanding_fees(application_data.person_id)
        validation_codes.extend(fees_validation.get("codes", []))
        business_rules.append("R-APP-006")
        
        if not outstanding_fees_cleared:
            warnings.extend(fees_validation.get("warnings", []))
        
        # R-APP-007: Suspension History Check
        suspension_check_passed, suspension_validation = self._check_suspension_history(application_data.person_id)
        validation_codes.extend(suspension_validation.get("codes", []))
        business_rules.append("R-APP-007")
        
        if not suspension_check_passed:
            errors.extend(suspension_validation.get("errors", []))
        
        # R-APP-004: Medical Certificate Requirements
        medical_requirements_met, medical_validation = self._check_medical_requirements(
            person, 
            application_data.license_type,
            application_data.medical_certificate_date
        )
        validation_codes.extend(medical_validation.get("codes", []))
        business_rules.append("R-APP-004")
        
        if not medical_requirements_met:
            if medical_validation.get("required", False):
                errors.extend(medical_validation.get("errors", []))
            else:
                warnings.extend(medical_validation.get("warnings", []))
        
        # R-APP-008: Blacklist Check (placeholder - would integrate with external system)
        blacklist_check_passed = True  # Implement actual blacklist check
        business_rules.append("R-APP-008")
        
        is_valid = (
            age_eligible and 
            prerequisites_met and 
            suspension_check_passed and 
            blacklist_check_passed and
            (medical_requirements_met or not medical_validation.get("required", False))
        )
        
        return LicenseApplicationValidation(
            is_valid=is_valid,
            validation_codes=list(set(validation_codes)),
            business_rules=list(set(business_rules)),
            errors=errors,
            warnings=warnings,
            age_eligible=age_eligible,
            prerequisites_met=prerequisites_met,
            outstanding_fees_cleared=outstanding_fees_cleared,
            suspension_check_passed=suspension_check_passed,
            medical_requirements_met=medical_requirements_met
        )
    
    def _check_age_eligibility(self, person: PersonModel, license_type: LicenseType) -> Tuple[bool, Dict]:
        """
        Check age eligibility based on license type
        Business Rule: R-APP-003
        """
        if not person.date_of_birth:
            return False, {
                "codes": ["V00065"],
                "errors": ["Date of birth is required for age verification"]
            }
        
        age = (datetime.now().date() - person.date_of_birth).days // 365
        
        # Age requirements by license type
        age_requirements = {
            LicenseType.LEARNER_A: 16,
            LicenseType.LEARNER_B: 16,
            LicenseType.A: 16,
            LicenseType.B: 18,
            LicenseType.C1: 18,
            LicenseType.C: 21,
            LicenseType.D1: 21,
            LicenseType.D: 24,
            LicenseType.EB: 21,
            LicenseType.EC1: 21,
            LicenseType.EC: 21
        }
        
        required_age = age_requirements.get(license_type, 18)
        
        if age < required_age:
            return False, {
                "codes": ["V00874"],
                "errors": [f"Applicant must be at least {required_age} years old for {license_type.value} license"]
            }
        
        return True, {"codes": ["V00874"]}
    
    def _check_prerequisites(self, person_id: str, license_type: LicenseType) -> Tuple[bool, Dict]:
        """
        Check prerequisite license requirements
        Business Rule: R-APP-005
        """
        # Define prerequisite requirements
        prerequisites = {
            LicenseType.C: [LicenseType.B],
            LicenseType.D: [LicenseType.C, LicenseType.B],
            LicenseType.EB: [LicenseType.C, LicenseType.B],
            LicenseType.EC1: [LicenseType.C1, LicenseType.B],
            LicenseType.EC: [LicenseType.C, LicenseType.B]
        }
        
        required_licenses = prerequisites.get(license_type, [])
        
        if not required_licenses:
            return True, {"codes": []}
        
        # Check if person has any of the required prerequisite licenses
        existing_licenses = self.db.query(LicenseApplication).filter(
            and_(
                LicenseApplication.person_id == person_id,
                LicenseApplication.license_type.in_(required_licenses),
                LicenseApplication.status == ApplicationStatus.LICENSE_ISSUED
            )
        ).all()
        
        if not existing_licenses:
            return False, {
                "codes": ["V00880"],
                "errors": [f"Prerequisite license required: {' or '.join([l.value for l in required_licenses])}"]
            }
        
        return True, {"codes": ["V00880"]}
    
    def _check_outstanding_fees(self, person_id: str) -> Tuple[bool, Dict]:
        """
        Check for outstanding fees
        Business Rule: R-APP-006
        """
        # Check for unpaid applications
        outstanding_applications = self.db.query(LicenseApplication).filter(
            and_(
                LicenseApplication.person_id == person_id,
                LicenseApplication.total_fees > LicenseApplication.fees_paid
            )
        ).count()
        
        if outstanding_applications > 0:
            return False, {
                "codes": ["V01882"],
                "warnings": ["Outstanding fees must be paid before new application"]
            }
        
        return True, {"codes": []}
    
    def _check_suspension_history(self, person_id: str) -> Tuple[bool, Dict]:
        """
        Check for active license suspensions
        Business Rule: R-APP-007
        """
        # This would integrate with suspension management system
        # For now, return True (no suspensions)
        return True, {"codes": []}
    
    def _check_medical_requirements(
        self, 
        person: PersonModel, 
        license_type: LicenseType,
        medical_cert_date: Optional[date]
    ) -> Tuple[bool, Dict]:
        """
        Check medical certificate requirements
        Business Rule: R-APP-004
        """
        age = (datetime.now().date() - person.date_of_birth).days // 365 if person.date_of_birth else 0
        
        # Medical requirements
        professional_licenses = [LicenseType.C, LicenseType.C1, LicenseType.D, LicenseType.D1, LicenseType.EB, LicenseType.EC, LicenseType.EC1]
        
        medical_required = (
            age > 60 or 
            license_type in professional_licenses
        )
        
        if not medical_required:
            return True, {"codes": [], "required": False}
        
        if not medical_cert_date:
            return False, {
                "codes": ["V00013"],
                "errors": ["Medical certificate is required"],
                "required": True
            }
        
        # Check if medical certificate is still valid (6 months)
        if medical_cert_date < (datetime.now().date() - timedelta(days=180)):
            return False, {
                "codes": ["V00013"],
                "errors": ["Medical certificate has expired (must be within 6 months)"],
                "required": True
            }
        
        return True, {"codes": [], "required": True}
    
    def _calculate_application_fees(self, license_type: LicenseType, application_type: str) -> Decimal:
        """
        Calculate application fees based on license type and application type
        Reference: Section 4.1 Fee Calculation System
        """
        # Base fees by license type (example values - would be configurable)
        base_fees = {
            LicenseType.LEARNER_A: Decimal("50.00"),
            LicenseType.LEARNER_B: Decimal("50.00"),
            LicenseType.A: Decimal("150.00"),
            LicenseType.B: Decimal("200.00"),
            LicenseType.C1: Decimal("300.00"),
            LicenseType.C: Decimal("400.00"),
            LicenseType.D1: Decimal("350.00"),
            LicenseType.D: Decimal("450.00"),
            LicenseType.EB: Decimal("500.00"),
            LicenseType.EC1: Decimal("400.00"),
            LicenseType.EC: Decimal("500.00")
        }
        
        base_fee = base_fees.get(license_type, Decimal("200.00"))
        
        # Application type multipliers
        multipliers = {
            "NEW": Decimal("1.0"),
            "RENEWAL": Decimal("0.8"),
            "UPGRADE": Decimal("1.2"),
            "DUPLICATE": Decimal("0.5")
        }
        
        multiplier = multipliers.get(application_type, Decimal("1.0"))
        
        return base_fee * multiplier
    
    def _get_prerequisite_license(self, person_id: str, license_type: LicenseType) -> Optional[str]:
        """
        Get the prerequisite license ID if applicable
        """
        prerequisites = {
            LicenseType.C: [LicenseType.B],
            LicenseType.D: [LicenseType.C, LicenseType.B],
            LicenseType.EB: [LicenseType.C, LicenseType.B],
            LicenseType.EC1: [LicenseType.C1, LicenseType.B],
            LicenseType.EC: [LicenseType.C, LicenseType.B]
        }
        
        required_licenses = prerequisites.get(license_type, [])
        
        if not required_licenses:
            return None
        
        # Find the highest level prerequisite license
        prerequisite_license = self.db.query(LicenseApplication).filter(
            and_(
                LicenseApplication.person_id == person_id,
                LicenseApplication.license_type.in_(required_licenses),
                LicenseApplication.status == ApplicationStatus.LICENSE_ISSUED
            )
        ).first()
        
        return str(prerequisite_license.id) if prerequisite_license else None
    
    def _generate_application_number(self) -> str:
        """
        Generate unique application number
        Format: {COUNTRY_CODE}{YEAR}{SEQUENCE}
        """
        year = datetime.now().year
        
        # Get the next sequence number for this year
        last_application = self.db.query(LicenseApplication).filter(
            LicenseApplication.application_number.like(f"{self.country_code}{year}%")
        ).order_by(LicenseApplication.application_number.desc()).first()
        
        if last_application:
            last_sequence = int(last_application.application_number[-6:])
            sequence = last_sequence + 1
        else:
            sequence = 1
        
        return f"{self.country_code}{year}{sequence:06d}"
    
    def update_application(
        self, 
        application_id: str, 
        update_data: LicenseApplicationUpdate,
        updated_by: str
    ) -> LicenseApplication:
        """
        Update an existing license application
        """
        application = self.db.query(LicenseApplication).filter(
            LicenseApplication.id == application_id
        ).first()
        
        if not application:
            raise ValueError("Application not found")
        
        # Update fields
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(application, field, value)
        
        application.updated_by = updated_by
        application.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(application)
        
        return application
    
    def get_application_by_id(self, application_id: str) -> Optional[LicenseApplication]:
        """Get application by ID"""
        return self.db.query(LicenseApplication).filter(
            LicenseApplication.id == application_id
        ).first()
    
    def get_applications_by_person(self, person_id: str) -> List[LicenseApplication]:
        """Get all applications for a person"""
        return self.db.query(LicenseApplication).filter(
            LicenseApplication.person_id == person_id
        ).order_by(LicenseApplication.application_date.desc()).all()
    
    def get_applications_by_status(self, status: ApplicationStatus) -> List[LicenseApplication]:
        """Get applications by status"""
        return self.db.query(LicenseApplication).filter(
            and_(
                LicenseApplication.status == status,
                LicenseApplication.country_code == self.country_code
            )
        ).order_by(LicenseApplication.application_date.desc()).all()
    
    def submit_application(self, application_id: str, submitted_by: str) -> LicenseApplication:
        """
        Submit application for processing
        Business Rule: R-APP-001 (State Transition)
        """
        application = self.get_application_by_id(application_id)
        
        if not application:
            raise ValueError("Application not found")
        
        if application.status != ApplicationStatus.DRAFT:
            raise ValueError("Only draft applications can be submitted")
        
        # Validate application before submission
        validation_result = self.validate_application(
            LicenseApplicationCreate(
                person_id=str(application.person_id),
                license_type=application.license_type,
                application_type=application.application_type,
                processing_location_id=str(application.processing_location_id),
                country_code=application.country_code,
                test_required=application.test_required,
                medical_required=application.medical_required,
                notes=application.notes
            )
        )
        
        if not validation_result.is_valid:
            raise ValueError(f"Application validation failed: {validation_result.errors}")
        
        # Update status and submission date
        application.status = ApplicationStatus.SUBMITTED
        application.submitted_date = datetime.utcnow()
        application.updated_by = submitted_by
        application.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(application)
        
        return application 