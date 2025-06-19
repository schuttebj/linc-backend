"""
Permission Middleware for LINC Dynamic Permission System
Integrates with the new permission engine for real-time authorization
"""

from typing import Callable, Dict, List, Optional, Any
from functools import wraps
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import structlog

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.permission_engine import get_permission_engine, SystemType
from app.models.user import User

logger = structlog.get_logger()

class PermissionDeniedError(HTTPException):
    """Custom exception for permission denied"""
    def __init__(self, permission: str, context: Dict[str, Any] = None):
        detail = f"Permission denied: {permission}"
        if context:
            detail += f" (context: {context})"
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )



def require_any_permission(*permissions: str, context_fields: List[str] = None):
    """
    Create a dependency for checking if user has ANY of the specified permissions
    
    Usage:
        async def my_endpoint(
            current_user: User = Depends(require_any_permission("license.read", "license.view"))
        ):
    """
    return AnyPermissionRequired(permissions, context_fields)

class AnyPermissionRequired:
    """
    FastAPI dependency for checking ANY of multiple permissions
    """
    def __init__(self, permissions: tuple, context_fields: List[str] = None):
        self.permissions = permissions
        self.context_fields = context_fields
    
    async def __call__(
        self,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        
        try:
            engine = get_permission_engine(db)
            has_permission = await engine.check_multiple_permissions(
                str(current_user.id),
                list(self.permissions),
                require_all=False,  # ANY permission
                context=None
            )
            
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"At least one of these permissions required: {', '.join(self.permissions)}"
                )
            
            return current_user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Multiple permission check failed", 
                       permissions=self.permissions, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Permission check failed"
            )

def require_all_permissions(*permissions: str, context_fields: List[str] = None):
    """
    Create a dependency for checking if user has ALL of the specified permissions
    
    Usage:
        async def my_endpoint(
            current_user: User = Depends(require_all_permissions("license.read", "license.approve"))
        ):
    """
    return AllPermissionsRequired(permissions, context_fields)

class AllPermissionsRequired:
    """
    FastAPI dependency for checking ALL of multiple permissions
    """
    def __init__(self, permissions: tuple, context_fields: List[str] = None):
        self.permissions = permissions
        self.context_fields = context_fields
    
    async def __call__(
        self,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        
        try:
            engine = get_permission_engine(db)
            has_permission = await engine.check_multiple_permissions(
                str(current_user.id),
                list(self.permissions),
                require_all=True,  # ALL permissions
                context=None
            )
            
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"All of these permissions required: {', '.join(self.permissions)}"
                )
            
            return current_user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("All permissions check failed", 
                       permissions=self.permissions, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Permission check failed"
            )

def require_system_type(*system_types: SystemType):
    """
    Create a dependency for checking user system type
    
    Usage:
        async def my_endpoint(
            current_user: User = Depends(require_system_type(SystemType.SUPER_ADMIN))
        ):
    """
    return SystemTypeRequired(*system_types)

def require_geographic_access(province_code: str = None, region_id: str = None, 
                            office_id: str = None) -> Callable:
    """
    Require user to have access to specific geographic areas
    
    Usage:
        @require_geographic_access(province_code="GP")
        @require_geographic_access(region_id="GP001")
        @require_geographic_access(office_id="GP001001")
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = None
            db_session = None
            
            for key, value in kwargs.items():
                if isinstance(value, User):
                    current_user = value
                elif isinstance(value, Session):
                    db_session = value
            
            if not current_user or not db_session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            try:
                engine = get_permission_engine(db_session)
                compiled = await engine.compile_user_permissions(str(current_user.id))
                
                # National Help Desk has access everywhere
                if compiled.system_type == SystemType.NATIONAL_HELP_DESK:
                    return await func(*args, **kwargs)
                
                # Check geographic access
                access_denied = False
                
                if province_code and province_code not in compiled.geographic_access.get("provinces", []):
                    access_denied = True
                
                if region_id and region_id not in compiled.geographic_access.get("regions", []):
                    access_denied = True
                
                if office_id and office_id not in compiled.geographic_access.get("offices", []):
                    access_denied = True
                
                if access_denied:
                    logger.warning("Geographic access denied",
                                 user_id=str(current_user.id),
                                 province_code=province_code,
                                 region_id=region_id,
                                 office_id=office_id)
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Geographic access denied"
                    )
                
                return await func(*args, **kwargs)
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error("Geographic access check failed", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Geographic access check failed"
                )
        
        return wrapper
    return decorator

# FastAPI Dependencies for easier use
def require_permission(permission: str, context_fields: List[str] = None):
    """
    Create a PermissionRequired dependency for use with Depends()
    
    Usage:
        async def my_endpoint(
            current_user: User = Depends(require_permission("license.create"))
        ):
    """
    return PermissionRequired(permission, context_fields)

class PermissionRequired:
    """
    FastAPI dependency for permission checking
    
    Usage:
        async def my_endpoint(
            current_user: User = Depends(PermissionRequired("license.create"))
        ):
    """
    def __init__(self, permission: str, context_fields: List[str] = None):
        self.permission = permission
        self.context_fields = context_fields
    
    async def __call__(
        self,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        
        try:
            engine = get_permission_engine(db)
            has_permission = await engine.check_permission(
                str(current_user.id), 
                self.permission
            )
            
            if not has_permission:
                raise PermissionDeniedError(self.permission)
            
            return current_user
            
        except PermissionDeniedError:
            raise
        except Exception as e:
            logger.error("Permission dependency check failed", 
                       permission=self.permission, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Permission check failed"
            )

class SystemTypeRequired:
    """
    FastAPI dependency for system type checking
    
    Usage:
        async def admin_endpoint(
            current_user: User = Depends(SystemTypeRequired(SystemType.SUPER_ADMIN))
        ):
    """
    def __init__(self, *system_types: SystemType):
        self.system_types = system_types
    
    async def __call__(
        self,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        
        try:
            engine = get_permission_engine(db)
            compiled = await engine.compile_user_permissions(str(current_user.id))
            
            if compiled.system_type not in self.system_types:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"System type required: {[st.value for st in self.system_types]}"
                )
            
            return current_user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("System type dependency check failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="System type check failed"
            )

# Backward compatibility with existing code
def require_admin_permission(permission: str):
    """
    Legacy compatibility function
    Maps to the new require_permission function
    """
    return require_permission(permission)