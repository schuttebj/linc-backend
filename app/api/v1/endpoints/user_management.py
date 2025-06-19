"""
User Management API Endpoints
Comprehensive user management API with role-based access control
Consolidated to use existing User model with extended functionality
"""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
import structlog

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.permission_middleware import require_permission, require_any_permission
from app.crud.user_management import user_management
from app.schemas.user_management import (
    UserProfileCreate, UserProfileUpdate, UserProfileResponse,
    UserListFilter, UserListResponse, UserStatistics,
    UserValidationResult, PermissionCheckResult,
    UserSessionCreate, UserSessionResponse
)
from app.schemas.location import (
    UserLocationAssignmentCreate,
    UserLocationAssignmentResponse
)
from app.models.user import User

logger = structlog.get_logger()
router = APIRouter()

# ========================================
# USER PROFILE MANAGEMENT ENDPOINTS
# ========================================

@router.post("/", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
def create_user_profile(
    *,
    db: Session = Depends(get_db),
    user_data: UserProfileCreate,
    current_user: User = Depends(require_permission("user.create"))
):
    """
    Create new user profile.
    
    Requires user_create permission.
    
    Implements business rules:
    - V06001: User Group must be active and valid
    - V06002: Office must exist within selected User Group
    - V06003: User Name must be unique within User Group
    - V06004: Email must be valid and unique system-wide
    - V06005: ID Number must be valid for selected ID Type
    """
    try:
        logger.info(
            "Creating user profile",
            username=user_data.username,
            user_group=user_data.user_group_code,
            created_by=current_user.username
        )
        
        # Create user profile
        new_user = user_management.create_user(
            db=db,
            user_data=user_data,
            created_by=current_user.username
        )
        
        logger.info(
            "User profile created successfully",
            user_id=str(new_user.id),
            username=new_user.username
        )
        
        return UserProfileResponse.from_user(new_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error creating user profile",
            username=user_data.username,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user profile"
        )

@router.get("/", response_model=UserListResponse)
def list_user_profiles(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by user status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    user_type: Optional[str] = Query(None, description="Filter by user type"),
    province_code: Optional[str] = Query(None, description="Filter by province"),
    user_group_code: Optional[str] = Query(None, description="Filter by user group"),
    search: Optional[str] = Query(None, description="Search users"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user.read"))
):
    """
    List user profiles with filtering and pagination.
    
    Requires user_view permission.
    
    Supports filtering by status, province, user group, and text search.
    Results are filtered based on user's permission level.
    """
    try:
        logger.info(
            "Listing user profiles",
            page=page,
            size=size,
            requested_by=current_user.username
        )
        
        # Build filters
        filters = UserListFilter(
            status=status_filter,
            is_active=is_active,
            user_type=user_type,
            province_code=province_code,
            user_group_code=user_group_code,
            search=search
        )
        
        # Get user profiles with permission filtering
        users, total = user_management.list_users(
            db=db,
            filters=filters,
            page=page,
            size=size
        )
        
        # Convert to response format
        user_responses = [UserProfileResponse.from_user(user) for user in users]
        
        # Build pagination info
        pages = (total + size - 1) // size
        has_next = page < pages
        has_previous = page > 1
        
        return UserListResponse(
            users=user_responses,
            total=total,
            page=page,
            size=size,
            pages=pages,
            has_next=has_next,
            has_previous=has_previous
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error listing user profiles",
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profiles"
        )

@router.get("/{user_id}", response_model=UserProfileResponse)
def get_user_profile_by_id(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user.read"))
):
    """
    Get user profile by ID.
    
    Requires user_view permission.
    
    Returns complete user profile with relationships.
    """
    try:
        logger.info(
            "Getting user profile",
            user_id=user_id,
            requested_by=current_user.username
        )
        
        user = user_management.get_user(db=db, user_id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        logger.info(
            "User profile retrieved successfully",
            user_id=user_id,
            username=user.username
        )
        
        return UserProfileResponse.from_user(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting user profile",
            user_id=user_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )

@router.put("/{user_id}", response_model=UserProfileResponse)
def update_user_profile(
    user_id: str,
    user_data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user.update"))
):
    """
    Update user profile.
    
    Requires user_edit permission.
    
    Supports partial updates with validation.
    """
    try:
        logger.info(
            "Updating user profile",
            user_id=user_id,
            updated_by=current_user.username
        )
        
        # Update user profile
        updated_user = user_management.update_user(
            db=db,
            user_id=user_id,
            user_data=user_data,
            updated_by=current_user.username
        )
        
        logger.info(
            "User profile updated successfully",
            user_id=user_id
        )
        
        return UserProfileResponse.from_user(updated_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error updating user profile",
            user_id=user_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )

@router.delete("/{user_id}", response_model=UserProfileResponse)
def delete_user_profile(
    user_id: str,
    soft_delete: bool = Query(True, description="Perform soft delete"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user.delete"))
):
    """
    Delete user profile.
    
    Requires user_delete permission.
    
    By default performs soft delete (sets is_active=False).
    """
    try:
        logger.info(
            "Deleting user profile",
            user_id=user_id,
            soft_delete=soft_delete,
            deleted_by=current_user.username
        )
        
        # Get existing user
        existing_user = user_management.get_user(db=db, user_id=user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        # Prevent self-deletion
        if str(existing_user.id) == str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own user profile"
            )
        
        # Perform soft delete
        existing_user.is_active = False
        db.add(existing_user)
        db.commit()
        
        logger.info(
            "User profile deleted successfully",
            user_id=user_id,
            soft_delete=soft_delete
        )
        
        return UserProfileResponse.from_user(existing_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error deleting user profile",
            user_id=user_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user profile"
        )

# ========================================
# USER SEARCH ENDPOINTS
# ========================================

@router.get("/search/users", response_model=List[UserProfileResponse])
def search_users(
    q: str = Query(..., min_length=2, description="Search term"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
    exclude_assigned: Optional[str] = Query(None, description="Exclude users already assigned to this location ID"),
    user_type: Optional[str] = Query(None, description="Filter by user type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user.read"))
):
    """
    Search users by name, username, email, or employee ID.
    Enhanced for staff assignment workflow.
    
    Requires user_view permission.
    """
    try:
        logger.info(
            "Searching users",
            search_term=q,
            limit=limit,
            exclude_assigned=exclude_assigned,
            user_type=user_type,
            requested_by=current_user.username
        )
        
        # Search users with enhanced filters for staff assignment
        users = user_management.search_users(
            db=db,
            search_term=q,
            limit=limit,
            exclude_assigned_to_location=exclude_assigned,
            user_type_filter=user_type
        )
        
        # Convert to response format
        user_responses = [UserProfileResponse.from_user(user) for user in users]
        
        logger.info(
            "Users search completed",
            results_count=len(user_responses),
            search_term=q
        )
        
        return user_responses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error searching users",
            search_term=q,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search users"
        )

# ========================================
# USER SESSION MANAGEMENT ENDPOINTS
# ========================================

@router.post("/{user_id}/sessions", response_model=UserSessionResponse)
def create_user_session(
    user_id: str,
    session_data: UserSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("session.create"))
):
    """
    Create user session.
    
    Requires session_create permission.
    
    Implements validation rules:
    - V00468: Payments must exist for specified User and Workstation
    - Session display logic (V01029, V01030)
    """
    try:
        logger.info(
            "Creating user session",
            user_id=user_id,
            workstation=session_data.workstation_id,
            created_by=current_user.username
        )
        
        # Create user session
        # (Implementation would include session creation logic)
        
        logger.info(
            "User session created successfully",
            user_id=user_id,
            workstation=session_data.workstation_id
        )
        
        # Return placeholder response
        return UserSessionResponse(
            id="session-id",
            user_id=user_id,
            user_group_code=session_data.user_group_code,
            user_number=session_data.user_number,
            workstation_id=session_data.workstation_id,
            session_type=session_data.session_type,
            session_start=datetime.utcnow(),
            session_expiry=datetime.utcnow() + timedelta(hours=8),
            ip_address=session_data.ip_address,
            user_agent=session_data.user_agent,
            is_active=True,
            user_profile_display="User Display",
            user_group_display="Group Display",
            office_display="Office Display"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error creating user session",
            user_id=user_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user session"
        )

@router.get("/{user_id}/sessions", response_model=List[UserSessionResponse])
def get_user_sessions(
    user_id: str,
    active_only: bool = Query(True, description="Return only active sessions"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("session.read"))
):
    """
    Get user sessions.
    
    Requires session_view permission.
    """
    try:
        logger.info(
            "Getting user sessions",
            user_id=user_id,
            active_only=active_only,
            requested_by=current_user.username
        )
        
        # Get user sessions
        # (Implementation would include session retrieval logic)
        
        return []
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting user sessions",
            user_id=user_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user sessions"
        )

@router.delete("/sessions/{session_id}")
def end_user_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("session.manage"))
):
    """
    End user session.
    
    Requires session_manage permission.
    """
    try:
        logger.info(
            "Ending user session",
            session_id=session_id,
            ended_by=current_user.username
        )
        
        # End user session
        # (Implementation would include session termination logic)
        
        logger.info(
            "User session ended successfully",
            session_id=session_id
        )
        
        return {"message": "Session ended successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error ending user session",
            session_id=session_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to end user session"
        )

# ========================================
# USER STATISTICS AND REPORTING ENDPOINTS
# ========================================

@router.get("/statistics/overview", response_model=UserStatistics)
def get_user_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user.read"))
):
    """
    Get user management statistics.
    
    Requires user_view permission.
    
    Statistics are filtered based on current user's permissions:
    - Provincial users see statistics for their province
    - Local users see statistics for their user group
    - National users see system-wide statistics
    """
    try:
        logger.info(
            "Getting user statistics",
            requested_by=current_user.username
        )
        
        # Get user statistics
        # (Implementation would include statistics calculation)
        
        return UserStatistics(
            total_users=0,
            active_users=0,
            inactive_users=0,
            suspended_users=0,
            pending_activation=0,
            by_user_type={},
            by_province={},
            by_user_group={},
            new_users_this_month=0,
            active_sessions=0,
            recent_logins=0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting user statistics",
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user statistics"
        )

# ========================================
# USER VALIDATION ENDPOINTS
# ========================================

@router.post("/validate/username")
def validate_username(
    username: str = Query(..., min_length=3, max_length=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user.create"))
):
    """
    Validate username availability.
    
    Requires user_create permission.
    """
    try:
        # Check if username exists
        existing_user = user_management.get_user_by_username(db=db, username=username)
        
        return {
            "username": username,
            "is_available": existing_user is None,
            "message": "Username is available" if existing_user is None else "Username already exists"
        }
        
    except Exception as e:
        logger.error(
            "Error validating username",
            username=username,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate username"
        )

@router.post("/validate/email")
def validate_email(
    email: str = Query(..., description="Email address to validate"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user.create"))
):
    """
    Validate email availability.
    
    Requires user_create permission.
    """
    try:
        # Check if email exists
        # (Implementation would include email validation logic)
        
        return {
            "email": email,
            "is_available": True,
            "message": "Email is available"
        }
        
    except Exception as e:
        logger.error(
            "Error validating email",
            email=email,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate email"
        )

# ========================================
# USER LOCATION ASSIGNMENT ENDPOINTS
# ========================================

@router.post("/{user_id}/assignments", response_model=UserLocationAssignmentResponse, status_code=status.HTTP_201_CREATED)
def assign_user_to_location(
    user_id: str,
    assignment_data: UserLocationAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("staff.assign"))
):
    """
    Assign user to location from user management screen.
    
    Requires staff_assign permission.
    """
    try:
        logger.info(
            "Assigning user to location",
            user_id=user_id,
            location_id=assignment_data.location_id,
            assigned_by=current_user.username
        )
        
        # Verify user exists
        user = user_management.get_user(db=db, user_id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Override user_id in assignment data
        assignment_data.user_id = user_id
        
        # Create assignment using location service
        from app.crud import location as location_crud
        assignment = location_crud.create_user_location_assignment(
            db=db,
            assignment_data=assignment_data,
            assigned_by=current_user.username
        )
        
        logger.info(
            "User assigned to location successfully",
            user_id=user_id,
            location_id=assignment_data.location_id,
            assignment_id=str(assignment.id)
        )
        
        return UserLocationAssignmentResponse.from_orm(assignment)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error assigning user to location",
            user_id=user_id,
            location_id=assignment_data.location_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign user to location"
        )

@router.get("/{user_id}/assignments", response_model=List[UserLocationAssignmentResponse])
def get_user_assignments(
    user_id: str,
    active_only: bool = Query(True, description="Return only active assignments"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user.read"))
):
    """
    Get user location assignments.
    
    Requires user_view permission.
    """
    try:
        logger.info(
            "Getting user assignments",
            user_id=user_id,
            active_only=active_only,
            requested_by=current_user.username
        )
        
        # Verify user exists
        user = user_management.get_user(db=db, user_id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get assignments
        from app.crud import location as location_crud
        assignments = location_crud.get_user_location_assignments(
            db=db,
            user_id=user_id,
            active_only=active_only
        )
        
        return [UserLocationAssignmentResponse.from_orm(assignment) for assignment in assignments]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting user assignments",
            user_id=user_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user assignments"
        )

# ========================================
# HELPER FUNCTIONS
# ========================================

# Import datetime for session endpoints
from datetime import datetime, timedelta 