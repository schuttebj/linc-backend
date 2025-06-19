"""
Office Management Schemas
Pydantic models for office management (merged from Location model)
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
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

class AssignmentTypeEnum(str, Enum):
    """Assignment types"""
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    TEMPORARY = "TEMPORARY"
    BACKUP = "BACKUP"
    TRAINING = "TRAINING"
    SUPERVISION = "SUPERVISION"
    MAINTENANCE = "MAINTENANCE"

class AssignmentStatusEnum(str, Enum):
    """Assignment status"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    PENDING = "PENDING"
    EXPIRED = "EXPIRED"

# Address Schema (for nested address support)
class AddressBase(BaseModel):
    """Address schema for nested address support"""
    address_line_1: str = Field(..., min_length=1, max_length=100, description="Address line 1")
    address_line_2: Optional[str] = Field(None, max_length=100, description="Address line 2")
    address_line_3: Optional[str] = Field(None, max_length=100, description="Address line 3")
    city: str = Field(..., min_length=1, max_length=50, description="City")
    province_code: str = Field(..., min_length=2, max_length=2, description="Province code")
    postal_code: Optional[str] = Field(None, max_length=10, description="Postal code")
    country_code: str = Field("ZA", min_length=2, max_length=2, description="Country code")

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
    
    @field_validator('office_code')
    @classmethod
    def validate_office_code(cls, v):
        if not v.isalnum():
            raise ValueError('Office code must be alphanumeric')
        return v.upper()
    
    @field_validator('province_code')
    @classmethod
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
    full_office_code: str = ""
    is_primary_office: bool = False
    is_mobile_unit: bool = False
    available_capacity: int = 0
    capacity_utilization: float = 0.0
    full_address: str = ""
    is_dltc: bool = False
    is_printing_facility: bool = False
    
    @field_validator('id', 'region_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v
    
    # Removed complex computed field validators to fix callable schema error
    # These will be computed in the service layer instead
    
    class Config:
        from_attributes = True

class OfficeCreateNested(BaseModel):
    """Office creation schema with nested address support (matches frontend field names)"""
    office_code: str = Field(..., min_length=1, max_length=10, description="Office code")
    office_name: str = Field(..., min_length=1, max_length=100, description="Office name")
    region_id: str = Field(..., description="Parent region ID")
    office_type: OfficeTypeEnum = Field(OfficeTypeEnum.BRANCH, description="Office type")
    infrastructure_type: InfrastructureTypeEnum = Field(..., description="Infrastructure type")
    
    # Nested address object
    address: AddressBase = Field(..., description="Address information")
    
    # Geographic coordinates
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude")
    
    # Operational configuration
    operational_status: OperationalStatusEnum = Field(OperationalStatusEnum.OPERATIONAL, description="Operational status")
    office_scope: OfficeScopeEnum = Field(OfficeScopeEnum.LOCAL, description="Service scope")
    
    # Contact information (using frontend field names)
    contact_person: Optional[str] = Field(None, max_length=100, description="Contact person")
    phone_number: Optional[str] = Field(None, max_length=20, description="Phone number")
    email_address: Optional[str] = Field(None, max_length=255, description="Email address")  # Frontend uses email_address
    
    # Capacity fields (using frontend field names)
    max_users: Optional[int] = Field(None, ge=0, description="Maximum users")  # Frontend uses max_users
    max_daily_capacity: Optional[int] = Field(None, ge=0, description="Maximum daily capacity")  # Frontend uses max_daily_capacity
    
    # Optional fields that may come from frontend
    current_load: Optional[int] = Field(0, ge=0, description="Current load")
    max_concurrent_operations: Optional[int] = Field(1, ge=1, description="Max concurrent operations")
    staff_count: Optional[int] = Field(0, ge=0, description="Staff count")
    
    # Status flags
    is_active: Optional[bool] = Field(True, description="Active status")
    is_public: Optional[bool] = Field(True, description="Public visibility")
    is_operational: Optional[bool] = Field(True, description="Operational status")
    requires_appointment: Optional[bool] = Field(False, description="Requires appointment")
    
    def to_flat_office_create(self):
        """Convert nested address structure to flat structure for database storage"""
        # Map frontend field names to backend field names
        daily_capacity = 0
        if self.max_daily_capacity is not None:
            daily_capacity = self.max_daily_capacity
        elif self.max_users is not None:
            daily_capacity = self.max_users
        
        flat_data = {
            "office_code": self.office_code,
            "office_name": self.office_name,
            "office_type": self.office_type,
            "infrastructure_type": self.infrastructure_type,
            "address_line_1": self.address.address_line_1,
            "address_line_2": self.address.address_line_2,
            "address_line_3": self.address.address_line_3,
            "city": self.address.city,
            "province_code": self.address.province_code,
            "postal_code": self.address.postal_code,
            "country_code": self.address.country_code,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "operational_status": self.operational_status,
            "office_scope": self.office_scope,
            "daily_capacity": daily_capacity,  # Map from max_daily_capacity or max_users
            "current_load": self.current_load or 0,
            "max_concurrent_operations": self.max_concurrent_operations or 1,
            "staff_count": self.staff_count or 0,
            "contact_person": self.contact_person,
            "phone_number": self.phone_number,
            "email": self.email_address,  # Map email_address -> email
            "is_active": self.is_active if self.is_active is not None else True,
            "is_public": self.is_public if self.is_public is not None else True,
            "is_operational": self.is_operational if self.is_operational is not None else True,
            "requires_appointment": self.requires_appointment if self.requires_appointment is not None else False,
        }
        return flat_data

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

# User Office Assignment Schemas
class UserOfficeAssignmentBase(BaseModel):
    """Base user office assignment schema"""
    assignment_type: AssignmentTypeEnum = Field(AssignmentTypeEnum.SECONDARY, description="Assignment type")
    assignment_status: AssignmentStatusEnum = Field(AssignmentStatusEnum.ACTIVE, description="Assignment status")
    effective_date: datetime = Field(..., description="Effective date")
    expiry_date: Optional[datetime] = Field(None, description="Expiry date")
    access_level: str = Field("standard", max_length=20, description="Access level")
    can_manage_office: bool = Field(False, description="Can manage office")
    can_assign_others: bool = Field(False, description="Can assign others")
    can_view_reports: bool = Field(True, description="Can view reports")
    can_manage_resources: bool = Field(False, description="Can manage resources")
    work_schedule: Optional[str] = Field(None, description="Work schedule")
    responsibilities: Optional[str] = Field(None, description="Responsibilities")
    assignment_reason: Optional[str] = Field(None, description="Assignment reason")
    notes: Optional[str] = Field(None, description="Notes")
    is_active: bool = Field(True, description="Active status")

class UserOfficeAssignmentCreate(UserOfficeAssignmentBase):
    """User office assignment creation schema"""
    user_id: str = Field(..., description="User ID - Must be existing user")
    office_id: Optional[str] = Field(None, description="Office ID - Will be set from URL parameter")
    
    # Optional user creation data for new users (if user_id is "new")
    create_new_user: Optional[bool] = Field(False, description="Create new user if user_id is 'new'")
    new_user_data: Optional[Dict[str, Any]] = Field(None, description="New user data if creating user")

class UserOfficeAssignmentUpdate(BaseModel):
    """User office assignment update schema"""
    assignment_type: Optional[AssignmentTypeEnum] = None
    assignment_status: Optional[AssignmentStatusEnum] = None
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    access_level: Optional[str] = Field(None, max_length=20)
    can_manage_office: Optional[bool] = None
    can_assign_others: Optional[bool] = None
    can_view_reports: Optional[bool] = None
    can_manage_resources: Optional[bool] = None
    work_schedule: Optional[str] = None
    responsibilities: Optional[str] = None
    assignment_reason: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

class UserOfficeAssignmentResponse(BaseModel):
    """User office assignment response schema"""
    id: str
    user_id: str
    office_id: str
    assignment_type: str
    assignment_status: str
    effective_date: datetime
    expiry_date: Optional[datetime]
    access_level: str
    can_manage_office: bool
    can_assign_others: bool
    can_view_reports: bool
    can_manage_resources: bool
    work_schedule: Optional[str]
    responsibilities: Optional[str]
    assigned_by: Optional[str]
    assignment_reason: Optional[str]
    notes: Optional[str]
    last_activity_date: Optional[datetime]
    total_hours_worked: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    is_valid_assignment: bool = True
    is_primary_assignment: bool = False
    is_temporary_assignment: bool = False
    days_until_expiry: int = 0
    assignment_duration_days: int = 0
    
    @field_validator('id', 'user_id', 'office_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v
    
    class Config:
        from_attributes = True 