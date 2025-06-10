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

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

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