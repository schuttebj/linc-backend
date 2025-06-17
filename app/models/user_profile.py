"""
User Profile Model
Enhanced user model implementing comprehensive requirements from Users_Locations.md
Supports user groups, personal identification, geographic assignment, and session management
"""

from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Integer, Date, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PythonEnum
import uuid
import json
from typing import Dict, Any

from app.models.base import BaseModel

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

class UserProfile(BaseModel):
    """
    Enhanced User Profile Model
    
    Implements comprehensive user management requirements from Users_Locations.md:
    - User Profile Structure (Section 1.1.1)
    - User Group Integration (Section 1.1.2)
    - Geographic Assignment (Section 1.1.3)
    - Session Management Integration (Section 1.3)
    - Personal Identification Details
    - Role-based Access Control
    - Administration Marks System Integration
    """
    __tablename__ = "user_profiles"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True,
               comment="Primary UUID identifier replacing legacy UserN")
    
    # Legacy compatibility fields
    user_number = Column(String(7), nullable=True, unique=True, index=True,
                        comment="Legacy user number format: 4+3 chars (UserGrpCd + sequence)")
    
    # System authentication
    username = Column(String(50), nullable=False, unique=True, index=True,
                     comment="Unique system username for authentication")
    password_hash = Column(String(255), nullable=False,
                          comment="Hashed password")
    
    # Core User Fields from documentation
    user_group_code = Column(String(4), nullable=False, index=True,
                           comment="User Group Code (SCHAR2) - determines authority level")
    office_code = Column(String(1), nullable=False,
                        comment="Office Code (SCHAR1) - office within user group")
    user_name = Column(String(30), nullable=False,
                      comment="User Name (SCHAR1) - display name for user")
    user_type_code = Column(String(1), nullable=False, default="1",
                           comment="User Type Code (NUM) - 1=Standard, 2=System, etc.")
    
    # Province assignment
    province_code = Column(String(2), nullable=False, index=True,
                          comment="Province Code (SCHAR2) - user's home province")
    
    # Personal identification
    id_type = Column(String(2), nullable=False,
                    comment="ID Type: 01=TRN, 02=SA ID, 03=Foreign ID, 04=Passport")
    id_number = Column(String(20), nullable=False, index=True,
                      comment="Identification number")
    full_name = Column(String(200), nullable=False,
                      comment="Full legal name")
    email = Column(String(255), nullable=False, unique=True, index=True,
                  comment="Email address (must be unique system-wide)")
    phone_number = Column(String(20), nullable=True,
                         comment="Primary contact phone number")
    alternative_phone = Column(String(20), nullable=True,
                              comment="Alternative phone number")
    
    # Geographic assignment
    country_code = Column(String(3), nullable=False, default='ZA',
                         comment="Country code assignment")
    region = Column(String(100), nullable=True,
                   comment="Regional assignment within province")
    
    # Employment details
    employee_id = Column(String(50), nullable=True, index=True,
                        comment="Employee/staff ID number")
    department = Column(String(100), nullable=True,
                       comment="Department or division")
    job_title = Column(String(100), nullable=True,
                      comment="Job title/position")
    
    # Infrastructure assignment (for DLTC users)
    infrastructure_number = Column(String(20), nullable=True,
                                  comment="Infrastructure number for DLTC users")
    
    # Account status
    status = Column(String(20), nullable=False, default=UserStatus.PENDING_ACTIVATION.value,
                   comment="User account status")
    is_active = Column(Boolean, nullable=False, default=True,
                      comment="Active flag")
    is_superuser = Column(Boolean, nullable=False, default=False,
                         comment="Superuser flag")
    is_verified = Column(Boolean, nullable=False, default=False,
                        comment="Email verification status")
    
    # Security settings
    require_password_change = Column(Boolean, nullable=False, default=True,
                                   comment="Force password change on next login")
    require_2fa = Column(Boolean, nullable=False, default=False,
                        comment="Require two-factor authentication")
    password_expires_at = Column(DateTime, nullable=True,
                                comment="Password expiration date")
    failed_login_attempts = Column(Integer, nullable=False, default=0,
                                  comment="Failed login attempt counter")
    locked_until = Column(DateTime, nullable=True,
                         comment="Account lock expiration")
    last_login_at = Column(DateTime, nullable=True,
                          comment="Last successful login timestamp")
    last_login_ip = Column(String(45), nullable=True,
                          comment="Last login IP address")
    
    # System preferences
    language = Column(String(10), nullable=False, default='en',
                     comment="Preferred language")
    timezone = Column(String(50), nullable=False, default='Africa/Johannesburg',
                     comment="User timezone")
    date_format = Column(String(20), nullable=False, default='YYYY-MM-DD',
                        comment="Preferred date format")
    
    # User group relationship
    user_group_id = Column(UUID(as_uuid=True), ForeignKey('user_groups.id'), nullable=True,
                          comment="Primary user group assignment")
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now(),
                       comment="Account creation timestamp")
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now(),
                       comment="Last update timestamp")
    created_by = Column(String(100), nullable=True,
                       comment="User who created this account")
    updated_by = Column(String(100), nullable=True,
                       comment="User who last updated this account")
    
    # Activation and verification
    email_verification_token = Column(String(255), nullable=True,
                                     comment="Email verification token")
    email_verification_expires = Column(DateTime, nullable=True,
                                       comment="Email verification expiration")
    password_reset_token = Column(String(255), nullable=True,
                                 comment="Password reset token")
    password_reset_expires = Column(DateTime, nullable=True,
                                   comment="Password reset expiration")
    
    # Relationships
    user_group = relationship("UserGroup", back_populates="users")
    user_sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    location_assignments = relationship("UserLocationAssignment", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("UserAuditLog", back_populates="user")
    roles = relationship("Role", secondary="user_roles", back_populates="users")
    
    def __repr__(self):
        return f"<UserProfile(id={self.id}, username='{self.username}', user_group='{self.user_group_code}', status='{self.status}')>"
    
    @property
    def display_name(self) -> str:
        """Get user's display name"""
        return self.user_name or self.full_name or self.username
    
    @property
    def is_locked(self) -> bool:
        """Check if account is currently locked"""
        if self.locked_until:
            return self.locked_until > func.now()
        return False
    
    @property
    def authority_level(self) -> str:
        """Get user's authority level based on user group"""
        if self.user_group:
            if self.user_group.is_national_help_desk:
                return AuthorityLevel.NATIONAL.value
            elif self.user_group.is_provincial_help_desk:
                return AuthorityLevel.PROVINCIAL.value
            else:
                return AuthorityLevel.LOCAL.value
        return AuthorityLevel.PERSONAL.value
    
    @property
    def legacy_user_number(self) -> str:
        """Generate legacy user number format (UserGrpCd + 3-digit sequence)"""
        if self.user_number:
            return self.user_number
        
        # Generate from user group code + sequence
        if self.user_group_code:
            return f"{self.user_group_code}001"  # Placeholder logic
        
        return "UNKNOWN"
    
    def has_permission(self, permission_name: str) -> bool:
        """Check if user has specific permission"""
        if self.is_superuser:
            return True
        
        for role in self.roles:
            if role.is_active:
                for permission in role.permissions:
                    if permission.is_active and permission.name == permission_name:
                        return True
        return False
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has specific role"""
        return any(role.name == role_name and role.is_active for role in self.roles)
    
    def can_access_province(self, province_code: str) -> bool:
        """Check if user can access a specific province"""
        if self.is_superuser:
            return True
        
        if self.user_group:
            if self.user_group.is_national_help_desk:
                return True
            
            if self.user_group.province_code == province_code:
                return True
        
        return self.province_code == province_code
    
    def can_manage_user_group(self, target_group_code: str) -> bool:
        """Check if user can manage another user group"""
        if self.is_superuser:
            return True
        
        if self.user_group:
            return self.user_group.can_manage_user_group(target_group_code)
        
        return False
    
    def can_add_administration_marks(self) -> bool:
        """Check if user can add administration marks (PLAMARK system variable)"""
        if self.is_superuser:
            return True
        
        if self.user_group:
            if self.user_group.is_provincial_help_desk:
                return True
            
            if self.user_group.is_national_help_desk:
                return True
        
        return False


class UserSession(BaseModel):
    """User Session Model implementing documentation Section 1.3"""
    __tablename__ = "user_sessions"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True,
               comment="Session UUID identifier")
    
    # User association
    user_id = Column(UUID(as_uuid=True), ForeignKey('user_profiles.id'), nullable=False, index=True,
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
    user = relationship("UserProfile", back_populates="user_sessions")
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_group='{self.user_group_code}', workstation='{self.workstation_id}')>"
    
    @property
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return self.session_expiry <= func.now()
    
    @property
    def user_profile_display(self) -> str:
        """User profile display name (V01029)"""
        if self.user:
            return f"{self.user.user_name} ({self.user_number})"
        return self.user_number
    
    @property
    def user_group_display(self) -> str:
        """User group display name (V01010)"""
        if self.user and self.user.user_group:
            return self.user.user_group.user_group_name
        return self.user_group_code
    
    @property
    def office_display(self) -> str:
        """Office display name (V00497)"""
        if self.user and self.user.user_group:
            for office in self.user.user_group.offices:
                if office.office_code == self.user.office_code:
                    return office.office_name
        return self.user.office_code if self.user else "Unknown"


# ========================================
# TABLE INDEXES AND CONSTRAINTS
# ========================================

# Additional indexes would be created via migration:
# - idx_user_profiles_user_group_code ON user_profiles(user_group_code)
# - idx_user_profiles_province_code ON user_profiles(province_code)
# - idx_user_profiles_id_number ON user_profiles(id_number)
# - idx_user_profiles_employee_id ON user_profiles(employee_id)
# - idx_user_profiles_status ON user_profiles(status)
# - idx_user_sessions_user_group ON user_sessions(user_group_code)
# - idx_user_sessions_workstation ON user_sessions(workstation_id)
# - idx_user_sessions_active ON user_sessions(is_active, session_expiry) 