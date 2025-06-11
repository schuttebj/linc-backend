"""
Database Migration Script - Phone Numbers and Additional Fields
Updates existing tables to support international phone format and new fields
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import get_settings
from app.core.database import Base
from app.models.person import Person, PersonAlias, NaturalPerson, PersonAddress

def run_migration():
    """Run the database migration"""
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    
    print("Starting migration: Phone Numbers and Additional Fields")
    
    with engine.connect() as connection:
        # Start transaction
        trans = connection.begin()
        
        try:
            print("1. Adding expiry date column to person_aliases table...")
            connection.execute(text("""
                ALTER TABLE person_aliases 
                ADD COLUMN IF NOT EXISTS id_document_expiry_date DATE;
            """))
            
            print("2. Updating phone number columns in persons table...")
            
            # First, add new columns 
            connection.execute(text("""
                ALTER TABLE persons 
                ADD COLUMN IF NOT EXISTS home_phone_number_new VARCHAR(20),
                ADD COLUMN IF NOT EXISTS work_phone_number_new VARCHAR(20),
                ADD COLUMN IF NOT EXISTS cell_phone_country_code VARCHAR(5),
                ADD COLUMN IF NOT EXISTS cell_phone_new VARCHAR(15),
                ADD COLUMN IF NOT EXISTS fax_number_new VARCHAR(20);
            """))
            
            print("3. Migrating existing phone data to new format...")
            
            # Migrate existing phone data 
            # Keep home/work/fax as-is, split cell phone into country code + number
            connection.execute(text("""
                UPDATE persons SET 
                    home_phone_number_new = CASE 
                        WHEN home_phone_number IS NOT NULL AND home_phone_number != '' THEN 
                            COALESCE(home_phone_code, '') || home_phone_number
                        ELSE NULL 
                    END,
                    work_phone_number_new = CASE 
                        WHEN work_phone_number IS NOT NULL AND work_phone_number != '' THEN 
                            COALESCE(work_phone_code, '') || work_phone_number
                        ELSE NULL 
                    END,
                    cell_phone_country_code = CASE 
                        WHEN cell_phone IS NOT NULL AND cell_phone != '' THEN 
                            CASE 
                                WHEN cell_phone LIKE '+%' THEN SUBSTRING(cell_phone FROM 1 FOR POSITION(' ' IN cell_phone || ' ') - 1)
                                ELSE '+27'
                            END
                        ELSE NULL 
                    END,
                    cell_phone_new = CASE 
                        WHEN cell_phone IS NOT NULL AND cell_phone != '' THEN 
                            CASE 
                                WHEN cell_phone LIKE '+%' THEN REGEXP_REPLACE(cell_phone, '^\\+\\d{1,4}', '')
                                WHEN cell_phone LIKE '0%' THEN SUBSTRING(cell_phone FROM 2)
                                ELSE cell_phone
                            END
                        ELSE NULL 
                    END,
                    fax_number_new = CASE 
                        WHEN fax_number IS NOT NULL AND fax_number != '' THEN 
                            COALESCE(fax_code, '') || fax_number
                        ELSE NULL 
                    END;
            """))
            
            print("4. Dropping old phone columns...")
            
            # Drop old phone columns and rename new ones
            connection.execute(text("""
                ALTER TABLE persons 
                DROP COLUMN IF EXISTS home_phone_code,
                DROP COLUMN IF EXISTS work_phone_code,
                DROP COLUMN IF EXISTS fax_code,
                DROP COLUMN IF EXISTS home_phone_number,
                DROP COLUMN IF EXISTS work_phone_number,
                DROP COLUMN IF EXISTS fax_number,
                DROP COLUMN IF EXISTS cell_phone;
            """))
            
            print("5. Renaming new phone columns...")
            
            # Rename new columns to final names
            connection.execute(text("""
                ALTER TABLE persons 
                RENAME COLUMN home_phone_number_new TO home_phone_number,
                RENAME COLUMN work_phone_number_new TO work_phone_number,
                RENAME COLUMN cell_phone_new TO cell_phone,
                RENAME COLUMN fax_number_new TO fax_number;
            """))
            
            print("6. Updating column constraints...")
            
            # Update column types and constraints
            connection.execute(text("""
                ALTER TABLE persons 
                ALTER COLUMN home_phone_number TYPE VARCHAR(20),
                ALTER COLUMN work_phone_number TYPE VARCHAR(20),
                ALTER COLUMN cell_phone_country_code TYPE VARCHAR(5),
                ALTER COLUMN cell_phone TYPE VARCHAR(15),
                ALTER COLUMN fax_number TYPE VARCHAR(20);
            """))
            
            print("7. Adding comments to new columns...")
            
            # Add comments
            connection.execute(text("""
                COMMENT ON COLUMN persons.home_phone_number IS 'Home phone number';
                COMMENT ON COLUMN persons.work_phone_number IS 'Work phone number';
                COMMENT ON COLUMN persons.cell_phone_country_code IS 'Cell phone country code (e.g., +27)';
                COMMENT ON COLUMN persons.cell_phone IS 'Cell phone number (without country code)';
                COMMENT ON COLUMN persons.fax_number IS 'Fax number';
                COMMENT ON COLUMN person_aliases.id_document_expiry_date IS 'ID document expiry date (required for foreign documents)';
            """))
            
            print("8. Creating indexes for performance...")
            
            # Create indexes for the new fields
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_person_aliases_expiry_date 
                ON person_aliases(id_document_expiry_date);
            """))
            
            # Commit transaction
            trans.commit()
            print("Migration completed successfully!")
            
        except Exception as e:
            # Rollback on error
            trans.rollback()
            print(f"Migration failed: {e}")
            raise

def verify_migration():
    """Verify the migration was successful"""
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    
    print("\nVerifying migration...")
    
    with engine.connect() as connection:
        # Check if new columns exist
        result = connection.execute(text("""
            SELECT column_name, data_type, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name IN ('persons', 'person_aliases') 
            AND column_name IN ('home_phone_number', 'work_phone_number', 'cell_phone_country_code', 'cell_phone', 'fax_number', 'id_document_expiry_date')
            ORDER BY table_name, column_name;
        """))
        
        columns = result.fetchall()
        print("Updated columns:")
        for col in columns:
            print(f"  {col[0]}: {col[1]}({col[2] or 'N/A'})")
        
        # Check data migration
        result = connection.execute(text("""
            SELECT COUNT(*) as total_persons,
                   COUNT(CASE WHEN cell_phone_country_code = '+27' THEN 1 END) as sa_country_codes,
                   COUNT(CASE WHEN cell_phone IS NOT NULL AND cell_phone != '' THEN 1 END) as has_cell_numbers
            FROM persons;
        """))
        
        data = result.fetchone()
        print(f"\nData verification:")
        print(f"  Total persons: {data[0]}")
        print(f"  SA country codes (+27): {data[1]}")
        print(f"  Has cell phone numbers: {data[2]}")
        
    print("Migration verification completed!")

if __name__ == "__main__":
    print("=" * 60)
    print("LINC Backend - Phone Numbers Migration")
    print("=" * 60)
    
    try:
        run_migration()
        verify_migration()
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1) 