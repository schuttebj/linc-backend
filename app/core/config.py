"""
LINC Configuration Settings
Multi-tenant, country-configurable settings with environment variable support
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Dict, Any, Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore"
    )
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "LINC Driver's Licensing System"
    VERSION: str = "1.0.0"
    
    # Security Configuration
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",  # React development server
        "http://localhost:3001",
        "https://linc-frontend.vercel.app"  # Production frontend
    ]
    ALLOWED_HOSTS: List[str] = ["*"]  # Restrict in production
    
    # Database Configuration
    # Default PostgreSQL connection - will be overridden per country
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/linc_default"
    
    # Multi-tenant database URLs (country-specific)
    COUNTRY_DATABASES: Dict[str, str] = {
        "ZA": "postgresql://postgres:password@localhost:5432/linc_south_africa",
        "KE": "postgresql://postgres:password@localhost:5432/linc_kenya",
        "NG": "postgresql://postgres:password@localhost:5432/linc_nigeria",
    }
    
    # File Storage Configuration
    FILE_STORAGE_BASE_PATH: str = "/var/linc-data"
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/gif"]
    ALLOWED_DOCUMENT_TYPES: List[str] = ["application/pdf", "image/jpeg", "image/png"]
    
    # Audit Configuration
    AUDIT_LOG_RETENTION_DAYS: int = 2555  # 7 years
    ENABLE_FILE_AUDIT_LOGS: bool = True
    ENABLE_PERFORMANCE_MONITORING: bool = True
    
    # Country Configuration
    DEFAULT_COUNTRY_CODE: str = "ZA"
    SUPPORTED_COUNTRIES: List[str] = ["ZA", "KE", "NG"]
    
    # External Integration Configuration
    ENABLE_MEDICAL_INTEGRATION: bool = False
    ENABLE_POLICE_CLEARANCE_INTEGRATION: bool = False
    
    # Performance Configuration
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_TIMEOUT: int = 30
    
    # Card Production Configuration
    CARD_PRODUCTION_MODE: str = "local"  # "local" or "centralized"
    ISO_18013_COMPLIANCE: bool = True
    
    @property
    def database_url_for_country(self) -> str:
        """Get database URL for default country"""
        return self.COUNTRY_DATABASES.get(self.DEFAULT_COUNTRY_CODE, self.DATABASE_URL)
    
    def get_database_url(self, country_code: str) -> str:
        """Get database URL for specific country"""
        return self.COUNTRY_DATABASES.get(country_code.upper(), self.DATABASE_URL)
    
    def get_file_storage_path(self, country_code: str) -> Path:
        """Get file storage path for specific country"""
        return Path(self.FILE_STORAGE_BASE_PATH) / country_code.upper()


class CountryConfig(BaseSettings):
    """Country-specific configuration template"""
    
    model_config = SettingsConfigDict(extra="allow")
    
    country_code: str
    country_name: str
    currency: str
    
    # Module toggles
    modules: Dict[str, bool] = {
        "person_management": True,
        "license_applications": True,
        "card_production": True,
        "financial_management": True,
        "prdp_management": True,
        "infringement_suspension": True,  # Limited to suspension only
        "vehicle_management": False,
        "court_integration": False,
        "complex_payment_gateways": False
    }
    
    # License types available in this country
    license_types: List[str] = ["A", "B", "C", "D", "EB", "EC"]
    
    # ID document types accepted
    id_document_types: List[str] = ["RSA_ID", "Passport", "Temporary_ID"]
    
    # Printing configuration
    printing_config: Dict[str, Any] = {
        "type": "distributed",  # "centralized" or "distributed"
        "iso_standards": ["ISO_18013"],
        "locations": []
    }
    
    # Compliance requirements
    compliance: Dict[str, Any] = {
        "data_privacy": "POPIA",
        "audit_retention_years": 7,
        "card_standards": ["ISO_18013"]
    }
    
    # Age requirements for license types
    age_requirements: Dict[str, int] = {
        "A": 16,    # Motorcycle
        "B": 18,    # Light vehicle
        "C": 21,    # Heavy vehicle
        "D": 24     # Bus/taxi
    }
    
    # Fee structure (in local currency)
    fee_structure: Dict[str, float] = {
        "learners_license": 100.00,
        "drivers_license": 250.00,
        "license_renewal": 200.00,
        "duplicate_license": 150.00,
        "prdp_application": 500.00
    }


# South Africa default configuration
SOUTH_AFRICA_CONFIG = CountryConfig(
    country_code="ZA",
    country_name="South Africa",
    currency="ZAR",
    id_document_types=["RSA_ID", "Passport", "Temporary_ID", "Asylum_Document"],
    compliance={
        "data_privacy": "POPIA",
        "audit_retention_years": 7,
        "card_standards": ["ISO_18013"]
    }
)

# Kenya configuration template
KENYA_CONFIG = CountryConfig(
    country_code="KE",
    country_name="Kenya",
    currency="KES",
    id_document_types=["National_ID", "Passport", "Birth_Certificate"],
    age_requirements={
        "A": 16,
        "B": 18,
        "C": 21,
        "D": 24
    },
    fee_structure={
        "learners_license": 3000.00,
        "drivers_license": 6000.00,
        "license_renewal": 5000.00,
        "duplicate_license": 4000.00,
        "prdp_application": 12000.00
    }
)

# Country configurations registry
COUNTRY_CONFIGS = {
    "ZA": SOUTH_AFRICA_CONFIG,
    "KE": KENYA_CONFIG,
}


# Create settings instance
settings = Settings() 