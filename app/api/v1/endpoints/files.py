"""
LINC File Management API Endpoints
Secure file upload, storage, and serving with comprehensive audit logging
Reference: linc-file-storage-audit.mdc requirements
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, Response
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import structlog
from pathlib import Path
import uuid
from datetime import datetime

from app.core.database import get_db
from app.core.config import get_settings
from app.core.security import get_current_user
from app.services.file_storage import FileStorageService, FileSystemMonitor, BackupService
from app.services.audit import AuditService, UserContext, AuditLogData
from app.models.user import User
from app.schemas.files import (
    FileMetadataResponse, 
    FileUploadResponse, 
    StorageMetricsResponse,
    BackupResponse
)

logger = structlog.get_logger()
router = APIRouter()
settings = get_settings()

def get_user_context(request: Request, current_user: User) -> UserContext:
    """Extract user context from request and current user"""
    return UserContext(
        user_id=str(current_user.id),
        username=current_user.username,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        session_id=request.headers.get("x-session-id")
    )

def get_file_storage_service(current_user: User = Depends(get_current_user)) -> FileStorageService:
    """Get file storage service for current user's country"""
    # For single-country deployment, use configured country
    # In multi-country setup, this would come from user's assigned country
    return FileStorageService(settings.COUNTRY_CODE)

def get_audit_service(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> AuditService:
    """Get audit service for current user's country"""
    return AuditService(db, settings.COUNTRY_CODE)

@router.post("/upload/citizen-photo", response_model=FileUploadResponse)
async def upload_citizen_photo(
    citizen_id: str,
    file: UploadFile = File(...),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    file_storage: FileStorageService = Depends(get_file_storage_service),
    audit_service: AuditService = Depends(get_audit_service),
    db: Session = Depends(get_db)
):
    """
    Upload citizen photo with audit logging
    Reference: Screen 1.1 Person Registration/Search Screen
    """
    try:
        user_context = get_user_context(request, current_user)
        
        # Validate file type
        if file.content_type not in settings.allowed_image_types_list:
            audit_service.log_security_event(
                "invalid_file_upload",
                f"Invalid file type attempted: {file.content_type}",
                user_context
            )
            raise HTTPException(
                status_code=400,
                detail=f"File type {file.content_type} not allowed"
            )
        
        # Validate file size
        if file.size and file.size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
            audit_service.log_security_event(
                "oversized_file_upload",
                f"File size {file.size} exceeds limit",
                user_context
            )
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds {settings.MAX_FILE_SIZE_MB}MB limit"
            )
        
        # Store the file
        metadata = await file_storage.store_citizen_photo_async(
            citizen_id=citizen_id,
            upload_file=file
        )
        
        # Log the file operation
        audit_service.log_file_operation(
            operation="CREATE",
            file_path=metadata["relative_path"],
            user_context=user_context,
            metadata={
                "citizen_id": citizen_id,
                "original_filename": metadata["original_filename"],
                "file_size": metadata["file_size"],
                "mime_type": metadata["mime_type"]
            },
            entity_type="CITIZEN_PHOTO",
            entity_id=citizen_id
        )
        
        logger.info(
            "Citizen photo uploaded successfully",
            citizen_id=citizen_id,
            file_id=metadata["file_id"],
            user=current_user.username
        )
        
        return FileUploadResponse(
            success=True,
            file_id=metadata["file_id"],
            file_path=metadata["relative_path"],
            file_size=metadata["file_size"],
            message="Photo uploaded successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading citizen photo: {e}")
        audit_service.log_action(AuditLogData(
            action_type="FILE_UPLOAD_ERROR",
            entity_type="CITIZEN_PHOTO",
            entity_id=citizen_id,
            success=False,
            error_message=str(e),
            **user_context.dict()
        ))
        raise HTTPException(status_code=500, detail="Failed to upload file")

@router.post("/upload/document", response_model=FileUploadResponse)
async def upload_document(
    entity_id: str,
    document_type: str,
    file: UploadFile = File(...),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    file_storage: FileStorageService = Depends(get_file_storage_service),
    audit_service: AuditService = Depends(get_audit_service)
):
    """Upload supporting documents with audit logging"""
    try:
        user_context = get_user_context(request, current_user)
        
        # Validate file type
        if file.content_type not in settings.allowed_document_types_list:
            raise HTTPException(
                status_code=400,
                detail=f"Document type {file.content_type} not allowed"
            )
        
        # Read file content
        content = await file.read()
        
        # Store the document
        metadata = file_storage.store_document(
            entity_id=entity_id,
            document_data=content,
            document_type=document_type,
            filename=file.filename or "document"
        )
        
        # Log the file operation
        audit_service.log_file_operation(
            operation="CREATE",
            file_path=metadata["relative_path"],
            user_context=user_context,
            metadata={
                "entity_id": entity_id,
                "document_type": document_type,
                "original_filename": metadata["original_filename"],
                "file_size": metadata["file_size"]
            },
            entity_type="DOCUMENT",
            entity_id=entity_id
        )
        
        return FileUploadResponse(
            success=True,
            file_id=metadata["file_id"],
            file_path=metadata["relative_path"],
            file_size=metadata["file_size"],
            message="Document uploaded successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload document")

@router.get("/serve")
async def serve_file(
    path: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    file_storage: FileStorageService = Depends(get_file_storage_service),
    audit_service: AuditService = Depends(get_audit_service)
):
    """
    Secure file serving with access control and audit logging
    """
    try:
        user_context = get_user_context(request, current_user)
        
        # Verify file exists
        if not file_storage.file_exists(path):
            audit_service.log_security_event(
                "file_not_found_access",
                f"Attempt to access non-existent file: {path}",
                user_context
            )
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get full file path
        full_path = file_storage.get_file_path(path)
        
        # TODO: Add role-based access control here
        # For now, logged-in users can access any file in their country
        
        # Log file access
        audit_service.log_file_operation(
            operation="ACCESS",
            file_path=path,
            user_context=user_context,
            metadata={
                "access_type": "download",
                "file_size": full_path.stat().st_size
            },
            entity_type="FILE",
            entity_id=path
        )
        
        # Serve the file
        return FileResponse(
            path=str(full_path),
            filename=full_path.name,
            media_type="application/octet-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving file {path}: {e}")
        raise HTTPException(status_code=500, detail="Failed to serve file")

@router.delete("/delete")
async def delete_file(
    path: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    file_storage: FileStorageService = Depends(get_file_storage_service),
    audit_service: AuditService = Depends(get_audit_service)
):
    """Delete file with audit logging (admin only)"""
    try:
        user_context = get_user_context(request, current_user)
        
        # Check if user has admin role
        if not current_user.is_superuser:
            audit_service.log_security_event(
                "unauthorized_file_delete",
                f"Non-admin user attempted file deletion: {path}",
                user_context
            )
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Verify file exists before deletion
        if not file_storage.file_exists(path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get file metadata before deletion
        full_path = file_storage.get_file_path(path)
        file_size = full_path.stat().st_size
        
        # Delete the file
        success = file_storage.delete_file(path)
        
        if success:
            # Log file deletion
            audit_service.log_file_operation(
                operation="DELETE",
                file_path=path,
                user_context=user_context,
                metadata={
                    "file_size": file_size,
                    "deletion_reason": "admin_request"
                },
                entity_type="FILE",
                entity_id=path
            )
            
            return {"success": True, "message": "File deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete file")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file {path}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete file")

@router.get("/storage/metrics", response_model=StorageMetricsResponse)
async def get_storage_metrics(
    current_user: User = Depends(get_current_user),
    file_storage: FileStorageService = Depends(get_file_storage_service)
):
    """Get storage utilization metrics"""
    try:
        # Check if user has admin role for detailed metrics
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        metrics = file_storage.get_storage_metrics()
        
        return StorageMetricsResponse(
            success=True,
            country_code=metrics["country_code"],
            total_space_gb=metrics["total_space_gb"],
            used_space_gb=metrics["used_space_gb"],
            free_space_gb=metrics["free_space_gb"],
            usage_percentage=metrics["usage_percentage"],
            total_files=metrics["total_files"],
            files_by_directory=metrics["files_by_directory"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting storage metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get storage metrics")

@router.get("/storage/health")
async def check_storage_health(
    current_user: User = Depends(get_current_user),
    file_storage: FileStorageService = Depends(get_file_storage_service)
):
    """Check storage health status"""
    try:
        # Get basic file storage health
        health = file_storage.get_storage_health()
        
        # If not in read-only mode, get detailed metrics
        if not file_storage.read_only_mode:
            try:
                monitor = FileSystemMonitor(settings.COUNTRY_CODE)
                detailed_health = monitor.check_storage_health()
                health.update(detailed_health)
            except Exception as e:
                logger.warning(f"Could not get detailed storage metrics: {e}")
                health["detailed_metrics_error"] = str(e)
        
        health["country_code"] = settings.COUNTRY_CODE
        return health
        
    except Exception as e:
        logger.error(f"Error checking storage health: {e}")
        return {
            "status": "error",
            "error": str(e),
            "country_code": settings.COUNTRY_CODE,
            "writable": False
        }

@router.post("/backup/daily", response_model=BackupResponse)
async def create_daily_backup(
    request: Request,
    current_user: User = Depends(get_current_user),
    audit_service: AuditService = Depends(get_audit_service)
):
    """Create daily backup (admin only)"""
    try:
        user_context = get_user_context(request, current_user)
        
        # Check admin permissions
        if not current_user.is_superuser:
            audit_service.log_security_event(
                "unauthorized_backup_request",
                "Non-admin user attempted backup creation",
                user_context
            )
            raise HTTPException(status_code=403, detail="Admin access required")
        
        backup_service = BackupService(settings.COUNTRY_CODE)
        result = await backup_service.perform_daily_backup()
        
        # Log backup operation
        audit_service.log_action(AuditLogData(
            action_type="BACKUP_CREATE",
            entity_type="SYSTEM",
            entity_id="daily_backup",
            success=result["success"],
            new_values=result,
            **user_context.dict()
        ))
        
        return BackupResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating daily backup: {e}")
        raise HTTPException(status_code=500, detail="Failed to create backup")

@router.post("/backup/weekly", response_model=BackupResponse)
async def create_weekly_backup(
    request: Request,
    current_user: User = Depends(get_current_user),
    audit_service: AuditService = Depends(get_audit_service)
):
    """Create weekly backup (admin only)"""
    try:
        user_context = get_user_context(request, current_user)
        
        # Check admin permissions
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        backup_service = BackupService(settings.COUNTRY_CODE)
        result = await backup_service.perform_weekly_backup()
        
        # Log backup operation
        audit_service.log_action(AuditLogData(
            action_type="BACKUP_CREATE",
            entity_type="SYSTEM",
            entity_id="weekly_backup",
            success=result["success"],
            new_values=result,
            **user_context.dict()
        ))
        
        return BackupResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating weekly backup: {e}")
        raise HTTPException(status_code=500, detail="Failed to create backup")

@router.get("/storage/largest-files")
async def get_largest_files(
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Get largest files for cleanup recommendations (admin only)"""
    try:
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        monitor = FileSystemMonitor(settings.COUNTRY_CODE)
        largest_files = monitor.get_largest_files(limit)
        
        return {
            "success": True,
            "largest_files": largest_files,
            "country_code": settings.COUNTRY_CODE
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting largest files: {e}")
        raise HTTPException(status_code=500, detail="Failed to get file listing") 