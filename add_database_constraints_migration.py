"""
Database Migration: Add Missing Constraints for Development Standards Compliance
Adds the database constraints specified in the LINC Users/Locations Development Standards

This migration adds:
- User group code format validation (4 characters, alphanumeric)
- Province code format validation (2 characters, letters)
- Office code format validation (single letter A-Z)
- Unique constraint on user_group_id + office_code combination
"""

from sqlalchemy import text
from app.core.database import get_db

def upgrade_database():
    """
    Apply database constraints as per development standards
    """
    db = next(get_db())
    
    try:
        print("Adding database constraints for development standards compliance...")
        
        # 1. Add user group code format constraint
        print("Adding user group code format constraint...")
        db.execute(text("""
            ALTER TABLE user_groups 
            ADD CONSTRAINT chk_user_group_code_format 
            CHECK (user_group_code ~ '^[A-Z0-9]{4}$');
        """))
        
        # 2. Add province code format constraint
        print("Adding province code format constraint...")
        db.execute(text("""
            ALTER TABLE user_groups 
            ADD CONSTRAINT chk_province_code_format 
            CHECK (province_code ~ '^[A-Z]{2}$');
        """))
        
        # 3. Add office code format constraint
        print("Adding office code format constraint...")
        db.execute(text("""
            ALTER TABLE offices 
            ADD CONSTRAINT chk_office_code_format 
            CHECK (office_code ~ '^[A-Z]$');
        """))
        
        # 4. Add unique constraint on user_group_id + office_code
        print("Adding unique constraint on user_group_id + office_code...")
        db.execute(text("""
            ALTER TABLE offices 
            ADD CONSTRAINT uq_office_user_group_code 
            UNIQUE (user_group_id, office_code);
        """))
        
        # 5. Add indexes for performance (if not already present)
        print("Adding performance indexes...")
        try:
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_user_groups_code ON user_groups(user_group_code);"))
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_user_groups_province ON user_groups(province_code);"))
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_user_groups_type ON user_groups(user_group_type);"))
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_locations_code ON locations(location_code);"))
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_locations_user_group ON locations(user_group_id);"))
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_locations_province ON locations(province_code);"))
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_user_location_assignments_user ON user_location_assignments(user_id);"))
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_user_location_assignments_location ON user_location_assignments(location_id);"))
        except Exception as e:
            print(f"Note: Some indexes may already exist: {str(e)}")
        
        db.commit()
        print("✅ Database constraints added successfully!")
        
    except Exception as e:
        print(f"❌ Error adding database constraints: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

def downgrade_database():
    """
    Remove database constraints (for rollback)
    """
    db = next(get_db())
    
    try:
        print("Removing database constraints...")
        
        # Remove constraints in reverse order
        db.execute(text("ALTER TABLE offices DROP CONSTRAINT IF EXISTS uq_office_user_group_code;"))
        db.execute(text("ALTER TABLE offices DROP CONSTRAINT IF EXISTS chk_office_code_format;"))
        db.execute(text("ALTER TABLE user_groups DROP CONSTRAINT IF EXISTS chk_province_code_format;"))
        db.execute(text("ALTER TABLE user_groups DROP CONSTRAINT IF EXISTS chk_user_group_code_format;"))
        
        db.commit()
        print("✅ Database constraints removed successfully!")
        
    except Exception as e:
        print(f"❌ Error removing database constraints: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--downgrade":
        downgrade_database()
    else:
        upgrade_database() 