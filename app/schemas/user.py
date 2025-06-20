"""
User Management Schemas
Pydantic models for user authentication and authorization
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from enum import Enum
import uuid

class UserStatus(str, Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    LOCKED = "locked"
    PENDING_ACTIVATION = "pending_activation"

# Authentication Schemas
class UserLogin(BaseModel):
    """User login request schema"""
    username: str = Field(..., min_length=3, max_length=50, description="Username or email")
    password: str = Field(..., min_length=8, description="Password")
    remember_me: bool = Field(False, description="Remember login session")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin",
                "password": "SecurePassword123!",
                "remember_me": False
            }
        }

class UserLoginResponse(BaseModel):
    """User login response schema"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "username": "admin",
                    "email": "admin@linc.gov.za",
                    "full_name": "System Administrator"
                }
            }
        }

class TokenRefresh(BaseModel):
    """Token refresh request schema"""
    refresh_token: str

class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class PasswordReset(BaseModel):
    """Password reset request schema"""
    email: EmailStr
    
class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema"""
    token: str
    new_password: str = Field(..., min_length=8, description="New password")
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class PasswordChange(BaseModel):
    """Password change schema"""
    current_password: str
    new_password: str = Field(..., min_length=8)
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

# User Management Schemas
class UserBase(BaseModel):
    """Base user schema"""
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="Email address")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    display_name: Optional[str] = Field(None, max_length=200, description="Display name")
    phone_number: Optional[str] = Field(None, max_length=20, description="Phone number")
    employee_id: Optional[str] = Field(None, max_length=50, description="Employee ID")
    department: Optional[str] = Field(None, max_length=100, description="Department")
    country_code: str = Field("ZA", min_length=2, max_length=3, description="Country code")
    province: Optional[str] = Field(None, max_length=100, description="Province")
    region: Optional[str] = Field(None, max_length=100, description="Region")
    office_location: Optional[str] = Field(None, max_length=200, description="Office location")
    language: str = Field("en", max_length=10, description="Preferred language")
    timezone: str = Field("Africa/Johannesburg", max_length=50, description="Timezone")

class UserCreate(UserBase):
    """User creation schema"""
    password: str = Field(..., min_length=8, description="Password")
    role_ids: List[str] = Field([], description="List of role IDs to assign")
    is_active: bool = Field(True, description="Active status")
    require_password_change: bool = Field(False, description="Require password change on first login")
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "jsmith",
                "email": "john.smith@linc.gov.za",
                "first_name": "John",
                "last_name": "Smith",
                "password": "SecurePassword123!",
                "employee_id": "EMP001",
                "department": "License Operations",
                "role_ids": ["operator-role-id"]
            }
        }

class UserUpdate(BaseModel):
    """User update schema"""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, max_length=200)
    phone_number: Optional[str] = Field(None, max_length=20)
    employee_id: Optional[str] = Field(None, max_length=50)
    department: Optional[str] = Field(None, max_length=100)
    province: Optional[str] = Field(None, max_length=100)
    region: Optional[str] = Field(None, max_length=100)
    office_location: Optional[str] = Field(None, max_length=200)
    language: Optional[str] = Field(None, max_length=10)
    timezone: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    status: Optional[UserStatus] = None
    role_ids: Optional[List[str]] = None

class UserResponse(BaseModel):
    """User response schema"""
    id: str
    username: str
    email: str
    first_name: str
    last_name: str
    full_name: str = ""
    display_name: Optional[str] = None
    phone_number: Optional[str] = None
    employee_id: Optional[str] = None
    department: Optional[str] = None
    country_code: str
    province: Optional[str] = None
    region: Optional[str] = None
    office_location: Optional[str] = None
    status: UserStatus
    is_active: bool
    is_superuser: bool = False
    is_verified: bool = False
    language: str = "en"
    timezone: str = "Africa/Johannesburg"
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # New permission system fields
    user_type_id: Optional[str] = None
    assigned_province: Optional[str] = None
    permission_overrides: Optional[List[str]] = None

    @model_validator(mode='before')
    @classmethod
    def convert_user_model(cls, values):
        """Convert User model to response format"""
        if hasattr(values, '__dict__'):
            # Convert SQLAlchemy model to dict
            data = {}
            for key, value in values.__dict__.items():
                if not key.startswith('_'):
                    data[key] = value
        else:
            data = values if isinstance(values, dict) else {}
        
        # Handle full_name - ensure it's never None
        if 'full_name' not in data or not data.get('full_name'):
            first_name = data.get('first_name') or ''
            last_name = data.get('last_name') or ''
            data['full_name'] = f"{first_name} {last_name}".strip() or "Unknown User"
        
        # Convert status to lowercase for enum
        if 'status' in data and data['status']:
            data['status'] = data['status'].lower()
        else:
            data['status'] = 'active'  # Default status
            
        # Ensure required string fields are not None
        string_fields = ['first_name', 'last_name', 'country_code', 'language', 'timezone']
        for field in string_fields:
            if field not in data or data[field] is None:
                if field == 'first_name':
                    data[field] = ''
                elif field == 'last_name':
                    data[field] = ''
                elif field == 'country_code':
                    data[field] = 'ZA'
                elif field == 'language':
                    data[field] = 'en'
                elif field == 'timezone':
                    data[field] = 'Africa/Johannesburg'
        
        # Ensure boolean fields have defaults
        boolean_fields = ['is_active', 'is_superuser', 'is_verified']
        for field in boolean_fields:
            if field not in data or data[field] is None:
                data[field] = False
        
        # Handle assigned_province mapping
        if 'assigned_province' not in data and 'province' in data:
            data['assigned_province'] = data['province']
            
        # Ensure datetime fields are handled properly
        datetime_fields = ['created_at', 'updated_at', 'last_login_at']
        for field in datetime_fields:
            if field in data and data[field] is None and field == 'created_at':
                # created_at should never be None, use current time if missing
                from datetime import datetime as dt
                data[field] = dt.utcnow()
        
        return data

    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        """Convert UUID to string"""
        return str(v) if v else None

    @field_validator('status', mode='before')
    @classmethod
    def convert_status(cls, v):
        """Convert status to lowercase"""
        if isinstance(v, str):
            return v.lower()
        return v

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "username": "jsmith",
                "email": "john.smith@linc.gov.za",
                "first_name": "John",
                "last_name": "Smith",
                "full_name": "John Smith",
                "status": "active",
                "is_active": True,
                "user_type_id": "license_operator",
                "assigned_province": "WC"
            }
        }

# Role Management Schemas
class RoleBase(BaseModel):
    """Base role schema"""
    name: str = Field(..., min_length=1, max_length=50, description="Role name")
    display_name: str = Field(..., min_length=1, max_length=100, description="Display name")
    description: Optional[str] = Field(None, description="Role description")
    is_active: bool = Field(True, description="Active status")
    parent_role_id: Optional[str] = Field(None, description="Parent role ID")

class RoleCreate(RoleBase):
    """Role creation schema"""
    permission_ids: List[str] = Field([], description="List of permission IDs")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "license_operator",
                "display_name": "License Operator",
                "description": "Can process license applications and manage customer data",
                "permission_ids": ["license.create", "license.read", "license.update"]
            }
        }

class RoleUpdate(BaseModel):
    """Role update schema"""
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    permission_ids: Optional[List[str]] = None

class RoleResponse(BaseModel):
    """Role response schema"""
    id: str
    name: str
    display_name: str
    description: Optional[str]
    is_active: bool
    is_system_role: bool
    level: int
    created_at: datetime
    permissions: List["PermissionResponse"] = []
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v
    
    class Config:
        from_attributes = True

# Permission Management Schemas
class PermissionBase(BaseModel):
    """Base permission schema"""
    name: str = Field(..., min_length=1, max_length=100, description="Permission name")
    display_name: str = Field(..., min_length=1, max_length=150, description="Display name")
    description: Optional[str] = Field(None, description="Permission description")
    category: str = Field(..., min_length=1, max_length=50, description="Category")
    resource: str = Field(..., min_length=1, max_length=100, description="Resource")
    action: str = Field(..., min_length=1, max_length=50, description="Action")
    is_active: bool = Field(True, description="Active status")

class PermissionCreate(PermissionBase):
    """Permission creation schema"""
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "license.application.create",
                "display_name": "Create License Application",
                "description": "Permission to create new license applications",
                "category": "license",
                "resource": "license_application",
                "action": "create"
            }
        }

class PermissionUpdate(BaseModel):
    """Permission update schema"""
    display_name: Optional[str] = Field(None, min_length=1, max_length=150)
    description: Optional[str] = None
    is_active: Optional[bool] = None

class PermissionResponse(BaseModel):
    """Permission response schema"""
    id: str
    name: str
    display_name: str
    description: Optional[str]
    category: str
    resource: str
    action: str
    is_active: bool
    is_system_permission: bool
    created_at: datetime
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v
    
    class Config:
        from_attributes = True

# Audit Log Schemas
class UserAuditLogResponse(BaseModel):
    """User audit log response schema"""
    id: str
    user_id: str
    action: str
    resource: Optional[str]
    resource_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    endpoint: Optional[str]
    method: Optional[str]
    success: bool
    error_message: Optional[str]
    details: Optional[str]
    created_at: datetime
    user: Optional[UserResponse]
    
    @field_validator('id', 'user_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v
    
    class Config:
        from_attributes = True

# User Profile and Preferences
class UserProfile(BaseModel):
    """User profile schema"""
    display_name: Optional[str] = None
    language: str = "en"
    timezone: str = "Africa/Johannesburg"
    date_format: str = "YYYY-MM-DD"
    
class UserPreferences(BaseModel):
    """User preferences schema"""
    notifications_enabled: bool = True
    email_notifications: bool = True
    sms_notifications: bool = False
    theme: str = "light"
    items_per_page: int = Field(20, ge=10, le=100)

# Two-Factor Authentication
class Enable2FA(BaseModel):
    """Enable 2FA schema"""
    password: str
    
class Confirm2FA(BaseModel):
    """Confirm 2FA setup schema"""
    totp_code: str = Field(..., min_length=6, max_length=6)
    
class Verify2FA(BaseModel):
    """Verify 2FA code schema"""
    totp_code: str = Field(..., min_length=6, max_length=6)

# List and Filter Schemas
class UserListFilter(BaseModel):
    """User list filter schema"""
    status: Optional[UserStatus] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None
    department: Optional[str] = None
    country_code: Optional[str] = None
    search: Optional[str] = None
    
class UserListResponse(BaseModel):
    """User list response schema"""
    users: List[UserResponse]
    total: int
    page: int
    size: int
    pages: int

class UserPermissionResponse(BaseModel):
    """User permission response schema"""
    name: str
    display_name: str
    description: Optional[str]
    category: str
    
    class Config:
        from_attributes = True

class UserRoleResponse(BaseModel):
    """User role response schema"""
    name: str
    display_name: str
    description: Optional[str]
    level: int
    
    class Config:
        from_attributes = True

# Update forward references
UserLoginResponse.model_rebuild()
UserResponse.model_rebuild()
RoleResponse.model_rebuild()
UserAuditLogResponse.model_rebuild()

class PasswordChangeRequest(BaseModel):
    """Password change request schema"""
    current_password: str = Field(..., min_length=1, description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")

class PasswordResetRequest(BaseModel):
    """Password reset request schema"""
    email: EmailStr = Field(..., description="Email address")
    new_password: str = Field(..., min_length=8, description="New password")

class LoginRequest(BaseModel):
    """Login request schema"""
    username: str = Field(..., min_length=1, description="Username")
    password: str = Field(..., min_length=1, description="Password")

class UserDetailResponse(BaseModel):
    """User detail response schema"""
    id: str
    username: str
    email: str
    first_name: str
    last_name: str
    full_name: str = ""
    user_type_id: Optional[str]
    assigned_province: Optional[str]
    permission_overrides: Optional[Dict[str, Any]]
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    """User list response schema"""
    id: str
    username: str
    email: str
    first_name: str
    last_name: str
    full_name: str = ""
    user_type_id: Optional[str]
    assigned_province: Optional[str]
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserSessionResponse(BaseModel):
    """User session response schema"""
    id: str
    user_id: str
    session_token: str
    expires_at: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True 