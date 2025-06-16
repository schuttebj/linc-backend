"""
User Location Assignment Model
Implements many-to-many relationships between users and locations
Handles user assignments to multiple locations with role-based access
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PythonEnum
import uuid

from app.models.base import BaseModel

class AssignmentType(PythonEnum):
    """Types of user-location assignments"""
    PRIMARY = "primary"                  # Primary/home location
    SECONDARY = "secondary"              # Secondary assignment
    TEMPORARY = "temporary"              # Temporary assignment
    BACKUP = "backup"                    # Backup coverage
    TRAINING = "training"                # Training assignment
    SUPERVISION = "supervision"          # Supervisory role
    MAINTENANCE = "maintenance"          # Maintenance role

class AssignmentStatus(PythonEnum):
    """Status of user assignments"""
    ACTIVE = "active"                    # Currently active
    INACTIVE = "inactive"                # Temporarily inactive
    SUSPENDED = "suspended"              # Suspended assignment
    PENDING = "pending"                  # Pending approval
    EXPIRED = "expired"                  # Assignment expired

class UserLocationAssignment(BaseModel):
    """
    User Location Assignment Model - User-Location Mapping
    
    Manages the many-to-many relationship between users and locations.
    Supports multiple assignment types, temporary assignments, and role-based access.
    
    Features:
    - Multiple assignment types (primary, secondary, temporary, etc.)
    - Date-based assignment validity
    - Assignment-specific permissions and access levels
    - Activity tracking and audit trail
    """
    __tablename__ = "user_location_assignments"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Relationship fields
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False,
                    comment="Assigned user")
    location_id = Column(UUID(as_uuid=True), ForeignKey('locations.id'), nullable=False,
                        comment="Assigned location")
    office_id = Column(UUID(as_uuid=True), ForeignKey('offices.id'), nullable=True,
                      comment="Specific office within location (optional)")
    
    # Assignment classification
    assignment_type = Column(String(20), nullable=False, default=AssignmentType.SECONDARY.value,
                           comment="Type of assignment")
    assignment_status = Column(String(20), nullable=False, default=AssignmentStatus.ACTIVE.value,
                             comment="Current assignment status")
    
    # Assignment validity
    effective_date = Column(DateTime, nullable=False, default=func.now(),
                          comment="Assignment effective date")
    expiry_date = Column(DateTime, nullable=True,
                        comment="Assignment expiry date (null = indefinite)")
    
    # Access and permissions
    access_level = Column(String(20), nullable=False, default="standard",
                        comment="Access level for this assignment")
    can_manage_location = Column(Boolean, nullable=False, default=False,
                               comment="Can manage location settings")
    can_assign_others = Column(Boolean, nullable=False, default=False,
                             comment="Can assign other users to this location")
    can_view_reports = Column(Boolean, nullable=False, default=True,
                            comment="Can view location reports")
    can_manage_resources = Column(Boolean, nullable=False, default=False,
                                comment="Can manage location resources")
    
    # Operational details
    work_schedule = Column(Text, nullable=True,
                         comment="Work schedule for this assignment (JSON)")
    responsibilities = Column(Text, nullable=True,
                            comment="Specific responsibilities at this location")
    
    # Assignment context
    assigned_by = Column(String(100), nullable=True, comment="Who made the assignment")
    assignment_reason = Column(Text, nullable=True, comment="Reason for assignment")
    notes = Column(Text, nullable=True, comment="Additional notes")
    
    # Activity tracking
    last_activity_date = Column(DateTime, nullable=True,
                              comment="Last activity at this location")
    total_hours_worked = Column(Integer, nullable=True, default=0,
                              comment="Total hours worked at this location")
    
    # Status management
    is_active = Column(Boolean, nullable=False, default=True, comment="Active status")
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="location_assignments")
    location = relationship("Location", back_populates="user_assignments")
    office = relationship("Office", back_populates="user_assignments")
    
    # Unique constraint to prevent duplicate active assignments
    __table_args__ = (
        {'comment': 'User-location assignments with role-based access control'},
    )
    
    def __repr__(self):
        return f"<UserLocationAssignment(user_id='{self.user_id}', location_id='{self.location_id}', type='{self.assignment_type}')>"
    
    @property
    def is_valid_assignment(self) -> bool:
        """Check if assignment is currently valid"""
        if not self.is_active or self.assignment_status != AssignmentStatus.ACTIVE.value:
            return False
        
        now = func.now()
        
        # Check effective date
        if self.effective_date and self.effective_date > now:
            return False
        
        # Check expiry date
        if self.expiry_date and self.expiry_date <= now:
            return False
        
        return True
    
    @property
    def is_primary_assignment(self) -> bool:
        """Check if this is a primary assignment"""
        return self.assignment_type == AssignmentType.PRIMARY.value
    
    @property
    def is_temporary_assignment(self) -> bool:
        """Check if this is a temporary assignment"""
        return self.assignment_type == AssignmentType.TEMPORARY.value
    
    @property
    def days_until_expiry(self) -> int:
        """Get number of days until assignment expires"""
        if not self.expiry_date:
            return -1  # Indefinite assignment
        
        delta = self.expiry_date - func.now()
        return delta.days if delta.days > 0 else 0
    
    @property
    def assignment_duration_days(self) -> int:
        """Get total assignment duration in days"""
        start_date = self.effective_date or self.created_at
        end_date = self.expiry_date or func.now()
        
        delta = end_date - start_date
        return delta.days
    
    def can_perform_action(self, action: str) -> bool:
        """Check if user can perform a specific action at this location"""
        if not self.is_valid_assignment:
            return False
        
        action_permissions = {
            "manage_location": self.can_manage_location,
            "assign_users": self.can_assign_others,
            "view_reports": self.can_view_reports,
            "manage_resources": self.can_manage_resources,
        }
        
        return action_permissions.get(action, False)
    
    def extend_assignment(self, new_expiry_date: DateTime) -> bool:
        """Extend assignment expiry date"""
        if new_expiry_date <= func.now():
            return False
        
        self.expiry_date = new_expiry_date
        return True
    
    def suspend_assignment(self, reason: str = None) -> None:
        """Suspend the assignment"""
        self.assignment_status = AssignmentStatus.SUSPENDED.value
        if reason:
            current_notes = self.notes or ""
            self.notes = f"{current_notes}\nSuspended: {reason}".strip()
    
    def reactivate_assignment(self) -> None:
        """Reactivate a suspended assignment"""
        if self.assignment_status == AssignmentStatus.SUSPENDED.value:
            self.assignment_status = AssignmentStatus.ACTIVE.value
    
    def record_activity(self, hours_worked: int = None) -> None:
        """Record user activity at this location"""
        self.last_activity_date = func.now()
        if hours_worked:
            self.total_hours_worked = (self.total_hours_worked or 0) + hours_worked
    
    def validate_assignment_constraints(self) -> list:
        """Validate assignment constraints and return any violations"""
        violations = []
        
        # Check date constraints
        if self.expiry_date and self.effective_date and self.expiry_date <= self.effective_date:
            violations.append("Expiry date must be after effective date")
        
        # Check primary assignment constraints
        if self.assignment_type == AssignmentType.PRIMARY.value:
            if self.expiry_date:
                violations.append("Primary assignments should not have expiry dates")
        
        # Check temporary assignment constraints
        if self.assignment_type == AssignmentType.TEMPORARY.value:
            if not self.expiry_date:
                violations.append("Temporary assignments must have expiry dates")
        
        return violations
    
    @staticmethod
    def get_user_primary_location(user_id: str):
        """Get user's primary location assignment"""
        # This would be implemented in the service layer
        # Return the primary assignment for the user
        pass
    
    @staticmethod
    def check_assignment_conflicts(user_id: str, location_id: str, 
                                 effective_date: DateTime, expiry_date: DateTime = None) -> list:
        """Check for assignment conflicts for a user"""
        # This would be implemented in the service layer
        # Check for overlapping assignments, capacity constraints, etc.
        conflicts = []
        return conflicts 