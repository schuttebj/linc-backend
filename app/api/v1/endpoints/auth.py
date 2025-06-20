"""
Authentication endpoints for LINC Backend
Handles cross-domain authentication between Render (backend) and Vercel (frontend)

Security Strategy:
- Access tokens for API authentication (stored in memory on frontend)
- Refresh tokens in httpOnly cookies with SameSite=None for cross-domain
- Automatic token refresh
- Secure logout and session management
"""

from datetime import datetime, timedelta
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import uuid
import logging
import structlog

# Internal imports
from app.core.database import get_db
from app.core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    create_refresh_token,
    verify_token,
    decode_token,
    get_current_user  # Import standardized auth function
)
from app.core.config import get_settings
from app.models.user import User, UserStatus
from app.schemas.auth import (
    LoginRequest, 
    LoginResponse, 
    RefreshRequest,
    RefreshResponse,
    UserResponse,
    ChangePasswordRequest
)
# from app.services.audit_service import AuditService  # TODO: Implement audit service

# Router setup
router = APIRouter()
security = HTTPBearer()
logger = structlog.get_logger()
settings = get_settings()

# Constants
REFRESH_TOKEN_EXPIRE_DAYS = 30
ACCESS_TOKEN_EXPIRE_MINUTES = 15

@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    response: Response,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Login endpoint with cross-domain cookie support
    
    Returns:
    - access_token: Short-lived token for API requests (stored in memory)
    - user: User information
    - Sets httpOnly refresh token cookie for automatic token refresh
    """
    try:
        # Find user by username
        user = db.query(User).filter(
            User.username == login_data.username.lower().strip()
        ).first()
        
        if not user:
            # Log failed login attempt
            logger.warning(
                f"Login failed - user not found: {login_data.username}, "
                f"IP: {login_data.ip_address or request.client.host}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Verify password
        if not verify_password(login_data.password, user.password_hash):
            # Log failed login attempt
            logger.warning(
                f"Login failed - invalid password: {login_data.username}, "
                f"IP: {login_data.ip_address or request.client.host}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Check if user is active
        if user.status != UserStatus.ACTIVE.value:
            logger.warning(
                f"Login failed - account inactive: {login_data.username}, "
                f"IP: {login_data.ip_address or request.client.host}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive"
            )
        
        # Create tokens
        access_token = create_access_token(
            data={"sub": str(user.id), "username": user.username},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        refresh_token = create_refresh_token(
            data={"sub": str(user.id), "username": user.username},
            expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        )
        
        # Set refresh token as httpOnly cookie with cross-domain support
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,  # Prevent XSS attacks
            secure=True,    # HTTPS only (required for SameSite=None)
            samesite="none",  # Allow cross-domain (Vercel ↔ Render)
            max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # 30 days
            path="/api/v1/auth"  # Restrict cookie to auth endpoints
        )
        
        # Update user's last login
        user.last_login_at = datetime.utcnow()
        user.last_login_ip = login_data.ip_address or request.client.host
        db.commit()
        
        # Log successful login
        logger.info(
            f"Login successful: {login_data.username}, "
            f"IP: {login_data.ip_address or request.client.host}"
        )
        
        # NEW PERMISSION SYSTEM - Get permissions from permission engine
        permissions = []  # TODO: Get from PermissionEngine.get_user_permissions()
        roles = []        # LEGACY REMOVED - Use user_type_id instead
        
        # Return login response
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse(
                id=str(user.id),
                username=user.username,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                is_active=user.status == UserStatus.ACTIVE.value,
                is_superuser=user.is_superuser,
                roles=roles,
                permissions=permissions,
                last_login_at=user.last_login_at
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to server error"
        )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using httpOnly refresh token cookie
    """
    try:
        # Get refresh token from httpOnly cookie
        refresh_token = request.cookies.get("refresh_token")
        
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found"
            )
        
        # Verify and decode refresh token
        try:
            payload = decode_token(refresh_token)
            user_id = payload.get("sub")
            username = payload.get("username")
            
            if not user_id or not username:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
                
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        # Get user from database
        user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        
        if not user or user.status != UserStatus.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new access token
        new_access_token = create_access_token(
            data={"sub": str(user.id), "username": user.username},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        # Optionally create new refresh token (token rotation)
        new_refresh_token = create_refresh_token(
            data={"sub": str(user.id), "username": user.username},
            expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        )
        
        # Update refresh token cookie
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=True,
            samesite="none",
            max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            path="/api/v1/auth"
        )
        
        # Log token refresh
        logger.info(f"Token refreshed for user: {user.username}, IP: {request.client.host}")
        
        return RefreshResponse(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user)
):
    """
    Logout endpoint - invalidates tokens and clears cookies
    """
    try:
        # User is already authenticated via dependency
        
        # Clear refresh token cookie
        response.delete_cookie(
            key="refresh_token",
            path="/api/v1/auth",
            secure=True,
            samesite="none"
        )
        
        # Log logout event
        logger.info(f"Logout successful: {current_user.username}, IP: {request.client.host}")
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        # Still try to clear the cookie even if there's an error
        response.delete_cookie(
            key="refresh_token",
            path="/api/v1/auth",
            secure=True,
            samesite="none"
        )
        return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information
    """
    try:
        # User is already authenticated and loaded via dependency
        
        # NEW PERMISSION SYSTEM - Get permissions from permission engine
        permissions = []  # TODO: Get from PermissionEngine.get_user_permissions()
        roles = []        # LEGACY REMOVED - Use user_type_id instead
        
        return UserResponse(
            id=str(current_user.id),
            username=current_user.username,
            email=current_user.email,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            is_active=current_user.status == UserStatus.ACTIVE.value,
            is_superuser=current_user.is_superuser,
            roles=roles,
            permissions=permissions,
            last_login_at=current_user.last_login_at
        )
        
    except Exception as e:
        logger.error(f"Get current user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )


@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change user password
    """
    try:
        # User is already authenticated via dependency
        
        # Verify current password
        if not verify_password(password_data.current_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        current_user.password_hash = get_password_hash(password_data.new_password)
        current_user.password_changed_at = datetime.utcnow()
        current_user.updated_at = datetime.utcnow()
        
        db.commit()
        
        # Log password change
        logger.info(f"Password changed for user: {current_user.username}")
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Change password error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@router.get("/test")
async def test_auth_endpoint():
    """
    Test endpoint to verify auth routes are working
    """
    return {
        "message": "Auth endpoints are working",
        "available_endpoints": [
            "POST /auth/login",
            "POST /auth/logout", 
            "POST /auth/refresh",
            "GET /auth/me",
            "POST /auth/change-password",
            "GET /auth/test"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }


# Note: get_current_user is now imported from app.core.security for consistency 