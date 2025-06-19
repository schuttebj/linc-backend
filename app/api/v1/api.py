"""
LINC API v1 Router
Single-country deployment with simplified routing
"""

from fastapi import APIRouter
from app.api.v1.endpoints import persons, countries, health, licenses, auth, users, files, monitoring, admin, lookups, migration, user_groups, locations, user_management, permissions

api_router = APIRouter()

# Authentication endpoints (no auth required)
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"]
)

# User management endpoints (admin only)
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["user-management"]
)

# Enhanced user management endpoints
api_router.include_router(
    user_management.router,
    prefix="/user-management",
    tags=["user-management"]
)

# Permission management endpoints (new system)
api_router.include_router(
    permissions.router,
    prefix="/permissions",
    tags=["permissions"]
)

# Location management endpoints
api_router.include_router(
    user_groups.router,
    prefix="/user-groups",
    tags=["user-groups"]
)

api_router.include_router(
    locations.router,
    prefix="/locations",
    tags=["locations"]
)

# Health and system endpoints
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["health"]
)

# Country configuration endpoints
api_router.include_router(
    countries.router,
    prefix="/countries",
    tags=["countries"]
)

# Lookup endpoints for form data
api_router.include_router(
    lookups.router,
    prefix="/lookups",
    tags=["lookups"]
)

# Core business endpoints (single country, no country prefix)
api_router.include_router(
    persons.router,
    prefix="/persons",
    tags=["persons"]
)

# License application endpoints
api_router.include_router(
    licenses.router,
    prefix="/licenses",
    tags=["licenses"]
)

# File management endpoints
api_router.include_router(
    files.router,
    prefix="/files",
    tags=["files"]
)

# Automatic endpoint monitoring
api_router.include_router(
    monitoring.router,
    prefix="/monitoring",
    tags=["monitoring"]
)

# Admin endpoints for database management
api_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["admin"]
)

# Migration endpoints for schema updates
api_router.include_router(
    migration.router,
    prefix="/migration",
    tags=["migration"]
) 