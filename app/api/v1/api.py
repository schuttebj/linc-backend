"""
LINC API v1 Router
Main API router with country-specific endpoints and multi-tenant routing
"""

from fastapi import APIRouter
from app.api.v1.endpoints import persons, countries, health

api_router = APIRouter()

# Health and system endpoints (no country context needed)
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

# Country-specific endpoints (require country context)
api_router.include_router(
    persons.router,
    prefix="/{country}/persons",
    tags=["persons"]
) 