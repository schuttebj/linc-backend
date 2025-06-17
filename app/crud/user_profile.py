"""
User Profile CRUD Operations
Comprehensive CRUD operations for user profile management
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_, or_, desc, func
from fastapi import HTTPException, status
from passlib.context import CryptContext

from app.models.user_profile import UserProfile, UserSession, UserStatus, UserType
from app.models.user_group import UserGroup
from app.models.user import Role
from app.schemas.user_management import (
    UserProfileCreate, UserProfileUpdate, UserListFilter
)
from app.core.security import get_password_hash
# No base CRUD class needed - using standalone pattern

class CRUDUserProfile:
    """CRUD operations for User Profile management"""
    
    def __init__(self, model=UserProfile):
        self.model = model
    
    def create_user_profile(
        self,
        db: Session,
        *,
        user_data: UserProfileCreate,
        created_by: str = None
    ) -> UserProfile:
        """Create new user profile with validation"""
        
        # Check if username already exists
        existing_user = db.query(UserProfile).filter(
            UserProfile.username == user_data.username
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        
        # Check if email already exists
        existing_email = db.query(UserProfile).filter(
            UserProfile.email == user_data.personal_details.email
        ).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        
        # Generate user number
        user_number = self._generate_user_number(db, user_data.user_group_code)
        
        # Create user profile
        user_profile = UserProfile(
            username=user_data.username,
            password_hash=get_password_hash(user_data.password),
            user_group_code=user_data.user_group_code,
            office_code=user_data.office_code,
            user_name=user_data.user_name,
            user_type_code=user_data.user_type_code.value,
            user_number=user_number,
            
            # Personal details
            id_type=user_data.personal_details.id_type.value,
            id_number=user_data.personal_details.id_number,
            full_name=user_data.personal_details.full_name,
            email=user_data.personal_details.email,
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
            created_by=created_by
        )
        
        # Set user group relationship
        user_group = db.query(UserGroup).filter(
            UserGroup.user_group_code == user_data.user_group_code
        ).first()
        if user_group:
            user_profile.user_group_id = user_group.id
        
        db.add(user_profile)
        db.flush()
        
        # TODO: Assign roles when roles relationship is properly set up
        # if user_data.role_ids:
        #     self._assign_roles(db, user_profile, user_data.role_ids)
        
        db.commit()
        db.refresh(user_profile)
        
        return user_profile
    
    def get_user_profile(
        self,
        db: Session,
        user_id: str,
        load_relationships: bool = True
    ) -> Optional[UserProfile]:
        """Get user profile by ID"""
        query = db.query(UserProfile).filter(UserProfile.id == user_id)
        
        if load_relationships:
            query = query.options(
                selectinload(UserProfile.user_group)
                # TODO: Add other relationships when they are properly set up
                # selectinload(UserProfile.roles),
                # selectinload(UserProfile.location_assignments)
            )
        
        return query.first()
    
    def get_user_by_username(
        self,
        db: Session,
        username: str
    ) -> Optional[UserProfile]:
        """Get user profile by username"""
        return db.query(UserProfile).filter(UserProfile.username == username).first()
    
    def list_user_profiles(
        self,
        db: Session,
        *,
        filters: UserListFilter = None,
        page: int = 1,
        size: int = 20
    ) -> Tuple[List[UserProfile], int]:
        """List user profiles with filtering and pagination"""
        
        query = db.query(UserProfile).options(
            selectinload(UserProfile.user_group)
            # TODO: Add roles relationship when properly set up
            # selectinload(UserProfile.roles)
        )
        
        # Apply search filters
        if filters:
            query = self._apply_search_filters(query, filters)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * size
        users = query.order_by(UserProfile.created_at.desc()).offset(offset).limit(size).all()
        
        return users, total
    
    def _generate_user_number(self, db: Session, user_group_code: str) -> str:
        """Generate legacy user number format"""
        
        # Find the highest existing user number for this user group
        highest_user = db.query(UserProfile).filter(
            UserProfile.user_group_code == user_group_code,
            UserProfile.user_number.isnot(None)
        ).order_by(UserProfile.user_number.desc()).first()
        
        if highest_user and highest_user.user_number:
            try:
                sequence = int(highest_user.user_number[-3:]) + 1
            except (ValueError, IndexError):
                sequence = 1
        else:
            sequence = 1
        
        return f"{user_group_code}{sequence:03d}"
    
    def _assign_roles(
        self,
        db: Session,
        user_profile: UserProfile,
        role_ids: List[str]
    ):
        """Assign roles to user profile"""
        # TODO: Implement role assignment when roles relationship is set up
        # roles = db.query(Role).filter(
        #     Role.id.in_(role_ids),
        #     Role.is_active == True
        # ).all()
        # 
        # for role in roles:
        #     user_profile.roles.append(role)
        pass
    
    def _apply_search_filters(self, query, filters: UserListFilter):
        """Apply search filters to query"""
        
        if filters.status:
            query = query.filter(UserProfile.status == filters.status.value)
        
        if filters.is_active is not None:
            query = query.filter(UserProfile.is_active == filters.is_active)
        
        if filters.user_type:
            query = query.filter(UserProfile.user_type_code == filters.user_type.value)
        
        if filters.province_code:
            query = query.filter(UserProfile.province_code == filters.province_code)
        
        if filters.user_group_code:
            query = query.filter(UserProfile.user_group_code == filters.user_group_code)
        
        if filters.search:
            search_pattern = f"%{filters.search}%"
            query = query.filter(
                or_(
                    UserProfile.full_name.ilike(search_pattern),
                    UserProfile.username.ilike(search_pattern),
                    UserProfile.email.ilike(search_pattern)
                )
            )
        
        return query


# Create instance
user_profile = CRUDUserProfile()

# Export functions for compatibility
def user_profile_create(db: Session, *, obj_in: UserProfileCreate, created_by: str = None) -> UserProfile:
    return user_profile.create_user_profile(db, user_data=obj_in, created_by=created_by)

def user_profile_update(db: Session, *, db_obj: UserProfile, obj_in: UserProfileUpdate, updated_by: str = None) -> UserProfile:
    # Implementation for update
    pass

def user_profile_delete(db: Session, *, id: str) -> UserProfile:
    # Implementation for delete
    pass 