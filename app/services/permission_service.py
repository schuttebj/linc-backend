"""
Permission Management Service
Handles role and permission administration for the LINC system
"""

import json
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_
from fastapi import HTTPException, status
import structlog

from app.core.permission_engine import get_permission_engine, SystemType

logger = structlog.get_logger()

class PermissionService:
    """
    Service for managing permissions, roles, and user assignments
    """
    
    def __init__(self, db: Session, cache_client=None):
        self.db = db
        self.cache_client = cache_client
        self.permission_engine = get_permission_engine(db, cache_client)
    
    # System Type Management
    async def get_system_types(self) -> List[Dict[str, Any]]:
        """Get all system types with their permissions"""
        try:
            query = text("""
                SELECT type_code, display_name, description, permissions, 
                       is_active, created_at, updated_at, updated_by
                FROM user_types 
                WHERE is_active = true
                ORDER BY type_code
            """)
            
            results = self.db.execute(query).fetchall()
            
            system_types = []
            for row in results:
                system_types.append({
                    "type_code": row.type_code,
                    "display_name": row.display_name,
                    "description": row.description,
                    "permissions": row.permissions or [],
                    "permission_count": len(row.permissions or []),
                    "is_active": row.is_active,
                    "created_at": row.created_at,
                    "updated_at": row.updated_at,
                    "updated_by": row.updated_by
                })
            
            return system_types
            
        except Exception as e:
            logger.error("Failed to get system types", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve system types"
            )
    
    async def update_system_type_permissions(self, type_code: str, permissions: List[str], 
                                           updated_by: str) -> bool:
        """Update permissions for a system type"""
        try:
            success = await self.permission_engine.update_role_permissions(
                "system", type_code, permissions, updated_by
            )
            
            if success:
                logger.info("System type permissions updated", 
                           type_code=type_code, 
                           permission_count=len(permissions))
            
            return success
            
        except Exception as e:
            logger.error("Failed to update system type permissions", 
                        type_code=type_code, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update system type permissions"
            )
    
    # Region Role Management
    async def get_region_roles(self) -> List[Dict[str, Any]]:
        """Get all region roles with their permissions"""
        try:
            query = text("""
                SELECT role_name, display_name, description, permissions, 
                       is_active, created_at, updated_at, updated_by
                FROM region_roles 
                WHERE is_active = true
                ORDER BY role_name
            """)
            
            results = self.db.execute(query).fetchall()
            
            region_roles = []
            for row in results:
                region_roles.append({
                    "role_name": row.role_name,
                    "display_name": row.display_name,
                    "description": row.description,
                    "permissions": row.permissions or [],
                    "permission_count": len(row.permissions or []),
                    "is_active": row.is_active,
                    "created_at": row.created_at,
                    "updated_at": row.updated_at,
                    "updated_by": row.updated_by
                })
            
            return region_roles
            
        except Exception as e:
            logger.error("Failed to get region roles", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve region roles"
            )
    
    async def update_region_role_permissions(self, role_name: str, permissions: List[str], 
                                           updated_by: str) -> bool:
        """Update permissions for a region role"""
        try:
            success = await self.permission_engine.update_role_permissions(
                "region", role_name, permissions, updated_by
            )
            
            if success:
                logger.info("Region role permissions updated", 
                           role_name=role_name, 
                           permission_count=len(permissions))
            
            return success
            
        except Exception as e:
            logger.error("Failed to update region role permissions", 
                        role_name=role_name, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update region role permissions"
            )
    
    # Office Role Management
    async def get_office_roles(self) -> List[Dict[str, Any]]:
        """Get all office roles with their permissions"""
        try:
            query = text("""
                SELECT role_name, display_name, description, permissions, 
                       is_active, created_at, updated_at, updated_by
                FROM office_roles 
                WHERE is_active = true
                ORDER BY role_name
            """)
            
            results = self.db.execute(query).fetchall()
            
            office_roles = []
            for row in results:
                office_roles.append({
                    "role_name": row.role_name,
                    "display_name": row.display_name,
                    "description": row.description,
                    "permissions": row.permissions or [],
                    "permission_count": len(row.permissions or []),
                    "is_active": row.is_active,
                    "created_at": row.created_at,
                    "updated_at": row.updated_at,
                    "updated_by": row.updated_by
                })
            
            return office_roles
            
        except Exception as e:
            logger.error("Failed to get office roles", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve office roles"
            )
    
    async def update_office_role_permissions(self, role_name: str, permissions: List[str], 
                                           updated_by: str) -> bool:
        """Update permissions for an office role"""
        try:
            success = await self.permission_engine.update_role_permissions(
                "office", role_name, permissions, updated_by
            )
            
            if success:
                logger.info("Office role permissions updated", 
                           role_name=role_name, 
                           permission_count=len(permissions))
            
            return success
            
        except Exception as e:
            logger.error("Failed to update office role permissions", 
                        role_name=role_name, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update office role permissions"
            )
    
    # Available Permissions Management
    async def get_available_permissions(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all available permissions organized by category"""
        try:
            # Define all available permissions by category
            permissions_by_category = {
                # License Management
                "license": [
                    {"name": "license.application.create", "display_name": "Create License Applications", "description": "Create new license applications"},
                    {"name": "license.application.read", "display_name": "View License Applications", "description": "View license applications and details"},
                    {"name": "license.application.update", "display_name": "Update License Applications", "description": "Update license application information"},
                    {"name": "license.application.delete", "display_name": "Delete License Applications", "description": "Delete license applications"},
                    {"name": "license.application.approve", "display_name": "Approve License Applications", "description": "Approve or reject license applications"},
                    {"name": "license.issue", "display_name": "Issue Licenses", "description": "Issue new licenses"},
                    {"name": "license.renew", "display_name": "Renew Licenses", "description": "Process license renewals"},
                    {"name": "license.suspend", "display_name": "Suspend Licenses", "description": "Suspend or revoke licenses"},
                    {"name": "license.duplicate", "display_name": "Issue Duplicate Licenses", "description": "Issue duplicate licenses"},
                ],
                
                # Person Management
                "person": [
                    {"name": "person.create", "display_name": "Create Person Records", "description": "Create new person records"},
                    {"name": "person.read", "display_name": "View Person Records", "description": "View person information"},
                    {"name": "person.update", "display_name": "Update Person Records", "description": "Update person information"},
                    {"name": "person.delete", "display_name": "Delete Person Records", "description": "Delete person records"},
                    {"name": "person.search", "display_name": "Search Persons", "description": "Search and find person records"},
                ],
                
                # Financial Operations
                "financial": [
                    {"name": "finance.payment.create", "display_name": "Process Payments", "description": "Process and record payments"},
                    {"name": "finance.payment.read", "display_name": "View Financial Records", "description": "View payment and financial records"},
                    {"name": "finance.payment.update", "display_name": "Update Payment Records", "description": "Update payment information"},
                    {"name": "finance.refund.process", "display_name": "Process Refunds", "description": "Process refund requests"},
                    {"name": "finance.receipt.generate", "display_name": "Generate Receipts", "description": "Generate payment receipts"},
                    {"name": "finance.reconciliation", "display_name": "Financial Reconciliation", "description": "Perform financial reconciliation"},
                ],
                
                # Testing Operations
                "testing": [
                    {"name": "test.schedule", "display_name": "Schedule Tests", "description": "Schedule driving tests"},
                    {"name": "test.conduct", "display_name": "Conduct Tests", "description": "Conduct and score driving tests"},
                    {"name": "test.results.read", "display_name": "View Test Results", "description": "View test results and scores"},
                    {"name": "test.results.update", "display_name": "Update Test Results", "description": "Update test results and scores"},
                    {"name": "test.booking.manage", "display_name": "Manage Test Bookings", "description": "Manage test booking appointments"},
                ],
                
                # Vehicle Operations
                "vehicle": [
                    {"name": "vehicle.registration.create", "display_name": "Create Vehicle Registrations", "description": "Register new vehicles"},
                    {"name": "vehicle.registration.read", "display_name": "View Vehicle Registrations", "description": "View vehicle registration details"},
                    {"name": "vehicle.registration.update", "display_name": "Update Vehicle Registrations", "description": "Update vehicle registration information"},
                    {"name": "vehicle.registration.renew", "display_name": "Renew Vehicle Registrations", "description": "Process vehicle registration renewals"},
                    {"name": "vehicle.inspection", "display_name": "Vehicle Inspections", "description": "Conduct vehicle inspections"},
                ],
                
                # Administrative Functions
                "administration": [
                    {"name": "admin.user.create", "display_name": "Create Users", "description": "Create new system users"},
                    {"name": "admin.user.read", "display_name": "View Users", "description": "View system users"},
                    {"name": "admin.user.update", "display_name": "Update Users", "description": "Update system user accounts"},
                    {"name": "admin.user.delete", "display_name": "Delete Users", "description": "Delete system user accounts"},
                    {"name": "admin.role.manage", "display_name": "Manage Roles", "description": "Create and manage user roles"},
                    {"name": "admin.permission.manage", "display_name": "Manage Permissions", "description": "Manage system permissions"},
                    {"name": "admin.system.config", "display_name": "System Configuration", "description": "Configure system settings"},
                    {"name": "admin.audit.read", "display_name": "View Audit Logs", "description": "View system audit logs"},
                ],
                
                # Reporting
                "reporting": [
                    {"name": "report.license.read", "display_name": "License Reports", "description": "Generate license-related reports"},
                    {"name": "report.financial.read", "display_name": "Financial Reports", "description": "Generate financial reports"},
                    {"name": "report.operational.read", "display_name": "Operational Reports", "description": "Generate operational reports"},
                    {"name": "report.audit.read", "display_name": "Audit Reports", "description": "Generate audit reports"},
                    {"name": "report.export", "display_name": "Export Reports", "description": "Export reports to various formats"},
                ],
                
                # Infringement Management
                "infringement": [
                    {"name": "infringement.create", "display_name": "Create Infringements", "description": "Create traffic infringement records"},
                    {"name": "infringement.read", "display_name": "View Infringements", "description": "View infringement records"},
                    {"name": "infringement.update", "display_name": "Update Infringements", "description": "Update infringement information"},
                    {"name": "infringement.process", "display_name": "Process Infringements", "description": "Process infringement payments and appeals"},
                ],
                
                # Location Management
                "location": [
                    {"name": "location.region.manage", "display_name": "Manage Regions", "description": "Manage region definitions and assignments"},
                    {"name": "location.office.manage", "display_name": "Manage Offices", "description": "Manage office definitions and assignments"},
                    {"name": "location.assignment.manage", "display_name": "Manage Location Assignments", "description": "Assign users to locations"},
                ]
            }
            
            return permissions_by_category
            
        except Exception as e:
            logger.error("Failed to get available permissions", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve available permissions"
            )
    
    # Permission Analysis and Impact
    async def analyze_permission_impact(self, role_type: str, role_name: str, 
                                      new_permissions: List[str]) -> Dict[str, Any]:
        """Analyze the impact of changing role permissions"""
        try:
            # Get current permissions
            current_permissions = set()
            if role_type == "system":
                current_permissions = await self.permission_engine._get_system_permissions(SystemType(role_name))
            elif role_type == "region":
                current_permissions = await self.permission_engine._get_region_role_permissions(role_name)
            elif role_type == "office":
                current_permissions = await self.permission_engine._get_office_role_permissions(role_name)
            
            new_permissions_set = set(new_permissions)
            
            # Calculate changes
            added_permissions = new_permissions_set - current_permissions
            removed_permissions = current_permissions - new_permissions_set
            unchanged_permissions = current_permissions & new_permissions_set
            
            # Get affected users
            affected_users = await self.permission_engine._get_users_with_role(role_type, role_name)
            
            # Get user details
            user_details = []
            if affected_users:
                query = text("""
                    SELECT id, username, first_name, last_name, email, is_active
                    FROM users 
                    WHERE id = ANY(:user_ids) AND is_active = true
                """)
                
                results = self.db.execute(query, {"user_ids": affected_users}).fetchall()
                
                for row in results:
                    user_details.append({
                        "id": str(row.id),
                        "username": row.username,
                        "display_name": f"{row.first_name} {row.last_name}".strip() or row.username,
                        "email": row.email,
                        "is_active": row.is_active
                    })
            
            impact_analysis = {
                "role_type": role_type,
                "role_name": role_name,
                "current_permission_count": len(current_permissions),
                "new_permission_count": len(new_permissions_set),
                "changes": {
                    "added": list(added_permissions),
                    "removed": list(removed_permissions),
                    "unchanged": list(unchanged_permissions),
                    "added_count": len(added_permissions),
                    "removed_count": len(removed_permissions)
                },
                "affected_users": {
                    "count": len(affected_users),
                    "users": user_details
                },
                "impact_level": self._calculate_impact_level(len(added_permissions), len(removed_permissions), len(affected_users))
            }
            
            return impact_analysis
            
        except Exception as e:
            logger.error("Failed to analyze permission impact", 
                        role_type=role_type, role_name=role_name, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to analyze permission impact"
            )
    
    def _calculate_impact_level(self, added_count: int, removed_count: int, user_count: int) -> str:
        """Calculate the impact level of permission changes"""
        total_changes = added_count + removed_count
        
        if total_changes == 0:
            return "none"
        elif total_changes <= 2 and user_count <= 5:
            return "low"
        elif total_changes <= 5 and user_count <= 20:
            return "medium"
        else:
            return "high"
    
    # User Permission Analysis
    async def get_user_permission_summary(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive permission summary for a user"""
        try:
            # Compile user permissions
            compiled = await self.permission_engine.compile_user_permissions(user_id)
            
            # Get user details
            query = text("""
                SELECT u.username, u.first_name, u.last_name, u.email, u.system_type,
                       u.is_active, u.created_at,
                       json_agg(DISTINCT jsonb_build_object(
                           'region_id', ura.region_id,
                           'region_role', ura.region_role,
                           'region_name', r.region_name
                       )) FILTER (WHERE ura.region_id IS NOT NULL) as region_assignments,
                       json_agg(DISTINCT jsonb_build_object(
                           'office_id', uoa.office_id,
                           'office_role', uoa.office_role,
                           'office_name', o.office_name
                       )) FILTER (WHERE uoa.office_id IS NOT NULL) as office_assignments
                FROM users u
                LEFT JOIN user_region_assignments ura ON u.id = ura.user_id AND ura.is_active = true
                LEFT JOIN regions r ON ura.region_id = r.id
                LEFT JOIN user_office_assignments uoa ON u.id = uoa.user_id AND uoa.is_active = true
                LEFT JOIN offices o ON uoa.office_id = o.id
                WHERE u.id = :user_id
                GROUP BY u.id, u.username, u.first_name, u.last_name, u.email, 
                         u.system_type, u.is_active, u.created_at
            """)
            
            result = self.db.execute(query, {"user_id": user_id}).fetchone()
            
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Organize permissions by source
            permission_sources = {
                "system": {
                    "type": compiled.system_type.value,
                    "permissions": list(compiled.system_permissions),
                    "count": len(compiled.system_permissions)
                },
                "regions": {},
                "offices": {},
                "individual": list(compiled.individual_overrides)
            }
            
            # Add region permissions
            for region_id, permissions in compiled.region_permissions.items():
                region_assignment = next((r for r in (result.region_assignments or []) 
                                        if r['region_id'] == region_id), None)
                permission_sources["regions"][region_id] = {
                    "region_name": region_assignment['region_name'] if region_assignment else f"Region {region_id}",
                    "region_role": region_assignment['region_role'] if region_assignment else "Unknown",
                    "permissions": list(permissions),
                    "count": len(permissions)
                }
            
            # Add office permissions
            for office_id, permissions in compiled.office_permissions.items():
                office_assignment = next((o for o in (result.office_assignments or []) 
                                        if o['office_id'] == office_id), None)
                permission_sources["offices"][office_id] = {
                    "office_name": office_assignment['office_name'] if office_assignment else f"Office {office_id}",
                    "office_role": office_assignment['office_role'] if office_assignment else "Unknown",
                    "permissions": list(permissions),
                    "count": len(permissions)
                }
            
            summary = {
                "user": {
                    "id": user_id,
                    "username": result.username,
                    "display_name": f"{result.first_name} {result.last_name}".strip() or result.username,
                    "email": result.email,
                    "system_type": result.system_type,
                    "is_active": result.is_active,
                    "created_at": result.created_at
                },
                "permission_summary": {
                    "total_permissions": len(compiled.final_permissions),
                    "compiled_at": compiled.compiled_at,
                    "expires_at": compiled.expires_at
                },
                "permission_sources": permission_sources,
                "final_permissions": list(compiled.final_permissions),
                "geographic_access": compiled.geographic_access,
                "assignments": {
                    "regions": result.region_assignments or [],
                    "offices": result.office_assignments or []
                }
            }
            
            return summary
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get user permission summary", user_id=user_id, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve user permission summary"
            )
    
    # Audit and History
    async def get_permission_audit_history(self, role_type: str = None, role_name: str = None, 
                                         limit: int = 50) -> List[Dict[str, Any]]:
        """Get permission change audit history"""
        try:
            query_conditions = ["1=1"]
            query_params = {"limit": limit}
            
            if role_type:
                query_conditions.append("role_type = :role_type")
                query_params["role_type"] = role_type
            
            if role_name:
                query_conditions.append("role_name = :role_name")
                query_params["role_name"] = role_name
            
            query = text(f"""
                SELECT id, role_type, role_name, action, details, updated_by, created_at
                FROM permission_audit_logs 
                WHERE {' AND '.join(query_conditions)}
                ORDER BY created_at DESC
                LIMIT :limit
            """)
            
            results = self.db.execute(query, query_params).fetchall()
            
            audit_history = []
            for row in results:
                details = {}
                try:
                    if row.details:
                        details = json.loads(row.details)
                except:
                    pass
                
                audit_history.append({
                    "id": str(row.id),
                    "role_type": row.role_type,
                    "role_name": row.role_name,
                    "action": row.action,
                    "details": details,
                    "updated_by": row.updated_by,
                    "created_at": row.created_at
                })
            
            return audit_history
            
        except Exception as e:
            logger.error("Failed to get permission audit history", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve permission audit history"
            )