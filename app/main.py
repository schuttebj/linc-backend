# app/main.py - LINC Driver's Licensing System Backend
# Version: 2025-06-11 - Fixed initials validation for natural persons
"""
LINC Driver's Licensing System - Main Application
FastAPI backend for modular, country-customizable driver licensing platform
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog
import time
import uuid

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.api import api_router
from app.core.middleware import AuditMiddleware

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Create application instance
app = FastAPI(
    title="LINC Driver's Licensing System",
    description="Modular, cloud-native driver's licensing platform for African countries",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Configure multiple authentication schemes for OpenAPI
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    from fastapi.openapi.utils import get_openapi
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add multiple authentication schemes
    # TODO: REMOVE HTTPBasic before PRODUCTION! ⚠️
    openapi_schema["components"]["securitySchemes"] = {
        "HTTPBasic": {
            "type": "http",
            "scheme": "basic",
            "description": "⚠️ TESTING ONLY - Simple username/password authentication (REMOVE IN PRODUCTION)"
        },
        "HTTPBearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT Bearer token authentication (for production)"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=settings.allowed_hosts_list
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom audit middleware
app.add_middleware(AuditMiddleware)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled exception",
        exc_info=exc,
        url=str(request.url),
        method=request.method
    )
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "timestamp": time.time()
        }
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "service": "LINC Driver's Licensing System",
        "version": "1.0.0",
        "status": "operational",
        "api_docs": f"{settings.API_V1_STR}/docs",
        "health_check": "/health",
        "cors_origins": settings.allowed_origins_list,  # Debug CORS config
        "timestamp": time.time()
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "LINC Backend",
        "version": "1.0.0",
        "timestamp": time.time()
    }

# Database health check endpoint
@app.get("/health/database")
async def database_health_check():
    """Database health check endpoint for debugging"""
    from app.core.database import DatabaseManager
    from app.core.config import get_settings
    import os
    
    try:
        config = get_settings()
        database_url = config.DATABASE_URL
        
        # Mask password for logging
        masked_url = database_url
        if "@" in database_url:
            parts = database_url.split("@")
            if "://" in parts[0]:
                schema_user = parts[0].split("://")
                if ":" in schema_user[1]:
                    user_pass = schema_user[1].split(":")
                    masked_url = f"{schema_user[0]}://{user_pass[0]}:***@{parts[1]}"
        
        # Test database connection
        connection_ok = DatabaseManager.test_connection()
        
        return {
            "status": "healthy" if connection_ok else "unhealthy",
            "database_url_masked": masked_url,
            "database_url_from_env": os.getenv("DATABASE_URL", "Not set"),
            "connection_test": "passed" if connection_ok else "failed",
            "timestamp": time.time()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "database_url_from_env": os.getenv("DATABASE_URL", "Not set"),
            "timestamp": time.time()
        }

# Database initialization endpoint (for debugging)
@app.post("/admin/init-database")
async def init_database():
    """Initialize database tables and basic data - ADMIN ONLY"""
    try:
        from app.core.database import engine, Base
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        return {
            "status": "success",
            "message": "Database tables created successfully",
            "timestamp": time.time()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }

# Database reset endpoint (for debugging) - DANGEROUS!
@app.post("/admin/reset-database")
async def reset_database():
    """Drop and recreate all database tables - ADMIN ONLY - DANGEROUS!"""
    try:
        from app.core.database import engine, Base
        
        # Drop all existing tables
        Base.metadata.drop_all(bind=engine)
        
        # Recreate all tables with current schema
        Base.metadata.create_all(bind=engine)
        
        return {
            "status": "success",
            "message": "Database tables dropped and recreated successfully",
            "warning": "All existing data was destroyed",
            "timestamp": time.time()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }

# User initialization endpoint (for debugging)
@app.post("/admin/init-users")
async def init_users():
    """Create default users and roles - ADMIN ONLY"""
    try:
        from app.core.database import get_db_context
        from app.models.user import User, Role, Permission, UserStatus
        from app.core.security import get_password_hash
        from datetime import datetime
        import uuid
        
        with get_db_context() as db:
            # Check if admin user already exists and update status if needed
            existing_admin = db.query(User).filter(User.username == "admin").first()
            if existing_admin:
                # Update existing admin user to ensure it's ACTIVE
                existing_admin.status = UserStatus.ACTIVE.value
                existing_admin.is_active = True
                existing_admin.password_hash = get_password_hash("Admin123!")
                db.commit()
                return {
                    "status": "success",
                    "message": "Admin user updated to ACTIVE status",
                    "username": "admin", 
                    "password": "Admin123!",
                    "status_set": "ACTIVE",
                    "timestamp": time.time()
                }
            
            # Create default permissions
            permissions = [
                # Person management
                {"name": "person_view", "display_name": "View Person Records", "description": "View person records", "category": "person", "resource": "person", "action": "read"},
                {"name": "person_create", "display_name": "Create Person Records", "description": "Create person records", "category": "person", "resource": "person", "action": "create"},
                {"name": "person_edit", "display_name": "Edit Person Records", "description": "Edit person records", "category": "person", "resource": "person", "action": "update"},
                
                # License management
                {"name": "license_view", "display_name": "View License Applications", "description": "View license applications", "category": "license", "resource": "license", "action": "read"},
                {"name": "license_create", "display_name": "Create License Applications", "description": "Create license applications", "category": "license", "resource": "license", "action": "create"},
                {"name": "license_approve", "display_name": "Approve License Applications", "description": "Approve license applications", "category": "license", "resource": "license", "action": "approve"},
                
                # User Group management (NEW)
                {"name": "user_group_create", "display_name": "Create User Groups", "description": "Create user groups and authorities", "category": "admin", "resource": "user_group", "action": "create"},
                {"name": "user_group_read", "display_name": "View User Groups", "description": "View user groups and authorities", "category": "admin", "resource": "user_group", "action": "read"},
                {"name": "user_group_update", "display_name": "Update User Groups", "description": "Update user groups and authorities", "category": "admin", "resource": "user_group", "action": "update"},
                {"name": "user_group_delete", "display_name": "Delete User Groups", "description": "Delete user groups and authorities", "category": "admin", "resource": "user_group", "action": "delete"},
                
                # Location management (NEW)
                {"name": "location_create", "display_name": "Create Locations", "description": "Create testing centers and facilities", "category": "admin", "resource": "location", "action": "create"},
                {"name": "location_read", "display_name": "View Locations", "description": "View testing centers and facilities", "category": "admin", "resource": "location", "action": "read"},
                {"name": "location_update", "display_name": "Update Locations", "description": "Update testing centers and facilities", "category": "admin", "resource": "location", "action": "update"},
                {"name": "location_delete", "display_name": "Delete Locations", "description": "Delete testing centers and facilities", "category": "admin", "resource": "location", "action": "delete"},
                
                # Office management (NEW)
                {"name": "office_create", "display_name": "Create Offices", "description": "Create offices within user groups", "category": "admin", "resource": "office", "action": "create"},
                {"name": "office_read", "display_name": "View Offices", "description": "View offices within user groups", "category": "admin", "resource": "office", "action": "read"},
                {"name": "office_update", "display_name": "Update Offices", "description": "Update offices within user groups", "category": "admin", "resource": "office", "action": "update"},
                {"name": "office_delete", "display_name": "Delete Offices", "description": "Delete offices within user groups", "category": "admin", "resource": "office", "action": "delete"},
                
                # Resource management (NEW)
                {"name": "resource_create", "display_name": "Create Resources", "description": "Create location resources", "category": "admin", "resource": "resource", "action": "create"},
                {"name": "resource_read", "display_name": "View Resources", "description": "View location resources", "category": "admin", "resource": "resource", "action": "read"},
                {"name": "resource_update", "display_name": "Update Resources", "description": "Update location resources", "category": "admin", "resource": "resource", "action": "update"},
                {"name": "resource_delete", "display_name": "Delete Resources", "description": "Delete location resources", "category": "admin", "resource": "resource", "action": "delete"},
                
                # User assignment management (NEW)
                {"name": "assignment_create", "display_name": "Create User Assignments", "description": "Assign users to locations", "category": "admin", "resource": "assignment", "action": "create"},
                {"name": "assignment_read", "display_name": "View User Assignments", "description": "View user location assignments", "category": "admin", "resource": "assignment", "action": "read"},
                {"name": "assignment_update", "display_name": "Update User Assignments", "description": "Update user location assignments", "category": "admin", "resource": "assignment", "action": "update"},
                {"name": "assignment_delete", "display_name": "Delete User Assignments", "description": "Remove user location assignments", "category": "admin", "resource": "assignment", "action": "delete"},
                
                # System administration
                {"name": "user_manage", "display_name": "Manage User Accounts", "description": "Manage user accounts", "category": "admin", "resource": "user", "action": "manage"},
                {"name": "system_admin", "display_name": "System Administration", "description": "System administration", "category": "admin", "resource": "system", "action": "admin"}
            ]
            
            created_permissions = {}
            for perm_data in permissions:
                permission = Permission(
                    id=uuid.uuid4(),
                    name=perm_data["name"],
                    display_name=perm_data["display_name"],
                    description=perm_data["description"],
                    category=perm_data["category"],
                    resource=perm_data["resource"],
                    action=perm_data["action"],
                    created_at=datetime.utcnow(),
                    created_by="system"
                )
                db.add(permission)
                created_permissions[perm_data["name"]] = permission
            
            # Create super admin role
            admin_role = Role(
                id=uuid.uuid4(),
                name="super_admin",
                display_name="Super Administrator",
                description="Super Administrator with full system access",
                is_system_role=True,
                created_at=datetime.utcnow(),
                created_by="system"
            )
            db.add(admin_role)
            
            # Add all permissions to admin role
            for permission in created_permissions.values():
                admin_role.permissions.append(permission)
            
            # Create admin user
            admin_user = User(
                id=uuid.uuid4(),
                username="admin",
                email="admin@linc.system",
                first_name="System",
                last_name="Administrator",
                password_hash=get_password_hash("Admin123!"),
                status=UserStatus.ACTIVE.value,
                is_superuser=True,
                require_password_change=True,
                created_at=datetime.utcnow(),
                created_by="system"
            )
            db.add(admin_user)
            
            # Add admin role to user
            admin_user.roles.append(admin_role)
            
            db.commit()
            
            return {
                "status": "success",
                "message": "Default users created successfully",
                "users_created": ["admin"],
                "default_password": "Admin123!",
                "note": "Password must be changed on first login",
                "timestamp": time.time()
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Add test endpoint to verify API router is working
@app.get("/api/v1/test-routing")
async def test_api_routing():
    """Test endpoint to verify API routing is working"""
    return {
        "message": "API routing is working",
        "prefix": settings.API_V1_STR,
        "timestamp": time.time()
    }

# Add debug endpoint to show all registered routes
@app.get("/debug/routes")
async def debug_routes():
    """Debug endpoint to show all registered routes"""
    routes = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods) if route.methods else [],
                "name": getattr(route, 'name', 'unknown')
            })
    return {
        "total_routes": len(routes),
        "routes": routes,
        "timestamp": time.time()
    }

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("LINC Backend starting up")
    
    # Create database tables
    # Note: In production, use Alembic migrations instead
    # Base.metadata.create_all(bind=engine)

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("LINC Backend shutting down")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 