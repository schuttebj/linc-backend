"""
Office CRUD Operations
Comprehensive database operations for office management
Merged from Location model - represents physical offices where services are provided
"""

from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from uuid import UUID
import math

from app.models.office import Office, InfrastructureType, OperationalStatus, OfficeScope
from app.schemas.office import OfficeCreate, OfficeUpdate, OfficeListFilter

class OfficeCRUD:
    """CRUD operations for Office"""
    
    def __init__(self, model=Office):
        self.model = model
    
    def create(self, db: Session, *, obj_in: OfficeCreate, created_by: str = None) -> Office:
        """Create a new office"""
        db_obj = Office(
            office_code=obj_in.office_code,
            office_name=obj_in.office_name,
            region_id=obj_in.region_id,
            infrastructure_type=obj_in.infrastructure_type,
            office_type=obj_in.office_type,
            address_line_1=obj_in.address_line_1,
            address_line_2=obj_in.address_line_2,
            address_line_3=obj_in.address_line_3,
            city=obj_in.city,
            province_code=obj_in.province_code,
            postal_code=obj_in.postal_code,
            country_code=obj_in.country_code,
            latitude=obj_in.latitude,
            longitude=obj_in.longitude,
            operational_status=obj_in.operational_status,
            office_scope=obj_in.office_scope,
            daily_capacity=obj_in.daily_capacity,
            current_load=obj_in.current_load,
            max_concurrent_operations=obj_in.max_concurrent_operations,
            staff_count=obj_in.staff_count,
            contact_person=obj_in.contact_person,
            phone_number=obj_in.phone_number,
            email=obj_in.email,
            is_active=obj_in.is_active,
            is_public=obj_in.is_public,
            is_operational=obj_in.is_operational,
            requires_appointment=obj_in.requires_appointment,
            created_by=created_by
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get(self, db: Session, id: UUID) -> Optional[Office]:
        """Get office by ID"""
        return db.query(Office).filter(Office.id == id).first()
    
    def get_by_code(self, db: Session, region_id: UUID, office_code: str) -> Optional[Office]:
        """Get office by region and office code"""
        return db.query(Office).filter(
            and_(
                Office.region_id == region_id,
                Office.office_code == office_code
            )
        ).first()
    
    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[OfficeListFilter] = None
    ) -> List[Office]:
        """Get multiple offices with optional filtering"""
        query = db.query(Office)
        
        if filters:
            if filters.province_code:
                query = query.filter(Office.province_code == filters.province_code)
            
            if filters.infrastructure_type:
                query = query.filter(Office.infrastructure_type == filters.infrastructure_type)
            
            if filters.office_type:
                query = query.filter(Office.office_type == filters.office_type)
            
            if filters.operational_status:
                query = query.filter(Office.operational_status == filters.operational_status)
            
            if filters.region_id:
                query = query.filter(Office.region_id == filters.region_id)
            
            if filters.is_active is not None:
                query = query.filter(Office.is_active == filters.is_active)
            
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        Office.office_code.ilike(search_term),
                        Office.office_name.ilike(search_term),
                        Office.city.ilike(search_term)
                    )
                )
        
        return query.order_by(Office.office_code).offset(skip).limit(limit).all()
    
    def update(
        self, 
        db: Session, 
        *, 
        db_obj: Office, 
        obj_in: OfficeUpdate,
        updated_by: str = None
    ) -> Office:
        """Update office"""
        update_data = obj_in.dict(exclude_unset=True)
        if updated_by:
            update_data["updated_by"] = updated_by
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, *, id: UUID) -> Office:
        """Soft delete office"""
        obj = db.query(Office).get(id)
        if obj:
            obj.is_active = False
            db.add(obj)
            db.commit()
        return obj
    
    def get_by_province(self, db: Session, province_code: str) -> List[Office]:
        """Get all offices in a province"""
        return db.query(Office).filter(
            and_(
                Office.province_code == province_code,
                Office.is_active == True
            )
        ).all()
    
    def get_by_region(self, db: Session, region_id: UUID) -> List[Office]:
        """Get all offices for a region"""
        return db.query(Office).filter(
            and_(
                Office.region_id == region_id,
                Office.is_active == True
            )
        ).all()
    
    def get_by_infrastructure_type(self, db: Session, infrastructure_types: List[str]) -> List[Office]:
        """Get offices by infrastructure type(s)"""
        return db.query(Office).filter(
            and_(
                Office.infrastructure_type.in_(infrastructure_types),
                Office.is_active == True
            )
        ).all()
    
    def get_dltc_offices(self, db: Session) -> List[Office]:
        """Get all DLTC offices"""
        return db.query(Office).filter(
            and_(
                Office.infrastructure_type.in_([
                    InfrastructureType.FIXED_DLTC.value,
                    InfrastructureType.MOBILE_DLTC.value
                ]),
                Office.is_active == True
            )
        ).all()
    
    def get_printing_offices(self, db: Session) -> List[Office]:
        """Get all printing offices"""
        return db.query(Office).filter(
            and_(
                Office.infrastructure_type.in_([
                    InfrastructureType.PRINTING_CENTER.value,
                    InfrastructureType.COMBINED_CENTER.value
                ]),
                Office.is_active == True
            )
        ).all()
    
    def get_operational(self, db: Session) -> List[Office]:
        """Get operationally active offices"""
        return db.query(Office).filter(
            and_(
                Office.is_active == True,
                Office.is_operational == True,
                Office.operational_status == OperationalStatus.OPERATIONAL.value
            )
        ).all()
    
    def get_public(self, db: Session) -> List[Office]:
        """Get public-facing offices"""
        return db.query(Office).filter(
            and_(
                Office.is_active == True,
                Office.is_public == True,
                Office.is_operational == True,
                Office.operational_status == OperationalStatus.OPERATIONAL.value
            )
        ).all()
    
    def get_with_capacity(self, db: Session, min_capacity: int = 1) -> List[Office]:
        """Get offices with available capacity"""
        return db.query(Office).filter(
            and_(
                Office.is_active == True,
                Office.is_operational == True,
                Office.operational_status == OperationalStatus.OPERATIONAL.value,
                Office.daily_capacity >= min_capacity,
                Office.current_load < Office.daily_capacity
            )
        ).all()
    
    def get_nearby_offices(
        self, 
        db: Session, 
        latitude: float, 
        longitude: float, 
        radius_km: float = 50
    ) -> List[Tuple[Office, float]]:
        """Get offices within a radius of coordinates"""
        offices = db.query(Office).filter(
            and_(
                Office.is_active == True,
                Office.latitude.isnot(None),
                Office.longitude.isnot(None)
            )
        ).all()
        
        nearby_offices = []
        for office in offices:
            distance = self._calculate_distance(
                latitude, longitude,
                float(office.latitude), float(office.longitude)
            )
            if distance <= radius_km:
                nearby_offices.append((office, distance))
        
        # Sort by distance
        nearby_offices.sort(key=lambda x: x[1])
        return nearby_offices
    
    def get_by_city(self, db: Session, city: str) -> List[Office]:
        """Get offices by city"""
        return db.query(Office).filter(
            and_(Office.city.ilike(f"%{city}%"), Office.is_active == True)
        ).all()
    
    def update_load(self, db: Session, office_id: UUID, new_load: int) -> Optional[Office]:
        """Update office current load"""
        office = db.query(Office).get(office_id)
        if office:
            office.current_load = new_load
            db.commit()
            db.refresh(office)
        return office
    
    def check_code_exists(self, db: Session, region_id: UUID, office_code: str, exclude_id: UUID = None) -> bool:
        """Check if office code exists in region"""
        query = db.query(Office).filter(
            and_(
                Office.region_id == region_id,
                Office.office_code == office_code
            )
        )
        if exclude_id:
            query = query.filter(Office.id != exclude_id)
        return query.first() is not None
    
    def get_statistics(self, db: Session) -> Dict[str, Any]:
        """Get office statistics"""
        total_offices = db.query(Office).count()
        active_offices = db.query(Office).filter(Office.is_active == True).count()
        operational_offices = db.query(Office).filter(
            and_(
                Office.is_active == True,
                Office.is_operational == True,
                Office.operational_status == OperationalStatus.OPERATIONAL.value
            )
        ).count()
        
        # Statistics by infrastructure type
        infrastructure_stats = {}
        for infra_type in InfrastructureType:
            count = db.query(Office).filter(
                and_(
                    Office.infrastructure_type == infra_type.value,
                    Office.is_active == True
                )
            ).count()
            infrastructure_stats[infra_type.name] = count
        
        # Statistics by province
        province_stats = db.query(
            Office.province_code,
            func.count(Office.id).label('count')
        ).filter(
            Office.is_active == True
        ).group_by(Office.province_code).all()
        
        province_dict = {stat.province_code: stat.count for stat in province_stats}
        
        # Capacity statistics
        total_capacity = db.query(
            func.sum(Office.daily_capacity)
        ).filter(Office.is_active == True).scalar() or 0
        
        total_load = db.query(
            func.sum(Office.current_load)
        ).filter(Office.is_active == True).scalar() or 0
        
        return {
            "total_offices": total_offices,
            "active_offices": active_offices,
            "operational_offices": operational_offices,
            "infrastructure_types": infrastructure_stats,
            "provinces": province_dict,
            "capacity": {
                "total_capacity": total_capacity,
                "current_load": total_load,
                "utilization_percentage": (total_load / total_capacity * 100) if total_capacity > 0 else 0
            }
        }
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates using Haversine formula"""
        # Convert latitude and longitude to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        
        return c * r

# Create instance
office = OfficeCRUD()

# Helper functions for backward compatibility
def office_create(db: Session, *, obj_in: OfficeCreate, created_by: str = None) -> Office:
    return office.create(db=db, obj_in=obj_in, created_by=created_by)

def office_update(db: Session, *, db_obj: Office, obj_in: OfficeUpdate, updated_by: str = None) -> Office:
    return office.update(db=db, db_obj=db_obj, obj_in=obj_in, updated_by=updated_by)

def office_delete(db: Session, *, id: UUID) -> Office:
    return office.delete(db=db, id=id) 