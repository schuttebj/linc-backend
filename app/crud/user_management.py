"""
User Management CRUD Operations
Consolidated CRUD operations for user management using the existing User model
Replaces the duplicate UserProfile model with extended User model functionality
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_, or_, desc, func
from fastapi import HTTPException, status
from passlib.context import CryptContext
import structlog

from app.models.user import User, UserSession, UserStatus, IDType
from app.models.user_type import UserType
from app.models.region import Region
from app.schemas.user_management import (
    UserProfileCreate, UserProfileUpdate, UserListFilter
)
from app.core.security import get_password_hash

logger = structlog.get_logger()

class CRUDUserManagement:
    """CRUD operations for comprehensive user management"""
    
    def __init__(self, model=User):
        self.model = model
    
    def create_user(
        self,
        db: Session,
        *,
        user_data: UserProfileCreate,
        created_by: str = None
    ) -> User:
        """Create new user with validation (V06001-V06005)"""
        
        # V06003: Check if username already exists
        existing_user = db.query(User).filter(
            User.username == user_data.username
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="V06003: Username already exists"
            )
        
        # V06004: Check if email already exists
        existing_email = db.query(User).filter(
            User.email == user_data.personal_details.email
        ).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="V06004: Email already exists"
            )
        
        # V06001: Validate region if provided
        region = None
        user_number = None
        if user_data.user_group_code:
            region = db.query(Region).filter(
                Region.user_group_code == user_data.user_group_code,
                Region.is_active == True
            ).first()
            if not region:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="V06001: Region must be active and valid"
                )
            # Generate user number
            user_number = self._generate_user_number(db, user_data.user_group_code)
        
        # Create user
        user = User(
            # Authentication
            username=user_data.username,
            password_hash=get_password_hash(user_data.password),
            email=user_data.personal_details.email,
            
            # Core user fields
            user_group_code=user_data.user_group_code,
            office_code=user_data.office_code,
            user_name=user_data.user_name,
            user_type_code=user_data.user_type_code.value,
            user_number=user_number,
            
            # Personal details
            id_type=user_data.personal_details.id_type.value,
            id_number=user_data.personal_details.id_number,
            full_name=user_data.personal_details.full_name,
            phone_number=user_data.personal_details.phone_number,
            alternative_phone=user_data.personal_details.alternative_phone,
            
            # Geographic assignment
            country_code=user_data.geographic_assignment.country_code,
            province_code=user_data.geographic_assignment.province_code,
            region=user_data.geographic_assignment.region,
            
            # Job details
            employee_id=user_data.employee_id,
            department=user_data.department,
            job_title=user_data.job_title,
            infrastructure_number=user_data.infrastructure_number,
            
            # System settings
            language=user_data.language,
            timezone=user_data.timezone,
            date_format=user_data.date_format,
            
            # Status
            status=user_data.status.value,
            is_active=user_data.is_active,
            
            # Security
            require_password_change=user_data.require_password_change,
            require_2fa=user_data.require_2fa,
            
            # Audit
            created_by=created_by,
            region_id=region.id if region else None
        )
        
        db.add(user)
        db.flush()
        
        # TODO: Implement new permission system assignments here
        # Legacy role assignment removed - use new permission system
        # if user_data.permission_assignments:
        #     # Assign regions, offices, and permission overrides
        #     pass
        
        db.commit()
        db.refresh(user)
        
        return user
    
    def get_user(
        self,
        db: Session,
        user_id: str,
        load_relationships: bool = True
    ) -> Optional[User]:
        """Get user by ID"""
        query = db.query(User).filter(User.id == user_id)
        
        if load_relationships:
            query = query.options(
                selectinload(User.region),
                selectinload(User.location_assignments)
            )
        
        return query.first()
    
    def get_user_by_username(
        self,
        db: Session,
        username: str
    ) -> Optional[User]:
        """Get user by username"""
        return db.query(User).filter(User.username == username).first()
    
    def list_users(
        self,
        db: Session,
        *,
        filters: UserListFilter = None,
        page: int = 1,
        size: int = 20
    ) -> Tuple[List[User], int]:
        """List users with filtering and pagination"""
        
        query = db.query(User).options(
            selectinload(User.region)
        )
        
        # Apply search filters
        if filters:
            query = self._apply_search_filters(query, filters)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * size
        users = query.order_by(User.created_at.desc()).offset(offset).limit(size).all()
        
        return users, total
    
    def search_users(
        self,
        db: Session,
        *,
        search_term: str,
        limit: int = 50,
        exclude_assigned_to_location: Optional[str] = None,
        user_type_filter: Optional[str] = None
    ) -> List[User]:
        """Search users for staff assignment with enhanced filtering"""
        
        try:
            # Start with basic query - no eager loading to avoid relationship issues
            query = db.query(User)
            
            # Build search filters with null checks
            search_filters = []
            
            # Add search conditions with proper null handling
            if User.full_name:
                search_filters.append(User.full_name.ilike(f"%{search_term}%"))
            if User.username:
                search_filters.append(User.username.ilike(f"%{search_term}%"))
            if User.email:
                search_filters.append(User.email.ilike(f"%{search_term}%"))
            if User.employee_id:
                search_filters.append(User.employee_id.ilike(f"%{search_term}%"))
            if User.user_name:
                search_filters.append(User.user_name.ilike(f"%{search_term}%"))
            
            # Apply search filter
            if search_filters:
                query = query.filter(or_(*search_filters))
            
            # Filter by user type if specified
            if user_type_filter:
                query = query.filter(User.user_type_code == user_type_filter)
            
            # Exclude users already assigned to specific location (simplified)
            if exclude_assigned_to_location:
                try:
                    from app.models.user_location_assignment import UserLocationAssignment
                    assigned_user_ids = db.query(UserLocationAssignment.user_id).filter(
                        UserLocationAssignment.location_id == exclude_assigned_to_location,
                        UserLocationAssignment.is_active == True
                    ).subquery()
                    query = query.filter(~User.id.in_(assigned_user_ids))
                except Exception as e:
                    # If location assignment filtering fails, continue without it
                    logger.warning(f"Location assignment filtering failed: {e}")
            
            # Only active users
            query = query.filter(User.is_active == True)
            
            # Simple ordering
            query = query.order_by(User.username.asc())
            
            # Execute query with limit
            return query.limit(limit).all()
            
        except Exception as e:
            logger.error(f"Error in search_users: {e}")
            # Return empty list on error rather than failing
            return []
    
    def update_user(
        self,
        db: Session,
        *,
        user_id: str,
        user_data: UserProfileUpdate,
        updated_by: str = None
    ) -> User:
        """Update user profile"""
        user = self.get_user(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update fields that are provided
        update_data = user_data.dict(exclude_unset=True)
        
        # Handle nested personal_details
        if 'personal_details' in update_data and update_data['personal_details']:
            personal_details = update_data.pop('personal_details')
            for field, value in personal_details.items():
                if hasattr(user, field):
                    setattr(user, field, value)
        
        # Handle other updates
        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        if updated_by:
            user.updated_by = updated_by
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    def _generate_user_number(self, db: Session, user_group_code: str) -> str:
        """Generate legacy user number format"""
        
        # Find the highest existing user number for this user group
        highest_user = db.query(User).filter(
            User.user_group_code == user_group_code,
            User.user_number.isnot(None)
        ).order_by(User.user_number.desc()).first()
        
        if highest_user and highest_user.user_number:
            try:
                sequence = int(highest_user.user_number[-3:]) + 1
            except (ValueError, IndexError):
                sequence = 1
        else:
            sequence = 1
        
        return f"{user_group_code}{sequence:03d}"
    
    def _apply_search_filters(self, query, filters: UserListFilter):
        """Apply search filters to query"""
        
        if filters.status:
            query = query.filter(User.status == filters.status.value)
        
        if filters.is_active is not None:
            query = query.filter(User.is_active == filters.is_active)
        
        if filters.user_type:
            query = query.filter(User.user_type_code == filters.user_type.value)
        
        if filters.province_code:
            query = query.filter(User.province_code == filters.province_code)
        
        if filters.user_group_code:
            query = query.filter(User.user_group_code == filters.user_group_code)
        
        if filters.office_code:
            query = query.filter(User.office_code == filters.office_code)
        
        if filters.department:
            query = query.filter(User.department.ilike(f"%{filters.department}%"))
        
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.filter(
                or_(
                    User.username.ilike(search_term),
                    User.full_name.ilike(search_term),
                    User.email.ilike(search_term),
                    User.user_name.ilike(search_term)
                )
            )
        
        if filters.created_after:
            query = query.filter(User.created_at >= filters.created_after)
        
        if filters.created_before:
            query = query.filter(User.created_at <= filters.created_before)
        
        if filters.last_login_after:
            query = query.filter(User.last_login_at >= filters.last_login_after)
        
        if filters.last_login_before:
            query = query.filter(User.last_login_at <= filters.last_login_before)
        
        return query
    
    def get_user_statistics(self, db: Session) -> Dict[str, Any]:
        """Get user management statistics"""
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        
        # Status distribution
        status_stats = db.query(
            User.status,
            func.count(User.id).label('count')
        ).group_by(User.status).all()
        
        # User type distribution
        type_stats = db.query(
            User.user_type_code,
            func.count(User.id).label('count')
        ).filter(User.is_active == True).group_by(User.user_type_code).all()
        
        # Province distribution
        province_stats = db.query(
            User.province_code,
            func.count(User.id).label('count')
        ).filter(User.is_active == True).group_by(User.province_code).all()
        
        # User group distribution
        user_group_stats = db.query(
            User.user_group_code,
            func.count(User.id).label('count')
        ).filter(User.is_active == True).group_by(User.user_group_code).all()
        
        # Recent activity
        thirty_days_ago = datetime.now() - timedelta(days=30)
        new_users_this_month = db.query(User).filter(
            User.created_at >= thirty_days_ago
        ).count()
        
        twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
        recent_logins = db.query(User).filter(
            User.last_login_at >= twenty_four_hours_ago
        ).count()
        
        active_sessions = db.query(UserSession).filter(
            UserSession.is_active == True,
            UserSession.session_expiry > func.now()
        ).count()
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "by_status": {stat.status: stat.count for stat in status_stats},
            "by_user_type": {stat.user_type_code: stat.count for stat in type_stats},
            "by_province": {stat.province_code: stat.count for stat in province_stats},
            "by_user_group": {stat.user_group_code: stat.count for stat in user_group_stats},
            "new_users_this_month": new_users_this_month,
            "recent_logins": recent_logins,
            "active_sessions": active_sessions
        }

# Create instance
user_management = CRUDUserManagement() 