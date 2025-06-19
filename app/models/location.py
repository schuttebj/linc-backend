"""
Location Model
Implements physical location management for testing centers, printing facilities, etc.
Integrates with Region and Office hierarchy for complete facility management.
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Integer, Numeric, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PythonEnum
import uuid

from app.models.base import BaseModel

class InfrastructureType(PythonEnum):
    """Infrastructure types - using numeric codes for consistency"""
    FIXED_DLTC = "10"                    # Fixed Driving License Testing Center
    MOBILE_DLTC = "11"                   # Mobile Driving License Testing Unit
    PRINTING_CENTER = "12"               # Printing Center/Facility
    COMBINED_CENTER = "13"               # Combined Testing & Printing
    ADMIN_OFFICE = "14"                  # Administrative Office
    REGISTERING_AUTHORITY = "20"         # Registering Authority Office
    PROVINCIAL_OFFICE = "30"             # Provincial Office
    NATIONAL_OFFICE = "31"               # National Office
    VEHICLE_TESTING = "40"               # Vehicle Testing Station
    HELP_DESK = "50"                     # Help Desk Office

class OperationalStatus(PythonEnum):
    """Operational status for locations"""
    OPERATIONAL = "operational"          # Fully operational
    MAINTENANCE = "maintenance"          # Under maintenance
    SUSPENDED = "suspended"              # Temporarily suspended
    SETUP = "setup"                      # Being set up
    DECOMMISSIONED = "decommissioned"    # No longer in use
    INSPECTION = "inspection"            # Under inspection

class LocationScope(PythonEnum):
    """Geographic scope of location service"""
    NATIONAL = "national"                # National scope
    PROVINCIAL = "provincial"            # Provincial scope
    REGIONAL = "regional"                # Regional scope
    LOCAL = "local"                      # Local/municipal scope

class Location(BaseModel):
    """
    Location Model - Physical Facility Management
    
    Represents physical locations for testing centers, printing facilities,
    administrative offices, and other infrastructure within the LINC system.
    
    Features:
    - Full address integration with ADDRCORR standard
    - Infrastructure type classification
    - Capacity and resource management
    - Operational status tracking
    - Geographic scope management
    """
    __tablename__ = "locations"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    location_code = Column(String(20), nullable=False, unique=True, index=True,
                          comment="Unique location identifier")
    location_name = Column(String(200), nullable=False,
                          comment="Location display name")
    
    # Hierarchical relationships
    region_id = Column(UUID(as_uuid=True), ForeignKey('regions.id'), nullable=False,
                          comment="Parent region authority")
    office_id = Column(UUID(as_uuid=True), ForeignKey('offices.id'), nullable=True,
                      comment="Parent office (optional)")
    
    # Infrastructure classification
    infrastructure_type = Column(String(2), nullable=False,
                                comment="Infrastructure type code (10=Fixed DLTC, etc.)")
    
    # Address integration (ADDRCORR standard)
    address_line_1 = Column(String(100), nullable=False, comment="Street address line 1")
    address_line_2 = Column(String(100), nullable=True, comment="Street address line 2")
    address_line_3 = Column(String(100), nullable=True, comment="Street address line 3")
    city = Column(String(50), nullable=False, comment="City name")
    province_code = Column(String(2), nullable=False, index=True, comment="Province code")
    postal_code = Column(String(10), nullable=True, comment="Postal code")
    country_code = Column(String(2), nullable=False, default="ZA", comment="Country code")
    
    # Geographic coordinates
    latitude = Column(Numeric(precision=10, scale=8), nullable=True, comment="Latitude coordinate")
    longitude = Column(Numeric(precision=11, scale=8), nullable=True, comment="Longitude coordinate")
    
    # Operational configuration
    operational_status = Column(String(20), nullable=False, default=OperationalStatus.OPERATIONAL.value,
                               comment="Current operational status")
    location_scope = Column(String(20), nullable=False, default=LocationScope.LOCAL.value,
                          comment="Geographic service scope")
    
    # Capacity management
    daily_capacity = Column(Integer, nullable=True, default=0,
                          comment="Maximum daily service capacity")
    current_load = Column(Integer, nullable=True, default=0,
                         comment="Current operational load")
    max_concurrent_operations = Column(Integer, nullable=True, default=1,
                                     comment="Maximum concurrent operations")
    
    # Service configuration
    services_offered = Column(JSON, nullable=True,
                            comment="Available services in JSON format")
    operating_hours = Column(JSON, nullable=True,
                           comment="Operating hours per day in JSON format")
    special_hours = Column(JSON, nullable=True,
                         comment="Special operating hours (holidays, etc.)")
    
    # Contact information
    contact_person = Column(String(100), nullable=True, comment="Primary contact person")
    phone_number = Column(String(20), nullable=True, comment="Contact phone number")
    fax_number = Column(String(20), nullable=True, comment="Fax number")
    email = Column(String(255), nullable=True, comment="Contact email address")
    
    # Facility details
    facility_description = Column(Text, nullable=True,
                                comment="Detailed facility description")
    accessibility_features = Column(JSON, nullable=True,
                                  comment="Accessibility features in JSON format")
    parking_availability = Column(Boolean, nullable=True,
                                comment="Parking availability")
    public_transport_access = Column(Text, nullable=True,
                                   comment="Public transport access information")
    
    # Operational notes and instructions
    operational_notes = Column(Text, nullable=True,
                             comment="Internal operational notes")
    public_instructions = Column(Text, nullable=True,
                               comment="Public instructions for visitors")
    
    # Status management
    is_active = Column(Boolean, nullable=False, default=True, comment="Active status")
    is_public = Column(Boolean, nullable=False, default=True,
                      comment="Visible to public/citizens")
    requires_appointment = Column(Boolean, nullable=False, default=False,
                                comment="Requires appointment for services")
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    
    # Relationships
    region = relationship("Region", back_populates="locations")
    office = relationship("Office", back_populates="locations")
    user_assignments = relationship("UserLocationAssignment", back_populates="location")
    resources = relationship("LocationResource", back_populates="location", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Location(code='{self.location_code}', name='{self.location_name}', type='{self.infrastructure_type}')>"
    
    @property
    def full_address(self) -> str:
        """Get formatted full address"""
        address_parts = [self.address_line_1]
        if self.address_line_2:
            address_parts.append(self.address_line_2)
        if self.address_line_3:
            address_parts.append(self.address_line_3)
        
        address_parts.append(self.city)
        if self.postal_code:
            address_parts.append(self.postal_code)
        
        return ", ".join(address_parts)
    
    @property
    def is_dltc(self) -> bool:
        """Check if this is a DLTC (Fixed or Mobile)"""
        return self.infrastructure_type in [
            InfrastructureType.FIXED_DLTC.value,
            InfrastructureType.MOBILE_DLTC.value
        ]
    
    @property
    def is_printing_facility(self) -> bool:
        """Check if this location offers printing services"""
        return self.infrastructure_type in [
            InfrastructureType.PRINTING_CENTER.value,
            InfrastructureType.COMBINED_CENTER.value
        ]
    
    @property
    def available_capacity(self) -> int:
        """Get available capacity for the location"""
        if not self.daily_capacity:
            return 0
        
        used_capacity = self.current_load or 0
        return max(0, self.daily_capacity - used_capacity)
    
    @property
    def capacity_utilization(self) -> float:
        """Get capacity utilization percentage"""
        if not self.daily_capacity:
            return 0.0
        
        used_capacity = self.current_load or 0
        return (used_capacity / self.daily_capacity) * 100
    
    def is_operational(self) -> bool:
        """Check if location is currently operational"""
        return (
            self.is_active and
            self.operational_status == OperationalStatus.OPERATIONAL.value
        )
    
    def can_provide_service(self, service_type: str) -> bool:
        """Check if location can provide a specific service"""
        if not self.is_operational():
            return False
        
        if not self.services_offered:
            return True  # Assume all services if not specified
        
        return service_type in self.services_offered
    
    def is_within_capacity(self, additional_load: int = 1) -> bool:
        """Check if location can handle additional load"""
        current_load = self.current_load or 0
        return (current_load + additional_load) <= (self.daily_capacity or 0)
    
    def validate_coordinates(self) -> bool:
        """Validate geographic coordinates"""
        if self.latitude is None or self.longitude is None:
            return True  # Coordinates are optional
        
        # Basic validation for South African coordinates
        # South Africa: roughly latitude -35 to -22, longitude 16 to 33
        return (
            -35 <= float(self.latitude) <= -22 and
            16 <= float(self.longitude) <= 33
        )
    
    def get_distance_to(self, other_location) -> float:
        """Calculate distance to another location (in kilometers)"""
        if (not self.latitude or not self.longitude or
            not other_location.latitude or not other_location.longitude):
            return float('inf')
        
        # Simple Haversine formula implementation
        import math
        
        lat1, lon1 = float(self.latitude), float(self.longitude)
        lat2, lon2 = float(other_location.latitude), float(other_location.longitude)
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in kilometers
        r = 6371
        
        return c * r
    
    @staticmethod
    def generate_location_code(user_group_code: str, infrastructure_type: str, sequence: int = 1) -> str:
        """Generate a location code based on user group and infrastructure type"""
        return f"{user_group_code}-{infrastructure_type}-{sequence:03d}" 