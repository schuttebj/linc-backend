"""
New Permission System Database Models
Implements the simplified permission architecture
"""

import uuid
import json
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import BaseModel

class UserType(BaseModel):
    """
    System-level user types with their permissions
    Replaces complex role hierarchies with simple predefined types
    """
    __tablename__ = "user_types"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    type_code = Column(String(50), nullable=False, unique=True, index=True, 
                      comment="System type code: super_admin, national_help_desk, provincial_help_desk, standard_user")
    display_name = Column(String(100), nullable=False, comment="Human-readable type name")
    description = Column(Text, nullable=True, comment="Type description")
    
    # JSONB field for flexible permission storage
    permissions = Column(JSON, nullable=True, comment="List of permission names in JSON array")
    
    # Type configuration
    is_system_type = Column(Boolean, nullable=False, default=True, comment="System-defined type (cannot be deleted)")
    is_active = Column(Boolean, nullable=False, default=True, comment="Active status")
    
    # Geographic access rules
    has_national_access = Column(Boolean, nullable=False, default=False, comment="Can access all provinces")
    restricted_to_province = Column(String(2), nullable=True, comment="Restricted to specific province code")
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    
    def __repr__(self):
        return f"<UserType(type_code='{self.type_code}', display_name='{self.display_name}')>"

class Region(BaseModel):
    """
    Regions (renamed from User Groups)
    Represents geographic/administrative regions
    """
    __tablename__ = "regions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    region_code = Column(String(10), nullable=False, unique=True, index=True, 
                        comment="Region identifier code")
    region_name = Column(String(100), nullable=False, comment="Region display name")
    description = Column(Text, nullable=True, comment="Region description")
    
    # Geographic assignment
    province_code = Column(String(2), nullable=False, index=True, comment="Province code this region belongs to")
    country_code = Column(String(3), nullable=False, default='ZA', comment="Country code")
    
    # Region settings
    is_active = Column(Boolean, nullable=False, default=True, comment="Active status")
    region_type = Column(String(20), nullable=False, default='standard', 
                        comment="Region type: standard, dltc, registration_authority")
    
    # Contact information
    contact_person = Column(String(100), nullable=True, comment="Region contact person")
    contact_email = Column(String(255), nullable=True, comment="Region contact email")
    contact_phone = Column(String(20), nullable=True, comment="Region contact phone")
    physical_address = Column(Text, nullable=True, comment="Physical address")
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    
    # Relationships
    offices = relationship("Office", back_populates="region", cascade="all, delete-orphan")
    user_assignments = relationship("UserRegionAssignment", back_populates="region")
    
    def __repr__(self):
        return f"<Region(region_code='{self.region_code}', region_name='{self.region_name}')>"

class RegionRole(BaseModel):
    """
    Predefined roles for region-level operations
    """
    __tablename__ = "region_roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    role_name = Column(String(50), nullable=False, unique=True, index=True, 
                      comment="Role identifier: region_administrator, region_supervisor, etc.")
    display_name = Column(String(100), nullable=False, comment="Human-readable role name")
    description = Column(Text, nullable=True, comment="Role description")
    
    # JSONB field for flexible permission storage
    permissions = Column(JSON, nullable=True, comment="List of permission names in JSON array")
    
    # Role configuration
    is_system_role = Column(Boolean, nullable=False, default=True, comment="System-defined role (cannot be deleted)")
    is_active = Column(Boolean, nullable=False, default=True, comment="Active status")
    role_level = Column(Integer, nullable=False, default=1, comment="Role hierarchy level")
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    
    def __repr__(self):
        return f"<RegionRole(role_name='{self.role_name}', display_name='{self.display_name}')>"

class Office(BaseModel):
    """
    Offices within regions
    """
    __tablename__ = "offices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    office_code = Column(String(15), nullable=False, unique=True, index=True, 
                        comment="Office identifier code")
    office_name = Column(String(100), nullable=False, comment="Office display name")
    description = Column(Text, nullable=True, comment="Office description")
    
    # Region assignment
    region_id = Column(UUID(as_uuid=True), ForeignKey('regions.id'), nullable=False, index=True, 
                      comment="Parent region")
    
    # Office settings
    is_active = Column(Boolean, nullable=False, default=True, comment="Active status")
    office_type = Column(String(20), nullable=False, default='standard', 
                        comment="Office type: standard, dltc, testing_center")
    
    # Contact information
    contact_person = Column(String(100), nullable=True, comment="Office contact person")
    contact_email = Column(String(255), nullable=True, comment="Office contact email")
    contact_phone = Column(String(20), nullable=True, comment="Office contact phone")
    physical_address = Column(Text, nullable=True, comment="Physical address")
    
    # Operating hours and capacity
    operating_hours = Column(Text, nullable=True, comment="Operating hours description")
    max_capacity = Column(Integer, nullable=True, comment="Maximum daily capacity")
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    
    # Relationships
    region = relationship("Region", back_populates="offices")
    user_assignments = relationship("UserOfficeAssignment", back_populates="office")
    
    def __repr__(self):
        return f"<Office(office_code='{self.office_code}', office_name='{self.office_name}')>"

class OfficeRole(BaseModel):
    """
    Predefined roles for office-level operations
    """
    __tablename__ = "office_roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    role_name = Column(String(50), nullable=False, unique=True, index=True, 
                      comment="Role identifier: data_clerk, cashier, examiner, etc.")
    display_name = Column(String(100), nullable=False, comment="Human-readable role name")
    description = Column(Text, nullable=True, comment="Role description")
    
    # JSONB field for flexible permission storage
    permissions = Column(JSON, nullable=True, comment="List of permission names in JSON array")
    
    # Role configuration
    is_system_role = Column(Boolean, nullable=False, default=True, comment="System-defined role (cannot be deleted)")
    is_active = Column(Boolean, nullable=False, default=True, comment="Active status")
    role_level = Column(Integer, nullable=False, default=1, comment="Role hierarchy level")
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    
    def __repr__(self):
        return f"<OfficeRole(role_name='{self.role_name}', display_name='{self.display_name}')>"

class UserRegionAssignment(BaseModel):
    """
    User assignments to regions with specific roles
    Many-to-many relationship allowing users to have multiple region assignments
    """
    __tablename__ = "user_region_assignments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Relationships
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    region_id = Column(UUID(as_uuid=True), ForeignKey('regions.id'), nullable=False, index=True)
    
    # Assignment details
    region_role = Column(String(50), nullable=False, comment="Region role for this assignment")
    assignment_type = Column(String(20), nullable=False, default='standard', 
                           comment="Assignment type: primary, secondary, temporary")
    
    # Assignment period
    effective_from = Column(DateTime, nullable=False, default=func.now(), 
                          comment="Assignment start date")
    effective_to = Column(DateTime, nullable=True, comment="Assignment end date (null = indefinite)")
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True, comment="Assignment is currently active")
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="region_assignments")
    region = relationship("Region", back_populates="user_assignments")
    
    @property
    def is_valid_assignment(self) -> bool:
        """Check if assignment is currently valid"""
        if not self.is_active:
            return False
        
        now = datetime.utcnow()
        if self.effective_from > now:
            return False
        
        if self.effective_to and self.effective_to <= now:
            return False
        
        return True
    
    def __repr__(self):
        return f"<UserRegionAssignment(user_id='{self.user_id}', region_id='{self.region_id}', role='{self.region_role}')>"

class UserOfficeAssignment(BaseModel):
    """
    User assignments to offices with specific roles
    Many-to-many relationship allowing users to have multiple office assignments
    """
    __tablename__ = "user_office_assignments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Relationships
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    office_id = Column(UUID(as_uuid=True), ForeignKey('offices.id'), nullable=False, index=True)
    
    # Assignment details
    office_role = Column(String(50), nullable=False, comment="Office role for this assignment")
    assignment_type = Column(String(20), nullable=False, default='standard', 
                           comment="Assignment type: primary, secondary, temporary")
    
    # Assignment period
    effective_from = Column(DateTime, nullable=False, default=func.now(), 
                          comment="Assignment start date")
    effective_to = Column(DateTime, nullable=True, comment="Assignment end date (null = indefinite)")
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True, comment="Assignment is currently active")
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="office_assignments")
    office = relationship("Office", back_populates="user_assignments")
    
    @property
    def is_valid_assignment(self) -> bool:
        """Check if assignment is currently valid"""
        if not self.is_active:
            return False
        
        now = datetime.utcnow()
        if self.effective_from > now:
            return False
        
        if self.effective_to and self.effective_to <= now:
            return False
        
        return True
    
    def __repr__(self):
        return f"<UserOfficeAssignment(user_id='{self.user_id}', office_id='{self.office_id}', role='{self.office_role}')>"

class PermissionAuditLog(BaseModel):
    """
    Audit log for permission and role changes
    """
    __tablename__ = "permission_audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Change details
    role_type = Column(String(20), nullable=False, index=True, 
                      comment="Type of role changed: system, region, office")
    role_name = Column(String(100), nullable=False, index=True, 
                      comment="Name of the role that was changed")
    action = Column(String(50), nullable=False, comment="Action performed: permissions_updated, role_created, etc.")
    
    # Change content
    details = Column(JSON, nullable=True, comment="Detailed information about the change in JSON format")
    
    # Audit fields
    updated_by = Column(String(100), nullable=False, comment="User who made the change")
    created_at = Column(DateTime, nullable=False, default=func.now(), index=True)
    
    def __repr__(self):
        return f"<PermissionAuditLog(role_type='{self.role_type}', role_name='{self.role_name}', action='{self.action}')>"