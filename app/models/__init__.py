# LINC Database Models Package 

from .base import BaseModel
from .enums import *
from .person import Person, PersonAddress, PersonAlias, NaturalPerson
from .license import (
    LicenseApplication, 
    LicenseCard, 
    ApplicationPayment, 
    TestCenter,
    ApplicationStatus,
    LicenseType
)
from .user import (
    User, UserAuditLog, UserStatus, UserSession, UserType
)
from .audit import AuditLog, FileMetadata

# Location Management Models (NEW)
from .region import Region, RegionType, RegistrationStatus
from .office import Office, OfficeType
from .location import Location, InfrastructureType, OperationalStatus, LocationScope, LocationType
from .location_resource import LocationResource, ResourceType, ResourceStatus
from .user_location_assignment import UserLocationAssignment, AssignmentType, AssignmentStatus

# NEW PERMISSION SYSTEM IMPORTS
from .user_type import UserType, UserRegionAssignment, UserOfficeAssignment

# LEGACY MODELS - TEMPORARY FOR MIGRATION
# These will be removed once migration is complete
from .user import Role, Permission  # TEMPORARY - Legacy models for migration

__all__ = [
    "BaseModel",
    "Person", 
    "PersonAddress",
    "PersonAlias",
    "NaturalPerson",
    "LicenseApplication",
    "LicenseCard", 
    "ApplicationPayment",
    "TestCenter",
    "ApplicationStatus",
    "LicenseType",
    "User",
    "UserType",
    "UserAuditLog",
    "UserStatus",
    "UserSession",
    "AuditLog",
    "FileMetadata",
    # Location Management Models
    "Region",
    "RegionType",
    "RegistrationStatus", 
    "Office",
    "OfficeType",
    "Location",
    "InfrastructureType",
    "OperationalStatus",
    "LocationScope",
    "LocationResource",
    "ResourceType",
    "ResourceStatus",
    "UserLocationAssignment",
    "AssignmentType",
    "AssignmentStatus",
    "LocationType",
    # Enums
    "Gender",
    "IdDocumentType", 
    "ValidationStatus",
    "AddressType",
    "PersonType",
    "NationalityType",
    # NEW PERMISSION SYSTEM
    "UserRegionAssignment",
    "UserOfficeAssignment",
    # LEGACY - TEMPORARY
    "Role",
    "Permission",
] 