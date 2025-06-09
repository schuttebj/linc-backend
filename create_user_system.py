#!/usr/bin/env python3
"""
LINC User System Initialization Script
Creates default roles, permissions, and users for the authentication system
"""

import os
import sys
from contextlib import contextmanager
from typing import List, Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import engine
from app.models.user import User, Role, Permission, UserRole, RolePermission, UserStatus
from app.schemas.user import UserCreate, RoleCreate, PermissionCreate
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


def create_default_permissions():
    """Create default permissions for the LINC system"""
    return [
        # License Management Permissions
        {
            "name": "license.application.create",
            "display_name": "Create License Application",
            "description": "Create new license applications",
            "category": "license"
        },
        {
            "name": "license.application.read", 
            "display_name": "View License Applications",
            "description": "View and search license applications",
            "category": "license"
        },
        {
            "name": "license.application.update",
            "display_name": "Update License Application",
            "description": "Update existing license applications",
            "category": "license"
        },
        {
            "name": "license.application.delete",
            "display_name": "Delete License Application",
            "description": "Delete license applications",
            "category": "license"
        },
        {
            "name": "license.application.approve",
            "display_name": "Approve License Application",
            "description": "Approve or reject license applications", 
            "category": "license"
        },
        {
            "name": "license.issue",
            "display_name": "Issue License",
            "description": "Issue approved licenses",
            "category": "license"
        },
        {
            "name": "license.renew",
            "display_name": "Renew License",
            "description": "Process license renewals",
            "category": "license"
        },
        {
            "name": "license.suspend",
            "display_name": "Suspend License",
            "description": "Suspend or reinstate licenses",
            "category": "license"
        },
        
        # Person Management Permissions
        {
            "name": "person.create",
            "display_name": "Create Person Record",
            "description": "Create new person records",
            "category": "person"
        },
        {
            "name": "person.read",
            "display_name": "View Person Records", 
            "description": "View person information",
            "category": "person"
        },
        {
            "name": "person.update",
            "display_name": "Update Person Record",
            "description": "Update person information",
            "category": "person"
        },
        {
            "name": "person.delete",
            "display_name": "Delete Person Record",
            "description": "Delete person records",
            "category": "person"
        },
        
        # Financial Permissions
        {
            "name": "finance.payment.create",
            "display_name": "Process Payments",
            "description": "Process and record payments",
            "category": "financial"
        },
        {
            "name": "finance.payment.read",
            "display_name": "View Financial Records",
            "description": "View payment and financial records",
            "category": "financial"
        },
        {
            "name": "finance.refund.process",
            "display_name": "Process Refunds",
            "description": "Process refund requests",
            "category": "financial"
        },
        
        # Testing Permissions
        {
            "name": "test.schedule",
            "display_name": "Schedule Tests",
            "description": "Schedule driving tests",
            "category": "testing"
        },
        {
            "name": "test.conduct",
            "display_name": "Conduct Tests",
            "description": "Conduct and score driving tests",
            "category": "testing"
        },
        {
            "name": "test.results.update",
            "display_name": "Update Test Results",
            "description": "Update test results and scores",
            "category": "testing"
        },
        
        # Administration Permissions
        {
            "name": "admin.user.create",
            "display_name": "Create Users",
            "description": "Create new system users",
            "category": "administration"
        },
        {
            "name": "admin.user.read",
            "display_name": "View Users",
            "description": "View system users",
            "category": "administration"
        },
        {
            "name": "admin.user.update",
            "display_name": "Update Users",
            "description": "Update system user accounts",
            "category": "administration"
        },
        {
            "name": "admin.user.delete",
            "display_name": "Delete Users", 
            "description": "Delete system user accounts",
            "category": "administration"
        },
        {
            "name": "admin.role.manage",
            "display_name": "Manage Roles",
            "description": "Create and manage user roles",
            "category": "administration"
        },
        {
            "name": "admin.system.config",
            "display_name": "System Configuration",
            "description": "Configure system settings",
            "category": "administration"
        },
        
        # Reporting Permissions
        {
            "name": "report.license.read",
            "display_name": "License Reports",
            "description": "Generate license-related reports",
            "category": "reporting"
        },
        {
            "name": "report.financial.read",
            "display_name": "Financial Reports",
            "description": "Generate financial reports",
            "category": "reporting"
        },
        {
            "name": "report.operational.read",
            "display_name": "Operational Reports", 
            "description": "Generate operational reports",
            "category": "reporting"
        }
    ]


def create_default_roles():
    """Create default roles with appropriate permissions"""
    return [
        {
            "name": "super_admin",
            "display_name": "Super Administrator",
            "description": "Full system access with all permissions",
            "level": 1,
            "is_system_role": True,
            "permissions": [
                "license.application.create", "license.application.read", "license.application.update", 
                "license.application.delete", "license.application.approve", "license.issue", 
                "license.renew", "license.suspend",
                "person.create", "person.read", "person.update", "person.delete",
                "finance.payment.create", "finance.payment.read", "finance.refund.process",
                "test.schedule", "test.conduct", "test.results.update",
                "admin.user.create", "admin.user.read", "admin.user.update", "admin.user.delete",
                "admin.role.manage", "admin.system.config",
                "report.license.read", "report.financial.read", "report.operational.read"
            ]
        },
        {
            "name": "admin",
            "display_name": "Administrator", 
            "description": "Administrative access with user management",
            "level": 2,
            "is_system_role": True,
            "permissions": [
                "license.application.read", "license.application.update", "license.application.approve",
                "person.create", "person.read", "person.update",
                "finance.payment.read",
                "admin.user.create", "admin.user.read", "admin.user.update",
                "admin.role.manage",
                "report.license.read", "report.operational.read"
            ]
        },
        {
            "name": "license_manager",
            "display_name": "License Manager",
            "description": "Manage license operations and approvals",
            "level": 3,
            "is_system_role": True,
            "permissions": [
                "license.application.create", "license.application.read", "license.application.update",
                "license.application.approve", "license.issue", "license.renew", "license.suspend",
                "person.create", "person.read", "person.update",
                "report.license.read", "report.operational.read"
            ]
        },
        {
            "name": "license_operator",
            "display_name": "License Operator",
            "description": "Process license applications and basic operations",
            "level": 4,
            "is_system_role": True,
            "permissions": [
                "license.application.create", "license.application.read", "license.application.update",
                "license.issue", "license.renew",
                "person.create", "person.read", "person.update",
                "finance.payment.create", "finance.payment.read"
            ]
        },
        {
            "name": "examiner",
            "display_name": "Driving Test Examiner",
            "description": "Conduct driving tests and manage test results",
            "level": 5,
            "is_system_role": True,
            "permissions": [
                "license.application.read",
                "person.read",
                "test.schedule", "test.conduct", "test.results.update"
            ]
        },
        {
            "name": "financial_officer",
            "display_name": "Financial Officer",
            "description": "Manage payments and financial operations",
            "level": 5,
            "is_system_role": True,
            "permissions": [
                "license.application.read",
                "person.read",
                "finance.payment.create", "finance.payment.read", "finance.refund.process",
                "report.financial.read"
            ]
        },
        {
            "name": "viewer",
            "display_name": "Viewer",
            "description": "Read-only access to basic information",
            "level": 6,
            "is_system_role": True,
            "permissions": [
                "license.application.read",
                "person.read",
                "finance.payment.read",
                "report.license.read", "report.operational.read"
            ]
        }
    ]


def main():
    """Initialize the user authentication system"""
    
    print("🚀 Initializing LINC User Authentication System")
    print("=" * 60)
    
    try:
        with get_db_session() as db:
            # Step 1: Create permissions
            print("\n📋 Creating system permissions...")
            permission_data = create_default_permissions()
            permissions_created = {}
            
            for perm_data in permission_data:
                try:
                    existing_permission = db.query(Permission).filter(
                        Permission.name == perm_data["name"]
                    ).first()
                    
                    if not existing_permission:
                        permission = Permission(
                            id=str(uuid.uuid4()),
                            name=perm_data["name"],
                            display_name=perm_data["display_name"],
                            description=perm_data["description"],
                            category=perm_data["category"],
                            is_active=True,
                            created_at=datetime.utcnow(),
                            created_by="system"
                        )
                        db.add(permission)
                        db.flush()
                        permissions_created[permission.name] = permission
                        print(f"  ✅ Created permission: {permission.display_name}")
                    else:
                        permissions_created[existing_permission.name] = existing_permission
                        print(f"  ⏭️  Permission exists: {existing_permission.display_name}")
                        
                except Exception as e:
                    print(f"  ❌ Error creating permission {perm_data['name']}: {e}")
            
            print(f"\n📊 Permissions summary: {len(permissions_created)} total")
            
            # Step 2: Create roles
            print("\n👥 Creating system roles...")
            role_data = create_default_roles()
            roles_created = {}
            
            for role_info in role_data:
                try:
                    existing_role = db.query(Role).filter(
                        Role.name == role_info["name"]
                    ).first()
                    
                    if not existing_role:
                        role = Role(
                            id=str(uuid.uuid4()),
                            name=role_info["name"],
                            display_name=role_info["display_name"],
                            description=role_info["description"],
                            level=role_info["level"],
                            is_system_role=role_info["is_system_role"],
                            is_active=True,
                            created_at=datetime.utcnow(),
                            created_by="system"
                        )
                        db.add(role)
                        db.flush()
                        
                        # Add permissions to role
                        for perm_name in role_info["permissions"]:
                            if perm_name in permissions_created:
                                role_permission = RolePermission(
                                    role_id=role.id,
                                    permission_id=permissions_created[perm_name].id,
                                    created_at=datetime.utcnow(),
                                    created_by="system"
                                )
                                db.add(role_permission)
                        
                        roles_created[role.name] = role
                        print(f"  ✅ Created role: {role.display_name} ({len(role_info['permissions'])} permissions)")
                    else:
                        roles_created[existing_role.name] = existing_role
                        print(f"  ⏭️  Role exists: {existing_role.display_name}")
                        
                except Exception as e:
                    print(f"  ❌ Error creating role {role_info['name']}: {e}")
            
            print(f"\n📊 Roles summary: {len(roles_created)} total")
            
            # Step 3: Create default admin user
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
                    
                    # Add super_admin role to admin user
                    if "super_admin" in roles_created:
                        user_role = UserRole(
                            user_id=admin_user.id,
                            role_id=roles_created["super_admin"].id,
                            created_at=datetime.utcnow(),
                            created_by="system"
                        )
                        db.add(user_role)
                    
                    print(f"  ✅ Created admin user: {admin_user.username}")
                    print(f"      📧 Email: {admin_user.email}")
                    print(f"      🔐 Password: Admin123! (CHANGE IMMEDIATELY)")
                    print(f"      🔄 Requires password change on first login")
                else:
                    print(f"  ⏭️  Admin user exists: {existing_admin.username}")
                    
            except Exception as e:
                print(f"  ❌ Error creating admin user: {e}")
            
            # Step 4: Create sample users
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
                    "role": "license_operator"
                },
                {
                    "username": "examiner1",
                    "email": "examiner1@linc.gov.za",
                    "first_name": "Mike",
                    "last_name": "Johnson",
                    "password": "Examiner123!",
                    "employee_id": "EX001",
                    "department": "Testing Division",
                    "role": "examiner"
                },
                {
                    "username": "finance1",
                    "email": "finance1@linc.gov.za",
                    "first_name": "Sarah",
                    "last_name": "Davis",
                    "password": "Finance123!",
                    "employee_id": "FN001",
                    "department": "Financial Services",
                    "role": "financial_officer"
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
                            is_active=True,
                            is_verified=True,
                            status=UserStatus.ACTIVE.value,
                            require_password_change=True,
                            created_at=datetime.utcnow(),
                            created_by="system"
                        )
                        db.add(user)
                        db.flush()
                        
                        # Add role to user
                        if user_info["role"] in roles_created:
                            user_role = UserRole(
                                user_id=user.id,
                                role_id=roles_created[user_info["role"]].id,
                                created_at=datetime.utcnow(),
                                created_by="system"
                            )
                            db.add(user_role)
                        
                        print(f"  ✅ Created user: {user.username} ({user_info['role']})")
                    else:
                        print(f"  ⏭️  User exists: {existing_user.username}")
                        
                except Exception as e:
                    print(f"  ❌ Error creating user {user_info['username']}: {e}")
            
            print("\n" + "=" * 60)
            print("🎉 LINC User Authentication System Initialized!")
            print("\n📋 Summary:")
            print(f"   • {len(permissions_created)} permissions created")
            print(f"   • {len(roles_created)} roles created") 
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
            print("   4. Review and adjust role permissions")
            
    except Exception as e:
        print(f"\n❌ Fatal error initializing user system: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 