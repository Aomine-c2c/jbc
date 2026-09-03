"""
Seed comprehensive operational demo data into test_dwrms.db.
Populates users, departments, locations, machine types, machines,
job cards in various workflow states, machine requisitions, and approvals.
"""
import asyncio
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from app.db.session import async_session_factory, Base, engine
from app.core.security import get_password_hash
from app.modules.iam.models import User, Role, UserRole, Department, Location
from app.modules.fleet.models import MachineType, Machine, MachineRequisition, RequisitionActionLog
from app.modules.jobs.models import JobCard, JobCardActionLog, JobCardPart, JobCardLabour
from app.modules.jobs.report_models import JobReport
from app.modules.approvals.models import ApprovalRequest, ApprovalStep
from app.modules.materials.models import MaterialCatalogItem

async def seed_data():
    async with async_session_factory() as db:
        print("[*] Starting database seeding...")

        # ── 1. ROLES LOOKUP ──────────────────────────────────────
        role_res = await db.execute(select(Role))
        roles_by_name = {r.name: r for r in role_res.scalars().all()}

        # ── 2. DEPARTMENTS ───────────────────────────────────────
        dept_res = await db.execute(select(Department))
        depts_by_name = {d.name: d for d in dept_res.scalars().all()}

        required_depts = ["Maintenance", "Mining Operations", "Processing Plant", "Safety & HSE", "Finance"]
        for dname in required_depts:
            if dname not in depts_by_name:
                d = Department(id=uuid.uuid4(), name=dname, code=dname[:4].upper())
                db.add(d)
                depts_by_name[dname] = d
        await db.flush()
        maint_dept = depts_by_name["Maintenance"]
        ops_dept = depts_by_name["Mining Operations"]

        # ── 3. LOCATIONS ─────────────────────────────────────────
        loc_res = await db.execute(select(Location))
        locs_by_name = {loc.name: loc for loc in loc_res.scalars().all()}

        sample_locations = [
            ("Central Heavy Workshop", "CHW-01"),
            ("Open Pit - Bench 5", "OP-B5"),
            ("Primary Crusher Station", "CRUSH-01"),
            ("Spodumene Concentrator", "PLANT-01"),
            ("ROM Pad Stockpile", "ROM-01"),
        ]
        for lname, lcode in sample_locations:
            if lname not in locs_by_name:
                loc = Location(id=uuid.uuid4(), name=lname, code=lcode)
                db.add(loc)
                locs_by_name[lname] = loc
        await db.flush()
        workshop_loc = locs_by_name["Central Heavy Workshop"]
        bench5_loc = locs_by_name["Open Pit - Bench 5"]

        # ── 4. USERS & ROLES ─────────────────────────────────────
        users_res = await db.execute(select(User))
        users_by_email = {u.email: u for u in users_res.scalars().all()}

        user_definitions = [
            ("admin@bikita.com", "Admin", "User", "System Administrator", maint_dept.id),
            ("mechmgr@bikita.com", "John", "Manager", "Department Manager", maint_dept.id),
            ("tech@bikita.com", "Tendai", "Mukamuri", "Technician", maint_dept.id),
            ("supervisor@bikita.com", "Christopher", "Moyo", "Supervisor", maint_dept.id),
            ("operator@bikita.com", "Crane", "Operator", "Operator", ops_dept.id),
            ("manager@bikita.com", "Tinashe", "Gumbo", "Department Manager", maint_dept.id),
            ("controller@bikita.com", "Ruvimbo", "Shumba", "Equipment Controller", ops_dept.id),
            ("safety@bikita.com", "Kudakwashe", "Sibanda", "Safety_Officer", maint_dept.id),
        ]

        pwd_hash = get_password_hash("password123")
        for email, fname, lname, rname, dept_id in user_definitions:
            if email not in users_by_email:
                u = User(
                    id=uuid.uuid4(),
                    email=email,
                    first_name=fname,
                    last_name=lname,
                    hashed_password=pwd_hash,
                    department_id=dept_id,
                    is_active=True,
                )
                db.add(u)
                users_by_email[email] = u
                await db.flush()

                target_role = roles_by_name.get(rname)
                if target_role:
                    ur = UserRole(id=uuid.uuid4(), user_id=u.id, role_id=target_role.id)
                    db.add(ur)
            else:
                # Ensure password hash is set
                u = users_by_email[email]
                u.hashed_password = pwd_hash
                target_role = roles_by_name.get(rname)
                if target_role:
                    # check if role assignment exists
                    ur_check = await db.execute(
                        select(UserRole).where(UserRole.user_id == u.id, UserRole.role_id == target_role.id)
                    )
                    if not ur_check.scalar_one_or_none():
                        db.add(UserRole(id=uuid.uuid4(), user_id=u.id, role_id=target_role.id))

        await db.flush()
        admin_u = users_by_email["admin@bikita.com"]
        tech_u = users_by_email["tech@bikita.com"]
        sup_u = users_by_email["supervisor@bikita.com"]
        mgr_u = users_by_email["manager@bikita.com"]

        # ── 5. MACHINE TYPES ────────────────────────────────────
        mtypes_res = await db.execute(select(MachineType))
        mtypes = {mt.name: mt for mt in mtypes_res.scalars().all()}

        mtype_defs = [
            ("Rigid Dump Truck", "Off-highway mining haul truck 90-100T capacity"),
            ("Hydraulic Excavator", "Heavy production excavator 70-90T class"),
            ("Wheel Loader", "Front-end wheel loader for ROM re-handling"),
            ("Mobile Crane", "Rough terrain hydraulic crane 50-70T"),
            ("Jaw Crusher", "Stationary primary jaw crushing station"),
            ("Track Dozer", "Heavy track bulldozer for pit floor and waste dump"),
        ]
        for tname, tdesc in mtype_defs:
            if tname not in mtypes:
                mt = MachineType(id=uuid.uuid4(), name=tname, description=tdesc)
                db.add(mt)
                mtypes[tname] = mt
        await db.flush()

        # ── 6. MACHINES ──────────────────────────────────────────
        mach_res = await db.execute(select(Machine))
        machines = {m.identifier: m for m in mach_res.scalars().all()}

        machine_defs = [
            ("DT-01", "Rigid Dump Truck", "AVAILABLE", "Central Equipment Yard", 1420.5),
            ("DT-02", "Rigid Dump Truck", "IN_USE", "Open Pit - Bench 5", 2850.0),
            ("EX-01", "Hydraulic Excavator", "AVAILABLE", "Open Pit - Bench 3", 3120.0),
            ("EX-02", "Hydraulic Excavator", "UNDER_MAINTENANCE", "Heavy Workshop Bay 2", 4560.5),
            ("WL-01", "Wheel Loader", "AVAILABLE", "ROM Pad Stockpile", 1890.0),
            ("CR-01", "Mobile Crane", "AVAILABLE", "Central Equipment Yard", 620.0),
            ("JC-01", "Jaw Crusher", "AVAILABLE", "Primary Crusher Station", 5400.0),
            ("DZ-01", "Track Dozer", "AVAILABLE", "Open Pit - Waste Dump 2", 3450.0),
        ]
        for ident, tname, mstatus, mloc, meter in machine_defs:
            if ident not in machines:
                m = Machine(
                    id=uuid.uuid4(),
                    identifier=ident,
                    machine_type_id=mtypes[tname].id,
                    status=mstatus,
                    location=mloc,
                    current_hour_meter=meter,
                )
                db.add(m)
                machines[ident] = m
        await db.flush()

        # ── 7. MATERIAL CATALOG ──────────────────────────────────
        cat_res = await db.execute(select(MaterialCatalogItem))
        catalog = {c.part_number: c for c in cat_res.scalars().all()}

        sample_spares = [
            ("HYD-FLT-01", "Hydraulic High Pressure Return Filter", "FILTERS", 85.0),
            ("SEAL-KIT-390", "Cylinder Gland & Piston Seal Kit CAT 390F", "SEALS", 320.0),
            ("JAW-PLT-120", "Metso LT120 Fixed Jaw Manganese Plate", "WEAR_PARTS", 2850.0),
            ("BRG-SPH-220", "Spherical Roller Bearing 22220-E1", "BEARINGS", 195.0),
            ("LUB-HD-68", "ISO VG 68 Heavy Hydraulic Oil (200L Drum)", "LUBRICANTS", 480.0),
        ]
        for pnum, pname, pcat, pcost in sample_spares:
            if pnum not in catalog:
                it = MaterialCatalogItem(
                    id=uuid.uuid4(),
                    part_number=pnum,
                    name=pname,
                    category=pcat,
                    default_unit_cost=pcost,
                    is_active=True,
                )
                db.add(it)
                catalog[pnum] = it
        await db.flush()

        # ── 8. JOB CARDS IN VARIOUS WORKFLOW STAGES ──────────────
        jc_res = await db.execute(select(JobCard))
        existing_jcs = {j.job_number: j for j in jc_res.scalars().all() if j.job_number}

        now = datetime.now(timezone.utc)

        job_cards_to_seed = [
            {
                "job_number": "JC-2026-0001",
                "title": "Hydraulic Pump Overhaul on CAT 390F EX-02",
                "description": "Main hydraulic implement pump pressure loss detected during cycle load test at Bench 5.",
                "status": "DRAFT",
                "priority": 2,
                "machine": machines.get("EX-02"),
                "creator": tech_u,
            },
            {
                "job_number": "JC-2026-0002",
                "title": "Primary Jaw Crusher Toggle Plate Replacement",
                "description": "Crusher overload release mechanism tripped. Inspect and replace sheared toggle plate.",
                "status": "SUBMITTED",
                "priority": 3,
                "machine": machines.get("JC-01"),
                "creator": tech_u,
            },
            {
                "job_number": "JC-2026-0003",
                "title": "CAT 777D DT-01 500-Hour Scheduled Preventive Service",
                "description": "Periodic 500-hr PM service: engine oil, transmission filters, final drive inspection.",
                "status": "APPROVED",
                "priority": 1,
                "machine": machines.get("DT-01"),
                "creator": tech_u,
                "approver": sup_u,
            },
            {
                "job_number": "JC-2026-0004",
                "title": "Komatsu WA600 Loader Bucket Bushing Replacement",
                "description": "Excessive play (>5mm) identified in front bellcrank pivot pin and bushings.",
                "status": "ASSIGNED",
                "priority": 2,
                "machine": machines.get("WL-01"),
                "creator": tech_u,
                "approver": sup_u,
                "supervisor": sup_u,
            },
            {
                "job_number": "JC-2026-0005",
                "title": "Secondary Crusher Hydraulic Lube Line Repair",
                "description": "Minor pinhole leak on secondary cone lubrication feed line near return manifold.",
                "status": "IN_PROGRESS",
                "priority": 2,
                "machine": machines.get("JC-01"),
                "creator": tech_u,
                "approver": sup_u,
                "supervisor": sup_u,
            },
            {
                "job_number": "JC-2026-0006",
                "title": "CAT D9R Track Tensioner Cylinder Re-pack",
                "description": "Grease cylinder seals failed causing left-hand track chain to lose operating tension.",
                "status": "COMPLETED",
                "priority": 1,
                "machine": machines.get("DZ-01"),
                "creator": tech_u,
                "approver": sup_u,
                "supervisor": sup_u,
            },
            {
                "job_number": "JC-2026-0007",
                "title": "Submersible Slurry Pump Impeller Replacement",
                "description": "Excessive cavitational wear on chrome alloy impeller leading to reduced discharge head.",
                "status": "VERIFIED",
                "priority": 1,
                "machine": None,
                "creator": tech_u,
                "approver": sup_u,
                "supervisor": sup_u,
            },
        ]

        for jdata in job_cards_to_seed:
            jnum = jdata["job_number"]
            if jnum not in existing_jcs:
                jc = JobCard(
                    id=uuid.uuid4(),
                    job_number=jnum,
                    title=jdata["title"],
                    description=jdata["description"],
                    status=jdata["status"],
                    priority=jdata["priority"],
                    department_id=maint_dept.id,
                    location="Central Heavy Workshop",
                    workshop_code="MECH-WS",
                    machine_id=jdata["machine"].id if jdata["machine"] else None,
                    creator_id=jdata["creator"].id,
                    approver_id=jdata.get("approver").id if jdata.get("approver") else None,
                    supervisor_id=jdata.get("supervisor").id if jdata.get("supervisor") else None,
                    assigned_personnel="T. Mukamuri (Lead Fitter), K. Chidzero (Electrician)",
                    estimated_hours=4.0,
                    estimated_cost=850.0,
                    action_taken="Inspected components, replaced worn seals, torqued fasteners to OEM specs." if jdata["status"] in ("COMPLETED", "VERIFIED") else None,
                    downtime_hours=3.5 if jdata["status"] in ("COMPLETED", "VERIFIED") else 0.0,
                    actual_start_time=now - timedelta(hours=5) if jdata["status"] in ("IN_PROGRESS", "COMPLETED", "VERIFIED") else None,
                    actual_end_time=now - timedelta(hours=1) if jdata["status"] in ("COMPLETED", "VERIFIED") else None,
                )
                db.add(jc)
                existing_jcs[jnum] = jc
                await db.flush()

                # Also create corresponding JobReport if IN_PROGRESS or COMPLETED
                if jdata["status"] in ("IN_PROGRESS", "COMPLETED", "VERIFIED"):
                    rep = JobReport(
                        id=uuid.uuid4(),
                        job_card_id=jc.id,
                        fault_found="Seal wear and internal leakage under pressure",
                        fault_code="HYD-LEAK-01",
                        corrective_action="Removed cylinder, honed barrel, installed genuine OEM seal kit.",
                        technical_notes="Torque verified with calibrated wrench. Post-assembly pressure test passed at 320 bar.",
                        actual_labour_hours=4.0,
                        actual_cost=450.0,
                    )
                    db.add(rep)

                # If SUBMITTED / PENDING_APPROVAL, create ApprovalRequest
                if jdata["status"] == "SUBMITTED":
                    ar = ApprovalRequest(
                        id=uuid.uuid4(),
                        resource_type="job_card",
                        resource_id=jc.id,
                        workflow_type="STANDARD",
                        priority=jdata["priority"],
                        status="OPEN",
                        created_by_id=jdata["creator"].id,
                    )
                    db.add(ar)
                    await db.flush()

                    step = ApprovalStep(
                        id=uuid.uuid4(),
                        approval_request_id=ar.id,
                        step_number=1,
                        authority_role="Supervisor",
                        required_permission="job_card:approve",
                        status="PENDING",
                    )
                    db.add(step)

        await db.flush()

        # ── 9. MACHINE REQUISITIONS IN VARIOUS STATES ────────────
        req_res = await db.execute(select(MachineRequisition))
        existing_reqs = {r.requisition_number: r for r in req_res.scalars().all() if r.requisition_number}

        requisitions_to_seed = [
            {
                "req_num": "MREQ-2026-0001",
                "type": mtypes["Rigid Dump Truck"],
                "purpose": "Production bench ore hauling from Bench 5 pit to ROM crusher pad",
                "status": "DRAFT",
                "machine": None,
            },
            {
                "req_num": "MREQ-2026-0002",
                "type": mtypes["Hydraulic Excavator"],
                "purpose": "Waste stripping at north wall cut-back, Bench 3",
                "status": "SUBMITTED",
                "machine": None,
            },
            {
                "req_num": "MREQ-2026-0003",
                "type": mtypes["Mobile Crane"],
                "purpose": "Primary crusher jaw plate maintenance and rigging support",
                "status": "REVIEWED",
                "machine": None,
            },
            {
                "req_num": "MREQ-2026-0004",
                "type": mtypes["Wheel Loader"],
                "purpose": "ROM pad stockpiling and feed hopper continuous feeding",
                "status": "AWAITING_ALLOCATION",
                "machine": None,
            },
            {
                "req_num": "MREQ-2026-0005",
                "type": mtypes["Rigid Dump Truck"],
                "purpose": "Concentrate haulage to regional dispatch siding",
                "status": "ALLOCATED",
                "machine": machines["DT-01"],
            },
            {
                "req_num": "MREQ-2026-0006",
                "type": mtypes["Track Dozer"],
                "purpose": "Pit floor drainage berm construction and cleanup",
                "status": "DISPATCHED",
                "machine": machines["DZ-01"],
            },
        ]

        for rdata in requisitions_to_seed:
            rnum = rdata["req_num"]
            if rnum not in existing_reqs:
                mr = MachineRequisition(
                    id=uuid.uuid4(),
                    requisition_number=rnum,
                    machine_type_id=rdata["type"].id,
                    machine_id=rdata["machine"].id if rdata["machine"] else None,
                    department_id=ops_dept.id,
                    requester_id=tech_u.id,
                    status=rdata["status"],
                    start_time=now + timedelta(hours=2),
                    end_time=now + timedelta(hours=14),
                    purpose=rdata["purpose"],
                    operator_required=True,
                )
                db.add(mr)
                existing_reqs[rnum] = mr
                await db.flush()

                # If SUBMITTED, add approval request
                if rdata["status"] == "SUBMITTED":
                    ar = ApprovalRequest(
                        id=uuid.uuid4(),
                        resource_type="machine_requisition",
                        resource_id=mr.id,
                        workflow_type="STANDARD",
                        priority=1,
                        status="OPEN",
                        created_by_id=tech_u.id,
                    )
                    db.add(ar)
                    await db.flush()

                    step = ApprovalStep(
                        id=uuid.uuid4(),
                        approval_request_id=ar.id,
                        step_number=1,
                        authority_role="Supervisor",
                        required_permission="requisition:review",
                        status="PENDING",
                    )
                    db.add(step)
                elif rdata["status"] == "REVIEWED":
                    ar = ApprovalRequest(
                        id=uuid.uuid4(),
                        resource_type="machine_requisition",
                        resource_id=mr.id,
                        workflow_type="STANDARD",
                        priority=2,
                        status="OPEN",
                        created_by_id=tech_u.id,
                    )
                    db.add(ar)
                    await db.flush()

                    step = ApprovalStep(
                        id=uuid.uuid4(),
                        approval_request_id=ar.id,
                        step_number=2,
                        authority_role="Department Manager",
                        required_permission="requisition:approve",
                        status="PENDING",
                    )
                    db.add(step)

        await db.commit()
        print("[+] Database seeding completed successfully!")
        print(f"    - Users: {len(users_by_email)}")
        print(f"    - Machines: {len(machines)}")
        print(f"    - Job Cards: {len(existing_jcs)}")
        print(f"    - Requisitions: {len(existing_reqs)}")

if __name__ == "__main__":
    asyncio.run(seed_data())
