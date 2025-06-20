"""
New Permission System Database Models - Unique Models Only
Contains models that are specific to the permission system and not duplicated elsewhere
"""

import uuid
import json
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import BaseModel

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