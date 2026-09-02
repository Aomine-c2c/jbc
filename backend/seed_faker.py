"""
Bikita Minerals DWRMS — Enterprise Synthetic Data Seeder using Faker
Generates rich industrial mining operations data:
- Sites, Locations, Departments, Teams, Positions, Users & Roles
- Heavy Fleet / Machines (Excavators, Haul Trucks, Crushers, Drills, Pumps, Loaders)
- Assets & Sub-assets with Criticality Levels
- Material Catalog / Spare Parts & Inventory
- Contractors & Service Providers with Safety Clearance
- Job Cards / Work Orders (Draft, Pending Approval, Approved, In-Progress, Completed, Verified, Closed) with Parts, Labour, Execution Events & Comments
- Multi-Stage Approval Requests & Steps (linked to pending Job Cards & Machine Requisitions)
- Operational Universal Requests & Machine Requisitions
- SLA Priority Configurations, Policies & Trackers
- Real-time Notifications & Immutable Business Audit Logs
- Workflow Definitions & Approval Steps
"""

import asyncio
import uuid
import random
from datetime import datetime, timedelta, timezone
from faker import Faker
from sqlalchemy import select

def now_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)

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
from app.modules.approvals.models import ApprovalRequest, ApprovalStep, WorkflowDefinition, WorkflowStepDef
from app.modules.contractors.models import ContractorCompany, ContractorCompanyStatus
from app.modules.notifications.models import Notification
from app.modules.audit.models import BusinessAuditLog
from app.modules.sla.models import SLAPriorityConfig, SLAPolicy
from app.modules.work.models import WorkItem, WorkItemType, WorkItemStatus

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
    {"pn": "PRT-SAF-0030", "name": "Mining Hard Hat & Visor with Lamp Bracket", "cat": "PPE & Safety", "unit": "piece", "cost": 45.0, "store": "Safety Store"},
    {"pn": "PRT-VLV-1120", "name": "High Pressure Knife Gate Valve DN200 PN25", "cat": "Valves & Piping", "unit": "piece", "cost": 1250.0, "store": "Heavy Spares Yard"},
    {"pn": "PRT-MOT-5500", "name": "WEG Mining Duty Electric Motor 75kW 4-Pole", "cat": "Motors & Drives", "unit": "piece", "cost": 5800.0, "store": "Electrical Stores"},
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
    },
    {
        "title": "Secondary Cone Crusher Eccentric Bushing Clearance Inspection",
        "job_type": "INSPECTION",
        "maint_type": "MECHANICAL",
        "priority": 2,
        "est_hours": 7.0,
        "est_cost": 2800.0,
        "issue": "Elevated lubricating oil discharge temperature (>65°C) detected by SCADA RTD sensor.",
        "instruction": "Drain lube oil tank and inspect suction strainers for bronze filings. Remove bowl assembly and measure upper/lower eccentric bushing clearance with feeler gauge. Record backlash on spiral bevel gear."
    },
    {
        "title": "Main Pit Dewatering Submersible Pump Auto-Start Circuit Fault",
        "job_type": "EMERGENCY",
        "maint_type": "ELECTRICAL",
        "priority": 3,
        "est_hours": 4.5,
        "est_cost": 1850.0,
        "issue": "Bench 6 sump water level alarm triggered; telemetry relay failed to start pump 2.",
        "instruction": "Isolate 525V motor control center cubicle. Megger test cable to pit sump (minimum 10 Mohm). Check float switch 24V DC loop impedance and replace faulty auxiliary contact block on soft starter."
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
        print("[+] Starting Enterprise Faker Data Seeding...")

        # ── 1. Base Organization & Site ──
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

        # ── 3. Departments ──
        depts_data = [
            ("MECH", "Mechanical Engineering & Fixed Plant", "Mechanical overhaul, fixed crushing, conveyor belts, mills and mobile workshop maintenance."),
            ("ELEC", "Electrical & Instrumentation", "HV switchgear, 33kV substations, automation SCADA loops, and motor control centers."),
            ("MINE", "Open Cast Mining Operations", "Load and haul, blast hole drilling, overburden stripping, and mine pit operations."),
            ("PLANT", "Mineral Processing & DMS Plant", "Dense media separation, lithium flotation, comminution, and gravity concentration circuits."),
            ("HSE", "Health, Safety & Environment (HSE)", "Mine safety compliance, LOTO isolations, environmental tailings monitoring, and hazard control."),
            ("STORES", "Supply Chain & Materials Management", "Central warehouse spares inventory, ERP receiving, issuing, and vendor logistics."),
            ("GEO", "Geology, Geotech & Exploration", "Diamond core exploration drilling, ore body block modeling, grade control assays, and pit wall stability."),
            ("CIVIL", "Civil Works & Tailings Infrastructure", "Tailings dam structural integrity, haul road maintenance, earth bund construction, and stormwater drainage."),
            ("IT", "Information Technology & Digital Systems", "Telemetry networking, industrial IoT mesh, server infrastructure, and software management."),
            ("RELIABILITY", "Asset Integrity & Reliability Engineering", "Vibration thermography analysis, oil condition lab analysis, and RCM maintenance optimization.")
        ]
        
        depts_map = {}
        for d_code, d_name, d_desc in depts_data:
            res = await session.execute(select(Department).where(Department.name == d_name))
            dept = res.scalars().first()
            if not dept:
                dept = Department(
                    id=uuid.uuid4(),
                    site_id=site.id,
                    code=d_code,
                    name=d_name,
                    description=d_desc,
                    sla_hours_default=24,
                    is_active=True
                )
                session.add(dept)
                await session.commit()
                await session.refresh(dept)
            depts_map[d_code] = dept
            depts_map[d_name] = dept

        # Aliases for robust lookups
        depts_map["Mechanical"] = depts_map.get("MECH")
        depts_map["Electrical"] = depts_map.get("ELEC")
        depts_map["Mining"] = depts_map.get("MINE")
        depts_map["Plant"] = depts_map.get("PLANT")
        depts_map["HSE"] = depts_map.get("HSE")
        depts_map["Safety"] = depts_map.get("HSE")
        depts_map["Supply Chain"] = depts_map.get("SUPPLY")
        depts_map["Civil"] = depts_map.get("CIVIL")
        depts_map["ICT"] = depts_map.get("ICT")
        depts_map["Admin"] = depts_map.get("ADMIN")
        depts_map["Reliability"] = depts_map.get("RELIABILITY")

        # ── 4. Sections & Teams under Departments ──
        sections_data = [
            ("MECH", "SEC-MECH-FIX", "Fixed Plant Maintenance", "Crushing, screening, and milling maintenance"),
            ("MECH", "SEC-MECH-FLT", "Mobile Heavy Equipment Workshop", "Haul trucks, excavators, loaders, and auxiliary fleet"),
            ("ELEC", "SEC-ELEC-HV", "High Voltage & Substations", "33kV/11kV transformer yards and transmission"),
            ("ELEC", "SEC-ELEC-INST", "Instrumentation & Automation", "SCADA, PLC programming, level transmitters, and flowmeters"),
            ("MINE", "SEC-MINE-PROD", "Pit Production & Haulage", "Ore extraction Bench 4 to 6 and haulage cycles"),
            ("MINE", "SEC-MINE-DRILL", "Drilling & Blast Prep", "Pattern layout, blast hole drilling, and explosives handling"),
            ("PLANT", "SEC-PLANT-DMS", "DMS & Cyclone Circuit", "Heavy media separation, ferrosilicon recovery, and screen decks"),
            ("PLANT", "SEC-PLANT-FLOT", "Flotation & Dewatering", "Rougher/cleaner flotation cells, filter presses, and concentrate dryers"),
            ("HSE", "SEC-HSE-AUDIT", "Mine Safety & LOTO Audits", "Permit to work, isolation compliance, and PPE auditing"),
            ("STORES", "SEC-STORE-WARE", "Central Warehouse Stores", "Spare parts receiving, binning, picking, and dispatching")
        ]
        
        for dept_key, s_code, s_name, s_desc in sections_data:
            res = await session.execute(select(Section).where(Section.code == s_code))
            sec = res.scalars().first()
            if not sec:
                sec = Section(
                    id=uuid.uuid4(),
                    department_id=depts_map[dept_key].id,
                    code=s_code,
                    name=s_name,
                    description=s_desc,
                    is_active=True
                )
                session.add(sec)
                await session.commit()
                await session.refresh(sec)

        # ── 5. Users across Departments ──
        res = await session.execute(select(User))
        existing_users = {u.email: u for u in res.scalars().all()}

        roles_res = await session.execute(select(Role))
        roles_dict = {r.name: r for r in roles_res.scalars().all()}
        created_users = list(existing_users.values())

        core_accounts = [
            ("admin@bikita.com", "Admin", "User", "Administrator", "IT"),
            ("supervisor@bikita.com", "Tendai", "Shumba", "Supervisor", "MECH"),
            ("tech@bikita.com", "Farai", "Moyo", "Technician", "MECH"),
            ("operator@bikita.com", "Blessing", "Ncube", "Operator", "MINE"),
            ("safety@bikita.com", "Kudzai", "Dube", "Safety Officer", "HSE"),
            ("stores@bikita.com", "Tariro", "Mutasa", "Supervisor", "STORES"),
            ("elec.tech@bikita.com", "Simba", "Chimedza", "Technician", "ELEC"),
            ("plant.op@bikita.com", "Garikai", "Mudzimu", "Operator", "PLANT"),
            ("geo.lead@bikita.com", "Nyasha", "Marere", "Supervisor", "GEO"),
            ("civil.eng@bikita.com", "Tatenda", "Hove", "Supervisor", "CIVIL")
        ]

        for email, first, last, role_name, dept_key in core_accounts:
            if email not in existing_users:
                u = User(
                    id=uuid.uuid4(),
                    email=email,
                    first_name=first,
                    last_name=last,
                    hashed_password=get_password_hash("password123"),
                    department_id=depts_map[dept_key].id,
                    employee_number=f"EMP-{fake.numerify('####')}",
                    is_active=True,
                    is_superuser=(role_name == "Administrator")
                )
                session.add(u)
                await session.commit()
                await session.refresh(u)
                existing_users[email] = u
                created_users.append(u)
                if role_name in roles_dict:
                    session.add(UserRole(user_id=u.id, role_id=roles_dict[role_name].id))
                await session.commit()

        admin_user = existing_users["admin@bikita.com"]
        supervisor_user = existing_users.get("supervisor@bikita.com", admin_user)
        tech_user = existing_users.get("tech@bikita.com", admin_user)
        operator_user = existing_users.get("operator@bikita.com", admin_user)
        stores_user = existing_users.get("stores@bikita.com", admin_user)
        safety_user = existing_users.get("safety@bikita.com", admin_user)

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
                        capacity_rating=f"{random.randint(25, 200)} Tonnes" if "Truck" in item["type"] or "Excavator" in item["type"] else f"{random.randint(100, 600)} kW",
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
                    commissioned_date=now_utc() - timedelta(days=random.randint(200, 1800)),
                    specifications={"voltage": "33kV / 400V", "duty_cycle": "Continuous 24/7", "design_capacity_tph": random.randint(150, 600)}
                )
                session.add(ast)
                await session.commit()
                await session.refresh(ast)
            assets_list.append(ast)

        # ── 7. Materials & Spare Parts ──
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
        for c_data in CONTRACTORS_DATA:
            res = await session.execute(select(ContractorCompany).where(ContractorCompany.company_code == c_data["vendor_code"]))
            if not res.scalars().first():
                contractor = ContractorCompany(
                    id=uuid.uuid4(),
                    name=c_data["name"],
                    company_code=c_data["vendor_code"],
                    primary_contact_name=fake.name(),
                    contact_email=c_data["email"],
                    contact_phone=c_data["phone"],
                    service_categories=[c_data["service"]],
                    status=ContractorCompanyStatus.ACTIVE.value,
                    safety_induction_valid_until=now_utc() + timedelta(days=365),
                    notes="Approved mining services provider with valid mine safety clearance."
                )
                session.add(contractor)
                await session.commit()

        # ── 9. Workflows ──
        res = await session.execute(select(WorkflowDefinition))
        if not res.scalars().first():
            w_std = WorkflowDefinition(
                id=uuid.uuid4(),
                name="Standard Operational Approval",
                description="Default supervisor authorization workflow",
                priority=0
            )
            w_std_step = WorkflowStepDef(
                id=uuid.uuid4(),
                workflow_id=w_std.id,
                step_number=1,
                authority_role="SUPERVISOR",
                required_permission="job_card:approve"
            )
            session.add_all([w_std, w_std_step])
            await session.commit()

        # ── 10. Job Cards & Pending Approvals ──
        job_statuses = ["PENDING_APPROVAL", "PENDING_APPROVAL", "APPROVED", "IN_PROGRESS", "IN_PROGRESS", "COMPLETED", "VERIFIED", "CLOSED"]

        for idx, template in enumerate(JOB_TEMPLATES):
            job_num = f"JC-2026-{1000 + idx}"
            res = await session.execute(select(JobCard).where(JobCard.job_number == job_num))
            existing_jc = res.scalars().first()
            if not existing_jc:
                status = job_statuses[idx % len(job_statuses)]
                loc = random.choice(list(locations.values()))
                mach = random.choice(machines_list) if machines_list else None
                created_dt = now_utc() - timedelta(days=random.randint(1, 20), hours=random.randint(1, 23))

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
                    jc.action_taken = f"Completed full safe execution of {template['title']}. Torque checked and clearances aligned."
                    jc.completion_notes = "Tested under no-load and full-load. Operating parameters within nominal limits."

                if status in ["VERIFIED", "CLOSED"]:
                    jc.verified_at = created_dt + timedelta(hours=16)
                    jc.requester_confirmed = True
                    jc.closure_date = created_dt + timedelta(hours=20)
                    jc.closed_by_id = supervisor_user.id

                session.add(jc)
                await session.flush()

                labour_entry = JobCardLabour(
                    id=uuid.uuid4(),
                    job_card_id=jc.id,
                    technician_name=f"{tech_user.first_name} {tech_user.last_name}",
                    trade="Mechanical Fitter" if "MECHANICAL" in template["maint_type"] else "High Voltage Electrician",
                    hours_spent=round(random.uniform(4.0, 12.0), 1),
                    hourly_rate=45.0,
                    notes=f"Work order execution for {template['title']}."
                )
                session.add(labour_entry)

                if status == "PENDING_APPROVAL":
                    app_req = ApprovalRequest(
                        id=uuid.uuid4(),
                        resource_type="job_card",
                        resource_id=jc.id,
                        workflow_type="STANDARD",
                        priority=jc.priority,
                        risk_level="MEDIUM",
                        estimated_cost=jc.estimated_cost or 2500.0,
                        status="OPEN",
                        created_by_id=operator_user.id,
                        created_at=created_dt
                    )
                    session.add(app_req)
                    await session.flush()

                    app_step = ApprovalStep(
                        id=uuid.uuid4(),
                        approval_request_id=app_req.id,
                        step_number=1,
                        authority_role="SUPERVISOR",
                        required_permission="job_card:approve",
                        status="PENDING",
                        created_at=created_dt
                    )
                    session.add(app_step)

                await session.commit()

        # ── 10. Material Requirements (Cross-Departmental) ──
        mat_items_res = await session.execute(select(MaterialCatalogItem))
        catalog_list = mat_items_res.scalars().all()
        
        req_seed_data = [
            ("MAT-2026-101", "Heavy Duty Manganese Jaw Plates 18% Mn", "PRT-CRU-1001", "Crusher Spares", "set", 4200.0, 2.0, 2.0, 1.0, 1.0, 0.0, "PARTIALLY_ISSUED", "Heavy Spares Yard", "Primary Crusher Liners Overhaul", "MECH"),
            ("MAT-2026-102", "High Pressure Hydraulic Filter 10 Micron", "PRT-HYD-2045", "Hydraulics", "piece", 185.0, 4.0, 4.0, 4.0, 2.0, 0.0, "ISSUED", "Central Store A", "PC1250 Boom Cylinder Maintenance", "MECH"),
            ("MAT-2026-103", "Warman Slurry Pump Impeller High Chrome A05", "PRT-PMP-9012", "Pump Spares", "piece", 2100.0, 1.0, 1.0, 0.0, 0.0, 0.0, "APPROVED", "Heavy Spares Yard", "Bench 6 Sump Pump Overhaul", "MECH"),
            ("MAT-2026-104", "33kV Vacuum Circuit Breaker Vacuum Bottle", "PRT-ELEC-7015", "Electrical HV", "piece", 1450.0, 2.0, 2.0, 2.0, 2.0, 0.0, "CONSUMED", "Electrical Stores", "Main Substation Bay 2 Recloser Upgrade", "ELEC"),
            ("MAT-2026-105", "Mining Hard Hat & Visor with Lamp Bracket", "PRT-SAF-0030", "PPE & Safety", "piece", 45.0, 20.0, 20.0, 20.0, 18.0, 2.0, "RETURNED", "Safety Store", "Annual Safety Induction PPE Issue", "HSE"),
            ("MAT-2026-106", "EP500/4 Conveyor Belt Rubber 1200mm (Roll)", "PRT-BELT-4020", "Conveyor Components", "meter", 88.0, 50.0, 50.0, 50.0, 45.0, 5.0, "IN_USE", "Bulk Materials Yard", "DMS Overland Conveyor 03 Splicing", "PLANT"),
            ("MAT-2026-107", "PC1250 Bucket Teeth Tiger Point & Pin", "PRT-GET-3102", "Ground Engaging Tools", "piece", 310.0, 6.0, 6.0, 6.0, 6.0, 0.0, "CONSUMED", "Heavy Spares Yard", "Bench 5 Loading Shovel GET Replacement", "MINE"),
            ("MAT-2026-108", "15W40 Heavy Duty Diesel Engine Oil 200L Drum", "PRT-LUB-6010", "Lubricants & Oils", "drum", 540.0, 3.0, 0.0, 0.0, 0.0, 0.0, "REQUESTED", "Oils & Fluids Shed", "Haul Fleet Scheduled 500-Hour Oil Service", "MECH"),
            ("MAT-2026-109", "Timken Spherical Roller Bearing 22324 CC/W33", "PRT-BRG-5080", "Bearings & Transmission", "piece", 760.0, 2.0, 2.0, 1.0, 0.0, 0.0, "PARTIALLY_ISSUED", "Precision Stores", "Vibrating Screen Exciters Relining", "PLANT"),
            ("MAT-2026-110", "High Tensile M24 Track Bolts & Nuts Gr 10.9", "PRT-FST-8090", "Fasteners & Hardware", "box", 95.0, 5.0, 5.0, 5.0, 5.0, 0.0, "CONSUMED", "Central Store B", "Drill Rig Undercarriage Track Pad Fastening", "MINE"),
            ("MAT-2026-111", "High Pressure Knife Gate Valve DN200 PN25", "PRT-VLV-1120", "Valves & Piping", "piece", 1250.0, 2.0, 0.0, 0.0, 0.0, 0.0, "REQUESTED", "Heavy Spares Yard", "Tailings Storage Facility Slurry Line Isolation", "CIVIL"),
            ("MAT-2026-112", "WEG Mining Duty Electric Motor 75kW 4-Pole", "PRT-MOT-5500", "Motors & Drives", "piece", 5800.0, 1.0, 1.0, 0.0, 0.0, 0.0, "APPROVED", "Electrical Stores", "Flotation Bank Air Blower Standby Drive", "ELEC"),
        ]
        
        for req_num, m_name, p_num, cat, unit, cost, q_req, q_app, q_iss, q_use, q_ret, st, store, purp, dept_key in req_seed_data:
            res = await session.execute(select(MaterialRequirement).where(MaterialRequirement.requirement_number == req_num))
            if not res.scalars().first():
                cat_match = next((c for c in catalog_list if c.part_number == p_num), None)
                mat_req = MaterialRequirement(
                    id=uuid.uuid4(),
                    requirement_number=req_num,
                    catalog_item_id=cat_match.id if cat_match else None,
                    material_name=m_name,
                    part_number=p_num,
                    category=cat,
                    unit=unit,
                    unit_cost=cost,
                    quantity_required=q_req,
                    quantity_approved=q_app,
                    quantity_issued=q_iss,
                    quantity_used=q_use,
                    quantity_returned=q_ret,
                    status=st,
                    store_location=store,
                    purpose=purp,
                    department_id=depts_map[dept_key].id,
                    requester_id=tech_user.id,
                    approver_id=supervisor_user.id if q_app > 0 else None
                )
                session.add(mat_req)
        await session.commit()

        # ── 11. Work Items (Unified Work Hub / Kanban across all Departments) ──
        work_items_data = [
            ("WI-2026-101", "Primary Jaw Crusher Fixed Jaw Liner Overhaul", "JOB_CARD", "IN_PROGRESS", 3, "MECH", "LOC-CRU-01", "Farai Moyo (Lead Fitter)", 12.0, 5800.0),
            ("WI-2026-102", "Komatsu PC1250 Boom Cylinder Gland Seal Repack", "JOB_CARD", "ASSIGNED", 2, "MECH", "LOC-PIT-01", "Blessing Ncube (Hydraulics Artisan)", 8.5, 2400.0),
            ("WI-2026-103", "Main Substation Bay 2 33kV Dielectric Oil Test", "INSPECTION", "COMPLETED", 1, "ELEC", "LOC-SUB-33KV", "Simba Chimedza (HV Electrician)", 4.0, 950.0),
            ("WI-2026-104", "DMS Plant Conveyor 03 Belt Hot Splicing", "JOB_CARD", "IN_PROGRESS", 3, "PLANT", "LOC-DMS-01", "Tariro Mutasa (Rubber Tech)", 6.0, 3200.0),
            ("WI-2026-105", "Bench 6 Sump Telemetry Auto-Start Replacement", "JOB_CARD", "PENDING_APPROVAL", 3, "ELEC", "LOC-PIT-01", "Simba Chimedza (HV Electrician)", 4.5, 1850.0),
            ("WI-2026-106", "Tailings Dam Piezometer & Pore Pressure Survey", "INSPECTION", "DRAFT", 1, "CIVIL", "LOC-TSF-01", "Tatenda Hove (Civil Eng)", 3.0, 450.0),
            ("WI-2026-107", "Bench 5 Blast Pattern 115mm Hole Pre-split", "PLANNED_MAINTENANCE", "ASSIGNED", 2, "MINE", "LOC-PIT-01", "Blessing Ncube (Operator)", 10.0, 3400.0),
            ("WI-2026-108", "Central Warehouse Flammable Store LOTO Audit", "INSPECTION", "COMPLETED", 0, "HSE", "LOC-STR-CENTRAL", "Kudzai Dube (Safety Officer)", 2.0, 200.0),
            ("WI-2026-109", "Diamond Core Drill Rig DP1500i Mast Alignment", "JOB_CARD", "PENDING_APPROVAL", 2, "GEO", "LOC-PIT-01", "Nyasha Marere (Geo Lead)", 5.0, 1200.0),
            ("WI-2026-110", "Lithium Flotation Cells B-Bank Motor Thermography", "INSPECTION", "COMPLETED", 0, "RELIABILITY", "LOC-FLOT-01", "Garikai Mudzimu (Plant Op)", 2.5, 350.0),
        ]
        
        for w_ref, w_title, w_type, w_status, w_prio, dept_key, loc_key, w_assign, w_hrs, w_cost in work_items_data:
            res = await session.execute(select(WorkItem).where(WorkItem.reference_number == w_ref))
            if not res.scalars().first():
                loc_obj = locations.get(loc_key)
                wi = WorkItem(
                    id=uuid.uuid4(),
                    reference_number=w_ref,
                    title=w_title,
                    description=f"Enterprise operational task execution for {w_title}",
                    work_type=w_type,
                    status=w_status,
                    priority=w_prio,
                    department_id=depts_map[dept_key].id,
                    location_id=loc_obj.id if loc_obj else None,
                    location=loc_obj.name if loc_obj else None,
                    assigned_personnel=w_assign,
                    requester_id=operator_user.id,
                    supervisor_id=supervisor_user.id,
                    estimated_hours=w_hrs,
                    estimated_cost=w_cost,
                    due_date=now_utc() + timedelta(days=2),
                    sla_status="WITHIN_SLA" if w_prio < 3 else "AT_RISK"
                )
                session.add(wi)
        await session.commit()

        # ── 12. Operational Requests ──
        for i in range(10):
            req_num = f"REQ-2026-{2001 + i}"
            res = await session.execute(select(OperationalRequest).where(OperationalRequest.request_number == req_num))
            if not res.scalars().first():
                loc = random.choice(list(locations.values()))
                created_dt = now_utc() - timedelta(days=random.randint(1, 15))
                dept_keys = ["MINE", "MECH", "ELEC", "PLANT", "CIVIL", "GEO"]
                chosen_dept = depts_map[dept_keys[i % len(dept_keys)]]
                op_req = OperationalRequest(
                    id=uuid.uuid4(),
                    request_number=req_num,
                    title=f"Cross-Dept Spares & Machine Support for {loc.name}",
                    purpose=f"Operational supply and dispatch support for {loc.name}",
                    description=fake.paragraph(nb_sentences=2),
                    request_type=random.choice(["MACHINE_REQUEST", "EQUIPMENT_REQUEST", "MATERIAL_REQUEST"]),
                    status=random.choice(["SUBMITTED", "APPROVED", "FULFILLED"]),
                    fulfillment_status="FULFILLED",
                    priority=random.randint(1, 3),
                    department_id=chosen_dept.id,
                    requester_id=operator_user.id,
                    location_id=loc.id,
                    location=loc.name,
                    required_from=created_dt + timedelta(days=1),
                    required_to=created_dt + timedelta(days=3),
                    estimated_cost=round(random.uniform(800.0, 9500.0), 2)
                )
                session.add(op_req)
                await session.commit()

        # ── 12. Machine Requisitions with Approval Requests ──
        for i, mach in enumerate(machines_list[:6]):
            req_no = f"MREQ-2026-{3001 + i}"
            res = await session.execute(select(MachineRequisition).where(MachineRequisition.requisition_number == req_no))
            if not res.scalars().first():
                loc = random.choice(list(locations.values()))
                start_t = now_utc() + timedelta(days=random.randint(1, 4))
                end_t = start_t + timedelta(hours=12)
                req_status = "PENDING_APPROVAL" if i < 3 else "ALLOCATED"

                m_req = MachineRequisition(
                    id=uuid.uuid4(),
                    requisition_number=req_no,
                    department_id=depts_map["Mining"].id,
                    requester_id=operator_user.id,
                    purpose=f"Production ore load & transport cycle at {loc.name}",
                    machine_type_id=mach.machine_type_id,
                    machine_id=mach.id,
                    quantity=1,
                    location=loc.name,
                    location_id=loc.id,
                    start_time=start_t,
                    end_time=end_t,
                    estimated_duration_hours=12.0,
                    priority=2,
                    operator_required=True,
                    operator_name=f"{operator_user.first_name} {operator_user.last_name}",
                    status=req_status,
                    estimated_cost=mach.machine_type.hourly_rate * 12.0
                )
                session.add(m_req)
                await session.commit()
                await session.refresh(m_req)

                if req_status == "PENDING_APPROVAL":
                    m_app_req = ApprovalRequest(
                        id=uuid.uuid4(),
                        resource_type="machine_requisition",
                        resource_id=m_req.id,
                        workflow_type="STANDARD",
                        priority=m_req.priority,
                        risk_level="LOW",
                        estimated_cost=m_req.estimated_cost or 1500.0,
                        status="OPEN",
                        created_by_id=operator_user.id,
                        created_at=start_t
                    )
                    session.add(m_app_req)
                    await session.flush()

                    m_app_step = ApprovalStep(
                        id=uuid.uuid4(),
                        approval_request_id=m_app_req.id,
                        step_number=1,
                        authority_role="SUPERVISOR",
                        required_permission="job_card:approve",
                        status="PENDING",
                        created_at=start_t
                    )
                    session.add(m_app_step)
                    await session.commit()

        # ── 13. SLA Policies ──
        res = await session.execute(select(SLAPriorityConfig))
        if not res.scalars().first():
            p_configs = [
                SLAPriorityConfig(id=uuid.uuid4(), name="CRITICAL", display_name="Priority 3 - Critical Breakdown", default_response_minutes=15, default_completion_minutes=180, sort_order=10, color_code="#EF4444"),
                SLAPriorityConfig(id=uuid.uuid4(), name="HIGH", display_name="Priority 2 - High Urgent", default_response_minutes=30, default_completion_minutes=360, sort_order=20, color_code="#F59E0B"),
                SLAPriorityConfig(id=uuid.uuid4(), name="NORMAL", display_name="Priority 1 - Normal Shift", default_response_minutes=60, default_completion_minutes=720, sort_order=30, color_code="#3B82F6"),
                SLAPriorityConfig(id=uuid.uuid4(), name="LOW", display_name="Priority 0 - Low Routine", default_response_minutes=120, default_completion_minutes=1440, sort_order=40, color_code="#6B7280"),
            ]
            session.add_all(p_configs)
            await session.commit()

        # ── 14. Audit Logs ──
        audit_events = [
            ("LOGIN", "USER", str(admin_user.id), "System Administrator authenticated via console"),
            ("APPROVE", "JOB_CARD", "JC-2026-1002", "Supervisor authorized seal overhaul with digital stamp"),
            ("CREATE", "MACHINE_REQUISITION", "MREQ-2026-3001", "CAT 777D haulage requisition submitted"),
            ("STATUS_CHANGE", "JOB_CARD", "JC-2026-1001", "LOTO safety gate cleared by Lead Artisan"),
            ("DISPATCH", "MATERIAL", "PRT-CRU-1001", "Central warehouse issued jaw plates to Crusher Plant"),
        ]
        for act, res_t, res_id, reason in audit_events:
            audit = BusinessAuditLog(
                id=uuid.uuid4(),
                user_id=admin_user.id,
                user_name="Admin User",
                department_name="IT & Operations",
                role_names="System Administrator",
                action=act,
                resource=res_t,
                resource_id=res_id,
                reason=reason,
                ip_address="192.168.1.10"
            )
            session.add(audit)
        await session.commit()

        print("[OK] Enterprise Faker Seeding Completed Successfully!")

if __name__ == "__main__":
    asyncio.run(seed_faker_data())
