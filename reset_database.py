#!/usr/bin/env python3
"""
LINC Database Reset Script
Drops all existing tables and recreates them with the new structure
"""

import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import DatabaseManager
from app.models import *  # Import all models to register them

def main():
    """Drop all tables and recreate them"""
    print("🗑️  Dropping all existing tables...")
    
    try:
        # Drop all tables
        DatabaseManager.drop_all_tables()
        print("✅ All tables dropped successfully")
        
        # Recreate all tables
        print("\n🏗️  Creating new tables...")
        DatabaseManager.create_all_tables()
        print("✅ All tables created successfully")
        
        print("\n🎉 Database reset complete!")
        print("📋 Next step: Run create_user_system.py to populate with data")
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 