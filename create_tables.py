#!/usr/bin/env python3
"""
LINC Database Table Creation Script

This script creates all database tables for the LINC system including:
- Person entities
- License applications
- License cards
- Application payments
- Test centers

Usage:
    python create_tables.py
"""

import sys
import os
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from app.core.database import DatabaseManager, engine
from app.models import *  # Import all models
import structlog

logger = structlog.get_logger()


def main():
    """Create all database tables"""
    try:
        logger.info("Starting database table creation...")
        
        # Test database connection first
        if not DatabaseManager.test_connection():
            logger.error("Database connection failed. Please check your configuration.")
            sys.exit(1)
        
        # Create all tables
        DatabaseManager.create_all_tables()
        
        logger.info("Successfully created all database tables!")
        logger.info("Tables created:")
        logger.info("- person_entities (Person management)")
        logger.info("- license_applications (License applications)")
        logger.info("- license_cards (License card production)")
        logger.info("- application_payments (Payment tracking)")
        logger.info("- test_centers (Test center management)")
        
        print("\n✅ Database tables created successfully!")
        print("\nNext steps:")
        print("1. Start the LINC Backend server: uvicorn app.main:app --reload")
        print("2. Access the API documentation: http://localhost:8000/docs")
        print("3. Create test data using the API endpoints")
        
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 