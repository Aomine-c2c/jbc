"""
Bikita Minerals DWRMS — Realistic Synthetic Data Seeder using Faker
Generates rich industrial mining operations data:
- Sites, Locations, Departments, Teams, Positions, Users
- Heavy Fleet / Machines (Excavators, Haul Trucks, Crushers, Drills, Pumps, Loaders)
- Assets & Sub-assets
- Material Catalog / Spare Parts & Inventory
- Job Cards / Work Orders (Draft, Approved, In-Progress, Completed, Verified, Closed) with Parts, Labour, Execution Events & Comments
- Operational Requests & Machine Requisitions
- Contractors & Service Providers
- SLA Policies & Trackers
- Real-time Notifications & System Logs
"""

import asyncio
import uuid
import random
from datetime import datetime, timedelta, timezone
from faker import Faker

from app.db.session import SessionLocal, engine, Base
from app.core.security import get_password_hash

# Models
from app.modules.iam.models import (
    Organization, Site, Location, Department, Section, Team, Position, User, Role, UserRole, Scope
)
from app.modules.fleet.models import MachineType, Machine, MachineRequisition, MachineReservation
from app.modules.assets.models import Asset, AssetType, AssetStatus, AssetCriticality
from app.modules.materials.models import MaterialCatalogItem, MaterialRequirement, MaterialTransaction, MaterialRequirementStatus, MaterialTransactionType
from app.modules.requests.models import OperationalRequest, RequestType, RequestStatus, FulfillmentStatus
from app.modules.jobs.models import (
    JobCard, JobCardPart, JobCardLabour, JobCardExecutionEvent, JobCardComment, JobCardActionLog, JobCardCollaborator
)
from app.modules.contractors.models import ContractorCompany, ContractorCompanyStatus
from app.modules.notifications.models import Notification

fake = Faker()
Faker.seed(42)
random.seed(42)

MINING_MACHINE_CATALOG = [
    {"type": "Rigid Dump Truck", "cat": "Haulage & Transport", "rate": 180.0, "models": ["CAT 777D", "Komatsu HD785-7", "BelAZ 7555B"], "prefix": "DT"},
    {"type": "Hydraulic Mining Excavator", "cat": "Earthmoving & Excavation", "rate": 260.0, "models": ["Komatsu PC1250-8", "CAT 390F", "Hitachi EX1200-7"], "prefix": "EX"},
    {"type": "Mobile Jaw Crusher", "cat": "Crushing & Screening", "rate": 210.0, "models": ["Terex Finlay J-1175", "Metso Lokotrack LT120", "Sandvik QJ341"], "prefix": "CR"},
    {"type": "Surface Drill Rig", "cat": "Drilling & Blasting", "rate": 195.0, "models": ["Sandvik Pantera DP1500i", "Atlas Copco ROC D7", "Epiroc SmartROC T45"], "prefix": "DR"},
    {"type": "Wheel Loader", "cat": "Loading & Stockpiling", "rate": 145.0, "models": ["CAT 988K", "Komatsu WA500-8", "Volvo L250H"], "prefix": "WL"},
    {"type": "Heavy Duty Diesel Generator", "cat": "Power & Auxiliary", "rate": 90.0, "models": ["Atlas Copco QAS 500", "Cummins C550D5e", "CAT C18 600kVA"], "prefix": "GEN"},
    {"type": "Slurry & Dewatering Pump", "cat": "Pumping & Dewatering", "rate": 65.0, "models": ["Warman 8/6 E-MCR", "Sykes CP150", "Flygt 2125 Submersible"], "prefix": "PUMP"},
    {"type": "Light Support Vehicle 4x4", "cat": "Support Fleet", "rate": 45.0, "models": ["Toyota Land Cruiser 79 4x4", "Isuzu D-Max Mining Spec"], "prefix": "LV"},
    {"type": "Rough Terrain Crane", "cat": "Lifting & Rigging", "rate": 220.0, "models": ["Tadano GR-700EX", "Grove RT890E", "Terex RT 90"], "prefix": "CRN"},
]

SPARE_PARTS_CATALOG = [
    {"pn": "PRT-CRU-1001", "name": "Heavy Duty Manganese Jaw Plates 18% Mn", "cat": "Crusher Spares", "unit": "set", "cost": 4200.0, "store": "Heavy Spares Yard"},
    {"pn": "PRT-HYD-2045", "name": "High Pressure Hydraulic Filter 10 Micron", "cat": "Hydraulics", "unit": "piece", "cost": 185.0, "store": "Central Store A"},
    {"pn": "PRT-GET-3102", "name": "PC1250 Bucket Teeth Tiger Point & Pin", "cat": "Ground Engaging Tools", "unit": "piece", "cost": 310.0, "store": "Heavy Spares Yard"},
    {"pn": "PRT-BELT-4020", "name": "EP500/4 Conveyor Belt Rubber 1200mm (Roll)", "cat": "Conveyor Components", "unit": "meter", "cost": 88.0, "store": "Bulk Materials Yard"},
    {"pn": "PRT-BRG-5080", "name": "Timken Spherical Roller Bearing 22324 CC/W33", "cat": "Bearings & Transmission", "unit": "piece", "cost": 760.0, "store": "Precision Stores"},
    {"pn": "PRT-LUB-6010", "name": "15W40 Heavy Duty Diesel Engine Oil 200L Drum", "cat": "Lubricants & Oils", "unit": "drum", "cost": 540.0, "store": "Oils & Fluids Shed"},
    {"pn": "PRT-ELEC-7015", "name": "33kV Vacuum Circuit Breaker Vacuum Bottle", "cat": "Electrical HV", "unit": "piece", "cost": 1450.0, "store": "Electrical Stores"},
    {"pn": "PRT-FST-8090", "name": "High Tensile M24 Track Bolts & Nuts Gr 10.9", "cat": "Fasteners & Hardware", "unit": "box", "cost": 95.0, "store": "Central Store B"},
    {"pn": "PRT-PMP-9012", "name": "Warman Slurry Pump Impeller High Chrome A05", "cat": "Pump Spares", "unit": "piece", "cost": 2100.0, "store": "Heavy Spares Yard"},
    {"pn": "PRT-SAF-0030", "name": "Mining Hard Hat & Visor with Integrated Lamp Bracket", "cat": "PPE & Safety", "unit": "piece", "cost": 45.0, "store": "Safety Store"},
]

JOB_TEMPLATES = [
    {
        "title": "Primary Jaw Crusher Toggle Plate & Liner Replacement",
        "job_type": "PREVENTIVE",
        "maint_type": "MECHANICAL",
        "priority": 3,
        "est_hours": 12.0,
        "est_cost": 5800.0,
        "issue": "High wear detected on fixed manganese jaw liner and excessive toggle seat vibration during shift inspection.",
        "instruction": "Lock out and tag out crusher feed conveyor. Rig crane to remove hopper feed chute. Unbolt worn fixed jaw liners and replace with new set PRT-CRU-1001. Inspect toggle plate seating and re-torque all tie bolts to 1100 Nm."
    },
    {
        "title": "Komatsu PC1250 Boom Cylinder Seal Overhaul",
        "job_type": "CORRECTIVE",
        "maint_type": "HYDRAULIC",
        "priority": 2,
        "est_hours": 8.5,
        "est_cost": 2400.0,
        "issue": "Hydraulic oil misting and pressure drop observed on left-hand boom lift cylinder during bench loading.",
        "instruction": "Depressurize main hydraulic circuit. Disconnect high-pressure hoses and cap fittings. Rig cylinder support trestles. Remove gland nut and replace rod seal kit and wiper ring. Flush and refill with ISO VG 46 hydraulic fluid."
    },
    {
        "title": "DMS Plant Conveyor Belt 03 Splice Hot Vulcanization",
        "job_type": "EMERGENCY",
        "maint_type": "MECHANICAL",
        "priority": 3,
        "est_hours": 6.0,
        "est_cost": 3200.0,
        "issue": "Longitudinal tear and mechanical fastener failure on 1200mm overland conveyor discharge end.",
        "instruction": "Clamp conveyor belt at tail and drive pulleys. Cut damaged section square. Step ply ends (4-ply EP500). Apply hot vulcanizing cement, tie gum, and cover rubber. Cure under vulcanizing press at 145°C for 45 minutes."
    },
    {
        "title": "33kV Main Substation Transformer 2 Oil Dielectric Testing",
        "job_type": "INSPECTION",
        "maint_type": "ELECTRICAL",
        "priority": 1,
        "est_hours": 4.0,
        "est_cost": 950.0,
        "issue": "Scheduled bi-annual transformer oil condition monitoring and silica gel breather inspection.",
        "instruction": "Isolate secondary circuit breakers. Draw bottom oil sample in sterile syringe for DGA (Dissolved Gas Analysis). Perform dielectric breakdown test (minimum 50 kV target). Inspect Buchholz relay and replace saturated silica gel."
    },
    {
        "title": "CAT 777D Front Suspension Cylinder Pressure Recharge",
        "job_type": "PREVENTIVE",
        "maint_type": "SUSPENSION",
        "priority": 1,
        "est_hours": 3.5,
        "est_cost": 650.0,
        "issue": "Front left strut ride height below nominal specifications by 45mm.",
        "instruction": "Position haul truck on level maintenance pad and install wheel chocks. Check nitrogen charging pressure using high pressure charging manifold. Charge dry nitrogen to 2200 kPa as per OEM maintenance bulletin."
    },
    {
        "title": "Dense Media Separation Cyclone Feed Slurry Pump Overhaul",
        "job_type": "CORRECTIVE",
        "maint_type": "MECHANICAL",
        "priority": 2,
        "est_hours": 10.0,
        "est_cost": 4100.0,
        "issue": "Severe cavitation noise and flow reduction to DMS cyclones.",
        "instruction": "Isolate suction and discharge knife gate valves. Disassemble casing halves. Inspect throatbush and high chrome impeller for erosion. Replace impeller PRT-PMP-9012 and mechanical seal packing. Set impeller-to-throatbush clearance to 0.5mm."
    },
    {
        "title": "Flotation Air Blower Motor Bearing Lubrication & Thermography",
        "job_type": "PREVENTIVE",
        "maint_type": "ELECTRICAL",
        "priority": 0,
        "est_hours": 2.0,
        "est_cost": 350.0,
        "issue": "Routine condition monitoring run for flotation plant blower motors.",
        "instruction": "Capture FLIR thermal images of drive end and non-drive end bearings. Measure vibration spectrum (peak velocity mm/s). Apply 150g synthetic polyurea grease to drive end bearing grease nipples."
    },
    {
        "title": "Drill Rig Sandvik Pantera Feed Chain Tensioning & Mast Alignment",
        "job_type": "CORRECTIVE",
        "maint_type": "RIGGING",
        "priority": 2,
        "est_hours": 5.0,
        "est_cost": 1200.0,
        "issue": "Feed chain slack causing rod misalignment and premature shank wear during bench drilling.",
        "instruction": "Lower drill mast to horizontal cradle. Measure chain sag at mid-span. Adjust tensioning hydraulic cylinders to 30mm deflection. Inspect rock drill cradle slide pads and replace worn bronze wear strips."
    }
]

CONTRACTORS_DATA = [
    {"name": "ZimDrill Exploration & Mining Services", "vendor_code": "VND-ZIM-01", "service": "Specialized Deep Core Drilling & Blast Hole Prep", "phone": "+263 77 123 4567", "email": "contracts@zimdrill.co.zw"},
    {"name": "Masvingo Heavy Engineering & Hydraulics", "vendor_code": "VND-MASV-02", "service": "High Pressure Cylinder Overhauls & Line Boring", "phone": "+263 71 987 6543", "email": "services@masvingoeng.co.zw"},
    {"name": "Apex Rubber & Conveyor Technologies", "vendor_code": "VND-APEX-03", "service": "Overland Conveyor Splicing, Pulley Lagging & Relining", "phone": "+263 77 345 6789", "email": "fieldservice@apexrubber.co.zw"},
    {"name": "VoltPower High Voltage Contractors", "vendor_code": "VND-VOLT-04", "service": "33kV Switchgear Maintenance & Transformer Filtration", "phone": "+263 78 555 1212", "email": "ops@voltpower.co.zw"}
]


async def seed_faker_data():
    async with SessionLocal() as session:
        print("[+] Starting Faker Industrial Operations Data Seeding...")

        # ── 1. Load or Verify Base Organization & Site ──
        from sqlalchemy import select
        res = await session.execute(select(Organization))
        org = res.scalars().first()
        if not org:
            org = Organization(
                id=uuid.uuid4(),
                code="BIK",
                name="Bikita Minerals Ltd",
                description="Leading producer of lithium and petalite minerals",
                industry_type="Mining & Mineral Processing",
                country="Zimbabwe",
                currency="USD"
            )
            session.add(org)
            await session.commit()
            await session.refresh(org)

        res = await session.execute(select(Site).where(Site.organization_id == org.id))
        site = res.scalars().first()
        if not site:
            site = Site(
                id=uuid.uuid4(),
                organization_id=org.id,
                code="MSV-1",
                name="Masvingo Mining & Processing Complex",
                site_type="MINE_SITE",
                address="Masvingo Province, Zimbabwe"
            )
            session.add(site)
            await session.commit()
            await session.refresh(site)

        # ── 2. Locations ──
        locations_data = [
            {"code": "LOC-PIT-01", "name": "Bikita Open Cast Main Pit (Bench 4 - 6)", "type": "OPEN_PIT"},
            {"code": "LOC-CRU-01", "name": "Primary & Secondary Crushing Circuit", "type": "PLANT_AREA"},
            {"code": "LOC-DMS-01", "name": "Dense Media Separation (DMS) Plant 1", "type": "PLANT_AREA"},
            {"code": "LOC-FLOT-01", "name": "Lithium Flotation & Dewatering Circuit", "type": "PLANT_AREA"},
            {"code": "LOC-WS-MECH", "name": "Central Mechanical & Fabrication Workshop", "type": "WORKSHOP"},
            {"code": "LOC-WS-FLEET", "name": "Mobile Heavy Equipment Maintenance Yard", "type": "WORKSHOP"},
            {"code": "LOC-SUB-33KV", "name": "Main 33kV Electrical Substation Yard", "type": "SUBSTATION"},
            {"code": "LOC-STR-CENTRAL", "name": "Central Mining Spares & Consumables Warehouse", "type": "WAREHOUSE"},
            {"code": "LOC-TSF-01", "name": "Tailings Storage Facility & Pumping Station", "type": "TAILINGS"},
        ]
        
        locations = {}
        for loc_info in locations_data:
            res = await session.execute(select(Location).where(Location.code == loc_info["code"]))
            loc = res.scalars().first()
            if not loc:
                loc = Location(
                    id=uuid.uuid4(),
                    site_id=site.id,
                    code=loc_info["code"],
                    name=loc_info["name"],
                    location_type=loc_info["type"],
                    description=fake.sentence(nb_words=8)
                )
                session.add(loc)
                await session.commit()
                await session.refresh(loc)
            locations[loc_info["code"]] = loc

        # ── 3. Departments, Sections, Teams, Positions ──
        depts_map = {}
        for d_code, d_name in [
            ("IT", "Information Technology & Digital Systems"),
            ("Mechanical", "Mechanical Engineering & Fixed Plant"),
            ("Electrical", "Electrical & Instrumentation"),
            ("Mining", "Open Cast Mining Operations"),
            ("Safety", "Health, Safety & Environment (HSE)"),
            ("Stores", "Supply Chain & Materials Management")
        ]:
            res = await session.execute(select(Department).where(Department.code == d_code))
            dept = res.scalars().first()
            if not dept:
                dept = Department(id=uuid.uuid4(), site_id=site.id, code=d_code, name=d_name)
                session.add(dept)
                await session.commit()
                await session.refresh(dept)
            depts_map[d_code] = dept

        # ── 4. Users & Employees ──
        res = await session.execute(select(User))
        existing_users = {u.email: u for u in res.scalars().all()}

        roles_res = await session.execute(select(Role))
        roles_dict = {r.name: r for r in roles_res.scalars().all()}

        created_users = list(existing_users.values())
        
        # Generate 15 additional realistic operators/technicians/engineers
        additional_roles = [
            ("Mechanical", "J-MECH", "Technician", "EMP-2000"),
            ("Electrical", "ELEC-TECH", "Technician", "EMP-2010"),
            ("Mining", "OPERATOR", "Operator", "EMP-2020"),
            ("Mining", "OPERATOR", "Operator", "EMP-2030"),
            ("Stores", "RES-COORD", "Coordinator", "EMP-2040"),
            ("Safety", "SAFETY-OFF", "Safety Officer", "EMP-2050"),
            ("Mechanical", "S-MECH", "Supervisor", "EMP-2060"),
            ("Electrical", "ELEC-SUP", "Supervisor", "EMP-2070"),
        ]

        for i, (dept_key, pos_code, role_name, emp_base) in enumerate(additional_roles):
            email = f"staff.{dept_key.lower()}{i+1}@bikita.com"
            if email not in existing_users:
                first = fake.first_name()
                last = fake.last_name()
                u = User(
                    id=uuid.uuid4(),
                    email=email,
                    first_name=first,
                    last_name=last,
                    hashed_password=get_password_hash("password123"),
                    department_id=depts_map[dept_key].id,
                    employee_number=f"{emp_base}-{i+1}",
                    is_active=True,
                    is_superuser=False
                )
                session.add(u)
                await session.commit()
                await session.refresh(u)
                created_users.append(u)
                if role_name in roles_dict:
                    session.add(UserRole(user_id=u.id, role_id=roles_dict[role_name].id))
                await session.commit()

        # ── 5. Machine Types & Machines (Fleet) ──
        machine_types = {}
        machines_list = []
        for item in MINING_MACHINE_CATALOG:
            res = await session.execute(select(MachineType).where(MachineType.name == item["type"]))
            m_type = res.scalars().first()
            if not m_type:
                m_type = MachineType(
                    id=uuid.uuid4(),
                    name=item["type"],
                    description=f"Industrial grade {item['type']} for mineral operations",
                    category=item["cat"],
                    hourly_rate=item["rate"]
                )
                session.add(m_type)
                await session.commit()
                await session.refresh(m_type)
            machine_types[item["type"]] = m_type

            # Create 2-3 units per machine type
            for idx, model_name in enumerate(item["models"]):
                ident = f"{item['prefix']}-{101 + idx}"
                res = await session.execute(select(Machine).where(Machine.identifier == ident))
                mach = res.scalars().first()
                if not mach:
                    status_choice = random.choice(["AVAILABLE", "AVAILABLE", "IN_USE", "IN_USE", "UNDER_MAINTENANCE", "RESERVED"])
                    loc_choice = random.choice(list(locations.values()))
                    mach = Machine(
                        id=uuid.uuid4(),
                        machine_type_id=m_type.id,
                        identifier=ident,
                        serial_number=f"SN-{model_name.replace(' ', '').upper()}-{fake.numerify('######')}",
                        status=status_choice,
                        location=loc_choice.name,
                        location_id=loc_choice.id,
                        capacity_rating=f"{random.randint(25, 200)} Tonnes" if "Truck" in item["type"] or "Excavator" in item["type"] or "Loader" in item["type"] else f"{random.randint(100, 600)} kW",
                        current_hour_meter=round(random.uniform(850.0, 14200.0), 1),
                        last_maintenance_date=datetime.now(timezone.utc) - timedelta(days=random.randint(5, 60))
                    )
                    session.add(mach)
                    await session.commit()
                    await session.refresh(mach)
                machines_list.append(mach)

        # ── 6. Assets Catalog ──
        assets_list = []
        asset_types = [AssetType.PRODUCTION_EQUIPMENT, AssetType.MACHINE, AssetType.INFRASTRUCTURE, AssetType.EQUIPMENT]
        for i, loc in enumerate(locations.values()):
            tag = f"AST-BIK-{loc.code.split('-')[1]}-{101 + i}"
            res = await session.execute(select(Asset).where(Asset.asset_tag == tag))
            ast = res.scalars().first()
            if not ast:
                ast = Asset(
                    id=uuid.uuid4(),
                    asset_tag=tag,
                    name=f"{loc.name} Primary Installation Unit {i+1}",
                    asset_type=random.choice(asset_types).value,
                    status=random.choice([AssetStatus.AVAILABLE.value, AssetStatus.IN_USE.value, AssetStatus.UNDER_MAINTENANCE.value]),
                    criticality=random.choice([AssetCriticality.CRITICAL.value, AssetCriticality.HIGH.value, AssetCriticality.MEDIUM.value]),
                    location_id=loc.id,
                    department_id=depts_map["Mechanical"].id if i % 2 == 0 else depts_map["Electrical"].id,
                    manufacturer=random.choice(["Metso Outotec", "FLSmidth", "Weir Minerals", "Schneider Electric", "ABB Automation"]),
                    model_number=f"MOD-{fake.bothify(text='??-####')}",
                    serial_number=fake.bothify(text='SN-#######'),
                    purchase_cost=round(random.uniform(45000.0, 850000.0), 2),
                    current_value=round(random.uniform(25000.0, 700000.0), 2),
                    commissioned_date=datetime.now(timezone.utc) - timedelta(days=random.randint(200, 1800)),
                    specifications={"voltage": "33kV / 400V", "duty_cycle": "Continuous 24/7", "design_capacity_tph": random.randint(150, 600)}
                )
                session.add(ast)
                await session.commit()
                await session.refresh(ast)
            assets_list.append(ast)

        # ── 7. Material Catalog Items ──
        materials_list = []
        for mat in SPARE_PARTS_CATALOG:
            res = await session.execute(select(MaterialCatalogItem).where(MaterialCatalogItem.part_number == mat["pn"]))
            m_item = res.scalars().first()
            if not m_item:
                m_item = MaterialCatalogItem(
                    id=uuid.uuid4(),
                    part_number=mat["pn"],
                    name=mat["name"],
                    description=f"OEM Certified {mat['name']} with high wear resistance for harsh mining duty.",
                    category=mat["cat"],
                    unit_of_measure=mat["unit"],
                    default_unit_cost=mat["cost"],
                    primary_store=mat["store"],
                    is_active=True,
                    external_erp_id=f"ERP-INV-{mat['pn']}"
                )
                session.add(m_item)
                await session.commit()
                await session.refresh(m_item)
            materials_list.append(m_item)

        # ── 8. Contractors ──
        contractors_list = []
        for c_data in CONTRACTORS_DATA:
            res = await session.execute(select(ContractorCompany).where(ContractorCompany.company_code == c_data["vendor_code"]))
            contractor = res.scalars().first()
            if not contractor:
                contractor = ContractorCompany(
                    id=uuid.uuid4(),
                    name=c_data["name"],
                    company_code=c_data["vendor_code"],
                    primary_contact_name=fake.name(),
                    contact_email=c_data["email"],
                    contact_phone=c_data["phone"],
                    service_categories=[c_data["service"]],
                    status=ContractorCompanyStatus.ACTIVE.value,
                    safety_induction_valid_until=datetime.now(timezone.utc) + timedelta(days=365),
                    notes="Approved mining services provider with valid mine safety clearance."
                )
                session.add(contractor)
                await session.commit()
                await session.refresh(contractor)
            contractors_list.append(contractor)

        # ── 9. Job Cards (Work Orders) with Parts, Labour, Execution Events & Comments ──
        admin_user = existing_users.get("admin@bikita.com") or created_users[0]
        supervisor_user = existing_users.get("supervisor@bikita.com") or created_users[0]
        tech_user = existing_users.get("tech@bikita.com") or created_users[0]
        operator_user = existing_users.get("operator@bikita.com") or created_users[0]

        job_statuses = ["DRAFT", "PENDING_APPROVAL", "APPROVED", "IN_PROGRESS", "IN_PROGRESS", "COMPLETED", "VERIFIED", "CLOSED"]

        for idx, template in enumerate(JOB_TEMPLATES):
            job_num = f"JC-2026-{1000 + idx}"
            res = await session.execute(select(JobCard).where(JobCard.job_number == job_num))
            existing_jc = res.scalars().first()
            if not existing_jc:
                status = random.choice(job_statuses)
                loc = random.choice(list(locations.values()))
                mach = random.choice(machines_list) if machines_list else None
                created_dt = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30), hours=random.randint(1, 23))

                jc = JobCard(
                    id=uuid.uuid4(),
                    job_number=job_num,
                    title=template["title"],
                    description=fake.paragraph(nb_sentences=3),
                    status=status,
                    priority=template["priority"],
                    department_id=depts_map["Mechanical"].id if "MECHANICAL" in template["maint_type"] else depts_map["Electrical"].id,
                    requesting_department_id=depts_map["Mining"].id,
                    responsible_department_id=depts_map["Mechanical"].id,
                    location=loc.name,
                    location_id=loc.id,
                    plant_area=loc.name,
                    machine_id=mach.id if mach else None,
                    creator_id=operator_user.id,
                    required_date=created_dt + timedelta(days=2),
                    job_type=template["job_type"],
                    maintenance_type=template["maint_type"],
                    reported_issue=template["issue"],
                    job_instruction=template["instruction"],
                    estimated_hours=template["est_hours"],
                    estimated_cost=template["est_cost"],
                    created_at=created_dt
                )

                if status in ["APPROVED", "IN_PROGRESS", "COMPLETED", "VERIFIED", "CLOSED"]:
                    jc.approver_id = admin_user.id
                    jc.approved_at = created_dt + timedelta(hours=3)
                    jc.supervisor_id = supervisor_user.id
                    jc.assigned_date = created_dt + timedelta(hours=4)
                    jc.assigned_personnel = f"{tech_user.first_name} {tech_user.last_name}"

                if status in ["IN_PROGRESS", "COMPLETED", "VERIFIED", "CLOSED"]:
                    jc.actual_start_time = created_dt + timedelta(hours=6)
                    jc.downtime_hours = round(random.uniform(2.0, 10.0), 1)

                if status in ["COMPLETED", "VERIFIED", "CLOSED"]:
                    jc.actual_end_time = created_dt + timedelta(hours=14)
                    jc.action_taken = f"Completed full task according to standard safe work procedure: {template['instruction'][:150]}... All torque specifications verified and clearance checked."
                    jc.labour_details = f"Technician {tech_user.first_name} ({template['est_hours']} hrs) + Assistant (4 hrs)"
                    jc.completion_notes = "Quality inspection passed. Equipment returned to operating conditions with zero defects noted."
                    jc.equipment_used = "Crane TAD-700, 1-inch Torque Wrench, Hydraulic Puller Kit"
                    jc.observations = "Normal operating temperatures and vibration within ISO limits."

                if status in ["VERIFIED", "CLOSED"]:
                    jc.verified_at = created_dt + timedelta(hours=16)
                    jc.requester_confirmed = True
                    jc.requester_confirmed_at = created_dt + timedelta(hours=18)
                    jc.closure_date = created_dt + timedelta(hours=20)
                    jc.closed_by_id = supervisor_user.id

                session.add(jc)
                await session.commit()
                await session.refresh(jc)

                # Add Required Parts
                part_sample = random.sample(materials_list, k=min(2, len(materials_list)))
                for part_item in part_sample:
                    part_entry = JobCardPart(
                        id=uuid.uuid4(),
                        job_card_id=jc.id,
                        part_number=part_item.part_number,
                        part_name=part_item.name,
                        quantity=float(random.randint(1, 4)),
                        unit_cost=part_item.default_unit_cost,
                        is_material=random.choice([True, False])
                    )
                    session.add(part_entry)

                # Add Labour Entries
                labour_entry = JobCardLabour(
                    id=uuid.uuid4(),
                    job_card_id=jc.id,
                    technician_name=f"{tech_user.first_name} {tech_user.last_name}",
                    trade="Mechanical Fitter" if "MECHANICAL" in template["maint_type"] else "High Voltage Electrician",
                    hours_spent=round(random.uniform(4.0, 12.0), 1),
                    hourly_rate=45.0,
                    notes=f"Assigned shift work order execution for {template['title']}."
                )
                session.add(labour_entry)

                # Add Execution Event
                event = JobCardExecutionEvent(
                    id=uuid.uuid4(),
                    job_card_id=jc.id,
                    event_type="STARTED" if status in ["IN_PROGRESS", "COMPLETED", "VERIFIED", "CLOSED"] else "REQUESTED",
                    timestamp=created_dt + timedelta(hours=2),
                    duration_minutes=round(random.uniform(30.0, 360.0), 1),
                    operator_name=f"{tech_user.first_name} {tech_user.last_name}"
                )
                session.add(event)

                # Add Comments
                comment = JobCardComment(
                    id=uuid.uuid4(),
                    job_card_id=jc.id,
                    author_id=tech_user.id,
                    comment=f"Pre-task safety risk assessment (Take 5) completed. Work permit issued under clearance #{fake.numerify('WP-####')}."
                )
                session.add(comment)

                # Add Action Log
                action_log = JobCardActionLog(
                    id=uuid.uuid4(),
                    job_card_id=jc.id,
                    user_id=admin_user.id,
                    action="STATUS_CHANGE",
                    details=f"Job Card status transition to {status} recorded."
                )
                session.add(action_log)
                await session.commit()

        # ── 10. Operational Universal Requests ──
        req_types = [RequestType.MACHINE_REQUEST, RequestType.EQUIPMENT_REQUEST, RequestType.MATERIAL_REQUEST, RequestType.VEHICLE_REQUEST, RequestType.CONTRACTOR_REQUEST]
        req_statuses = [RequestStatus.SUBMITTED, RequestStatus.APPROVED, RequestStatus.AWAITING_FULFILLMENT, RequestStatus.FULFILLED, RequestStatus.CLOSED]

        for i in range(12):
            req_num = f"REQ-2026-{2001 + i}"
            res = await session.execute(select(OperationalRequest).where(OperationalRequest.request_number == req_num))
            if not res.scalars().first():
                r_type = random.choice(req_types)
                r_status = random.choice(req_statuses)
                loc = random.choice(list(locations.values()))
                created_dt = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 20))

                op_req = OperationalRequest(
                    id=uuid.uuid4(),
                    request_number=req_num,
                    title=f"{r_type.value.replace('_', ' ').title()} for {loc.name}",
                    purpose=f"Operational supply and equipment dispatch support for {loc.name}",
                    description=fake.paragraph(nb_sentences=2),
                    request_type=r_type.value,
                    status=r_status.value,
                    fulfillment_status=FulfillmentStatus.FULFILLED.value if r_status in [RequestStatus.FULFILLED, RequestStatus.CLOSED] else FulfillmentStatus.AWAITING_FULFILLMENT.value,
                    priority=random.randint(0, 3),
                    department_id=depts_map["Mining"].id if i % 2 == 0 else depts_map["Mechanical"].id,
                    requester_id=operator_user.id,
                    location_id=loc.id,
                    location=loc.name,
                    required_from=created_dt + timedelta(days=1),
                    required_to=created_dt + timedelta(days=3),
                    estimated_cost=round(random.uniform(500.0, 8500.0), 2),
                    type_specific_data={"risk_assessment_ref": f"RA-{fake.numerify('2026-####')}"}
                )
                session.add(op_req)
                await session.commit()

        # ── 11. Machine Requisitions & Reservations ──
        for i, mach in enumerate(machines_list[:6]):
            req_no = f"MREQ-2026-{3001 + i}"
            res = await session.execute(select(MachineRequisition).where(MachineRequisition.requisition_number == req_no))
            if not res.scalars().first():
                loc = random.choice(list(locations.values()))
                start_t = datetime.now(timezone.utc) + timedelta(days=random.randint(-5, 5), hours=random.randint(1, 8))
                end_t = start_t + timedelta(hours=random.randint(4, 24))

                m_req = MachineRequisition(
                    id=uuid.uuid4(),
                    requisition_number=req_no,
                    department_id=depts_map["Mining"].id,
                    requester_id=operator_user.id,
                    purpose=f"Bench load and haul ore transfer at {loc.name}",
                    machine_type_id=mach.machine_type_id,
                    machine_id=mach.id,
                    quantity=1,
                    location=loc.name,
                    location_id=loc.id,
                    start_time=start_t,
                    end_time=end_t,
                    estimated_duration_hours=round((end_t - start_t).total_seconds() / 3600.0, 1),
                    priority=random.randint(1, 3),
                    operator_required=True,
                    operator_name=f"{operator_user.first_name} {operator_user.last_name}",
                    status="ALLOCATED",
                    estimated_cost=mach.machine_type.hourly_rate * 8.0,
                    dept_approver_id=admin_user.id,
                    dept_approved_at=start_t - timedelta(hours=2)
                )
                session.add(m_req)
                await session.commit()
                await session.refresh(m_req)

                # Machine Reservation
                resv = MachineReservation(
                    id=uuid.uuid4(),
                    machine_id=mach.id,
                    requisition_id=m_req.id,
                    start_time=start_t,
                    end_time=end_t,
                    reservation_status="ALLOCATED",
                    reservation_type="REQUISITION"
                )
                session.add(resv)
                await session.commit()

        # ── 12. Notifications & Telemetry Feed ──
        notifications_data = [
            ("Crusher Liner Wear Exceeded 80%", "CRITICAL_ALERT", 3, "Primary Jaw Crusher Fixed Jaw 18% Mn reached replacement threshold."),
            ("Job Card JC-2026-1002 Approved", "APPROVAL", 2, "Supervisor approved Komatsu PC1250 Boom Cylinder Seal Overhaul."),
            ("Emergency Conveyor Hot Splicing Scheduled", "SYSTEM_ALERT", 3, "Overland Conveyor 03 splice crew dispatched to Tailings area."),
            ("Transformer Oil Dielectric Test Passed", "TASK_UPDATE", 1, "33kV Main Substation Transformer 2 returned 62 kV breakdown strength."),
            ("Spare Parts Requisition Dispatched", "TASK_UPDATE", 0, "Warehouse issued 4x Bucket Teeth and 2x Hydraulic Filters to Workshop A.")
        ]

        for title, n_type, n_prio, msg in notifications_data:
            notif = Notification(
                id=uuid.uuid4(),
                user_id=admin_user.id,
                type=n_type,
                priority=n_prio,
                title=title,
                message=msg,
                resource_type="JOB_CARD",
                resource_id=uuid.uuid4(),
                is_read=False
            )
            session.add(notif)
        await session.commit()

        print("[OK] Database Faker Data Seeding Successfully Finished!")

if __name__ == "__main__":
    asyncio.run(seed_faker_data())
