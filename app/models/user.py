"""
User Management Models
Implements user authentication and authorization system
UPDATED: Now uses simplified 4-tier permission system - legacy permissions removed
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PythonEnum
import uuid

from app.models.base import BaseModel
from app.models.enums import ValidationStatus

class UserStatus(PythonEnum):
    """User account status from documentation"""
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED" 
    INACTIVE = "INACTIVE"
    LOCKED = "LOCKED"
    PENDING_ACTIVATION = "PENDING_ACTIVATION"

class UserType(PythonEnum):
    """User type codes from documentation"""
    STANDARD = "1"                      # Standard user
    SYSTEM = "2"                        # System user
    EXAMINER = "3"                      # Examiner
    SUPERVISOR = "4"                    # Supervisor
    ADMIN = "5"                         # Administrator

class IDType(PythonEnum):
    """ID Type codes from documentation"""
    TRN = "01"                          # Tax Reference Number
    SA_ID = "02"                        # South African ID
    FOREIGN_ID = "03"                   # Foreign ID
    PASSPORT = "04"                     # Passport
    OTHER = "97"                        # Other ID type

class AuthorityLevel(PythonEnum):
    """Authority hierarchy levels"""
    NATIONAL = "NATIONAL"               # All provinces, all data
    PROVINCIAL = "PROVINCIAL"           # Single province, all RAs
    REGIONAL = "REGIONAL"               # Multiple RAs within province
    LOCAL = "LOCAL"                     # Single RA/DLTC
    OFFICE = "OFFICE"                   # Single office within RA
    PERSONAL = "PERSONAL"               # Own transactions only

class User(BaseModel):
    """
    User account model for system authentication and authorization
    
    UPDATED: Now uses simplified 4-tier permission system
    - System types: super_admin, national_help_desk, provincial_help_desk, standard_user
    - Region assignments with roles
    - Office assignments with roles
    - Individual permission overrides
    """
    __tablename__ = "users"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Legacy compatibility fields (maintained for migration)
    user_number = Column(String(7), nullable=True, unique=True, index=True,
                        comment="Legacy user number format: 4+3 chars (UserGrpCd + sequence)")
    
    # Authentication credentials
    username = Column(String(50), nullable=False, unique=True, index=True, comment="Unique username for login")
    email = Column(String(255), nullable=False, unique=True, index=True, comment="Email address")
    password_hash = Column(String(255), nullable=False, comment="Hashed password")
    
    # Core User Fields from Users_Locations.md documentation
    user_group_code = Column(String(4), nullable=True, index=True,
                           comment="User Group Code (SCHAR2) - determines authority level")
    office_code = Column(String(1), nullable=True,
                        comment="Office Code (SCHAR1) - office within user group")
    user_name = Column(String(30), nullable=True,
                      comment="User Name (SCHAR1) - display name for user")
    user_type_code = Column(String(1), nullable=False, default="1",
                           comment="User Type Code (NUM) - 1=Standard, 2=System, etc.")
    
    # Personal identification
    id_type = Column(String(2), nullable=True,
                    comment="ID Type: 01=TRN, 02=SA ID, 03=Foreign ID, 04=Passport")
    id_number = Column(String(20), nullable=True, index=True,
                      comment="Identification number")
    alternative_phone = Column(String(20), nullable=True,
                              comment="Alternative phone number")
    
    # Personal information
    first_name = Column(String(100), nullable=True, comment="User's first name")
    last_name = Column(String(100), nullable=True, comment="User's last name")
    full_name = Column(String(200), nullable=True, comment="Full legal name")
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
    job_title = Column(String(100), nullable=True, comment="Job title/position")
    
    # Infrastructure assignment (for DLTC users)
    infrastructure_number = Column(String(20), nullable=True,
                                  comment="Infrastructure number for DLTC users")
    
    # Geographic and jurisdiction assignment
    country_code = Column(String(3), nullable=False, default='ZA', comment="Assigned country code")
    province_code = Column(String(2), nullable=True, index=True, comment="Province code assignment")
    province = Column(String(100), nullable=True, comment="Assigned province/state")
    region = Column(String(100), nullable=True, comment="Assigned region")
    office_location = Column(String(200), nullable=True, comment="Physical office location")
    
    # NEW PERMISSION SYSTEM FIELDS
    user_type_id = Column(String(50), ForeignKey('user_types.id'), nullable=True,
                         comment="System type: super_admin, national_help_desk, provincial_help_desk, standard_user")
    assigned_province = Column(String(2), nullable=True, index=True,
                              comment="Assigned province for provincial help desk users")
    permission_overrides = Column(JSON, nullable=True,
                                comment="Individual permission overrides - rare usage")
    
    # Region assignment (replaces legacy user group)  
    region_id = Column(UUID(as_uuid=True), ForeignKey('regions.id'), nullable=True,
                      comment="Primary region assignment")
    
    # Security settings
    require_password_change = Column(Boolean, nullable=False, default=True, comment="Force password change on next login")
    require_2fa = Column(Boolean, nullable=False, default=False, comment="Require two-factor authentication")
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
    
    # NEW PERMISSION SYSTEM RELATIONSHIPS
    user_type = relationship("UserType", back_populates="users", foreign_keys=[user_type_id])
    region_assignments = relationship("UserRegionAssignment", cascade="all, delete-orphan")
    office_assignments = relationship("UserOfficeAssignment", cascade="all, delete-orphan")
    
    # Existing relationships (maintained)
    audit_logs = relationship("UserAuditLog", back_populates="user")
    region = relationship("Region", back_populates="users")
    location_assignments = relationship("UserLocationAssignment", back_populates="user", cascade="all, delete-orphan")  # Legacy - deprecated
    user_sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', user_group='{self.user_group_code}', status='{self.status}')>"
    
    @property
    def full_display_name(self) -> str:
        """Get user's full display name"""
        if self.user_name:
            return self.user_name
        elif self.display_name:
            return self.display_name
        elif self.full_name:
            return self.full_name
        elif self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        else:
            return self.username
    
    @property
    def legacy_user_number(self) -> str:
        """Generate legacy user number format (UserGrpCd + sequence)"""
        if self.user_number:
            return self.user_number
        elif self.user_group_code:
            # Extract sequence from ID for backward compatibility
            sequence = str(self.id)[-3:] if self.id else "001"
            return f"{self.user_group_code}{sequence}"
        else:
            return f"U{str(self.id)[-6:]}" if self.id else "U000001"
    
    @property
    def is_locked(self) -> bool:
        """Check if user account is locked"""
        return (self.status == UserStatus.LOCKED.value or 
                (self.locked_until and self.locked_until > func.now()))
    
    # LEGACY METHODS - REMOVED TO FORCE MIGRATION
    # These methods will now raise errors to force developers to use new permission system
    
    def has_permission(self, permission_name: str) -> bool:
        """LEGACY METHOD - REMOVED"""
        raise NotImplementedError(
            "Legacy permission checking removed. Use PermissionEngine.check_permission() instead.\n"
            "from app.core.permission_engine import PermissionEngine\n"
            "engine = PermissionEngine()\n"
            "has_perm = await engine.check_permission(user_id, 'person.register')"
        )
    
    def has_role(self, role_name: str) -> bool:
        """LEGACY METHOD - REMOVED"""
        raise NotImplementedError(
            "Legacy role checking removed. Use new permission system with region/office roles.\n"
            "Check user assignments: user.region_assignments and user.office_assignments"
        )
    
    @property
    def roles(self):
        """LEGACY PROPERTY - REMOVED"""
        raise NotImplementedError(
            "Legacy roles property removed. Use new permission system.\n"
            "Access region_assignments and office_assignments instead."
        )
    
    @property 
    def permissions(self):
        """LEGACY PROPERTY - REMOVED"""
        raise NotImplementedError(
            "Legacy permissions property removed. Use PermissionEngine.get_user_permissions() instead.\n"
            "from app.core.permission_engine import PermissionEngine\n"
            "engine = PermissionEngine()\n"
            "permissions = await engine.get_user_permissions(user_id)"
        )
    
    def can_access_province(self, province_code: str) -> bool:
        """Check if user can access specific province using new permission system"""
        # This is maintained but should use the new geographic scope system
        from app.core.permission_engine import PermissionEngine
        import asyncio
        
        # For now, return basic logic - should be replaced with PermissionEngine call
        if self.user_type and self.user_type.can_access_all_provinces:
            return True
        return self.assigned_province == province_code or self.province_code == province_code
    
    def can_manage_user_group(self, target_group_code: str) -> bool:
        """LEGACY METHOD - UPDATED to use new permission system"""
        # This should be replaced with proper permission checking
        from app.core.permission_engine import PermissionEngine
        # For now, basic logic - should use permission engine
        return self.user_group_code == target_group_code
    
    def can_manage_region(self, target_region_code: str) -> bool:
        """Check if user can manage a specific region"""
        # This should use the new permission system
        from app.core.permission_engine import PermissionEngine
        # For now, basic logic - should use permission engine
        return self.user_group_code == target_region_code
    
    def get_primary_location_assignment(self):
        """Get primary location assignment - LEGACY"""
        # Maintained for backward compatibility during migration
        if self.location_assignments:
            return self.location_assignments[0]
        return None
    
    def get_accessible_locations(self):
        """Get all accessible locations - LEGACY"""
        # Should be replaced with geographic scope from new permission system
        return [assignment.location for assignment in self.location_assignments if assignment.is_active]
    
    def can_access_location(self, location_id: str) -> bool:
        """Check location access - LEGACY"""
        # Should use new geographic scope system
        accessible_locations = self.get_accessible_locations()
        return any(loc.id == location_id for loc in accessible_locations)
    
    @property
    def authority_level(self) -> str:
        """Get user authority level using new permission system"""
        if not self.user_type:
            return AuthorityLevel.PERSONAL.value
            
        if self.user_type.name == 'super_admin':
            return AuthorityLevel.NATIONAL.value
        elif self.user_type.name == 'national_help_desk':
            return AuthorityLevel.NATIONAL.value
        elif self.user_type.name == 'provincial_help_desk':
            return AuthorityLevel.PROVINCIAL.value
        else:
            return AuthorityLevel.LOCAL.value

# LEGACY MODELS REMOVED - These will break existing code to force migration
# Role and Permission models are no longer available
# user_roles and role_permissions tables are no longer defined

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
        return f"<UserAuditLog(id={self.id}, user_id={self.user_id}, action='{self.action}')>"

class UserSession(BaseModel):
    """
    User Session Model implementing documentation Section 1.3
    Session management for user workstation validation and audit trail
    """
    __tablename__ = "user_sessions"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True,
               comment="Session UUID identifier")
    
    # User association
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True,
                    comment="User UUID")
    
    # Session fields from documentation (Section 1.3.1)
    user_group_code = Column(String(4), nullable=False, index=True,
                           comment="UserSes.UserGrpCd - User group for session")
    user_number = Column(String(7), nullable=False,
                        comment="UserSes.UserN - Legacy user number (4+3 format)")
    province_code = Column(String(2), nullable=False,
                          comment="User's home province")
    
    # Session timing
    session_start = Column(DateTime, nullable=False, default=func.now(),
                          comment="Session start timestamp")
    session_expiry = Column(DateTime, nullable=False,
                           comment="Session expiry timestamp")
    
    # Workstation and network information
    workstation_id = Column(String(10), nullable=False,
                           comment="Workstation identifier (SCHAR3)")
    ip_address = Column(String(45), nullable=True,
                       comment="Client IP address")
    user_agent = Column(Text, nullable=True,
                       comment="Client user agent string")
    
    # Session type and status
    session_type = Column(String(20), nullable=False, default="interactive",
                         comment="Session type")
    is_active = Column(Boolean, nullable=False, default=True,
                      comment="Session active status")
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    ended_at = Column(DateTime, nullable=True,
                     comment="Session end timestamp")
    
    # Relationships
    user = relationship("User", back_populates="user_sessions")
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, workstation='{self.workstation_id}')>"
    
    @property
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return self.session_expiry < func.now()
    
    @property
    def user_profile_display(self) -> str:
        """Display user profile information"""
        return f"{self.user_number} ({self.user_group_code})"
    
    @property
    def user_group_display(self) -> str:
        """Display user group information"""
        return f"{self.user_group_code} - {self.province_code}"
    
    @property
    def office_display(self) -> str:
        """Display office information from user group and office code"""
        # Extract office code from workstation or user data
        return f"{self.user_group_code}{self.workstation_id[-1] if len(self.workstation_id) > 0 else 'A'}"

# LEGACY MODELS COMPLETELY REMOVED
# All legacy Role, Permission, user_roles, role_permissions have been removed
# Use new permission system: PermissionEngine, UserType, Region assignments 