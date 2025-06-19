"""
Region CRUD Operations
Comprehensive database operations for region management
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from uuid import UUID

from app.models.region import Region, RegionType, RegistrationStatus
from app.schemas.location import RegionCreate, RegionUpdate, RegionListFilter

class RegionCRUD:
    """CRUD operations for Region"""
    
    def __init__(self, model=Region):
        self.model = model
    
    def create(self, db: Session, *, obj_in: RegionCreate, created_by: str = None) -> Region:
        """Create a new region"""
        db_obj = Region(
            user_group_code=obj_in.user_group_code,
            user_group_name=obj_in.user_group_name,
            user_group_type=obj_in.user_group_type,
            province_code=obj_in.province_code,
            parent_region_id=obj_in.parent_region_id,
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
    
    def get(self, db: Session, id: UUID) -> Optional[Region]:
        """Get region by ID"""
        return db.query(Region).filter(Region.id == id).first()
    
    def get_by_code(self, db: Session, region_code: str) -> Optional[Region]:
        """Get region by code"""
        return db.query(Region).filter(Region.user_group_code == region_code).first()
    
    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[RegionListFilter] = None
    ) -> List[Region]:
        """Get multiple regions with optional filtering"""
        query = db.query(Region)
        
        if filters:
            if filters.province_code:
                query = query.filter(Region.province_code == filters.province_code)
            
            if filters.region_type:
                query = query.filter(Region.user_group_type == filters.region_type)
            
            if filters.registration_status:
                query = query.filter(Region.registration_status == filters.registration_status)
            
            if filters.is_active is not None:
                query = query.filter(Region.is_active == filters.is_active)
            
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        Region.user_group_code.ilike(search_term),
                        Region.user_group_name.ilike(search_term),
                        Region.contact_person.ilike(search_term)
                    )
                )
        
        return query.order_by(Region.user_group_code).offset(skip).limit(limit).all()
    
    def update(
        self, 
        db: Session, 
        *, 
        db_obj: Region, 
        obj_in: RegionUpdate,
        updated_by: str = None
    ) -> Region:
        """Update region"""
        update_data = obj_in.dict(exclude_unset=True)
        if updated_by:
            update_data["updated_by"] = updated_by
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, *, id: UUID) -> Region:
        """Soft delete region"""
        obj = db.query(Region).get(id)
        if obj:
            obj.is_active = False
            db.add(obj)
            db.commit()
        return obj
    
    def get_by_province(self, db: Session, province_code: str) -> List[Region]:
        """Get all regions in a province"""
        return db.query(Region).filter(
            and_(
                Region.province_code == province_code,
                Region.is_active == True
            )
        ).all()
    
    def get_dltc_regions(self, db: Session) -> List[Region]:
        """Get all DLTC regions"""
        return db.query(Region).filter(
            and_(
                Region.user_group_type.in_([RegionType.FIXED_DLTC.value, RegionType.MOBILE_DLTC.value]),
                Region.is_active == True
            )
        ).all()
    
    def get_help_desk_regions(self, db: Session) -> List[Region]:
        """Get all help desk regions"""
        return db.query(Region).filter(
            and_(
                or_(
                    Region.is_provincial_help_desk == True,
                    Region.is_national_help_desk == True
                ),
                Region.is_active == True
            )
        ).all()
    
    def get_operational_regions(self, db: Session) -> List[Region]:
        """Get operationally valid regions"""
        return db.query(Region).filter(
            and_(
                Region.is_active == True,
                Region.registration_status == RegistrationStatus.REGISTERED.value,
                or_(
                    Region.suspended_until.is_(None),
                    Region.suspended_until <= func.now()
                )
            )
        ).all()
    
    def check_code_exists(self, db: Session, region_code: str, exclude_id: UUID = None) -> bool:
        """Check if region code already exists"""
        query = db.query(Region).filter(Region.user_group_code == region_code)
        if exclude_id:
            query = query.filter(Region.id != exclude_id)
        return query.first() is not None
    
    def get_children(self, db: Session, parent_id: UUID) -> List[Region]:
        """Get child regions"""
        return db.query(Region).filter(
            and_(
                Region.parent_region_id == parent_id,
                Region.is_active == True
            )
        ).all()
    
    def get_statistics(self, db: Session) -> Dict[str, Any]:
        """Get region statistics"""
        total = db.query(Region).count()
        active = db.query(Region).filter(Region.is_active == True).count()
        
        # Group by type
        type_stats = db.query(
            Region.user_group_type,
            func.count(Region.id).label('count')
        ).filter(Region.is_active == True).group_by(Region.user_group_type).all()
        
        # Group by province
        province_stats = db.query(
            Region.province_code,
            func.count(Region.id).label('count')
        ).filter(Region.is_active == True).group_by(Region.province_code).all()
        
        return {
            "total_regions": total,
            "active_regions": active,
            "regions_by_type": {stat.user_group_type: stat.count for stat in type_stats},
            "regions_by_province": {stat.province_code: stat.count for stat in province_stats}
        }

# Create instance for use in endpoints
region = RegionCRUD()

# Convenience functions for backward compatibility during migration
def region_create(db: Session, *, obj_in: RegionCreate, created_by: str = None) -> Region:
    return region.create(db=db, obj_in=obj_in, created_by=created_by)

def region_update(db: Session, *, db_obj: Region, obj_in: RegionUpdate, updated_by: str = None) -> Region:
    return region.update(db=db, db_obj=db_obj, obj_in=obj_in, updated_by=updated_by)

def region_delete(db: Session, *, id: UUID) -> Region:
    return region.delete(db=db, id=id) 