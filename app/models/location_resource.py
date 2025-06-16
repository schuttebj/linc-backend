"""
Location Resource Model
Implements basic resource management for locations
Tracks equipment, printers, testing apparatus, and other resources
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PythonEnum
import uuid

from app.models.base import BaseModel

class ResourceType(PythonEnum):
    """Resource types available at locations"""
    PRINTER = "printer"                  # Printing equipment
    TESTING_EQUIPMENT = "testing"        # Testing apparatus
    COMPUTER = "computer"                # Computer workstations
    SCANNER = "scanner"                  # Document scanners
    CAMERA = "camera"                    # Photography equipment
    VEHICLE = "vehicle"                  # Testing vehicles
    FURNITURE = "furniture"              # Office furniture
    SECURITY = "security"                # Security equipment
    NETWORK = "network"                  # Network equipment
    OTHER = "other"                      # Other resources

class ResourceStatus(PythonEnum):
    """Resource operational status"""
    OPERATIONAL = "operational"          # Fully operational
    MAINTENANCE = "maintenance"          # Under maintenance
    REPAIR = "repair"                    # Needs repair
    DECOMMISSIONED = "decommissioned"    # No longer in use
    RESERVED = "reserved"                # Reserved for specific use
    CALIBRATION = "calibration"          # Under calibration

class LocationResource(BaseModel):
    """
    Location Resource Model - Equipment and Asset Management
    
    Tracks physical and digital resources available at each location.
    Supports capacity planning, maintenance scheduling, and resource allocation.
    
    Features:
    - Resource type classification
    - Status and availability tracking
    - Maintenance and lifecycle management
    - Capacity and utilization metrics
    """
    __tablename__ = "location_resources"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    resource_code = Column(String(50), nullable=False, index=True,
                          comment="Unique resource identifier")
    resource_name = Column(String(100), nullable=False,
                          comment="Resource display name")
    
    # Location relationship
    location_id = Column(UUID(as_uuid=True), ForeignKey('locations.id'), nullable=False,
                        comment="Parent location")
    
    # Resource classification
    resource_type = Column(String(20), nullable=False,
                          comment="Resource type category")
    subtype = Column(String(50), nullable=True,
                    comment="Resource subtype/model")
    
    # Specifications and details
    manufacturer = Column(String(100), nullable=True, comment="Manufacturer name")
    model_number = Column(String(100), nullable=True, comment="Model/part number")
    serial_number = Column(String(100), nullable=True, comment="Serial number")
    specifications = Column(Text, nullable=True, comment="Technical specifications")
    
    # Status and availability
    resource_status = Column(String(20), nullable=False, default=ResourceStatus.OPERATIONAL.value,
                           comment="Current operational status")
    is_available = Column(Boolean, nullable=False, default=True,
                         comment="Available for use")
    is_shared = Column(Boolean, nullable=False, default=False,
                      comment="Shared across multiple services")
    
    # Capacity and utilization
    capacity_units = Column(String(50), nullable=True,
                          comment="Units of measurement (pages/hour, tests/day, etc.)")
    max_capacity_per_hour = Column(Integer, nullable=True, default=0,
                                 comment="Maximum capacity per hour")
    max_capacity_per_day = Column(Integer, nullable=True, default=0,
                                comment="Maximum capacity per day")
    current_utilization = Column(Numeric(precision=5, scale=2), nullable=True, default=0.0,
                               comment="Current utilization percentage")
    
    # Lifecycle management
    acquisition_date = Column(DateTime, nullable=True, comment="Date acquired")
    warranty_expiry = Column(DateTime, nullable=True, comment="Warranty expiry date")
    next_maintenance = Column(DateTime, nullable=True, comment="Next scheduled maintenance")
    replacement_due = Column(DateTime, nullable=True, comment="Replacement due date")
    
    # Cost and value tracking
    acquisition_cost = Column(Numeric(precision=12, scale=2), nullable=True,
                            comment="Original acquisition cost")
    current_value = Column(Numeric(precision=12, scale=2), nullable=True,
                         comment="Current estimated value")
    annual_maintenance_cost = Column(Numeric(precision=10, scale=2), nullable=True,
                                   comment="Annual maintenance cost")
    
    # Operational configuration
    operating_instructions = Column(Text, nullable=True,
                                  comment="Operating instructions and notes")
    maintenance_notes = Column(Text, nullable=True,
                             comment="Maintenance history and notes")
    safety_requirements = Column(Text, nullable=True,
                               comment="Safety requirements and precautions")
    
    # Location within facility
    room_location = Column(String(50), nullable=True, comment="Room/area within location")
    asset_tag = Column(String(50), nullable=True, comment="Asset tag/barcode")
    
    # Status management
    is_active = Column(Boolean, nullable=False, default=True, comment="Active status")
    requires_certification = Column(Boolean, nullable=False, default=False,
                                  comment="Requires operator certification")
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    
    # Relationships
    location = relationship("Location", back_populates="resources")
    
    def __repr__(self):
        return f"<LocationResource(code='{self.resource_code}', name='{self.resource_name}', type='{self.resource_type}')>"
    
    @property
    def is_operational(self) -> bool:
        """Check if resource is currently operational"""
        return (
            self.is_active and
            self.is_available and
            self.resource_status == ResourceStatus.OPERATIONAL.value
        )
    
    @property
    def needs_maintenance(self) -> bool:
        """Check if resource needs maintenance"""
        if not self.next_maintenance:
            return False
        
        return self.next_maintenance <= func.now()
    
    @property
    def is_under_warranty(self) -> bool:
        """Check if resource is still under warranty"""
        if not self.warranty_expiry:
            return False
        
        return self.warranty_expiry > func.now()
    
    @property
    def available_capacity_per_hour(self) -> int:
        """Get available capacity per hour based on current utilization"""
        if not self.max_capacity_per_hour:
            return 0
        
        utilization = float(self.current_utilization or 0) / 100
        used_capacity = int(self.max_capacity_per_hour * utilization)
        return max(0, self.max_capacity_per_hour - used_capacity)
    
    @property
    def available_capacity_per_day(self) -> int:
        """Get available capacity per day based on current utilization"""
        if not self.max_capacity_per_day:
            return 0
        
        utilization = float(self.current_utilization or 0) / 100
        used_capacity = int(self.max_capacity_per_day * utilization)
        return max(0, self.max_capacity_per_day - used_capacity)
    
    def can_handle_load(self, required_capacity: int, time_period: str = "hour") -> bool:
        """Check if resource can handle additional load"""
        if not self.is_operational:
            return False
        
        if time_period == "hour":
            available = self.available_capacity_per_hour
        elif time_period == "day":
            available = self.available_capacity_per_day
        else:
            return False
        
        return available >= required_capacity
    
    def update_utilization(self, new_utilization: float) -> None:
        """Update current utilization percentage"""
        self.current_utilization = max(0.0, min(100.0, new_utilization))
    
    def schedule_maintenance(self, maintenance_date: DateTime, notes: str = None) -> None:
        """Schedule maintenance for the resource"""
        self.next_maintenance = maintenance_date
        if notes:
            current_notes = self.maintenance_notes or ""
            self.maintenance_notes = f"{current_notes}\n{func.now()}: {notes}".strip()
    
    def mark_for_replacement(self, replacement_date: DateTime) -> None:
        """Mark resource for replacement"""
        self.replacement_due = replacement_date
        self.resource_status = ResourceStatus.MAINTENANCE.value
    
    def calculate_depreciation(self, years_in_service: int = None) -> float:
        """Calculate current depreciated value"""
        if not self.acquisition_cost:
            return 0.0
        
        if years_in_service is None and self.acquisition_date:
            years_in_service = (func.now() - self.acquisition_date).days / 365.25
        
        if not years_in_service:
            return float(self.acquisition_cost)
        
        # Simple straight-line depreciation over 5 years
        depreciation_rate = 0.20  # 20% per year
        total_depreciation = min(1.0, years_in_service * depreciation_rate)
        
        return float(self.acquisition_cost) * (1 - total_depreciation)
    
    @staticmethod
    def generate_resource_code(location_code: str, resource_type: str, sequence: int = 1) -> str:
        """Generate a resource code based on location and type"""
        type_prefix = resource_type[:3].upper()
        return f"{location_code}-{type_prefix}-{sequence:03d}" 