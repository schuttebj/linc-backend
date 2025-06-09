"""
Authentication API Endpoints
Handles user authentication, authorization, and session management
"""

from datetime import datetime, timedelta
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import structlog

from app.core.database import get_db
from app.core.security import get_current_user
from app.services.user_service import UserService
from app.schemas.user import (
    UserLogin, UserLoginResponse, UserResponse,
    TokenRefresh, TokenResponse,
    PasswordReset, PasswordResetConfirm, PasswordChange
)
from app.models.user import User

logger = structlog.get_logger()
router = APIRouter()
security = HTTPBearer()

@router.post("/login", response_model=UserLoginResponse)
async def login(
    user_credentials: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    User login endpoint
    
    Authenticates user credentials and returns access/refresh tokens
    Implements authentication business rules from documentation
    """
    try:
        logger.info("User login attempt", username=user_credentials.username)
        
        user_service = UserService(db)
        
        # Get client IP address
        client_ip = request.client.host if request.client else None
        
        # Authenticate user
        user = await user_service.authenticate_user(
            username=user_credentials.username,
            password=user_credentials.password,
            ip_address=client_ip
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Create tokens
        tokens = await user_service.create_tokens(user)
        
        # Prepare response
        user_response = UserResponse.from_orm(user)
        
        response = UserLoginResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            expires_in=tokens["expires_in"],
            user=user_response
        )
        
        logger.info("User logged in successfully", 
                   user_id=user.id, username=user.username)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Login error", username=user_credentials.username, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to server error"
        )

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    User logout endpoint
    
    Invalidates current user session and tokens
    """
    try:
        logger.info("User logout", user_id=current_user.id, username=current_user.username)
        
        # Invalidate current token
        current_user.current_token_id = None
        current_user.token_expires_at = None
        current_user.refresh_token_hash = None
        
        db.commit()
        
        user_service = UserService(db)
        await user_service._log_audit(
            current_user.id, "logout", "authentication", success=True
        )
        
        logger.info("User logged out successfully", 
                   user_id=current_user.id, username=current_user.username)
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        logger.error("Logout error", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed due to server error"
        )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: TokenRefresh,
    db: Session = Depends(get_db)
):
    """
    Token refresh endpoint
    
    Exchanges refresh token for new access token
    """
    try:
        logger.info("Token refresh attempt")
        
        user_service = UserService(db)
        
        # Verify and refresh token
        new_tokens = await user_service.security_manager.refresh_access_token(
            token_data.refresh_token
        )
        
        if not new_tokens:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        response = TokenResponse(
            access_token=new_tokens["access_token"],
            token_type="bearer",
            expires_in=new_tokens["expires_in"]
        )
        
        logger.info("Token refreshed successfully")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Token refresh error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information
    
    Returns detailed information about the authenticated user
    """
    try:
        logger.info("Get current user info", user_id=current_user.id)
        
        return UserResponse.from_orm(current_user)
        
    except Exception as e:
        logger.error("Get current user error", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information"
        )

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change user password
    
    Allows authenticated users to change their password
    """
    try:
        logger.info("Password change attempt", user_id=current_user.id)
        
        user_service = UserService(db)
        
        success = await user_service.change_password(
            user_id=str(current_user.id),
            current_password=password_data.current_password,
            new_password=password_data.new_password
        )
        
        if success:
            logger.info("Password changed successfully", user_id=current_user.id)
            return {"message": "Password changed successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to change password"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Password change error", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )

@router.post("/forgot-password")
async def forgot_password(
    reset_data: PasswordReset,
    db: Session = Depends(get_db)
):
    """
    Initiate password reset
    
    Sends password reset email to user (placeholder for future email integration)
    """
    try:
        logger.info("Password reset request", email=reset_data.email)
        
        user_service = UserService(db)
        user = await user_service.get_user_by_username(reset_data.email)
        
        if user:
            # In a real implementation, you would:
            # 1. Generate a secure reset token
            # 2. Store it with expiration time
            # 3. Send email with reset link
            # For now, we'll just log the attempt
            
            await user_service._log_audit(
                str(user.id), "password_reset_requested", "security",
                success=True, details=f"Password reset requested for {reset_data.email}"
            )
            
            logger.info("Password reset email would be sent", 
                       user_id=user.id, email=reset_data.email)
        
        # Always return success to prevent email enumeration
        return {
            "message": "If the email exists in our system, a password reset link has been sent"
        }
        
    except Exception as e:
        logger.error("Forgot password error", email=reset_data.email, error=str(e))
        # Still return success message to prevent information disclosure
        return {
            "message": "If the email exists in our system, a password reset link has been sent"
        }

@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """
    Complete password reset
    
    Resets user password using valid reset token (placeholder implementation)
    """
    try:
        logger.info("Password reset confirmation attempt")
        
        # This is a placeholder implementation
        # In a real system, you would:
        # 1. Validate the reset token
        # 2. Check if it's not expired
        # 3. Update the user's password
        # 4. Invalidate the reset token
        
        # For now, return an error indicating this feature is not fully implemented
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Password reset functionality will be implemented in Phase 2"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Password reset error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )

@router.get("/permissions")
async def get_user_permissions(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user permissions
    
    Returns list of permissions for the authenticated user
    """
    try:
        logger.info("Get user permissions", user_id=current_user.id)
        
        permissions = []
        
        if current_user.is_superuser:
            permissions.append("*")  # Superuser has all permissions
        else:
            for role in current_user.roles:
                if role.is_active:
                    for permission in role.permissions:
                        if permission.is_active:
                            permissions.append(permission.name)
        
        return {
            "user_id": str(current_user.id),
            "username": current_user.username,
            "roles": [role.name for role in current_user.roles if role.is_active],
            "permissions": list(set(permissions))  # Remove duplicates
        }
        
    except Exception as e:
        logger.error("Get permissions error", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user permissions"
        )

@router.get("/roles")
async def get_user_roles(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user roles
    
    Returns list of roles for the authenticated user
    """
    try:
        logger.info("Get user roles", user_id=current_user.id)
        
        roles = []
        for role in current_user.roles:
            if role.is_active:
                roles.append({
                    "id": str(role.id),
                    "name": role.name,
                    "display_name": role.display_name,
                    "description": role.description
                })
        
        return {
            "user_id": str(current_user.id),
            "username": current_user.username,
            "roles": roles
        }
        
    except Exception as e:
        logger.error("Get roles error", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user roles"
        )

@router.post("/validate-token")
async def validate_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Validate authentication token
    
    Validates the provided JWT token and returns user information
    """
    try:
        logger.info("Token validation request")
        
        # Get current user will validate the token
        current_user = await get_current_user(credentials, db)
        
        return {
            "valid": True,
            "user_id": str(current_user.id),
            "username": current_user.username,
            "expires_at": current_user.token_expires_at.isoformat() if current_user.token_expires_at else None
        }
        
    except HTTPException as e:
        logger.info("Invalid token validation attempt")
        return {
            "valid": False,
            "error": e.detail
        }
    except Exception as e:
        logger.error("Token validation error", error=str(e))
        return {
            "valid": False,
            "error": "Token validation failed"
        } 