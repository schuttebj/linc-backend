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
import uuid
import logging

from app.core.config import get_settings
from app.core.database import get_db

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security schemes
security_bearer = HTTPBearer()
security_basic = HTTPBasic()
settings = get_settings()

logger = logging.getLogger(__name__)

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
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=30)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")  # Token contains user_id, not username
        if user_id is None:
            return None
        return payload
    except jwt.PyJWTError:
        return None

def decode_token(token: str) -> dict:
    """Decode a JWT token (with exceptions)"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security_bearer),
    db: Session = Depends(get_db)
):
    """Get current user from JWT token"""
    from app.models.user import User, UserStatus
    
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
    
    if user.status != UserStatus.ACTIVE.value:
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
    from app.models.user import User, UserStatus
    
    # Authenticate user with username/password
    user = db.query(User).filter(User.username == credentials.username).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    if user.status != UserStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_bearer),
    db: Session = Depends(get_db)
):
    """
    Get current user from JWT token - SECURE STANDARDIZED VERSION
    Uses the same logic as auth endpoints for consistency
    """
    from app.models.user import User, UserStatus
    
    try:
        # Decode token (same as auth endpoints)
        payload = decode_token(credentials.credentials)
        
        user_id = payload.get("sub")
        username = payload.get("username")
        
        if not user_id or not username:
            logger.error("get_current_user - invalid token payload")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        
        # Get user from database by ID (more secure than username)
        user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        
        if not user:
            logger.error("get_current_user - user not found in database")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if user.status != UserStatus.ACTIVE.value:
            logger.error(f"get_current_user - user account inactive: {user.status}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_current_user - authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )

async def get_current_active_user(current_user = Depends(get_current_user)):
    """Get current active user"""
    from app.models.user import UserStatus
    if current_user.status != UserStatus.ACTIVE.value:
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
    """LEGACY DECORATOR - REMOVED TO FORCE MIGRATION"""
    raise NotImplementedError(
        f"Legacy require_permission decorator removed. Use new permission system instead.\n"
        f"Replace with: from app.core.permission_middleware import require_permission\n"
        f"@require_permission('{permission}')\n"
        f"The new system uses dot notation: 'person.register', 'license.application.create', etc.\n"
        f"See cursor rules for permission mapping."
    )

def require_role(role: str):
    """LEGACY DECORATOR - REMOVED TO FORCE MIGRATION"""
    raise NotImplementedError(
        f"Legacy require_role decorator removed. Use new permission system instead.\n"
        f"Roles are now handled through region/office assignments.\n"
        f"Use permission decorators: from app.core.permission_middleware import require_permission\n"
        f"Check the permission mapping in the cursor rules for equivalent permissions."
    )

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