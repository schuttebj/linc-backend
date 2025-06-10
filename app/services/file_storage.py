"""
LINC File Storage Service
Local file storage system with country separation and backup capabilities
Reference: linc-file-storage-audit.mdc requirements
"""

from pathlib import Path
from typing import Optional, BinaryIO, Dict, Any, List
import uuid
from datetime import datetime
import shutil
import json
import mimetypes
import tarfile
import asyncio
from fastapi import UploadFile
import structlog

from app.core.config import settings

logger = structlog.get_logger()

class FileStorageService:
    """
    Local file storage service with country separation
    Reference: LINC File Storage & Audit System Requirements
    """
    
    def __init__(self, country_code: str):
        self.country_code = country_code.upper()
        self.base_path = Path(settings.FILE_STORAGE_PATH) / self.country_code
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
            (self.base_path / directory).mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {self.base_path / directory}")
    
    def store_citizen_photo(self, citizen_id: str, image_data: BinaryIO, 
                           original_filename: str) -> Dict[str, Any]:
        """
        Store citizen photo with metadata
        Reference: Screen 1.1 Person Registration/Search Screen
        """
        file_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        extension = Path(original_filename).suffix.lower()
        
        # Validate image format
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        if extension not in allowed_extensions:
            raise ValueError(f"Unsupported image format: {extension}")
        
        # Store original photo
        original_path = self.base_path / f"images/citizens/photos/{citizen_id}_{file_id}{extension}"
        
        with open(original_path, 'wb') as f:
            content = image_data.read()
            f.write(content)
        
        # Return metadata for database storage
        metadata = {
            "file_id": file_id,
            "original_path": str(original_path),
            "relative_path": str(original_path.relative_to(self.base_path)),
            "original_filename": original_filename,
            "stored_at": timestamp,
            "file_size": len(content),
            "mime_type": self._get_mime_type(extension),
            "country_code": self.country_code
        }
        
        logger.info(
            "Citizen photo stored",
            citizen_id=citizen_id,
            file_id=file_id,
            file_size=metadata["file_size"],
            country_code=self.country_code
        )
        
        return metadata
    
    async def store_citizen_photo_async(self, citizen_id: str, upload_file: UploadFile) -> Dict[str, Any]:
        """
        Async version for FastAPI UploadFile
        """
        file_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        extension = Path(upload_file.filename or "").suffix.lower()
        
        # Validate image format
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        if extension not in allowed_extensions:
            raise ValueError(f"Unsupported image format: {extension}")
        
        # Store original photo
        original_path = self.base_path / f"images/citizens/photos/{citizen_id}_{file_id}{extension}"
        
        content = await upload_file.read()
        with open(original_path, 'wb') as f:
            f.write(content)
        
        metadata = {
            "file_id": file_id,
            "original_path": str(original_path),
            "relative_path": str(original_path.relative_to(self.base_path)),
            "original_filename": upload_file.filename,
            "stored_at": timestamp,
            "file_size": len(content),
            "mime_type": upload_file.content_type or self._get_mime_type(extension),
            "country_code": self.country_code
        }
        
        logger.info(
            "Citizen photo stored (async)",
            citizen_id=citizen_id,
            file_id=file_id,
            file_size=metadata["file_size"],
            country_code=self.country_code
        )
        
        return metadata
    
    def store_license_card(self, license_id: str, card_data: bytes, 
                          card_type: str = "standard") -> Dict[str, Any]:
        """
        Store generated license card
        Reference: Screen 2.2 Card Ordering System
        """
        file_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Store card file
        card_path = self.base_path / f"images/licenses/cards/{license_id}_{card_type}_{file_id}.pdf"
        
        with open(card_path, 'wb') as f:
            f.write(card_data)
        
        metadata = {
            "file_id": file_id,
            "card_path": str(card_path),
            "relative_path": str(card_path.relative_to(self.base_path)),
            "card_type": card_type,
            "license_id": license_id,
            "generated_at": timestamp,
            "file_size": len(card_data),
            "country_code": self.country_code
        }
        
        logger.info(
            "License card stored",
            license_id=license_id,
            card_type=card_type,
            file_id=file_id,
            file_size=metadata["file_size"],
            country_code=self.country_code
        )
        
        return metadata
    
    def store_document(self, entity_id: str, document_data: bytes, 
                      document_type: str, filename: str) -> Dict[str, Any]:
        """
        Store supporting documents
        """
        file_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        extension = Path(filename).suffix.lower()
        
        # Store document
        doc_path = self.base_path / f"images/citizens/documents/{entity_id}_{document_type}_{file_id}{extension}"
        
        with open(doc_path, 'wb') as f:
            f.write(document_data)
        
        return {
            "file_id": file_id,
            "document_path": str(doc_path),
            "relative_path": str(doc_path.relative_to(self.base_path)),
            "document_type": document_type,
            "entity_id": entity_id,
            "original_filename": filename,
            "stored_at": timestamp,
            "file_size": len(document_data),
            "mime_type": self._get_mime_type(extension),
            "country_code": self.country_code
        }
    
    def get_file_url(self, file_path: str) -> str:
        """Generate secure file access URL"""
        return f"/api/v1/{self.country_code.lower()}/files/serve?path={file_path}"
    
    def get_file_path(self, relative_path: str) -> Path:
        """Get full file path from relative path"""
        return self.base_path / relative_path
    
    def file_exists(self, relative_path: str) -> bool:
        """Check if file exists"""
        full_path = self.get_file_path(relative_path)
        return full_path.exists() and full_path.is_file()
    
    def delete_file(self, relative_path: str) -> bool:
        """Delete file safely"""
        try:
            full_path = self.get_file_path(relative_path)
            if full_path.exists() and full_path.is_file():
                full_path.unlink()
                logger.info(f"File deleted: {relative_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file {relative_path}: {e}")
            return False
    
    def backup_file(self, source_path: str, backup_type: str = "daily") -> bool:
        """Backup file to appropriate backup location"""
        source = Path(source_path)
        if not source.exists():
            logger.warning(f"Source file does not exist: {source_path}")
            return False
            
        backup_dir = self.base_path / f"backups/{backup_type}"
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{timestamp}_{source.name}"
        
        try:
            shutil.copy2(source, backup_path)
            logger.info(f"File backed up: {source_path} -> {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Error backing up file {source_path}: {e}")
            return False
    
    def _get_mime_type(self, extension: str) -> str:
        """Get MIME type from file extension"""
        mime_type, _ = mimetypes.guess_type(f"file{extension}")
        return mime_type or "application/octet-stream"
    
    def get_storage_metrics(self) -> Dict[str, Any]:
        """Get current storage utilization metrics"""
        try:
            total, used, free = shutil.disk_usage(self.base_path)
            
            # Count files in each directory
            file_counts = {}
            total_files = 0
            for directory in ["images", "exports", "audit", "backups"]:
                if (self.base_path / directory).exists():
                    count = sum(1 for _ in (self.base_path / directory).rglob("*") if _.is_file())
                    file_counts[directory] = count
                    total_files += count
            
            return {
                "country_code": self.country_code,
                "total_space_gb": round(total / (1024**3), 2),
                "used_space_gb": round(used / (1024**3), 2),
                "free_space_gb": round(free / (1024**3), 2),
                "usage_percentage": round((used / total) * 100, 2),
                "total_files": total_files,
                "files_by_directory": file_counts,
                "base_path": str(self.base_path)
            }
        except Exception as e:
            logger.error(f"Error getting storage metrics: {e}")
            return {
                "error": str(e),
                "country_code": self.country_code
            }


class BackupService:
    """
    Automated backup service for file storage
    """
    
    def __init__(self, country_code: str):
        self.country_code = country_code.upper()
        self.storage = FileStorageService(country_code)
        
    async def perform_daily_backup(self) -> Dict[str, Any]:
        """Daily incremental backup of all files"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_file = self.storage.base_path / f"backups/daily/backup_{timestamp}.tar.gz"
        
        try:
            # Create compressed backup of images and exports
            with tarfile.open(backup_file, "w:gz") as tar:
                # Add images directory
                images_path = self.storage.base_path / "images"
                if images_path.exists():
                    tar.add(images_path, arcname="images")
                
                # Add exports directory
                exports_path = self.storage.base_path / "exports"
                if exports_path.exists():
                    tar.add(exports_path, arcname="exports")
                
                # Add audit directory
                audit_path = self.storage.base_path / "audit"
                if audit_path.exists():
                    tar.add(audit_path, arcname="audit")
            
            # Verify backup integrity
            if self._verify_backup(str(backup_file)):
                # Clean up old backups (keep 30 days)
                await self._cleanup_old_backups("daily", 30)
                
                result = {
                    "success": True,
                    "backup_file": str(backup_file),
                    "backup_size": backup_file.stat().st_size,
                    "timestamp": timestamp,
                    "country_code": self.country_code
                }
                
                logger.info("Daily backup completed successfully", **result)
                return result
            else:
                return {
                    "success": False,
                    "error": "Backup verification failed",
                    "backup_file": str(backup_file),
                    "country_code": self.country_code
                }
                
        except Exception as e:
            logger.error(f"Daily backup failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "country_code": self.country_code
            }
    
    async def perform_weekly_backup(self) -> Dict[str, Any]:
        """Weekly full system backup"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_file = self.storage.base_path / f"backups/weekly/full_backup_{timestamp}.tar.gz"
        
        try:
            # Create compressed backup of entire country directory
            with tarfile.open(backup_file, "w:gz") as tar:
                tar.add(self.storage.base_path, arcname=self.country_code)
            
            if self._verify_backup(str(backup_file)):
                await self._cleanup_old_backups("weekly", 12)  # Keep 12 weeks
                
                result = {
                    "success": True,
                    "backup_file": str(backup_file),
                    "backup_size": backup_file.stat().st_size,
                    "timestamp": timestamp,
                    "country_code": self.country_code,
                    "backup_type": "full"
                }
                
                logger.info("Weekly backup completed successfully", **result)
                return result
            else:
                return {
                    "success": False,
                    "error": "Weekly backup verification failed",
                    "backup_file": str(backup_file),
                    "country_code": self.country_code
                }
        except Exception as e:
            logger.error(f"Weekly backup failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "country_code": self.country_code
            }
    
    def _verify_backup(self, backup_file: str) -> bool:
        """Verify backup file integrity"""
        try:
            with tarfile.open(backup_file, "r:gz") as tar:
                # This will fail if the file is corrupted
                members = tar.getmembers()
                return len(members) > 0
        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            return False
    
    async def _cleanup_old_backups(self, backup_type: str, keep_count: int):
        """Clean up old backup files"""
        backup_dir = self.storage.base_path / f"backups/{backup_type}"
        if not backup_dir.exists():
            return
        
        # Get all backup files sorted by creation time
        backup_files = sorted(
            [f for f in backup_dir.iterdir() if f.is_file() and f.suffix == '.gz'],
            key=lambda x: x.stat().st_ctime,
            reverse=True
        )
        
        # Remove old backups
        for backup_file in backup_files[keep_count:]:
            try:
                backup_file.unlink()
                logger.info(f"Removed old backup: {backup_file}")
            except Exception as e:
                logger.error(f"Error removing old backup {backup_file}: {e}")


class FileSystemMonitor:
    """
    File system monitoring and health checks
    """
    
    def __init__(self, country_code: str):
        self.country_code = country_code.upper()
        self.storage = FileStorageService(country_code)
    
    def check_storage_health(self) -> Dict[str, Any]:
        """Check storage health and alert on issues"""
        metrics = self.storage.get_storage_metrics()
        alerts = []
        
        if "error" in metrics:
            return {
                "status": "error",
                "alerts": [f"Storage metrics error: {metrics['error']}"],
                "metrics": metrics,
                "country_code": self.country_code
            }
        
        # Check disk usage
        if metrics["usage_percentage"] > 85:
            alerts.append("Storage usage above 85%")
        
        if metrics["free_space_gb"] < 10:
            alerts.append("Less than 10GB free space remaining")
        
        # Check file counts for unusual patterns
        if metrics["total_files"] > 1000000:  # 1M files
            alerts.append("Very high file count detected")
        
        status = "healthy"
        if alerts:
            status = "warning" if metrics["usage_percentage"] < 95 else "critical"
        
        return {
            "status": status,
            "alerts": alerts,
            "metrics": metrics,
            "country_code": self.country_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_largest_files(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get largest files for cleanup recommendations"""
        try:
            files = []
            for file_path in self.storage.base_path.rglob("*"):
                if file_path.is_file():
                    stat = file_path.stat()
                    files.append({
                        "path": str(file_path.relative_to(self.storage.base_path)),
                        "size_mb": round(stat.st_size / (1024**2), 2),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            
            # Sort by size and return top files
            return sorted(files, key=lambda x: x["size_mb"], reverse=True)[:limit]
            
        except Exception as e:
            logger.error(f"Error getting largest files: {e}")
            return [] 