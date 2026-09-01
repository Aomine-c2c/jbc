import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session_factory
from app.modules.iam.models import Role, Permission, RolePermission, Scope
from sqlalchemy import select, delete
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

ROLES_PERMISSIONS = {
    "Employee": {
        "job_card:view": Scope.OWN,
        "job_card:create": Scope.OWN,
    },
    "Technician": {
        "job_card:view": Scope.ASSIGNED,
        "job_card:edit": Scope.ASSIGNED,
        "job_card:submit": Scope.ASSIGNED,
    },
    "Operator": {
        "job_card:view": Scope.DEPARTMENT,
        "machine:view": Scope.GLOBAL,
        "requisition:dispatch": Scope.GLOBAL,
    },
    "Supervisor": {
        "job_card:view": Scope.DEPARTMENT,
        "job_card:approve": Scope.DEPARTMENT,
        "job_card:assign": Scope.DEPARTMENT,
        "job_card:return": Scope.DEPARTMENT,
        "job_card:allocate": Scope.DEPARTMENT,
    },
    "Department Manager": {
        "job_card:view": Scope.DEPARTMENT,
        "job_card:approve": Scope.DEPARTMENT,
        "job_card:cancel": Scope.DEPARTMENT,
        "admin:users": Scope.DEPARTMENT,
    },
    "Resource_Coordinator": {
        "machine:view": Scope.GLOBAL,
        "machine:allocate": Scope.GLOBAL,
        "job_card:allocate": Scope.GLOBAL,
    },
    "Safety_Officer": {
        "job_card:view": Scope.GLOBAL,
        "job_card:approve": Scope.GLOBAL,
    },
    "System Administrator": {
        "admin:system": Scope.GLOBAL,
        "admin:users": Scope.GLOBAL,
        "job_card:view": Scope.GLOBAL,
        "machine:view": Scope.GLOBAL,
        "admin:workflows": Scope.GLOBAL,
    },
    "Platform Administrator": {
        "admin:system": Scope.GLOBAL,
        "admin:users": Scope.GLOBAL,
        "admin:workflows": Scope.GLOBAL,
    },
    "Server Administrator": {
        "admin:system": Scope.GLOBAL,
    }
}

PERMISSION_DESCRIPTIONS = {
    "job_card:view": "View job cards",
    "job_card:create": "Create a new job card",
    "job_card:edit": "Edit an existing job card",
    "job_card:submit": "Submit a job card for approval",
    "job_card:approve": "Approve a job card or work package",
    "job_card:reject": "Reject a job card",
    "job_card:return": "Return a job card for rework",
    "job_card:assign": "Assign a job card to a user",
    "job_card:allocate": "Allocate parts/resources to a job card",
    "job_card:close": "Close a completed job card",
    "job_card:cancel": "Cancel a job card",
    "job_card:export": "Export job cards data",
    "machine:view": "View machine resources",
    "machine:allocate": "Allocate machines for use",
    "machine:manage": "Manage machine master data",
    "requisition:dispatch": "Dispatch requisitions and resources",
    "admin:users": "Manage users and roles",
    "admin:workflows": "Manage workflow configurations",
    "admin:system": "System-wide administration",
}

async def seed_rbac():
    logger.info("Seeding RBAC system...")
    async with async_session_factory() as session:
        # 1. Create or fetch Permissions
        db_permissions = {}
        for perm_name, desc in PERMISSION_DESCRIPTIONS.items():
            result = await session.execute(select(Permission).where(Permission.name == perm_name))
            perm = result.scalar_one_or_none()
            if not perm:
                perm = Permission(name=perm_name, description=desc)
                session.add(perm)
            db_permissions[perm_name] = perm
        
        await session.flush()
        
        # 2. Create or fetch Roles and link Permissions
        for role_name, perms in ROLES_PERMISSIONS.items():
            result = await session.execute(select(Role).where(Role.name == role_name))
            role = result.scalar_one_or_none()
            if not role:
                is_system = role_name in ["System Administrator", "Platform Administrator", "Server Administrator"]
                role = Role(name=role_name, description=f"{role_name} standard role", is_system=is_system)
                session.add(role)
                await session.flush()
            
            # Clear existing RolePermissions for this role to ensure fresh matrix
            await session.execute(delete(RolePermission).where(RolePermission.role_id == role.id))
            await session.flush()
            
            # Add new permissions for the role
            for perm_name, scope in perms.items():
                perm = db_permissions[perm_name]
                new_mapping = RolePermission(role_id=role.id, permission_id=perm.id, scope=scope)
                session.add(new_mapping)

        await session.commit()
        logger.info("RBAC Seeding Complete!")

if __name__ == "__main__":
    asyncio.run(seed_rbac())
