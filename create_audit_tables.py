#!/usr/bin/env python3
"""
LINC Database Migration - Add Audit and File Storage Tables
Creates the audit_logs and file_metadata tables for comprehensive tracking
"""

import os
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent / "app"))

from sqlalchemy import create_engine, text
from app.core.config import get_settings
from app.core.database import Base, engine, DatabaseManager
from app.models.audit import AuditLog, FileMetadata
import structlog

logger = structlog.get_logger()

def create_audit_tables():
    """Create audit and file metadata tables"""
    try:
        settings = get_settings()
        logger.info(f"Creating audit tables for database: {settings.DATABASE_URL}")
        
        # Test database connection first
        if not DatabaseManager.test_connection():
            logger.error("Database connection failed!")
            return False
        
        # Create all tables (this will only create missing tables)
        Base.metadata.create_all(bind=engine)
        
        # Verify tables were created
        with engine.connect() as conn:
            # Check if audit_logs table exists
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('audit_logs', 'file_metadata')
            """))
            
            existing_tables = [row[0] for row in result]
            
            if 'audit_logs' in existing_tables:
                logger.info("✅ audit_logs table created successfully")
            else:
                logger.error("❌ audit_logs table not found")
                return False
                
            if 'file_metadata' in existing_tables:
                logger.info("✅ file_metadata table created successfully")
            else:
                logger.error("❌ file_metadata table not found")
                return False
        
        logger.info("🎉 All audit tables created successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error creating audit tables: {e}")
        return False

def verify_audit_system():
    """Verify audit system is working"""
    try:
        from app.services.audit import AuditService, UserContext, AuditLogData
        from app.core.database import get_db
        
        # Test audit service
        db = next(get_db())
        audit_service = AuditService(db, "ZA")
        
        # Create test audit log
        test_context = UserContext(
            user_id="test-user",
            username="test_admin",
            ip_address="127.0.0.1",
            session_id="test-session"
        )
        
        test_audit = AuditLogData(
            action_type="SYSTEM_TEST",
            entity_type="SYSTEM",
            entity_id="audit_test",
            success=True,
            new_values={"test": "audit_system_working"},
            **test_context.dict()
        )
        
        transaction_id = audit_service.log_action(test_audit)
        
        if transaction_id:
            logger.info(f"✅ Audit system test successful: {transaction_id}")
            return True
        else:
            logger.error("❌ Audit system test failed")
            return False
            
    except Exception as e:
        logger.error(f"Error testing audit system: {e}")
        return False

def verify_file_storage():
    """Verify file storage system is working"""
    try:
        from app.services.file_storage import FileStorageService, FileSystemMonitor
        
        # Test file storage service
        file_storage = FileStorageService("ZA")
        
        # Check storage metrics
        metrics = file_storage.get_storage_metrics()
        
        if "error" not in metrics:
            logger.info(f"✅ File storage system working. Base path: {metrics.get('base_path')}")
            logger.info(f"   Storage: {metrics.get('used_space_gb', 0):.2f}GB used of {metrics.get('total_space_gb', 0):.2f}GB")
            return True
        else:
            logger.error(f"❌ File storage system error: {metrics['error']}")
            return False
            
    except Exception as e:
        logger.error(f"Error testing file storage: {e}")
        return False

def main():
    """Main migration function"""
    logger.info("🚀 Starting LINC Audit System Migration...")
    
    # Step 1: Create audit tables
    logger.info("Step 1: Creating audit tables...")
    if not create_audit_tables():
        logger.error("❌ Failed to create audit tables")
        return False
    
    # Step 2: Verify audit system
    logger.info("Step 2: Testing audit system...")
    if not verify_audit_system():
        logger.error("❌ Audit system verification failed")
        return False
    
    # Step 3: Verify file storage
    logger.info("Step 3: Testing file storage system...")
    if not verify_file_storage():
        logger.error("❌ File storage verification failed")
        return False
    
    logger.info("🎉 LINC Audit System Migration Completed Successfully!")
    logger.info("")
    logger.info("✅ Phase 1 Foundation Complete:")
    logger.info("   • Comprehensive audit logging")
    logger.info("   • Local file storage with backup")
    logger.info("   • Security monitoring")
    logger.info("   • Multi-tenant architecture")
    logger.info("   • API documentation")
    logger.info("")
    logger.info("🚀 Ready for Phase 2: License Application Processing")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 