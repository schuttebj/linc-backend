"""
Admin Database Management Endpoints
Provides API endpoints for database initialization and management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import structlog
import subprocess
import sys
import os

from app.core.database import get_db, engine, Base
from app.core.permission_middleware import require_permission
from app.models.user import User

logger = structlog.get_logger()
router = APIRouter()

@router.post("/init-database", response_model=Dict[str, Any])
def init_database(
    current_user: User = Depends(require_permission("admin.database.reset"))
):
    """
    Initialize Database - Create all tables from models
    
    Creates all database tables based on SQLAlchemy models.
    Safe to run multiple times - will not drop existing data.
    """
    try:
        logger.info(f"Database initialization initiated by user: {current_user.username}")
        
        # Create all tables from models
        Base.metadata.create_all(bind=engine)
        logger.info("All tables created successfully")
        
        return {
            "status": "success",
            "message": "Database tables created successfully",
            "initiated_by": current_user.username,
            "warning": "Tables created - use init-users to populate data"
        }
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database initialization failed: {str(e)}"
        )

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
        
        # Drop all existing tables
        Base.metadata.drop_all(bind=engine)
        logger.info("All tables dropped successfully")
        
        # Recreate all tables
        Base.metadata.create_all(bind=engine)
        logger.info("All tables created successfully")
        
        return {
            "status": "success",
            "message": "Database reset completed successfully",
            "warning": "All existing data was destroyed",
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

@router.post("/init-users", response_model=Dict[str, Any])
def init_users(
    current_user: User = Depends(require_permission("admin.system.initialize"))
):
    """
    Initialize User System - Create default user types, regions, offices, and users
    
    Runs the create_new_user_system.py script to populate the database with
    default data for the new permission system. Safe to run multiple times.
    """
    try:
        logger.info(f"User system initialization initiated by: {current_user.username}")
        
        # Get the path to the create_new_user_system.py script
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "create_new_user_system.py")
        
        # Run the user system initialization script
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(script_path)
        )
        
        if result.returncode == 0:
            return {
                "status": "success",
                "message": "User system initialized successfully",
                "script_output": result.stdout,
                "initiated_by": current_user.username,
                "default_admin": {
                    "username": "admin",
                    "password": "Admin123!",
                    "note": "Password must be changed on first login"
                }
            }
        else:
            logger.error(f"User system initialization failed: {result.stderr}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"User system initialization failed: {result.stderr}"
            )
        
    except subprocess.SubprocessError as e:
        logger.error(f"Failed to run user initialization script: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run user initialization script: {str(e)}"
        )
    except Exception as e:
        logger.error(f"User system initialization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User system initialization failed: {str(e)}"
        )

@router.post("/add-missing-permissions", response_model=Dict[str, Any])
def add_missing_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("admin.system.config"))
):
    """
    Add Missing Permissions - Add new permissions to existing user types
    
    This endpoint adds any new permissions that have been defined but are
    missing from existing user types. Useful when new features are added.
    """
    try:
        logger.info(f"Adding missing permissions initiated by: {current_user.username}")
        
        from app.models.user_type import UserType
        from datetime import datetime
        
        # Define new permissions that might be missing
        new_permissions = [
            # Add any new permissions here as the system evolves
            "admin.database.init",
            "admin.database.reset", 
            "admin.database.read",
            "admin.system.initialize",
            "admin.permission.manage",
            "region.create",
            "region.read",
            "region.update", 
            "region.delete",
            "office.create",
            "office.read",
            "office.update",
            "office.delete"
        ]
        
        # Get all user types
        user_types = db.query(UserType).all()
        
        updates_made = []
        
        for user_type in user_types:
            current_permissions = user_type.default_permissions or []
            permissions_added = []
            
            # Add missing permissions based on user type
            if user_type.id == "super_admin":
                # Super admin gets all permissions
                for permission in new_permissions:
                    if permission not in current_permissions:
                        current_permissions.append(permission)
                        permissions_added.append(permission)
            
            elif user_type.id in ["national_help_desk", "provincial_help_desk"]:
                # Help desk gets read permissions
                read_permissions = [p for p in new_permissions if ".read" in p]
                for permission in read_permissions:
                    if permission not in current_permissions:
                        current_permissions.append(permission)
                        permissions_added.append(permission)
            
            elif user_type.id == "license_manager":
                # License managers get region and office management
                manager_permissions = [p for p in new_permissions if p.startswith(("region.", "office."))]
                for permission in manager_permissions:
                    if permission not in current_permissions:
                        current_permissions.append(permission)
                        permissions_added.append(permission)
            
            # Update the user type if permissions were added
            if permissions_added:
                user_type.default_permissions = current_permissions
                user_type.updated_at = datetime.utcnow()
                user_type.updated_by = current_user.username
                updates_made.append({
                    "user_type": user_type.id,
                    "permissions_added": permissions_added
                })
        
        db.commit()
        
        return {
            "status": "success",
            "message": f"Updated {len(updates_made)} user types with missing permissions",
            "updates_made": updates_made,
            "initiated_by": current_user.username
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Adding missing permissions failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Adding missing permissions failed: {str(e)}"
        ) 