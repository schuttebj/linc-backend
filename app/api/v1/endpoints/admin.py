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
        # Create audit_logs table
        audit_logs_sql = """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id SERIAL PRIMARY KEY,
            action VARCHAR(50) NOT NULL,
            entity_type VARCHAR(100),
            entity_id VARCHAR(100),
            user_id INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            details JSONB,
            ip_address INET,
            user_agent TEXT,
            success BOOLEAN DEFAULT TRUE,
            error_message TEXT,
            session_id VARCHAR(255),
            country_code VARCHAR(10) DEFAULT 'ZA'
        );
        """
        
        # Create audit_events table 
        audit_events_sql = """
        CREATE TABLE IF NOT EXISTS audit_events (
            id SERIAL PRIMARY KEY,
            event_type VARCHAR(100) NOT NULL,
            event_data JSONB,
            user_id INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            source VARCHAR(100),
            severity VARCHAR(20) DEFAULT 'INFO',
            country_code VARCHAR(10) DEFAULT 'ZA'
        );
        """
        
        # Create indices for better performance
        audit_logs_indices = [
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(entity_type, entity_id);",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_country ON audit_logs(country_code);"
        ]
        
        audit_events_indices = [
            "CREATE INDEX IF NOT EXISTS idx_audit_events_timestamp ON audit_events(timestamp);",
            "CREATE INDEX IF NOT EXISTS idx_audit_events_type ON audit_events(event_type);",
            "CREATE INDEX IF NOT EXISTS idx_audit_events_user ON audit_events(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_audit_events_country ON audit_events(country_code);"
        ]
        
        results = {
            "tables_created": [],
            "indices_created": [],
            "errors": [],
            "timestamp": time.time()
        }
        
        try:
            with get_db_context() as session:
                # Create audit_logs table
                session.execute(text(audit_logs_sql))
                results["tables_created"].append("audit_logs")
                
                # Create audit_events table
                session.execute(text(audit_events_sql))
                results["tables_created"].append("audit_events")
                
                # Create indices for audit_logs
                for index_sql in audit_logs_indices:
                    try:
                        session.execute(text(index_sql))
                        results["indices_created"].append(index_sql.split("idx_")[1].split(" ")[0])
                    except Exception as e:
                        results["errors"].append(f"Index creation error: {str(e)}")
                
                # Create indices for audit_events
                for index_sql in audit_events_indices:
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
                "audit_events": "audit_events" in tables
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
            "debug": settings.DEBUG,
            "testing": getattr(settings, 'TESTING', False)
        },
        "timestamp": time.time()
    } 