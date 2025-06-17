"""
User Management Schemas
Pydantic models for user authentication and authorization
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, validator, Field
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
    
    @validator('new_password')
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
    
    @validator('new_password')
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
    
    @validator('password')
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
    full_name: Optional[str] = None
    display_name: Optional[str]
    phone_number: Optional[str]
    employee_id: Optional[str]
    department: Optional[str]
    country_code: str
    province: Optional[str]
    region: Optional[str]
    office_location: Optional[str]
    status: UserStatus
    is_active: bool
    is_superuser: bool
    is_verified: bool
    language: str
    timezone: str
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    roles: List["RoleResponse"] = []
    
    @validator('full_name', pre=True, always=True)
    def generate_full_name(cls, v, values):
        """Generate full_name from first_name and last_name if not provided"""
        if v is None:
            first_name = values.get('first_name', '')
            last_name = values.get('last_name', '')
            return f"{first_name} {last_name}".strip() if first_name or last_name else "Unknown User"
        return v
    
    @validator('id', pre=True)
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
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
                "roles": [
                    {
                        "id": "role-id",
                        "name": "operator",
                        "display_name": "License Operator"
                    }
                ]
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
    
    @validator('id', pre=True)
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
    
    @validator('id', pre=True)
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
    
    @validator('id', 'user_id', pre=True)
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