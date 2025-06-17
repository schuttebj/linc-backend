"""
Office Model
Implements the office management system within user groups
Handles A-Z office codes for branch offices, mobile units, etc.
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Integer, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PythonEnum
import uuid

from app.models.base import BaseModel

class OfficeType(PythonEnum):
    """Office types within user groups"""
    PRIMARY = "primary"                  # Main/Head Office (usually A)
    BRANCH = "branch"                    # Branch Office (B-F)
    SPECIALIZED = "specialized"          # Specialized Units (G-L)
    MOBILE = "mobile"                    # Mobile/Temporary Units (M-P)
    SUPPORT = "support"                  # Support/Maintenance (Q-Z)

class Office(BaseModel):
    """
    Office Model - Sub-Authority Management
    
    Implements office codes (A-Z) within user groups for organizational structure.
    Each user group can have multiple offices representing different operational units.
    
    Examples:
    - WC01A: Cape Town Main Testing Center
    - WC01B: Bellville Branch Office
    - WC01M: Mobile Unit 1
    """
    __tablename__ = "offices"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    office_code = Column(String(1), nullable=False, 
                        comment="Single letter office code (A-Z)")
    office_name = Column(String(100), nullable=False, 
                        comment="Office name (e.g., Main Office, Branch Office)")
    
    # User group relationship
    user_group_id = Column(UUID(as_uuid=True), ForeignKey('user_groups.id'), nullable=False,
                          comment="Parent user group")
    
    # Office classification
    office_type = Column(String(20), nullable=False, default=OfficeType.BRANCH.value,
                        comment="Office type for operational classification")
    
    # Operational details
    description = Column(Text, nullable=True, comment="Office description and purpose")
    contact_person = Column(String(100), nullable=True, comment="Office contact person")
    phone_number = Column(String(20), nullable=True, comment="Office phone number")
    email = Column(String(255), nullable=True, comment="Office email address")
    
    # Capacity and operational limits
    daily_capacity = Column(Integer, nullable=True, default=0, 
                          comment="Daily operational capacity (tests, applications, etc.)")
    staff_count = Column(Integer, nullable=True, default=0, 
                        comment="Number of staff assigned to this office")
    
    # Status management
    is_active = Column(Boolean, nullable=False, default=True, comment="Active status")
    is_operational = Column(Boolean, nullable=False, default=True, 
                          comment="Currently operational for services")
    
    # Operational hours and configuration
    operating_hours = Column(Text, nullable=True, 
                           comment="Operating hours in JSON format")
    service_types = Column(Text, nullable=True, 
                         comment="Available service types in JSON format")
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    
    # Relationships
    user_group = relationship("UserGroup", back_populates="offices")
    locations = relationship("Location", back_populates="office", cascade="all, delete-orphan")
    user_assignments = relationship("UserLocationAssignment", back_populates="office")
    
    # Table constraints as per development standards
    __table_args__ = (
        UniqueConstraint('user_group_id', 'office_code', name='uq_office_user_group_code'),
        CheckConstraint("office_code ~ '^[A-Z]$'", name='chk_office_code_format'),
        {'comment': 'Office management within user groups with A-Z codes'},
    )
    
    def __repr__(self):
        return f"<Office(code='{self.office_code}', name='{self.office_name}', group='{self.user_group_id}')>"
    
    @property
    def full_office_code(self) -> str:
        """Get the full office identifier (UserGroupCode + OfficeCode)"""
        if self.user_group:
            return f"{self.user_group.user_group_code}{self.office_code}"
        return self.office_code
    
    @property
    def is_primary_office(self) -> bool:
        """Check if this is the primary office (usually code 'A')"""
        return self.office_type == OfficeType.PRIMARY.value or self.office_code == 'A'
    
    @property
    def is_mobile_unit(self) -> bool:
        """Check if this is a mobile unit"""
        return self.office_type == OfficeType.MOBILE.value
    
    def can_provide_service(self, service_type: str = None) -> bool:
        """Check if this office can provide a specific service"""
        if not self.is_active or not self.is_operational:
            return False
        
        if service_type and self.service_types:
            # If service types are defined, check if the requested service is available
            import json
            try:
                available_services = json.loads(self.service_types)
                return service_type in available_services
            except (json.JSONDecodeError, TypeError):
                pass
        
        # If no specific service types defined, assume all services available
        return True
    
    def get_available_capacity(self) -> int:
        """Get available capacity for the office"""
        if not self.daily_capacity:
            return 0
        
        # In a real implementation, this would check current bookings/assignments
        # For now, return the full daily capacity
        return self.daily_capacity
    
    def validate_office_code(self) -> bool:
        """Validate office code format (single letter A-Z)"""
        if not self.office_code:
            return False
        
        return (len(self.office_code) == 1 and 
                self.office_code.isalpha() and 
                self.office_code.isupper())
    
    @staticmethod
    def suggest_office_code(user_group_id: str, office_type: OfficeType = None) -> str:
        """Suggest the next available office code for a user group"""
        # This would query existing offices and suggest the next available code
        # For now, return a basic suggestion based on office type
        
        if office_type == OfficeType.PRIMARY:
            return 'A'
        elif office_type == OfficeType.MOBILE:
            return 'M'
        else:
            return 'B'  # Default to first branch office 