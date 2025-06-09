"""
Country Configuration Schemas
Pydantic models for country-specific settings, modules, and configurations
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class CountryBasicInfo(BaseModel):
    """Basic country information"""
    country_code: str = Field(..., description="ISO 2-letter country code")
    country_name: str = Field(..., description="Full country name")
    currency: str = Field(..., description="ISO currency code")
    is_active: bool = Field(True, description="Whether country is active")


class CountryListResponse(BaseModel):
    """Response model for list of supported countries"""
    countries: List[CountryBasicInfo]
    total_count: int
    default_country: str


class CountryConfigResponse(BaseModel):
    """Complete country configuration response"""
    country_code: str
    country_name: str
    currency: str
    modules: Dict[str, bool]
    license_types: List[str]
    id_document_types: List[str]
    printing_config: Dict[str, Any]
    compliance: Dict[str, Any]
    age_requirements: Dict[str, int]
    fee_structure: Dict[str, float]
    
    class Config:
        json_schema_extra = {
            "example": {
                "country_code": "ZA",
                "country_name": "South Africa",
                "currency": "ZAR",
                "modules": {
                    "person_management": True,
                    "license_applications": True,
                    "card_production": True,
                    "financial_management": True,
                    "prdp_management": True,
                    "infringement_suspension": True,
                    "vehicle_management": False,
                    "court_integration": False
                },
                "license_types": ["A", "B", "C", "D", "EB", "EC"],
                "id_document_types": ["RSA_ID", "Passport", "Temporary_ID"],
                "printing_config": {
                    "type": "distributed",
                    "iso_standards": ["ISO_18013"]
                },
                "compliance": {
                    "data_privacy": "POPIA",
                    "audit_retention_years": 7
                },
                "age_requirements": {
                    "A": 16,
                    "B": 18,
                    "C": 21,
                    "D": 24
                },
                "fee_structure": {
                    "learners_license": 100.00,
                    "drivers_license": 250.00,
                    "license_renewal": 200.00
                }
            }
        } 