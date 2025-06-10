"""
Security utilities for authentication and authorization
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Union
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPBasic, HTTPBasicCredentials, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import secrets

from app.core.config import get_settings
from app.core.database import get_db

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security schemes
security_bearer = HTTPBearer()
security_basic = HTTPBasic()
settings = get_settings()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return payload
    except jwt.PyJWTError:
        return None

async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security_bearer),
    db: Session = Depends(get_db)
):
    """Get current user from JWT token"""
    from app.models.user import User
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verify_token(credentials.credentials)
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user

async def get_current_user_from_basic_auth(
    credentials: HTTPBasicCredentials = Depends(security_basic),
    db: Session = Depends(get_db)
):
    """Get current user from HTTP Basic Auth"""
    from app.models.user import User
    
    # Authenticate user with username/password
    user = db.query(User).filter(User.username == credentials.username).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user

async def get_current_user(
    db: Session = Depends(get_db)
):
    """
    Get current user supporting both JWT Bearer tokens and HTTP Basic Auth
    This function will be used with custom dependency logic
    """
    from fastapi import Request
    from app.models.user import User
    
    # This is a placeholder - the actual authentication logic 
    # will be handled by the dependency injection system
    pass

# Custom dependency for dual authentication
class DualAuth:
    """
    Custom authentication class supporting both JWT and Basic Auth
    
    ⚠️  SECURITY WARNING ⚠️
    HTTP Basic Auth is included for TESTING CONVENIENCE only!
    
    TODO: REMOVE HTTP Basic Auth before PRODUCTION deployment:
    1. Remove basic_auth parameter from __call__ method
    2. Remove HTTPBasic import and security_basic instance
    3. Remove the "Try HTTP Basic Auth" section below
    4. Update OpenAPI config to only show Bearer token
    
    Basic Auth sends credentials with every request and is less secure than JWT tokens.
    """
    
    def __init__(self):
        self.security_bearer = HTTPBearer(auto_error=False)
        self.security_basic = HTTPBasic(auto_error=False)  # TODO: Remove before production!
    
    async def __call__(
        self,
        db: Session = Depends(get_db),
        bearer_token: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
        basic_auth: Optional[HTTPBasicCredentials] = Depends(HTTPBasic(auto_error=False))  # TODO: Remove before production!
    ):
        """
        Try both authentication methods
        
        ⚠️  PRODUCTION TODO: Remove basic_auth parameter and related logic below
        """
        from app.models.user import User
        
        # Try JWT Bearer token first
        if bearer_token:
            try:
                payload = verify_token(bearer_token.credentials)
                if payload:
                    username = payload.get("sub")
                    if username:
                        user = db.query(User).filter(User.username == username).first()
                        if user and user.is_active:
                            return user
            except:
                pass
        
        # Try HTTP Basic Auth
        # TODO: REMOVE THIS ENTIRE SECTION BEFORE PRODUCTION! ⚠️
        if basic_auth:
            try:
                user = db.query(User).filter(User.username == basic_auth.username).first()
                if user and verify_password(basic_auth.password, user.password_hash) and user.is_active:
                    return user
            except:
                pass
        # END OF SECTION TO REMOVE ⚠️
        
        # If neither method worked, raise authentication error
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Create the dependency instance
get_current_user = DualAuth()

async def get_current_active_user(current_user = Depends(get_current_user)):
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_active_superuser(current_user = Depends(get_current_user)):
    """Get current active superuser"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

def require_permission(permission: str):
    """
    Decorator to require specific permission
    """
    def permission_checker(current_user = Depends(get_current_user)) -> dict:
        user_permissions = current_user.get("permissions", [])
        if permission not in user_permissions and "admin" not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission}"
            )
        return current_user
    return permission_checker

def require_role(role: str):
    """
    Decorator to require specific role
    """
    def role_checker(current_user = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role", "")
        if user_role != role and user_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {role}"
            )
        return current_user
    return role_checker

# For development/testing - create a test token
def create_test_token() -> str:
    """Create a test token for development purposes"""
    test_data = {
        "sub": "test-user-123",
        "username": "testuser",
        "role": "admin",
        "permissions": ["read", "write", "admin"]
    }
    return create_access_token(test_data)

# Optional: Create a simple user for testing
TEST_USER = {
    "username": "testuser",
    "password_hash": get_password_hash("testpass123"),
    "role": "admin",
    "permissions": ["read", "write", "admin"]
} 