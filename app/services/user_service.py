"""
User Management Service
Handles user authentication, authorization, and management operations
"""

from typing import Optional, List, Dict, Tuple, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_, or_, desc, func
from fastapi import HTTPException, status
from passlib.context import CryptContext
import secrets
import structlog
from jose import JWTError, jwt
import uuid

from app.models.user import User, Role, Permission, UserAuditLog, UserStatus
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, 
    RoleCreate, RoleUpdate, PermissionCreate,
    UserLogin, UserListFilter
)
from app.core.security import create_access_token, verify_password, get_password_hash
from app.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

class UserService:
    """Service for user management operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # Authentication Methods
    async def authenticate_user(self, username: str, password: str, ip_address: str = None) -> Optional[User]:
        """
        Authenticate user login
        Implements security rules from documentation
        """
        try:
            # Get user by username or email
            user = self.db.query(User).filter(
                or_(User.username == username, User.email == username)
            ).first()
            
            if not user:
                await self._log_audit(
                    None, "login_failed", "authentication", 
                    ip_address=ip_address, success=False,
                    error_message=f"User not found: {username}"
                )
                return None
            
            # Check if account is locked
            if user.is_locked:
                await self._log_audit(
                    user.id, "login_failed", "authentication",
                    ip_address=ip_address, success=False,
                    error_message="Account is locked"
                )
                return None
            
            # Check if account is active
            if not user.is_active or user.status != UserStatus.ACTIVE.value:
                await self._log_audit(
                    user.id, "login_failed", "authentication",
                    ip_address=ip_address, success=False,
                    error_message=f"Account is not active: {user.status}"
                )
                return None
            
            # Verify password
            if not self.pwd_context.verify(password, user.password_hash):
                # Increment failed login attempts
                user.failed_login_attempts += 1
                
                # Lock account after 5 failed attempts
                if user.failed_login_attempts >= 5:
                    user.locked_until = datetime.utcnow() + timedelta(minutes=30)
                    user.status = UserStatus.LOCKED.value
                
                self.db.commit()
                
                await self._log_audit(
                    user.id, "login_failed", "authentication",
                    ip_address=ip_address, success=False,
                    error_message="Invalid password"
                )
                return None
            
            # Reset failed login attempts on successful authentication
            user.failed_login_attempts = 0
            user.last_login_at = datetime.utcnow()
            user.last_login_ip = ip_address
            if user.locked_until:
                user.locked_until = None
                user.status = UserStatus.ACTIVE.value
            
            self.db.commit()
            
            await self._log_audit(
                user.id, "login_success", "authentication",
                ip_address=ip_address, success=True
            )
            
            return user
            
        except Exception as e:
            logger.error("Error authenticating user", username=username, error=str(e))
            await self._log_audit(
                None, "login_error", "authentication",
                ip_address=ip_address, success=False,
                error_message=str(e)
            )
            return None
    
    async def create_tokens(self, user: User) -> Dict[str, Any]:
        """Create access and refresh tokens for user"""
        try:
            token_data = {
                "sub": user.username,  # Use username as subject
                "user_id": str(user.id),
                "roles": [role.name for role in user.roles],
                "permissions": self._get_user_permissions(user)
            }
            
            # Create access token with 15 minute expiry
            access_token = create_access_token(token_data, expires_delta=timedelta(minutes=15))
            
            # Create refresh token with 7 day expiry
            refresh_token_data = {"sub": user.username, "user_id": str(user.id)}
            refresh_token = create_access_token(refresh_token_data, expires_delta=timedelta(days=7))
            
            # Update user token info
            user.last_login_at = datetime.utcnow()
            user.refresh_token_hash = self.pwd_context.hash(refresh_token)
            
            self.db.commit()
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": 900  # 15 minutes in seconds
            }
            
        except Exception as e:
            logger.error("Error creating tokens", user_id=user.id, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating authentication tokens"
            )
    
    def _get_user_permissions(self, user: User) -> List[str]:
        """Get list of user permissions from roles"""
        permissions = set()
        
        if user.is_superuser:
            # Superuser has all permissions
            all_permissions = self.db.query(Permission).filter(Permission.is_active == True).all()
            return [p.name for p in all_permissions]
        
        for role in user.roles:
            if role.is_active:
                for permission in role.permissions:
                    if permission.is_active:
                        permissions.add(permission.name)
        
        return list(permissions)
    
    # User Management Methods
    async def create_user(self, user_data: UserCreate, created_by: str = None) -> User:
        """
        Create new user account
        Implements user creation business rules
        """
        try:
            logger.info("Creating new user", username=user_data.username, email=user_data.email)
            
            # Check if username already exists
            existing_user = self.db.query(User).filter(
                or_(User.username == user_data.username, User.email == user_data.email)
            ).first()
            
            if existing_user:
                if existing_user.username == user_data.username:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Username already exists"
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already exists"
                    )
            
            # Create user
            user = User(
                username=user_data.username,
                email=user_data.email,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                display_name=user_data.display_name,
                phone_number=user_data.phone_number,
                employee_id=user_data.employee_id,
                department=user_data.department,
                country_code=user_data.country_code,
                province=user_data.province,
                region=user_data.region,
                office_location=user_data.office_location,
                language=user_data.language,
                timezone=user_data.timezone,
                password_hash=self.pwd_context.hash(user_data.password),
                is_active=user_data.is_active,
                require_password_change=user_data.require_password_change,
                status=UserStatus.ACTIVE.value if user_data.is_active else UserStatus.INACTIVE.value,
                created_by=created_by
            )
            
            self.db.add(user)
            self.db.flush()  # Get user ID
            
            # Assign roles
            if user_data.role_ids:
                roles = self.db.query(Role).filter(
                    Role.id.in_(user_data.role_ids),
                    Role.is_active == True
                ).all()
                user.roles = roles
            
            self.db.commit()
            self.db.refresh(user)
            
            await self._log_audit(
                user.id, "user_created", "user_management",
                success=True, details=f"User created: {user.username}"
            )
            
            logger.info("User created successfully", user_id=user.id, username=user.username)
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error("Error creating user", username=user_data.username, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating user account"
            )
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID with roles and permissions"""
        try:
            user = self.db.query(User).options(
                selectinload(User.roles).selectinload(Role.permissions)
            ).filter(User.id == user_id).first()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error getting user by ID", user_id=user_id, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving user"
            )
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        try:
            user = self.db.query(User).options(
                selectinload(User.roles).selectinload(Role.permissions)
            ).filter(User.username == username).first()
            
            return user
            
        except Exception as e:
            logger.error("Error getting user by username", username=username, error=str(e))
            return None
    
    async def update_user(self, user_id: str, user_data: UserUpdate, updated_by: str = None) -> User:
        """Update user account"""
        try:
            user = await self.get_user_by_id(user_id)
            
            # Update fields
            update_data = user_data.dict(exclude_unset=True)
            
            # Handle email uniqueness check
            if 'email' in update_data:
                existing_user = self.db.query(User).filter(
                    User.email == update_data['email'],
                    User.id != user_id
                ).first()
                if existing_user:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email already exists"
                    )
            
            # Update roles if provided
            if 'role_ids' in update_data:
                role_ids = update_data.pop('role_ids')
                if role_ids is not None:
                    roles = self.db.query(Role).filter(
                        Role.id.in_(role_ids),
                        Role.is_active == True
                    ).all()
                    user.roles = roles
            
            # Update other fields
            for field, value in update_data.items():
                setattr(user, field, value)
            
            user.updated_by = updated_by
            user.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(user)
            
            await self._log_audit(
                user.id, "user_updated", "user_management",
                success=True, details=f"User updated: {user.username}"
            )
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error("Error updating user", user_id=user_id, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating user account"
            )
    
    async def list_users(
        self, 
        filters: UserListFilter = None,
        page: int = 1,
        size: int = 20
    ) -> Tuple[List[User], int]:
        """List users with filtering and pagination"""
        try:
            query = self.db.query(User).options(
                selectinload(User.roles)
            )
            
            # Apply filters
            if filters:
                if filters.status:
                    query = query.filter(User.status == filters.status.value)
                if filters.is_active is not None:
                    query = query.filter(User.is_active == filters.is_active)
                if filters.department:
                    query = query.filter(User.department.ilike(f"%{filters.department}%"))
                if filters.country_code:
                    query = query.filter(User.country_code == filters.country_code)
                if filters.search:
                    search_term = f"%{filters.search}%"
                    query = query.filter(
                        or_(
                            User.username.ilike(search_term),
                            User.email.ilike(search_term),
                            User.first_name.ilike(search_term),
                            User.last_name.ilike(search_term),
                            User.employee_id.ilike(search_term)
                        )
                    )
                if filters.role:
                    query = query.join(User.roles).filter(Role.name == filters.role)
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            offset = (page - 1) * size
            users = query.order_by(User.created_at.desc()).offset(offset).limit(size).all()
            
            return users, total
            
        except Exception as e:
            logger.error("Error listing users", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving users"
            )
    
    # Role Management Methods
    async def create_role(self, role_data: RoleCreate, created_by: str = None) -> Role:
        """Create new role"""
        try:
            # Check if role name already exists
            existing_role = self.db.query(Role).filter(Role.name == role_data.name).first()
            if existing_role:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Role name already exists"
                )
            
            role = Role(
                name=role_data.name,
                display_name=role_data.display_name,
                description=role_data.description,
                is_active=role_data.is_active,
                parent_role_id=role_data.parent_role_id,
                created_by=created_by
            )
            
            self.db.add(role)
            self.db.flush()
            
            # Assign permissions
            if role_data.permission_ids:
                permissions = self.db.query(Permission).filter(
                    Permission.id.in_(role_data.permission_ids),
                    Permission.is_active == True
                ).all()
                role.permissions = permissions
            
            self.db.commit()
            self.db.refresh(role)
            
            await self._log_audit(
                None, "role_created", "role_management",
                success=True, details=f"Role created: {role.name}"
            )
            
            return role
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error("Error creating role", role_name=role_data.name, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating role"
            )
    
    async def get_roles(self) -> List[Role]:
        """Get all active roles"""
        try:
            roles = self.db.query(Role).options(
                selectinload(Role.permissions)
            ).filter(Role.is_active == True).order_by(Role.name).all()
            
            return roles
            
        except Exception as e:
            logger.error("Error getting roles", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving roles"
            )
    
    # Permission Management Methods
    async def create_permission(self, permission_data: PermissionCreate, created_by: str = None) -> Permission:
        """Create new permission"""
        try:
            # Check if permission name already exists
            existing_permission = self.db.query(Permission).filter(
                Permission.name == permission_data.name
            ).first()
            if existing_permission:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Permission name already exists"
                )
            
            permission = Permission(
                name=permission_data.name,
                display_name=permission_data.display_name,
                description=permission_data.description,
                category=permission_data.category,
                resource=permission_data.resource,
                action=permission_data.action,
                is_active=permission_data.is_active,
                created_by=created_by
            )
            
            self.db.add(permission)
            self.db.commit()
            self.db.refresh(permission)
            
            await self._log_audit(
                None, "permission_created", "permission_management",
                success=True, details=f"Permission created: {permission.name}"
            )
            
            return permission
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error("Error creating permission", permission_name=permission_data.name, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating permission"
            )
    
    async def get_permissions(self) -> List[Permission]:
        """Get all active permissions"""
        try:
            permissions = self.db.query(Permission).filter(
                Permission.is_active == True
            ).order_by(Permission.category, Permission.name).all()
            
            return permissions
            
        except Exception as e:
            logger.error("Error getting permissions", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving permissions"
            )
    
    # Password Management Methods
    async def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """Change user password"""
        try:
            user = await self.get_user_by_id(user_id)
            
            # Verify current password
            if not self.pwd_context.verify(current_password, user.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect"
                )
            
            # Update password
            user.password_hash = self.pwd_context.hash(new_password)
            user.require_password_change = False
            user.password_expires_at = datetime.utcnow() + timedelta(days=90)  # 90 day expiry
            user.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            await self._log_audit(
                user.id, "password_changed", "security",
                success=True
            )
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error("Error changing password", user_id=user_id, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error changing password"
            )
    
    # Authorization Methods
    def check_permission(self, user: User, permission_name: str) -> bool:
        """Check if user has specific permission"""
        return user.has_permission(permission_name)
    
    def check_role(self, user: User, role_name: str) -> bool:
        """Check if user has specific role"""
        return user.has_role(role_name)
    
    # Audit Methods
    async def _log_audit(
        self,
        user_id: Optional[str],
        action: str,
        resource: str,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        details: Optional[str] = None
    ):
        """Log user audit event"""
        try:
            audit_log = UserAuditLog(
                user_id=user_id,
                action=action,
                resource=resource,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent,
                endpoint=endpoint,
                method=method,
                success=success,
                error_message=error_message,
                details=details
            )
            
            self.db.add(audit_log)
            self.db.commit()
            
        except Exception as e:
            logger.error("Error logging audit event", action=action, error=str(e))
            # Don't raise exception for audit logging failures 