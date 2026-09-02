import asyncio
import uuid
from sqlalchemy import select
from app.db.session import SessionLocal
from app.modules.iam.models import (
    Role, Permission, User, Department, RolePermission, UserRole, Scope,
    Organization, Site, Section, Team, Position, EmployeeProfile
)
from app.core.security import get_password_hash

async def seed():
    async with SessionLocal() as session:
        # Check if users already exist to avoid duplicates
        existing = await session.execute(select(User).limit(1))
        if existing.scalar_one_or_none():
            print("Database already seeded. Skipping.")
            return

        print("Seeding Industrial Operations Core Architecture (v1.0)...")

        # 1. Organization & Site
        org = Organization(
            id=uuid.uuid4(),
            code="BIK",
            name="Bikita Minerals Ltd",
            description="Leading producer of lithium and rare earth minerals",
            industry_type="Mining & Mineral Processing",
            country="Zimbabwe",
            currency="USD"
        )
        session.add(org)
        await session.commit()
        await session.refresh(org)

        site = Site(
            id=uuid.uuid4(),
            organization_id=org.id,
            code="MSV-1",
            name="Masvingo Main Plant",
            site_type="MINE_SITE",
            address="Masvingo Province, Zimbabwe"
        )
        session.add(site)
        await session.commit()
        await session.refresh(site)

        # 2. Departments
        depts_data = {
            "IT": "Information Technology",
            "Instrumentation": "Instrumentation and Control",
            "Mechanical": "Mechanical Engineering & Maintenance",
            "Electrical": "Electrical Engineering"
        }
        departments = {}
        for code, name in depts_data.items():
            dept = Department(
                id=uuid.uuid4(),
                site_id=site.id,
                code=code,
                name=name,
                description=f"{name} Department"
            )
            session.add(dept)
            departments[code] = dept
        
        await session.commit()
        for dept in departments.values():
            await session.refresh(dept)

        # 3. Sections & Teams
        # For Mechanical
        mech_section = Section(id=uuid.uuid4(), department_id=departments["Mechanical"].id, code="CRUSHING", name="Crushing & Screening")
        session.add(mech_section)
        await session.commit()
        await session.refresh(mech_section)

        mech_team_alpha = Team(id=uuid.uuid4(), section_id=mech_section.id, code="SHIFT-A", name="Shift Alpha")
        session.add(mech_team_alpha)

        # For Electrical
        elec_section = Section(id=uuid.uuid4(), department_id=departments["Electrical"].id, code="HV-PLANT", name="High Voltage Plant")
        session.add(elec_section)
        await session.commit()
        await session.refresh(elec_section)

        elec_team_callout = Team(id=uuid.uuid4(), section_id=elec_section.id, code="CALLOUT", name="Emergency Callout Team")
        session.add(elec_team_callout)

        # For Instrumentation
        inst_section = Section(id=uuid.uuid4(), department_id=departments["Instrumentation"].id, code="SCADA", name="SCADA & Automation")
        session.add(inst_section)
        await session.commit()
        await session.refresh(inst_section)
        
        # 4. Positions (Operational Titles)
        positions_data = [
            (departments["Mechanical"].id, "S-MECH", "Senior Mechanical Fitter", "MASTER"),
            (departments["Mechanical"].id, "J-MECH", "Mechanical Artisan", "JOURNEYMAN"),
            (departments["Electrical"].id, "S-ELEC", "HV Electrician", "MASTER"),
            (departments["Instrumentation"].id, "ENG-INST", "Automation Engineer", "MASTER"),
            (departments["IT"].id, "IT-ADMIN", "Systems Administrator", "MASTER"),
            (departments["Mechanical"].id, "OPERATOR", "Machine Operator", "JOURNEYMAN"),
            (departments["Mechanical"].id, "RES-COORD", "Resource Coordinator", "MASTER"),
            (departments["Electrical"].id, "SAFETY-OFF", "Safety Officer", "MASTER"),
            (None, "MGR", "Plant Manager", "EXECUTIVE"),
        ]
        positions = {}
        for dept_id, code, title, skill in positions_data:
            pos = Position(id=uuid.uuid4(), code=code, title=title, department_id=dept_id, skill_level=skill)
            session.add(pos)
            positions[code] = pos
            
        await session.commit()
        for pos in positions.values():
            await session.refresh(pos)

        # 5. Core Resource Permissions
        permissions = [
            "job_card:read", "job_card:create", "job_card:update", "job_card:delete", "job_card:approve", "job_card:verify",
            "job_card:allocate", "job_card:close", "job_card:cancel", "job_card:export",
            "job_request:read", "job_request:create", "job_request:update", "job_request:delete", "job_request:approve",
            "machine_requisition:read", "machine_requisition:create", "machine_requisition:update", "machine_requisition:approve",
            "machine:view", "machine:allocate", "machine:manage",
            "requisition:create", "requisition:approve", "requisition:submit", "requisition:review",
            "requisition:allocate", "requisition:dispatch", "requisition:return", "requisition:close",
            "users:read", "users:manage",
            "departments:read", "departments:manage",
            "settings:manage",
            "system:configure", "audit_logs:read", "audit:read"
        ]
        
        perm_objs = {}
        for p in permissions:
            perm = Permission(name=p, description=f"Permission to {p}")
            session.add(perm)
            perm_objs[p] = perm
            
        await session.commit()
        for p in perm_objs.values():
            await session.refresh(p)

        # 6. Roles Definition (System RBAC)
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
                    ("job_card:submit", Scope.ASSIGNED),
                    ("job_request:read", Scope.DEPARTMENT)
                ]
            },
            "Operator": {
                "perms": [
                    ("job_card:read", Scope.DEPARTMENT),
                    ("machine:view", Scope.GLOBAL),
                    ("requisition:dispatch", Scope.GLOBAL),
                ]
            },
            "Supervisor": {
                "perms": [
                    ("job_card:read", Scope.DEPARTMENT),
                    ("job_card:create", Scope.DEPARTMENT),
                    ("job_card:update", Scope.DEPARTMENT),
                    ("job_card:approve", Scope.DEPARTMENT),
                    ("job_card:verify", Scope.DEPARTMENT),
                    ("job_card:assign", Scope.DEPARTMENT),
                    ("job_card:return", Scope.DEPARTMENT),
                    ("job_card:allocate", Scope.DEPARTMENT),
                    ("job_request:read", Scope.DEPARTMENT),
                    ("job_request:approve", Scope.DEPARTMENT),
                    ("users:read", Scope.DEPARTMENT)
                ]
            },
            "Department Manager": {
                "perms": [
                    ("job_card:read", Scope.DEPARTMENT),
                    ("job_card:approve", Scope.DEPARTMENT),
                    ("job_request:read", Scope.DEPARTMENT),
                    ("job_request:approve", Scope.DEPARTMENT),
                    ("machine_requisition:read", Scope.DEPARTMENT),
                    ("machine_requisition:approve", Scope.DEPARTMENT),
                    ("users:read", Scope.DEPARTMENT),
                    ("users:manage", Scope.DEPARTMENT),
                    ("departments:read", Scope.DEPARTMENT)
                ]
            },
            "Resource_Coordinator": {
                "perms": [
                    ("machine:view", Scope.GLOBAL),
                    ("machine:allocate", Scope.GLOBAL),
                    ("machine:manage", Scope.GLOBAL),
                    ("job_card:allocate", Scope.GLOBAL),
                    ("machine_requisition:read", Scope.GLOBAL),
                    ("machine_requisition:approve", Scope.GLOBAL),
                    ("requisition:create", Scope.GLOBAL),
                    ("requisition:approve", Scope.GLOBAL),
                    ("requisition:submit", Scope.GLOBAL),
                    ("requisition:review", Scope.GLOBAL),
                    ("requisition:allocate", Scope.GLOBAL),
                    ("requisition:dispatch", Scope.GLOBAL),
                    ("requisition:return", Scope.GLOBAL),
                    ("requisition:close", Scope.GLOBAL),
                ]
            },
            "Safety_Officer": {
                "perms": [
                    ("job_card:read", Scope.GLOBAL),
                    ("job_card:approve", Scope.GLOBAL),
                ]
            },
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

        # 7. Users
        # IT Admin
        admin_user = User(
            id=uuid.uuid4(),
            email="admin@bikita.com",
            first_name="Admin",
            last_name="User",
            hashed_password=get_password_hash("password123"),
            department_id=departments["IT"].id,
            position_id=positions["IT-ADMIN"].id,
            employee_number="EMP-0001",
            is_active=True,
            is_superuser=True
        )
        
        # Mechanical Manager
        mech_mgr = User(
            id=uuid.uuid4(),
            email="mechmgr@bikita.com",
            first_name="John",
            last_name="Manager",
            hashed_password=get_password_hash("password123"),
            department_id=departments["Mechanical"].id,
            position_id=positions["MGR"].id,
            employee_number="EMP-1000",
            is_active=True,
            is_superuser=False
        )
        
        # Mechanical Supervisor
        mech_sup = User(
            id=uuid.uuid4(),
            email="supervisor@bikita.com",
            first_name="Super",
            last_name="Visor",
            hashed_password=get_password_hash("password123"),
            department_id=departments["Mechanical"].id,
            section_id=mech_section.id,
            position_id=positions["S-MECH"].id,
            supervisor_id=mech_mgr.id,
            employee_number="EMP-1050",
            is_active=True,
            is_superuser=False
        )
        
        # Mechanical Technician
        mech_tech = User(
            id=uuid.uuid4(),
            email="tech@bikita.com",
            first_name="Tech",
            last_name="User",
            hashed_password=get_password_hash("password123"),
            department_id=departments["Mechanical"].id,
            section_id=mech_section.id,
            team_id=mech_team_alpha.id,
            position_id=positions["J-MECH"].id,
            supervisor_id=mech_sup.id,
            employee_number="EMP-1051",
            is_active=True,
            is_superuser=False
        )

        # Machine Operator
        operator = User(
            id=uuid.uuid4(),
            email="operator@bikita.com",
            first_name="Crane",
            last_name="Operator",
            hashed_password=get_password_hash("password123"),
            department_id=departments["Mechanical"].id,
            section_id=mech_section.id,
            team_id=mech_team_alpha.id,
            position_id=positions["OPERATOR"].id,
            supervisor_id=mech_sup.id,
            employee_number="EMP-1052",
            is_active=True,
            is_superuser=False
        )

        # Resource Coordinator
        coordinator = User(
            id=uuid.uuid4(),
            email="coordinator@bikita.com",
            first_name="Resource",
            last_name="Coordinator",
            hashed_password=get_password_hash("password123"),
            department_id=departments["Mechanical"].id,
            position_id=positions["RES-COORD"].id,
            supervisor_id=mech_mgr.id,
            employee_number="EMP-1060",
            is_active=True,
            is_superuser=False
        )

        # Safety Officer
        safety = User(
            id=uuid.uuid4(),
            email="safety@bikita.com",
            first_name="Safety",
            last_name="Officer",
            hashed_password=get_password_hash("password123"),
            department_id=departments["Electrical"].id,
            position_id=positions["SAFETY-OFF"].id,
            supervisor_id=mech_mgr.id,
            employee_number="EMP-1070",
            is_active=True,
            is_superuser=False
        )

        session.add_all([admin_user, mech_mgr, mech_sup, mech_tech, operator, coordinator, safety])
        await session.commit()
        await session.refresh(admin_user)
        await session.refresh(mech_mgr)
        await session.refresh(mech_sup)
        await session.refresh(mech_tech)
        await session.refresh(operator)
        await session.refresh(coordinator)
        await session.refresh(safety)

        # Set section supervisors / team leads now that users exist
        mech_section.supervisor_id = mech_sup.id
        mech_team_alpha.team_lead_id = mech_sup.id
        departments["Mechanical"].hod_id = mech_mgr.id
        await session.commit()

        # 8. User Roles
        session.add(UserRole(user_id=admin_user.id, role_id=role_objs["System Administrator"]["obj"].id))
        
        session.add(UserRole(user_id=mech_mgr.id, role_id=role_objs["Department Manager"]["obj"].id))
        
        session.add(UserRole(user_id=mech_sup.id, role_id=role_objs["Supervisor"]["obj"].id))
        
        session.add(UserRole(user_id=mech_tech.id, role_id=role_objs["Technician"]["obj"].id))
        session.add(UserRole(user_id=mech_tech.id, role_id=role_objs["Employee/Requester"]["obj"].id))

        session.add(UserRole(user_id=operator.id, role_id=role_objs["Operator"]["obj"].id))
        session.add(UserRole(user_id=coordinator.id, role_id=role_objs["Resource_Coordinator"]["obj"].id))
        session.add(UserRole(user_id=safety.id, role_id=role_objs["Safety_Officer"]["obj"].id))
        await session.commit()

        # 9. Employee Profiles
        session.add(EmployeeProfile(
            user_id=mech_tech.id,
            national_id="63-1234567X89",
            emergency_contact_name="Jane Doe",
            emergency_contact_phone="+263772123456",
            skills_and_certifications=[{"skill": "Hydraulics", "level": "Advanced"}, {"skill": "Welding", "level": "Intermediate"}]
        ))
        await session.commit()

        print("Database seeded successfully with Industrial Operations Core!")

if __name__ == "__main__":
    asyncio.run(seed())
