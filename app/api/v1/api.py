"""
LINC API v1 Router
Single-country deployment with simplified routing
"""

from fastapi import APIRouter
from app.api.v1.endpoints import persons, countries, health, licenses

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