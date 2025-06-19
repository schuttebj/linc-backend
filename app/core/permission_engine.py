"""
Dynamic Permission Engine for LINC System
Handles multi-tier permission compilation and real-time updates
"""

import json
import uuid
from typing import Dict, List, Optional, Set, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_
import structlog
import asyncio
from contextlib import asynccontextmanager

logger = structlog.get_logger()

class SystemType(Enum):
    """System-level user types"""
    SUPER_ADMIN = "super_admin"
    NATIONAL_HELP_DESK = "national_help_desk" 
    PROVINCIAL_HELP_DESK = "provincial_help_desk"
    STANDARD_USER = "standard_user"

class PermissionLevel(Enum):
    """Permission hierarchy levels"""
    SYSTEM = "system"
    REGION = "region"
    OFFICE = "office"
    INDIVIDUAL = "individual"

@dataclass
class CompiledPermissions:
    """Compiled user permissions from all sources"""
    user_id: str
    system_type: SystemType
    system_permissions: Set[str]
    region_permissions: Dict[str, Set[str]]  # region_id -> permissions
    office_permissions: Dict[str, Set[str]]  # office_id -> permissions
    individual_overrides: Set[str]
    final_permissions: Set[str]
    geographic_access: Dict[str, Any]  # provinces, regions, offices accessible
    compiled_at: datetime
    expires_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for caching"""
        return {
            "user_id": self.user_id,
            "system_type": self.system_type.value,
            "system_permissions": list(self.system_permissions),
            "region_permissions": {k: list(v) for k, v in self.region_permissions.items()},
            "office_permissions": {k: list(v) for k, v in self.office_permissions.items()},
            "individual_overrides": list(self.individual_overrides),
            "final_permissions": list(self.final_permissions),
            "geographic_access": self.geographic_access,
            "compiled_at": self.compiled_at.isoformat(),
            "expires_at": self.expires_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CompiledPermissions':
        """Create from cached dictionary"""
        return cls(
            user_id=data["user_id"],
            system_type=SystemType(data["system_type"]),
            system_permissions=set(data["system_permissions"]),
            region_permissions={k: set(v) for k, v in data["region_permissions"].items()},
            office_permissions={k: set(v) for k, v in data["office_permissions"].items()},
            individual_overrides=set(data["individual_overrides"]),
            final_permissions=set(data["final_permissions"]),
            geographic_access=data["geographic_access"],
            compiled_at=datetime.fromisoformat(data["compiled_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"])
        )

class PermissionEngine:
    """
    Core permission engine for dynamic permission management
    """
    
    def __init__(self, db: Session, cache_client=None):
        self.db = db
        self.cache_client = cache_client
        self.cache_ttl = 3600  # 1 hour default
        self.permission_cache_prefix = "linc:permissions:"
        self.role_cache_prefix = "linc:roles:"
        
    async def compile_user_permissions(self, user_id: str, force_refresh: bool = False) -> CompiledPermissions:
        """
        Compile all permissions for a user from all sources
        
        Permission Compilation Logic:
        Final Permissions = System Permissions + Region Permissions + Office Permissions + Individual Overrides
        """
        cache_key = f"{self.permission_cache_prefix}{user_id}"
        
        # Try cache first (unless force refresh)
        if not force_refresh and self.cache_client:
            try:
                cached_data = await self._get_from_cache(cache_key)
                if cached_data:
                    compiled = CompiledPermissions.from_dict(cached_data)
                    if compiled.expires_at > datetime.utcnow():
                        logger.debug("Permissions loaded from cache", user_id=user_id)
                        return compiled
            except Exception as e:
                logger.warning("Cache read failed, falling back to database", error=str(e))
        
        # Compile from database
        logger.info("Compiling user permissions from database", user_id=user_id)
        
        try:
            # Get user with all assignments
            user_data = await self._get_user_assignments(user_id)
            if not user_data:
                raise ValueError(f"User {user_id} not found")
            
            # Initialize compiled permissions
            compiled = CompiledPermissions(
                user_id=user_id,
                system_type=SystemType(user_data["system_type"]),
                system_permissions=set(),
                region_permissions={},
                office_permissions={},
                individual_overrides=set(),
                final_permissions=set(),
                geographic_access={},
                compiled_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(seconds=self.cache_ttl)
            )
            
            # 1. System-level permissions
            compiled.system_permissions = await self._get_system_permissions(compiled.system_type)
            
            # 2. Region-level permissions
            for region_assignment in user_data.get("region_assignments", []):
                region_id = region_assignment["region_id"]
                region_role = region_assignment["region_role"]
                permissions = await self._get_region_role_permissions(region_role)
                compiled.region_permissions[region_id] = permissions
            
            # 3. Office-level permissions  
            for office_assignment in user_data.get("office_assignments", []):
                office_id = office_assignment["office_id"]
                office_role = office_assignment["office_role"]
                permissions = await self._get_office_role_permissions(office_role)
                compiled.office_permissions[office_id] = permissions
            
            # 4. Individual permission overrides
            compiled.individual_overrides = set(user_data.get("individual_permissions", []))
            
            # 5. Compile final permission set
            compiled.final_permissions = self._merge_permissions(compiled)
            
            # 6. Compile geographic access
            compiled.geographic_access = await self._compile_geographic_access(user_data)
            
            # Cache the compiled permissions
            if self.cache_client:
                try:
                    await self._store_in_cache(cache_key, compiled.to_dict(), self.cache_ttl)
                    logger.debug("Permissions cached", user_id=user_id)
                except Exception as e:
                    logger.warning("Cache store failed", error=str(e))
            
            logger.info("User permissions compiled successfully", 
                       user_id=user_id, 
                       permission_count=len(compiled.final_permissions))
            
            return compiled
            
        except Exception as e:
            logger.error("Failed to compile user permissions", user_id=user_id, error=str(e))
            raise
    
    def _merge_permissions(self, compiled: CompiledPermissions) -> Set[str]:
        """Merge permissions from all sources with proper precedence"""
        final_permissions = set()
        
        # Start with system permissions
        final_permissions.update(compiled.system_permissions)
        
        # Add all region permissions
        for region_perms in compiled.region_permissions.values():
            final_permissions.update(region_perms)
        
        # Add all office permissions
        for office_perms in compiled.office_permissions.values():
            final_permissions.update(office_perms)
        
        # Apply individual overrides (can add or remove permissions)
        final_permissions.update(compiled.individual_overrides)
        
        return final_permissions
    
    async def check_permission(self, user_id: str, permission: str, context: Dict[str, Any] = None) -> bool:
        """
        Check if user has specific permission with optional context
        
        Context can include:
        - province_code: For geographic restrictions
        - region_id: For region-specific operations
        - office_id: For office-specific operations
        """
        try:
            compiled = await self.compile_user_permissions(user_id)
            
            # Super admin always has access
            if compiled.system_type == SystemType.SUPER_ADMIN:
                return True
            
            # Check if user has the permission
            if permission not in compiled.final_permissions:
                return False
            
            # Apply geographic restrictions if context provided
            if context:
                if not await self._check_geographic_access(compiled, context):
                    return False
            
            return True
            
        except Exception as e:
            logger.error("Permission check failed", user_id=user_id, permission=permission, error=str(e))
            return False
    
    async def check_multiple_permissions(self, user_id: str, permissions: List[str], 
                                       require_all: bool = True, context: Dict[str, Any] = None) -> bool:
        """Check multiple permissions with AND/OR logic"""
        try:
            compiled = await self.compile_user_permissions(user_id)
            
            # Super admin always has access
            if compiled.system_type == SystemType.SUPER_ADMIN:
                return True
            
            # Check permissions
            results = []
            for permission in permissions:
                has_perm = permission in compiled.final_permissions
                if has_perm and context:
                    has_perm = await self._check_geographic_access(compiled, context)
                results.append(has_perm)
            
            return all(results) if require_all else any(results)
            
        except Exception as e:
            logger.error("Multiple permission check failed", 
                        user_id=user_id, permissions=permissions, error=str(e))
            return False
    
    async def invalidate_user_permissions(self, user_id: str) -> bool:
        """Invalidate cached permissions for a specific user"""
        if not self.cache_client:
            return True
        
        try:
            cache_key = f"{self.permission_cache_prefix}{user_id}"
            await self._delete_from_cache(cache_key)
            logger.info("User permissions cache invalidated", user_id=user_id)
            return True
        except Exception as e:
            logger.error("Failed to invalidate user permissions cache", user_id=user_id, error=str(e))
            return False
    
    async def invalidate_role_permissions(self, role_type: str, role_name: str) -> bool:
        """
        Invalidate permissions for all users with a specific role
        This is called when role permissions are updated
        """
        try:
            # Find all users with this role
            user_ids = await self._get_users_with_role(role_type, role_name)
            
            # Invalidate cache for each user
            invalidated_count = 0
            for user_id in user_ids:
                if await self.invalidate_user_permissions(user_id):
                    invalidated_count += 1
            
            logger.info("Role permission cache invalidated", 
                       role_type=role_type, role_name=role_name, 
                       users_affected=invalidated_count)
            
            return invalidated_count == len(user_ids)
            
        except Exception as e:
            logger.error("Failed to invalidate role permissions", 
                        role_type=role_type, role_name=role_name, error=str(e))
            return False
    
    async def update_role_permissions(self, role_type: str, role_name: str, 
                                    permissions: List[str], updated_by: str) -> bool:
        """
        Update permissions for a role and propagate to all users
        
        Args:
            role_type: 'system', 'region', 'office'
            role_name: The role identifier
            permissions: List of permission names
            updated_by: User making the change
        """
        try:
            # Update role permissions in database
            success = await self._update_role_in_db(role_type, role_name, permissions, updated_by)
            
            if success:
                # Invalidate cache for all affected users
                await self.invalidate_role_permissions(role_type, role_name)
                
                # Log audit trail
                await self._log_permission_change(role_type, role_name, permissions, updated_by)
                
                logger.info("Role permissions updated successfully", 
                           role_type=role_type, role_name=role_name, 
                           permission_count=len(permissions))
                return True
            
            return False
            
        except Exception as e:
            logger.error("Failed to update role permissions", 
                        role_type=role_type, role_name=role_name, error=str(e))
            return False
    
    # Database interaction methods
    async def _get_user_assignments(self, user_id: str) -> Dict[str, Any]:
        """Get user with all role assignments"""
        # This will be implemented with the new database schema
        query = text("""
            SELECT 
                u.id,
                u.system_type,
                u.individual_permissions,
                json_agg(DISTINCT jsonb_build_object(
                    'region_id', ura.region_id,
                    'region_role', ura.region_role,
                    'is_active', ura.is_active
                )) FILTER (WHERE ura.region_id IS NOT NULL) as region_assignments,
                json_agg(DISTINCT jsonb_build_object(
                    'office_id', uoa.office_id,
                    'office_role', uoa.office_role,
                    'is_active', uoa.is_active
                )) FILTER (WHERE uoa.office_id IS NOT NULL) as office_assignments
            FROM users u
            LEFT JOIN user_region_assignments ura ON u.id = ura.user_id AND ura.is_active = true
            LEFT JOIN user_office_assignments uoa ON u.id = uoa.user_id AND uoa.is_active = true
            WHERE u.id = :user_id AND u.is_active = true
            GROUP BY u.id, u.system_type, u.individual_permissions
        """)
        
        result = self.db.execute(query, {"user_id": user_id}).fetchone()
        
        if not result:
            return None
        
        return {
            "user_id": str(result.id),
            "system_type": result.system_type,
            "individual_permissions": result.individual_permissions or [],
            "region_assignments": result.region_assignments or [],
            "office_assignments": result.office_assignments or []
        }
    
    async def _get_system_permissions(self, system_type: SystemType) -> Set[str]:
        """Get permissions for system type"""
        query = text("""
            SELECT permissions 
            FROM user_types 
            WHERE type_code = :system_type AND is_active = true
        """)
        
        result = self.db.execute(query, {"system_type": system_type.value}).fetchone()
        
        if result and result.permissions:
            return set(result.permissions)
        
        return set()
    
    async def _get_region_role_permissions(self, region_role: str) -> Set[str]:
        """Get permissions for region role"""
        query = text("""
            SELECT permissions 
            FROM region_roles 
            WHERE role_name = :role_name AND is_active = true
        """)
        
        result = self.db.execute(query, {"role_name": region_role}).fetchone()
        
        if result and result.permissions:
            return set(result.permissions)
        
        return set()
    
    async def _get_office_role_permissions(self, office_role: str) -> Set[str]:
        """Get permissions for office role"""
        query = text("""
            SELECT permissions 
            FROM office_roles 
            WHERE role_name = :role_name AND is_active = true
        """)
        
        result = self.db.execute(query, {"role_name": office_role}).fetchone()
        
        if result and result.permissions:
            return set(result.permissions)
        
        return set()
    
    async def _compile_geographic_access(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compile geographic access from user assignments"""
        access = {
            "provinces": set(),
            "regions": set(), 
            "offices": set()
        }
        
        # Add regions and their provinces
        for assignment in user_data.get("region_assignments", []):
            region_id = assignment["region_id"]
            access["regions"].add(region_id)
            
            # Get province for this region
            query = text("SELECT province_code FROM regions WHERE id = :region_id")
            result = self.db.execute(query, {"region_id": region_id}).fetchone()
            if result:
                access["provinces"].add(result.province_code)
        
        # Add offices and their regions/provinces
        for assignment in user_data.get("office_assignments", []):
            office_id = assignment["office_id"]
            access["offices"].add(office_id)
            
            # Get region and province for this office
            query = text("""
                SELECT r.id as region_id, r.province_code 
                FROM offices o 
                JOIN regions r ON o.region_id = r.id 
                WHERE o.id = :office_id
            """)
            result = self.db.execute(query, {"office_id": office_id}).fetchone()
            if result:
                access["regions"].add(result.region_id)
                access["provinces"].add(result.province_code)
        
        # Convert sets to lists for JSON serialization
        return {k: list(v) for k, v in access.items()}
    
    async def _check_geographic_access(self, compiled: CompiledPermissions, context: Dict[str, Any]) -> bool:
        """Check if user has geographic access based on context"""
        
        # National Help Desk has access to all provinces
        if compiled.system_type == SystemType.NATIONAL_HELP_DESK:
            return True
        
        # Check province access
        if "province_code" in context:
            if context["province_code"] not in compiled.geographic_access.get("provinces", []):
                return False
        
        # Check region access
        if "region_id" in context:
            if context["region_id"] not in compiled.geographic_access.get("regions", []):
                return False
        
        # Check office access
        if "office_id" in context:
            if context["office_id"] not in compiled.geographic_access.get("offices", []):
                return False
        
        return True
    
    # Cache interaction methods (will integrate with existing cache system)
    async def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache"""
        if not self.cache_client:
            return None
        
        try:
            # Assuming Redis-like interface
            data = await self.cache_client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning("Cache get failed", key=key, error=str(e))
        
        return None
    
    async def _store_in_cache(self, key: str, data: Dict[str, Any], ttl: int) -> bool:
        """Store data in cache"""
        if not self.cache_client:
            return False
        
        try:
            await self.cache_client.setex(key, ttl, json.dumps(data, default=str))
            return True
        except Exception as e:
            logger.warning("Cache store failed", key=key, error=str(e))
            return False
    
    async def _delete_from_cache(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.cache_client:
            return False
        
        try:
            await self.cache_client.delete(key)
            return True
        except Exception as e:
            logger.warning("Cache delete failed", key=key, error=str(e))
            return False
    
    # Helper methods for role management
    async def _get_users_with_role(self, role_type: str, role_name: str) -> List[str]:
        """Get all user IDs that have a specific role"""
        if role_type == "system":
            query = text("SELECT id FROM users WHERE system_type = :role_name AND is_active = true")
            results = self.db.execute(query, {"role_name": role_name}).fetchall()
            
        elif role_type == "region":
            query = text("SELECT user_id FROM user_region_assignments WHERE region_role = :role_name AND is_active = true")
            results = self.db.execute(query, {"role_name": role_name}).fetchall()
            
        elif role_type == "office":
            query = text("SELECT user_id FROM user_office_assignments WHERE office_role = :role_name AND is_active = true")
            results = self.db.execute(query, {"role_name": role_name}).fetchall()
            
        else:
            return []
        
        return [str(row[0]) for row in results]
    
    async def _update_role_in_db(self, role_type: str, role_name: str, 
                                permissions: List[str], updated_by: str) -> bool:
        """Update role permissions in database"""
        try:
            permissions_json = json.dumps(permissions)
            
            if role_type == "system":
                query = text("""
                    UPDATE user_types 
                    SET permissions = :permissions, updated_by = :updated_by, updated_at = NOW()
                    WHERE type_code = :role_name
                """)
                
            elif role_type == "region":
                query = text("""
                    UPDATE region_roles 
                    SET permissions = :permissions, updated_by = :updated_by, updated_at = NOW()
                    WHERE role_name = :role_name
                """)
                
            elif role_type == "office":
                query = text("""
                    UPDATE office_roles 
                    SET permissions = :permissions, updated_by = :updated_by, updated_at = NOW()
                    WHERE role_name = :role_name
                """)
            else:
                return False
            
            result = self.db.execute(query, {
                "permissions": permissions_json,
                "role_name": role_name,
                "updated_by": updated_by
            })
            
            self.db.commit()
            return result.rowcount > 0
            
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to update role in database", error=str(e))
            return False
    
    async def _log_permission_change(self, role_type: str, role_name: str, 
                                   permissions: List[str], updated_by: str) -> None:
        """Log permission changes for audit trail"""
        try:
            audit_data = {
                "role_type": role_type,
                "role_name": role_name,
                "permissions": permissions,
                "permission_count": len(permissions)
            }
            
            query = text("""
                INSERT INTO permission_audit_logs 
                (id, role_type, role_name, action, details, updated_by, created_at)
                VALUES (:id, :role_type, :role_name, :action, :details, :updated_by, NOW())
            """)
            
            self.db.execute(query, {
                "id": str(uuid.uuid4()),
                "role_type": role_type,
                "role_name": role_name,
                "action": "permissions_updated",
                "details": json.dumps(audit_data),
                "updated_by": updated_by
            })
            
            self.db.commit()
            
        except Exception as e:
            logger.error("Failed to log permission change", error=str(e))


# Global permission engine instance (will be initialized with database)
_permission_engine: Optional[PermissionEngine] = None

def get_permission_engine(db: Session, cache_client=None) -> PermissionEngine:
    """Get or create permission engine instance"""
    global _permission_engine
    
    if _permission_engine is None:
        _permission_engine = PermissionEngine(db, cache_client)
    
    return _permission_engine

async def check_user_permission(user_id: str, permission: str, db: Session, 
                              context: Dict[str, Any] = None, cache_client=None) -> bool:
    """Convenience function for permission checking"""
    engine = get_permission_engine(db, cache_client)
    return await engine.check_permission(user_id, permission, context)