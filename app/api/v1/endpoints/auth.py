"""
Authentication API Endpoints
Handles user authentication, authorization, and session management
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import structlog

from app.core.database import get_db
from app.core.security import get_current_user, get_current_active_superuser
from app.services.user_service import UserService
from app.schemas.user import (
    UserLogin, UserLoginResponse, UserResponse,
    TokenRefresh, TokenResponse,
    PasswordReset, PasswordResetConfirm, PasswordChange,
    UserPermissionResponse, UserRoleResponse
)
from app.models.user import User, Role, Permission, UserRole, RolePermission, UserStatus
from app.core.config import get_settings
from app.core.security import create_access_token, verify_password
import uuid
from app.core.security import get_password_hash

logger = structlog.get_logger()
router = APIRouter()
security = HTTPBearer()
settings = get_settings()

@router.post("/login", response_model=UserLoginResponse)
async def login(
    user_credentials: UserLogin,
    background_tasks: BackgroundTasks,
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
        client_ip = user_credentials.ip_address if user_credentials.ip_address else None
        
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
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username, "user_id": str(user.id)},
            expires_delta=access_token_expires
        )
        
        # Prepare response
        user_response = UserResponse.from_orm(user)
        
        response = UserLoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_response
        )
        
        # Log successful login
        background_tasks.add_task(
            user_service.log_user_action,
            user_id=user.id,
            action="login",
            ip_address=client_ip,
            success=True
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
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
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
        
        # Logout action
        background_tasks.add_task(
            lambda: None  # Placeholder for logout action
        )
        
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
    background_tasks: BackgroundTasks,
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
        
        # Verify current password
        if not verify_password(password_data.current_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid current password"
            )
        
        # Update password
        await user_service.update_user_password(
            user_id=current_user.id,
            new_password=password_data.new_password
        )
        
        # Log password change
        background_tasks.add_task(
            user_service.log_user_action,
            user_id=current_user.id,
            action="password_change",
            success=True
        )
        
        logger.info("Password changed successfully", user_id=current_user.id)
        return {"message": "Password changed successfully"}
            
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

@router.get("/permissions", response_model=List[UserPermissionResponse])
async def get_current_user_permissions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user permissions
    
    Returns list of permissions for the authenticated user
    """
    try:
        logger.info("Get user permissions", user_id=current_user.id)
        
        user_service = UserService(db)
        permissions = await user_service.get_user_permissions(current_user.id)
        
        return [
            UserPermissionResponse(
                name=perm.name,
                display_name=perm.display_name,
                description=perm.description,
                category=perm.category
            )
            for perm in permissions
        ]
        
    except Exception as e:
        logger.error("Get permissions error", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user permissions"
        )

@router.get("/roles", response_model=List[UserRoleResponse])
async def get_current_user_roles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user roles
    
    Returns list of roles for the authenticated user
    """
    try:
        logger.info("Get user roles", user_id=current_user.id)
        
        user_service = UserService(db)
        roles = await user_service.get_user_roles(current_user.id)
        
        return [
            UserRoleResponse(
                name=role.name,
                display_name=role.display_name,
                description=role.description,
                level=role.level
            )
            for role in roles
        ]
        
    except Exception as e:
        logger.error("Get roles error", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user roles"
        )

@router.post("/validate-token")
async def validate_token(
    current_user: User = Depends(get_current_user)
):
    """
    Validate if current token is valid
    """
    return {
        "valid": True,
        "user_id": str(current_user.id),
        "username": current_user.username
    }

@router.post("/initialize-system")
async def initialize_system(
    db: Session = Depends(get_db)
):
    """
    Initialize the authentication system with default users and roles
    TEMPORARY ENDPOINT - Remove in production!
    """
    try:
        # Check if admin user already exists
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            return {"message": "System already initialized", "admin_exists": True}
        
        # Create default permissions
        permissions_data = [
            {"name": "license.application.create", "display_name": "Create License Application", "description": "Create new license applications", "category": "license"},
            {"name": "license.application.read", "display_name": "View License Applications", "description": "View and search license applications", "category": "license"},
            {"name": "license.application.update", "display_name": "Update License Application", "description": "Update existing license applications", "category": "license"},
            {"name": "admin.user.create", "display_name": "Create Users", "description": "Create new system users", "category": "administration"},
            {"name": "admin.user.read", "display_name": "View Users", "description": "View system users", "category": "administration"},
            {"name": "admin.user.update", "display_name": "Update Users", "description": "Update system user accounts", "category": "administration"},
        ]
        
        permissions_created = {}
        for perm_data in permissions_data:
            permission = Permission(
                id=str(uuid.uuid4()),
                name=perm_data["name"],
                display_name=perm_data["display_name"],
                description=perm_data["description"],
                category=perm_data["category"],
                is_active=True,
                created_at=datetime.utcnow(),
                created_by="system"
            )
            db.add(permission)
            permissions_created[permission.name] = permission
        
        db.flush()
        
        # Create admin role
        admin_role = Role(
            id=str(uuid.uuid4()),
            name="super_admin",
            display_name="Super Administrator",
            description="Full system access with all permissions",
            level=1,
            is_system_role=True,
            is_active=True,
            created_at=datetime.utcnow(),
            created_by="system"
        )
        db.add(admin_role)
        db.flush()
        
        # Add permissions to admin role
        for perm in permissions_created.values():
            role_permission = RolePermission(
                role_id=admin_role.id,
                permission_id=perm.id,
                created_at=datetime.utcnow(),
                created_by="system"
            )
            db.add(role_permission)
        
        # Create admin user
        admin_user = User(
            id=str(uuid.uuid4()),
            username="admin",
            email="admin@linc.gov.za",
            first_name="System",
            last_name="Administrator",
            password_hash=get_password_hash("Admin123!"),
            employee_id="ADMIN001",
            department="IT Administration",
            country_code="ZA",
            is_active=True,
            is_verified=True,
            is_superuser=True,
            status=UserStatus.ACTIVE.value,
            require_password_change=True,
            created_at=datetime.utcnow(),
            created_by="system"
        )
        db.add(admin_user)
        db.flush()
        
        # Add admin role to user
        user_role = UserRole(
            user_id=admin_user.id,
            role_id=admin_role.id,
            created_at=datetime.utcnow(),
            created_by="system"
        )
        db.add(user_role)
        
        # Create test users
        test_users = [
            {"username": "operator1", "password": "Operator123!", "first_name": "Jane", "last_name": "Smith"},
            {"username": "examiner1", "password": "Examiner123!", "first_name": "Mike", "last_name": "Johnson"},
        ]
        
        for user_data in test_users:
            user = User(
                id=str(uuid.uuid4()),
                username=user_data["username"],
                email=f"{user_data['username']}@linc.gov.za",
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                password_hash=get_password_hash(user_data["password"]),
                employee_id=f"EMP{user_data['username'][-1]}",
                department="Operations",
                country_code="ZA",
                is_active=True,
                is_verified=True,
                status=UserStatus.ACTIVE.value,
                require_password_change=True,
                created_at=datetime.utcnow(),
                created_by="system"
            )
            db.add(user)
        
        db.commit()
        
        return {
            "message": "Authentication system initialized successfully!",
            "admin_user": "admin",
            "admin_password": "Admin123!",
            "note": "Please change the default password immediately",
            "test_users": ["operator1", "examiner1"],
            "warning": "Remove this endpoint in production!"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize system: {str(e)}"
        ) 