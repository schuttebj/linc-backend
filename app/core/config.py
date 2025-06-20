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
    # For cross-domain credentials, cannot use wildcard - must specify exact origins
    # Can be overridden with ALLOWED_ORIGINS environment variable
    ALLOWED_ORIGINS: str = "https://linc-frontend-opal.vercel.app,http://localhost:3000,http://localhost:5173"
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
            # Split by comma and clean whitespace
            origins = [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
            # Filter out empty strings
            return [origin for origin in origins if origin]
    
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
    
    # Database Configuration (Single Country)
    # This will be overridden by environment variables in production
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/linc_database"
    
    # Database SSL mode for production
    DB_SSL_MODE: str = "prefer"  # prefer, require, disable
    
    # File Storage Configuration
    FILE_STORAGE_PATH: str = "/var/linc-data"
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_IMAGE_TYPES: str = "image/jpeg,image/png,image/gif,image/bmp,image/tiff"
    ALLOWED_DOCUMENT_TYPES: str = "application/pdf,image/jpeg,image/png"
    
    # Backup Configuration
    BACKUP_RETENTION_DAILY: int = 30  # Keep 30 daily backups
    BACKUP_RETENTION_WEEKLY: int = 12  # Keep 12 weekly backups
    ENABLE_AUTO_BACKUP: bool = True
    
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
    
    # Country Configuration (Single Country per Deployment)
    COUNTRY_CODE: str = "ZA"
    COUNTRY_NAME: str = "South Africa"
    CURRENCY: str = "ZAR"
    
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
    
    def get_file_storage_path(self) -> Path:
        """Get file storage path for this deployment's country"""
        return Path(self.FILE_STORAGE_PATH) / self.COUNTRY_CODE


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


def get_settings() -> Settings:
    """Get application settings instance"""
    return settings 