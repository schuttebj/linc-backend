from pydantic import BaseModel, Field, field_validator, root_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
import uuid

from ..models.license import ApplicationStatus, LicenseType


class LicenseApplicationBase(BaseModel):
    """Base schema for License Application"""
    license_type: LicenseType = Field(..., description="Type of license being applied for")
    application_type: str = Field(..., description="NEW, RENEWAL, UPGRADE, DUPLICATE")
    test_required: bool = Field(True, description="Whether a test is required")
    medical_required: bool = Field(False, description="Whether medical certificate is required")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    @field_validator('application_type')
    @classmethod
    def validate_application_type(cls, v):
        valid_types = ['NEW', 'RENEWAL', 'UPGRADE', 'DUPLICATE']
        if v not in valid_types:
            raise ValueError(f'Application type must be one of: {valid_types}')
        return v


class LicenseApplicationCreate(LicenseApplicationBase):
    """Schema for creating a new license application"""
    person_id: str = Field(..., description="UUID of the person applying")
    processing_location_id: str = Field(..., description="UUID of processing location")
    country_code: str = Field(..., description="Country code for this application")
    
    # Optional fields for creation
    test_center_id: Optional[str] = Field(None, description="Preferred test center UUID")
    medical_certificate_number: Optional[str] = Field(None, description="Medical certificate number if available")
    medical_certificate_date: Optional[date] = Field(None, description="Medical certificate date")
    
    @field_validator('country_code')
    @classmethod
    def validate_country_code(cls, v):
        if len(v) != 2:
            raise ValueError('Country code must be 2 characters')
        return v.upper()


class LicenseApplicationUpdate(BaseModel):
    """Schema for updating a license application"""
    status: Optional[ApplicationStatus] = Field(None, description="Application status")
    test_date: Optional[datetime] = Field(None, description="Scheduled test date")
    test_center_id: Optional[str] = Field(None, description="Test center UUID")
    test_result: Optional[str] = Field(None, description="PASS, FAIL, PENDING")
    test_score: Optional[int] = Field(None, description="Test score")
    medical_certificate_number: Optional[str] = Field(None, description="Medical certificate number")
    medical_certificate_date: Optional[date] = Field(None, description="Medical certificate date")
    medical_practitioner_id: Optional[str] = Field(None, description="Medical practitioner UUID")
    examiner_id: Optional[str] = Field(None, description="Examiner UUID")
    approver_id: Optional[str] = Field(None, description="Approver UUID")
    notes: Optional[str] = Field(None, description="Additional notes")
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection")
    
    @field_validator('test_result')
    @classmethod
    def validate_test_result(cls, v):
        if v is not None:
            valid_results = ['PASS', 'FAIL', 'PENDING']
            if v not in valid_results:
                raise ValueError(f'Test result must be one of: {valid_results}')
        return v
    
    @field_validator('test_score')
    @classmethod
    def validate_test_score(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Test score must be between 0 and 100')
        return v


class LicenseApplicationResponse(LicenseApplicationBase):
    """Schema for license application response"""
    id: str = Field(..., description="Application UUID")
    application_number: str = Field(..., description="Unique application number")
    person_id: str = Field(..., description="Person UUID")
    status: ApplicationStatus = Field(..., description="Current application status")
    
    # Dates
    application_date: datetime = Field(..., description="Application submission date")
    submitted_date: Optional[datetime] = Field(None, description="Date when submitted for processing")
    approved_date: Optional[datetime] = Field(None, description="Date when approved")
    expiry_date: Optional[datetime] = Field(None, description="License expiry date")
    
    # Test information
    test_date: Optional[datetime] = Field(None, description="Scheduled test date")
    test_center_id: Optional[str] = Field(None, description="Test center UUID")
    test_result: Optional[str] = Field(None, description="Test result")
    test_score: Optional[int] = Field(None, description="Test score")
    
    # Medical information
    medical_certificate_date: Optional[date] = Field(None, description="Medical certificate date")
    medical_certificate_number: Optional[str] = Field(None, description="Medical certificate number")
    
    # Prerequisites and validations
    prerequisite_license_id: Optional[str] = Field(None, description="Required prerequisite license UUID")
    age_verified: bool = Field(..., description="Age eligibility verified")
    outstanding_fees_cleared: bool = Field(..., description="Outstanding fees cleared")
    suspension_check_passed: bool = Field(..., description="Suspension check passed")
    
    # Financial information
    total_fees: Decimal = Field(..., description="Total fees for application")
    fees_paid: Decimal = Field(..., description="Amount paid")
    payment_reference: Optional[str] = Field(None, description="Payment reference number")
    
    # Card production
    card_ordered: bool = Field(..., description="Card ordered for production")
    card_order_date: Optional[datetime] = Field(None, description="Card order date")
    card_production_date: Optional[datetime] = Field(None, description="Card production date")
    card_collection_date: Optional[datetime] = Field(None, description="Card collection date")
    
    # Processing information
    processing_location_id: str = Field(..., description="Processing location UUID")
    examiner_id: Optional[str] = Field(None, description="Examiner UUID")
    approver_id: Optional[str] = Field(None, description="Approver UUID")
    
    # Validation tracking
    validation_codes: Optional[List[str]] = Field(None, description="Applied validation codes")
    business_rules_applied: Optional[List[str]] = Field(None, description="Applied business rules")
    
    # Country configuration
    country_code: str = Field(..., description="Country code")
    
    # Audit fields
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class LicenseCardBase(BaseModel):
    """Base schema for License Card"""
    license_type: LicenseType = Field(..., description="License type")
    card_type: str = Field("STANDARD", description="STANDARD, DUPLICATE, REPLACEMENT")
    card_template: str = Field("ISO_18013", description="Card template standard")
    
    @field_validator('card_type')
    @classmethod
    def validate_card_type(cls, v):
        valid_types = ['STANDARD', 'DUPLICATE', 'REPLACEMENT']
        if v not in valid_types:
            raise ValueError(f'Card type must be one of: {valid_types}')
        return v


class LicenseCardCreate(LicenseCardBase):
    """Schema for creating a license card"""
    application_id: str = Field(..., description="Application UUID")
    person_id: str = Field(..., description="Person UUID")
    expiry_date: datetime = Field(..., description="Card expiry date")
    image_handle: str = Field(..., description="Image handle for card photo")
    country_code: str = Field(..., description="Country code")
    replacement_reason: Optional[str] = Field(None, description="Reason for replacement if applicable")


class LicenseCardResponse(LicenseCardBase):
    """Schema for license card response"""
    id: str = Field(..., description="Card UUID")
    card_number: str = Field(..., description="Unique card number")
    application_id: str = Field(..., description="Application UUID")
    person_id: str = Field(..., description="Person UUID")
    
    # Validity
    issue_date: datetime = Field(..., description="Card issue date")
    expiry_date: datetime = Field(..., description="Card expiry date")
    valid_from: datetime = Field(..., description="Valid from date")
    
    # Production information
    production_status: str = Field(..., description="Production status")
    production_date: Optional[datetime] = Field(None, description="Production date")
    production_location: Optional[str] = Field(None, description="Production location")
    dispatch_date: Optional[datetime] = Field(None, description="Dispatch date")
    collection_date: Optional[datetime] = Field(None, description="Collection date")
    
    # Card specifications
    image_handle: str = Field(..., description="Image handle")
    security_features: Optional[Dict[str, Any]] = Field(None, description="Security features")
    
    # File storage
    card_file_path: Optional[str] = Field(None, description="Card file path")
    card_file_id: Optional[str] = Field(None, description="Card file ID")
    
    # Status tracking
    is_active: bool = Field(..., description="Active status")
    is_collected: bool = Field(..., description="Collection status")
    replacement_reason: Optional[str] = Field(None, description="Replacement reason")
    
    # Country configuration
    country_code: str = Field(..., description="Country code")
    
    # Audit fields
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class ApplicationPaymentBase(BaseModel):
    """Base schema for Application Payment"""
    amount: Decimal = Field(..., description="Payment amount", gt=0)
    payment_method: str = Field(..., description="CASH, CARD, BANK_TRANSFER")
    
    @field_validator('payment_method')
    @classmethod
    def validate_payment_method(cls, v):
        valid_methods = ['CASH', 'CARD', 'BANK_TRANSFER']
        if v not in valid_methods:
            raise ValueError(f'Payment method must be one of: {valid_methods}')
        return v


class ApplicationPaymentCreate(ApplicationPaymentBase):
    """Schema for creating an application payment"""
    application_id: str = Field(..., description="Application UUID")
    country_code: str = Field(..., description="Country code")
    fee_breakdown: Optional[Dict[str, Any]] = Field(None, description="Fee breakdown details")


class ApplicationPaymentResponse(ApplicationPaymentBase):
    """Schema for application payment response"""
    id: str = Field(..., description="Payment UUID")
    payment_reference: str = Field(..., description="Unique payment reference")
    application_id: str = Field(..., description="Application UUID")
    payment_status: str = Field(..., description="Payment status")
    
    # Payment processing
    payment_date: datetime = Field(..., description="Payment date")
    processed_date: Optional[datetime] = Field(None, description="Processing date")
    processor_reference: Optional[str] = Field(None, description="Processor reference")
    
    # Fee breakdown
    fee_breakdown: Optional[Dict[str, Any]] = Field(None, description="Fee breakdown")
    
    # Country configuration
    country_code: str = Field(..., description="Country code")
    
    # Audit fields
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class TestCenterBase(BaseModel):
    """Base schema for Test Center"""
    center_name: str = Field(..., description="Test center name")
    address_line_1: str = Field(..., description="Address line 1")
    address_line_2: Optional[str] = Field(None, description="Address line 2")
    city: str = Field(..., description="City")
    province: str = Field(..., description="Province/State")
    postal_code: str = Field(..., description="Postal code")
    phone_number: Optional[str] = Field(None, description="Phone number")
    email_address: Optional[str] = Field(None, description="Email address")
    capacity_per_day: int = Field(50, description="Daily testing capacity", gt=0)


class TestCenterCreate(TestCenterBase):
    """Schema for creating a test center"""
    center_code: str = Field(..., description="Unique center code")
    country_code: str = Field(..., description="Country code")
    operating_hours: Optional[Dict[str, Any]] = Field(None, description="Operating hours")
    test_types_supported: Optional[List[str]] = Field(None, description="Supported test types")


class TestCenterResponse(TestCenterBase):
    """Schema for test center response"""
    id: str = Field(..., description="Test center UUID")
    center_code: str = Field(..., description="Center code")
    is_active: bool = Field(..., description="Active status")
    operating_hours: Optional[Dict[str, Any]] = Field(None, description="Operating hours")
    test_types_supported: Optional[List[str]] = Field(None, description="Supported test types")
    country_code: str = Field(..., description="Country code")
    
    # Audit fields
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class LicenseApplicationValidation(BaseModel):
    """Schema for license application validation results"""
    is_valid: bool = Field(..., description="Overall validation result")
    validation_codes: List[str] = Field(..., description="Applied validation codes")
    business_rules: List[str] = Field(..., description="Applied business rules")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    
    # Specific validation results
    age_eligible: bool = Field(..., description="Age eligibility check result")
    prerequisites_met: bool = Field(..., description="Prerequisites check result")
    outstanding_fees_cleared: bool = Field(..., description="Outstanding fees check result")
    suspension_check_passed: bool = Field(..., description="Suspension check result")
    medical_requirements_met: bool = Field(..., description="Medical requirements check result")


class LicenseApplicationSummary(BaseModel):
    """Summary schema for license application lists"""
    id: str = Field(..., description="Application UUID")
    application_number: str = Field(..., description="Application number")
    person_name: str = Field(..., description="Applicant name")
    license_type: LicenseType = Field(..., description="License type")
    status: ApplicationStatus = Field(..., description="Application status")
    application_date: datetime = Field(..., description="Application date")
    total_fees: Decimal = Field(..., description="Total fees")
    fees_paid: Decimal = Field(..., description="Fees paid")
    
    class Config:
        from_attributes = True 