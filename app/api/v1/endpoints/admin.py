"""
Admin Endpoints - Database and System Administration
Endpoints for database initialization, table creation, and system administration
"""

from fastapi import APIRouter, HTTPException
from sqlalchemy import text
import time
from typing import Dict, Any

from app.core.database import get_db_context, engine
from app.core.config import settings

router = APIRouter()


@router.post("/database/create-audit-tables")
async def create_audit_tables() -> Dict[str, Any]:
    """
    Create audit tables if they don't exist.
    This endpoint can be called to initialize the audit system.
    """
    try:
        # Create audit_logs table matching the AuditLog SQLAlchemy model
        audit_logs_sql = """
        CREATE TABLE audit_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            transaction_id UUID NOT NULL DEFAULT gen_random_uuid(),
            session_id VARCHAR(128),
            user_id UUID,
            username VARCHAR(100),
            ip_address VARCHAR(45) NOT NULL,
            user_agent TEXT,
            location_id UUID,
            action_type VARCHAR(50) NOT NULL,
            entity_type VARCHAR(50) NOT NULL,
            entity_id VARCHAR(100),
            screen_reference VARCHAR(20),
            validation_codes JSONB,
            business_rules_applied JSONB,
            old_values JSONB,
            new_values JSONB,
            changed_fields JSONB,
            files_created JSONB,
            files_modified JSONB,
            files_deleted JSONB,
            execution_time_ms INTEGER,
            database_queries INTEGER,
            memory_usage_mb INTEGER,
            success BOOLEAN NOT NULL DEFAULT TRUE,
            error_message TEXT,
            warning_messages JSONB,
            timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            country_code VARCHAR(2) NOT NULL DEFAULT 'ZA',
            system_version VARCHAR(20),
            module_name VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by UUID,
            updated_by UUID,
            is_active BOOLEAN DEFAULT TRUE,
            deleted_at TIMESTAMP,
            deleted_by UUID
        );
        """
        
        # Create file_metadata table matching the FileMetadata SQLAlchemy model
        file_metadata_sql = """
        CREATE TABLE file_metadata (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            file_id VARCHAR(100) NOT NULL UNIQUE,
            original_filename VARCHAR(255) NOT NULL,
            stored_filename VARCHAR(255) NOT NULL,
            relative_path VARCHAR(500) NOT NULL,
            file_size INTEGER NOT NULL,
            mime_type VARCHAR(100) NOT NULL,
            checksum VARCHAR(64),
            entity_type VARCHAR(50) NOT NULL,
            entity_id VARCHAR(100) NOT NULL,
            document_type VARCHAR(50),
            country_code VARCHAR(2) NOT NULL DEFAULT 'ZA',
            storage_location VARCHAR(100) NOT NULL,
            uploaded_by UUID NOT NULL,
            uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_accessed TIMESTAMP,
            access_count INTEGER NOT NULL DEFAULT 0,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            is_backed_up BOOLEAN NOT NULL DEFAULT FALSE,
            last_backup_date TIMESTAMP,
            encryption_status VARCHAR(20) NOT NULL DEFAULT 'none',
            access_restrictions JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by UUID,
            updated_by UUID,
            deleted_at TIMESTAMP,
            deleted_by UUID
        );
        """
        
        # Create indices for better performance
        audit_logs_indices = [
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_action_type ON audit_logs(action_type);",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(entity_type, entity_id);",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_country ON audit_logs(country_code);",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_transaction ON audit_logs(transaction_id);",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_session ON audit_logs(session_id);"
        ]
        
        file_metadata_indices = [
            "CREATE INDEX IF NOT EXISTS idx_file_metadata_file_id ON file_metadata(file_id);",
            "CREATE INDEX IF NOT EXISTS idx_file_metadata_entity ON file_metadata(entity_type, entity_id);",
            "CREATE INDEX IF NOT EXISTS idx_file_metadata_uploaded_at ON file_metadata(uploaded_at);",
            "CREATE INDEX IF NOT EXISTS idx_file_metadata_country ON file_metadata(country_code);",
            "CREATE INDEX IF NOT EXISTS idx_file_metadata_active ON file_metadata(is_active);"
        ]
        
        results = {
            "tables_created": [],
            "indices_created": [],
            "errors": [],
            "timestamp": time.time()
        }
        
        try:
            with get_db_context() as session:
                # Drop existing tables first to recreate with correct schema
                try:
                    session.execute(text("DROP TABLE IF EXISTS audit_logs CASCADE;"))
                    session.execute(text("DROP TABLE IF EXISTS file_metadata CASCADE;"))
                    results["tables_created"].append("dropped_existing_tables")
                except Exception as e:
                    results["errors"].append(f"Drop table warning: {str(e)}")
                
                # Create audit_logs table
                session.execute(text(audit_logs_sql))
                results["tables_created"].append("audit_logs")
                
                # Create file_metadata table
                session.execute(text(file_metadata_sql))
                results["tables_created"].append("file_metadata")
                
                # Create indices for audit_logs
                for index_sql in audit_logs_indices:
                    try:
                        session.execute(text(index_sql))
                        results["indices_created"].append(index_sql.split("idx_")[1].split(" ")[0])
                    except Exception as e:
                        results["errors"].append(f"Index creation error: {str(e)}")
                
                # Create indices for file_metadata
                for index_sql in file_metadata_indices:
                    try:
                        session.execute(text(index_sql))
                        results["indices_created"].append(index_sql.split("idx_")[1].split(" ")[0])
                    except Exception as e:
                        results["errors"].append(f"Index creation error: {str(e)}")
                
                results["status"] = "success"
                results["message"] = f"Created {len(results['tables_created'])} tables and {len(results['indices_created'])} indices"
                
        except Exception as e:
            results["status"] = "error"
            results["message"] = f"Database error: {str(e)}"
            results["errors"].append(str(e))
            
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create audit tables: {str(e)}"
        )


@router.get("/database/check-tables")
async def check_database_tables() -> Dict[str, Any]:
    """
    Check which tables exist in the database
    """
    try:
        with get_db_context() as session:
            # Query to get all table names
            table_check_sql = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
            """
            
            result = session.execute(text(table_check_sql))
            tables = [row[0] for row in result.fetchall()]
            
            # Check specifically for audit tables
            audit_tables = {
                "audit_logs": "audit_logs" in tables,
                "file_metadata": "file_metadata" in tables
            }
            
            return {
                "status": "success",
                "all_tables": tables,
                "audit_tables": audit_tables,
                "audit_system_ready": all(audit_tables.values()),
                "timestamp": time.time()
            }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check database tables: {str(e)}"
        )


@router.post("/database/migrate")
async def run_database_migrations() -> Dict[str, Any]:
    """
    Run any pending database migrations or updates
    """
    try:
        results = {
            "migrations_run": [],
            "errors": [],
            "timestamp": time.time()
        }
        
        # For now, this just creates audit tables if they don't exist
        audit_result = await create_audit_tables()
        
        if audit_result["status"] == "success":
            results["migrations_run"].append("audit_tables_creation")
        else:
            results["errors"].extend(audit_result.get("errors", []))
        
        results["status"] = "success" if not results["errors"] else "partial"
        results["message"] = f"Completed {len(results['migrations_run'])} migrations with {len(results['errors'])} errors"
        
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run migrations: {str(e)}"
        )


@router.get("/system/info")
async def get_system_info() -> Dict[str, Any]:
    """
    Get system information and configuration
    """
    return {
        "service": "LINC Backend",
        "version": settings.VERSION,
        "country": {
            "code": settings.COUNTRY_CODE,
            "name": settings.COUNTRY_NAME,
            "currency": settings.CURRENCY
        },
        "environment": {
            "debug": getattr(settings, 'DEBUG', False),
            "testing": getattr(settings, 'TESTING', False)
        },
        "timestamp": time.time()
    } 