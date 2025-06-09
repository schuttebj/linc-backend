#!/usr/bin/env python3
"""
LINC User System Initialization Script

This script creates the default user management system including:
- System roles (Admin, Operator, Examiner, Viewer)
- System permissions (based on documentation business rules)
- Default admin user
- Default test users

Usage:
    python create_user_system.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import uuid

# Add the app directory to the Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from app.core.database import get_db_context
from app.models.user import User, Role, Permission, UserStatus, user_roles, role_permissions
from app.models.enums import ValidationStatus
from app.services.user_service import UserService
from app.schemas.user import UserCreate, RoleCreate, PermissionCreate
import structlog

logger = structlog.get_logger()

def create_default_permissions():
    """Create default system permissions based on documentation business rules"""
    
    permissions = [
        # License Application Management
        {
            "name": "license.application.create",
            "display_name": "Create License Application",
            "description": "Permission to create new license applications",
            "category": "license",
            "resource": "license_application",
            "action": "create"
        },
        {
            "name": "license.application.read",
            "display_name": "View License Applications",
            "description": "Permission to view license applications",
            "category": "license",
            "resource": "license_application",
            "action": "read"
        },
        {
            "name": "license.application.update",
            "display_name": "Update License Application",
            "description": "Permission to update license applications",
            "category": "license",
            "resource": "license_application",
            "action": "update"
        },
        {
            "name": "license.application.delete",
            "display_name": "Delete License Application",
            "description": "Permission to delete license applications",
            "category": "license",
            "resource": "license_application",
            "action": "delete"
        },
        {
            "name": "license.application.submit",
            "display_name": "Submit License Application",
            "description": "Permission to submit license applications for processing",
            "category": "license",
            "resource": "license_application",
            "action": "submit"
        },
        {
            "name": "license.application.approve",
            "display_name": "Approve License Application",
            "description": "Permission to approve license applications",
            "category": "license",
            "resource": "license_application",
            "action": "approve"
        },
        {
            "name": "license.application.reject",
            "display_name": "Reject License Application",
            "description": "Permission to reject license applications",
            "category": "license",
            "resource": "license_application",
            "action": "reject"
        },
        
        # Person Management
        {
            "name": "person.create",
            "display_name": "Create Person",
            "description": "Permission to create new person records",
            "category": "person",
            "resource": "person",
            "action": "create"
        },
        {
            "name": "person.read",
            "display_name": "View Person Records",
            "description": "Permission to view person records",
            "category": "person",
            "resource": "person",
            "action": "read"
        },
        {
            "name": "person.update",
            "display_name": "Update Person Records",
            "description": "Permission to update person records",
            "category": "person",
            "resource": "person",
            "action": "update"
        },
        {
            "name": "person.delete",
            "display_name": "Delete Person Records",
            "description": "Permission to delete person records",
            "category": "person",
            "resource": "person",
            "action": "delete"
        },
        
        # Financial Management
        {
            "name": "finance.payment.create",
            "display_name": "Process Payments",
            "description": "Permission to process payments and fees",
            "category": "financial",
            "resource": "payment",
            "action": "create"
        },
        {
            "name": "finance.payment.read",
            "display_name": "View Payment Records",
            "description": "Permission to view payment records",
            "category": "financial",
            "resource": "payment",
            "action": "read"
        },
        {
            "name": "finance.refund.create",
            "display_name": "Process Refunds",
            "description": "Permission to process refunds",
            "category": "financial",
            "resource": "refund",
            "action": "create"
        },
        {
            "name": "finance.report.read",
            "display_name": "View Financial Reports",
            "description": "Permission to view financial reports",
            "category": "financial",
            "resource": "report",
            "action": "read"
        },
        
        # Test Center Management
        {
            "name": "test.schedule.create",
            "display_name": "Schedule Tests",
            "description": "Permission to schedule driving tests",
            "category": "testing",
            "resource": "test_schedule",
            "action": "create"
        },
        {
            "name": "test.result.create",
            "display_name": "Record Test Results",
            "description": "Permission to record test results",
            "category": "testing",
            "resource": "test_result",
            "action": "create"
        },
        {
            "name": "test.center.manage",
            "display_name": "Manage Test Centers",
            "description": "Permission to manage test center information",
            "category": "testing",
            "resource": "test_center",
            "action": "manage"
        },
        
        # Administrative Functions
        {
            "name": "admin.user.create",
            "display_name": "Create Users",
            "description": "Permission to create new user accounts",
            "category": "administration",
            "resource": "user",
            "action": "create"
        },
        {
            "name": "admin.user.read",
            "display_name": "View Users",
            "description": "Permission to view user accounts",
            "category": "administration",
            "resource": "user",
            "action": "read"
        },
        {
            "name": "admin.user.update",
            "display_name": "Update Users",
            "description": "Permission to update user accounts",
            "category": "administration",
            "resource": "user",
            "action": "update"
        },
        {
            "name": "admin.user.delete",
            "display_name": "Delete Users",
            "description": "Permission to delete user accounts",
            "category": "administration",
            "resource": "user",
            "action": "delete"
        },
        {
            "name": "admin.role.manage",
            "display_name": "Manage Roles",
            "description": "Permission to manage user roles and permissions",
            "category": "administration",
            "resource": "role",
            "action": "manage"
        },
        {
            "name": "admin.system.manage",
            "display_name": "System Administration",
            "description": "Permission for system administration tasks",
            "category": "administration",
            "resource": "system",
            "action": "manage"
        },
        {
            "name": "admin.audit.read",
            "display_name": "View Audit Logs",
            "description": "Permission to view system audit logs",
            "category": "administration",
            "resource": "audit_log",
            "action": "read"
        },
        
        # Reporting
        {
            "name": "report.license.read",
            "display_name": "License Reports",
            "description": "Permission to view license-related reports",
            "category": "reporting",
            "resource": "license_report",
            "action": "read"
        },
        {
            "name": "report.operational.read",
            "display_name": "Operational Reports",
            "description": "Permission to view operational reports",
            "category": "reporting",
            "resource": "operational_report",
            "action": "read"
        },
        {
            "name": "report.export",
            "display_name": "Export Reports",
            "description": "Permission to export reports and data",
            "category": "reporting",
            "resource": "export",
            "action": "create"
        }
    ]
    
    return permissions

def create_default_roles():
    """Create default system roles based on documentation requirements"""
    
    roles = [
        {
            "name": "super_admin",
            "display_name": "Super Administrator",
            "description": "Full system access with all permissions",
            "is_system_role": True,
            "level": 0,
            "permissions": []  # Superusers get all permissions automatically
        },
        {
            "name": "admin",
            "display_name": "Administrator",
            "description": "Administrative access to manage users and system configuration",
            "is_system_role": True,
            "level": 1,
            "permissions": [
                "admin.user.create", "admin.user.read", "admin.user.update", "admin.user.delete",
                "admin.role.manage", "admin.system.manage", "admin.audit.read",
                "person.create", "person.read", "person.update",
                "license.application.read", "license.application.update",
                "report.license.read", "report.operational.read", "report.export"
            ]
        },
        {
            "name": "license_manager",
            "display_name": "License Manager",
            "description": "Full license application management including approvals",
            "is_system_role": True,
            "level": 2,
            "permissions": [
                "license.application.create", "license.application.read", 
                "license.application.update", "license.application.submit",
                "license.application.approve", "license.application.reject",
                "person.create", "person.read", "person.update",
                "finance.payment.read", "finance.report.read",
                "test.schedule.create", "test.center.manage",
                "report.license.read", "report.operational.read"
            ]
        },
        {
            "name": "license_operator",
            "display_name": "License Operator",
            "description": "License application processing and customer service",
            "is_system_role": True,
            "level": 3,
            "permissions": [
                "license.application.create", "license.application.read", 
                "license.application.update", "license.application.submit",
                "person.create", "person.read", "person.update",
                "finance.payment.create", "finance.payment.read",
                "test.schedule.create",
                "report.license.read"
            ]
        },
        {
            "name": "examiner",
            "display_name": "Driving Test Examiner",
            "description": "Conduct driving tests and record results",
            "is_system_role": True,
            "level": 3,
            "permissions": [
                "license.application.read",
                "person.read",
                "test.schedule.create", "test.result.create", "test.center.manage",
                "report.operational.read"
            ]
        },
        {
            "name": "financial_officer",
            "display_name": "Financial Officer",
            "description": "Financial operations and payment processing",
            "is_system_role": True,
            "level": 3,
            "permissions": [
                "finance.payment.create", "finance.payment.read",
                "finance.refund.create", "finance.report.read",
                "license.application.read",
                "person.read",
                "report.operational.read", "report.export"
            ]
        },
        {
            "name": "viewer",
            "display_name": "Read-Only Viewer",
            "description": "Read-only access to view records and reports",
            "is_system_role": True,
            "level": 4,
            "permissions": [
                "license.application.read",
                "person.read",
                "finance.payment.read",
                "report.license.read", "report.operational.read"
            ]
        }
    ]
    
    return roles

def main():
    """Initialize the user authentication system"""
    
    print("🚀 Initializing LINC User Authentication System")
    print("=" * 60)
    
    try:
        with get_db_context() as db:
            user_service = UserService(db)
            
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
                        permission_create = PermissionCreate(**perm_data)
                        permission = await user_service.create_permission(
                            permission_create, created_by="system"
                        )
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
                        # Get permission IDs for this role
                        permission_ids = []
                        for perm_name in role_info["permissions"]:
                            if perm_name in permissions_created:
                                permission_ids.append(str(permissions_created[perm_name].id))
                        
                        role_create_data = {
                            "name": role_info["name"],
                            "display_name": role_info["display_name"],
                            "description": role_info["description"],
                            "is_active": True,
                            "permission_ids": permission_ids
                        }
                        
                        role_create = RoleCreate(**role_create_data)
                        role = await user_service.create_role(role_create, created_by="system")
                        
                        # Set system role flag
                        role.is_system_role = role_info["is_system_role"]
                        role.level = role_info["level"]
                        db.commit()
                        
                        roles_created[role.name] = role
                        print(f"  ✅ Created role: {role.display_name} ({len(permission_ids)} permissions)")
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
                    # Get super_admin role ID
                    super_admin_role = roles_created.get("super_admin")
                    role_ids = [str(super_admin_role.id)] if super_admin_role else []
                    
                    admin_user_data = UserCreate(
                        username="admin",
                        email="admin@linc.gov.za",
                        first_name="System",
                        last_name="Administrator",
                        password="Admin123!",  # Default password - should be changed immediately
                        employee_id="ADMIN001",
                        department="IT Administration",
                        country_code="ZA",
                        role_ids=role_ids,
                        is_active=True,
                        require_password_change=True
                    )
                    
                    admin_user = await user_service.create_user(admin_user_data, created_by="system")
                    
                    # Set superuser flag
                    admin_user.is_superuser = True
                    admin_user.is_verified = True
                    admin_user.status = UserStatus.ACTIVE.value
                    db.commit()
                    
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
                        # Get role ID
                        role = roles_created.get(user_info["role"])
                        role_ids = [str(role.id)] if role else []
                        
                        user_data = UserCreate(
                            username=user_info["username"],
                            email=user_info["email"],
                            first_name=user_info["first_name"],
                            last_name=user_info["last_name"],
                            password=user_info["password"],
                            employee_id=user_info["employee_id"],
                            department=user_info["department"],
                            country_code="ZA",
                            role_ids=role_ids,
                            is_active=True,
                            require_password_change=True
                        )
                        
                        user = await user_service.create_user(user_data, created_by="system")
                        user.is_verified = True
                        user.status = UserStatus.ACTIVE.value
                        db.commit()
                        
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