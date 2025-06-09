"""
Country Configuration Endpoints
Manage country-specific settings, modules, and feature toggles
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import structlog

from app.core.config import settings, COUNTRY_CONFIGS, CountryConfig
from app.schemas.country import CountryConfigResponse, CountryListResponse

router = APIRouter()
logger = structlog.get_logger()


@router.get("/", response_model=CountryListResponse)
async def get_supported_countries() -> CountryListResponse:
    """Get list of all supported countries"""
    countries = []
    
    for country_code in settings.SUPPORTED_COUNTRIES:
        country_config = COUNTRY_CONFIGS.get(country_code)
        if country_config:
            countries.append({
                "country_code": country_config.country_code,
                "country_name": country_config.country_name,
                "currency": country_config.currency,
                "is_active": True
            })
        else:
            # Country is supported but no detailed config available
            countries.append({
                "country_code": country_code,
                "country_name": f"Country {country_code}",
                "currency": "USD",  # Default
                "is_active": True
            })
    
    return CountryListResponse(
        countries=countries,
        total_count=len(countries),
        default_country=settings.DEFAULT_COUNTRY_CODE
    )


@router.get("/{country_code}", response_model=CountryConfigResponse)
async def get_country_configuration(country_code: str) -> CountryConfigResponse:
    """Get detailed configuration for specific country"""
    country_code = country_code.upper()
    
    if country_code not in settings.SUPPORTED_COUNTRIES:
        raise HTTPException(
            status_code=404,
            detail=f"Country {country_code} is not supported"
        )
    
    country_config = COUNTRY_CONFIGS.get(country_code)
    if not country_config:
        raise HTTPException(
            status_code=404,
            detail=f"Configuration not found for country {country_code}"
        )
    
    return CountryConfigResponse(
        country_code=country_config.country_code,
        country_name=country_config.country_name,
        currency=country_config.currency,
        modules=country_config.modules,
        license_types=country_config.license_types,
        id_document_types=country_config.id_document_types,
        printing_config=country_config.printing_config,
        compliance=country_config.compliance,
        age_requirements=country_config.age_requirements,
        fee_structure=country_config.fee_structure
    )


@router.get("/{country_code}/modules")
async def get_enabled_modules(country_code: str) -> Dict[str, Any]:
    """Get enabled modules for specific country"""
    country_code = country_code.upper()
    
    if country_code not in settings.SUPPORTED_COUNTRIES:
        raise HTTPException(
            status_code=404,
            detail=f"Country {country_code} is not supported"
        )
    
    country_config = COUNTRY_CONFIGS.get(country_code)
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
            "country_code": country_code,
            "modules": default_modules,
            "enabled_modules": [k for k, v in default_modules.items() if v]
        }
    
    enabled_modules = [
        module for module, enabled in country_config.modules.items() 
        if enabled
    ]
    
    return {
        "country_code": country_code,
        "modules": country_config.modules,
        "enabled_modules": enabled_modules
    }


@router.get("/{country_code}/license-types")
async def get_license_types(country_code: str) -> Dict[str, Any]:
    """Get available license types for specific country"""
    country_code = country_code.upper()
    
    if country_code not in settings.SUPPORTED_COUNTRIES:
        raise HTTPException(
            status_code=404,
            detail=f"Country {country_code} is not supported"
        )
    
    country_config = COUNTRY_CONFIGS.get(country_code)
    if not country_config:
        # Return default license types
        return {
            "country_code": country_code,
            "license_types": ["A", "B", "C", "D", "EB", "EC"],
            "age_requirements": {
                "A": 16, "B": 18, "C": 21, "D": 24, "EB": 18, "EC": 21
            }
        }
    
    return {
        "country_code": country_code,
        "license_types": country_config.license_types,
        "age_requirements": country_config.age_requirements
    }


@router.get("/{country_code}/printing-config")
async def get_printing_configuration(country_code: str) -> Dict[str, Any]:
    """Get printing configuration for specific country"""
    country_code = country_code.upper()
    
    if country_code not in settings.SUPPORTED_COUNTRIES:
        raise HTTPException(
            status_code=404,
            detail=f"Country {country_code} is not supported"
        )
    
    country_config = COUNTRY_CONFIGS.get(country_code)
    if not country_config:
        # Return default printing config
        return {
            "country_code": country_code,
            "printing_config": {
                "type": "distributed",
                "iso_standards": ["ISO_18013"],
                "locations": []
            }
        }
    
    return {
        "country_code": country_code,
        "printing_config": country_config.printing_config
    }


@router.get("/{country_code}/fees")
async def get_fee_structure(country_code: str) -> Dict[str, Any]:
    """Get fee structure for specific country"""
    country_code = country_code.upper()
    
    if country_code not in settings.SUPPORTED_COUNTRIES:
        raise HTTPException(
            status_code=404,
            detail=f"Country {country_code} is not supported"
        )
    
    country_config = COUNTRY_CONFIGS.get(country_code)
    if not country_config:
        # Return default fee structure
        return {
            "country_code": country_code,
            "currency": "USD",
            "fee_structure": {
                "learners_license": 50.00,
                "drivers_license": 100.00,
                "license_renewal": 75.00,
                "duplicate_license": 60.00,
                "prdp_application": 200.00
            }
        }
    
    return {
        "country_code": country_code,
        "currency": country_config.currency,
        "fee_structure": country_config.fee_structure
    } 