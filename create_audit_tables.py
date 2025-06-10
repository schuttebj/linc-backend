#!/usr/bin/env python3
"""
Create audit_logs table migration
Creates the missing audit_logs table for the audit system
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import get_settings
from app.models.audit import AuditLog, FileMetadata
from app.core.database import Base

def create_audit_tables():
    """Create audit tables if they don't exist"""
    settings = get_settings()
    
    # Create engine
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        # Create tables
        print("Creating audit tables...")
        Base.metadata.create_all(bind=engine, tables=[
            AuditLog.__table__,
            FileMetadata.__table__
        ])
        
        print("✅ Audit tables created successfully!")
        
        # Verify tables exist
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('audit_logs', 'file_metadata')
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result]
            print(f"✅ Verified tables exist: {tables}")
        
    except Exception as e:
        print(f"❌ Error creating audit tables: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("LINC Audit Tables Creation")
    print("=" * 40)
    
    success = create_audit_tables()
    
    if success:
        print("\n🎉 Audit system tables are ready!")
    else:
        print("\n💥 Failed to create audit tables")
        sys.exit(1) 