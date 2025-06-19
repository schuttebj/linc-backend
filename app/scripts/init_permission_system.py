"""
Initialize New Permission System
Creates tables and populates with default data for the simplified permission system
"""

import sys
import os
import uuid
import json
from datetime import datetime

# Add the parent directory to sys.path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.core.database import BaseModel
from app.models.permission_system import (
    UserType, Region, RegionRole, Office, OfficeRole, 
    UserRegionAssignment, UserOfficeAssignment, PermissionAuditLog
)

def get_database_session():
    """Get database session"""
    settings = get_settings()
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        echo=True  # Enable SQL logging
    )
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal(), engine

def create_tables(engine):
    """Create all new permission system tables"""
    print("🔧 Creating permission system tables...")
    
    # Create all tables defined in permission_system models
    BaseModel.metadata.create_all(bind=engine, checkfirst=True)
    
    print("✅ Permission system tables created successfully")

def create_system_types(session):
    """Create system types with predefined permissions"""
    print("👑 Creating system types...")
    
    system_types_data = [
        {
            "type_code": "super_admin",
            "display_name": "Super Administrator", 
            "description": "Full system access with all permissions and configuration capabilities",
            "permissions": [
                # All permissions - Super Admin has everything
                "license.application.create", "license.application.read", "license.application.update", 
                "license.application.delete", "license.application.approve", "license.issue", 
                "license.renew", "license.suspend", "license.duplicate",
                "person.create", "person.read", "person.update", "person.delete", "person.search",
                "finance.payment.create", "finance.payment.read", "finance.payment.update",
                "finance.refund.process", "finance.receipt.generate", "finance.reconciliation",
                "test.schedule", "test.conduct", "test.results.read", "test.results.update", "test.booking.manage",
                "vehicle.registration.create", "vehicle.registration.read", "vehicle.registration.update",
                "vehicle.registration.renew", "vehicle.inspection",
                "admin.user.create", "admin.user.read", "admin.user.update", "admin.user.delete",
                "admin.role.manage", "admin.permission.manage", "admin.system.config", "admin.audit.read",
                "report.license.read", "report.financial.read", "report.operational.read", 
                "report.audit.read", "report.export",
                "infringement.create", "infringement.read", "infringement.update", "infringement.process",
                "location.region.manage", "location.office.manage", "location.assignment.manage"
            ],
            "has_national_access": True,
            "restricted_to_province": None
        },
        {
            "type_code": "national_help_desk",
            "display_name": "National Help Desk",
            "description": "All operational functions across all provinces, no system configuration",
            "permissions": [
                # All operational permissions, limited admin
                "license.application.create", "license.application.read", "license.application.update", 
                "license.application.approve", "license.issue", "license.renew", "license.suspend", "license.duplicate",
                "person.create", "person.read", "person.update", "person.search",
                "finance.payment.create", "finance.payment.read", "finance.payment.update",
                "finance.refund.process", "finance.receipt.generate",
                "test.schedule", "test.conduct", "test.results.read", "test.results.update", "test.booking.manage",
                "vehicle.registration.create", "vehicle.registration.read", "vehicle.registration.update",
                "vehicle.registration.renew", "vehicle.inspection",
                "admin.user.read", "admin.user.update",  # Can view and update users but not create/delete
                "report.license.read", "report.financial.read", "report.operational.read", "report.export",
                "infringement.create", "infringement.read", "infringement.update", "infringement.process"
            ],
            "has_national_access": True,
            "restricted_to_province": None
        },
        {
            "type_code": "provincial_help_desk", 
            "display_name": "Provincial Help Desk",
            "description": "All operational functions within assigned province only",
            "permissions": [
                # Operational permissions within province
                "license.application.create", "license.application.read", "license.application.update", 
                "license.application.approve", "license.issue", "license.renew", "license.suspend",
                "person.create", "person.read", "person.update", "person.search",
                "finance.payment.create", "finance.payment.read", "finance.payment.update",
                "finance.refund.process", "finance.receipt.generate",
                "test.schedule", "test.conduct", "test.results.read", "test.results.update", "test.booking.manage",
                "vehicle.registration.create", "vehicle.registration.read", "vehicle.registration.update",
                "vehicle.registration.renew", "vehicle.inspection",
                "report.license.read", "report.financial.read", "report.operational.read", "report.export",
                "infringement.create", "infringement.read", "infringement.update", "infringement.process"
            ],
            "has_national_access": False,
            "restricted_to_province": None  # Will be set per user
        },
        {
            "type_code": "standard_user",
            "display_name": "Standard User",
            "description": "Role-based access requiring region and office assignments",
            "permissions": [
                # Basic permissions that all users get
                "person.read", 
                "license.application.read",
                "report.license.read"
            ],
            "has_national_access": False,
            "restricted_to_province": None
        }
    ]
    
    created_count = 0
    for type_data in system_types_data:
        # Check if exists
        existing = session.query(UserType).filter(UserType.type_code == type_data["type_code"]).first()
        
        if not existing:
            user_type = UserType(
                id=uuid.uuid4(),
                type_code=type_data["type_code"],
                display_name=type_data["display_name"],
                description=type_data["description"],
                permissions=type_data["permissions"],
                has_national_access=type_data["has_national_access"],
                restricted_to_province=type_data["restricted_to_province"],
                is_system_type=True,
                is_active=True,
                created_at=datetime.utcnow(),
                created_by="system"
            )
            session.add(user_type)
            created_count += 1
            print(f"  ✅ Created system type: {type_data['display_name']}")
        else:
            print(f"  ⏭️  System type exists: {type_data['display_name']}")
    
    session.commit()
    print(f"📊 System types: {created_count} created")

def create_region_roles(session):
    """Create predefined region roles"""
    print("🏢 Creating region roles...")
    
    region_roles_data = [
        {
            "role_name": "region_administrator",
            "display_name": "Region Administrator",
            "description": "Full management of region operations and users",
            "permissions": [
                "license.application.create", "license.application.read", "license.application.update", 
                "license.application.approve", "license.issue", "license.renew", "license.suspend",
                "person.create", "person.read", "person.update", "person.delete", "person.search",
                "finance.payment.create", "finance.payment.read", "finance.payment.update",
                "finance.refund.process", "finance.receipt.generate", "finance.reconciliation",
                "test.schedule", "test.conduct", "test.results.read", "test.results.update", "test.booking.manage",
                "vehicle.registration.create", "vehicle.registration.read", "vehicle.registration.update",
                "vehicle.registration.renew", "vehicle.inspection",
                "admin.user.create", "admin.user.read", "admin.user.update",
                "report.license.read", "report.financial.read", "report.operational.read", "report.export",
                "infringement.create", "infringement.read", "infringement.update", "infringement.process",
                "location.office.manage", "location.assignment.manage"
            ],
            "role_level": 1
        },
        {
            "role_name": "region_supervisor",
            "display_name": "Region Supervisor", 
            "description": "Operational oversight across all offices in region",
            "permissions": [
                "license.application.read", "license.application.update", "license.application.approve",
                "person.create", "person.read", "person.update", "person.search",
                "finance.payment.read", "finance.payment.update", "finance.refund.process",
                "test.schedule", "test.results.read", "test.results.update", "test.booking.manage",
                "vehicle.registration.read", "vehicle.registration.update", "vehicle.inspection",
                "admin.user.read", "admin.user.update",
                "report.license.read", "report.financial.read", "report.operational.read", "report.export",
                "infringement.read", "infringement.update", "infringement.process"
            ],
            "role_level": 2
        },
        {
            "role_name": "region_financial_administrator",
            "display_name": "Region Financial Administrator",
            "description": "Financial oversight and reconciliation across region",
            "permissions": [
                "license.application.read", "person.read", "person.search",
                "finance.payment.create", "finance.payment.read", "finance.payment.update",
                "finance.refund.process", "finance.receipt.generate", "finance.reconciliation",
                "report.financial.read", "report.operational.read", "report.export",
                "infringement.read", "infringement.process"
            ],
            "role_level": 3
        },
        {
            "role_name": "region_query_specialist",
            "display_name": "Region Query Specialist",
            "description": "Data analysis and reporting across region",
            "permissions": [
                "license.application.read", "person.read", "person.search",
                "finance.payment.read", "test.results.read", "vehicle.registration.read",
                "report.license.read", "report.financial.read", "report.operational.read", 
                "report.audit.read", "report.export",
                "infringement.read"
            ],
            "role_level": 4
        },
        {
            "role_name": "region_test_administrator",
            "display_name": "Region Test Administrator",
            "description": "Testing operations oversight (DLTC only)",
            "permissions": [
                "license.application.read", "person.read", "person.search",
                "test.schedule", "test.conduct", "test.results.read", "test.results.update", "test.booking.manage",
                "report.license.read", "report.operational.read", "report.export"
            ],
            "role_level": 5
        },
        {
            "role_name": "region_vehicle_administrator",
            "display_name": "Region Vehicle Administrator", 
            "description": "Vehicle registration oversight (RA only)",
            "permissions": [
                "license.application.read", "person.read", "person.search",
                "vehicle.registration.create", "vehicle.registration.read", "vehicle.registration.update",
                "vehicle.registration.renew", "vehicle.inspection",
                "report.license.read", "report.operational.read", "report.export"
            ],
            "role_level": 6
        }
    ]
    
    created_count = 0
    for role_data in region_roles_data:
        existing = session.query(RegionRole).filter(RegionRole.role_name == role_data["role_name"]).first()
        
        if not existing:
            region_role = RegionRole(
                id=uuid.uuid4(),
                role_name=role_data["role_name"],
                display_name=role_data["display_name"],
                description=role_data["description"],
                permissions=role_data["permissions"],
                role_level=role_data["role_level"],
                is_system_role=True,
                is_active=True,
                created_at=datetime.utcnow(),
                created_by="system"
            )
            session.add(region_role)
            created_count += 1
            print(f"  ✅ Created region role: {role_data['display_name']}")
        else:
            print(f"  ⏭️  Region role exists: {role_data['display_name']}")
    
    session.commit()
    print(f"📊 Region roles: {created_count} created")

def create_office_roles(session):
    """Create predefined office roles"""
    print("🏬 Creating office roles...")
    
    office_roles_data = [
        {
            "role_name": "office_supervisor",
            "display_name": "Office Supervisor",
            "description": "Management and oversight of office operations",
            "permissions": [
                "license.application.create", "license.application.read", "license.application.update", 
                "license.application.approve", "license.issue", "license.renew",
                "person.create", "person.read", "person.update", "person.search",
                "finance.payment.create", "finance.payment.read", "finance.payment.update",
                "finance.refund.process", "finance.receipt.generate",
                "test.schedule", "test.results.read", "test.booking.manage",
                "vehicle.registration.create", "vehicle.registration.read", "vehicle.registration.update",
                "admin.user.read", "admin.user.update",
                "report.license.read", "report.financial.read", "report.operational.read",
                "infringement.create", "infringement.read", "infringement.update", "infringement.process"
            ],
            "role_level": 1
        },
        {
            "role_name": "office_administrator",
            "display_name": "Office Administrator",
            "description": "Administrative functions and user management within office",
            "permissions": [
                "license.application.read", "license.application.update",
                "person.create", "person.read", "person.update", "person.search",
                "finance.payment.read", "finance.receipt.generate",
                "admin.user.read", "admin.user.update",
                "report.license.read", "report.operational.read",
                "infringement.read", "infringement.update"
            ],
            "role_level": 2
        },
        {
            "role_name": "data_clerk",
            "display_name": "Data Clerk",
            "description": "Data entry and basic license processing",
            "permissions": [
                "license.application.create", "license.application.read", "license.application.update",
                "person.create", "person.read", "person.update", "person.search",
                "report.license.read"
            ],
            "role_level": 3
        },
        {
            "role_name": "cashier",
            "display_name": "Cashier",
            "description": "Payment processing and receipt generation",
            "permissions": [
                "license.application.read", "person.read", "person.search",
                "finance.payment.create", "finance.payment.read", "finance.receipt.generate",
                "report.financial.read"
            ],
            "role_level": 3
        },
        {
            "role_name": "registration_clerk",
            "display_name": "Registration Clerk",
            "description": "Vehicle registration processing",
            "permissions": [
                "person.read", "person.search",
                "vehicle.registration.create", "vehicle.registration.read", "vehicle.registration.update",
                "vehicle.registration.renew", "vehicle.inspection",
                "report.license.read"
            ],
            "role_level": 3
        },
        {
            "role_name": "examiner",
            "display_name": "Examiner",
            "description": "Conduct driving tests and manage results",
            "permissions": [
                "license.application.read", "person.read", "person.search",
                "test.conduct", "test.results.read", "test.results.update",
                "report.license.read"
            ],
            "role_level": 4
        },
        {
            "role_name": "booking_clerk",
            "display_name": "Booking Clerk",
            "description": "Manage test appointments and scheduling",
            "permissions": [
                "license.application.read", "person.read", "person.search",
                "test.schedule", "test.booking.manage",
                "report.license.read"
            ],
            "role_level": 4
        },
        {
            "role_name": "infringement_clerk",
            "display_name": "Infringement Clerk",
            "description": "Process traffic infringements and fines",
            "permissions": [
                "person.read", "person.search",
                "infringement.create", "infringement.read", "infringement.update", "infringement.process",
                "finance.payment.create", "finance.payment.read", "finance.receipt.generate",
                "report.operational.read"
            ],
            "role_level": 4
        },
        {
            "role_name": "technical_support",
            "display_name": "Technical Support",
            "description": "System support and troubleshooting",
            "permissions": [
                "license.application.read", "person.read", "person.search",
                "admin.user.read", 
                "report.license.read", "report.operational.read"
            ],
            "role_level": 5
        }
    ]
    
    created_count = 0
    for role_data in office_roles_data:
        existing = session.query(OfficeRole).filter(OfficeRole.role_name == role_data["role_name"]).first()
        
        if not existing:
            office_role = OfficeRole(
                id=uuid.uuid4(),
                role_name=role_data["role_name"],
                display_name=role_data["display_name"],
                description=role_data["description"],
                permissions=role_data["permissions"],
                role_level=role_data["role_level"],
                is_system_role=True,
                is_active=True,
                created_at=datetime.utcnow(),
                created_by="system"
            )
            session.add(office_role)
            created_count += 1
            print(f"  ✅ Created office role: {role_data['display_name']}")
        else:
            print(f"  ⏭️  Office role exists: {role_data['display_name']}")
    
    session.commit()
    print(f"📊 Office roles: {created_count} created")

def create_sample_regions_and_offices(session):
    """Create sample regions and offices for testing"""
    print("🌍 Creating sample regions and offices...")
    
    # Sample regions
    regions_data = [
        {
            "region_code": "GP001",
            "region_name": "Johannesburg Central",
            "province_code": "GP",
            "region_type": "standard",
            "description": "Central Johannesburg region covering CBD and surrounding areas"
        },
        {
            "region_code": "GP002", 
            "region_name": "Pretoria North",
            "province_code": "GP",
            "region_type": "dltc",
            "description": "Pretoria North DLTC region"
        },
        {
            "region_code": "WC001",
            "region_name": "Cape Town Metro",
            "province_code": "WC", 
            "region_type": "standard",
            "description": "Cape Town metropolitan region"
        }
    ]
    
    created_regions = 0
    region_objects = {}
    
    for region_data in regions_data:
        existing = session.query(Region).filter(Region.region_code == region_data["region_code"]).first()
        
        if not existing:
            region = Region(
                id=uuid.uuid4(),
                region_code=region_data["region_code"],
                region_name=region_data["region_name"],
                province_code=region_data["province_code"],
                region_type=region_data["region_type"],
                description=region_data["description"],
                is_active=True,
                created_at=datetime.utcnow(),
                created_by="system"
            )
            session.add(region)
            region_objects[region_data["region_code"]] = region
            created_regions += 1
            print(f"  ✅ Created region: {region_data['region_name']}")
        else:
            region_objects[region_data["region_code"]] = existing
            print(f"  ⏭️  Region exists: {region_data['region_name']}")
    
    session.commit()
    
    # Sample offices
    offices_data = [
        {
            "office_code": "GP001001",
            "office_name": "Johannesburg CBD Office",
            "region_code": "GP001",
            "office_type": "standard",
            "description": "Main office in Johannesburg CBD"
        },
        {
            "office_code": "GP001002",
            "office_name": "Sandton Office",
            "region_code": "GP001", 
            "office_type": "standard",
            "description": "Sandton branch office"
        },
        {
            "office_code": "GP002001",
            "office_name": "Pretoria DLTC",
            "region_code": "GP002",
            "office_type": "dltc",
            "description": "Pretoria Driving License Testing Centre"
        },
        {
            "office_code": "WC001001",
            "office_name": "Cape Town Central Office",
            "region_code": "WC001",
            "office_type": "standard", 
            "description": "Cape Town central office"
        }
    ]
    
    created_offices = 0
    
    for office_data in offices_data:
        existing = session.query(Office).filter(Office.office_code == office_data["office_code"]).first()
        
        if not existing and office_data["region_code"] in region_objects:
            office = Office(
                id=uuid.uuid4(),
                office_code=office_data["office_code"],
                office_name=office_data["office_name"],
                region_id=region_objects[office_data["region_code"]].id,
                office_type=office_data["office_type"],
                description=office_data["description"],
                is_active=True,
                created_at=datetime.utcnow(),
                created_by="system"
            )
            session.add(office)
            created_offices += 1
            print(f"  ✅ Created office: {office_data['office_name']}")
        else:
            print(f"  ⏭️  Office exists or region not found: {office_data['office_name']}")
    
    session.commit()
    print(f"📊 Sample data: {created_regions} regions, {created_offices} offices created")

def main():
    """Initialize the permission system"""
    print("🚀 Initializing LINC Simplified Permission System")
    print("=" * 60)
    
    try:
        session, engine = get_database_session()
        
        # Step 1: Create tables
        create_tables(engine)
        
        # Step 2: Create system types
        create_system_types(session)
        
        # Step 3: Create region roles
        create_region_roles(session)
        
        # Step 4: Create office roles  
        create_office_roles(session)
        
        # Step 5: Create sample regions and offices
        create_sample_regions_and_offices(session)
        
        print("\n" + "=" * 60)
        print("🎉 Permission system initialization completed successfully!")
        print("\nNext steps:")
        print("1. Update existing users to use new system types")
        print("2. Assign users to regions and offices with appropriate roles")
        print("3. Test permission compilation and caching")
        print("4. Update API endpoints to use new permission middleware")
        
        session.close()
        
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        if 'session' in locals():
            session.rollback()
            session.close()
        raise

if __name__ == "__main__":
    main()