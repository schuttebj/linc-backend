"""
User Type Models for New Permission System
Implements 4-tier user hierarchy: super_admin -> national_help_desk -> provincial_help_desk -> standard_user
"""

from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base_class import Base


class UserType(Base):
    """
    User Type Model - Defines the 4-tier permission hierarchy
    
    Tier 1: super_admin (Full system access)
    Tier 2: national_help_desk (National level access)
    Tier 3: provincial_help_desk (Province level access)  
    Tier 4: standard_user (Limited regional access)
    """
    __tablename__ = "user_types"
    
    # Primary key
    id = Column(String(50), primary_key=True)  # e.g., "super_admin", "national_help_desk"
    
    # Display information
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Hierarchy
    tier_level = Column(String(10), nullable=False)  # "1", "2", "3", "4"
    parent_type_id = Column(String(50), nullable=True)  # Parent in hierarchy
    
    # Permission configuration
    default_permissions = Column(JSON, nullable=False, default=list)  # List of default permissions
    permission_constraints = Column(JSON, nullable=False, default=dict)  # Geographic/scope constraints
    
    # Geographic scope
    can_access_all_provinces = Column(Boolean, default=False)
    can_access_all_regions = Column(Boolean, default=False)
    can_access_all_offices = Column(Boolean, default=False)
    
    # System flags
    is_system_type = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=True)
    
    # Relationships
    users = relationship("User", back_populates="user_type", foreign_keys="User.user_type_id")
    
    def __repr__(self):
        return f"<UserType(id='{self.id}', display_name='{self.display_name}', tier={self.tier_level})>"
    
    @property
    def full_display_name(self) -> str:
        """Get full display name with tier info"""
        return f"{self.display_name} (Tier {self.tier_level})"
    
    def get_effective_permissions(self, user_overrides: list = None) -> list:
        """
        Get effective permissions for this user type
        Combines default permissions with user-specific overrides
        """
        permissions = set(self.default_permissions or [])
        
        if user_overrides:
            # Handle wildcard permissions
            if "*" in user_overrides:
                return ["*"]  # Full access
            
            # Add override permissions
            permissions.update(user_overrides)
        
        return sorted(list(permissions))
    
    def can_manage_user_type(self, target_type_id: str) -> bool:
        """
        Check if this user type can manage another user type
        Higher tiers can manage lower tiers
        """
        if self.id == "super_admin":
            return True
        
        # Define hierarchy
        hierarchy = {
            "super_admin": 1,
            "national_help_desk": 2,
            "provincial_help_desk": 3,
            "standard_user": 4
        }
        
        current_tier = hierarchy.get(self.id, 999)
        target_tier = hierarchy.get(target_type_id, 999)
        
        return current_tier < target_tier


class UserRegionAssignment(Base):
    """
    User Region Assignment - Links users to specific regions they can access
    """
    __tablename__ = "user_region_assignments"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    region_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Assignment details
    assignment_type = Column(String(20), nullable=False, default="read_write")  # read_only, read_write, admin
    granted_by = Column(String(100), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Optional expiry
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<UserRegionAssignment(user_id='{self.user_id}', region_id='{self.region_id}', type='{self.assignment_type}')>"


class UserOfficeAssignment(Base):
    """
    User Office Assignment - Links users to specific offices they can access
    """
    __tablename__ = "user_office_assignments"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    office_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Assignment details
    assignment_type = Column(String(20), nullable=False, default="read_write")  # read_only, read_write, admin
    granted_by = Column(String(100), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Optional expiry
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<UserOfficeAssignment(user_id='{self.user_id}', office_id='{self.office_id}', type='{self.assignment_type}')>" 