"""
Office Management Schemas
Pydantic models for office management (merged from Location model)
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, validator, Field
from enum import Enum
import uuid

# Enums for validation
class InfrastructureTypeEnum(str, Enum):
    """Infrastructure types"""
    FIXED_DLTC = "10"
    MOBILE_DLTC = "11"
    PRINTING_CENTER = "12"
    COMBINED_CENTER = "13"
    ADMIN_OFFICE = "14"
    REGISTERING_AUTHORITY = "20"
    PROVINCIAL_OFFICE = "30"
    NATIONAL_OFFICE = "31"
    VEHICLE_TESTING = "40"
    HELP_DESK = "50"

class OperationalStatusEnum(str, Enum):
    """Operational status"""
    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"
    SUSPENDED = "suspended"
    SETUP = "setup"
    DECOMMISSIONED = "decommissioned"
    INSPECTION = "inspection"

class OfficeScopeEnum(str, Enum):
    """Geographic scope"""
    NATIONAL = "national"
    PROVINCIAL = "provincial"
    REGIONAL = "regional"
    LOCAL = "local"

class OfficeTypeEnum(str, Enum):
    """Office types"""
    PRIMARY = "primary"
    BRANCH = "branch"
    SPECIALIZED = "specialized"
    MOBILE = "mobile"
    SUPPORT = "support"

# Office Schemas
class OfficeBase(BaseModel):
    """Base office schema"""
    office_code: str = Field(..., min_length=1, max_length=10, description="Office code")
    office_name: str = Field(..., min_length=1, max_length=100, description="Office name")
    office_type: OfficeTypeEnum = Field(OfficeTypeEnum.BRANCH, description="Office type")
    infrastructure_type: InfrastructureTypeEnum = Field(..., description="Infrastructure type")
    address_line_1: str = Field(..., min_length=1, max_length=100, description="Address line 1")
    address_line_2: Optional[str] = Field(None, max_length=100, description="Address line 2")
    address_line_3: Optional[str] = Field(None, max_length=100, description="Address line 3")
    city: str = Field(..., min_length=1, max_length=50, description="City")
    province_code: str = Field(..., min_length=2, max_length=2, description="Province code")
    postal_code: Optional[str] = Field(None, max_length=10, description="Postal code")
    country_code: str = Field("ZA", min_length=2, max_length=2, description="Country code")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude")
    operational_status: OperationalStatusEnum = Field(OperationalStatusEnum.OPERATIONAL, description="Operational status")
    office_scope: OfficeScopeEnum = Field(OfficeScopeEnum.LOCAL, description="Service scope")
    daily_capacity: int = Field(0, ge=0, description="Daily capacity")
    current_load: int = Field(0, ge=0, description="Current load")
    max_concurrent_operations: int = Field(1, ge=1, description="Max concurrent operations")
    staff_count: int = Field(0, ge=0, description="Staff count")
    contact_person: Optional[str] = Field(None, max_length=100, description="Contact person")
    phone_number: Optional[str] = Field(None, max_length=20, description="Phone number")
    email: Optional[str] = Field(None, max_length=255, description="Email address")
    is_active: bool = Field(True, description="Active status")
    is_public: bool = Field(True, description="Public visibility")
    is_operational: bool = Field(True, description="Operational status")
    requires_appointment: bool = Field(False, description="Requires appointment")

class OfficeCreate(OfficeBase):
    """Office creation schema"""
    region_id: str = Field(..., description="Parent region ID")
    
    @validator('office_code')
    def validate_office_code(cls, v):
        if not v.isalnum():
            raise ValueError('Office code must be alphanumeric')
        return v.upper()
    
    @validator('province_code')
    def validate_province_code(cls, v):
        valid_provinces = ['WC', 'GP', 'KZN', 'EC', 'FS', 'NW', 'NC', 'MP', 'LP', 'NAT']
        if v.upper() not in valid_provinces:
            raise ValueError(f'Invalid province code. Must be one of: {valid_provinces}')
        return v.upper()

class OfficeUpdate(BaseModel):
    """Office update schema"""
    office_name: Optional[str] = Field(None, min_length=1, max_length=100)
    office_type: Optional[OfficeTypeEnum] = None
    infrastructure_type: Optional[InfrastructureTypeEnum] = None
    address_line_1: Optional[str] = Field(None, min_length=1, max_length=100)
    address_line_2: Optional[str] = Field(None, max_length=100)
    address_line_3: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, min_length=1, max_length=50)
    postal_code: Optional[str] = Field(None, max_length=10)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    operational_status: Optional[OperationalStatusEnum] = None
    office_scope: Optional[OfficeScopeEnum] = None
    daily_capacity: Optional[int] = Field(None, ge=0)
    current_load: Optional[int] = Field(None, ge=0)
    max_concurrent_operations: Optional[int] = Field(None, ge=1)
    staff_count: Optional[int] = Field(None, ge=0)
    contact_person: Optional[str] = Field(None, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    is_operational: Optional[bool] = None
    requires_appointment: Optional[bool] = None

class OfficeResponse(BaseModel):
    """Office response schema"""
    id: str
    office_code: str
    office_name: str
    region_id: str
    office_type: str
    infrastructure_type: str
    address_line_1: str
    address_line_2: Optional[str]
    address_line_3: Optional[str]
    city: str
    province_code: str
    postal_code: Optional[str]
    country_code: str
    latitude: Optional[float]
    longitude: Optional[float]
    operational_status: str
    office_scope: str
    daily_capacity: int
    current_load: int
    max_concurrent_operations: int
    staff_count: int
    contact_person: Optional[str]
    phone_number: Optional[str]
    email: Optional[str]
    is_active: bool
    is_public: bool
    is_operational: bool
    requires_appointment: bool
    created_at: datetime
    updated_at: datetime
    full_office_code: str
    is_primary_office: bool
    is_mobile_unit: bool
    available_capacity: int
    capacity_utilization: float
    full_address: str
    is_dltc: bool
    is_printing_facility: bool
    
    @validator('id', 'region_id', pre=True)
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v
    
    @validator('full_office_code', pre=True)
    def compute_full_office_code(cls, v, values):
        if 'region_id' in values and 'office_code' in values:
            return f"{values.get('region_id', '')}-{values.get('office_code', '')}"
        return v or ""
    
    @validator('is_primary_office', pre=True)
    def compute_is_primary_office(cls, v, values):
        return values.get('office_type') == 'primary'
    
    @validator('is_mobile_unit', pre=True)
    def compute_is_mobile_unit(cls, v, values):
        return values.get('office_type') == 'mobile'
    
    @validator('available_capacity', pre=True)
    def compute_available_capacity(cls, v, values):
        daily_capacity = values.get('daily_capacity', 0)
        current_load = values.get('current_load', 0)
        return max(0, daily_capacity - current_load)
    
    @validator('capacity_utilization', pre=True)
    def compute_capacity_utilization(cls, v, values):
        daily_capacity = values.get('daily_capacity', 0)
        current_load = values.get('current_load', 0)
        if daily_capacity > 0:
            return round((current_load / daily_capacity) * 100, 2)
        return 0.0
    
    @validator('full_address', pre=True)
    def compute_full_address(cls, v, values):
        parts = []
        if values.get('address_line_1'):
            parts.append(values['address_line_1'])
        if values.get('address_line_2'):
            parts.append(values['address_line_2'])
        if values.get('address_line_3'):
            parts.append(values['address_line_3'])
        if values.get('city'):
            parts.append(values['city'])
        if values.get('postal_code'):
            parts.append(values['postal_code'])
        return ', '.join(parts)
    
    @validator('is_dltc', pre=True)
    def compute_is_dltc(cls, v, values):
        infrastructure_type = values.get('infrastructure_type', '')
        return infrastructure_type in ['10', '11']  # FIXED_DLTC, MOBILE_DLTC
    
    @validator('is_printing_facility', pre=True)
    def compute_is_printing_facility(cls, v, values):
        infrastructure_type = values.get('infrastructure_type', '')
        return infrastructure_type in ['12', '13']  # PRINTING_CENTER, COMBINED_CENTER
    
    class Config:
        from_attributes = True

class OfficeListFilter(BaseModel):
    """Office list filter schema"""
    province_code: Optional[str] = None
    infrastructure_type: Optional[InfrastructureTypeEnum] = None
    office_type: Optional[OfficeTypeEnum] = None
    operational_status: Optional[OperationalStatusEnum] = None
    region_id: Optional[str] = None
    is_active: Optional[bool] = None
    search: Optional[str] = None

class OfficeStatistics(BaseModel):
    """Office statistics schema"""
    total_offices: int
    operational_offices: int
    capacity_utilization_avg: float
    total_daily_capacity: int
    offices_by_type: Dict[str, int]
    offices_by_province: Dict[str, int]
    offices_by_infrastructure: Dict[str, int] 