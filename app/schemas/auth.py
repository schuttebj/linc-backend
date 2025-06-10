"""
Authentication schemas for LINC Backend
Pydantic models for authentication requests and responses
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime

# Login Request/Response
class LoginRequest(BaseModel):
    """Login request schema"""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=6, description="Password")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin",
                "password": "password123"
            }
        }

class UserResponse(BaseModel):
    """User information response"""
    id: str = Field(..., description="User UUID")
    username: str = Field(..., description="Username")
    email: Optional[str] = Field(None, description="Email address")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    is_active: bool = Field(..., description="Whether user is active")
    is_superuser: bool = Field(..., description="Whether user is superuser")
    roles: List[str] = Field(default=[], description="User roles")
    permissions: List[str] = Field(default=[], description="User permissions")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "username": "admin",
                "email": "admin@example.com",
                "first_name": "Admin",
                "last_name": "User",
                "is_active": True,
                "is_superuser": True,
                "roles": ["admin"],
                "permissions": ["person:read", "person:create"],
                "last_login_at": "2024-01-01T10:00:00Z"
            }
        }

class LoginResponse(BaseModel):
    """Login response schema"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    user: UserResponse = Field(..., description="User information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 900,
                "user": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "username": "admin",
                    "email": "admin@example.com",
                    "first_name": "Admin",
                    "last_name": "User",
                    "is_active": True,
                    "is_superuser": True,
                    "roles": ["admin"],
                    "permissions": ["person:read", "person:create"]
                }
            }
        }

# Token Refresh
class RefreshRequest(BaseModel):
    """Token refresh request (for future use if needed)"""
    refresh_token: Optional[str] = Field(None, description="Refresh token")

class RefreshResponse(BaseModel):
    """Token refresh response"""
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 900
            }
        }

# Password Change
class ChangePasswordRequest(BaseModel):
    """Change password request"""
    current_password: str = Field(..., min_length=6, description="Current password")
    new_password: str = Field(..., min_length=6, description="New password")
    
    class Config:
        json_schema_extra = {
            "example": {
                "current_password": "oldpassword123",
                "new_password": "newpassword456"
            }
        }

class ChangePasswordResponse(BaseModel):
    """Change password response"""
    message: str = Field(..., description="Success message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Password changed successfully"
            }
        }

# Error Responses
class AuthErrorResponse(BaseModel):
    """Authentication error response"""
    detail: str = Field(..., description="Error message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Invalid username or password"
            }
        } 