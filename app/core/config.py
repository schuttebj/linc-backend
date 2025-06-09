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
    ALLOWED_ORIGINS: str = "*"
    ALLOWED_HOSTS: str = "*"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert ALLOWED_ORIGINS string to list"""
        if self.ALLOWED_ORIGINS == "*":
            return ["*"]
        # Support comma-separated values or JSON array
        try:
            import json
            return json.loads(self.ALLOWED_ORIGINS)
        except:
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    @property
    def allowed_hosts_list(self) -> List[str]:
        """Convert ALLOWED_HOSTS string to list"""
        if self.ALLOWED_HOSTS == "*":
            return ["*"]
        try:
            import json
            return json.loads(self.ALLOWED_HOSTS)
        except:
            return [host.strip() for host in self.ALLOWED_HOSTS.split(",")]
    
    # Database Configuration
    # Default PostgreSQL connection - will be overridden per country
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/linc_default"
    
    # Multi-tenant database URLs (country-specific)
    DATABASE_URL_ZA: str = "postgresql://postgres:password@localhost:5432/linc_south_africa"
    DATABASE_URL_KE: str = "postgresql://postgres:password@localhost:5432/linc_kenya"
    DATABASE_URL_NG: str = "postgresql://postgres:password@localhost:5432/linc_nigeria"
    
    @property
    def COUNTRY_DATABASES(self) -> Dict[str, str]:
        """Get country databases from environment variables"""
        return {
            "ZA": self.DATABASE_URL_ZA,
            "KE": self.DATABASE_URL_KE,
            "NG": self.DATABASE_URL_NG,
        }
    
    # File Storage Configuration
    FILE_STORAGE_BASE_PATH: str = "/var/linc-data"
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_IMAGE_TYPES: str = "image/jpeg,image/png,image/gif"
    ALLOWED_DOCUMENT_TYPES: str = "application/pdf,image/jpeg,image/png"
    
    @property
    def allowed_image_types_list(self) -> List[str]:
        """Convert ALLOWED_IMAGE_TYPES string to list"""
        try:
            import json
            return json.loads(self.ALLOWED_IMAGE_TYPES)
        except:
            return [mime_type.strip() for mime_type in self.ALLOWED_IMAGE_TYPES.split(",")]
    
    @property
    def allowed_document_types_list(self) -> List[str]:
        """Convert ALLOWED_DOCUMENT_TYPES string to list"""
        try:
            import json
            return json.loads(self.ALLOWED_DOCUMENT_TYPES)
        except:
            return [mime_type.strip() for mime_type in self.ALLOWED_DOCUMENT_TYPES.split(",")]
    
    # Audit Configuration
    AUDIT_LOG_RETENTION_DAYS: int = 2555  # 7 years
    ENABLE_FILE_AUDIT_LOGS: bool = True
    ENABLE_PERFORMANCE_MONITORING: bool = True
    
    # Country Configuration
    DEFAULT_COUNTRY_CODE: str = "ZA"
    SUPPORTED_COUNTRIES: str = "ZA,KE,NG"
    
    @property
    def supported_countries_list(self) -> List[str]:
        """Convert SUPPORTED_COUNTRIES string to list"""
        try:
            import json
            return json.loads(self.SUPPORTED_COUNTRIES)
        except:
            return [country.strip() for country in self.SUPPORTED_COUNTRIES.split(",")]
    
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