#!/usr/bin/env python3
"""
LINC Force Database Reset Script
Uses raw SQL to drop all tables regardless of foreign key constraints
"""

import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.core.database import DatabaseManager
from app.models import *  # Import all models

def main():
    """Force drop all tables and recreate them"""
    print("🗑️  Force dropping all existing tables...")
    
    try:
        # Create engine directly
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                print("📋 Getting list of all tables...")
                
                # Get all table names
                result = conn.execute(text("""
                    SELECT tablename FROM pg_tables 
                    WHERE schemaname = 'public'
                    AND tablename NOT LIKE 'pg_%'
                    AND tablename NOT LIKE 'information_schema%'
                """))
                
                tables = [row[0] for row in result.fetchall()]
                print(f"Found {len(tables)} tables: {', '.join(tables)}")
                
                if tables:
                    print("🔥 Dropping all tables with CASCADE...")
                    
                    # Drop all tables with CASCADE to ignore foreign key constraints
                    for table in tables:
                        print(f"  Dropping table: {table}")
                        conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                    
                    print("✅ All tables dropped successfully")
                else:
                    print("ℹ️  No tables found to drop")
                
                # Also drop any remaining sequences, views, etc.
                print("🧹 Cleaning up sequences and views...")
                
                # Drop sequences
                seq_result = conn.execute(text("""
                    SELECT sequence_name FROM information_schema.sequences 
                    WHERE sequence_schema = 'public'
                """))
                sequences = [row[0] for row in seq_result.fetchall()]
                for seq in sequences:
                    print(f"  Dropping sequence: {seq}")
                    conn.execute(text(f"DROP SEQUENCE IF EXISTS {seq} CASCADE"))
                
                # Drop views
                view_result = conn.execute(text("""
                    SELECT table_name FROM information_schema.views 
                    WHERE table_schema = 'public'
                """))
                views = [row[0] for row in view_result.fetchall()]
                for view in views:
                    print(f"  Dropping view: {view}")
                    conn.execute(text(f"DROP VIEW IF EXISTS {view} CASCADE"))
                
                # Commit the drops
                trans.commit()
                print("✅ Database cleanup completed")
                
            except Exception as e:
                trans.rollback()
                raise e
        
        # Now recreate all tables using SQLAlchemy
        print("\n🏗️  Creating new tables...")
        
        # Create all tables
        DatabaseManager.create_all_tables()
        print("✅ All tables created successfully")
        
        print("\n🎉 Database force reset complete!")
        print("📋 Next step: Run create_user_system.py to populate with data")
        
        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY tablename
            """))
            new_tables = [row[0] for row in result.fetchall()]
            print(f"\n📊 New tables created ({len(new_tables)}): {', '.join(new_tables)}")
        
    except Exception as e:
        print(f"❌ Error force resetting database: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 