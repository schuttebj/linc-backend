"""
Security module for authentication and authorization
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
import structlog

logger = structlog.get_logger()

# Security configuration
SECRET_KEY = "your-secret-key-here"  # Should be loaded from environment
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Security instances
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_security = HTTPBearer()

class SecurityManager:
    """Security manager for authentication and authorization"""
    
    def __init__(self):
        self.pwd_context = pwd_context
        self.secret_key = SECRET_KEY
        self.algorithm = ALGORITHM
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Get password hash"""
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

# Security manager instance
security_manager = SecurityManager()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_security)) -> Dict[str, Any]:
    """
    Get current authenticated user from JWT token
    For now, this is a simplified implementation
    """
    try:
        # Verify the token
        payload = security_manager.verify_token(credentials.credentials)
        
        # Extract user information from token
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # For now, return a basic user object
        # In a real implementation, you would fetch user details from database
        user = {
            "id": user_id,
            "username": payload.get("username", "unknown"),
            "role": payload.get("role", "user"),
            "permissions": payload.get("permissions", [])
        }
        
        return user
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get current active user (can be extended to check if user is active/disabled)
    """
    # In a real implementation, check if user is active in database
    return current_user

def require_permission(permission: str):
    """
    Decorator to require specific permission
    """
    def permission_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
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
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
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
    return security_manager.create_access_token(test_data)

# Optional: Create a simple user for testing
TEST_USER = {
    "username": "testuser",
    "password_hash": security_manager.get_password_hash("testpass123"),
    "role": "admin",
    "permissions": ["read", "write", "admin"]
} 