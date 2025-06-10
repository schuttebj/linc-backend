"""
LINC File Management Schemas
Pydantic models for file upload, storage, and management endpoints
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

class FileUploadResponse(BaseModel):
    """Response model for file upload operations"""
    success: bool
    file_id: str
    file_path: str
    file_size: int
    message: str

class FileMetadataResponse(BaseModel):
    """Response model for file metadata"""
    file_id: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: str
    stored_at: str
    country_code: str

class StorageMetricsResponse(BaseModel):
    """Response model for storage metrics"""
    success: bool
    country_code: str
    total_space_gb: float
    used_space_gb: float
    free_space_gb: float
    usage_percentage: float
    total_files: int
    files_by_directory: Dict[str, int]

class BackupResponse(BaseModel):
    """Response model for backup operations"""
    success: bool
    backup_file: Optional[str] = None
    backup_size: Optional[int] = None
    timestamp: Optional[str] = None
    country_code: str
    error: Optional[str] = None
    backup_type: Optional[str] = None

class FileListResponse(BaseModel):
    """Response model for file listings"""
    success: bool
    files: List[Dict[str, Any]]
    total_count: int
    country_code: str

class LargestFilesResponse(BaseModel):
    """Response model for largest files listing"""
    success: bool
    largest_files: List[Dict[str, Any]]
    country_code: str

class StorageHealthResponse(BaseModel):
    """Response model for storage health check"""
    status: str  # healthy, warning, critical, error
    alerts: List[str]
    metrics: Dict[str, Any]
    country_code: str
    timestamp: str

# Request models
class FileDeleteRequest(BaseModel):
    """Request model for file deletion"""
    file_path: str
    reason: Optional[str] = None

class BackupRequest(BaseModel):
    """Request model for backup operations"""
    backup_type: str = Field(..., regex="^(daily|weekly|manual)$")
    include_audit: bool = True
    compress: bool = True 