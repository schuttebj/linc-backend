#!/usr/bin/env python3
"""
LINC New User System Initialization Script
Creates default user types and users for the new permission system
"""

import os
import sys
from contextlib import contextmanager
from typing import List, Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import engine
from app.models.user import User, UserStatus
from app.models.user_type import UserType
from app.models.region import Region
from app.models.office import Office
from app.core.security import get_password_hash
from datetime import datetime
import uuid


@contextmanager
def get_db_session():
    """Get database session context manager"""
    db = Session(engine)
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def create_default_user_types():
    """Create default user types for the new permission system"""
    return [
        {
            "type_code": "super_admin",
            "display_name": "Super Administrator",
            "description": "Full system access with all permissions",
            "permissions": [
                "license.application.create", "license.application.read", "license.application.update", 
                "license.application.delete", "license.application.approve", "license.issue", 
                "license.renew", "license.suspend",
                "person.create", "person.read", "person.update", "person.delete",
                "finance.payment.create", "finance.payment.read", "finance.refund.process",
                "test.schedule", "test.conduct", "test.results.update",
                "admin.user.create", "admin.user.read", "admin.user.update", "admin.user.delete",
                "admin.role.manage", "admin.system.config", "admin.database.reset", 
                "admin.database.read", "admin.system.initialize",
                "report.license.read", "report.financial.read", "report.operational.read"
            ],
            "has_national_access": True,
            "is_system_type": True
        },
        {
            "type_code": "national_help_desk",
            "display_name": "National Help Desk",
            "description": "National level support with cross-province access",
            "permissions": [
                "license.application.read", "license.application.update", "license.application.approve",
                "person.create", "person.read", "person.update",
                "finance.payment.read", "finance.refund.process",
                "admin.user.read", "admin.user.update",
                "report.license.read", "report.operational.read"
            ],
            "has_national_access": True,
            "is_system_type": True
        },
        {
            "type_code": "provincial_help_desk",
            "display_name": "Provincial Help Desk",
            "description": "Provincial level support with province-wide access",
            "permissions": [
                "license.application.read", "license.application.update",
                "person.create", "person.read", "person.update",
                "finance.payment.read",
                "report.license.read", "report.operational.read"
            ],
            "has_national_access": False,
            "is_system_type": True
        },
        {
            "type_code": "license_manager",
            "display_name": "License Manager",
            "description": "Manage license operations and approvals",
            "permissions": [
                "license.application.create", "license.application.read", "license.application.update",
                "license.application.approve", "license.issue", "license.renew", "license.suspend",
                "person.create", "person.read", "person.update",
                "report.license.read", "report.operational.read"
            ],
            "has_national_access": False,
            "is_system_type": True
        },
        {
            "type_code": "license_operator",
            "display_name": "License Operator",
            "description": "Process license applications and basic operations",
            "permissions": [
                "license.application.create", "license.application.read", "license.application.update",
                "license.issue", "license.renew",
                "person.create", "person.read", "person.update",
                "finance.payment.create", "finance.payment.read"
            ],
            "has_national_access": False,
            "is_system_type": True
        },
        {
            "type_code": "examiner",
            "display_name": "Driving Test Examiner",
            "description": "Conduct driving tests and manage test results",
            "permissions": [
                "license.application.read",
                "person.read",
                "test.schedule", "test.conduct", "test.results.update"
            ],
            "has_national_access": False,
            "is_system_type": True
        },
        {
            "type_code": "financial_officer",
            "display_name": "Financial Officer",
            "description": "Manage payments and financial operations",
            "permissions": [
                "license.application.read",
                "person.read",
                "finance.payment.create", "finance.payment.read", "finance.refund.process",
                "report.financial.read"
            ],
            "has_national_access": False,
            "is_system_type": True
        },
        {
            "type_code": "standard_user",
            "display_name": "Standard User",
            "description": "Basic user with limited permissions",
            "permissions": [
                "license.application.read",
                "person.read",
                "finance.payment.read"
            ],
            "has_national_access": False,
            "is_system_type": True
        }
    ]


def create_default_region():
    """Create a default region for testing"""
    return {
        "user_group_code": "TEST",
        "user_group_name": "Test Region",
        "user_group_type": "10",  # DLTC
        "province_code": "WC",  # Western Cape - 2 char province code
        "is_active": True
    }


def create_default_office():
    """Create a default office for testing"""
    return {
        "office_code": "TEST001",
        "office_name": "Test Office",
        "office_type": "DLTC",
        "infrastructure_type": "FIXED",
        "province_code": "WC",  # Western Cape - 2 char province code
        "is_active": True
    }


def main():
    """Initialize the new user system"""
    
    print("🚀 Initializing LINC New User System")
    print("=" * 60)
    
    try:
        with get_db_session() as db:
            # Step 1: Create user types
            print("\n👥 Creating user types...")
            user_type_data = create_default_user_types()
            user_types_created = {}
            
            for type_data in user_type_data:
                try:
                    existing_type = db.query(UserType).filter(
                        UserType.id == type_data["type_code"]
                    ).first()
                    
                    if not existing_type:
                        user_type = UserType(
                            id=type_data["type_code"],  # Use type_code as id
                            display_name=type_data["display_name"],
                            description=type_data["description"],
                            tier_level="1" if type_data["type_code"] == "super_admin" else "2",
                            default_permissions=type_data["permissions"],  # JSON array
                            can_access_all_provinces=type_data["has_national_access"],
                            is_system_type=type_data["is_system_type"],
                            is_active=True,
                            created_at=datetime.utcnow(),
                            created_by="system"
                        )
                        db.add(user_type)
                        db.flush()
                        user_types_created[user_type.id] = user_type
                        print(f"  ✅ Created user type: {user_type.display_name}")
                    else:
                        user_types_created[existing_type.id] = existing_type
                        print(f"  ⏭️  User type exists: {existing_type.display_name}")
                        
                except Exception as e:
                    print(f"  ❌ Error creating user type {type_data['type_code']}: {e}")
            
            print(f"\n📊 User types summary: {len(user_types_created)} total")
            
            # Step 2: Create default region
            print("\n🌍 Creating default region...")
            try:
                region_data = create_default_region()
                existing_region = db.query(Region).filter(
                    Region.user_group_code == region_data["user_group_code"]
                ).first()
                
                if not existing_region:
                    region = Region(
                        id=str(uuid.uuid4()),
                        user_group_code=region_data["user_group_code"],
                        user_group_name=region_data["user_group_name"],
                        user_group_type=region_data["user_group_type"],
                        province_code=region_data["province_code"],
                        is_active=region_data["is_active"],
                        created_at=datetime.utcnow(),
                        created_by="system"
                    )
                    db.add(region)
                    db.flush()
                    print(f"  ✅ Created region: {region.user_group_name}")
                else:
                    region = existing_region
                    print(f"  ⏭️  Region exists: {existing_region.user_group_name}")
                    
            except Exception as e:
                print(f"  ❌ Error creating region: {e}")
                region = None
            
            # Step 3: Create default office
            print("\n🏢 Creating default office...")
            try:
                office_data = create_default_office()
                existing_office = db.query(Office).filter(
                    Office.office_code == office_data["office_code"]
                ).first()
                
                if not existing_office and region:
                    office = Office(
                        id=str(uuid.uuid4()),
                        office_code=office_data["office_code"],
                        office_name=office_data["office_name"],
                        office_type=office_data["office_type"],
                        infrastructure_type=office_data["infrastructure_type"],
                        province_code=office_data["province_code"],
                        region_id=region.id,
                        is_active=office_data["is_active"],
                        created_at=datetime.utcnow(),
                        created_by="system"
                    )
                    db.add(office)
                    db.flush()
                    print(f"  ✅ Created office: {office.office_name}")
                else:
                    office = existing_office
                    print(f"  ⏭️  Office exists or region missing")
                    
            except Exception as e:
                print(f"  ❌ Error creating office: {e}")
                office = None
            
            # Step 4: Create default admin user
            print("\n👤 Creating default admin user...")
            try:
                existing_admin = db.query(User).filter(User.username == "admin").first()
                
                if not existing_admin:
                    admin_user = User(
                        id=str(uuid.uuid4()),
                        username="admin",
                        email="admin@linc.gov.za",
                        first_name="System",
                        last_name="Administrator",
                        password_hash=get_password_hash("Admin123!"),
                        employee_id="ADMIN001",
                        department="IT Administration",
                        country_code="ZA",
                        user_type_id=user_types_created["super_admin"].id if "super_admin" in user_types_created else None,
                        assigned_province="WC",  # Western Cape - 2 char province code
                        is_active=True,
                        is_verified=True,
                        is_superuser=True,
                        status=UserStatus.ACTIVE.value,
                        require_password_change=True,
                        created_at=datetime.utcnow(),
                        created_by="system"
                    )
                    db.add(admin_user)
                    db.flush()
                    
                    print(f"  ✅ Created admin user: {admin_user.username}")
                    print(f"      📧 Email: {admin_user.email}")
                    print(f"      🔐 Password: Admin123! (CHANGE IMMEDIATELY)")
                    print(f"      🔄 Requires password change on first login")
                else:
                    print(f"  ⏭️  Admin user exists: {existing_admin.username}")
                    
            except Exception as e:
                print(f"  ❌ Error creating admin user: {e}")
            
            # Step 5: Create sample users
            print("\n👥 Creating sample users...")
            sample_users = [
                {
                    "username": "operator1",
                    "email": "operator1@linc.gov.za",
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "password": "Operator123!",
                    "employee_id": "OP001",
                    "department": "License Operations",
                    "user_type": "license_operator"
                },
                {
                    "username": "examiner1",
                    "email": "examiner1@linc.gov.za",
                    "first_name": "Mike",
                    "last_name": "Johnson",
                    "password": "Examiner123!",
                    "employee_id": "EX001",
                    "department": "Testing Division",
                    "user_type": "examiner"
                },
                {
                    "username": "finance1",
                    "email": "finance1@linc.gov.za",
                    "first_name": "Sarah",
                    "last_name": "Davis",
                    "password": "Finance123!",
                    "employee_id": "FN001",
                    "department": "Financial Services",
                    "user_type": "financial_officer"
                }
            ]
            
            for user_info in sample_users:
                try:
                    existing_user = db.query(User).filter(
                        User.username == user_info["username"]
                    ).first()
                    
                    if not existing_user:
                        user = User(
                            id=str(uuid.uuid4()),
                            username=user_info["username"],
                            email=user_info["email"],
                            first_name=user_info["first_name"],
                            last_name=user_info["last_name"],
                            password_hash=get_password_hash(user_info["password"]),
                            employee_id=user_info["employee_id"],
                            department=user_info["department"],
                            country_code="ZA",
                            user_type_id=user_types_created[user_info["user_type"]].id if user_info["user_type"] in user_types_created else None,
                            assigned_province="WC",  # Western Cape - 2 char province code
                            is_active=True,
                            is_verified=True,
                            status=UserStatus.ACTIVE.value,
                            require_password_change=True,
                            created_at=datetime.utcnow(),
                            created_by="system"
                        )
                        db.add(user)
                        db.flush()
                        
                        print(f"  ✅ Created user: {user.username} ({user_info['user_type']})")
                    else:
                        print(f"  ⏭️  User exists: {existing_user.username}")
                        
                except Exception as e:
                    print(f"  ❌ Error creating user {user_info['username']}: {e}")
            
            print("\n" + "=" * 60)
            print("🎉 LINC New User System Initialized!")
            print("\n📋 Summary:")
            print(f"   • {len(user_types_created)} user types created")
            print(f"   • 1 default region created")
            print(f"   • 1 default office created")
            print(f"   • Default admin user: admin / Admin123!")
            print(f"   • 3 sample users created")
            
            print("\n🔐 Security Notes:")
            print("   • All users have default passwords that MUST be changed")
            print("   • Password change is required on first login")
            print("   • Admin user has superuser privileges")
            
            print("\n🚀 Next Steps:")
            print("   1. Test login with admin user")
            print("   2. Change all default passwords")
            print("   3. Configure additional users as needed")
            print("   4. Review and adjust user type permissions")
            
    except Exception as e:
        print(f"\n❌ Fatal error initializing user system: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 