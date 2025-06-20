# LINC Database Models Package 

from .base import BaseModel
from .enums import *
from .person import Person, PersonNature, IdentificationType, AddressType, PersonAlias, NaturalPerson, PersonAddress, Organization
from .license import LicenseApplication, LicenseCard, ApplicationPayment, TestCenter, ApplicationStatus, LicenseType
# from .application import Application, ApplicationType, ApplicationStatus  # TODO: Create application model
from .user import User, UserAuditLog, UserSession, UserStatus
from .region import Region, RegionType, RegistrationStatus
from .office import Office, OfficeType, InfrastructureType, OperationalStatus, OfficeScope
from .location_resource import LocationResource, ResourceType, ResourceStatus
from .user_location_assignment import UserLocationAssignment, AssignmentType, AssignmentStatus

# NEW PERMISSION SYSTEM IMPORTS
from .user_type import UserType, UserRegionAssignment, UserOfficeAssignment
from .permission_system import RegionRole, OfficeRole, PermissionAuditLog

# LEGACY MODELS REMOVED - Migration complete

__all__ = [
    "BaseModel",
    # Person models
    "Person",
    "PersonNature",
    "IdentificationType", 
    "PersonAlias",
    "NaturalPerson",
    "PersonAddress",
    "Organization",
    "AddressType",
    
    # License models
    "LicenseApplication",
    "LicenseCard", 
    "ApplicationPayment",
    "TestCenter",
    "ApplicationStatus",
    "LicenseType",
    
    # Application models - TODO: Create application model
    # "Application",
    # "ApplicationType", 
    # "ApplicationStatus",
    
    # User models
    "User",
    "UserAuditLog",
    "UserSession",
    "UserStatus",
    "UserType",
    
    # Organization models
    "Region",
    "RegionType",
    "RegistrationStatus",
    "Office",
    "OfficeType",
    "InfrastructureType",
    "OperationalStatus",
    "OfficeScope",
    
    # Resource models
    "LocationResource",
    "ResourceType",
    "ResourceStatus",
    
    # Assignment models
    "UserLocationAssignment",
    "AssignmentType",
    "AssignmentStatus",
    
    # Enums (from enums.py)
    "Gender",
    "ValidationStatus",
    
    # Permission system
    "UserRegionAssignment",
    "UserOfficeAssignment",
    "RegionRole",
    "OfficeRole", 
    "PermissionAuditLog",
] 