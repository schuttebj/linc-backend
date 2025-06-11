"""
Lookup endpoints for dropdowns and reference data
Provides country-specific lookup data for forms
"""

from typing import Dict, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.country_config import country_config_manager

router = APIRouter()


class ProvinceResponse(BaseModel):
    """Schema for province lookup response"""
    code: str
    name: str


class PhoneCodeResponse(BaseModel):
    """Schema for phone code lookup response"""
    default_country_code: str
    international_codes: Dict[str, str]  # Code -> Display name
    format_pattern: str


class LanguageResponse(BaseModel):
    """Schema for language lookup response"""
    code: str
    name: str


class LookupResponse(BaseModel):
    """Schema for combined lookup response"""
    provinces: List[ProvinceResponse]
    phone_codes: PhoneCodeResponse
    languages: List[str]
    id_types: List[str]
    license_types: List[str]


@router.get("/provinces", response_model=List[ProvinceResponse])
async def get_provinces():
    """
    Get list of provinces for current country
    Returns province codes and names for dropdown
    """
    try:
        provinces = country_config_manager.get_provinces()
        return [
            ProvinceResponse(code=code, name=name)
            for code, name in provinces.items()
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching provinces: {str(e)}")


@router.get("/phone-codes", response_model=PhoneCodeResponse)
async def get_phone_codes():
    """
    Get international phone codes for dropdown
    Returns default country code and international codes list
    """
    try:
        default_country_code = country_config_manager.get_phone_country_code()
        international_codes = country_config_manager.get_international_phone_codes()
        format_pattern = country_config_manager.config.phone_format_pattern or ""
        
        return PhoneCodeResponse(
            default_country_code=default_country_code,
            international_codes=international_codes,
            format_pattern=format_pattern
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching phone codes: {str(e)}")


@router.get("/languages", response_model=List[str])
async def get_languages():
    """
    Get list of supported languages for current country
    """
    try:
        return country_config_manager.get_supported_languages()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching languages: {str(e)}")


@router.get("/id-types", response_model=List[str])
async def get_id_types():
    """
    Get list of supported ID document types for current country
    """
    try:
        return country_config_manager.get_supported_id_types()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching ID types: {str(e)}")


@router.get("/license-types", response_model=List[str])
async def get_license_types():
    """
    Get list of supported license types for current country
    """
    try:
        return country_config_manager.get_supported_license_types()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching license types: {str(e)}")


@router.get("/all", response_model=LookupResponse)
async def get_all_lookups():
    """
    Get all lookup data in a single response
    Useful for initializing forms
    """
    try:
        provinces = country_config_manager.get_provinces()
        default_country_code = country_config_manager.get_phone_country_code()
        international_codes = country_config_manager.get_international_phone_codes()
        format_pattern = country_config_manager.config.phone_format_pattern or ""
        
        return LookupResponse(
            provinces=[
                ProvinceResponse(code=code, name=name)
                for code, name in provinces.items()
            ],
            phone_codes=PhoneCodeResponse(
                default_country_code=default_country_code,
                international_codes=international_codes,
                format_pattern=format_pattern
            ),
            languages=country_config_manager.get_supported_languages(),
            id_types=country_config_manager.get_supported_id_types(),
            license_types=country_config_manager.get_supported_license_types()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching lookup data: {str(e)}")


@router.post("/validate-phone")
async def validate_phone_number(country_code: str, phone_number: str):
    """
    Validate international phone number format
    """
    try:
        is_valid = country_config_manager.validate_international_phone(country_code, phone_number)
        formatted = country_config_manager.format_phone_number(country_code, phone_number) if is_valid else ""
        
        return {
            "is_valid": is_valid,
            "formatted": formatted,
            "country_code": country_code,
            "phone_number": phone_number
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error validating phone number: {str(e)}")


@router.post("/validate-province")
async def validate_province_code(province_code: str):
    """
    Validate province code for current country
    """
    try:
        is_valid = country_config_manager.validate_province_code(province_code)
        provinces = country_config_manager.get_provinces()
        province_name = provinces.get(province_code, "")
        
        return {
            "is_valid": is_valid,
            "province_code": province_code,
            "province_name": province_name
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error validating province code: {str(e)}") 