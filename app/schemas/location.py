"""
Location Management Schemas
Pydantic models for location, user group, office, and resource management
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, validator, Field
from enum import Enum
import uuid

# Enums for validation
class UserGroupTypeEnum(str, Enum):
    """User group authority types"""
    FIXED_DLTC = "10"
    MOBILE_DLTC = "11"
    PRINTING_CENTER = "12"
    REGISTERING_AUTHORITY = "20"
    PROVINCIAL_HELP_DESK = "30"
    NATIONAL_HELP_DESK = "31"
    VEHICLE_TESTING_STATION = "40"
    ADMIN_OFFICE = "50"

class RegistrationStatusEnum(str, Enum):
    """Registration status"""
    PENDING_REGISTRATION = "1"
    REGISTERED = "2"
    SUSPENDED = "3"
    PENDING_RENEWAL = "4"
    CANCELLED = "5"
    PENDING_INSPECTION = "6"
    INSPECTION_FAILED = "7"
    DEREGISTERED = "8"

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

class LocationScopeEnum(str, Enum):
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

class ResourceTypeEnum(str, Enum):
    """Resource types"""
    PRINTER = "printer"
    TESTING_EQUIPMENT = "testing"
    COMPUTER = "computer"
    SCANNER = "scanner"
    CAMERA = "camera"
    VEHICLE = "vehicle"
    FURNITURE = "furniture"
    SECURITY = "security"
    NETWORK = "network"
    OTHER = "other"

class ResourceStatusEnum(str, Enum):
    """Resource status"""
    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"
    REPAIR = "repair"
    DECOMMISSIONED = "decommissioned"
    RESERVED = "reserved"
    CALIBRATION = "calibration"

class AssignmentTypeEnum(str, Enum):
    """Assignment types"""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    TEMPORARY = "temporary"
    BACKUP = "backup"
    TRAINING = "training"
    SUPERVISION = "supervision"
    MAINTENANCE = "maintenance"

class AssignmentStatusEnum(str, Enum):
    """Assignment status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"
    EXPIRED = "expired"

# UserGroup Schemas
class UserGroupBase(BaseModel):
    """Base user group schema"""
    user_group_code: str = Field(..., min_length=4, max_length=4, description="4-character authority code")
    user_group_name: str = Field(..., min_length=1, max_length=100, description="Authority name")
    user_group_type: UserGroupTypeEnum = Field(..., description="Authority type")
    province_code: str = Field(..., min_length=2, max_length=2, description="Province code")
    parent_group_id: Optional[str] = Field(None, description="Parent authority ID")
    is_provincial_help_desk: bool = Field(False, description="Provincial Help Desk flag")
    is_national_help_desk: bool = Field(False, description="National Help Desk flag")
    registration_status: RegistrationStatusEnum = Field(RegistrationStatusEnum.REGISTERED, description="Registration status")
    suspended_until: Optional[datetime] = Field(None, description="Suspension end date")
    contact_person: Optional[str] = Field(None, max_length=100, description="Contact person")
    phone_number: Optional[str] = Field(None, max_length=20, description="Phone number")
    email: Optional[str] = Field(None, max_length=255, description="Email address")
    operational_notes: Optional[str] = Field(None, description="Operational notes")
    service_area_description: Optional[str] = Field(None, description="Service area description")
    is_active: bool = Field(True, description="Active status")

class UserGroupCreate(UserGroupBase):
    """User group creation schema"""
    
    @validator('user_group_code')
    def validate_user_group_code(cls, v):
        if not v.isalnum():
            raise ValueError('User group code must be alphanumeric')
        return v.upper()
    
    @validator('province_code')
    def validate_province_code(cls, v):
        valid_provinces = ['WC', 'GP', 'KZN', 'EC', 'FS', 'NW', 'NC', 'MP', 'LP', 'NAT']
        if v.upper() not in valid_provinces:
            raise ValueError(f'Invalid province code. Must be one of: {valid_provinces}')
        return v.upper()

class UserGroupUpdate(BaseModel):
    """User group update schema"""
    user_group_name: Optional[str] = Field(None, min_length=1, max_length=100)
    contact_person: Optional[str] = Field(None, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    operational_notes: Optional[str] = None
    service_area_description: Optional[str] = None
    registration_status: Optional[RegistrationStatusEnum] = None
    suspended_until: Optional[datetime] = None
    is_active: Optional[bool] = None

class UserGroupResponse(BaseModel):
    """User group response schema"""
    id: str
    user_group_code: str
    user_group_name: str
    user_group_type: str
    province_code: str
    parent_group_id: Optional[str]
    is_provincial_help_desk: bool
    is_national_help_desk: bool
    registration_status: str
    suspended_until: Optional[datetime]
    contact_person: Optional[str]
    phone_number: Optional[str]
    email: Optional[str]
    operational_notes: Optional[str]
    service_area_description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    authority_level: str
    is_dltc: bool
    can_access_all_provinces: bool
    
    @validator('id', pre=True)
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v
    
    class Config:
        from_attributes = True

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
    office_code: str = Field(..., min_length=1, max_length=1, description="Single letter office code")
    office_name: str = Field(..., min_length=1, max_length=100, description="Office name")
    office_type: OfficeTypeEnum = Field(OfficeTypeEnum.BRANCH, description="Office type")
    description: Optional[str] = Field(None, description="Office description")
    contact_person: Optional[str] = Field(None, max_length=100, description="Contact person")
    phone_number: Optional[str] = Field(None, max_length=20, description="Phone number")
    email: Optional[str] = Field(None, max_length=255, description="Email address")
    daily_capacity: int = Field(0, ge=0, description="Daily capacity")
    staff_count: int = Field(0, ge=0, description="Staff count")
    is_active: bool = Field(True, description="Active status")
    is_operational: bool = Field(True, description="Operational status")
    operating_hours: Optional[Dict[str, Any]] = Field(None, description="Operating hours")
    service_types: Optional[List[str]] = Field(None, description="Service types")

class OfficeCreate(OfficeBase):
    """Office creation schema"""
    user_group_id: str = Field(..., description="Parent user group ID")
    
    @validator('office_code')
    def validate_office_code(cls, v):
        if not v.isalpha() or not v.isupper():
            raise ValueError('Office code must be a single uppercase letter')
        return v

class OfficeUpdate(BaseModel):
    """Office update schema"""
    office_name: Optional[str] = Field(None, min_length=1, max_length=100)
    office_type: Optional[OfficeTypeEnum] = None
    description: Optional[str] = None
    contact_person: Optional[str] = Field(None, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    daily_capacity: Optional[int] = Field(None, ge=0)
    staff_count: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    is_operational: Optional[bool] = None
    operating_hours: Optional[Dict[str, Any]] = None
    service_types: Optional[List[str]] = None

class OfficeResponse(BaseModel):
    """Office response schema"""
    id: str
    office_code: str
    office_name: str
    user_group_id: str
    office_type: str
    description: Optional[str]
    contact_person: Optional[str]
    phone_number: Optional[str]
    email: Optional[str]
    daily_capacity: int
    staff_count: int
    is_active: bool
    is_operational: bool
    operating_hours: Optional[Dict[str, Any]]
    service_types: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    full_office_code: str
    is_primary_office: bool
    is_mobile_unit: bool
    
    @validator('id', 'user_group_id', pre=True)
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v
    
    class Config:
        from_attributes = True

# Location Schemas
class LocationBase(BaseModel):
    """Base location schema"""
    location_code: str = Field(..., min_length=1, max_length=20, description="Location identifier")
    location_name: str = Field(..., min_length=1, max_length=200, description="Location name")
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
    location_scope: LocationScopeEnum = Field(LocationScopeEnum.LOCAL, description="Service scope")
    daily_capacity: int = Field(0, ge=0, description="Daily capacity")
    current_load: int = Field(0, ge=0, description="Current load")
    max_concurrent_operations: int = Field(1, ge=1, description="Max concurrent operations")
    services_offered: Optional[List[str]] = Field(None, description="Services offered")
    operating_hours: Optional[Dict[str, Any]] = Field(None, description="Operating hours")
    special_hours: Optional[Dict[str, Any]] = Field(None, description="Special hours")
    contact_person: Optional[str] = Field(None, max_length=100, description="Contact person")
    phone_number: Optional[str] = Field(None, max_length=20, description="Phone number")
    fax_number: Optional[str] = Field(None, max_length=20, description="Fax number")
    email: Optional[str] = Field(None, max_length=255, description="Email address")
    facility_description: Optional[str] = Field(None, description="Facility description")
    accessibility_features: Optional[List[str]] = Field(None, description="Accessibility features")
    parking_availability: Optional[bool] = Field(None, description="Parking available")
    public_transport_access: Optional[str] = Field(None, description="Public transport access")
    operational_notes: Optional[str] = Field(None, description="Operational notes")
    public_instructions: Optional[str] = Field(None, description="Public instructions")
    is_active: bool = Field(True, description="Active status")
    is_public: bool = Field(True, description="Public visibility")
    requires_appointment: bool = Field(False, description="Requires appointment")

class LocationCreateNested(BaseModel):
    """Location creation schema with nested address support (matches frontend field names)"""
    location_code: str = Field(..., min_length=1, max_length=20, description="Location identifier")
    location_name: str = Field(..., min_length=1, max_length=200, description="Location name")
    user_group_id: str = Field(..., description="Parent user group ID")
    office_id: Optional[str] = Field(None, description="Parent office ID")
    infrastructure_type: InfrastructureTypeEnum = Field(..., description="Infrastructure type")
    
    # Nested address object
    address: AddressBase = Field(..., description="Address information")
    
    # Geographic coordinates
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude")
    
    # Operational configuration
    operational_status: OperationalStatusEnum = Field(OperationalStatusEnum.OPERATIONAL, description="Operational status")
    location_scope: LocationScopeEnum = Field(LocationScopeEnum.LOCAL, description="Service scope")
    
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
    services_offered: Optional[List[str]] = Field(None, description="Services offered")
    operating_hours: Optional[Dict[str, Any]] = Field(None, description="Operating hours")
    special_hours: Optional[Dict[str, Any]] = Field(None, description="Special hours")
    fax_number: Optional[str] = Field(None, max_length=20, description="Fax number")
    facility_description: Optional[str] = Field(None, description="Facility description")
    accessibility_features: Optional[List[str]] = Field(None, description="Accessibility features")
    parking_availability: Optional[bool] = Field(None, description="Parking available")
    public_transport_access: Optional[str] = Field(None, description="Public transport access")
    operational_notes: Optional[str] = Field(None, description="Operational notes")
    public_instructions: Optional[str] = Field(None, description="Public instructions")
    
    # Status flags
    is_active: Optional[bool] = Field(True, description="Active status")
    is_public: Optional[bool] = Field(True, description="Public visibility")
    requires_appointment: Optional[bool] = Field(False, description="Requires appointment")
    
    def to_flat_location_create(self) -> 'LocationBase':
        """Convert nested address structure to flat structure for database storage"""
        # Map frontend field names to backend field names
        daily_capacity = 0
        if self.max_daily_capacity is not None:
            daily_capacity = self.max_daily_capacity
        elif self.max_users is not None:
            daily_capacity = self.max_users
        
        flat_data = {
            "location_code": self.location_code,
            "location_name": self.location_name,
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
            "location_scope": self.location_scope,
            "daily_capacity": daily_capacity,  # Map from max_daily_capacity or max_users
            "current_load": self.current_load or 0,
            "max_concurrent_operations": self.max_concurrent_operations or 1,
            "services_offered": self.services_offered,
            "operating_hours": self.operating_hours,
            "special_hours": self.special_hours,
            "contact_person": self.contact_person,
            "phone_number": self.phone_number,
            "fax_number": self.fax_number,
            "email": self.email_address,  # Map email_address -> email
            "facility_description": self.facility_description,
            "accessibility_features": self.accessibility_features,
            "parking_availability": self.parking_availability,
            "public_transport_access": self.public_transport_access,
            "operational_notes": self.operational_notes,
            "public_instructions": self.public_instructions,
            "is_active": self.is_active if self.is_active is not None else True,
            "is_public": self.is_public if self.is_public is not None else True,
            "requires_appointment": self.requires_appointment if self.requires_appointment is not None else False,
        }
        return LocationBase(**flat_data)

class LocationCreate(LocationBase):
    """Location creation schema (flat structure for backward compatibility)"""
    user_group_id: str = Field(..., description="Parent user group ID")
    office_id: Optional[str] = Field(None, description="Parent office ID")

class LocationUpdate(BaseModel):
    """Location update schema"""
    location_name: Optional[str] = Field(None, min_length=1, max_length=200)
    address_line_1: Optional[str] = Field(None, min_length=1, max_length=100)
    address_line_2: Optional[str] = Field(None, max_length=100)
    address_line_3: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, min_length=1, max_length=50)
    postal_code: Optional[str] = Field(None, max_length=10)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    operational_status: Optional[OperationalStatusEnum] = None
    location_scope: Optional[LocationScopeEnum] = None
    daily_capacity: Optional[int] = Field(None, ge=0)
    current_load: Optional[int] = Field(None, ge=0)
    max_concurrent_operations: Optional[int] = Field(None, ge=1)
    services_offered: Optional[List[str]] = None
    operating_hours: Optional[Dict[str, Any]] = None
    special_hours: Optional[Dict[str, Any]] = None
    contact_person: Optional[str] = Field(None, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    fax_number: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    facility_description: Optional[str] = None
    accessibility_features: Optional[List[str]] = None
    parking_availability: Optional[bool] = None
    public_transport_access: Optional[str] = None
    operational_notes: Optional[str] = None
    public_instructions: Optional[str] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    requires_appointment: Optional[bool] = None

class LocationResponse(BaseModel):
    """Location response schema"""
    id: str
    location_code: str
    location_name: str
    user_group_id: str
    office_id: Optional[str]
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
    location_scope: str
    daily_capacity: int
    current_load: int
    max_concurrent_operations: int
    services_offered: Optional[List[str]]
    operating_hours: Optional[Dict[str, Any]]
    special_hours: Optional[Dict[str, Any]]
    contact_person: Optional[str]
    phone_number: Optional[str]
    fax_number: Optional[str]
    email: Optional[str]
    facility_description: Optional[str]
    accessibility_features: Optional[List[str]]
    parking_availability: Optional[bool]
    public_transport_access: Optional[str]
    operational_notes: Optional[str]
    public_instructions: Optional[str]
    is_active: bool
    is_public: bool
    requires_appointment: bool
    created_at: datetime
    updated_at: datetime
    full_address: str
    is_dltc: bool
    is_printing_facility: bool
    available_capacity: int
    capacity_utilization: float
    is_operational: bool
    
    @validator('id', 'user_group_id', 'office_id', pre=True)
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v
    
    class Config:
        from_attributes = True

# Resource Schemas
class LocationResourceBase(BaseModel):
    """Base location resource schema"""
    resource_code: str = Field(..., min_length=1, max_length=50, description="Resource identifier")
    resource_name: str = Field(..., min_length=1, max_length=100, description="Resource name")
    resource_type: ResourceTypeEnum = Field(..., description="Resource type")
    subtype: Optional[str] = Field(None, max_length=50, description="Resource subtype")
    manufacturer: Optional[str] = Field(None, max_length=100, description="Manufacturer")
    part_number: Optional[str] = Field(None, max_length=100, description="Model/part number")
    serial_number: Optional[str] = Field(None, max_length=100, description="Serial number")
    specifications: Optional[str] = Field(None, description="Specifications")
    resource_status: ResourceStatusEnum = Field(ResourceStatusEnum.OPERATIONAL, description="Resource status")
    is_available: bool = Field(True, description="Available for use")
    is_shared: bool = Field(False, description="Shared resource")
    capacity_units: Optional[str] = Field(None, max_length=50, description="Capacity units")
    max_capacity_per_hour: int = Field(0, ge=0, description="Max capacity per hour")
    max_capacity_per_day: int = Field(0, ge=0, description="Max capacity per day")
    current_utilization: float = Field(0.0, ge=0, le=100, description="Current utilization %")
    acquisition_date: Optional[datetime] = Field(None, description="Acquisition date")
    warranty_expiry: Optional[datetime] = Field(None, description="Warranty expiry")
    next_maintenance: Optional[datetime] = Field(None, description="Next maintenance")
    replacement_due: Optional[datetime] = Field(None, description="Replacement due")
    acquisition_cost: Optional[float] = Field(None, ge=0, description="Acquisition cost")
    current_value: Optional[float] = Field(None, ge=0, description="Current value")
    annual_maintenance_cost: Optional[float] = Field(None, ge=0, description="Annual maintenance cost")
    operating_instructions: Optional[str] = Field(None, description="Operating instructions")
    maintenance_notes: Optional[str] = Field(None, description="Maintenance notes")
    safety_requirements: Optional[str] = Field(None, description="Safety requirements")
    room_location: Optional[str] = Field(None, max_length=50, description="Room location")
    asset_tag: Optional[str] = Field(None, max_length=50, description="Asset tag")
    is_active: bool = Field(True, description="Active status")
    requires_certification: bool = Field(False, description="Requires certification")

class LocationResourceCreate(LocationResourceBase):
    """Location resource creation schema"""
    location_id: str = Field(..., description="Parent location ID")

class LocationResourceUpdate(BaseModel):
    """Location resource update schema"""
    resource_name: Optional[str] = Field(None, min_length=1, max_length=100)
    subtype: Optional[str] = Field(None, max_length=50)
    manufacturer: Optional[str] = Field(None, max_length=100)
    part_number: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    specifications: Optional[str] = None
    resource_status: Optional[ResourceStatusEnum] = None
    is_available: Optional[bool] = None
    is_shared: Optional[bool] = None
    capacity_units: Optional[str] = Field(None, max_length=50)
    max_capacity_per_hour: Optional[int] = Field(None, ge=0)
    max_capacity_per_day: Optional[int] = Field(None, ge=0)
    current_utilization: Optional[float] = Field(None, ge=0, le=100)
    acquisition_date: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None
    next_maintenance: Optional[datetime] = None
    replacement_due: Optional[datetime] = None
    acquisition_cost: Optional[float] = Field(None, ge=0)
    current_value: Optional[float] = Field(None, ge=0)
    annual_maintenance_cost: Optional[float] = Field(None, ge=0)
    operating_instructions: Optional[str] = None
    maintenance_notes: Optional[str] = None
    safety_requirements: Optional[str] = None
    room_location: Optional[str] = Field(None, max_length=50)
    asset_tag: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    requires_certification: Optional[bool] = None

class LocationResourceResponse(BaseModel):
    """Location resource response schema"""
    id: str
    resource_code: str
    resource_name: str
    location_id: str
    resource_type: str
    subtype: Optional[str]
    manufacturer: Optional[str]
    part_number: Optional[str]
    serial_number: Optional[str]
    specifications: Optional[str]
    resource_status: str
    is_available: bool
    is_shared: bool
    capacity_units: Optional[str]
    max_capacity_per_hour: int
    max_capacity_per_day: int
    current_utilization: float
    acquisition_date: Optional[datetime]
    warranty_expiry: Optional[datetime]
    next_maintenance: Optional[datetime]
    replacement_due: Optional[datetime]
    acquisition_cost: Optional[float]
    current_value: Optional[float]
    annual_maintenance_cost: Optional[float]
    operating_instructions: Optional[str]
    maintenance_notes: Optional[str]
    safety_requirements: Optional[str]
    room_location: Optional[str]
    asset_tag: Optional[str]
    is_active: bool
    requires_certification: bool
    created_at: datetime
    updated_at: datetime
    is_operational: bool
    needs_maintenance: bool
    is_under_warranty: bool
    available_capacity_per_hour: int
    available_capacity_per_day: int
    
    @validator('id', 'location_id', pre=True)
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v
    
    class Config:
        from_attributes = True

# User Assignment Schemas
class UserLocationAssignmentBase(BaseModel):
    """Base user location assignment schema"""
    assignment_type: AssignmentTypeEnum = Field(AssignmentTypeEnum.SECONDARY, description="Assignment type")
    assignment_status: AssignmentStatusEnum = Field(AssignmentStatusEnum.ACTIVE, description="Assignment status")
    effective_date: datetime = Field(..., description="Effective date")
    expiry_date: Optional[datetime] = Field(None, description="Expiry date")
    access_level: str = Field("standard", max_length=20, description="Access level")
    can_manage_location: bool = Field(False, description="Can manage location")
    can_assign_others: bool = Field(False, description="Can assign others")
    can_view_reports: bool = Field(True, description="Can view reports")
    can_manage_resources: bool = Field(False, description="Can manage resources")
    work_schedule: Optional[str] = Field(None, description="Work schedule")
    responsibilities: Optional[str] = Field(None, description="Responsibilities")
    assignment_reason: Optional[str] = Field(None, description="Assignment reason")
    notes: Optional[str] = Field(None, description="Notes")
    is_active: bool = Field(True, description="Active status")

class UserLocationAssignmentCreate(UserLocationAssignmentBase):
    """User location assignment creation schema"""
    user_id: str = Field(..., description="User ID")
    location_id: str = Field(..., description="Location ID")
    office_id: Optional[str] = Field(None, description="Office ID")

class UserLocationAssignmentUpdate(BaseModel):
    """User location assignment update schema"""
    assignment_type: Optional[AssignmentTypeEnum] = None
    assignment_status: Optional[AssignmentStatusEnum] = None
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    access_level: Optional[str] = Field(None, max_length=20)
    can_manage_location: Optional[bool] = None
    can_assign_others: Optional[bool] = None
    can_view_reports: Optional[bool] = None
    can_manage_resources: Optional[bool] = None
    work_schedule: Optional[str] = None
    responsibilities: Optional[str] = None
    assignment_reason: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

class UserLocationAssignmentResponse(BaseModel):
    """User location assignment response schema"""
    id: str
    user_id: str
    location_id: str
    office_id: Optional[str]
    assignment_type: str
    assignment_status: str
    effective_date: datetime
    expiry_date: Optional[datetime]
    access_level: str
    can_manage_location: bool
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
    is_valid_assignment: bool
    is_primary_assignment: bool
    is_temporary_assignment: bool
    days_until_expiry: int
    assignment_duration_days: int
    
    @validator('id', 'user_id', 'location_id', 'office_id', pre=True)
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v
    
    class Config:
        from_attributes = True

# List and Filter Schemas
class UserGroupListFilter(BaseModel):
    """User group list filter schema"""
    province_code: Optional[str] = None
    user_group_type: Optional[UserGroupTypeEnum] = None
    registration_status: Optional[RegistrationStatusEnum] = None
    is_active: Optional[bool] = None
    search: Optional[str] = None

class LocationListFilter(BaseModel):
    """Location list filter schema"""
    province_code: Optional[str] = None
    infrastructure_type: Optional[InfrastructureTypeEnum] = None
    operational_status: Optional[OperationalStatusEnum] = None
    location_scope: Optional[LocationScopeEnum] = None
    user_group_id: Optional[str] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    search: Optional[str] = None

class LocationResourceListFilter(BaseModel):
    """Location resource list filter schema"""
    location_id: Optional[str] = None
    resource_type: Optional[ResourceTypeEnum] = None
    resource_status: Optional[ResourceStatusEnum] = None
    is_available: Optional[bool] = None
    is_active: Optional[bool] = None
    search: Optional[str] = None

class UserLocationAssignmentListFilter(BaseModel):
    """User location assignment list filter schema"""
    user_id: Optional[str] = None
    location_id: Optional[str] = None
    assignment_type: Optional[AssignmentTypeEnum] = None
    assignment_status: Optional[AssignmentStatusEnum] = None
    is_active: Optional[bool] = None

# Summary and Statistics Schemas
class LocationStatistics(BaseModel):
    """Location statistics schema"""
    total_locations: int
    operational_locations: int
    capacity_utilization_avg: float
    total_daily_capacity: int
    locations_by_type: Dict[str, int]
    locations_by_province: Dict[str, int]

class UserGroupStatistics(BaseModel):
    """User group statistics schema"""
    total_user_groups: int
    active_user_groups: int
    user_groups_by_type: Dict[str, int]
    user_groups_by_province: Dict[str, int]

class ResourceStatistics(BaseModel):
    """Resource statistics schema"""
    total_resources: int
    operational_resources: int
    resources_by_type: Dict[str, int]
    resources_needing_maintenance: int
    average_utilization: float 