"""
LINC Audit Log Database Models
Comprehensive audit logging model for all system actions
Reference: linc-file-storage-audit.mdc requirements
"""

from sqlalchemy import Column, String, DateTime, JSON, Text, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime
import uuid

from app.models.base import BaseModel

class AuditLog(BaseModel):
    """
    Comprehensive audit logging model for all system actions
    Reference: Business Rules - Audit and Compliance Requirements
    """
    __tablename__ = "audit_logs"
    
    # Core identification
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(PGUUID(as_uuid=True), nullable=False, default=uuid.uuid4)
    session_id = Column(String(128), nullable=True)
    
    # User and system context
    user_id = Column(PGUUID(as_uuid=True), nullable=True)
    username = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=False)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    location_id = Column(PGUUID(as_uuid=True), nullable=True)
    
    # Action details
    action_type = Column(String(50), nullable=False)  # CREATE, UPDATE, DELETE, VIEW, PRINT, etc.
    entity_type = Column(String(50), nullable=False)  # PERSON, LICENSE, APPLICATION, etc.
    entity_id = Column(String(100), nullable=True)
    screen_reference = Column(String(20), nullable=True)  # P00068, etc.
    
    # Business rule tracking
    validation_codes = Column(JSON, nullable=True)  # List of validation codes applied
    business_rules_applied = Column(JSON, nullable=True)  # List of business rules
    
    # Data change tracking
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    changed_fields = Column(JSON, nullable=True)
    
    # File operations
    files_created = Column(JSON, nullable=True)
    files_modified = Column(JSON, nullable=True)
    files_deleted = Column(JSON, nullable=True)
    
    # System metrics
    execution_time_ms = Column(Integer, nullable=True)
    database_queries = Column(Integer, nullable=True)
    memory_usage_mb = Column(Integer, nullable=True)
    
    # Status and results
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)
    warning_messages = Column(JSON, nullable=True)
    
    # Timestamps
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Metadata
    country_code = Column(String(2), nullable=False)
    system_version = Column(String(20), nullable=True)
    module_name = Column(String(50), nullable=False)
    
    def __repr__(self):
        return f"<AuditLog {self.id}: {self.action_type}:{self.entity_type} by {self.username}>"

class FileMetadata(BaseModel):
    """
    File metadata tracking for audit and management
    """
    __tablename__ = "file_metadata"
    
    # Core identification
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = Column(String(100), nullable=False, unique=True)
    
    # File information
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    relative_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    checksum = Column(String(64), nullable=True)  # SHA-256 hash
    
    # Entity relationship
    entity_type = Column(String(50), nullable=False)  # PERSON, LICENSE, etc.
    entity_id = Column(String(100), nullable=False)
    document_type = Column(String(50), nullable=True)  # photo, document, card, etc.
    
    # Storage metadata
    country_code = Column(String(2), nullable=False)
    storage_location = Column(String(100), nullable=False)  # local, backup, archive
    
    # File lifecycle
    uploaded_by = Column(PGUUID(as_uuid=True), nullable=False)
    uploaded_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_accessed = Column(DateTime, nullable=True)
    access_count = Column(Integer, nullable=False, default=0)
    
    # Status and flags
    is_active = Column(Boolean, nullable=False, default=True)
    is_backed_up = Column(Boolean, nullable=False, default=False)
    last_backup_date = Column(DateTime, nullable=True)
    
    # Security
    encryption_status = Column(String(20), nullable=False, default="none")  # none, encrypted
    access_restrictions = Column(JSON, nullable=True)  # Role-based access rules
    
    def __repr__(self):
        return f"<FileMetadata {self.file_id}: {self.original_filename}>" 