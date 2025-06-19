#!/usr/bin/env python3
"""
Initialize LINC Permission System
Creates the 4-tier user type hierarchy and default permissions
"""

import asyncio
from datetime import datetime

from app.core.database import get_db_context
from app.models.user_type import UserType


async def init_permission_system():
    """Initialize the 4-tier permission system"""
    
    print("🚀 Initializing LINC Permission System...")
    
    with get_db_context() as db:
        # Define the 4-tier user type hierarchy
        user_types = [
            {
                "id": "super_admin",
                "display_name": "Super Administrator",
                "description": "Full system access - can manage all users, regions, and system configuration",
                "tier_level": "1",
                "parent_type_id": None,
                "default_permissions": ["*"],  # Wildcard = full access
                "permission_constraints": {},
                "can_access_all_provinces": True,
                "can_access_all_regions": True,
                "can_access_all_offices": True,
                "is_system_type": True
            },
            {
                "id": "national_help_desk",
                "display_name": "National Help Desk",
                "description": "National level support - can access all provinces and manage regional help desk users",
                "tier_level": "2",
                "parent_type_id": "super_admin",
                "default_permissions": [
                    # User management
                    "user.read", "user.create", "user.update",
                    "admin.user.read", "admin.user.create", "admin.user.update",
                    
                    # Region management
                    "region.read", "region.create", "region.update",
                    
                    # Office management
                    "office.read", "office.create", "office.update",
                    
                    # Location management
                    "location.read", "location.create", "location.update",
                    
                    # Person management
                    "person.read", "person.register", "person.update",
                    
                    # Session management
                    "session.create", "session.read", "session.manage",
                    
                    # Staff assignment
                    "staff.assign"
                ],
                "permission_constraints": {
                    "geographic_scope": "national"
                },
                "can_access_all_provinces": True,
                "can_access_all_regions": True,
                "can_access_all_offices": True,
                "is_system_type": True
            },
            {
                "id": "provincial_help_desk",
                "display_name": "Provincial Help Desk",
                "description": "Provincial level support - can access assigned province and manage standard users",
                "tier_level": "3",
                "parent_type_id": "national_help_desk",
                "default_permissions": [
                    # User management (limited)
                    "user.read", "user.create", "user.update",
                    
                    # Region management (read-only)
                    "region.read",
                    
                    # Office management (limited)
                    "office.read", "office.update",
                    
                    # Location management
                    "location.read", "location.update",
                    
                    # Person management
                    "person.read", "person.register", "person.update",
                    
                    # Session management
                    "session.create", "session.read"
                ],
                "permission_constraints": {
                    "geographic_scope": "provincial",
                    "requires_province_assignment": True
                },
                "can_access_all_provinces": False,
                "can_access_all_regions": False,
                "can_access_all_offices": False,
                "is_system_type": True
            },
            {
                "id": "standard_user",
                "display_name": "Standard User",
                "description": "Standard system user - limited to assigned regions and basic operations",
                "tier_level": "4",
                "parent_type_id": "provincial_help_desk",
                "default_permissions": [
                    # Person management (basic)
                    "person.read", "person.register",
                    
                    # Location management (read-only)
                    "location.read",
                    
                    # Session management
                    "session.create"
                ],
                "permission_constraints": {
                    "geographic_scope": "regional",
                    "requires_region_assignment": True
                },
                "can_access_all_provinces": False,
                "can_access_all_regions": False,
                "can_access_all_offices": False,
                "is_system_type": False
            }
        ]
        
        print("📝 Creating user types...")
        
        for user_type_data in user_types:
            # Check if user type already exists
            existing = db.query(UserType).filter(UserType.id == user_type_data["id"]).first()
            
            if existing:
                print(f"   ⚠️  User type '{user_type_data['id']}' already exists - updating...")
                
                # Update existing user type
                for key, value in user_type_data.items():
                    if key != "id":  # Don't update the ID
                        setattr(existing, key, value)
                
                existing.updated_at = datetime.utcnow()
                
            else:
                print(f"   ✅ Creating user type '{user_type_data['id']}'...")
                
                # Create new user type
                user_type = UserType(
                    created_at=datetime.utcnow(),
                    created_by="system",
                    **user_type_data
                )
                db.add(user_type)
        
        # Commit all changes
        db.commit()
        
        print("✅ Permission system initialized successfully!")
        print()
        print("📊 User Type Hierarchy:")
        print("   1️⃣  super_admin (Full system access)")
        print("   2️⃣  national_help_desk (National level)")
        print("   3️⃣  provincial_help_desk (Provincial level)")
        print("   4️⃣  standard_user (Regional level)")
        print()
        print("🔐 Permission System Features:")
        print("   • Dot notation permissions (e.g., user.create, person.read)")
        print("   • Geographic scope enforcement")
        print("   • Hierarchical user management")
        print("   • Individual permission overrides")
        print("   • Real-time permission compilation")
        print()
        
        # Show created user types
        user_types = db.query(UserType).order_by(UserType.tier_level).all()
        print("📋 Created User Types:")
        for ut in user_types:
            print(f"   {ut.tier_level}. {ut.id} - {ut.display_name}")
            print(f"      Permissions: {len(ut.default_permissions)} default")
            print(f"      Geographic: {'All' if ut.can_access_all_provinces else 'Limited'}")
            print()


def run_init():
    """Run the initialization synchronously"""
    asyncio.run(init_permission_system())


if __name__ == "__main__":
    run_init()