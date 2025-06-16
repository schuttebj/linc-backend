"""
User Management Models
Implements user authentication and authorization system
Based on documentation requirements for role-based access control
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PythonEnum
import uuid

from app.models.base import BaseModel
from app.models.enums import ValidationStatus

# Association table for many-to-many relationship between users and roles
user_roles = Table(
    'user_roles',
    BaseModel.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True),
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id'), primary_key=True)
)

# Association table for many-to-many relationship between roles and permissions
role_permissions = Table(
    'role_permissions', 
    BaseModel.metadata,
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', UUID(as_uuid=True), ForeignKey('permissions.id'), primary_key=True)
)

class UserStatus(PythonEnum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive" 
    SUSPENDED = "suspended"
    LOCKED = "locked"
    PENDING_ACTIVATION = "pending_activation"

class User(BaseModel):
    """
    User account model for system authentication and authorization
    
    Implements user management requirements from documentation:
    - Role-based access control
    - User authorization for transactions
    - Audit trail requirements
    """
    __tablename__ = "users"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Authentication credentials
    username = Column(String(50), nullable=False, unique=True, index=True, comment="Unique username for login")
    email = Column(String(255), nullable=False, unique=True, index=True, comment="Email address")
    password_hash = Column(String(255), nullable=False, comment="Hashed password")
    
    # Personal information
    first_name = Column(String(100), nullable=False, comment="User's first name")
    last_name = Column(String(100), nullable=False, comment="User's last name")
    display_name = Column(String(200), nullable=True, comment="Display name for UI")
    
    # Account status and settings
    status = Column(String(20), nullable=False, default=UserStatus.PENDING_ACTIVATION.value, comment="Account status")
    is_active = Column(Boolean, nullable=False, default=True, comment="Active flag")
    is_superuser = Column(Boolean, nullable=False, default=False, comment="Superuser flag")
    is_verified = Column(Boolean, nullable=False, default=False, comment="Email verification status")
    
    # Contact information
    phone_number = Column(String(20), nullable=True, comment="Contact phone number")
    employee_id = Column(String(50), nullable=True, comment="Employee/staff ID number")
    department = Column(String(100), nullable=True, comment="Department or division")
    
    # Geographic and jurisdiction assignment
    country_code = Column(String(3), nullable=False, default='ZA', comment="Assigned country code")
    province = Column(String(100), nullable=True, comment="Assigned province/state")
    region = Column(String(100), nullable=True, comment="Assigned region")
    office_location = Column(String(200), nullable=True, comment="Physical office location")
    
    # User group assignment (NEW - from documentation requirements)
    user_group_id = Column(UUID(as_uuid=True), ForeignKey('user_groups.id'), nullable=True,
                          comment="Primary user group assignment")
    user_group_code = Column(String(4), nullable=True, index=True,
                           comment="Primary user group code (e.g., WC01, GP03)")
    
    # Security settings
    require_password_change = Column(Boolean, nullable=False, default=False, comment="Force password change on next login")
    password_expires_at = Column(DateTime, nullable=True, comment="Password expiration date")
    failed_login_attempts = Column(Integer, nullable=False, default=0, comment="Failed login attempt counter")
    locked_until = Column(DateTime, nullable=True, comment="Account lock expiration")
    last_login_at = Column(DateTime, nullable=True, comment="Last successful login timestamp")
    last_login_ip = Column(String(45), nullable=True, comment="Last login IP address")
    
    # Two-factor authentication
    is_2fa_enabled = Column(Boolean, nullable=False, default=False, comment="Two-factor authentication enabled")
    totp_secret = Column(String(32), nullable=True, comment="TOTP secret for 2FA")
    backup_codes = Column(Text, nullable=True, comment="JSON array of backup codes")
    
    # Session and token management
    current_token_id = Column(String(255), nullable=True, comment="Current active token ID")
    token_expires_at = Column(DateTime, nullable=True, comment="Current token expiration")
    refresh_token_hash = Column(String(255), nullable=True, comment="Refresh token hash")
    
    # User preferences
    language = Column(String(10), nullable=False, default='en', comment="Preferred language")
    timezone = Column(String(50), nullable=False, default='Africa/Johannesburg', comment="User timezone")
    date_format = Column(String(20), nullable=False, default='YYYY-MM-DD', comment="Preferred date format")
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now(), comment="Account creation timestamp")
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment="Last update timestamp")
    created_by = Column(String(100), nullable=True, comment="User who created this account")
    updated_by = Column(String(100), nullable=True, comment="User who last updated this account")
    
    # Activation and verification
    email_verification_token = Column(String(255), nullable=True, comment="Email verification token")
    email_verification_expires = Column(DateTime, nullable=True, comment="Email verification expiration")
    password_reset_token = Column(String(255), nullable=True, comment="Password reset token")
    password_reset_expires = Column(DateTime, nullable=True, comment="Password reset expiration")
    
    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    audit_logs = relationship("UserAuditLog", back_populates="user")
    user_group = relationship("UserGroup", back_populates="users")
    location_assignments = relationship("UserLocationAssignment", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}', status='{self.status}')>"
    
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_locked(self) -> bool:
        """Check if account is currently locked"""
        if self.locked_until:
            return self.locked_until > func.now()
        return False
    
    def has_permission(self, permission_name: str) -> bool:
        """Check if user has specific permission"""
        if self.is_superuser:
            return True
        
        for role in self.roles:
            for permission in role.permissions:
                if permission.name == permission_name:
                    return True
        return False
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has specific role"""
        return any(role.name == role_name for role in self.roles)
    
    # NEW METHODS - User Group and Location Management
    def can_access_province(self, province_code: str) -> bool:
        """Check if user can access a specific province"""
        if self.is_superuser:
            return True
        
        # If user has a user group, check group permissions
        if self.user_group:
            # National Help Desk can access all provinces
            if self.user_group.is_national_help_desk:
                return True
            
            # Provincial Help Desk or local groups can access their province
            if self.user_group.province_code == province_code:
                return True
        
        # Check user's directly assigned province
        return self.province == province_code
    
    def can_manage_user_group(self, target_group_code: str) -> bool:
        """Check if user can manage another user group"""
        if self.is_superuser:
            return True
        
        if self.user_group:
            return self.user_group.can_manage_user_group(target_group_code)
        
        return False
    
    def get_primary_location_assignment(self):
        """Get user's primary location assignment"""
        for assignment in self.location_assignments:
            if (assignment.is_valid_assignment and 
                assignment.assignment_type == "primary"):
                return assignment
        return None
    
    def get_accessible_locations(self):
        """Get all locations user can access"""
        locations = []
        for assignment in self.location_assignments:
            if assignment.is_valid_assignment:
                locations.append(assignment.location)
        return locations
    
    def can_access_location(self, location_id: str) -> bool:
        """Check if user can access a specific location"""
        if self.is_superuser:
            return True
        
        # Check direct location assignments
        for assignment in self.location_assignments:
            if (assignment.is_valid_assignment and 
                str(assignment.location_id) == str(location_id)):
                return True
        
        return False
    
    @property
    def authority_level(self) -> str:
        """Get user's authority level based on user group"""
        if self.user_group:
            return self.user_group.authority_level
        return "Local"

class Role(BaseModel):
    """
    User role model for role-based access control
    
    Implements roles from documentation:
    - Admin: Full system access
    - Operator: Transaction processing
    - Examiner: Test administration
    - Viewer: Read-only access
    """
    __tablename__ = "roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(50), nullable=False, unique=True, comment="Role name")
    display_name = Column(String(100), nullable=False, comment="Human-readable role name")
    description = Column(Text, nullable=True, comment="Role description")
    
    # Role settings
    is_system_role = Column(Boolean, nullable=False, default=False, comment="System-defined role (cannot be deleted)")
    is_active = Column(Boolean, nullable=False, default=True, comment="Active status")
    
    # Hierarchy and inheritance
    parent_role_id = Column(UUID(as_uuid=True), ForeignKey('roles.id'), nullable=True, comment="Parent role for inheritance")
    level = Column(Integer, nullable=False, default=0, comment="Role hierarchy level")
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    
    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    child_roles = relationship("Role", backref="parent_role", remote_side=[id])
    
    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}', display_name='{self.display_name}')>"

class Permission(BaseModel):
    """
    Permission model for granular access control
    
    Implements permissions from documentation business rules:
    - License application processing
    - Financial transaction authorization
    - Administrative functions
    - Report generation
    """
    __tablename__ = "permissions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), nullable=False, unique=True, comment="Permission name/code")
    display_name = Column(String(150), nullable=False, comment="Human-readable permission name")
    description = Column(Text, nullable=True, comment="Permission description")
    
    # Permission categorization
    category = Column(String(50), nullable=False, comment="Permission category (license, financial, admin, etc.)")
    resource = Column(String(100), nullable=False, comment="Resource being protected")
    action = Column(String(50), nullable=False, comment="Action being permitted (create, read, update, delete)")
    
    # Permission settings
    is_system_permission = Column(Boolean, nullable=False, default=False, comment="System-defined permission")
    is_active = Column(Boolean, nullable=False, default=True, comment="Active status")
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    
    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")
    
    def __repr__(self):
        return f"<Permission(id={self.id}, name='{self.name}', category='{self.category}')>"

class UserAuditLog(BaseModel):
    """
    User audit log for tracking user actions
    Implements audit trail requirements from documentation
    """
    __tablename__ = "user_audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    
    # Action details
    action = Column(String(100), nullable=False, comment="Action performed")
    resource = Column(String(100), nullable=True, comment="Resource affected")
    resource_id = Column(String(100), nullable=True, comment="ID of affected resource")
    
    # Request details
    ip_address = Column(String(45), nullable=True, comment="Client IP address")
    user_agent = Column(Text, nullable=True, comment="Client user agent")
    endpoint = Column(String(200), nullable=True, comment="API endpoint accessed")
    method = Column(String(10), nullable=True, comment="HTTP method")
    
    # Result details
    success = Column(Boolean, nullable=False, comment="Whether action was successful")
    error_message = Column(Text, nullable=True, comment="Error message if failed")
    details = Column(Text, nullable=True, comment="Additional action details (JSON)")
    
    # Timing
    created_at = Column(DateTime, nullable=False, default=func.now(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<UserAuditLog(id={self.id}, user_id={self.user_id}, action='{self.action}', success={self.success})>" 