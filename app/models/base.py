"""
Base Database Model
Common functionality and audit fields for all LINC models
"""

from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from datetime import datetime
import uuid

from app.core.database import Base


class BaseModel(Base):
    """Base model with common fields and functionality"""
    __abstract__ = True
    
    @declared_attr
    def __tablename__(cls):
        """Generate table name from class name"""
        # Convert CamelCase to snake_case
        import re
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=True)  # User ID who created the record
    updated_by = Column(UUID(as_uuid=True), nullable=True)  # User ID who last updated the record
    
    # Soft delete support
    is_active = Column(Boolean, default=True, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Country context for multi-tenant support
    country_code = Column(String(2), nullable=False, index=True)
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, uuid.UUID):
                value = str(value)
            result[column.name] = value
        return result
    
    def soft_delete(self, deleted_by_user_id: uuid.UUID = None):
        """Soft delete the record"""
        self.is_active = False
        self.deleted_at = datetime.utcnow()
        self.deleted_by = deleted_by_user_id
    
    def restore(self):
        """Restore a soft-deleted record"""
        self.is_active = True
        self.deleted_at = None
        self.deleted_by = None 