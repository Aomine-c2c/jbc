import asyncio
from sqlalchemy import select
from app.db.session import SessionLocal
import app.modules.iam.models  # noqa: F401
import app.modules.fleet.models  # noqa: F401
import app.modules.jobs.models  # noqa: F401
from app.modules.iam.models import Role, Permission, User, Department, RolePermission, UserRole, Scope
from app.modules.fleet.models import MachineType, Machine
from app.core.security import get_password_hash

async def seed():
    async with SessionLocal() as session:
        # Check if users already exist to avoid duplicates
        existing = await session.execute(select(User).limit(1))
        if existing.scalar_one_or_none():
            print("Database already seeded. Skipping.")
            return

        # Departments
        dept_maintenance = Department(name="Maintenance", description="Maintenance and repairs")
        dept_operations = Department(name="Operations", description="Mine operations")
        dept_finance = Department(name="Finance", description="Finance and Administration")
        session.add_all([dept_maintenance, dept_operations, dept_finance])
        await session.commit()
        await session.refresh(dept_maintenance)

        # Core Resource Permissions
        permissions = [
            "job_card:read", "job_card:create", "job_card:update", "job_card:delete", "job_card:approve", "job_card:verify",
            "job_request:read", "job_request:create", "job_request:update", "job_request:delete", "job_request:approve",
            "machine_requisition:read", "machine_requisition:create", "machine_requisition:update", "machine_requisition:approve",
            "users:read", "users:manage",
            "departments:read", "departments:manage",
            "system:configure", "audit_logs:read"
        ]
        
        perm_objs = {}
        for p in permissions:
            perm = Permission(name=p, description=f"Permission to {p}")
            session.add(perm)
            perm_objs[p] = perm
            
        await session.commit()
        for p in perm_objs.values():
            await session.refresh(p)

        # Roles Definition
        role_definitions = {
            "System Administrator": {
                "perms": [(p, Scope.GLOBAL) for p in permissions],
                "is_system": True
            },
            "System Auditor": {
                "perms": [(p, Scope.GLOBAL) for p in permissions if ":read" in p],
                "is_system": True
            },
            "Employee/Requester": {
                "perms": [
                    ("job_request:create", Scope.OWN),
                    ("job_request:read", Scope.OWN),
                    ("job_card:read", Scope.OWN)
                ]
            },
            "Technician": {
                "perms": [
                    ("job_card:read", Scope.ASSIGNED),
                    ("job_card:update", Scope.ASSIGNED),
                    ("job_request:read", Scope.DEPARTMENT)
                ]
            },
            "Supervisor": {
                "perms": [
                    ("job_card:read", Scope.DEPARTMENT),
                    ("job_card:create", Scope.DEPARTMENT),
                    ("job_card:update", Scope.DEPARTMENT),
                    ("job_card:approve", Scope.DEPARTMENT),
                    ("job_card:verify", Scope.DEPARTMENT),
                    ("job_request:read", Scope.DEPARTMENT),
                    ("job_request:approve", Scope.DEPARTMENT)
                ]
            },
            "Department Manager": {
                "perms": [
                    ("job_card:read", Scope.DEPARTMENT),
                    ("job_card:approve", Scope.DEPARTMENT),
                    ("job_request:read", Scope.DEPARTMENT),
                    ("job_request:approve", Scope.DEPARTMENT),
                    ("machine_requisition:read", Scope.DEPARTMENT),
                    ("machine_requisition:approve", Scope.DEPARTMENT)
                ]
            }
        }
        
        # Add remaining roles simply
        other_roles = [
            "Maintenance Planner", "Workshop Manager", "Equipment Controller", 
            "Stores Officer", "Procurement Officer", "HSE Officer", "Finance Officer"
        ]
        for role_name in other_roles:
            role_definitions[role_name] = {
                "perms": [("job_card:read", Scope.DEPARTMENT)] # Minimal placeholder permissions
            }
            
        role_objs = {}
        for r_name, r_data in role_definitions.items():
            role = Role(name=r_name, description=r_name, is_system=r_data.get("is_system", False))
            session.add(role)
            role_objs[r_name] = {"obj": role, "perms": r_data["perms"]}
            
        await session.commit()
        for r in role_objs.values():
            await session.refresh(r["obj"])
            
        # Role Permissions
        for r_data in role_objs.values():
            role = r_data["obj"]
            for perm_name, scope in r_data["perms"]:
                rp = RolePermission(role_id=role.id, permission_id=perm_objs[perm_name].id, scope=scope)
                session.add(rp)
        await session.commit()

        # Users
        admin_user = User(
            email="admin@bikita.com",
            first_name="Admin",
            last_name="User",
            hashed_password=get_password_hash("password123"),
            department_id=dept_maintenance.id,
            is_active=True,
            is_superuser=True
        )
        tech_user = User(
            email="tech@bikita.com",
            first_name="Tech",
            last_name="User",
            hashed_password=get_password_hash("password123"),
            department_id=dept_maintenance.id,
            is_active=True,
            is_superuser=False
        )
        sup_user = User(
            email="supervisor@bikita.com",
            first_name="Super",
            last_name="Visor",
            hashed_password=get_password_hash("password123"),
            department_id=dept_maintenance.id,
            is_active=True,
            is_superuser=False
        )
        session.add_all([admin_user, tech_user, sup_user])
        await session.commit()
        await session.refresh(admin_user)
        await session.refresh(tech_user)
        await session.refresh(sup_user)

        # User Roles
        session.add(UserRole(user_id=admin_user.id, role_id=role_objs["System Administrator"]["obj"].id))
        session.add(UserRole(user_id=tech_user.id, role_id=role_objs["Technician"]["obj"].id))
        session.add(UserRole(user_id=sup_user.id, role_id=role_objs["Supervisor"]["obj"].id))
        await session.commit()

        print("Database seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed())
