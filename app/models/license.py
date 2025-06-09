from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, ForeignKey, Enum as SQLEnum, Numeric, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime
from enum import Enum

from .base import BaseModel


class ApplicationStatus(str, Enum):
    """Application status enumeration based on R-APP-001"""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAYMENT_CONFIRMED = "PAYMENT_CONFIRMED"
    APPROVED = "APPROVED"
    LICENSE_PRODUCED = "LICENSE_PRODUCED"
    LICENSE_ISSUED = "LICENSE_ISSUED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class LicenseType(str, Enum):
    """License type enumeration"""
    LEARNER_A = "A1"  # Learner - Motorcycle
    LEARNER_B = "B1"  # Learner - Light Motor Vehicle
    A = "A"           # Motorcycle
    B = "B"           # Light Motor Vehicle
    C1 = "C1"         # Heavy Motor Vehicle (3500-16000kg)
    C = "C"           # Heavy Motor Vehicle (>16000kg)
    D1 = "D1"         # Minibus (8-16 passengers)
    D = "D"           # Bus (>16 passengers)
    EB = "EB"         # Articulated Heavy Motor Vehicle
    EC1 = "EC1"       # Heavy Motor Vehicle with trailer
    EC = "EC"         # Heavy Motor Vehicle with heavy trailer


class LicenseApplication(BaseModel):
    """
    License Application entity
    Reference: Section 2.1 License Application Form
    Business Rules: R-APP-001 to R-APP-009
    """
    __tablename__ = "license_applications"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_number = Column(String(20), unique=True, nullable=False, index=True)
    
    # Person reference
    person_id = Column(UUID(as_uuid=True), ForeignKey("person_entities.id"), nullable=False)
    
    # Application details
    license_type = Column(SQLEnum(LicenseType), nullable=False)
    application_type = Column(String(20), nullable=False)  # NEW, RENEWAL, UPGRADE, DUPLICATE
    status = Column(SQLEnum(ApplicationStatus), nullable=False, default=ApplicationStatus.DRAFT)
    
    # Dates
    application_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    submitted_date = Column(DateTime, nullable=True)
    approved_date = Column(DateTime, nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    
    # Test information
    test_required = Column(Boolean, nullable=False, default=True)
    test_date = Column(DateTime, nullable=True)
    test_center_id = Column(UUID(as_uuid=True), nullable=True)
    test_result = Column(String(10), nullable=True)  # PASS, FAIL, PENDING
    test_score = Column(Integer, nullable=True)
    
    # Medical requirements
    medical_required = Column(Boolean, nullable=False, default=False)
    medical_certificate_date = Column(DateTime, nullable=True)
    medical_certificate_number = Column(String(50), nullable=True)
    medical_practitioner_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Prerequisites and validations
    prerequisite_license_id = Column(UUID(as_uuid=True), nullable=True)
    age_verified = Column(Boolean, nullable=False, default=False)
    outstanding_fees_cleared = Column(Boolean, nullable=False, default=False)
    suspension_check_passed = Column(Boolean, nullable=False, default=False)
    
    # Financial information
    total_fees = Column(Numeric(10, 2), nullable=False, default=0.00)
    fees_paid = Column(Numeric(10, 2), nullable=False, default=0.00)
    payment_reference = Column(String(50), nullable=True)
    
    # Card production
    card_ordered = Column(Boolean, nullable=False, default=False)
    card_order_date = Column(DateTime, nullable=True)
    card_production_date = Column(DateTime, nullable=True)
    card_collection_date = Column(DateTime, nullable=True)
    
    # Image and biometric data
    image_handle = Column(String(100), nullable=True)
    image_captured_date = Column(DateTime, nullable=True)
    biometric_data = Column(JSON, nullable=True)
    
    # Processing information
    processing_location_id = Column(UUID(as_uuid=True), nullable=False)
    examiner_id = Column(UUID(as_uuid=True), nullable=True)
    approver_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Validation codes applied
    validation_codes = Column(JSON, nullable=True)
    business_rules_applied = Column(JSON, nullable=True)
    
    # Notes and comments
    notes = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Country configuration
    country_code = Column(String(2), nullable=False)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    updated_by = Column(UUID(as_uuid=True), nullable=False)
    
    # Relationships
    person = relationship("PersonModel", back_populates="license_applications")
    license_cards = relationship("LicenseCard", back_populates="application")
    payments = relationship("ApplicationPayment", back_populates="application")


class LicenseCard(BaseModel):
    """
    License Card entity for card production and management
    Reference: Section 2.2 Card Ordering System
    """
    __tablename__ = "license_cards"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    card_number = Column(String(20), unique=True, nullable=False, index=True)
    
    # Application reference
    application_id = Column(UUID(as_uuid=True), ForeignKey("license_applications.id"), nullable=False)
    person_id = Column(UUID(as_uuid=True), ForeignKey("person_entities.id"), nullable=False)
    
    # Card details
    license_type = Column(SQLEnum(LicenseType), nullable=False)
    card_type = Column(String(20), nullable=False, default="STANDARD")  # STANDARD, DUPLICATE, REPLACEMENT
    
    # Validity
    issue_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    expiry_date = Column(DateTime, nullable=False)
    valid_from = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Production information
    production_status = Column(String(20), nullable=False, default="ORDERED")  # ORDERED, PRODUCED, DISPATCHED, COLLECTED
    production_date = Column(DateTime, nullable=True)
    production_location = Column(String(100), nullable=True)
    dispatch_date = Column(DateTime, nullable=True)
    collection_date = Column(DateTime, nullable=True)
    
    # Card specifications
    card_template = Column(String(50), nullable=False, default="ISO_18013")
    image_handle = Column(String(100), nullable=False)
    security_features = Column(JSON, nullable=True)
    
    # File storage
    card_file_path = Column(String(500), nullable=True)
    card_file_id = Column(String(100), nullable=True)
    
    # Status tracking
    is_active = Column(Boolean, nullable=False, default=True)
    is_collected = Column(Boolean, nullable=False, default=False)
    replacement_reason = Column(String(100), nullable=True)
    
    # Country configuration
    country_code = Column(String(2), nullable=False)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    updated_by = Column(UUID(as_uuid=True), nullable=False)
    
    # Relationships
    application = relationship("LicenseApplication", back_populates="license_cards")
    person = relationship("PersonModel")


class ApplicationPayment(BaseModel):
    """
    Application Payment tracking
    Reference: Section 4.1 Fee Calculation System
    """
    __tablename__ = "application_payments"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_reference = Column(String(50), unique=True, nullable=False, index=True)
    
    # Application reference
    application_id = Column(UUID(as_uuid=True), ForeignKey("license_applications.id"), nullable=False)
    
    # Payment details
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String(20), nullable=False)  # CASH, CARD, BANK_TRANSFER
    payment_status = Column(String(20), nullable=False, default="PENDING")  # PENDING, CONFIRMED, FAILED, REFUNDED
    
    # Payment processing
    payment_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    processed_date = Column(DateTime, nullable=True)
    processor_reference = Column(String(100), nullable=True)
    
    # Fee breakdown
    fee_breakdown = Column(JSON, nullable=True)
    
    # Country configuration
    country_code = Column(String(2), nullable=False)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    updated_by = Column(UUID(as_uuid=True), nullable=False)
    
    # Relationships
    application = relationship("LicenseApplication", back_populates="payments")


class TestCenter(BaseModel):
    """
    Test Center entity for managing testing locations
    """
    __tablename__ = "test_centers"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    center_code = Column(String(10), unique=True, nullable=False, index=True)
    center_name = Column(String(100), nullable=False)
    
    # Location details
    address_line_1 = Column(String(100), nullable=False)
    address_line_2 = Column(String(100), nullable=True)
    city = Column(String(50), nullable=False)
    province = Column(String(50), nullable=False)
    postal_code = Column(String(10), nullable=False)
    
    # Contact information
    phone_number = Column(String(20), nullable=True)
    email_address = Column(String(100), nullable=True)
    
    # Operational details
    is_active = Column(Boolean, nullable=False, default=True)
    operating_hours = Column(JSON, nullable=True)
    test_types_supported = Column(JSON, nullable=True)
    capacity_per_day = Column(Integer, nullable=False, default=50)
    
    # Country configuration
    country_code = Column(String(2), nullable=False)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    updated_by = Column(UUID(as_uuid=True), nullable=False) 