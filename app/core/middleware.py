"""
LINC Custom Middleware
Audit logging, file operations, and performance monitoring middleware
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
import time
import uuid
import structlog
import json
from typing import Optional
from pathlib import Path

from app.core.config import settings

logger = structlog.get_logger()


class AuditMiddleware(BaseHTTPMiddleware):
    """Basic audit middleware for LINC system"""
    
    async def dispatch(self, request: Request, call_next):
        transaction_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate execution time
        execution_time = (time.time() - start_time) * 1000
        
        # Log request
        logger.info(
            "Request processed",
            transaction_id=transaction_id,
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            execution_time_ms=round(execution_time, 2)
        )
        
        # Add transaction ID to response headers
        response.headers["X-Transaction-ID"] = transaction_id
        
        return response


class FileStorageService:
    """
    File storage service with audit logging
    Implements secure file operations with comprehensive tracking
    """
    
    def __init__(self, country_code: str):
        self.country_code = country_code.upper()
        self.base_path = settings.get_file_storage_path(country_code)
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create directory structure if it doesn't exist"""
        directories = [
            "images/citizens/photos",
            "images/citizens/processed", 
            "images/citizens/documents",
            "images/licenses/cards",
            "images/licenses/templates",
            "images/licenses/certificates",
            "exports/reports",
            "exports/batch_files",
            "exports/integrations",
            "audit/logs",
            "audit/transactions",
            "audit/changes",
            "backups/daily",
            "backups/weekly",
            "backups/archive"
        ]
        
        for directory in directories:
            dir_path = self.base_path / directory
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def store_citizen_photo(self, citizen_id: str, image_data: bytes, 
                           original_filename: str, user_context: dict = None) -> dict:
        """
        Store citizen photo with metadata and audit logging
        Reference: Screen 1.1 Person Registration/Search Screen
        """
        file_id = str(uuid.uuid4())
        timestamp = time.time()
        extension = Path(original_filename).suffix.lower()
        
        # Validate file type
        if not self._is_allowed_image_type(extension):
            raise ValueError(f"File type {extension} not allowed")
        
        # Store original photo
        original_path = self.base_path / f"images/citizens/photos/{citizen_id}_{file_id}{extension}"
        
        try:
            with open(original_path, 'wb') as f:
                f.write(image_data)
            
            file_metadata = {
                "file_id": file_id,
                "original_path": str(original_path),
                "original_filename": original_filename,
                "stored_at": timestamp,
                "file_size": len(image_data),
                "mime_type": self._get_mime_type(extension),
                "citizen_id": citizen_id
            }
            
            # Log file operation
            self._log_file_operation(
                "STORE_CITIZEN_PHOTO", 
                str(original_path), 
                user_context, 
                file_metadata
            )
            
            return file_metadata
            
        except Exception as e:
            logger.error(f"Failed to store citizen photo: {e}")
            raise
    
    def store_license_card(self, license_id: str, card_data: bytes, 
                          card_type: str = "standard", user_context: dict = None) -> dict:
        """
        Store generated license card
        Reference: Screen 2.2 Card Ordering System
        """
        file_id = str(uuid.uuid4())
        timestamp = time.time()
        
        # Store card file
        card_path = self.base_path / f"images/licenses/cards/{license_id}_{card_type}_{file_id}.pdf"
        
        try:
            with open(card_path, 'wb') as f:
                f.write(card_data)
            
            card_metadata = {
                "file_id": file_id,
                "card_path": str(card_path),
                "card_type": card_type,
                "generated_at": timestamp,
                "file_size": len(card_data),
                "license_id": license_id
            }
            
            # Log file operation
            self._log_file_operation(
                "STORE_LICENSE_CARD", 
                str(card_path), 
                user_context, 
                card_metadata
            )
            
            return card_metadata
            
        except Exception as e:
            logger.error(f"Failed to store license card: {e}")
            raise
    
    def get_file_path(self, file_path: str) -> Path:
        """Get secure file path within country storage"""
        # Ensure path is within country storage directory
        requested_path = Path(file_path)
        
        if not str(requested_path).startswith(str(self.base_path)):
            # If relative path, make it relative to base path
            file_path = self.base_path / file_path
        else:
            file_path = requested_path
        
        # Verify file exists and is within allowed directory
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not str(file_path.resolve()).startswith(str(self.base_path.resolve())):
            raise PermissionError("Access denied to file outside country storage")
        
        return file_path
    
    def backup_file(self, source_path: str, backup_type: str = "daily") -> bool:
        """Backup file to appropriate backup location"""
        try:
            source = Path(source_path)
            if not source.exists():
                return False
                
            backup_dir = self.base_path / f"backups/{backup_type}"
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"{timestamp}_{source.name}"
            
            # Copy file to backup location
            import shutil
            shutil.copy2(source, backup_path)
            
            logger.info(f"File backed up: {source} -> {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Backup failed for {source_path}: {e}")
            return False
    
    def _is_allowed_image_type(self, extension: str) -> bool:
        """Check if image type is allowed"""
        allowed_extensions = [".jpg", ".jpeg", ".png", ".gif"]
        return extension.lower() in allowed_extensions
    
    def _get_mime_type(self, extension: str) -> str:
        """Get MIME type from file extension"""
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg", 
            ".png": "image/png",
            ".gif": "image/gif",
            ".pdf": "application/pdf"
        }
        return mime_types.get(extension.lower(), "application/octet-stream")
    
    def _log_file_operation(self, operation: str, file_path: str, 
                           user_context: dict = None, metadata: dict = None):
        """Log file operations for security and compliance"""
        log_data = {
            "operation": operation,
            "file_path": file_path,
            "country_code": self.country_code,
            "timestamp": time.time()
        }
        
        if user_context:
            log_data.update(user_context)
        
        if metadata:
            log_data["metadata"] = metadata
        
        logger.info("File operation", **log_data)
        
        # Also write to file-based audit log
        self._write_file_audit_log(log_data)
    
    def _write_file_audit_log(self, log_data: dict):
        """Write file operation to audit log file"""
        if not settings.ENABLE_FILE_AUDIT_LOGS:
            return
        
        try:
            log_file = self.base_path / f"audit/logs/{time.strftime('%Y%m%d')}_file_operations.log"
            
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_data) + '\n')
                
        except Exception as e:
            logger.error(f"Failed to write file audit log: {e}")


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Performance monitoring middleware for capacity planning"""
    
    async def dispatch(self, request: Request, call_next) -> StarletteResponse:
        if not settings.ENABLE_PERFORMANCE_MONITORING:
            return await call_next(request)
        
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        response = await call_next(request)
        
        execution_time = (time.time() - start_time) * 1000
        end_memory = self._get_memory_usage()
        memory_diff = end_memory - start_memory
        
        # Log performance metrics
        logger.info(
            "Performance metrics",
            path=request.url.path,
            method=request.method,
            execution_time_ms=round(execution_time, 2),
            memory_usage_mb=round(memory_diff, 2),
            status_code=response.status_code
        )
        
        return response
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except ImportError:
            return 0.0  # psutil not available 