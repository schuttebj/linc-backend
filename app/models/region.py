"""
Region Model
Implements the 4-character region authority system from eNaTIS documentation
Represents authorities like DLTC, RA, Provincial Help Desk, etc.
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Integer, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PythonEnum
import uuid

from app.models.base import BaseModel

class RegionType(PythonEnum):
    """User group authority types - using numeric codes for consistency"""
    FIXED_DLTC = "10"                    # Fixed Driving License Testing Center
    MOBILE_DLTC = "11"                   # Mobile Driving License Testing Unit
    PRINTING_CENTER = "12"               # Printing Center (NEW)
    REGISTERING_AUTHORITY = "20"         # Registering Authority
    PROVINCIAL_HELP_DESK = "30"          # Provincial Help Desk
    NATIONAL_HELP_DESK = "31"            # National Help Desk
    VEHICLE_TESTING_STATION = "40"       # Vehicle Testing Station
    ADMIN_OFFICE = "50"                  # Administrative Office

class RegistrationStatus(PythonEnum):
    """Registration status for DLTC and other infrastructure"""
    PENDING_REGISTRATION = "1"           # Initial application
    REGISTERED = "2"                     # Fully operational
    SUSPENDED = "3"                      # Temporarily halted
    PENDING_RENEWAL = "4"                # Renewal process
    CANCELLED = "5"                      # Permanently closed
    PENDING_INSPECTION = "6"             # Awaiting inspection
    INSPECTION_FAILED = "7"              # Failed inspection
    DEREGISTERED = "8"                   # Formally deregistered

class Region(BaseModel):
    """
    Region Model - Authority Management System
    
    Implements the 4-character region codes from eNaTIS documentation.
    Represents authorities like DLTC, RA, Provincial Help Desk, etc.
    
    Examples:
    - WC01: Cape Town DLTC
    - GP03: Johannesburg RA
    - WCHD: Western Cape Help Desk
    """
    __tablename__ = "regions"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_group_code = Column(String(4), nullable=False, unique=True, index=True, 
                           comment="4-character authority code (e.g., WC01, GP03)")
    user_group_name = Column(String(100), nullable=False, 
                           comment="Full authority name (e.g., Cape Town DLTC)")
    
    # Authority classification
    user_group_type = Column(String(2), nullable=False, 
                           comment="Authority type code (10=Fixed DLTC, 20=RA, etc.)")
    
    # Geographic assignment
    province_code = Column(String(2), nullable=False, index=True,
                         comment="Province code (WC, GP, KZN, etc.)")
    
    # Hierarchical relationships
    parent_region_id = Column(UUID(as_uuid=True), ForeignKey('regions.id'), nullable=True,
                           comment="Parent authority for hierarchical structures")
    
    # System variables from documentation
    is_provincial_help_desk = Column(Boolean, nullable=False, default=False,
                                   comment="PLAMARK system variable - Provincial Help Desk")
    is_national_help_desk = Column(Boolean, nullable=False, default=False,
                                 comment="NHELPDESK system variable - National Help Desk")
    
    # Registration and status
    registration_status = Column(String(1), nullable=False, default=RegistrationStatus.REGISTERED.value,
                               comment="Registration status for infrastructure")
    suspended_until = Column(DateTime, nullable=True, 
                           comment="Suspension end date for status validation")
    
    # Contact and operational details
    contact_person = Column(String(100), nullable=True, comment="Primary contact person")
    phone_number = Column(String(20), nullable=True, comment="Contact phone number")
    email = Column(String(255), nullable=True, comment="Contact email address")
    
    # Operational configuration
    operational_notes = Column(Text, nullable=True, comment="Operational notes and instructions")
    service_area_description = Column(Text, nullable=True, comment="Geographic service area description")
    
    # Status management
    is_active = Column(Boolean, nullable=False, default=True, comment="Active status")
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    
    # Relationships
    child_regions = relationship("Region", backref="parent_region", remote_side=[id])
    users = relationship("User", back_populates="region")
    offices = relationship("Office", back_populates="region", cascade="all, delete-orphan")
    locations = relationship("Location", back_populates="region", cascade="all, delete-orphan")
    
    # Database constraints as per development standards
    __table_args__ = (
        CheckConstraint("user_group_code ~ '^[A-Z0-9]{4}$'", name='chk_user_group_code_format'),
        CheckConstraint("province_code ~ '^[A-Z]{2}$'", name='chk_province_code_format'),
        {'comment': 'Region authority management with 4-character codes'},
    )
    
    def __repr__(self):
        return f"<Region(code='{self.user_group_code}', name='{self.user_group_name}', type='{self.user_group_type}')>"
    
    @property
    def is_dltc(self) -> bool:
        """Check if this is a DLTC (Fixed or Mobile)"""
        return self.user_group_type in [RegionType.FIXED_DLTC.value, RegionType.MOBILE_DLTC.value]
    
    @property
    def can_access_all_provinces(self) -> bool:
        """Check if this authority can access all provinces (National Help Desk)"""
        return self.is_national_help_desk
    
    @property
    def can_access_province_data(self) -> bool:
        """Check if this authority can access province-wide data (Provincial Help Desk)"""
        return self.is_provincial_help_desk or self.is_national_help_desk
    
    @property
    def authority_level(self) -> str:
        """Get the authority level for display"""
        if self.is_national_help_desk:
            return "National"
        elif self.is_provincial_help_desk:
            return "Provincial"
        else:
            return "Local"
    
    def can_manage_region(self, target_group_code: str) -> bool:
        """Check if this region can manage another region"""
        # National Help Desk can manage all
        if self.is_national_help_desk:
            return True
        
        # Provincial Help Desk can manage within their province
        if self.is_provincial_help_desk:
            target_province = target_group_code[:2] if len(target_group_code) >= 2 else ""
            return target_province == self.province_code
        
        # Local authorities can only manage themselves
        return self.user_group_code == target_group_code
    
    def validate_registration_status(self) -> bool:
        """Validate if the authority is operational based on registration status"""
        # Non-operational statuses from V00489
        non_operational = [
            RegistrationStatus.PENDING_REGISTRATION.value,
            RegistrationStatus.PENDING_INSPECTION.value,
            RegistrationStatus.INSPECTION_FAILED.value,
            RegistrationStatus.DEREGISTERED.value
        ]
        
        if self.registration_status in non_operational:
            return False
        
        # Check suspension (V00491)
        if (self.registration_status == RegistrationStatus.REGISTERED.value and 
            self.suspended_until and self.suspended_until >= func.now()):
            return False
        
        # Check cancellation (V00490)
        if self.registration_status == RegistrationStatus.CANCELLED.value:
            return False
        
        return True 