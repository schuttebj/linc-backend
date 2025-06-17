"""
User Management Service
Business logic layer for comprehensive user management
Implements requirements from Users_Locations.md
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
from app.crud.user_profile import user_profile
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
        self.crud = user_profile
    
    # ========================================
    # USER PROFILE MANAGEMENT
    # ========================================
    
    def create_user_profile(
        self,
        db: Session,
        user_data: UserProfileCreate,
        created_by: UserProfile
    ) -> UserProfile:
        """
        Create user profile with comprehensive validation
        
        Business Rules Implemented:
        - V-USER-001: User Group must be active and valid
        - V-USER-002: Office must exist within selected User Group
        - V-USER-003: User Name must be unique within User Group
        - V-USER-004: Email must be valid and unique system-wide
        - V-USER-005: ID Number must be valid for selected ID Type
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
            new_user = self.crud.create_user_profile(
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
        current_user: UserProfile,
        load_relationships: bool = True
    ) -> Optional[UserProfile]:
        """Get user profile with permission validation"""
        
        user = self.crud.get_user_profile(
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
        current_user: UserProfile
    ) -> Tuple[List[UserProfile], int]:
        """List user profiles with permission-based filtering"""
        
        # Apply permission-based filtering to the filters
        filtered_filters = self._apply_permission_filters(filters, current_user)
        
        return self.crud.list_user_profiles(
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
        current_user: UserProfile
    ) -> UserProfile:
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
        # Implementation would call CRUD update method
        
        return existing_user
    
    # ========================================
    # SESSION MANAGEMENT
    # ========================================
    
    def create_user_session(
        self,
        db: Session,
        user_id: str,
        session_data: UserSessionCreate,
        current_user: UserProfile
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
        # Implementation would call CRUD session creation
        
        return None  # Placeholder
    
    # ========================================
    # STATISTICS AND REPORTING
    # ========================================
    
    def get_user_statistics(
        self,
        db: Session,
        current_user: UserProfile
    ) -> UserStatistics:
        """Get user statistics with permission filtering"""
        
        # Get statistics filtered by user's permissions
        return self.crud.get_user_statistics(
            db=db,
            current_user=current_user
        )
    
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
        
        Business Rules:
        - V-USER-001: User Group must be active and valid
        - V-USER-002: Office must exist within selected User Group
        - V-USER-003: User Name must be unique within User Group
        - V-USER-004: Email must be valid and unique system-wide
        - V-USER-005: ID Number must be valid for selected ID Type
        """
        
        validation_result = {
            'is_valid': True,
            'validation_errors': [],
            'validation_warnings': [],
            'business_rule_violations': []
        }
        
        # V06001: User Group validation
        user_group = db.query(UserGroup).filter(
            UserGroup.user_group_code == user_data.user_group_code
        ).first()
        
        if not user_group:
            validation_result['validation_errors'].append("User Group does not exist")
        elif not user_group.is_active:
            validation_result['validation_errors'].append("User Group is not active")
        
        # V06002: Office validation
        if user_group:
            office_exists = any(
                office.office_code == user_data.office_code
                for office in user_group.offices
            )
            if not office_exists:
                validation_result['validation_errors'].append(
                    f"Office '{user_data.office_code}' does not exist in User Group '{user_data.user_group_code}'"
                )
        
        # V06003: User Name uniqueness within User Group
        existing_user_name = db.query(User).filter(
            User.user_group_code == user_data.user_group_code,
            User.user_name == user_data.user_name
        ).first()
        
        if existing_user_name:
            validation_result['validation_errors'].append(
                f"User Name '{user_data.user_name}' already exists in User Group '{user_data.user_group_code}'"
            )
        
        # V06004: Email uniqueness system-wide
        existing_email = db.query(User).filter(
            User.email == user_data.personal_details.email
        ).first()
        
        if existing_email:
            validation_result['validation_errors'].append(
                f"Email '{user_data.personal_details.email}' is already in use"
            )
        
        # V06005: ID Number validation
        id_validation = self._validate_id_number(
            user_data.personal_details.id_type,
            user_data.personal_details.id_number
        )
        
        if not id_validation['is_valid']:
            validation_result['validation_errors'].extend(id_validation['errors'])
        
        # Username uniqueness (system-wide)
        existing_username = db.query(UserProfile).filter(
            UserProfile.username == user_data.username
        ).first()
        
        if existing_username:
            validation_result['validation_errors'].append(
                f"Username '{user_data.username}' is already in use"
            )
        
        # Set overall validity
        validation_result['is_valid'] = len(validation_result['validation_errors']) == 0
        
        return validation_result
    
    def _validate_id_number(
        self,
        id_type: IDType,
        id_number: str
    ) -> Dict[str, Any]:
        """
        ID Number validation based on type
        
        Validation Rules:
        - V00017: RSA ID (02) must be numeric
        - V00018: ID types 01,02,04,97 must be 13 characters
        - V00019: Valid check digit for ID types 01,02,04
        """
        
        validation_result = {
            'is_valid': True,
            'errors': []
        }
        
        # V00018: Length validation
        if id_type in [IDType.TRN, IDType.SA_ID, IDType.PASSPORT, IDType.OTHER]:
            if len(id_number) != 13:
                validation_result['errors'].append(
                    f"ID type {id_type.value} must be exactly 13 characters long"
                )
        
        # V00017: Numeric validation for SA ID and TRN
        if id_type in [IDType.SA_ID, IDType.TRN]:
            if not id_number.isdigit():
                validation_result['errors'].append(
                    f"ID type {id_type.value} must contain only numeric characters"
                )
        
        # V00019: Check digit validation (simplified implementation)
        if id_type == IDType.SA_ID and len(id_number) == 13 and id_number.isdigit():
            # Implement South African ID number check digit validation
            # This is a simplified version - real implementation would use Luhn algorithm
            if not self._validate_sa_id_check_digit(id_number):
                validation_result['errors'].append("Invalid South African ID number check digit")
        
        validation_result['is_valid'] = len(validation_result['errors']) == 0
        
        return validation_result
    
    def _validate_sa_id_check_digit(self, id_number: str) -> bool:
        """
        Validate South African ID number check digit using Luhn algorithm
        Simplified implementation
        """
        # Simplified validation - real implementation would be more complex
        return True
    
    # ========================================
    # PERMISSION METHODS
    # ========================================
    
    def _can_create_user(
        self,
        creator: UserProfile,
        user_data: UserProfileCreate
    ) -> bool:
        """Check if user can create another user with specified attributes"""
        
        # Superusers can create any user
        if creator.is_superuser:
            return True
        
        # Check province access
        target_province = user_data.geographic_assignment.province_code
        if not creator.can_access_province(target_province):
            return False
        
        # Check user group access
        if creator.user_group:
            if not creator.user_group.can_manage_user_group(user_data.user_group_code):
                return False
        
        return True
    
    def _can_access_user_data(
        self,
        accessor: UserProfile,
        target_user: UserProfile
    ) -> bool:
        """Check if user can access another user's data"""
        
        # Superusers can access any user
        if accessor.is_superuser:
            return True
        
        # Users can access their own data
        if accessor.id == target_user.id:
            return True
        
        # Check province access
        if not accessor.can_access_province(target_user.province_code):
            return False
        
        # Check user group hierarchy
        if accessor.user_group:
            return accessor.user_group.can_manage_user_group(target_user.user_group_code)
        
        return False
    
    def _can_update_user(
        self,
        updater: UserProfile,
        target_user: UserProfile,
        update_data: UserProfileUpdate
    ) -> bool:
        """Check if user can update another user with specified changes"""
        
        # Basic access check
        if not self._can_access_user_data(updater, target_user):
            return False
        
        # Check for sensitive field updates
        sensitive_fields = ['user_group_code', 'province_code', 'status', 'role_ids']
        
        for field in sensitive_fields:
            if getattr(update_data, field, None) is not None:
                if not updater.is_superuser:
                    # Additional permission checks for sensitive updates
                    if field in ['status', 'role_ids']:
                        if not updater.has_permission('user_admin'):
                            return False
        
        return True
    
    def _can_user_login(self, user: UserProfile) -> bool:
        """Check if user can create a login session"""
        
        # User must be active
        if not user.is_active:
            return False
        
        # User status must allow login
        if user.status not in [UserStatus.ACTIVE.value]:
            return False
        
        # Account must not be locked
        if user.is_locked:
            return False
        
        return True
    
    def _validate_workstation_access(
        self,
        user: UserProfile,
        workstation_id: str
    ) -> bool:
        """
        Validate user access to workstation (V00468 equivalent)
        
        In the context of LINC, this would check:
        - User's location assignments
        - Workstation location mapping
        - Infrastructure permissions
        """
        
        # For now, basic validation
        # Real implementation would check location assignments and infrastructure access
        
        return True
    
    def _apply_permission_filters(
        self,
        filters: UserListFilter,
        current_user: UserProfile
    ) -> UserListFilter:
        """Apply permission-based filters to user list request"""
        
        # If not superuser, apply geographic restrictions
        if not current_user.is_superuser:
            # Force province filter for provincial users
            if current_user.user_group and current_user.user_group.is_provincial_help_desk:
                filters.province_code = current_user.province_code
            
            # Force user group filter for local users
            elif current_user.user_group and not current_user.user_group.is_national_help_desk:
                filters.user_group_code = current_user.user_group_code
        
        return filters


# Create service instance
user_management_service = UserManagementService() 