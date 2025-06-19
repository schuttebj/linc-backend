"""
Office Model - Physical Facility Management
Merged from Location model - represents physical offices/facilities where services are provided
Implements office codes (A-Z) within regions for organizational structure
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Integer, Numeric, JSON, UniqueConstraint, CheckConstraint
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
    """Operational status for offices"""
    OPERATIONAL = "operational"          # Fully operational
    MAINTENANCE = "maintenance"          # Under maintenance
    SUSPENDED = "suspended"              # Temporarily suspended
    SETUP = "setup"                      # Being set up
    DECOMMISSIONED = "decommissioned"    # No longer in use
    INSPECTION = "inspection"            # Under inspection

class OfficeScope(PythonEnum):
    """Geographic scope of office service"""
    NATIONAL = "national"                # National scope
    PROVINCIAL = "provincial"            # Provincial scope
    REGIONAL = "regional"                # Regional scope
    LOCAL = "local"                      # Local/municipal scope

class OfficeType(PythonEnum):
    """Office types within regions"""
    PRIMARY = "primary"                  # Main/Head Office (usually A)
    BRANCH = "branch"                    # Branch Office (B-F)
    SPECIALIZED = "specialized"          # Specialized Units (G-L)
    MOBILE = "mobile"                    # Mobile/Temporary Units (M-P)
    SUPPORT = "support"                  # Support/Maintenance (Q-Z)

class Office(BaseModel):
    """
    Office Model - Physical Facility Management
    
    Represents physical offices for testing centers, printing facilities,
    administrative offices, and other infrastructure within the LINC system.
    
    Features:
    - Office codes (A-Z) within regions
    - Full address integration with ADDRCORR standard
    - Infrastructure type classification
    - Capacity and resource management
    - Operational status tracking
    - Geographic scope management
    """
    __tablename__ = "offices"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    office_code = Column(String(1), nullable=False, 
                        comment="Single letter office code (A-Z)")
    office_name = Column(String(200), nullable=False,
                        comment="Office display name")
    
    # Hierarchical relationships
    region_id = Column(UUID(as_uuid=True), ForeignKey('regions.id'), nullable=False,
                      comment="Parent region authority")
    
    # Infrastructure classification
    infrastructure_type = Column(String(2), nullable=False,
                                comment="Infrastructure type code (10=Fixed DLTC, etc.)")
    office_type = Column(String(20), nullable=False, default=OfficeType.BRANCH.value,
                        comment="Office type for organizational classification")
    
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
    office_scope = Column(String(20), nullable=False, default=OfficeScope.LOCAL.value,
                         comment="Geographic service scope")
    
    # Capacity management
    daily_capacity = Column(Integer, nullable=True, default=0,
                          comment="Maximum daily service capacity")
    current_load = Column(Integer, nullable=True, default=0,
                         comment="Current operational load")
    max_concurrent_operations = Column(Integer, nullable=True, default=1,
                                     comment="Maximum concurrent operations")
    staff_count = Column(Integer, nullable=True, default=0, 
                        comment="Number of staff assigned to this office")
    
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
    is_operational = Column(Boolean, nullable=False, default=True, 
                          comment="Currently operational for services")
    requires_appointment = Column(Boolean, nullable=False, default=False,
                                comment="Requires appointment for services")
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    
    # Relationships
    region = relationship("Region", back_populates="offices")
    user_assignments = relationship("UserLocationAssignment", back_populates="office")
    
    # Table constraints
    __table_args__ = (
        UniqueConstraint('region_id', 'office_code', name='uq_office_region_code'),
        CheckConstraint("office_code ~ '^[A-Z]$'", name='chk_office_code_format'),
        {'comment': 'Office management within regions with A-Z codes'},
    )
    
    def __repr__(self):
        return f"<Office(code='{self.office_code}', name='{self.office_name}', type='{self.infrastructure_type}')>"
    
    @property
    def full_office_code(self) -> str:
        """Get the full office identifier (RegionCode + OfficeCode)"""
        if self.region:
            return f"{self.region.user_group_code}{self.office_code}"
        return self.office_code
    
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
    def is_primary_office(self) -> bool:
        """Check if this is the primary office (usually code 'A')"""
        return self.office_type == OfficeType.PRIMARY.value or self.office_code == 'A'
    
    @property
    def is_mobile_unit(self) -> bool:
        """Check if this is a mobile unit"""
        return (self.office_type == OfficeType.MOBILE.value or 
                self.infrastructure_type == InfrastructureType.MOBILE_DLTC.value)
    
    @property
    def is_dltc(self) -> bool:
        """Check if this is a DLTC (Fixed or Mobile)"""
        return self.infrastructure_type in [
            InfrastructureType.FIXED_DLTC.value,
            InfrastructureType.MOBILE_DLTC.value
        ]
    
    @property
    def is_printing_facility(self) -> bool:
        """Check if this office offers printing services"""
        return self.infrastructure_type in [
            InfrastructureType.PRINTING_CENTER.value,
            InfrastructureType.COMBINED_CENTER.value
        ]
    
    @property
    def available_capacity(self) -> int:
        """Get available capacity for the office"""
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
        """Check if office is currently operational"""
        return (
            self.is_active and
            self.is_operational and
            self.operational_status == OperationalStatus.OPERATIONAL.value
        )
    
    def can_provide_service(self, service_type: str = None) -> bool:
        """Check if this office can provide a specific service"""
        if not self.is_operational():
            return False
        
        if service_type and self.services_offered:
            return service_type in self.services_offered
        
        # If no specific service types defined, assume all services available
        return True
    
    def is_within_capacity(self, additional_load: int = 1) -> bool:
        """Check if office can handle additional load"""
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
    
    def get_distance_to(self, other_office) -> float:
        """Calculate distance to another office (in kilometers)"""
        if (not self.latitude or not self.longitude or
            not other_office.latitude or not other_office.longitude):
            return float('inf')
        
        # Simple Haversine formula implementation
        import math
        
        lat1, lon1 = float(self.latitude), float(self.longitude)
        lat2, lon2 = float(other_office.latitude), float(other_office.longitude)
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in kilometers
        r = 6371
        
        return c * r
    
    @staticmethod
    def suggest_office_code(region_id: str, office_type: OfficeType = None) -> str:
        """Suggest the next available office code for a region"""
        if office_type == OfficeType.PRIMARY:
            return 'A'
        elif office_type == OfficeType.MOBILE:
            return 'M'
        else:
            return 'B'  # Default to first branch office
    
    @staticmethod
    def generate_office_code(region_code: str, office_code: str) -> str:
        """Generate full office identifier"""
        return f"{region_code}{office_code}" 