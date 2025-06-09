"""
Health Check Endpoints - Simplified Single Country
System health, database connectivity, and status monitoring
"""

from fastapi import APIRouter
import time
from typing import Dict, Any

from app.core.database import DatabaseManager
from app.core.config import settings

router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "LINC Backend",
        "version": settings.VERSION,
        "country": settings.COUNTRY_CODE,
        "timestamp": time.time()
    }


@router.get("/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """Detailed health check with database connectivity"""
    health_status = {
        "status": "healthy",
        "service": "LINC Backend",
        "version": settings.VERSION,
        "country": settings.COUNTRY_CODE,
        "timestamp": time.time(),
        "database": {},
        "file_storage": {},
        "configuration": {
            "country_code": settings.COUNTRY_CODE,
            "country_name": settings.COUNTRY_NAME,
            "currency": settings.CURRENCY
        }
    }
    
    # Test database connection
    try:
        connection_status = DatabaseManager.test_connection()
        health_status["database"] = {
            "status": "connected" if connection_status else "failed",
            "tested_at": time.time()
        }
    except Exception as e:
        health_status["database"] = {
            "status": "error",
            "error": str(e),
            "tested_at": time.time()
        }
    
    # Test file storage accessibility
    try:
        storage_path = settings.get_file_storage_path()
        storage_accessible = storage_path.exists()
        health_status["file_storage"] = {
            "status": "accessible" if storage_accessible else "not_found",
            "path": str(storage_path),
            "tested_at": time.time()
        }
    except Exception as e:
        health_status["file_storage"] = {
            "status": "error",
            "error": str(e),
            "tested_at": time.time()
        }
    
    # Determine overall health status
    if (health_status["database"]["status"] != "connected" or 
        health_status["file_storage"]["status"] != "accessible"):
        health_status["status"] = "degraded"
        health_status["issues"] = []
        
        if health_status["database"]["status"] != "connected":
            health_status["issues"].append("database_connection")
        
        if health_status["file_storage"]["status"] != "accessible":
            health_status["issues"].append("file_storage")
    
    return health_status


@router.get("/database")
async def test_database_connection() -> Dict[str, Any]:
    """Test database connection"""
    try:
        connection_status = DatabaseManager.test_connection()
        return {
            "country": settings.COUNTRY_CODE,
            "database_status": "connected" if connection_status else "failed",
            "tested_at": time.time()
        }
    except Exception as e:
        return {
            "country": settings.COUNTRY_CODE,
            "database_status": "error",
            "error": str(e),
            "tested_at": time.time()
        } 