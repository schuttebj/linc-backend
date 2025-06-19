# LINC Database Models Package 

from .base import BaseModel
from .enums import *
from .person import Person, PersonStatus, PersonType, NationalityType, Gender, PersonAddress, AddressType
from .license import License, LicenseType, LicenseStatus, LicenseCategory, LicenseEndorsement, LicenseRestriction
from .application import Application, ApplicationType, ApplicationStatus
from .user import User, UserAuditLog, UserSession, UserStatus
from .region import Region, RegionType, RegistrationStatus
from .office import Office, OfficeType, InfrastructureType, OperationalStatus, OfficeScope
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
    "PersonStatus",
    "PersonType",
    "NationalityType",
    "Gender",
    "PersonAddress",
    "AddressType",
    "License",
    "LicenseType",
    "LicenseStatus",
    "LicenseCategory",
    "LicenseEndorsement",
    "LicenseRestriction",
    "Application",
    "ApplicationType",
    "ApplicationStatus",
    "User",
    "UserAuditLog",
    "UserSession",
    "UserStatus",
    "UserType",
    "Region",
    "RegionType",
    "RegistrationStatus",
    "Office",
    "OfficeType",
    "InfrastructureType",
    "OperationalStatus",
    "OfficeScope",
    "LocationResource",
    "ResourceType",
    "ResourceStatus",
    "UserLocationAssignment",
    "AssignmentType",
    "AssignmentStatus",
    "Gender",
    "PersonType",
    "PersonStatus",
    "AddressType",
    "UserType",
    "UserType",
    "UserAuditLog",
    "UserStatus",
    "UserType",
    "LicenseType",
    "User",
    "UserType",
    "UserAuditLog",
    "UserStatus",
    "UserRegionAssignment",
    "UserOfficeAssignment",
    "Role",
    "Permission",
] 