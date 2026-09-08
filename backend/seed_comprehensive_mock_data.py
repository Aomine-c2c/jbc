"""
Bikita Minerals DWRMS — Authoritative Mock Data Generation Engine (v2.9.0)
Uses Python Faker library to generate a comprehensive, ultra-realistic, diverse operational dataset
covering every functional domain, table, and user interface route of the system.
"""

import asyncio
import os
import random
import uuid
from datetime import datetime, timedelta, timezone
from faker import Faker
from sqlalchemy import select, text
from app.db.session import SessionLocal

# Import all domain models
from app.modules.iam.models import (
    Organization, Site, Location, Department, Section, Team, Position, User, Role, Permission, RolePermission, UserRole
)
from app.modules.jobs.models import (
    JobCard, JobCardPart, JobCardLabour, JobCardExecutionEvent, JobCardComment, JobCardAttachment, JobCardCollaborator
)
from app.modules.jobs.report_models import JobReport, JobReportProgressUpdate, JobReportMaterial
from app.modules.work.models import (
    WorkItem, WorkItemPart, WorkItemComment, WorkItemActionLog, WorkItemType, WorkItemStatus
)
from app.modules.fleet.models import (
    MachineType, Machine, MachineRequisition, MachineReservation, RequisitionActionLog
)
from app.modules.materials.models import (
    MaterialCatalogItem, MaterialRequirement, MaterialTransaction,
    MaterialRequirementStatus, MaterialTransactionType
)
from app.modules.assets.models import (
    Asset, AssetActivityLog, AssetMaintenanceRecord, AssetType, AssetStatus, AssetCriticality
)
from app.modules.contractors.models import (
    ContractorCompany, ContractorWorker, ContractorAssignment, ContractorWorkerAssignment,
    ContractorCompanyStatus, ContractorWorkerStatus, ContractorVerificationStatus
)
from app.modules.requests.models import (
    OperationalRequest, RequestMaterialItem, RequestActionLog, RequestComment,
    RequestType, RequestStatus, FulfillmentStatus
)
from app.modules.approvals.models import (
    ApprovalRequest, ApprovalStep, WorkflowDefinition, WorkflowStepDef
)
from app.modules.sla.models import (
    SLAPriorityConfig, SLAPolicy, SLATracker, SLAPriority, SLAStatus, SLAHealth
)
from app.modules.workflow.models import (
    WorkflowTemplate, WorkflowInstance, WorkflowTransitionLog, WorkflowEntityType
)
from app.modules.audit.models import BusinessAuditLog
from app.modules.notifications.models import Notification, NotificationRule
from app.modules.common.models import SMSMessage, AuditLog
from app.modules.dashboard.models import DashboardSavedView
from app.core.security import get_password_hash

fake = Faker()
Faker.seed(42)
random.seed(42)

# Operational constants tailored to Bikita Minerals Lithium Operations
BIKITA_LOCATIONS = [
    ("PIT-SOUTH", "Southern Open Pit Benches", "OPEN_PIT", "Mining Excavation Face B4-B7", "CRITICAL"),
    ("PIT-NORTH", "Northern Open Pit Extension", "OPEN_PIT", "Pegmatite Lithium Ore Body Ext", "CRITICAL"),
    ("CRUSH-PRIMARY", "Primary Jaw & Cone Crushing Circuit", "PROCESSING_PLANT", "Run-of-Mine feed conveyor hopper", "CRITICAL"),
    ("DMS-PLANT", "Dense Media Separation (DMS) Plant", "PROCESSING_PLANT", "Spodumene & Petalite heavy media cyclones", "CRITICAL"),
    ("FLOT-CIRCUIT", "Flotation Beneficiation Plant", "PROCESSING_PLANT", "Froth flotation cells and conditioner tanks", "HIGH"),
    ("TAILINGS-DAM", "Tailings Storage Facility (TSF-2)", "INFRASTRUCTURE", "Water reclaim pumps and slurry pipeline", "CRITICAL"),
    ("HEAVY-WORKSHOP", "Central Heavy Mobile Workshop", "WORKSHOP", "Bays 1 to 6 for CAT 777D & Komatsu PC1250", "HIGH"),
    ("LIGHT-WORKSHOP", "Light Vehicle Maintenance Depot", "WORKSHOP", "Hilux and Land Cruiser fleet service bays", "MEDIUM"),
    ("MAIN-SUBSTATION", "33kV / 11kV Central Substation", "SUBSTATION", "ZESA Grid feed transformers and switchgear", "CRITICAL"),
    ("SLURRY-PUMP-STN", "High-Pressure Slurry Pumping Station", "PUMP_STATION", "Warman 10/8 heavy slurry transfer pumps", "HIGH"),
    ("CENTRAL-STORES", "Main Engineering & Spares Warehouse", "WAREHOUSE", "Bins A1-D12 for mechanical & electrical inventory", "MEDIUM"),
    ("ASSAY-LAB", "Metallurgical Assay & Quality Control Lab", "LABORATORY", "XRF, AAS & ICP lithium assay analyzers", "HIGH"),
    ("ADMIN-BLOCK", "Mine Administration & Technical Services", "OFFICE", "Planning, survey, geology & IT server rooms", "LOW"),
    ("FUEL-DEPOT", "500,000L Bulk Diesel Fuel Farm", "DEPOT", "Fuel loading gantries and dispensing meters", "CRITICAL")
]

MINING_EQUIPMENT_CATALOG = [
    ("CAT-777D-01", "Caterpillar 777D Off-Highway Haul Truck", "CAT", "777D", "VEHICLE", "CRITICAL"),
    ("CAT-777D-02", "Caterpillar 777D Off-Highway Haul Truck", "CAT", "777D", "VEHICLE", "CRITICAL"),
    ("CAT-777D-03", "Caterpillar 777D Off-Highway Haul Truck", "CAT", "777D", "VEHICLE", "CRITICAL"),
    ("KOM-PC1250-01", "Komatsu PC1250-8R Heavy Mining Excavator", "Komatsu", "PC1250-8R", "MACHINE", "CRITICAL"),
    ("KOM-PC1250-02", "Komatsu PC1250-8R Heavy Mining Excavator", "Komatsu", "PC1250-8R", "MACHINE", "CRITICAL"),
    ("CAT-988H-01", "Caterpillar 988H Large Wheel Loader", "CAT", "988H", "MACHINE", "HIGH"),
    ("SANDVIK-DI550", "Sandvik Pantera DI550 Down-the-Hole Drill", "Sandvik", "DI550", "MACHINE", "CRITICAL"),
    ("EPIROC-D65", "Epiroc FlexiROC D65 Blast Hole Drill Rig", "Epiroc", "D65", "MACHINE", "CRITICAL"),
    ("METSO-C140", "Metso Superior Primary Jaw Crusher", "Metso Outotec", "C140", "PRODUCTION_EQUIPMENT", "CRITICAL"),
    ("TEREX-CONE-300", "Terex Cedarapids Secondary Cone Crusher", "Terex", "TC-300", "PRODUCTION_EQUIPMENT", "CRITICAL"),
    ("WARMAN-10-8", "Warman 10/8 Slurry Dewatering Pump 01", "Weir Minerals", "AH 10/8", "EQUIPMENT", "HIGH"),
    ("WARMAN-10-8-B", "Warman 10/8 Slurry Dewatering Pump 02", "Weir Minerals", "AH 10/8", "EQUIPMENT", "HIGH"),
    ("CAT-16M-01", "Caterpillar 16M Haul Road Motor Grader", "CAT", "16M", "MACHINE", "MEDIUM"),
    ("CAT-D9R-01", "Caterpillar D9R Heavy Track Dozer", "CAT", "D9R", "MACHINE", "HIGH"),
    ("VOLVO-FMX-01", "Volvo FMX 440 20kL Water Bowser", "Volvo", "FMX-440", "VEHICLE", "MEDIUM"),
    ("SCANIA-R500-01", "Scania R500 Flatbed Heavy Spares Carrier", "Scania", "R500", "VEHICLE", "MEDIUM"),
    ("LIEB-LTM1100", "Liebherr LTM 1100-4.2 Mobile All-Terrain Crane", "Liebherr", "LTM-1100", "MACHINE", "HIGH"),
    ("TOY-HILUX-01", "Toyota Hilux 2.8GD6 4x4 Field Inspection Utility", "Toyota", "Hilux 4x4", "VEHICLE", "LOW"),
    ("TOY-HILUX-02", "Toyota Hilux 2.8GD6 4x4 Electrical Emergency Van", "Toyota", "Hilux 4x4", "VEHICLE", "LOW"),
    ("CUMMINS-1250", "Cummins 1250kVA Prime Power Standby Generator", "Cummins", "QSK50-G4", "EQUIPMENT", "CRITICAL")
]

SPARE_PARTS_MASTER = [
    ("HYD-PUMP-CAT777", "Hydraulic Main Piston Pump Assembly", "Hydraulics", "units", 4250.00, "Central Engineering Spares"),
    ("FILTER-OIL-LF9009", "Heavy Duty Lube Oil Filter Element", "Filters", "units", 38.50, "Central Engineering Spares"),
    ("FILTER-AIR-AF25125", "High Capacity Primary Air Filter", "Filters", "units", 82.00, "Central Engineering Spares"),
    ("JAW-PLATE-MN18", "Metso C140 Manganese Jaw Die Plate (Fixed)", "Wear Liners", "units", 11800.00, "Heavy Workshop Yard"),
    ("CONE-MANTLE-MP800", "High-Carbon Concave & Mantle Set", "Wear Liners", "sets", 14500.00, "Heavy Workshop Yard"),
    ("CONVEYOR-BELT-EP800", "Heavy Duty Conveyor Belt EP800/4 1200mm", "Conveyor Belts", "meters", 125.00, "Central Engineering Spares"),
    ("SLURRY-IMPELLER-AH", "Warman 10/8 High-Chrome Slurry Impeller", "Pumps", "units", 2350.00, "Central Engineering Spares"),
    ("BEARING-SKF-22328", "SKF Spherical Roller Bearing 22328 CC/W33", "Bearings", "units", 680.00, "Central Engineering Spares"),
    ("V-BELT-SPC-4000", "Heavy Industrial Wedge V-Belt Set", "Transmission", "sets", 115.00, "Central Engineering Spares"),
    ("GREASE-EP2-180KG", "Mobilgrease XHP 222 Mine Drum 180kg", "Lubricants", "drums", 890.00, "Bulk Lubricant Bay"),
    ("HYD-HOSE-2WIRE-1IN", "Gates MegaSys 2-Wire Hydraulic Hose 1\"", "Hydraulics", "meters", 24.50, "Hose Fabrication Bay"),
    ("DRILL-STEEL-T51", "Sandvik 3660mm T51 Round MF Drill Rod", "Drilling Consumables", "units", 310.00, "Drill Tool Store"),
    ("DRILL-BIT-115MM", "Retrac Ballistic Carbide Drill Bit 115mm", "Drilling Consumables", "units", 245.00, "Drill Tool Store"),
    ("SOLENOID-VALVE-24V", "Parker 24VDC 4-Way Directional Solenoid Valve", "Automation", "units", 410.00, "Instrumentation Lab"),
    ("PRESSURE-XMTR-420", "Endress+Hauser Cerabar Pressure Transmitter", "Instrumentation", "units", 950.00, "Instrumentation Lab"),
    ("CONTACTOR-ABB-110KW", "ABB AF265-30 Heavy Motor Contactor 110kW", "Electrical Switchgear", "units", 1420.00, "Electrical Stores"),
    ("BREAKER-SCHNEIDER-630", "Schneider Compact NSX630F 630A MCCB", "Electrical Switchgear", "units", 1850.00, "Electrical Stores"),
    ("WELDING-ROD-LH-5KG", "Afrox E7018-1 Low Hydrogen Electrodes 5kg", "Consumables", "packs", 45.00, "Welding Bay"),
    ("OXYGEN-GAS-CYL", "Industrial Compressed Oxygen Cylinder 48L", "Gases", "cylinders", 62.00, "Gas Storage Compound"),
    ("ACETYLENE-GAS-CYL", "Dissolved Acetylene Cylinder 40L", "Gases", "cylinders", 84.00, "Gas Storage Compound")
]

EXTERNAL_CONTRACTORS_SEED = [
    ("CONT-BARMINCO", "Barminco Mining Services Africa", "Underground Drilling & Blasting", "Reg-ZW-88412", "contact@barminco.co.zw"),
    ("CONT-DRA", "DRA Global Engineering & Projects", "Mineral Processing & EPC", "Reg-ZW-40192", "info@draglobal.com"),
    ("CONT-BABCOCK", "Babcock Equipment Services Ltd", "CAT & Komatsu Fleet Overhaul", "Reg-ZW-11934", "service@babcock.co.zw"),
    ("CONT-WEIR", "Weir Minerals Slurry Services", "Slurry Pumping & Mill Linings", "Reg-ZW-99214", "support@weirminerals.co.zw"),
    ("CONT-ZESA-CON", "ZESA National Grid Power Contractors", "HV Line Maintenance & Transformers", "Reg-ZW-77123", "hvlines@zesa.co.zw"),
    ("CONT-BARRICK-CIVIL", "Masvingo Industrial Civil Works", "Tailings Dam Earthworks & Concrete", "Reg-ZW-33418", "admin@masvingocivil.co.zw")
]

JOB_CARD_SCENARIOS = [
    ("CAT 777D #01 Transmission Pressure Drop & Torque Converter Overheat", "MECHANICAL", "HIGH", "Replaced charge pump relief valve, flushed torque converter cooler lines, and refilled with SAE 30 TO-4 fluid.", "COMPLETED"),
    ("Komatsu PC1250 Excavator Boom Cylinder Rod Seal Blown", "MECHANICAL", "CRITICAL", "Isolated boom hydraulic lock, removed 240mm cylinder head gland, replaced chevron packing set, and pressure-tested to 320 bar.", "CLOSED"),
    ("Metso C140 Jaw Crusher Toggle Plate Fracture & Sensor Fault", "MECHANICAL", "CRITICAL", "Installed replacement cast-iron toggle plate, recalibrated toggle seat proximity sensor, verified CSS discharge to 120mm.", "VERIFIED"),
    ("Secondary Cone Crusher Lubrication Pump Low Flow Trip", "MECHANICAL", "HIGH", "Cleaned dual basket suction strainers, purged air from suction manifold, verified lube pressure at 4.2 bar.", "APPROVED"),
    ("Primary Feed Conveyor CV-01 Belt Ripped - 15 Meter Splicing", "MECHANICAL", "CRITICAL", "Cold vulcanized 15m longitudinal belt slice using ContiTech repair strips and EP800 reinforcement ply.", "IN_PROGRESS"),
    ("TSF-2 Slurry Transfer Pump Warman 10/8 Gland Seal Failure", "MECHANICAL", "HIGH", "Repacked gland packing with PTFE-graphite rings, adjusted lantern ring flush water supply to 6 bar.", "PLANNING"),
    ("High Voltage 33kV Intake Feeder 2 SF6 Circuit Breaker Trip", "ELECTRICAL", "CRITICAL", "Investigated overcurrent earth fault on overhead feeder 2. Cleared tree limb contact and tested protection relays.", "CLOSED"),
    ("Ball Mill 01 1200kW Synchronous Motor Slip Ring Flashover", "ELECTRICAL", "CRITICAL", "Cleaned carbon dust from slip ring assembly, stone-honed copper rings, fitted new grade EG236 brushes.", "COMPLETED"),
    ("Crusher MCC Panel 4 Overload Relay Intermittent Tripping", "ELECTRICAL", "NORMAL", "Thermal imaged busbar connections, retorqued terminal bolts, recalibrated electronic overload trip curve.", "IN_PROGRESS"),
    ("DMS Plant Cyclone Pressure Transmitter 4-20mA Calibration", "INSTRUMENTATION", "NORMAL", "Zero and span calibrated Endress+Hauser pressure sensor using Hart 475 field communicator.", "COMPLETED"),
    ("Flotation Cell Air Mass Flow Controller Signal Dropout", "INSTRUMENTATION", "NORMAL", "Re-terminated shielded signal cable at junction box JB-FLOT-04, verified Modbus TCP packet reception in SCADA.", "VERIFIED"),
    ("Tailings Dam Ultrasonic Slurry Level Monitor Zero Drift", "INSTRUMENTATION", "HIGH", "Cleaned transducer acoustic face, verified reference offset against laser gauge survey benchmark.", "SUBMITTED"),
    ("Open Pit Haul Road Dust Suppression Water Bowser Brake Overhaul", "MECHANICAL", "NORMAL", "Relined drive axle S-cam brake shoes, replaced ruptured booster diaphragm, road-tested deceleration.", "IN_PROGRESS"),
    ("Surface Core Drill Rig Sandvik DI550 Mast Cable Snapped", "MECHANICAL", "HIGH", "Rigged new 19mm non-rotating hoist wire rope, calibrated load limiter sensor, signed off lifting certificate.", "PENDING_APPROVAL"),
    ("Central Mine Office Server Room Inrow Precision AC Trip", "IT_SYSTEMS", "HIGH", "Cleared high discharge pressure fault, chemically washed outdoor condenser coils, stabilized temperature to 19°C.", "COMPLETED")
]

async def seed_comprehensive_mock_data():
    async with SessionLocal() as session:
        print("\n==================================================================")
        print("  BIKITA MINERALS DWRMS - ENTERPRISE MOCK DATA GENERATION CORE   ")
        print("==================================================================")

        # 1. Fetch Baseline Infrastructure
        res_org = await session.execute(select(Organization).limit(1))
        org = res_org.scalar_one_or_none()
        if not org:
            org = Organization(code="BIK", name="Bikita Minerals Ltd", industry_type="Lithium Mining & Processing")
            session.add(org)
            await session.commit()
            await session.refresh(org)

        res_site = await session.execute(select(Site).limit(1))
        site = res_site.scalar_one_or_none()
        if not site:
            site = Site(organization_id=org.id, code="MSV-1", name="Bikita Lithium Mine Site", site_type="MINE_SITE")
            session.add(site)
            await session.commit()
            await session.refresh(site)

        # 2. Fetch / Seed Departments
        dept_names = [
            ("MECH", "Mechanical Engineering & Maintenance", "Heavy and fixed plant mechanical maintenance"),
            ("ELEC", "Electrical Engineering & HV", "High voltage switchgear, distribution and electric drives"),
            ("INST", "Instrumentation & Control", "SCADA, telemetry, field instrumentation and process control"),
            ("MINING", "Open Pit Mining Operations", "Blasting, excavation, load and haul heavy fleet management"),
            ("PLANT", "Processing & Beneficiation Plant", "Crushing, DMS, flotation and lithium concentrate production"),
            ("SAFETY", "Health, Safety & Environment (HSE)", "Mining regulations compliance, LOTO, and risk auditing"),
            ("STORES", "Supply Chain & Materials Management", "Central engineering stores, parts inventory and procurement"),
            ("IT", "Information Technology & Digital Systems", "Platform administration, mine LAN/WAN, and operational tech")
        ]
        departments_map = {}
        for code, name, desc in dept_names:
            q = await session.execute(select(Department).where(Department.name == name))
            d = q.scalar_one_or_none()
            if not d:
                d = Department(site_id=site.id, code=code, name=name, description=desc, sla_hours_default=24)
                session.add(d)
                await session.commit()
                await session.refresh(d)
            departments_map[code] = d

        # 3. Seed Physical Locations (GIS & Hierarchical spatial nodes)
        print(" • Seeding hierarchical GIS locations & mine plant sectors...")
        locations_list = []
        for code, name, loc_type, desc, crit in BIKITA_LOCATIONS:
            q = await session.execute(select(Location).where(Location.code == code))
            loc = q.scalar_one_or_none()
            if not loc:
                loc = Location(
                    organization_id=org.id,
                    site_id=site.id,
                    code=code,
                    name=name,
                    location_type=loc_type,
                    description=desc,
                    criticality_rating=crit,
                    gps_coordinates=f"-20.08{random.randint(10, 99)}, 31.95{random.randint(10, 99)}",
                    barcode_or_nfc=f"LOC-NFC-{code}",
                    breadcrumb=f"Bikita Mine > {site.name} > {name}"
                )
                session.add(loc)
                await session.commit()
                await session.refresh(loc)
            locations_list.append(loc)

        # 4. Fetch Users and Create Additional Realistic Staff Personas
        print(" • Enriching personnel profiles and technical artisan teams...")
        existing_users_res = await session.execute(select(User))
        all_users = list(existing_users_res.scalars().all())
        user_by_email = {u.email: u for u in all_users}

        default_pw = get_password_hash("password123")
        tech_roles = ["Senior Mechanical Fitter", "HV Electrician", "Instrumentation Tech", "Heavy Equipment Operator", "Rigging Specialist"]
        
        while len(all_users) < 35:
            first_name = fake.first_name()
            last_name = fake.last_name()
            email = f"{first_name.lower()}.{last_name.lower()}@bikita.com"
            if email in user_by_email:
                continue
            dept = random.choice(list(departments_map.values()))
            loc = random.choice(locations_list)
            u = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                hashed_password=default_pw,
                department_id=dept.id,
                location_id=loc.id,
                site_id=site.id,
                employee_number=f"EMP-{random.randint(2000, 9999)}",
                phone_number=f"+26377{random.randint(1000000, 9999999)}",
                shift_pattern=random.choice(["DAY_SHIFT", "NIGHT_SHIFT", "CALLOUT_ROSTER"]),
                is_active=True,
                is_superuser=False
            )
            session.add(u)
            await session.commit()
            await session.refresh(u)
            all_users.append(u)
            user_by_email[email] = u

        # Ensure core role mapping
        res_roles = await session.execute(select(Role))
        role_objs = {r.name: r for r in res_roles.scalars().all()}
        
        # 5. Seed Contractor Companies and External Workforce
        print(" • Seeding specialized mining contractors and certified artisan workers...")
        contractors_list = []
        for code, name, service, reg, email in EXTERNAL_CONTRACTORS_SEED:
            q = await session.execute(select(ContractorCompany).where(ContractorCompany.company_code == code))
            comp = q.scalar_one_or_none()
            if not comp:
                comp = ContractorCompany(
                    company_code=code,
                    name=name,
                    registration_number=reg,
                    primary_contact_name=fake.name(),
                    contact_email=email,
                    contact_phone=f"+26371{random.randint(1000000, 9999999)}",
                    service_categories=[service, "Heavy Mining Infrastructure"],
                    status=ContractorCompanyStatus.ACTIVE.value,
                    safety_induction_valid_until=datetime.now(timezone.utc) + timedelta(days=random.randint(90, 365)),
                    notes=f"Tier-1 Approved Mining Contractor for {service}"
                )
                session.add(comp)
                await session.commit()
                await session.refresh(comp)
            contractors_list.append(comp)

        # Seed Contractor Workers
        for comp in contractors_list:
            res_w = await session.execute(select(ContractorWorker).where(ContractorWorker.contractor_company_id == comp.id))
            workers = res_w.scalars().all()
            if len(workers) < 3:
                for i in range(3):
                    w = ContractorWorker(
                        contractor_company_id=comp.id,
                        worker_code=f"CW-{comp.company_code[-4:]}-{i+1:02d}",
                        full_name=fake.name(),
                        skill_or_role=random.choice(tech_roles),
                        status=ContractorWorkerStatus.ACTIVE.value,
                        phone_number=f"+26377{random.randint(1000000, 9999999)}",
                        badge_number=f"BADGE-EXT-{random.randint(100, 999)}",
                        certification_records=[
                            {"cert": "Mine Safety & Environmental Induction", "valid": True},
                            {"cert": "High-Voltage Isolation / Rigging", "valid": True}
                        ],
                        certification_expiry=datetime.now(timezone.utc) + timedelta(days=random.randint(60, 300))
                    )
                    session.add(w)
                await session.commit()

        # 6. Seed Materials & Spare Parts Catalog (Warehouse Master)
        print(" • Seeding warehouse spares catalog and material inventory...")
        catalog_items = []
        for pnum, name, cat, uom, cost, store in SPARE_PARTS_MASTER:
            q = await session.execute(select(MaterialCatalogItem).where(MaterialCatalogItem.part_number == pnum))
            item = q.scalar_one_or_none()
            if not item:
                item = MaterialCatalogItem(
                    part_number=pnum,
                    name=name,
                    description=f"OEM certified {name} specification for high-throughput lithium plant operations",
                    category=cat,
                    unit_of_measure=uom,
                    default_unit_cost=cost,
                    primary_store=store,
                    is_active=True
                )
                session.add(item)
                await session.commit()
                await session.refresh(item)
            catalog_items.append(item)

        # 7. Seed Physical Fleet & Capital Assets
        print(" • Seeding mobile machinery fleet, telemetry meters, and capital assets...")
        res_mtypes = await session.execute(select(MachineType))
        mtypes = list(res_mtypes.scalars().all())
        
        assets_list = []
        machines_list = []
        for tag, name, mfg, model, atype, crit in MINING_EQUIPMENT_CATALOG:
            q = await session.execute(select(Asset).where(Asset.asset_tag == tag))
            ast = q.scalar_one_or_none()
            dept = departments_map["MECH"] if "CAT" in tag or "KOM" in tag else departments_map["PLANT"]
            loc = random.choice(locations_list)
            custodian = random.choice(all_users)
            
            if not ast:
                ast = Asset(
                    asset_tag=tag,
                    name=name,
                    asset_type=atype,
                    category="Heavy Mining Fleet" if atype == "VEHICLE" else "Process Beneficiation",
                    manufacturer=mfg,
                    model_number=model,
                    serial_number=f"SN-{mfg[:3]}-{random.randint(100000, 999999)}",
                    department_id=dept.id,
                    custodian_id=custodian.id,
                    location_id=loc.id,
                    location=loc.name,
                    status=random.choice([AssetStatus.AVAILABLE.value, AssetStatus.IN_USE.value, AssetStatus.UNDER_MAINTENANCE.value]),
                    criticality=crit,
                    commissioned_date=datetime.now(timezone.utc) - timedelta(days=random.randint(200, 1800)),
                    purchase_cost=random.uniform(75000.0, 1250000.0),
                    current_value=random.uniform(50000.0, 950000.0),
                    barcode_or_nfc=f"NFC-AST-{tag}"
                )
                session.add(ast)
                await session.commit()
                await session.refresh(ast)
            assets_list.append(ast)

            # Link into Machine registry
            qm = await session.execute(select(Machine).where(Machine.identifier == tag))
            mac = qm.scalar_one_or_none()
            if not mac and mtypes:
                mtype = random.choice(mtypes)
                mac = Machine(
                    machine_type_id=mtype.id,
                    identifier=tag,
                    serial_number=ast.serial_number,
                    status=random.choice(["AVAILABLE", "IN_USE", "UNDER_MAINTENANCE", "ALLOCATED"]),
                    location=loc.name,
                    location_id=loc.id,
                    asset_id=ast.id,
                    capacity_rating="Full Payload" if atype == "VEHICLE" else "Heavy Duty Continuous",
                    current_hour_meter=random.uniform(1250.0, 18450.0),
                    last_maintenance_date=datetime.now(timezone.utc) - timedelta(days=random.randint(5, 60))
                )
                session.add(mac)
                await session.commit()
                await session.refresh(mac)
            if mac:
                machines_list.append(mac)

        # 8. Seed Configurable Workflows (Workflow Engine)
        print(" • Seeding automated multi-tier workflow state machines...")
        res_wf = await session.execute(select(WorkflowTemplate))
        existing_wfs = res_wf.scalars().all()
        if not existing_wfs:
            std_states = [
                {"name": "DRAFT", "label": "Draft Work Order", "is_initial": True, "is_terminal": False},
                {"name": "PENDING_APPROVAL", "label": "Superintendent Sign-off", "requires_approval": True, "approval_role": "Department Manager", "sla_minutes": 120},
                {"name": "ASSIGNED", "label": "Crew Dispatched", "is_terminal": False},
                {"name": "IN_PROGRESS", "label": "Artisan In Execution", "is_terminal": False},
                {"name": "QA_VERIFICATION", "label": "Supervisor QA Inspection", "requires_approval": True, "approval_role": "Supervisor", "sla_minutes": 60},
                {"name": "CLOSED", "label": "Officially Closed & Costed", "is_terminal": True}
            ]
            std_transitions = [
                {"from_state": "DRAFT", "to_state": "PENDING_APPROVAL", "action": "submit", "label": "Submit for Authorization"},
                {"from_state": "PENDING_APPROVAL", "to_state": "ASSIGNED", "action": "approve", "label": "Approve Requisition", "required_role": "Department Manager"},
                {"from_state": "ASSIGNED", "to_state": "IN_PROGRESS", "action": "start", "label": "Commence Physical Work"},
                {"from_state": "IN_PROGRESS", "to_state": "QA_VERIFICATION", "action": "complete", "label": "Mark Mechanical Work Complete"},
                {"from_state": "QA_VERIFICATION", "to_state": "CLOSED", "action": "verify", "label": "Pass QA & Seal Job Card", "required_role": "Supervisor"}
            ]
            
            wf_template = WorkflowTemplate(
                name="Bikita Enterprise Heavy Work Order Workflow",
                description="Standard multi-tiered operational lifecycle for plant maintenance and breakdown remediation",
                entity_type=WorkflowEntityType.JOB_CARD.value,
                version=1,
                is_active=True,
                is_default=True,
                states=std_states,
                transitions=std_transitions
            )
            session.add(wf_template)
            await session.commit()

        # 9. Seed SLA Policies and Live SLA Trackers
        print(" • Seeding SLA policies, escalation ladders, and live countdown trackers...")
        res_pol = await session.execute(select(SLAPolicy))
        existing_pols = res_pol.scalars().all()
        if not existing_pols:
            p1 = SLAPolicy(
                name="Pit & Plant Emergency Breakdown SLA",
                description="Target response < 30 mins, completion < 4 hours for Tier-1 mining stoppages",
                priority="CRITICAL",
                response_time_minutes=30,
                completion_time_minutes=240,
                warning_threshold_percentage=75,
                escalation_rules=[
                    {"level": 1, "trigger": "RESPONSE_WARNING", "after_percentage": 75, "target_role": "Supervisor"},
                    {"level": 2, "trigger": "RESPONSE_BREACH", "after_percentage": 100, "target_role": "Department Manager"},
                    {"level": 3, "trigger": "COMPLETION_BREACH", "after_percentage": 100, "target_role": "Plant_Manager"}
                ],
                is_active=True,
                is_default=True
            )
            p2 = SLAPolicy(
                name="Standard Preventive Maintenance SLA",
                description="Shift-level maintenance operations response < 2 hrs, turnaround < 24 hrs",
                priority="NORMAL",
                response_time_minutes=120,
                completion_time_minutes=1440,
                warning_threshold_percentage=80,
                is_active=True,
                is_default=False
            )
            session.add_all([p1, p2])
            await session.commit()

        # 10. Seed Diverse Job Cards, Work Packages, and Execution Reports
        print(" • Seeding realistic Job Cards across all lifecycle phases...")
        admin_user = user_by_email.get("admin@bikita.com", all_users[0])
        tech_user = user_by_email.get("tech@bikita.com", all_users[1])
        sup_user = user_by_email.get("supervisor@bikita.com", all_users[2])
        mgr_user = user_by_email.get("mechmgr@bikita.com", all_users[0])

        for idx, (title, dept_code, prio_name, action_notes, status) in enumerate(JOB_CARD_SCENARIOS):
            job_num = f"JC-2026-{2000 + idx}"
            q = await session.execute(select(JobCard).where(JobCard.job_number == job_num))
            if q.scalar_one_or_none():
                continue
            
            prio_int = 3 if prio_name == "CRITICAL" else (2 if prio_name == "HIGH" else 1)
            dept = departments_map.get(dept_code, departments_map["MECH"])
            loc = random.choice(locations_list)
            mac = random.choice(machines_list) if machines_list else None

            created_time = datetime.now(timezone.utc) - timedelta(days=random.randint(1, 14), hours=random.randint(1, 23))
            start_time = created_time + timedelta(minutes=random.randint(20, 120)) if status in ["IN_PROGRESS", "COMPLETED", "VERIFIED", "CLOSED"] else None
            end_time = start_time + timedelta(hours=random.randint(2, 8)) if status in ["COMPLETED", "VERIFIED", "CLOSED"] else None

            jc = JobCard(
                job_number=job_num,
                title=title,
                description=f"Detailed engineering breakdown notice on {loc.name}. Immediate artisan intervention required.",
                status=status,
                priority=prio_int,
                department_id=dept.id,
                requesting_department_id=departments_map["MINING"].id,
                responsible_department_id=dept.id,
                location=loc.name,
                location_id=loc.id,
                machine_id=mac.id if mac else None,
                creator_id=admin_user.id,
                required_date=created_time + timedelta(days=1),
                job_type="UNSCHEDULED_BREAKDOWN" if prio_name == "CRITICAL" else "PREVENTIVE_MAINTENANCE",
                reported_issue=title,
                job_instruction="Perform comprehensive dynamic pressure check, isolate electrical drive, and verify LOTO safety lock.",
                supervisor_id=sup_user.id,
                assigned_date=created_time + timedelta(minutes=30),
                assigned_personnel=tech_user.first_name + " " + tech_user.last_name,
                estimated_hours=random.uniform(2.0, 10.0),
                estimated_cost=random.uniform(250.0, 8500.0),
                actual_start_time=start_time,
                actual_end_time=end_time,
                downtime_hours=random.uniform(1.5, 6.0) if end_time else 0.0,
                action_taken=action_notes if status in ["COMPLETED", "VERIFIED", "CLOSED"] else None,
                completion_notes="Work completed strictly under Bikita Minerals mining safety procedures." if end_time else None,
                safety_cleared=True if prio_name == "CRITICAL" else False,
                safety_cleared_at=start_time if prio_name == "CRITICAL" else None,
                loto_tag_number=f"LOTO-2026-{random.randint(1000, 9999)}" if prio_name == "CRITICAL" else None
            )
            session.add(jc)
            await session.commit()
            await session.refresh(jc)

            # Add Job Card Parts
            for part_item in random.sample(catalog_items, k=min(2, len(catalog_items))):
                qty = float(random.randint(1, 4))
                session.add(JobCardPart(
                    job_card_id=jc.id,
                    part_name=part_item.name,
                    part_number=part_item.part_number,
                    quantity=qty,
                    unit_cost=part_item.default_unit_cost,
                    is_material=False
                ))

            # Add Labour Entries
            session.add(JobCardLabour(
                job_card_id=jc.id,
                technician_name=f"{tech_user.first_name} {tech_user.last_name}",
                trade="Lead Mechanical Artisan",
                hours_spent=random.uniform(2.5, 8.0),
                hourly_rate=35.0,
                notes="Shift execution including LOTO permit verification and final run-testing"
            ))

            # Add Execution Events
            session.add(JobCardExecutionEvent(
                job_card_id=jc.id,
                event_type="STARTED",
                timestamp=created_time + timedelta(minutes=20),
                duration_minutes=120.0,
                operator_name=f"{tech_user.first_name} {tech_user.last_name}",
                reason="Work commenced after safety clearance"
            ))

            # Add 1:1 JobReport
            if status in ["IN_PROGRESS", "COMPLETED", "VERIFIED", "CLOSED"]:
                session.add(JobReport(
                    job_card_id=jc.id,
                    is_locked=True if status == "CLOSED" else False,
                    fault_found=f"Abnormal vibration and diagnostic trip observed on {jc.title}",
                    fault_code=f"ERR-{random.randint(100, 999)}",
                    corrective_action=action_notes,
                    technical_notes="Cleaned and overhauled components in compliance with mining engineering standard operating procedures.",
                    observations="All operating parameters normalized post-service.",
                    recommendations="Inspect again during next scheduled 250-hour service interval.",
                    actual_labour_hours=random.uniform(2.5, 6.0),
                    actual_cost=random.uniform(300.0, 4500.0),
                    dept_schema_type="MECHANICAL" if dept_code == "MECH" else ("ELECTRICAL" if dept_code == "ELEC" else "GENERIC")
                ))

            # Add Live SLA Tracker
            session.add(SLATracker(
                resource_type="JOB_CARD",
                resource_id=jc.id,
                resource_reference=jc.job_number,
                title=jc.title,
                priority=prio_name,
                department_id=dept.id,
                location_id=loc.id,
                status=SLAStatus.COMPLETED.value if status in ["COMPLETED", "VERIFIED", "CLOSED"] else SLAStatus.IN_PROGRESS.value,
                health=SLAHealth.ON_TRACK.value if random.random() > 0.2 else SLAHealth.AT_RISK.value,
                target_response_at=created_time + timedelta(minutes=45),
                target_completion_at=created_time + timedelta(hours=6),
                actual_response_at=start_time,
                actual_completion_at=end_time
            ))

        await session.commit()

        # 11. Seed Universal Operational Requests
        print(" • Seeding universal requisitions for equipment, personnel, and warehouse stock...")
        for req_idx in range(15):
            req_num = f"REQ-2026-{4000 + req_idx}"
            q = await session.execute(select(OperationalRequest).where(OperationalRequest.request_number == req_num))
            if q.scalar_one_or_none():
                continue

            rtype = random.choice([RequestType.MACHINE_REQUEST.value, RequestType.MATERIAL_REQUEST.value, RequestType.CONTRACTOR_REQUEST.value])
            rstatus = random.choice([RequestStatus.APPROVED.value, RequestStatus.UNDER_REVIEW.value, RequestStatus.AWAITING_FULFILLMENT.value, RequestStatus.FULFILLED.value])
            requester = random.choice(all_users)
            dept = random.choice(list(departments_map.values()))
            loc = random.choice(locations_list)

            op_req = OperationalRequest(
                request_number=req_num,
                request_type=rtype,
                title=f"Shift Request: {fake.bs().title()}",
                purpose=f"Critical operational deployment for {loc.name} to sustain 24/7 ore throughput.",
                description=f"Authorized requisition under department code {dept.code}.",
                priority=random.randint(1, 3),
                status=rstatus,
                fulfillment_status=FulfillmentStatus.FULFILLED.value if rstatus == RequestStatus.FULFILLED.value else FulfillmentStatus.AWAITING_FULFILLMENT.value,
                requester_id=requester.id,
                department_id=dept.id,
                location_id=loc.id,
                location=loc.name,
                required_from=datetime.now(timezone.utc) + timedelta(days=random.randint(1, 3)),
                required_to=datetime.now(timezone.utc) + timedelta(days=random.randint(4, 10)),
                estimated_duration_hours=random.uniform(8.0, 48.0),
                estimated_cost=random.uniform(350.0, 15000.0),
                approver_id=mgr_user.id if rstatus in [RequestStatus.APPROVED.value, RequestStatus.FULFILLED.value] else None,
                approved_at=datetime.now(timezone.utc) - timedelta(days=1) if rstatus in [RequestStatus.APPROVED.value, RequestStatus.FULFILLED.value] else None
            )
            session.add(op_req)
            await session.commit()
            await session.refresh(op_req)

            # If material request, add items
            if rtype == RequestType.MATERIAL_REQUEST.value:
                for mat in random.sample(catalog_items, k=2):
                    session.add(RequestMaterialItem(
                        request_id=op_req.id,
                        material_name=mat.name,
                        part_number=mat.part_number,
                        quantity_requested=float(random.randint(2, 10)),
                        unit=mat.unit_of_measure,
                        unit_cost=mat.default_unit_cost,
                        store_location=mat.primary_store
                    ))
            
            # Add action log
            session.add(RequestActionLog(
                request_id=op_req.id,
                user_id=requester.id,
                action="CREATED",
                notes="Requisition submitted through operational web portal"
            ))

        await session.commit()

        # 12. Seed Machine Requisitions
        print(" • Seeding machine fleet reservations and heavy equipment dispatches...")
        for mr_idx in range(12):
            req_num = f"MREQ-2026-{5000 + mr_idx}"
            q = await session.execute(select(MachineRequisition).where(MachineRequisition.requisition_number == req_num))
            if q.scalar_one_or_none():
                continue

            requester = random.choice(all_users)
            dept = random.choice(list(departments_map.values()))
            loc = random.choice(locations_list)
            mac = random.choice(machines_list) if machines_list else None

            start_t = datetime.now(timezone.utc) + timedelta(days=random.randint(1, 5))
            end_t = start_t + timedelta(hours=random.randint(8, 72))
            mtype_id = mac.machine_type_id if mac else (mtypes[0].id if mtypes else None)

            if mtype_id:
                m_req = MachineRequisition(
                    requisition_number=req_num,
                    department_id=dept.id,
                    requester_id=requester.id,
                    machine_type_id=mtype_id,
                    machine_id=mac.id if mac else None,
                    purpose=f"High-tonnage lithium ore load and haul operation at {loc.name}",
                    location=loc.name,
                    location_id=loc.id,
                    start_time=start_t,
                    end_time=end_t,
                    estimated_duration_hours=float(random.randint(8, 72)),
                    priority=random.randint(1, 3),
                    status=random.choice(["APPROVED", "IN_USE", "SCHEDULED", "AWAITING_ALLOCATION"]),
                    operator_required=True,
                    estimated_cost=random.uniform(800.0, 12000.0)
                )
                session.add(m_req)
        await session.commit()

        # 13. Seed Contractor Assignments
        print(" • Seeding external contractor work packages and compliance QA...")
        for ca_idx in range(8):
            assign_num = f"CASN-2026-{3000 + ca_idx}"
            q = await session.execute(select(ContractorAssignment).where(ContractorAssignment.assignment_number == assign_num))
            if q.scalar_one_or_none():
                continue

            comp = random.choice(contractors_list)
            session.add(ContractorAssignment(
                assignment_number=assign_num,
                contractor_company_id=comp.id,
                work_scope=f"Specialist contractor turnkey service: {comp.service_categories[0]} across plant infrastructure.",
                assignment_date=datetime.now(timezone.utc) - timedelta(days=random.randint(2, 20)),
                start_date=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 10)),
                supervisor_id=sup_user.id,
                verified_by_id=mgr_user.id,
                verification_status=random.choice([ContractorVerificationStatus.COMPLETED.value, ContractorVerificationStatus.IN_PROGRESS.value]),
                performance_rating=random.randint(4, 5),
                cost_agreed=random.uniform(5000.0, 45000.0),
                actual_cost=random.uniform(4800.0, 44000.0)
            ))
        await session.commit()

        # 14. Seed Material Requirements & Stock Movements
        print(" • Seeding storekeeper material transactions and issues...")
        for mr_idx in range(15):
            req_no = f"MAT-REQ-2026-{6000 + mr_idx}"
            q = await session.execute(select(MaterialRequirement).where(MaterialRequirement.requirement_number == req_no))
            if q.scalar_one_or_none():
                continue

            mat = random.choice(catalog_items)
            dept = random.choice(list(departments_map.values()))
            requester = random.choice(all_users)
            qty = float(random.randint(1, 8))

            m_req = MaterialRequirement(
                requirement_number=req_no,
                catalog_item_id=mat.id,
                material_name=mat.name,
                part_number=mat.part_number,
                category=mat.category,
                unit=mat.unit_of_measure,
                unit_cost=mat.default_unit_cost,
                quantity_required=qty,
                quantity_approved=qty,
                quantity_issued=qty if random.random() > 0.3 else 0.0,
                quantity_used=qty if random.random() > 0.5 else 0.0,
                status=random.choice([MaterialRequirementStatus.APPROVED.value, MaterialRequirementStatus.ISSUED.value, MaterialRequirementStatus.CONSUMED.value]),
                store_location=mat.primary_store,
                purpose=f"Planned replacement and rebuild component for plant uptime",
                department_id=dept.id,
                requester_id=requester.id,
                approver_id=mgr_user.id,
                approved_at=datetime.now(timezone.utc) - timedelta(days=2)
            )
            session.add(m_req)
            await session.commit()
            await session.refresh(m_req)

            # Add Material Transaction
            if m_req.quantity_issued > 0:
                session.add(MaterialTransaction(
                    requirement_id=m_req.id,
                    catalog_item_id=mat.id,
                    transaction_type=MaterialTransactionType.ISSUE.value,
                    quantity=m_req.quantity_issued,
                    unit=mat.unit_of_measure,
                    unit_cost=mat.default_unit_cost,
                    total_cost=m_req.quantity_issued * mat.default_unit_cost,
                    store_location=mat.primary_store,
                    batch_or_serial=f"BATCH-2026-{random.randint(100, 999)}"
                ))

        await session.commit()

        # 15. Seed Approval Requests & Multi-Level Authority Steps
        print(" • Seeding multi-tiered approvals, cost sign-offs, and digital signatures...")
        for apr_idx in range(10):
            res_id = uuid.uuid4()
            app_req = ApprovalRequest(
                resource_type="JOB_CARD" if apr_idx % 2 == 0 else "OPERATIONAL_REQUEST",
                resource_id=res_id,
                workflow_type="CAPEX_APPROVAL" if apr_idx % 3 == 0 else "MAINTENANCE_OPEX",
                priority=random.randint(1, 3),
                risk_level=random.choice(["MEDIUM", "HIGH", "CRITICAL"]),
                estimated_cost=random.uniform(1500.0, 35000.0),
                status=random.choice(["OPEN", "APPROVED", "PENDING_FINANCE"]),
                created_by_id=tech_user.id
            )
            session.add(app_req)
            await session.commit()
            await session.refresh(app_req)

            # Step 1: Supervisor Check
            session.add(ApprovalStep(
                approval_request_id=app_req.id,
                step_number=1,
                authority_role="Supervisor",
                required_permission="job_card:approve",
                status="APPROVED",
                approver_id=sup_user.id,
                approver_name=f"{sup_user.first_name} {sup_user.last_name}",
                approver_role_name="Shift Mechanical Supervisor",
                action="APPROVE",
                comment="Scope and spares availability verified against warehouse stocks."
            ))

            # Step 2: Department Manager
            session.add(ApprovalStep(
                approval_request_id=app_req.id,
                step_number=2,
                authority_role="Department Manager",
                required_permission="job_card:approve",
                status="APPROVED" if app_req.status == "APPROVED" else "PENDING",
                approver_id=mgr_user.id if app_req.status == "APPROVED" else None,
                approver_name=f"{mgr_user.first_name} {mgr_user.last_name}" if app_req.status == "APPROVED" else None,
                action="APPROVE" if app_req.status == "APPROVED" else None,
                comment="Approved under 2026 Mining Maintenance Budget." if app_req.status == "APPROVED" else None
            ))

        await session.commit()

        # 16. Seed Business Audit Trail (Immutable Events)
        print(" • Seeding enterprise audit trail and security event stream...")
        audit_events = [
            ("JOB_CARD", "CREATE", "Job card initiated for CAT 777D haul truck breakdown"),
            ("JOB_CARD", "SAFETY_CLEARANCE", "Granted LOTO electrical isolation permit #LOTO-8812"),
            ("APPROVAL", "AUTHORIZE", "Superintendent authorized $14,500 emergency jaw plate purchase"),
            ("FLEET", "DISPATCH", "Komatsu PC1250 excavator dispatched to Southern Open Pit Face"),
            ("MATERIALS", "ISSUE", "Issued 4x Spherical roller bearings to Heavy Workshop Bay 2"),
            ("CONTRACTOR", "VERIFY", "QA inspection approved for ZESA HV line transformer overhaul")
        ]
        for rtype, act, reason in audit_events:
            session.add(BusinessAuditLog(
                user_id=mgr_user.id,
                user_name=f"{mgr_user.first_name} {mgr_user.last_name}",
                department_name="Mechanical Engineering & Maintenance",
                role_names="Department Manager, Superintendent",
                action=act,
                resource=rtype,
                resource_id=str(uuid.uuid4()),
                reason=reason,
                ip_address="192.168.1.105",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Bikita/DWRMS-Client-2.9.0"
            ))

        # 17. Seed Real-time Push Notifications & SMS Dispatches
        print(" • Seeding system notifications, critical alerts, and SMS delivery receipts...")
        notification_types = [
            ("HIGH_PRIORITY_BREAKDOWN", "CRITICAL ALERT: Primary Crusher C140 Jaw Jammed", "Immediate technician response required at Primary Crushing Hopper."),
            ("LOTO_REQUIRED", "SAFETY NOTICE: Electrical Isolation Required", "Job Card JC-2026-2003 requires formal lock-out tag-out before physical work."),
            ("APPROVAL_REQUIRED", "PENDING SIGN-OFF: Requisition REQ-2026-4005", "Spares order exceeding $5,000 awaits Department Superintendent endorsement."),
            ("FLEET_DISPATCH", "FLEET DISPATCH: CAT 777D #02 Allocated", "Haul truck allocated to Shift Alpha for Lithium Pegmatite haulage.")
        ]
        for ntype, title, msg in notification_types:
            session.add(Notification(
                user_id=tech_user.id,
                type=ntype,
                title=title,
                message=msg,
                resource_type="JOB_CARD",
                resource_id=uuid.uuid4(),
                priority=2,
                is_read=random.choice([True, False])
            ))
            session.add(SMSMessage(
                recipient_phone="+263772123456",
                content=f"[DWRMS ALERT] {title}: {msg[:120]}...",
                provider_status="DELIVERED",
                sent_at=datetime.now(timezone.utc) - timedelta(minutes=random.randint(10, 360))
            ))

        await session.commit()

        print("\n==================================================================")
        print("  MOCK DATA GENERATION COMPLETE: ALL PAGES ENRICHED WITH REALISM! ")
        print("==================================================================")

if __name__ == "__main__":
    asyncio.run(seed_comprehensive_mock_data())
