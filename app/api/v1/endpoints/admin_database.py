"""
Admin Database Management Endpoints
Provides API endpoints for database initialization and management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import structlog

from app.core.database import get_db, DatabaseManager
from app.core.permission_middleware import require_permission
from app.models.user import User
from app.models import *  # Import all models

logger = structlog.get_logger()
router = APIRouter()

@router.post("/reset-database", response_model=Dict[str, Any])
def reset_database(
    current_user: User = Depends(require_permission("admin.database.reset"))
):
    """
    Reset Database - Drop and recreate all tables
    
    **DANGER**: This will delete ALL data in the database!
    Only use this for development or when migrating to new schema.
    """
    try:
        logger.info(f"Database reset initiated by user: {current_user.username}")
        
        # Drop all tables
        DatabaseManager.drop_all_tables()
        logger.info("All tables dropped successfully")
        
        # Recreate all tables
        DatabaseManager.create_all_tables()
        logger.info("All tables created successfully")
        
        return {
            "status": "success",
            "message": "Database reset completed successfully",
            "tables_dropped": True,
            "tables_created": True,
            "initiated_by": current_user.username
        }
        
    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database reset failed: {str(e)}"
        )

@router.post("/initialize-users", response_model=Dict[str, Any])
def initialize_user_system(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("admin.system.initialize"))
):
    """
    Initialize User System - Create default roles, permissions, and users
    
    This is safe to run multiple times - it will skip existing records.
    """
    try:
        logger.info(f"User system initialization initiated by: {current_user.username}")
        
        # Import the initialization logic
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        
        from create_user_system import create_default_permissions, create_default_roles
        from app.models.user import Permission, Role
        from app.core.security import get_password_hash
        from app.models.enums import UserStatus
        import uuid
        from datetime import datetime
        
        permissions_created = 0
        roles_created = 0
        users_created = 0
        
        # Create permissions
        permission_data = create_default_permissions()
        for perm_data in permission_data:
            existing = db.query(Permission).filter(Permission.name == perm_data["name"]).first()
            if not existing:
                permission = Permission(
                    id=str(uuid.uuid4()),
                    name=perm_data["name"],
                    display_name=perm_data["display_name"],
                    description=perm_data["description"],
                    category=perm_data["category"],
                    is_active=True,
                    created_at=datetime.utcnow(),
                    created_by=current_user.username
                )
                db.add(permission)
                permissions_created += 1
        
        db.commit()
        
        # Create roles
        role_data = create_default_roles()
        for role_info in role_data:
            existing = db.query(Role).filter(Role.name == role_info["name"]).first()
            if not existing:
                role = Role(
                    id=str(uuid.uuid4()),
                    name=role_info["name"],
                    display_name=role_info["display_name"],
                    description=role_info["description"],
                    level=role_info["level"],
                    is_system_role=role_info["is_system_role"],
                    is_active=True,
                    created_at=datetime.utcnow(),
                    created_by=current_user.username
                )
                db.add(role)
                db.flush()
                
                # Add permissions to role
                for perm_name in role_info["permissions"]:
                    permission = db.query(Permission).filter(Permission.name == perm_name).first()
                    if permission:
                        role.permissions.append(permission)
                
                roles_created += 1
        
        db.commit()
        
        # Create admin user if doesn't exist
        admin_exists = db.query(User).filter(User.username == "admin").first()
        if not admin_exists:
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
                created_by=current_user.username
            )
            db.add(admin_user)
            db.flush()
            
            # Add super_admin role
            super_admin_role = db.query(Role).filter(Role.name == "super_admin").first()
            if super_admin_role:
                admin_user.roles.append(super_admin_role)
            
            users_created += 1
        
        db.commit()
        
        return {
            "status": "success",
            "message": "User system initialized successfully",
            "permissions_created": permissions_created,
            "roles_created": roles_created,
            "users_created": users_created,
            "initiated_by": current_user.username
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"User system initialization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User system initialization failed: {str(e)}"
        )

@router.get("/database-status", response_model=Dict[str, Any])
def get_database_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("admin.database.read"))
):
    """
    Get Database Status - Check table existence and record counts
    """
    try:
        from sqlalchemy import text
        
        # Check if main tables exist and get counts
        tables_status = {}
        
        main_tables = [
            "users", "regions", "offices", "user_types", 
            "permissions", "roles", "user_roles", "role_permissions",
            "persons", "audit_logs"
        ]
        
        for table in main_tables:
            try:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                tables_status[table] = {"exists": True, "count": count}
            except Exception:
                tables_status[table] = {"exists": False, "count": 0}
        
        # Test database connection
        connection_ok = DatabaseManager.test_connection()
        
        return {
            "status": "success",
            "connection_ok": connection_ok,
            "tables": tables_status,
            "checked_by": current_user.username
        }
        
    except Exception as e:
        logger.error(f"Database status check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database status check failed: {str(e)}"
        ) 