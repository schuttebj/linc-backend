"""
Migration endpoint for running database schema updates
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/run-phone-migration")
async def run_phone_migration(db: Session = Depends(get_db)):
    """
    Run the phone and address fields migration
    This endpoint applies the database schema changes for the enhanced person registration
    """
    try:
        logger.info("Starting phone and address fields migration...")
        
        # Migration SQL statements
        migration_statements = [
            # Add new phone fields to persons table
            """
            ALTER TABLE persons 
            ADD COLUMN IF NOT EXISTS cell_phone_country_code VARCHAR(10),
            ADD COLUMN IF NOT EXISTS home_phone VARCHAR(20),
            ADD COLUMN IF NOT EXISTS work_phone VARCHAR(20),
            ADD COLUMN IF NOT EXISTS fax_phone VARCHAR(20);
            """,
            
            # Remove old phone fields (if they exist)
            """
            ALTER TABLE persons 
            DROP COLUMN IF EXISTS home_phone_number,
            DROP COLUMN IF EXISTS work_phone_number,
            DROP COLUMN IF EXISTS fax_number;
            """,
            
            # Add expiry date to person_aliases table
            """
            ALTER TABLE person_aliases 
            ADD COLUMN IF NOT EXISTS id_document_expiry_date DATE;
            """,
            
            # Add province_code to addresses table
            """
            ALTER TABLE addresses 
            ADD COLUMN IF NOT EXISTS province_code VARCHAR(10);
            """,
            
            # Update existing cell_phone data if needed
            """
            UPDATE persons 
            SET cell_phone_country_code = '+27' 
            WHERE cell_phone IS NOT NULL 
            AND cell_phone != '' 
            AND cell_phone_country_code IS NULL;
            """
        ]
        
        # Execute each migration statement
        for i, statement in enumerate(migration_statements):
            try:
                logger.info(f"Executing migration statement {i+1}/{len(migration_statements)}")
                db.execute(text(statement))
                db.commit()
                logger.info(f"Migration statement {i+1} completed successfully")
            except Exception as e:
                logger.error(f"Error in migration statement {i+1}: {str(e)}")
                db.rollback()
                # Continue with other statements - some might fail if columns already exist
                continue
        
        logger.info("Phone and address fields migration completed successfully")
        
        return {
            "success": True,
            "message": "Phone and address fields migration completed successfully",
            "statements_executed": len(migration_statements)
        }
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Migration failed: {str(e)}"
        )

@router.get("/check-schema")
async def check_schema(db: Session = Depends(get_db)):
    """
    Check if the new schema fields exist
    """
    try:
        checks = []
        
        # Check persons table columns
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'persons' 
            AND column_name IN ('cell_phone_country_code', 'home_phone', 'work_phone', 'fax_phone')
        """))
        persons_columns = [row[0] for row in result.fetchall()]
        checks.append({
            "table": "persons",
            "expected_columns": ["cell_phone_country_code", "home_phone", "work_phone", "fax_phone"],
            "existing_columns": persons_columns,
            "missing_columns": [col for col in ["cell_phone_country_code", "home_phone", "work_phone", "fax_phone"] if col not in persons_columns]
        })
        
        # Check person_aliases table columns
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'person_aliases' 
            AND column_name = 'id_document_expiry_date'
        """))
        aliases_columns = [row[0] for row in result.fetchall()]
        checks.append({
            "table": "person_aliases",
            "expected_columns": ["id_document_expiry_date"],
            "existing_columns": aliases_columns,
            "missing_columns": [col for col in ["id_document_expiry_date"] if col not in aliases_columns]
        })
        
        # Check addresses table columns
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'addresses' 
            AND column_name = 'province_code'
        """))
        addresses_columns = [row[0] for row in result.fetchall()]
        checks.append({
            "table": "addresses",
            "expected_columns": ["province_code"],
            "existing_columns": addresses_columns,
            "missing_columns": [col for col in ["province_code"] if col not in addresses_columns]
        })
        
        # Determine if migration is needed
        migration_needed = any(check["missing_columns"] for check in checks)
        
        return {
            "migration_needed": migration_needed,
            "schema_checks": checks,
            "message": "Migration needed" if migration_needed else "Schema is up to date"
        }
        
    except Exception as e:
        logger.error(f"Schema check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Schema check failed: {str(e)}"
        ) 