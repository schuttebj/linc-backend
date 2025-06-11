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
    logger.info(f"🔍 decode_token called with token: {token[:20]}...{token[-20:] if len(token) > 40 else token}")
    logger.info(f"🔍 Token length: {len(token)}")
    logger.info(f"🔍 SECRET_KEY present: {bool(settings.SECRET_KEY)}")
    logger.info(f"🔍 Algorithm: {settings.ALGORITHM}")
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        logger.info(f"🔍 Token decoded successfully: {payload}")
        return payload
    except jwt.ExpiredSignatureError as e:
        logger.error(f"🔍 Token expired: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError as e:
        logger.error(f"🔍 Invalid token error: {str(e)}")
        logger.error(f"🔍 JWT error type: {type(e)}")
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
    
    logger.info("🚨 get_current_user starting...")
    logger.info(f"🚨 Credentials object: {credentials}")
    logger.info(f"🚨 Credentials type: {type(credentials)}")
    
    if credentials:
        logger.info(f"🚨 Credentials.scheme: {credentials.scheme}")
        logger.info(f"🚨 Credentials.credentials: {credentials.credentials}")
        logger.info(f"🔑 Raw token received: {credentials.credentials[:20]}...{credentials.credentials[-20:] if len(credentials.credentials) > 40 else credentials.credentials}")
        logger.info(f"🔑 Token length: {len(credentials.credentials)}")
    else:
        logger.error("🚨 No credentials received!")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authorization credentials provided"
        )

    try:
        # Decode token (same as auth endpoints)
        logger.info("🔑 About to decode token...")
        payload = decode_token(credentials.credentials)
        logger.info(f"🔑 Token decoded successfully: {payload}")
        
        user_id = payload.get("sub")
        username = payload.get("username")
        
        if not user_id or not username:
            logger.error("get_current_user - invalid token payload")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        
        logger.info(f"get_current_user - token verified for user: {username}, id: {user_id}")
        
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
        
        logger.info("get_current_user - authentication successful")
        return user
        
    except HTTPException as http_exc:
        logger.error(f"get_current_user - HTTPException: status={http_exc.status_code}, detail={http_exc.detail}")
        raise
    except Exception as e:
        logger.error(f"get_current_user - authentication error: {str(e)}")
        logger.error(f"get_current_user - authentication error type: {type(e)}")
        http_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
        logger.error(f"get_current_user - raising HTTPException: {http_exception.detail}")
        raise http_exception

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