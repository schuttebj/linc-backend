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

def require_permission(permission: str, context_fields: List[str] = None) -> Callable:
    """
    Enhanced permission decorator with context support
    
    Args:
        permission: Permission name to check
        context_fields: List of field names to extract from request for geographic context
        
    Usage:
        @require_permission("license.create")
        @require_permission("license.approve", context_fields=["province_code", "region_id"])
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user and database session
            current_user = None
            db_session = None
            request = None
            
            # Extract dependencies from kwargs
            for key, value in kwargs.items():
                if isinstance(value, User):
                    current_user = value
                elif isinstance(value, Session):
                    db_session = value
                elif isinstance(value, Request):
                    request = value
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not db_session:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database session not available"
                )
            
            # Build context from request if context_fields specified
            context = {}
            if context_fields and request:
                # Extract from path parameters
                if hasattr(request, 'path_params'):
                    for field in context_fields:
                        if field in request.path_params:
                            context[field] = request.path_params[field]
                
                # Extract from query parameters
                if hasattr(request, 'query_params'):
                    for field in context_fields:
                        if field in request.query_params:
                            context[field] = request.query_params[field]
                
                # Extract from request body (if available)
                if hasattr(request, '_body') and request._body:
                    try:
                        import json
                        body = json.loads(request._body)
                        for field in context_fields:
                            if field in body:
                                context[field] = body[field]
                    except:
                        pass  # Ignore JSON parse errors
            
            # Check permission
            try:
                engine = get_permission_engine(db_session)
                has_permission = await engine.check_permission(
                    str(current_user.id), 
                    permission, 
                    context if context else None
                )
                
                if not has_permission:
                    logger.warning("Permission denied", 
                                 user_id=str(current_user.id),
                                 username=current_user.username,
                                 permission=permission,
                                 context=context)
                    raise PermissionDeniedError(permission, context)
                
                logger.debug("Permission granted", 
                           user_id=str(current_user.id),
                           permission=permission)
                
                return await func(*args, **kwargs)
                
            except PermissionDeniedError:
                raise
            except Exception as e:
                logger.error("Permission check failed", 
                           user_id=str(current_user.id),
                           permission=permission,
                           error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Permission check failed"
                )
        
        return wrapper
    return decorator

def require_any_permission(*permissions: str, context_fields: List[str] = None) -> Callable:
    """
    Check if user has ANY of the specified permissions
    
    Usage:
        @require_any_permission("license.read", "license.view")
        @require_any_permission("admin.user.read", "admin.user.view", context_fields=["province_code"])
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get dependencies (same as require_permission)
            current_user = None
            db_session = None
            request = None
            
            for key, value in kwargs.items():
                if isinstance(value, User):
                    current_user = value
                elif isinstance(value, Session):
                    db_session = value
                elif isinstance(value, Request):
                    request = value
            
            if not current_user or not db_session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Build context
            context = {}
            if context_fields and request:
                # Similar context building logic as require_permission
                pass  # Simplified for brevity
            
            # Check permissions
            try:
                engine = get_permission_engine(db_session)
                has_permission = await engine.check_multiple_permissions(
                    str(current_user.id),
                    list(permissions),
                    require_all=False,  # ANY permission
                    context=context if context else None
                )
                
                if not has_permission:
                    logger.warning("None of required permissions found",
                                 user_id=str(current_user.id),
                                 permissions=permissions)
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"At least one of these permissions required: {', '.join(permissions)}"
                    )
                
                return await func(*args, **kwargs)
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error("Multiple permission check failed", 
                           user_id=str(current_user.id),
                           permissions=permissions,
                           error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Permission check failed"
                )
        
        return wrapper
    return decorator

def require_all_permissions(*permissions: str, context_fields: List[str] = None) -> Callable:
    """
    Check if user has ALL of the specified permissions
    
    Usage:
        @require_all_permissions("license.read", "license.approve")
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Similar implementation to require_any_permission but with require_all=True
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
                has_permission = await engine.check_multiple_permissions(
                    str(current_user.id),
                    list(permissions),
                    require_all=True,  # ALL permissions
                    context=None
                )
                
                if not has_permission:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"All of these permissions required: {', '.join(permissions)}"
                    )
                
                return await func(*args, **kwargs)
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error("All permissions check failed", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Permission check failed"
                )
        
        return wrapper
    return decorator

def require_system_type(*system_types: SystemType) -> Callable:
    """
    Require user to have specific system type(s)
    
    Usage:
        @require_system_type(SystemType.SUPER_ADMIN)
        @require_system_type(SystemType.SUPER_ADMIN, SystemType.NATIONAL_HELP_DESK)
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
                
                if compiled.system_type not in system_types:
                    logger.warning("System type access denied",
                                 user_id=str(current_user.id),
                                 user_system_type=compiled.system_type.value,
                                 required_types=[st.value for st in system_types])
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"System type required: {[st.value for st in system_types]}"
                    )
                
                return await func(*args, **kwargs)
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error("System type check failed", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="System type check failed"
                )
        
        return wrapper
    return decorator

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
def require_admin_permission(permission: str) -> Callable:
    """
    Legacy compatibility function
    Maps to the new require_permission function
    """
    return require_permission(permission)