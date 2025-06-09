"""
Country Configuration Endpoints - Simplified Single Country
Manage country-specific settings, modules, and feature toggles
"""

from fastapi import APIRouter
from typing import Dict, Any
import structlog

from app.core.config import settings, COUNTRY_CONFIGS

router = APIRouter()
logger = structlog.get_logger()


@router.get("/current")
async def get_current_country() -> Dict[str, Any]:
    """Get current country configuration for this deployment"""
    country_config = COUNTRY_CONFIGS.get(settings.COUNTRY_CODE)
    
    if not country_config:
        # Return basic configuration if detailed config not available
        return {
            "country_code": settings.COUNTRY_CODE,
            "country_name": settings.COUNTRY_NAME,
            "currency": settings.CURRENCY,
            "is_active": True,
            "modules": {
                "person_management": True,
                "license_applications": True,
                "card_production": True,
                "financial_management": True,
                "prdp_management": True,
                "infringement_suspension": True,
                "vehicle_management": False,
                "court_integration": False
            }
        }
    
    return {
        "country_code": country_config.country_code,
        "country_name": country_config.country_name,
        "currency": country_config.currency,
        "is_active": True,
        "modules": country_config.modules,
        "license_types": country_config.license_types,
        "id_document_types": country_config.id_document_types,
        "printing_config": country_config.printing_config,
        "compliance": country_config.compliance,
        "age_requirements": country_config.age_requirements,
        "fee_structure": country_config.fee_structure
    }


@router.get("/modules")
async def get_enabled_modules() -> Dict[str, Any]:
    """Get enabled modules for current country"""
    country_config = COUNTRY_CONFIGS.get(settings.COUNTRY_CODE)
    
    if not country_config:
        # Return default modules if no specific config
        default_modules = {
            "person_management": True,
            "license_applications": True,
            "card_production": True,
            "financial_management": True,
            "prdp_management": True,
            "infringement_suspension": True,
            "vehicle_management": False,
            "court_integration": False
        }
        return {
            "country_code": settings.COUNTRY_CODE,
            "modules": default_modules,
            "enabled_modules": [k for k, v in default_modules.items() if v]
        }
    
    enabled_modules = [
        module for module, enabled in country_config.modules.items() 
        if enabled
    ]
    
    return {
        "country_code": settings.COUNTRY_CODE,
        "modules": country_config.modules,
        "enabled_modules": enabled_modules
    }


@router.get("/license-types")
async def get_license_types() -> Dict[str, Any]:
    """Get available license types for current country"""
    country_config = COUNTRY_CONFIGS.get(settings.COUNTRY_CODE)
    
    if not country_config:
        # Return default license types
        return {
            "country_code": settings.COUNTRY_CODE,
            "license_types": ["A", "B", "C", "D", "EB", "EC"],
            "age_requirements": {
                "A": 16, "B": 18, "C": 21, "D": 24, "EB": 18, "EC": 21
            }
        }
    
    return {
        "country_code": settings.COUNTRY_CODE,
        "license_types": country_config.license_types,
        "age_requirements": country_config.age_requirements
    }


@router.get("/printing-config")
async def get_printing_configuration() -> Dict[str, Any]:
    """Get printing configuration for current country"""
    country_config = COUNTRY_CONFIGS.get(settings.COUNTRY_CODE)
    
    if not country_config:
        # Return default printing config
        return {
            "country_code": settings.COUNTRY_CODE,
            "printing_config": {
                "type": "distributed",
                "iso_standards": ["ISO_18013"],
                "locations": []
            }
        }
    
    return {
        "country_code": settings.COUNTRY_CODE,
        "printing_config": country_config.printing_config
    }


@router.get("/fees")
async def get_fee_structure() -> Dict[str, Any]:
    """Get fee structure for current country"""
    country_config = COUNTRY_CONFIGS.get(settings.COUNTRY_CODE)
    
    if not country_config:
        # Return default fee structure
        return {
            "country_code": settings.COUNTRY_CODE,
            "currency": settings.CURRENCY,
            "fee_structure": {
                "learners_license": 50.00,
                "drivers_license": 100.00,
                "license_renewal": 75.00,
                "duplicate_license": 60.00,
                "license_conversion": 80.00,
                "prdp_application": 25.00
            }
        }
    
    return {
        "country_code": settings.COUNTRY_CODE,
        "currency": country_config.currency,
        "fee_structure": country_config.fee_structure
    } 