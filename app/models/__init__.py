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
from .user import User, Role, Permission, UserAuditLog, UserStatus
from .user_profile import UserProfile, UserSession
from .audit import AuditLog, FileMetadata

# Location Management Models (NEW)
from .user_group import UserGroup, UserGroupType, RegistrationStatus
from .office import Office, OfficeType
from .location import Location, InfrastructureType, OperationalStatus, LocationScope
from .location_resource import LocationResource, ResourceType, ResourceStatus
from .user_location_assignment import UserLocationAssignment, AssignmentType, AssignmentStatus

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
    "Role",
    "Permission", 
    "UserAuditLog",
    "UserStatus",
    "UserProfile",
    "UserSession",
    "AuditLog",
    "FileMetadata",
    # Location Management Models
    "UserGroup",
    "UserGroupType",
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
    # Enums
    "Gender",
    "IdDocumentType", 
    "ValidationStatus",
    "AddressType",
    "PersonType",
    "NationalityType"
] 