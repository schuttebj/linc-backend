"""
LINC API v1 Router - Simplified Single-Country Version
Single-country deployment without multi-tenant routing complexity
"""

from fastapi import APIRouter
from app.api.v1.endpoints import persons, countries, health

api_router = APIRouter()

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

# Core business endpoints (no country prefix needed)
api_router.include_router(
    persons.router,
    prefix="/persons",
    tags=["persons"]
) 