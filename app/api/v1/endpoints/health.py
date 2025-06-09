"""
Health Check Endpoints
System health, database connectivity, and status monitoring
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import time
from typing import Dict, Any

from app.core.database import get_db, DatabaseManager
from app.core.config import settings

router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "LINC Backend",
        "version": settings.VERSION,
        "timestamp": time.time()
    }


@router.get("/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """Detailed health check with database connectivity"""
    health_status = {
        "status": "healthy",
        "service": "LINC Backend",
        "version": settings.VERSION,
        "timestamp": time.time(),
        "database_connections": {},
        "file_storage": {},
        "configuration": {
            "supported_countries": settings.SUPPORTED_COUNTRIES,
            "default_country": settings.DEFAULT_COUNTRY_CODE
        }
    }
    
    # Test database connections for all countries
    for country_code in settings.SUPPORTED_COUNTRIES:
        try:
            connection_status = DatabaseManager.test_connection(country_code)
            health_status["database_connections"][country_code] = {
                "status": "connected" if connection_status else "failed",
                "tested_at": time.time()
            }
        except Exception as e:
            health_status["database_connections"][country_code] = {
                "status": "error",
                "error": str(e),
                "tested_at": time.time()
            }
    
    # Test file storage accessibility
    for country_code in settings.SUPPORTED_COUNTRIES:
        try:
            storage_path = settings.get_file_storage_path(country_code)
            storage_accessible = storage_path.exists()
            health_status["file_storage"][country_code] = {
                "status": "accessible" if storage_accessible else "not_found",
                "path": str(storage_path),
                "tested_at": time.time()
            }
        except Exception as e:
            health_status["file_storage"][country_code] = {
                "status": "error",
                "error": str(e),
                "tested_at": time.time()
            }
    
    # Determine overall health status
    db_issues = [
        country for country, status in health_status["database_connections"].items()
        if status["status"] != "connected"
    ]
    
    storage_issues = [
        country for country, status in health_status["file_storage"].items()
        if status["status"] != "accessible"
    ]
    
    if db_issues or storage_issues:
        health_status["status"] = "degraded"
        health_status["issues"] = {
            "database_issues": db_issues,
            "storage_issues": storage_issues
        }
    
    return health_status


@router.get("/database/{country}")
async def test_database_connection(country: str) -> Dict[str, Any]:
    """Test database connection for specific country"""
    country_code = country.upper()
    
    if country_code not in settings.SUPPORTED_COUNTRIES:
        raise HTTPException(
            status_code=404,
            detail=f"Country {country_code} not supported"
        )
    
    try:
        connection_status = DatabaseManager.test_connection(country_code)
        return {
            "country": country_code,
            "database_status": "connected" if connection_status else "failed",
            "tested_at": time.time()
        }
    except Exception as e:
        return {
            "country": country_code,
            "database_status": "error",
            "error": str(e),
            "tested_at": time.time()
        } 