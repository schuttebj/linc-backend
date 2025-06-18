"""
User Location Assignment CRUD Operations
Comprehensive database operations for user-location assignment management
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from uuid import UUID

from app.models.user_location_assignment import UserLocationAssignment, AssignmentType, AssignmentStatus
from app.schemas.location import UserLocationAssignmentCreate, UserLocationAssignmentUpdate, UserLocationAssignmentListFilter

class UserLocationAssignmentCRUD:
    """CRUD operations for UserLocationAssignment"""
    
    def __init__(self, model=UserLocationAssignment):
        self.model = model
    
    def create(self, db: Session, *, obj_in: UserLocationAssignmentCreate, created_by: str = None) -> UserLocationAssignment:
        """Create a new user location assignment"""
        db_obj = UserLocationAssignment(
            user_id=obj_in.user_id,
            location_id=obj_in.location_id,
            office_id=obj_in.office_id,
            assignment_type=obj_in.assignment_type,
            assignment_status=obj_in.assignment_status,
            effective_date=obj_in.effective_date,
            expiry_date=obj_in.expiry_date,
            access_level=obj_in.access_level,
            can_manage_location=obj_in.can_manage_location,
            can_assign_others=obj_in.can_assign_others,
            can_view_reports=obj_in.can_view_reports,
            can_manage_resources=obj_in.can_manage_resources,
            work_schedule=obj_in.work_schedule,
            responsibilities=obj_in.responsibilities,
            assignment_reason=obj_in.assignment_reason,
            notes=obj_in.notes,
            is_active=obj_in.is_active,
            created_by=created_by
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get(self, db: Session, id: UUID) -> Optional[UserLocationAssignment]:
        """Get assignment by ID"""
        return db.query(UserLocationAssignment).filter(UserLocationAssignment.id == id).first()
    
    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[UserLocationAssignmentListFilter] = None
    ) -> List[UserLocationAssignment]:
        """Get multiple assignments with optional filtering"""
        query = db.query(UserLocationAssignment)
        
        if filters:
            if filters.user_id:
                query = query.filter(UserLocationAssignment.user_id == filters.user_id)
            
            if filters.location_id:
                query = query.filter(UserLocationAssignment.location_id == filters.location_id)
            
            if filters.assignment_type:
                query = query.filter(UserLocationAssignment.assignment_type == filters.assignment_type)
            
            if filters.assignment_status:
                query = query.filter(UserLocationAssignment.assignment_status == filters.assignment_status)
            
            if filters.is_active is not None:
                query = query.filter(UserLocationAssignment.is_active == filters.is_active)
        
        return query.order_by(UserLocationAssignment.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_by_user(self, db: Session, user_id: UUID) -> List[UserLocationAssignment]:
        """Get all assignments for a user"""
        return db.query(UserLocationAssignment).filter(
            and_(
                UserLocationAssignment.user_id == user_id,
                UserLocationAssignment.is_active == True
            )
        ).all()
    
    def get_by_location(self, db: Session, location_id: UUID) -> List[UserLocationAssignment]:
        """Get all assignments for a location"""
        return db.query(UserLocationAssignment).filter(
            and_(
                UserLocationAssignment.location_id == location_id,
                UserLocationAssignment.is_active == True
            )
        ).all()
    
    def get_active_assignments(self, db: Session, user_id: UUID = None, location_id: UUID = None) -> List[UserLocationAssignment]:
        """Get active assignments, optionally filtered by user or location"""
        query = db.query(UserLocationAssignment).filter(
            and_(
                UserLocationAssignment.is_active == True,
                UserLocationAssignment.assignment_status == AssignmentStatus.ACTIVE.value
            )
        )
        
        if user_id:
            query = query.filter(UserLocationAssignment.user_id == user_id)
        
        if location_id:
            query = query.filter(UserLocationAssignment.location_id == location_id)
        
        return query.all()
    
    def get_primary_assignment(self, db: Session, user_id: UUID) -> Optional[UserLocationAssignment]:
        """Get user's primary location assignment"""
        return db.query(UserLocationAssignment).filter(
            and_(
                UserLocationAssignment.user_id == user_id,
                UserLocationAssignment.assignment_type == AssignmentType.PRIMARY.value,
                UserLocationAssignment.is_active == True,
                UserLocationAssignment.assignment_status == AssignmentStatus.ACTIVE.value
            )
        ).first()
    
    def update(
        self, 
        db: Session, 
        *, 
        db_obj: UserLocationAssignment, 
        obj_in: UserLocationAssignmentUpdate,
        updated_by: str = None
    ) -> UserLocationAssignment:
        """Update assignment"""
        update_data = obj_in.dict(exclude_unset=True)
        if updated_by:
            update_data["updated_by"] = updated_by
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, *, id: UUID) -> UserLocationAssignment:
        """Soft delete assignment"""
        obj = db.query(UserLocationAssignment).get(id)
        if obj:
            obj.is_active = False
            db.add(obj)
            db.commit()
        return obj
    
    def check_assignment_exists(self, db: Session, user_id: UUID, location_id: UUID) -> bool:
        """Check if active assignment exists for user-location pair"""
        return db.query(UserLocationAssignment).filter(
            and_(
                UserLocationAssignment.user_id == user_id,
                UserLocationAssignment.location_id == location_id,
                UserLocationAssignment.is_active == True
            )
        ).first() is not None
    
    def get_assignments_by_user_group(self, db: Session, user_group_id: UUID) -> List[UserLocationAssignment]:
        """Get all assignments for locations in a user group"""
        from app.models.location import Location
        return db.query(UserLocationAssignment).join(Location).filter(
            and_(
                Location.user_group_id == user_group_id,
                UserLocationAssignment.is_active == True
            )
        ).all()

# Create instance for use
user_location_assignment = UserLocationAssignmentCRUD(UserLocationAssignment)

# Function-based interface for backward compatibility
def user_location_assignment_create(db: Session, *, obj_in: UserLocationAssignmentCreate, created_by: str = None) -> UserLocationAssignment:
    """Create user location assignment"""
    return user_location_assignment.create(db=db, obj_in=obj_in, created_by=created_by)

def user_location_assignment_update(db: Session, *, db_obj: UserLocationAssignment, obj_in: UserLocationAssignmentUpdate, updated_by: str = None) -> UserLocationAssignment:
    """Update user location assignment"""
    return user_location_assignment.update(db=db, db_obj=db_obj, obj_in=obj_in, updated_by=updated_by)

def user_location_assignment_delete(db: Session, *, id: UUID) -> UserLocationAssignment:
    """Delete user location assignment"""
    return user_location_assignment.delete(db=db, id=id) 