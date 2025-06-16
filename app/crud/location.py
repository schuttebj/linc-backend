"""
Location CRUD Operations
Comprehensive database operations for location management
"""

from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from uuid import UUID
import math

from app.models.location import Location, InfrastructureType, OperationalStatus, LocationScope
from app.schemas.location import LocationCreate, LocationUpdate, LocationListFilter

class LocationCRUD:
    """CRUD operations for Location"""
    
    def __init__(self, model=Location):
        self.model = model
    
    def create(self, db: Session, *, obj_in: LocationCreate, created_by: str = None) -> Location:
        """Create a new location"""
        db_obj = Location(
            location_code=obj_in.location_code,
            location_name=obj_in.location_name,
            user_group_id=obj_in.user_group_id,
            office_id=obj_in.office_id,
            infrastructure_type=obj_in.infrastructure_type,
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
            location_scope=obj_in.location_scope,
            daily_capacity=obj_in.daily_capacity,
            current_load=obj_in.current_load,
            max_concurrent_operations=obj_in.max_concurrent_operations,
            contact_person=obj_in.contact_person,
            phone_number=obj_in.phone_number,
            email=obj_in.email,
            is_active=obj_in.is_active,
            is_public=obj_in.is_public,
            requires_appointment=obj_in.requires_appointment,
            created_by=created_by
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get(self, db: Session, id: UUID) -> Optional[Location]:
        """Get location by ID"""
        return db.query(Location).filter(Location.id == id).first()
    
    def get_by_code(self, db: Session, location_code: str) -> Optional[Location]:
        """Get location by code"""
        return db.query(Location).filter(Location.location_code == location_code).first()
    
    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[LocationListFilter] = None
    ) -> List[Location]:
        """Get multiple locations with optional filtering"""
        query = db.query(Location)
        
        if filters:
            if filters.province_code:
                query = query.filter(Location.province_code == filters.province_code)
            
            if filters.infrastructure_type:
                query = query.filter(Location.infrastructure_type == filters.infrastructure_type)
            
            if filters.operational_status:
                query = query.filter(Location.operational_status == filters.operational_status)
            
            if filters.user_group_id:
                query = query.filter(Location.user_group_id == filters.user_group_id)
            
            if filters.is_active is not None:
                query = query.filter(Location.is_active == filters.is_active)
            
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        Location.location_code.ilike(search_term),
                        Location.location_name.ilike(search_term),
                        Location.city.ilike(search_term)
                    )
                )
        
        return query.order_by(Location.location_code).offset(skip).limit(limit).all()
    
    def update(
        self, 
        db: Session, 
        *, 
        db_obj: Location, 
        obj_in: LocationUpdate,
        updated_by: str = None
    ) -> Location:
        """Update location"""
        update_data = obj_in.dict(exclude_unset=True)
        if updated_by:
            update_data["updated_by"] = updated_by
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, *, id: UUID) -> Location:
        """Soft delete location"""
        obj = db.query(Location).get(id)
        if obj:
            obj.is_active = False
            db.add(obj)
            db.commit()
        return obj
    
    def get_by_province(self, db: Session, province_code: str) -> List[Location]:
        """Get all locations in a province"""
        return db.query(Location).filter(
            and_(
                Location.province_code == province_code,
                Location.is_active == True
            )
        ).all()
    
    def get_by_user_group(self, db: Session, user_group_id: UUID) -> List[Location]:
        """Get all locations for a user group"""
        return db.query(Location).filter(
            and_(
                Location.user_group_id == user_group_id,
                Location.is_active == True
            )
        ).all()
    
    def get_dltc_locations(self, db: Session) -> List[Location]:
        """Get all DLTC locations"""
        return db.query(Location).filter(
            and_(
                Location.infrastructure_type.in_([
                    InfrastructureType.FIXED_DLTC.value,
                    InfrastructureType.MOBILE_DLTC.value
                ]),
                Location.is_active == True
            )
        ).all()
    
    def get_printing_locations(self, db: Session) -> List[Location]:
        """Get all printing locations"""
        return db.query(Location).filter(
            and_(
                Location.infrastructure_type.in_([
                    InfrastructureType.PRINTING_CENTER.value,
                    InfrastructureType.COMBINED_CENTER.value
                ]),
                Location.is_active == True
            )
        ).all()
    
    def get_operational_locations(self, db: Session) -> List[Location]:
        """Get operationally active locations"""
        return db.query(Location).filter(
            and_(
                Location.is_active == True,
                Location.operational_status == OperationalStatus.OPERATIONAL.value
            )
        ).all()
    
    def get_public_locations(self, db: Session) -> List[Location]:
        """Get public-facing locations"""
        return db.query(Location).filter(
            and_(
                Location.is_active == True,
                Location.is_public == True,
                Location.operational_status == OperationalStatus.OPERATIONAL.value
            )
        ).all()
    
    def get_locations_with_capacity(self, db: Session, min_capacity: int = 1) -> List[Location]:
        """Get locations with available capacity"""
        return db.query(Location).filter(
            and_(
                Location.is_active == True,
                Location.operational_status == OperationalStatus.OPERATIONAL.value,
                Location.daily_capacity >= min_capacity,
                Location.current_load < Location.daily_capacity
            )
        ).all()
    
    def get_nearby_locations(
        self, 
        db: Session, 
        latitude: float, 
        longitude: float, 
        radius_km: float = 50
    ) -> List[Tuple[Location, float]]:
        """Get locations within specified radius with distance"""
        locations = db.query(Location).filter(
            and_(
                Location.is_active == True,
                Location.latitude.isnot(None),
                Location.longitude.isnot(None)
            )
        ).all()
        
        nearby_locations = []
        for location in locations:
            distance = self._calculate_distance(
                latitude, longitude,
                float(location.latitude), float(location.longitude)
            )
            if distance <= radius_km:
                nearby_locations.append((location, distance))
        
        # Sort by distance
        nearby_locations.sort(key=lambda x: x[1])
        return nearby_locations
    
    def get_locations_by_city(self, db: Session, city: str) -> List[Location]:
        """Get locations in a specific city"""
        return db.query(Location).filter(
            and_(
                Location.city.ilike(f"%{city}%"),
                Location.is_active == True
            )
        ).all()
    
    def update_load(self, db: Session, location_id: UUID, new_load: int) -> Optional[Location]:
        """Update current load for a location"""
        location = self.get(db, location_id)
        if location:
            location.current_load = new_load
            db.add(location)
            db.commit()
            db.refresh(location)
        return location
    
    def check_code_exists(self, db: Session, location_code: str, exclude_id: UUID = None) -> bool:
        """Check if location code already exists"""
        query = db.query(Location).filter(Location.location_code == location_code)
        if exclude_id:
            query = query.filter(Location.id != exclude_id)
        return query.first() is not None
    
    def get_statistics(self, db: Session) -> Dict[str, Any]:
        """Get location statistics"""
        total = db.query(Location).count()
        operational = db.query(Location).filter(
            Location.operational_status == OperationalStatus.OPERATIONAL.value
        ).count()
        
        # Calculate average capacity utilization
        locations_with_capacity = db.query(Location).filter(
            and_(
                Location.daily_capacity > 0,
                Location.is_active == True
            )
        ).all()
        
        if locations_with_capacity:
            total_capacity = sum(loc.daily_capacity for loc in locations_with_capacity)
            total_load = sum(loc.current_load or 0 for loc in locations_with_capacity)
            avg_utilization = (total_load / total_capacity * 100) if total_capacity > 0 else 0
        else:
            total_capacity = 0
            avg_utilization = 0
        
        # Group by type
        type_stats = db.query(
            Location.infrastructure_type,
            func.count(Location.id).label('count')
        ).filter(Location.is_active == True).group_by(Location.infrastructure_type).all()
        
        # Group by province
        province_stats = db.query(
            Location.province_code,
            func.count(Location.id).label('count')
        ).filter(Location.is_active == True).group_by(Location.province_code).all()
        
        return {
            "total_locations": total,
            "operational_locations": operational,
            "capacity_utilization_avg": round(avg_utilization, 2),
            "total_daily_capacity": total_capacity,
            "locations_by_type": {stat.infrastructure_type: stat.count for stat in type_stats},
            "locations_by_province": {stat.province_code: stat.count for stat in province_stats}
        }
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates using Haversine formula"""
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

# Create instance
location = LocationCRUD(Location) 