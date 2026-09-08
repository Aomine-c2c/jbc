"""
Authoritative Comprehensive Operational Demo Seeder for Bikita Minerals DWRMS.
Populates:
1. SLA Policies, Priority Configs, Live SLA Trackers (On Track, At Risk, Breached, Paused, Completed), and Escalation Logs.
2. Work Items, Statutory HSE Shift Audits, and Field Hazard Notices.
3. Materials Inventory & Spare Parts Catalog.
4. Contractor Engineering Companies & Inducted Workforce.
5. Job Cards with Safety Clearance Gates and LOTO locks.
"""
import asyncio
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, delete
from app.db.session import async_session_factory
from app.modules.iam.models import User, Role, Department, Location
from app.modules.assets.models import Asset
from app.modules.fleet.models import Machine
from app.modules.sla.models import (
    SLAPriorityConfig,
    SLAPolicy,
    SLATracker,
    SLAEscalationLog,
    SLAPriority,
    SLAStatus,
    SLAHealth,
)
from app.modules.work.models import WorkItem, WorkItemType, WorkItemStatus
from app.modules.materials.models import MaterialCatalogItem
from app.modules.contractors.models import (
    ContractorCompany,
    ContractorWorker,
    ContractorCompanyStatus,
    ContractorWorkerStatus,
)
from app.modules.jobs.models import JobCard


async def run_seed():
    print("[*] Starting comprehensive operational database seeder...")
    async with async_session_factory() as db:
        now = datetime.now(timezone.utc)

        # ── 1. LOOKUP REQUIRED BASE ENTITIES ─────────────────────
        dept_res = await db.execute(select(Department))
        depts = {d.name: d for d in dept_res.scalars().all()}
        
        # Match real departments in database
        maint_dept = (
            depts.get("Maintenance")
            or depts.get("Mechanical Engineering & Fixed Plant")
            or next(iter(depts.values()), None)
        )
        ops_dept = depts.get("Mining Operations") or depts.get("Operations") or maint_dept
        hse_dept = depts.get("Safety & HSE") or depts.get("Health, Safety & Environment (HSE)") or maint_dept

        loc_res = await db.execute(select(Location))
        locs = {l.name: l for l in loc_res.scalars().all()}
        workshop_loc = (
            locs.get("Central Heavy Workshop")
            or locs.get("Central Mechanical & Fabrication Workshop")
            or next(iter(locs.values()), None)
        )
        pit_loc = (
            locs.get("Open Pit - Bench 5")
            or locs.get("Bikita Open Cast Main Pit (Bench 4 - 6)")
            or workshop_loc
        )
        crusher_loc = (
            locs.get("Primary Crusher Station")
            or locs.get("Primary & Secondary Crushing Circuit")
            or workshop_loc
        )
        plant_loc = (
            locs.get("Spodumene Concentrator")
            or locs.get("Dense Media Separation (DMS) Plant 1")
            or workshop_loc
        )

        user_res = await db.execute(select(User))
        users = {u.email: u for u in user_res.scalars().all()}
        tech_user = users.get("tech@bikita.com") or next(iter(users.values()), None)
        sup_user = users.get("supervisor@bikita.com") or tech_user
        safety_user = users.get("safety@bikita.com") or tech_user

        # ── 2. SLA PRIORITY CONFIGURATIONS ───────────────────────
        print("    -> Seeding SLA Priority Configs...")
        p_configs = [
            ("CRITICAL", "Critical Breakdown", "Immediate threat to life, production stoppage, or critical infrastructure loss", "#ef4444", 30, 240, 10),
            ("HIGH", "High Urgency", "Heavy equipment down, high safety hazard, or secondary production line stopped", "#f97316", 60, 480, 20),
            ("NORMAL", "Normal Priority", "Standard mechanical/electrical repair or routine maintenance order", "#3b82f6", 240, 1440, 30),
            ("LOW", "Low Priority", "Cosmetic, scheduled inspection, or minor housekeeping maintenance", "#10b981", 480, 2880, 40),
        ]
        for name, dname, desc, color, r_min, c_min, order in p_configs:
            existing = await db.execute(select(SLAPriorityConfig).where(SLAPriorityConfig.name == name))
            if not existing.scalar_one_or_none():
                pc = SLAPriorityConfig(
                    id=uuid.uuid4(),
                    name=name,
                    display_name=dname,
                    description=desc,
                    color_code=color,
                    default_response_minutes=r_min,
                    default_completion_minutes=c_min,
                    sort_order=order,
                    is_active=True,
                )
                db.add(pc)
        await db.flush()

        # ── 3. SLA POLICIES ──────────────────────────────────────
        print("    -> Seeding SLA Policies...")
        policies_data = [
            {
                "name": "Critical Plant Breakdown SLA",
                "desc": "Mandatory response and recovery time for primary crushing, processing plant, and power substation failures.",
                "priority": "CRITICAL",
                "work_type": "MAINTENANCE",
                "r_mins": 30,
                "c_mins": 240,
                "warn_pct": 80,
                "is_default": False,
                "rules": [
                    {"level": 1, "trigger": "RESPONSE_WARNING", "after_percentage": 80, "target_role": "Supervisor"},
                    {"level": 2, "trigger": "RESPONSE_BREACH", "after_percentage": 100, "target_role": "Department Manager"},
                    {"level": 3, "trigger": "COMPLETION_BREACH", "after_percentage": 100, "target_role": "Plant Superintendent"},
                ],
            },
            {
                "name": "Mine Safety Hazard SLA",
                "desc": "Statutory response window for critical/high field hazards and environmental containment orders.",
                "priority": "HIGH",
                "work_type": "INSPECTION",
                "r_mins": 60,
                "c_mins": 360,
                "warn_pct": 75,
                "is_default": False,
                "rules": [
                    {"level": 1, "trigger": "RESPONSE_WARNING", "after_percentage": 75, "target_role": "Safety Officer"},
                    {"level": 2, "trigger": "RESPONSE_BREACH", "after_percentage": 100, "target_role": "HSE Manager"},
                ],
            },
            {
                "name": "Standard Mechanical Job Card SLA",
                "desc": "Baseline SLA policy for preventive and corrective maintenance on plant equipment.",
                "priority": "NORMAL",
                "work_type": "JOB_CARD",
                "r_mins": 120,
                "c_mins": 720,
                "warn_pct": 80,
                "is_default": True,
                "rules": [
                    {"level": 1, "trigger": "RESPONSE_WARNING", "after_percentage": 80, "target_role": "Supervisor"},
                ],
            },
        ]

        saved_policies = {}
        for pdata in policies_data:
            existing = await db.execute(select(SLAPolicy).where(SLAPolicy.name == pdata["name"]))
            p = existing.scalar_one_or_none()
            if not p:
                p = SLAPolicy(
                    id=uuid.uuid4(),
                    name=pdata["name"],
                    description=pdata["desc"],
                    priority=pdata["priority"],
                    work_type=pdata["work_type"],
                    department_id=maint_dept.id if maint_dept else None,
                    response_time_minutes=pdata["r_mins"],
                    completion_time_minutes=pdata["c_mins"],
                    warning_threshold_percentage=pdata["warn_pct"],
                    completion_warning_threshold_percentage=pdata["warn_pct"],
                    notification_cooldown_minutes=60,
                    escalation_rules=pdata["rules"],
                    is_active=True,
                    is_default=pdata["is_default"],
                )
                db.add(p)
                await db.flush()
            saved_policies[pdata["name"]] = p

        # ── 4. LIVE SLA TRACKERS & ESCALATION LOGS ───────────────
        print("    -> Seeding Live SLA Trackers (On Track, At Risk, Breached, Paused, Completed)...")
        crit_policy = saved_policies.get("Critical Plant Breakdown SLA")
        safety_policy = saved_policies.get("Mine Safety Hazard SLA")
        std_policy = saved_policies.get("Standard Mechanical Job Card SLA")

        trackers_to_seed = [
            # 1. ON TRACK
            {
                "ref": "SLA-TRK-2026-0001",
                "title": "Primary Crusher Hydraulic Unit Pressure Drop",
                "priority": "NORMAL",
                "policy": std_policy,
                "health": SLAHealth.ON_TRACK.value,
                "status": SLAStatus.IN_PROGRESS.value,
                "created_at": now - timedelta(minutes=45),
                "target_resp": now + timedelta(minutes=75),
                "actual_resp": now - timedelta(minutes=30),
                "target_comp": now + timedelta(minutes=675),
                "paused_mins": 0.0,
                "escalation_level": 0,
                "logs": [],
            },
            # 2. ON TRACK
            {
                "ref": "SLA-TRK-2026-0002",
                "title": "Conveyor CV-01 Idler Roller Lubrication & Alignment",
                "priority": "NORMAL",
                "policy": std_policy,
                "health": SLAHealth.ON_TRACK.value,
                "status": SLAStatus.CREATED.value,
                "created_at": now - timedelta(minutes=15),
                "target_resp": now + timedelta(minutes=105),
                "actual_resp": None,
                "target_comp": now + timedelta(minutes=705),
                "paused_mins": 0.0,
                "escalation_level": 0,
                "logs": [],
            },
            # 3. AT RISK (Approaching Warning Threshold: 86% elapsed)
            {
                "ref": "SLA-TRK-2026-0003",
                "title": "Flotation Cell 3 Aeration Impeller Excessive Vibration",
                "priority": "HIGH",
                "policy": safety_policy,
                "health": SLAHealth.AT_RISK.value,
                "status": SLAStatus.IN_PROGRESS.value,
                "created_at": now - timedelta(minutes=310),
                "target_resp": now - timedelta(minutes=250),
                "actual_resp": now - timedelta(minutes=270),
                "target_comp": now + timedelta(minutes=50),  # 310 of 360 mins elapsed = 86%
                "paused_mins": 0.0,
                "escalation_level": 1,
                "logs": [
                    (1, "WARNING_THRESHOLD", "Target completion window is 86% elapsed. Automated warning dispatched to Shift Supervisor.", now - timedelta(minutes=20))
                ],
            },
            # 4. AT RISK (Approaching Warning Threshold: 88% elapsed)
            {
                "ref": "SLA-TRK-2026-0004",
                "title": "33kV Substation Transformer Oil Temperature Rise",
                "priority": "HIGH",
                "policy": safety_policy,
                "health": SLAHealth.AT_RISK.value,
                "status": SLAStatus.IN_PROGRESS.value,
                "created_at": now - timedelta(minutes=315),
                "target_resp": now - timedelta(minutes=260),
                "actual_resp": now - timedelta(minutes=280),
                "target_comp": now + timedelta(minutes=45),  # 88% elapsed
                "paused_mins": 0.0,
                "escalation_level": 1,
                "logs": [
                    (1, "WARNING_THRESHOLD", "Target completion window is 88% elapsed. Automated alert dispatched to Electrical Engineering.", now - timedelta(minutes=15))
                ],
            },
            # 5. BREACHED (Response Breach)
            {
                "ref": "SLA-TRK-2026-0005",
                "title": "Dense Media Separation (DMS) Sump Slurry Overflow",
                "priority": "CRITICAL",
                "policy": crit_policy,
                "health": SLAHealth.BREACHED_RESPONSE.value,
                "status": SLAStatus.IN_PROGRESS.value,
                "created_at": now - timedelta(minutes=75),
                "target_resp": now - timedelta(minutes=45),  # 30m response exceeded
                "actual_resp": now - timedelta(minutes=10),
                "target_comp": now + timedelta(minutes=165),
                "paused_mins": 0.0,
                "escalation_level": 2,
                "breach_reason": "Emergency response window (30 mins) breached by 35 minutes before technician dispatch.",
                "logs": [
                    (1, "RESPONSE_WARNING", "80% of response window elapsed with no assigned artisan.", now - timedelta(minutes=51)),
                    (2, "RESPONSE_BREACH", "SLA Response window breached (30m target). Escalated to Department Manager.", now - timedelta(minutes=45)),
                ],
            },
            # 6. BREACHED (Completion Breach)
            {
                "ref": "SLA-TRK-2026-0006",
                "title": "Emergency Tailings Pump P-201 Discharge Valve Seizure",
                "priority": "CRITICAL",
                "policy": crit_policy,
                "health": SLAHealth.BREACHED_COMPLETION.value,
                "status": SLAStatus.IN_PROGRESS.value,
                "created_at": now - timedelta(minutes=360),
                "target_resp": now - timedelta(minutes=335),
                "actual_resp": now - timedelta(minutes=340),
                "target_comp": now - timedelta(minutes=120),  # 240m target completion breached 2 hours ago
                "paused_mins": 0.0,
                "escalation_level": 3,
                "breach_reason": "Target completion window (240 mins) breached by 120 minutes due to seized flange bolts.",
                "logs": [
                    (1, "RESPONSE_WARNING", "80% response window elapsed.", now - timedelta(minutes=336)),
                    (2, "COMPLETION_WARNING", "80% completion window elapsed. Warning dispatched to Workshop Foreman.", now - timedelta(minutes=168)),
                    (3, "COMPLETION_BREACH", "Critical Completion Deadline Breached. Level 3 emergency notice sent to Plant Superintendent.", now - timedelta(minutes=120)),
                ],
            },
            # 7. PAUSED SLA
            {
                "ref": "SLA-TRK-2026-0007",
                "title": "Ball Mill Trunnion Bearing Re-alignment",
                "priority": "NORMAL",
                "policy": std_policy,
                "health": SLAHealth.ON_TRACK.value,
                "status": SLAStatus.PAUSED.value,
                "created_at": now - timedelta(minutes=240),
                "target_resp": now - timedelta(minutes=200),
                "actual_resp": now - timedelta(minutes=210),
                "target_comp": now + timedelta(minutes=600),
                "paused_mins": 145.0,
                "escalation_level": 0,
                "logs": [],
            },
            # 8. COMPLETED (MET)
            {
                "ref": "SLA-TRK-2026-0008",
                "title": "Secondary Screen Deck Mesh Replacement",
                "priority": "NORMAL",
                "policy": std_policy,
                "health": SLAHealth.MET.value,
                "status": SLAStatus.COMPLETED.value,
                "created_at": now - timedelta(days=1),
                "target_resp": now - timedelta(days=1, minutes=-120),
                "actual_resp": now - timedelta(days=1, minutes=-25),
                "target_comp": now - timedelta(days=1, minutes=-720),
                "actual_comp": now - timedelta(days=1, minutes=-410),
                "paused_mins": 0.0,
                "escalation_level": 0,
                "logs": [],
            },
        ]

        for tdata in trackers_to_seed:
            existing = await db.execute(select(SLATracker).where(SLATracker.resource_reference == tdata["ref"]))
            trk = existing.scalar_one_or_none()
            if not trk:
                trk = SLATracker(
                    id=uuid.uuid4(),
                    policy_id=tdata["policy"].id if tdata["policy"] else None,
                    resource_type="work_item",
                    resource_id=uuid.uuid4(),
                    resource_reference=tdata["ref"],
                    title=tdata["title"],
                    priority=tdata["priority"],
                    department_id=maint_dept.id if maint_dept else None,
                    location_id=workshop_loc.id if workshop_loc else None,
                    status=tdata["status"],
                    health=tdata["health"],
                    target_response_at=tdata["target_resp"],
                    target_completion_at=tdata["target_comp"],
                    actual_response_at=tdata["actual_resp"],
                    actual_completion_at=tdata.get("actual_comp"),
                    total_paused_minutes=tdata["paused_mins"],
                    current_escalation_level=tdata["escalation_level"],
                    breach_reason=tdata.get("breach_reason"),
                    created_at=tdata["created_at"],
                )
                db.add(trk)
                await db.flush()

                for lvl, trg, msg, log_time in tdata["logs"]:
                    elog = SLAEscalationLog(
                        id=uuid.uuid4(),
                        tracker_id=trk.id,
                        escalation_level=lvl,
                        trigger_type=trg,
                        notified_role="Workshop Supervisor" if lvl == 1 else ("Department Manager" if lvl == 2 else "Plant Superintendent"),
                        notified_user_ids=[],
                        message=msg,
                        fired_at=log_time,
                    )
                    db.add(elog)

        # ── 5. STATUTORY SHIFT AUDITS & HAZARD WORK ITEMS ────────
        print("    -> Seeding Statutory Shift Audits & Field Hazard Notices...")
        work_items_to_seed = [
            {
                "ref": "AUD-2026-0101",
                "type": WorkItemType.INSPECTION.value,
                "title": "Daily Open Pit Haul Road Berm & Safety Bund Audit",
                "desc": "Verify minimum bund height (1.5x haul truck tire diameter) along main pit haulage ramp.",
                "status": WorkItemStatus.IN_PROGRESS.value,
                "priority": 2,
                "dept": ops_dept,
                "loc": pit_loc,
            },
            {
                "ref": "AUD-2026-0102",
                "type": WorkItemType.INSPECTION.value,
                "title": "Substation 33kV Fire Suppression & Inergen Gas Flood System Audit",
                "desc": "Check pressure gauges, thermal sensors, and manual release break-glass units.",
                "status": WorkItemStatus.APPROVED.value,
                "priority": 3,
                "dept": maint_dept,
                "loc": workshop_loc,
            },
            {
                "ref": "AUD-2026-0103",
                "type": WorkItemType.INSPECTION.value,
                "title": "Tailings Storage Facility (TSF) Dam Crest Freeboard & Siphon Check",
                "desc": "Measure piezometer hydrostatic levels and verify decant pump overflow rate.",
                "status": WorkItemStatus.IN_PROGRESS.value,
                "priority": 2,
                "dept": ops_dept,
                "loc": plant_loc,
            },
            {
                "ref": "HAZ-2026-0041",
                "type": WorkItemType.OTHER.value,
                "title": "CRITICAL: Guarding Removed on Secondary Crusher Drive Pulley",
                "desc": "Exposed high-speed V-belt and pulley without interlock guard. Immediate Red-Tag issued.",
                "status": WorkItemStatus.ON_HOLD.value,
                "priority": 4,
                "dept": maint_dept,
                "loc": crusher_loc,
            },
            {
                "ref": "HAZ-2026-0042",
                "type": WorkItemType.OTHER.value,
                "title": "HIGH: Lubricant & Heavy Oil Spill on Ball Mill Walkway",
                "desc": "Slip and fall hazard on elevated gantry. Containment socks and sawdust deployed.",
                "status": WorkItemStatus.IN_PROGRESS.value,
                "priority": 3,
                "dept": maint_dept,
                "loc": plant_loc,
            },
            {
                "ref": "HAZ-2026-0043",
                "type": WorkItemType.OTHER.value,
                "title": "MEDIUM: Haul Truck DT-02 Reversing Siren Intermittent Failure",
                "desc": "Near-miss reported by bench spotter. Unit flagged for electrical inspection.",
                "status": WorkItemStatus.SUBMITTED.value,
                "priority": 2,
                "dept": ops_dept,
                "loc": pit_loc,
            },
        ]

        for wdata in work_items_to_seed:
            existing = await db.execute(select(WorkItem).where(WorkItem.reference_number == wdata["ref"]))
            if not existing.scalar_one_or_none():
                wi = WorkItem(
                    id=uuid.uuid4(),
                    reference_number=wdata["ref"],
                    work_type=wdata["type"],
                    title=wdata["title"],
                    description=wdata["desc"],
                    status=wdata["status"],
                    priority=wdata["priority"],
                    department_id=wdata["dept"].id if wdata["dept"] else maint_dept.id,
                    location_id=wdata["loc"].id if wdata["loc"] else None,
                    location=wdata["loc"].name if wdata["loc"] else "Bikita Site",
                    requester_id=safety_user.id if safety_user else tech_user.id,
                    created_at=now - timedelta(hours=3),
                )
                db.add(wi)

        # ── 6. MATERIALS CATALOG & PARTS INVENTORY ───────────────
        print("    -> Seeding Materials Catalog & Inventory...")
        materials_data = [
            ("PRT-PMP-9012", "Warman Slurry Pump Impeller High Chrome A05", "Ultra-wear resistant 27% high chrome cast iron impeller for froth pumps.", "Pump Spares", "piece", 2100.0, "Heavy Spares Yard"),
            ("PRT-ELEC-7015", "33kV Vacuum Circuit Breaker Vacuum Bottle", "High reliability arc interruption vacuum interrupter bottle.", "Electrical HV", "piece", 1450.0, "Electrical Stores"),
            ("PRT-LUB-6010", "15W40 Heavy Duty Diesel Engine Oil 200L Drum", "API CK-4 premium mineral engine oil for heavy haul fleet.", "Lubricants & Oils", "drum", 540.0, "Oils & Fluids Shed"),
            ("PRT-BRG-4501", "SKF 22220 EK Spherical Roller Bearing", "Tapered bore double row spherical roller bearing for vibrating screens.", "Bearings", "piece", 320.0, "Mechanical Store Shelf B-04"),
            ("PRT-BLT-3305", "Optibelt Red Power 3 SPB 3150 V-Belt", "High performance wrapped wedge belt for primary jaw crusher motor.", "Belts & Drives", "piece", 85.0, "Mechanical Store Shelf D-12"),
            ("PRT-HSE-8020", "Hydraulic Hose 4SP 1-inch 5000 PSI (Per Meter)", "High pressure 4-spiral steel wire reinforced hydraulic hose.", "Hydraulics", "meter", 42.0, "Hose Fabrication Shed"),
            ("PRT-FLT-1102", "CAT 777D Heavy Duty Primary Air Filter Element", "Dual-stage radial seal air filter element for 3508B diesel engines.", "Fleet Filters", "piece", 195.0, "Heavy Haul Workshop Stores"),
            ("PRT-SCR-2040", "Polyurethane Modular Screen Panel 300x300mm 5mm Slot", "Abrasion resistant screen panel for spodumene dewatering screen.", "Screening Media", "piece", 65.0, "Concentrator Yard"),
        ]

        for part_num, name, desc, cat, uom, cost, store in materials_data:
            existing = await db.execute(select(MaterialCatalogItem).where(MaterialCatalogItem.part_number == part_num))
            if not existing.scalar_one_or_none():
                mat = MaterialCatalogItem(
                    id=uuid.uuid4(),
                    part_number=part_num,
                    name=name,
                    description=desc,
                    category=cat,
                    unit_of_measure=uom,
                    default_unit_cost=cost,
                    primary_store=store,
                    is_active=True,
                )
                db.add(mat)

        # ── 7. CONTRACTOR COMPANIES & WORKFORCE ──────────────────
        print("    -> Seeding Contractors & Specialized Workforce...")
        contractors_data = [
            {
                "code": "CONT-BARLOW-01",
                "name": "Barloworld Equipment Zimbabwe",
                "reg": "REG-ZW-10492/2012",
                "contact": "Tafadzwa Chidzero",
                "email": "tchidzero@barloworld-zw.com",
                "phone": "+263 77 210 4921",
                "cats": ["Earthmoving Machinery", "CAT Powertrain Rebuilds", "Hydraulics"],
                "workers": [
                    ("WKR-BAR-01", "Simba Chimedza", "Senior Certified CAT Fitter", "EMP-CAT-8812", "+263 77 341 0921"),
                    ("WKR-BAR-02", "Garikai Mudzimu", "Heavy Plant Auto Electrician", "EMP-CAT-8815", "+263 77 412 8820"),
                ],
            },
            {
                "code": "CONT-ABB-02",
                "name": "ABB Power Grids Southern Africa",
                "reg": "REG-ZW-40192/2015",
                "contact": "Farai Marange",
                "email": "fmarange@abb-zw.com",
                "phone": "+263 71 288 3012",
                "cats": ["High Voltage Switchgear", "Transformer Overhauls", "Protection Relays"],
                "workers": [
                    ("WKR-ABB-01", "Nyasha Mapfumo", "HV Substation Specialist", "EMP-ABB-3010", "+263 71 882 1092"),
                ],
            },
            {
                "code": "CONT-METSO-03",
                "name": "Metso Outotec Mineral Processing Support",
                "reg": "REG-ZW-88102/2018",
                "contact": "Blessing Mutasa",
                "email": "bmutasa@metso-zw.com",
                "phone": "+263 77 550 4910",
                "cats": ["Crushing Circuits", "DMS Cyclones", "Flotation Plants"],
                "workers": [
                    ("WKR-MET-01", "Tawanda Zizhou", "Mill Liner & Crusher Specialist", "EMP-MET-4401", "+263 77 901 2234"),
                ],
            },
        ]

        for cdata in contractors_data:
            existing = await db.execute(select(ContractorCompany).where(ContractorCompany.company_code == cdata["code"]))
            comp = existing.scalar_one_or_none()
            if not comp:
                comp = ContractorCompany(
                    id=uuid.uuid4(),
                    company_code=cdata["code"],
                    name=cdata["name"],
                    registration_number=cdata["reg"],
                    primary_contact_name=cdata["contact"],
                    contact_email=cdata["email"],
                    contact_phone=cdata["phone"],
                    service_categories=cdata["cats"],
                    status=ContractorCompanyStatus.ACTIVE.value,
                    safety_induction_valid_until=now + timedelta(days=300),
                )
                db.add(comp)
                await db.flush()

                for w_code, full_name, skill, b_num, w_phone in cdata["workers"]:
                    w_exist = await db.execute(select(ContractorWorker).where(ContractorWorker.worker_code == w_code))
                    if not w_exist.scalar_one_or_none():
                        cw = ContractorWorker(
                            id=uuid.uuid4(),
                            contractor_company_id=comp.id,
                            worker_code=w_code,
                            full_name=full_name,
                            skill_or_role=skill,
                            badge_number=b_num,
                            phone_number=w_phone,
                            status=ContractorWorkerStatus.ACTIVE.value,
                            certification_expiry=now + timedelta(days=180),
                            certification_records=[{"certification": skill, "issued_at": (now - timedelta(days=90)).isoformat()}],
                        )
                        db.add(cw)

        # ── 8. GATED JOB CARDS WITH LOTO & SAFETY CLEARANCE ──────
        print("    -> Seeding Gated Job Cards with LOTO Isolations...")
        job_cards_to_seed = [
            {
                "num": "JOB-2026-081",
                "title": "Primary Jaw Crusher Stationary Jaw Plate Replacement",
                "desc": "Heavy wear on manganese jaw plates. Requires 525V electrical lock-out and hydraulic energy dissipation.",
                "status": "IN_PROGRESS",
                "priority": 3,
                "safety_cleared": False,
                "loto_tag": "LOTO-BK-0081",
                "plant_area": "Primary Crushing Station",
                "loc": crusher_loc,
            },
            {
                "num": "JOB-2026-082",
                "title": "Ball Mill 1 Trunnion Lubrication Line Inspection & Seal Replacement",
                "desc": "Confined space entry permit required for mill interior inspection. Hydrostatic zero-pressure lock-out verified.",
                "status": "APPROVED",
                "priority": 2,
                "safety_cleared": False,
                "loto_tag": "LOTO-BK-0082",
                "plant_area": "Milling & Grinding",
                "loc": plant_loc,
            },
            {
                "num": "JOB-2026-083",
                "title": "Flotation Bank 2 High-Pressure Air Line Manifold Repair",
                "desc": "Pneumatic 10 Bar isolation and bleeding required before flange unbolting.",
                "status": "IN_PROGRESS",
                "priority": 2,
                "safety_cleared": True,
                "safety_cleared_at": now - timedelta(hours=4),
                "loto_tag": "LOTO-BK-0083",
                "plant_area": "Spodumene Flotation",
                "loc": plant_loc,
            },
        ]

        for jdata in job_cards_to_seed:
            existing = await db.execute(select(JobCard).where(JobCard.job_number == jdata["num"]))
            if not existing.scalar_one_or_none():
                jc = JobCard(
                    id=uuid.uuid4(),
                    job_number=jdata["num"],
                    title=jdata["title"],
                    description=jdata["desc"],
                    department_id=maint_dept.id if maint_dept else None,
                    location_id=jdata["loc"].id if jdata["loc"] else None,
                    plant_area=jdata.get("plant_area"),
                    assigned_personnel="Tafadzwa Chidzero (Lead Mech), Simba Chimedza",
                    creator_id=sup_user.id if sup_user else tech_user.id,
                    status=jdata["status"],
                    priority=jdata["priority"],
                    safety_cleared=jdata["safety_cleared"],
                    safety_cleared_at=jdata.get("safety_cleared_at"),
                    safety_cleared_by_id=safety_user.id if jdata["safety_cleared"] and safety_user else None,
                    loto_tag_number=jdata["loto_tag"],
                    created_at=now - timedelta(hours=6),
                )
                db.add(jc)

        await db.commit()
        print("[+] Comprehensive operational seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(run_seed())
