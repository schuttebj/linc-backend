"""
UserGroup CRUD Operations
Comprehensive database operations for user group management
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from uuid import UUID

from app.models.user_group import UserGroup, UserGroupType, RegistrationStatus
from app.schemas.location import UserGroupCreate, UserGroupUpdate, UserGroupListFilter

class UserGroupCRUD:
    """CRUD operations for UserGroup"""
    
    def __init__(self, model=UserGroup):
        self.model = model
    
    def create(self, db: Session, *, obj_in: UserGroupCreate, created_by: str = None) -> UserGroup:
        """Create a new user group"""
        db_obj = UserGroup(
            user_group_code=obj_in.user_group_code,
            user_group_name=obj_in.user_group_name,
            user_group_type=obj_in.user_group_type,
            province_code=obj_in.province_code,
            parent_group_id=obj_in.parent_group_id,
            is_provincial_help_desk=obj_in.is_provincial_help_desk,
            is_national_help_desk=obj_in.is_national_help_desk,
            registration_status=obj_in.registration_status,
            suspended_until=obj_in.suspended_until,
            contact_person=obj_in.contact_person,
            phone_number=obj_in.phone_number,
            email=obj_in.email,
            operational_notes=obj_in.operational_notes,
            service_area_description=obj_in.service_area_description,
            is_active=obj_in.is_active,
            created_by=created_by
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get(self, db: Session, id: UUID) -> Optional[UserGroup]:
        """Get user group by ID"""
        return db.query(UserGroup).filter(UserGroup.id == id).first()
    
    def get_by_code(self, db: Session, user_group_code: str) -> Optional[UserGroup]:
        """Get user group by code"""
        return db.query(UserGroup).filter(UserGroup.user_group_code == user_group_code).first()
    
    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[UserGroupListFilter] = None
    ) -> List[UserGroup]:
        """Get multiple user groups with optional filtering"""
        query = db.query(UserGroup)
        
        if filters:
            if filters.province_code:
                query = query.filter(UserGroup.province_code == filters.province_code)
            
            if filters.user_group_type:
                query = query.filter(UserGroup.user_group_type == filters.user_group_type)
            
            if filters.registration_status:
                query = query.filter(UserGroup.registration_status == filters.registration_status)
            
            if filters.is_active is not None:
                query = query.filter(UserGroup.is_active == filters.is_active)
            
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        UserGroup.user_group_code.ilike(search_term),
                        UserGroup.user_group_name.ilike(search_term),
                        UserGroup.contact_person.ilike(search_term)
                    )
                )
        
        return query.order_by(UserGroup.user_group_code).offset(skip).limit(limit).all()
    
    def update(
        self, 
        db: Session, 
        *, 
        db_obj: UserGroup, 
        obj_in: UserGroupUpdate,
        updated_by: str = None
    ) -> UserGroup:
        """Update user group"""
        update_data = obj_in.dict(exclude_unset=True)
        if updated_by:
            update_data["updated_by"] = updated_by
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, *, id: UUID) -> UserGroup:
        """Soft delete user group"""
        obj = db.query(UserGroup).get(id)
        if obj:
            obj.is_active = False
            db.add(obj)
            db.commit()
        return obj
    
    def get_by_province(self, db: Session, province_code: str) -> List[UserGroup]:
        """Get all user groups in a province"""
        return db.query(UserGroup).filter(
            and_(
                UserGroup.province_code == province_code,
                UserGroup.is_active == True
            )
        ).all()
    
    def get_dltc_groups(self, db: Session) -> List[UserGroup]:
        """Get all DLTC user groups"""
        return db.query(UserGroup).filter(
            and_(
                UserGroup.user_group_type.in_([UserGroupType.FIXED_DLTC.value, UserGroupType.MOBILE_DLTC.value]),
                UserGroup.is_active == True
            )
        ).all()
    
    def get_help_desk_groups(self, db: Session) -> List[UserGroup]:
        """Get all help desk groups"""
        return db.query(UserGroup).filter(
            and_(
                or_(
                    UserGroup.is_provincial_help_desk == True,
                    UserGroup.is_national_help_desk == True
                ),
                UserGroup.is_active == True
            )
        ).all()
    
    def get_operational_groups(self, db: Session) -> List[UserGroup]:
        """Get operationally valid user groups"""
        return db.query(UserGroup).filter(
            and_(
                UserGroup.is_active == True,
                UserGroup.registration_status == RegistrationStatus.REGISTERED.value,
                or_(
                    UserGroup.suspended_until.is_(None),
                    UserGroup.suspended_until <= func.now()
                )
            )
        ).all()
    
    def check_code_exists(self, db: Session, user_group_code: str, exclude_id: UUID = None) -> bool:
        """Check if user group code already exists"""
        query = db.query(UserGroup).filter(UserGroup.user_group_code == user_group_code)
        if exclude_id:
            query = query.filter(UserGroup.id != exclude_id)
        return query.first() is not None
    
    def get_children(self, db: Session, parent_id: UUID) -> List[UserGroup]:
        """Get child user groups"""
        return db.query(UserGroup).filter(
            and_(
                UserGroup.parent_group_id == parent_id,
                UserGroup.is_active == True
            )
        ).all()
    
    def get_statistics(self, db: Session) -> Dict[str, Any]:
        """Get user group statistics"""
        total = db.query(UserGroup).count()
        active = db.query(UserGroup).filter(UserGroup.is_active == True).count()
        
        # Group by type
        type_stats = db.query(
            UserGroup.user_group_type,
            func.count(UserGroup.id).label('count')
        ).filter(UserGroup.is_active == True).group_by(UserGroup.user_group_type).all()
        
        # Group by province
        province_stats = db.query(
            UserGroup.province_code,
            func.count(UserGroup.id).label('count')
        ).filter(UserGroup.is_active == True).group_by(UserGroup.province_code).all()
        
        return {
            "total_user_groups": total,
            "active_user_groups": active,
            "user_groups_by_type": {stat.user_group_type: stat.count for stat in type_stats},
            "user_groups_by_province": {stat.province_code: stat.count for stat in province_stats}
        }

# Create instance
user_group = UserGroupCRUD(UserGroup) 