"""
User Management Schemas
Comprehensive user management schemas based on Users_Locations.md specifications
Implements user profiles, user groups, administration marks, and session management
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, EmailStr, validator, Field, root_validator
from enum import Enum
import uuid
import re

# ========================================
# ENUMS AND CONSTANTS
# ========================================

class UserStatus(str, Enum):
    """User account status from documentation"""
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED" 
    INACTIVE = "INACTIVE"
    LOCKED = "LOCKED"
    PENDING_ACTIVATION = "PENDING_ACTIVATION"

class UserType(str, Enum):
    """User type codes from documentation"""
    STANDARD = "1"                      # Standard user
    SYSTEM = "2"                        # System user
    EXAMINER = "3"                      # Examiner
    SUPERVISOR = "4"                    # Supervisor
    ADMIN = "5"                         # Administrator

class IDType(str, Enum):
    """ID Type codes from documentation"""
    TRN = "01"                          # Tax Reference Number
    SA_ID = "02"                        # South African ID
    FOREIGN_ID = "03"                   # Foreign ID
    PASSPORT = "04"                     # Passport
    OTHER = "97"                        # Other ID type

class SystemRole(str, Enum):
    """Core system roles from documentation"""
    EXAMINER = "EXAMINER"
    ADMINISTRATOR = "ADMINISTRATOR"
    DATA_CLERK = "DATA_CLERK"
    QUERY_USER = "QUERY_USER"
    SUPERVISOR = "SUPERVISOR"
    HELP_DESK = "HELP_DESK"
    PROVINCIAL_ADMIN = "PROVINCIAL_ADMIN"
    NATIONAL_ADMIN = "NATIONAL_ADMIN"

class AuthorityLevel(str, Enum):
    """Authority hierarchy levels"""
    NATIONAL = "NATIONAL"               # All provinces, all data
    PROVINCIAL = "PROVINCIAL"           # Single province, all RAs
    REGIONAL = "REGIONAL"               # Multiple RAs within province
    LOCAL = "LOCAL"                     # Single RA/DLTC
    OFFICE = "OFFICE"                   # Single office within RA
    PERSONAL = "PERSONAL"               # Own transactions only

class AdministrationMarkType(str, Enum):
    """Administration mark types"""
    GENERAL = "GENERAL"
    RESTRICTION = "RESTRICTION"
    SUSPENSION = "SUSPENSION"
    INVESTIGATION = "INVESTIGATION"
    SPECIAL_HANDLING = "SPECIAL_HANDLING"

# ========================================
# BASE SCHEMAS
# ========================================

class PersonalDetailsBase(BaseModel):
    """Personal identification details"""
    id_type: IDType = Field(..., description="Identification type")
    id_number: str = Field(..., min_length=1, max_length=20, description="Identification number")
    full_name: str = Field(..., min_length=1, max_length=200, description="Full legal name")
    email: EmailStr = Field(..., description="Email address")
    phone_number: Optional[str] = Field(None, max_length=20, description="Contact phone number")
    alternative_phone: Optional[str] = Field(None, max_length=20, description="Alternative phone number")
    
    @validator('id_number')
    def validate_id_number(cls, v, values):
        """Validate ID number based on ID type"""
        id_type = values.get('id_type')
        
        if id_type in [IDType.TRN, IDType.SA_ID, IDType.PASSPORT]:
            if len(v) != 13:
                raise ValueError(f'{id_type} must be 13 characters long')
            if id_type in [IDType.SA_ID, IDType.TRN] and not v.isdigit():
                raise ValueError(f'{id_type} must be numeric')
        
        return v
    
    @validator('phone_number', 'alternative_phone')
    def validate_phone_number(cls, v):
        """Validate South African phone number format"""
        if v is not None:
            # Remove spaces, hyphens, parentheses
            cleaned = re.sub(r'[\s\-\(\)]', '', v)
            # Check if it matches SA format
            if not re.match(r'^(\+27|0)[1-9]\d{8}$', cleaned):
                raise ValueError('Invalid South African phone number format')
        return v

class GeographicAssignmentBase(BaseModel):
    """Geographic and jurisdictional assignment"""
    country_code: str = Field("ZA", min_length=2, max_length=3, description="Country code")
    province_code: str = Field(..., min_length=2, max_length=2, description="Province code")
    region: Optional[str] = Field(None, max_length=100, description="Regional assignment")
    
    @validator('province_code')
    def validate_province_code(cls, v):
        """Validate South African province codes"""
        valid_provinces = ['EC', 'FS', 'GP', 'KZN', 'LP', 'MP', 'NC', 'NW', 'WC']
        if v not in valid_provinces:
            raise ValueError(f'Invalid province code. Must be one of: {", ".join(valid_provinces)}')
        return v

# ========================================
# USER PROFILE SCHEMAS
# ========================================

class UserProfileBase(BaseModel):
    """Base user profile schema"""
    # Core identification (NEW - following documentation)
    user_group_code: str = Field(..., min_length=4, max_length=4, description="User group code (SCHAR2)")
    office_code: str = Field(..., min_length=1, max_length=1, description="Office code within user group (SCHAR1)")
    user_name: str = Field(..., min_length=1, max_length=30, description="Display name for user (SCHAR1)")
    user_type_code: UserType = Field(UserType.STANDARD, description="User type code")
    
    # Personal details
    personal_details: PersonalDetailsBase = Field(..., description="Personal identification details")
    
    # Geographic assignment
    geographic_assignment: GeographicAssignmentBase = Field(..., description="Geographic assignment")
    
    # Job details
    employee_id: Optional[str] = Field(None, max_length=50, description="Employee/staff ID number")
    department: Optional[str] = Field(None, max_length=100, description="Department or division")
    job_title: Optional[str] = Field(None, max_length=100, description="Job title")
    
    # Infrastructure assignment (for DLTC users)
    infrastructure_number: Optional[str] = Field(None, max_length=20, description="Infrastructure number for DLTC users")
    
    # System settings
    language: str = Field("en", max_length=10, description="Preferred language")
    timezone: str = Field("Africa/Johannesburg", max_length=50, description="User timezone")
    date_format: str = Field("YYYY-MM-DD", max_length=20, description="Preferred date format")
    
    @validator('user_group_code')
    def validate_user_group_code(cls, v):
        """Validate user group code format"""
        if not re.match(r'^[A-Z]{2}\d{2}$', v):
            raise ValueError('User group code must be format LLNN (e.g., WC01, GP03)')
        return v
    
    @validator('office_code')
    def validate_office_code(cls, v):
        """Validate office code format"""
        if not re.match(r'^[A-Z]$', v):
            raise ValueError('Office code must be a single uppercase letter (A-Z)')
        return v
    
    @validator('user_name')
    def validate_user_name(cls, v):
        """Validate user name format"""
        if not re.match(r'^[a-zA-Z0-9\s\.\-\']+$', v):
            raise ValueError('User name contains invalid characters')
        return v

class UserProfileCreate(UserProfileBase):
    """User profile creation schema"""
    # Authentication
    username: str = Field(..., min_length=3, max_length=50, description="System username")
    password: str = Field(..., min_length=8, description="Initial password")
    
    # Status
    status: UserStatus = Field(UserStatus.PENDING_ACTIVATION, description="Initial account status")
    is_active: bool = Field(True, description="Active flag")
    
    # Role assignments
    role_ids: List[str] = Field([], description="List of role IDs to assign")
    permission_ids: List[str] = Field([], description="Additional permission IDs")
    
    # Security
    require_password_change: bool = Field(True, description="Require password change on first login")
    require_2fa: bool = Field(False, description="Require two-factor authentication")
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            raise ValueError('Password must contain at least one special character')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format"""
        if not re.match(r'^[a-zA-Z0-9_\-\.]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, hyphens, and dots')
        return v

class UserProfileUpdate(BaseModel):
    """User profile update schema"""
    # Personal details can be updated
    personal_details: Optional[PersonalDetailsBase] = None
    
    # Job details
    employee_id: Optional[str] = Field(None, max_length=50)
    department: Optional[str] = Field(None, max_length=100)
    job_title: Optional[str] = Field(None, max_length=100)
    
    # Geographic assignment (restricted - requires elevated permissions)
    province_code: Optional[str] = Field(None, min_length=2, max_length=2)
    region: Optional[str] = Field(None, max_length=100)
    
    # User group assignment (restricted - requires elevated permissions)
    user_group_code: Optional[str] = Field(None, min_length=4, max_length=4)
    office_code: Optional[str] = Field(None, min_length=1, max_length=1)
    
    # Infrastructure assignment
    infrastructure_number: Optional[str] = Field(None, max_length=20)
    
    # System settings
    language: Optional[str] = Field(None, max_length=10)
    timezone: Optional[str] = Field(None, max_length=50)
    date_format: Optional[str] = Field(None, max_length=20)
    
    # Status (restricted - requires admin permissions)
    status: Optional[UserStatus] = None
    is_active: Optional[bool] = None
    
    # Role assignments (restricted - requires admin permissions)
    role_ids: Optional[List[str]] = None
    permission_ids: Optional[List[str]] = None

class UserProfileResponse(BaseModel):
    """User profile response schema"""
    # System fields
    id: str = Field(..., description="User UUID")
    username: str = Field(..., description="System username")
    
    # Core user profile (following documentation structure)
    user_group_code: str = Field(..., description="User group code")
    office_code: str = Field(..., description="Office code")
    user_name: str = Field(..., description="Display name")
    user_type_code: str = Field(..., description="User type code")
    
    # Personal details
    personal_details: PersonalDetailsBase = Field(..., description="Personal details")
    
    # Geographic assignment
    geographic_assignment: GeographicAssignmentBase = Field(..., description="Geographic assignment")
    
    # Job details
    employee_id: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    infrastructure_number: Optional[str] = None
    
    # Status
    status: UserStatus
    is_active: bool
    is_superuser: bool = Field(False, description="Superuser flag")
    is_verified: bool = Field(False, description="Email verification status")
    
    # Authority level (computed)
    authority_level: AuthorityLevel
    
    # User group information
    user_group: Optional[Dict[str, Any]] = None
    office: Optional[Dict[str, Any]] = None
    
    # Roles and permissions
    roles: List[Dict[str, Any]] = Field(default=[], description="Assigned roles")
    permissions: List[str] = Field(default=[], description="All permissions")
    
    # Location assignments
    location_assignments: List[Dict[str, Any]] = Field(default=[], description="Location assignments")
    
    # System settings
    language: str
    timezone: str
    date_format: str
    
    # Audit fields
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    last_login_at: Optional[datetime] = None
    
    @validator('id', pre=True)
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v
    
    class Config:
        from_attributes = True

# ========================================
# USER SESSION SCHEMAS
# ========================================

class UserSessionBase(BaseModel):
    """User session schema"""
    user_group_code: str = Field(..., description="Session user group")
    user_number: str = Field(..., description="Legacy user number (7 chars: 4+3)")
    workstation_id: str = Field(..., max_length=10, description="Workstation identifier")
    session_type: str = Field("interactive", description="Session type")

class UserSessionCreate(UserSessionBase):
    """User session creation"""
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")

class UserSessionResponse(UserSessionBase):
    """User session response"""
    id: str = Field(..., description="Session UUID")
    user_id: str = Field(..., description="User UUID")
    session_start: datetime = Field(..., description="Session start time")
    session_expiry: datetime = Field(..., description="Session expiry time")
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool = Field(True, description="Session active status")
    
    # User profile display (following documentation V01029, V01030)
    user_profile_display: str = Field(..., description="User profile display name")
    user_group_display: str = Field(..., description="User group display name")
    office_display: str = Field(..., description="Office display name")
    
    @validator('id', 'user_id', pre=True)
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v
    
    class Config:
        from_attributes = True

# ========================================
# USER MANAGEMENT UTILITIES
# ========================================

class UserListFilter(BaseModel):
    """User list filtering schema"""
    # Status filters
    status: Optional[UserStatus] = None
    is_active: Optional[bool] = None
    user_type: Optional[UserType] = None
    
    # Geographic filters
    province_code: Optional[str] = None
    user_group_code: Optional[str] = None
    office_code: Optional[str] = None
    
    # Role filters
    role_name: Optional[str] = None
    authority_level: Optional[AuthorityLevel] = None
    
    # Department filters
    department: Optional[str] = None
    
    # Search
    search: Optional[str] = Field(None, description="Search in name, username, email")
    
    # Date filters
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    last_login_after: Optional[datetime] = None
    last_login_before: Optional[datetime] = None

class UserListResponse(BaseModel):
    """User list response with pagination"""
    users: List[UserProfileResponse] = Field(default=[], description="List of users")
    total: int = Field(0, description="Total number of users")
    page: int = Field(1, description="Current page")
    size: int = Field(20, description="Page size")
    pages: int = Field(0, description="Total pages")
    has_next: bool = Field(False, description="Has next page")
    has_previous: bool = Field(False, description="Has previous page")

class UserStatistics(BaseModel):
    """User management statistics"""
    total_users: int = Field(0, description="Total users")
    active_users: int = Field(0, description="Active users")
    inactive_users: int = Field(0, description="Inactive users")
    suspended_users: int = Field(0, description="Suspended users")
    pending_activation: int = Field(0, description="Pending activation")
    
    # By type
    by_user_type: Dict[str, int] = Field(default={}, description="Users by type")
    by_province: Dict[str, int] = Field(default={}, description="Users by province")
    by_user_group: Dict[str, int] = Field(default={}, description="Users by user group")
    by_authority_level: Dict[str, int] = Field(default={}, description="Users by authority level")
    
    # Recent activity
    new_users_this_month: int = Field(0, description="New users this month")
    active_sessions: int = Field(0, description="Currently active sessions")
    recent_logins: int = Field(0, description="Logins in last 24 hours")

# ========================================
# VALIDATION AND BUSINESS RULES
# ========================================

class UserValidationResult(BaseModel):
    """User validation result"""
    is_valid: bool = Field(..., description="Overall validation result")
    validation_errors: List[str] = Field(default=[], description="Validation error messages")
    validation_warnings: List[str] = Field(default=[], description="Validation warnings")
    business_rule_violations: List[str] = Field(default=[], description="Business rule violations")
    
    # Specific validation checks (following documentation rules)
    user_group_valid: bool = Field(True, description="V-USER-001: User Group must be active and valid")
    office_valid: bool = Field(True, description="V-USER-002: Office must exist within selected User Group")
    user_name_unique: bool = Field(True, description="V-USER-003: User Name must be unique within User Group")
    email_unique: bool = Field(True, description="V-USER-004: Email must be valid and unique system-wide")
    id_number_valid: bool = Field(True, description="V-USER-005: ID Number must be valid for selected ID Type")

class PermissionCheckResult(BaseModel):
    """Permission check result"""
    has_permission: bool = Field(..., description="Permission check result")
    permission_name: str = Field(..., description="Permission being checked")
    user_id: str = Field(..., description="User being checked")
    reason: Optional[str] = Field(None, description="Reason for permission grant/denial")
    authority_level: AuthorityLevel = Field(..., description="User's authority level")
    applicable_constraints: List[str] = Field(default=[], description="Applicable permission constraints")

# ========================================
# EXPORT SCHEMAS
# ========================================

class UserExportFilter(UserListFilter):
    """User export filter schema"""
    export_format: str = Field("csv", description="Export format (csv, xlsx, json)")
    include_sensitive_data: bool = Field(False, description="Include sensitive information")
    include_audit_trail: bool = Field(False, description="Include audit information")

class UserExportResponse(BaseModel):
    """User export response"""
    export_id: str = Field(..., description="Export job UUID")
    status: str = Field("processing", description="Export status")
    file_url: Optional[str] = Field(None, description="Download URL when ready")
    created_at: datetime = Field(..., description="Export creation time")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    record_count: int = Field(0, description="Number of records to export") 