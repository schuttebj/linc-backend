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

# Database endpoints are now handled by the admin_database router

# Development admin endpoints (no auth required for database setup)
@app.post("/admin/init-database")
async def init_database_dev():
    """Initialize database tables - DEVELOPMENT ONLY"""
    try:
        from app.core.database import engine, Base
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        return {
            "status": "success",
            "message": "Database tables created successfully",
            "warning": "Development endpoint - no authentication required",
            "timestamp": time.time()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }

@app.post("/admin/reset-database")
async def reset_database_dev():
    """Drop and recreate all database tables - DEVELOPMENT ONLY - DANGEROUS!"""
    try:
        from app.core.database import engine, Base
        
        # Drop all existing tables
        Base.metadata.drop_all(bind=engine)
        
        # Recreate all tables with current schema
        Base.metadata.create_all(bind=engine)
        
        return {
            "status": "success",
            "message": "Database tables dropped and recreated successfully",
            "warning": "All existing data was destroyed - Development endpoint",
            "timestamp": time.time()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }

@app.post("/admin/init-users")
async def init_users_dev():
    """Create default users - DEVELOPMENT ONLY"""
    try:
        import subprocess
        import sys
        import os
        
        # Get the path to the create_new_user_system.py script
        script_path = os.path.join(os.path.dirname(__file__), "..", "create_new_user_system.py")
        script_path = os.path.abspath(script_path)
        
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
                "warning": "Development endpoint - no authentication required",
                "default_admin": {
                    "username": "admin",
                    "password": "Admin123!",
                    "note": "Password must be changed on first login"
                },
                "timestamp": time.time()
            }
        else:
            return {
                "status": "error",
                "error": result.stderr,
                "script_output": result.stdout,
                "timestamp": time.time()
            }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }

@app.post("/admin/add-missing-permissions")
async def add_missing_permissions_dev():
    """Add missing permissions to existing user types - DEVELOPMENT ONLY"""
    try:
        from app.core.database import get_db_context
        from app.models.user_type import UserType
        from datetime import datetime
        
        # Define new permissions that might be missing
        new_permissions = [
            "admin.database.init",
            "admin.database.reset", 
            "admin.database.read",
            "admin.system.initialize",
            "admin.system.config",
            "region.create",
            "region.read",
            "region.update", 
            "region.delete",
            "office.create",
            "office.read",
            "office.update",
            "office.delete"
        ]
        
        with get_db_context() as db:
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
                    user_type.updated_by = "system"
                    updates_made.append({
                        "user_type": user_type.id,
                        "permissions_added": permissions_added
                    })
            
            db.commit()
            
            return {
                "status": "success",
                "message": f"Updated {len(updates_made)} user types with missing permissions",
                "updates_made": updates_made,
                "warning": "Development endpoint - no authentication required",
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