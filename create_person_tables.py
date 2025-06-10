#!/usr/bin/env python3
"""
Person Management Tables Creation Script
Adds person, natural_person, person_aliases, and person_addresses tables to existing database
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

from app.core.database import Base, engine
from app.models.person import Person, PersonAlias, NaturalPerson, PersonAddress

def create_person_tables():
    """Create person management tables"""
    try:
        print("🔄 Creating person management tables...")
        
        # Import all models to ensure they're registered
        from app.models import *
        
        # Create only the person-related tables
        person_tables = [Person, PersonAlias, NaturalPerson, PersonAddress]
        
        for table_model in person_tables:
            try:
                table_model.__table__.create(engine, checkfirst=True)
                print(f"✅ Created table: {table_model.__tablename__}")
            except Exception as e:
                print(f"⚠️  Table {table_model.__tablename__} already exists or error: {str(e)}")
        
        print("✅ Person management tables created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating person tables: {str(e)}")
        return False

def verify_tables():
    """Verify that tables were created successfully"""
    try:
        print("\n🔍 Verifying table creation...")
        
        with engine.connect() as conn:
            # Check each table
            tables_to_check = [
                'persons',
                'person_aliases', 
                'natural_persons',
                'person_addresses'
            ]
            
            for table_name in tables_to_check:
                result = conn.execute(text(f"SELECT 1 FROM information_schema.tables WHERE table_name = '{table_name}'"))
                if result.fetchone():
                    print(f"✅ Table verified: {table_name}")
                else:
                    print(f"❌ Table missing: {table_name}")
                    return False
            
            print("✅ All person tables verified successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Error verifying tables: {str(e)}")
        return False

def show_table_info():
    """Show information about the created tables"""
    try:
        print("\n📋 Table Information:")
        
        with engine.connect() as conn:
            # Get table info
            tables = [
                ('persons', 'Main person entity - individuals and organizations'),
                ('person_aliases', 'ID documents and aliases for persons'),
                ('natural_persons', 'Additional details for natural persons (individuals)'),
                ('person_addresses', 'Addresses for persons (residential, postal, business)')
            ]
            
            for table_name, description in tables:
                result = conn.execute(text(f"""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}' 
                    ORDER BY ordinal_position
                """))
                
                columns = result.fetchall()
                print(f"\n📁 {table_name}: {description}")
                print(f"   Columns: {len(columns)}")
                for col in columns[:5]:  # Show first 5 columns
                    print(f"   - {col[0]} ({col[1]}) {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
                if len(columns) > 5:
                    print(f"   ... and {len(columns) - 5} more columns")
        
    except Exception as e:
        print(f"❌ Error showing table info: {str(e)}")

if __name__ == "__main__":
    print("🚀 LINC Person Management Tables Creation")
    print("=" * 50)
    
    # Check database connection
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        print("\n💡 Make sure your DATABASE_URL environment variable is set correctly")
        sys.exit(1)
    
    # Create tables
    if create_person_tables():
        if verify_tables():
            show_table_info()
            print("\n🎉 Person management system ready!")
            print("\n📖 Next steps:")
            print("1. Test the API endpoints at: /docs")
            print("2. Create some test persons")
            print("3. Try the search functionality")
            print("4. Test person validation")
        else:
            print("\n❌ Table verification failed!")
            sys.exit(1)
    else:
        print("\n❌ Table creation failed!")
        sys.exit(1) 