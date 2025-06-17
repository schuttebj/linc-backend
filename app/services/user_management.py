"""
User Management Service
Business logic layer for comprehensive user management
Consolidated to use existing User model with extended functionality
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import structlog

from app.models.user import User, UserSession, UserStatus, UserType, IDType
from app.models.location import UserGroup, Office
from app.schemas.user_management import (
    UserProfileCreate, UserProfileUpdate, UserListFilter,
    UserSessionCreate, UserStatistics
)
from app.crud.user_management import user_management
from app.core.security import get_password_hash

logger = structlog.get_logger()

class UserManagementService:
    """
    User Management Service
    
    Implements comprehensive user management business logic:
    - User profile lifecycle management
    - Business rule validation 
    - Permission-based data filtering
    - Session management
    - User statistics and reporting
    """
    
    def __init__(self):
        self.crud = user_management
    
    # ========================================
    # USER PROFILE MANAGEMENT
    # ========================================
    
    def create_user_profile(
        self,
        db: Session,
        user_data: UserProfileCreate,
        created_by: User
    ) -> User:
        """
        Create user profile with comprehensive validation
        
        Business Rules Implemented:
        - V06001: User Group must be active and valid
        - V06002: Office must exist within selected User Group
        - V06003: User Name must be unique within User Group
        - V06004: Email must be valid and unique system-wide
        - V06005: ID Number must be valid for selected ID Type
        """
        
        logger.info(
            "Starting user profile creation",
            username=user_data.username,
            user_group=user_data.user_group_code,
            created_by=created_by.username
        )
        
        # Validate business rules
        validation_result = self._validate_user_creation(db, user_data)
        if not validation_result['is_valid']:
            logger.warning(
                "User creation validation failed",
                username=user_data.username,
                errors=validation_result['validation_errors']
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "User validation failed",
                    "errors": validation_result['validation_errors'],
                    "validation_details": validation_result
                }
            )
        
        # Check creation permissions
        if not self._can_create_user(created_by, user_data):
            logger.warning(
                "Insufficient permissions for user creation",
                username=user_data.username,
                created_by=created_by.username,
                target_province=user_data.geographic_assignment.province_code
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to create user in specified province/user group"
            )
        
        # Create the user profile
        try:
            new_user = self.crud.create_user(
                db=db,
                user_data=user_data,
                created_by=created_by.username
            )
            
            logger.info(
                "User profile created successfully",
                user_id=str(new_user.id),
                username=new_user.username,
                user_group=new_user.user_group_code
            )
            
            return new_user
            
        except Exception as e:
            logger.error(
                "Error during user profile creation",
                username=user_data.username,
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user profile"
            )
    
    def get_user_profile(
        self,
        db: Session,
        user_id: str,
        current_user: User,
        load_relationships: bool = True
    ) -> Optional[User]:
        """Get user profile with permission validation"""
        
        user = self.crud.get_user(
            db=db,
            user_id=user_id,
            load_relationships=load_relationships
        )
        
        if not user:
            return None
        
        # Check if current user can access this user's data
        if not self._can_access_user_data(current_user, user):
            logger.warning(
                "Access denied to user profile",
                requested_user_id=user_id,
                current_user=current_user.username
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to user profile"
            )
        
        return user
    
    def list_user_profiles(
        self,
        db: Session,
        filters: UserListFilter,
        page: int,
        size: int,
        current_user: User
    ) -> Tuple[List[User], int]:
        """List user profiles with permission-based filtering"""
        
        # Apply permission-based filtering to the filters
        filtered_filters = self._apply_permission_filters(filters, current_user)
        
        return self.crud.list_users(
            db=db,
            filters=filtered_filters,
            page=page,
            size=size
        )
    
    def update_user_profile(
        self,
        db: Session,
        user_id: str,
        user_data: UserProfileUpdate,
        current_user: User
    ) -> User:
        """Update user profile with permission validation"""
        
        # Get existing user
        existing_user = self.get_user_profile(db, user_id, current_user)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        # Validate update permissions
        if not self._can_update_user(current_user, existing_user, user_data):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for requested updates"
            )
        
        # Perform update
        updated_user = self.crud.update_user(
            db=db,
            user_id=user_id,
            user_data=user_data,
            updated_by=current_user.username
        )
        
        return updated_user
    
    # ========================================
    # SESSION MANAGEMENT
    # ========================================
    
    def create_user_session(
        self,
        db: Session,
        user_id: str,
        session_data: UserSessionCreate,
        current_user: User
    ) -> UserSession:
        """
        Create user session with validation
        
        Implements validation rules:
        - V00468: Payments must exist for specified User and Workstation
        - User must be active and able to login
        - Workstation validation
        """
        
        # Get target user
        target_user = self.get_user_profile(db, user_id, current_user)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Validate user can create session
        if not self._can_user_login(target_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not able to login"
            )
        
        # Validate workstation (V00468 equivalent)
        if not self._validate_workstation_access(target_user, session_data.workstation_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User does not have access to specified workstation"
            )
        
        # Create session
        new_session = UserSession(
            user_id=target_user.id,
            user_group_code=session_data.user_group_code,
            user_number=session_data.user_number,
            workstation_id=session_data.workstation_id,
            session_type=session_data.session_type,
            ip_address=session_data.ip_address,
            user_agent=session_data.user_agent
        )
        
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        
        return new_session
    
    def get_user_statistics(
        self,
        db: Session,
        current_user: User
    ) -> UserStatistics:
        """Get user management statistics"""
        
        return self.crud.get_user_statistics(db=db)
    
    # ========================================
    # VALIDATION METHODS
    # ========================================
    
    def _validate_user_creation(
        self,
        db: Session,
        user_data: UserProfileCreate
    ) -> Dict[str, Any]:
        """
        Comprehensive user creation validation
        
        Implements business rules:
        - V06001: User Group must be active and valid
        - V06002: Office must exist within selected User Group
        - V06003: User Name must be unique within User Group
        - V06004: Email must be valid and unique system-wide
        - V06005: ID Number must be valid for selected ID Type
        """
        
        validation_result = {
            'is_valid': True,
            'validation_errors': [],
            'validation_warnings': []
        }
        
        # V06001: Validate User Group
        user_group = db.query(UserGroup).filter(
            UserGroup.user_group_code == user_data.user_group_code,
            UserGroup.is_active == True
        ).first()
        
        if not user_group:
            validation_result['is_valid'] = False
            validation_result['validation_errors'].append(
                "V06001: User Group must be active and valid"
            )
        
        # V06002: Validate Office within User Group
        if user_group:
            office = db.query(Office).filter(
                Office.office_code == user_data.office_code,
                Office.user_group_id == user_group.id,
                Office.is_active == True
            ).first()
            
            if not office:
                validation_result['is_valid'] = False
                validation_result['validation_errors'].append(
                    "V06002: Office must exist within selected User Group"
                )
        
        # V06003: Validate User Name uniqueness within User Group
        existing_user_name = db.query(User).filter(
            User.user_name == user_data.user_name,
            User.user_group_code == user_data.user_group_code
        ).first()
        
        if existing_user_name:
            validation_result['is_valid'] = False
            validation_result['validation_errors'].append(
                "V06003: User Name must be unique within User Group"
            )
        
        # V06004: Validate Email uniqueness system-wide
        existing_email = db.query(User).filter(
            User.email == user_data.personal_details.email
        ).first()
        
        if existing_email:
            validation_result['is_valid'] = False
            validation_result['validation_errors'].append(
                "V06004: Email must be valid and unique system-wide"
            )
        
        # V06005: Validate ID Number for ID Type
        id_validation = self._validate_id_number(
            user_data.personal_details.id_type,
            user_data.personal_details.id_number
        )
        
        if not id_validation['is_valid']:
            validation_result['is_valid'] = False
            validation_result['validation_errors'].append(
                "V06005: ID Number must be valid for selected ID Type"
            )
            validation_result['validation_errors'].extend(id_validation['errors'])
        
        # Username uniqueness
        existing_username = db.query(User).filter(
            User.username == user_data.username
        ).first()
        
        if existing_username:
            validation_result['is_valid'] = False
            validation_result['validation_errors'].append(
                "Username already exists"
            )
        
        return validation_result
    
    def _validate_id_number(
        self,
        id_type: IDType,
        id_number: str
    ) -> Dict[str, Any]:
        """
        Validate ID number based on type
        
        V06005: ID Number must be valid for selected ID Type
        """
        
        validation_result = {
            'is_valid': True,
            'errors': []
        }
        
        if id_type == IDType.SA_ID:
            # South African ID validation (13 digits)
            if not id_number.isdigit() or len(id_number) != 13:
                validation_result['is_valid'] = False
                validation_result['errors'].append("SA ID must be 13 digits")
            elif not self._validate_sa_id_check_digit(id_number):
                validation_result['is_valid'] = False
                validation_result['errors'].append("Invalid SA ID check digit")
        
        elif id_type == IDType.PASSPORT:
            # Passport validation (various formats)
            if len(id_number) < 4 or len(id_number) > 20:
                validation_result['is_valid'] = False
                validation_result['errors'].append("Passport number must be 4-20 characters")
        
        elif id_type == IDType.FOREIGN_ID:
            # Foreign ID validation (flexible)
            if len(id_number) < 5 or len(id_number) > 25:
                validation_result['is_valid'] = False
                validation_result['errors'].append("Foreign ID must be 5-25 characters")
        
        return validation_result
    
    def _validate_sa_id_check_digit(self, id_number: str) -> bool:
        """Validate South African ID check digit using Luhn algorithm"""
        if len(id_number) != 13 or not id_number.isdigit():
            return False
        
        # Luhn algorithm for SA ID validation
        total = 0
        for i in range(12):
            digit = int(id_number[i])
            if i % 2 == 1:
                digit *= 2
                if digit > 9:
                    digit = digit // 10 + digit % 10
            total += digit
        
        check_digit = (10 - (total % 10)) % 10
        return check_digit == int(id_number[12])
    
    def _can_create_user(
        self,
        creator: User,
        user_data: UserProfileCreate
    ) -> bool:
        """Check if creator can create user in specified location/group"""
        
        # Superusers can create anywhere
        if creator.is_superuser:
            return True
        
        # Provincial admins can create within their province
        if creator.authority_level == "PROVINCIAL":
            return creator.province_code == user_data.geographic_assignment.province_code
        
        # Local admins can create within their user group
        if creator.authority_level == "LOCAL":
            return creator.user_group_code == user_data.user_group_code
        
        # Regular users cannot create other users
        return False
    
    def _can_access_user_data(
        self,
        accessor: User,
        target_user: User
    ) -> bool:
        """Check if accessor can view target user's data"""
        
        # Users can always access their own data
        if accessor.id == target_user.id:
            return True
        
        # Superusers can access all data
        if accessor.is_superuser:
            return True
        
        # Provincial admins can access users in their province
        if accessor.authority_level == "PROVINCIAL":
            return accessor.province_code == target_user.province_code
        
        # Local admins can access users in their user group
        if accessor.authority_level == "LOCAL":
            return accessor.user_group_code == target_user.user_group_code
        
        # Regular users cannot access other users' data
        return False
    
    def _can_update_user(
        self,
        updater: User,
        target_user: User,
        update_data: UserProfileUpdate
    ) -> bool:
        """Check if updater can modify target user with given changes"""
        
        # Users can update their own basic information
        if updater.id == target_user.id:
            # Check if trying to update restricted fields
            restricted_fields = ['user_group_code', 'province_code', 'status', 'role_ids']
            for field in restricted_fields:
                if hasattr(update_data, field) and getattr(update_data, field) is not None:
                    return False
            return True
        
        # Admin users can update others
        return self._can_access_user_data(updater, target_user)
    
    def _can_user_login(self, user: User) -> bool:
        """Check if user can login"""
        return (
            user.is_active and 
            user.status in [UserStatus.ACTIVE, UserStatus.PENDING_ACTIVATION] and
            not user.is_locked
        )
    
    def _validate_workstation_access(
        self,
        user: User,
        workstation_id: str
    ) -> bool:
        """
        Validate user has access to workstation
        
        V00468: Payments must exist for specified User and Workstation
        """
        
        # TODO: Implement workstation validation logic
        # This would check:
        # - User has permission to use workstation
        # - Workstation is active and available
        # - Any licensing/payment requirements
        
        return True  # Placeholder - always allow for now
    
    def _apply_permission_filters(
        self,
        filters: UserListFilter,
        current_user: User
    ) -> UserListFilter:
        """Apply permission-based filtering to user list filters"""
        
        # Superusers see all users
        if current_user.is_superuser:
            return filters
        
        # Provincial admins see users in their province
        if current_user.authority_level == "PROVINCIAL":
            filters.province_code = current_user.province_code
        
        # Local admins see users in their user group
        elif current_user.authority_level == "LOCAL":
            filters.user_group_code = current_user.user_group_code
        
        # Regular users see only themselves
        else:
            filters.search = current_user.username
        
        return filters

# Create singleton instance
user_service = UserManagementService() 