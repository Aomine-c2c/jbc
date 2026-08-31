import uuid
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import select, func, or_, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.modules.assets.models import (
    Asset,
    AssetActivityLog,
    AssetMaintenanceRecord,
    AssetAttachment,
    AssetType,
    AssetStatus,
    AssetCriticality,
)
from app.modules.assets.schemas import (
    AssetCreate,
    AssetUpdate,
    AssetStatusTransition,
    AssetMaintenanceCreate,
    AssetResponse,
    AssetListResponse,
    AssetActivityLogResponse,
    AssetMaintenanceResponse,
    AssetAttachmentResponse,
    AssetMigrationSummary,
)
from app.modules.iam.models import User, Department, Location
from app.modules.fleet.models import Machine
from app.modules.work.models import WorkItem
from app.core.authz import AuthzGuard
from app.modules.audit.service import AuditService
from app.modules.iam.api import _get_user_permissions


class AssetService:

    @staticmethod
    def _generate_asset_tag(asset_type: str) -> str:
        year = datetime.utcnow().year
        short_id = uuid.uuid4().hex[:6].upper()
        at = (asset_type or "EQUIPMENT").upper().strip()
        if at == "MACHINE":
            return f"MCH-{year}-{short_id}"
        elif at == "VEHICLE":
            return f"VEH-{year}-{short_id}"
        elif at == "TOOL":
            return f"TOL-{year}-{short_id}"
        elif at == "INFRASTRUCTURE":
            return f"INF-{year}-{short_id}"
        elif at == "IT_EQUIPMENT":
            return f"IT-{year}-{short_id}"
        elif at == "PRODUCTION_EQUIPMENT":
            return f"PRD-{year}-{short_id}"
        else:
            return f"AST-{year}-{short_id}"

    # ── CRUD Operations ──────────────────────────────────────────

    @staticmethod
    async def create_asset(db: AsyncSession, data: AssetCreate, current_user: User) -> Asset:
        user_perms = _get_user_permissions(current_user)
        if not AuthzGuard.check_permission(current_user, "settings:manage", user_perms, resource_dept_id=data.department_id) and \
           not AuthzGuard.check_permission(current_user, "job_card:create", user_perms, resource_dept_id=data.department_id):
            raise HTTPException(status_code=403, detail="Not enough privileges to register asset")

        tag = data.asset_tag.strip() if data.asset_tag else AssetService._generate_asset_tag(data.asset_type)

        # Check tag uniqueness
        existing = await db.execute(select(Asset).where(Asset.asset_tag == tag))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail=f"Asset tag '{tag}' already exists")

        # Resolve location text if location_id given
        location_text = data.location
        if data.location_id and not location_text:
            loc_res = await db.execute(select(Location).where(Location.id == data.location_id))
            loc = loc_res.scalar_one_or_none()
            if loc:
                location_text = loc.breadcrumb or loc.name

        asset = Asset(
            id=uuid.uuid4(),
            asset_tag=tag,
            name=data.name.strip(),
            asset_type=data.asset_type.upper().strip(),
            category=data.category.strip() if data.category else None,
            manufacturer=data.manufacturer.strip() if data.manufacturer else None,
            model_number=data.model_number.strip() if data.model_number else None,
            serial_number=data.serial_number.strip() if data.serial_number else None,
            department_id=data.department_id,
            location_id=data.location_id,
            location=location_text,
            custodian_id=data.custodian_id,
            status=data.status.upper().strip(),
            criticality=data.criticality.upper().strip(),
            commissioned_date=data.commissioned_date,
            retired_date=data.retired_date,
            purchase_cost=data.purchase_cost or 0.0,
            current_value=data.current_value or data.purchase_cost or 0.0,
            barcode_or_nfc=data.barcode_or_nfc.strip() if data.barcode_or_nfc else None,
            notes=data.notes,
            specifications=data.specifications or {},
            machine_id=data.machine_id,
        )
        db.add(asset)
        await db.commit()
        await db.refresh(asset)

        # Record Initial Activity Log
        init_log = AssetActivityLog(
            id=uuid.uuid4(),
            asset_id=asset.id,
            user_id=current_user.id,
            activity_type="REGISTRATION",
            previous_value=None,
            new_value=asset.status,
            notes=f"Asset '{asset.name}' ({asset.asset_tag}) registered into central registry",
        )
        db.add(init_log)
        await db.commit()

        try:
            await AuditService.log_event(
                db=db,
                user=current_user,
                action="ASSET_CREATE",
                resource="ASSET",
                resource_id=str(asset.id),
                new_value={"tag": asset.asset_tag, "name": asset.name, "type": asset.asset_type},
                reason=f"Created asset {asset.asset_tag}",
            )
        except Exception:
            pass

        return asset

    @staticmethod
    async def get_asset(db: AsyncSession, asset_id: uuid.UUID, current_user: User) -> AssetResponse:
        res = await db.execute(select(Asset).where(Asset.id == asset_id))
        asset = res.scalar_one_or_none()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        # Count open work items
        open_work_q = select(func.count(WorkItem.id)).where(
            or_(
                WorkItem.asset_id == asset.id,
                and_(asset.machine_id is not None, WorkItem.machine_id == asset.machine_id),
            ),
            WorkItem.status.in_(["DRAFT", "SUBMITTED", "APPROVED", "ASSIGNED", "IN_PROGRESS", "ON_HOLD"]),
        )
        open_work_res = await db.execute(open_work_q)
        open_work_count = open_work_res.scalar_one_or_none() or 0

        resp = AssetResponse.model_validate(asset)
        resp.department_name = asset.department.name if asset.department else None
        resp.location_breadcrumb = asset.location_ref.breadcrumb if asset.location_ref else (asset.location or None)
        resp.custodian_name = f"{asset.custodian.first_name} {asset.custodian.last_name}" if asset.custodian else None
        resp.machine_identifier = asset.machine.identifier if asset.machine else None
        resp.open_work_items_count = open_work_count

        # Explicitly query activity logs, maintenance records, and attachments
        logs_res = await db.execute(select(AssetActivityLog).where(AssetActivityLog.asset_id == asset.id).order_by(AssetActivityLog.created_at.desc()))
        logs = logs_res.scalars().all()

        maint_res = await db.execute(select(AssetMaintenanceRecord).where(AssetMaintenanceRecord.asset_id == asset.id).order_by(AssetMaintenanceRecord.service_date.desc()))
        maint = maint_res.scalars().all()

        attach_res = await db.execute(select(AssetAttachment).where(AssetAttachment.asset_id == asset.id))
        attachments = attach_res.scalars().all()

        resp.activity_logs = [
            AssetActivityLogResponse(
                id=l.id,
                asset_id=l.asset_id,
                user_id=l.user_id,
                activity_type=l.activity_type,
                previous_value=l.previous_value,
                new_value=l.new_value,
                notes=l.notes,
                created_at=l.created_at,
                user_name=f"{l.user.first_name} {l.user.last_name}" if l.user else None,
            )
            for l in logs
        ]

        resp.maintenance_records = [
            AssetMaintenanceResponse.model_validate(m) for m in maint
        ]

        resp.attachments = [
            AssetAttachmentResponse.model_validate(a) for a in attachments
        ]

        return resp

    @staticmethod
    async def list_assets(
        db: AsyncSession,
        current_user: User,
        asset_type: Optional[str] = None,
        category: Optional[str] = None,
        department_id: Optional[uuid.UUID] = None,
        location_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        criticality: Optional[str] = None,
        include_archived: bool = False,
        search_query: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AssetListResponse]:
        query = select(Asset)

        if not include_archived:
            query = query.where(Asset.is_archived == False)

        if asset_type:
            query = query.where(Asset.asset_type == asset_type.upper().strip())
        if category:
            query = query.where(Asset.category.ilike(f"%{category.strip()}%"))
        if department_id:
            query = query.where(Asset.department_id == department_id)
        if location_id:
            query = query.where(Asset.location_id == location_id)
        if status:
            query = query.where(Asset.status == status.upper().strip())
        if criticality:
            query = query.where(Asset.criticality == criticality.upper().strip())

        if search_query:
            p = f"%{search_query.strip()}%"
            query = query.where(
                or_(
                    Asset.asset_tag.ilike(p),
                    Asset.name.ilike(p),
                    Asset.serial_number.ilike(p),
                    Asset.manufacturer.ilike(p),
                    Asset.model_number.ilike(p),
                    Asset.barcode_or_nfc.ilike(p),
                    Asset.location.ilike(p),
                )
            )

        query = query.order_by(Asset.name.asc()).limit(limit).offset(offset)
        res = await db.execute(query)
        assets = res.scalars().all()

        results = []
        for a in assets:
            row = AssetListResponse(
                id=a.id,
                asset_tag=a.asset_tag,
                name=a.name,
                asset_type=a.asset_type,
                category=a.category,
                manufacturer=a.manufacturer,
                model_number=a.model_number,
                serial_number=a.serial_number,
                department_id=a.department_id,
                department_name=a.department.name if a.department else None,
                location_breadcrumb=a.location_ref.breadcrumb if a.location_ref else (a.location or None),
                custodian_name=f"{a.custodian.first_name} {a.custodian.last_name}" if a.custodian else None,
                status=a.status,
                criticality=a.criticality,
                is_archived=a.is_archived,
                machine_id=a.machine_id,
                created_at=a.created_at,
            )
            results.append(row)
        return results

    @staticmethod
    async def update_asset(db: AsyncSession, asset_id: uuid.UUID, data: AssetUpdate, current_user: User) -> Asset:
        res = await db.execute(select(Asset).where(Asset.id == asset_id))
        asset = res.scalar_one_or_none()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        # Track movements or custody transfers
        if data.location_id is not None and data.location_id != asset.location_id:
            loc_res = await db.execute(select(Location).where(Location.id == data.location_id))
            new_loc = loc_res.scalar_one_or_none()
            new_breadcrumb = (new_loc.breadcrumb or new_loc.name) if new_loc else str(data.location_id)
            old_breadcrumb = asset.location_ref.breadcrumb if asset.location_ref else (asset.location or "None")
            
            activity = AssetActivityLog(
                id=uuid.uuid4(),
                asset_id=asset.id,
                user_id=current_user.id,
                activity_type="LOCATION_CHANGE",
                previous_value=old_breadcrumb,
                new_value=new_breadcrumb,
                notes="Asset relocated",
            )
            db.add(activity)
            asset.location_id = data.location_id
            asset.location = new_breadcrumb

        if data.custodian_id is not None and data.custodian_id != asset.custodian_id:
            old_cust = f"{asset.custodian.first_name} {asset.custodian.last_name}" if asset.custodian else "None"
            cust_res = await db.execute(select(User).where(User.id == data.custodian_id))
            new_cust_obj = cust_res.scalar_one_or_none()
            new_cust = f"{new_cust_obj.first_name} {new_cust_obj.last_name}" if new_cust_obj else str(data.custodian_id)

            activity = AssetActivityLog(
                id=uuid.uuid4(),
                asset_id=asset.id,
                user_id=current_user.id,
                activity_type="CUSTODIAN_CHANGE",
                previous_value=old_cust,
                new_value=new_cust,
                notes="Asset custody transferred",
            )
            db.add(activity)
            asset.custodian_id = data.custodian_id

        # Update remaining attributes
        for k, v in data.model_dump(exclude_unset=True).items():
            if k not in ["location_id", "custodian_id"] and hasattr(asset, k) and v is not None:
                setattr(asset, k, v)

        await db.commit()
        await db.refresh(asset)
        return asset

    @staticmethod
    async def transition_status(
        db: AsyncSession, asset_id: uuid.UUID, data: AssetStatusTransition, current_user: User
    ) -> Asset:
        res = await db.execute(select(Asset).where(Asset.id == asset_id))
        asset = res.scalar_one_or_none()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        target_status = data.status.upper().strip()
        old_status = asset.status

        if old_status == target_status:
            return asset

        asset.status = target_status
        await db.commit()
        await db.refresh(asset)

        # Log Activity
        activity = AssetActivityLog(
            id=uuid.uuid4(),
            asset_id=asset.id,
            user_id=current_user.id,
            activity_type="STATUS_CHANGE",
            previous_value=old_status,
            new_value=target_status,
            notes=data.notes or f"Status changed from {old_status} to {target_status}",
        )
        db.add(activity)
        await db.commit()

        # Synchronize linked Machine if present
        if asset.machine_id:
            m_res = await db.execute(select(Machine).where(Machine.id == asset.machine_id))
            machine = m_res.scalar_one_or_none()
            if machine and machine.status != target_status:
                if target_status in ["AVAILABLE", "IN_USE", "UNDER_MAINTENANCE", "OUT_OF_SERVICE", "RETIRED"]:
                    machine.status = target_status
                    await db.commit()

        return asset

    @staticmethod
    async def archive_asset(db: AsyncSession, asset_id: uuid.UUID, reason: str, current_user: User) -> Asset:
        res = await db.execute(select(Asset).where(Asset.id == asset_id))
        asset = res.scalar_one_or_none()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        asset.is_archived = True
        asset.archived_at = datetime.utcnow()
        asset.archived_reason = reason.strip()
        asset.status = "RETIRED"
        await db.commit()

        activity = AssetActivityLog(
            id=uuid.uuid4(),
            asset_id=asset.id,
            user_id=current_user.id,
            activity_type="ARCHIVE",
            previous_value="Active",
            new_value="Archived",
            notes=f"Decommissioned/Archived: {reason.strip()}",
        )
        db.add(activity)
        await db.commit()
        return asset

    @staticmethod
    async def restore_asset(db: AsyncSession, asset_id: uuid.UUID, current_user: User) -> Asset:
        res = await db.execute(select(Asset).where(Asset.id == asset_id))
        asset = res.scalar_one_or_none()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        asset.is_archived = False
        asset.archived_at = None
        asset.archived_reason = None
        asset.status = "AVAILABLE"
        await db.commit()

        activity = AssetActivityLog(
            id=uuid.uuid4(),
            asset_id=asset.id,
            user_id=current_user.id,
            activity_type="RESTORE",
            previous_value="Archived",
            new_value="AVAILABLE",
            notes="Restored asset back to operational service",
        )
        db.add(activity)
        await db.commit()
        return asset

    @staticmethod
    async def record_maintenance(
        db: AsyncSession, asset_id: uuid.UUID, data: AssetMaintenanceCreate, current_user: User
    ) -> AssetMaintenanceRecord:
        res = await db.execute(select(Asset).where(Asset.id == asset_id))
        asset = res.scalar_one_or_none()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        m_rec = AssetMaintenanceRecord(
            id=uuid.uuid4(),
            asset_id=asset.id,
            maintenance_type=data.maintenance_type.upper().strip(),
            summary=data.summary.strip(),
            service_date=data.service_date or datetime.utcnow(),
            performed_by=data.performed_by or f"{current_user.first_name} {current_user.last_name}",
            meter_reading=data.meter_reading or 0.0,
            cost=data.cost or 0.0,
            work_item_id=data.work_item_id,
            job_card_id=data.job_card_id,
        )
        db.add(m_rec)
        await db.commit()

        # Log Activity
        activity = AssetActivityLog(
            id=uuid.uuid4(),
            asset_id=asset.id,
            user_id=current_user.id,
            activity_type="MAINTENANCE_EVENT",
            previous_value=None,
            new_value=data.maintenance_type.upper().strip(),
            notes=f"Maintenance logged: {data.summary.strip()} (${data.cost or 0.0:.2f})",
        )
        db.add(activity)
        await db.commit()
        return m_rec

    @staticmethod
    async def migrate_machines_to_assets(db: AsyncSession) -> AssetMigrationSummary:
        """Non-destructively creates corresponding physical Asset records for all existing Machines."""
        summary = AssetMigrationSummary()
        res = await db.execute(select(Machine))
        machines = res.scalars().all()
        summary.scanned_machines = len(machines)

        for m in machines:
            if not m.asset_id:
                # Check if asset with tag exists
                existing = await db.execute(select(Asset).where(Asset.asset_tag == m.identifier))
                asset = existing.scalar_one_or_none()
                if not asset:
                    # Find default department (or first available)
                    dept_res = await db.execute(select(Department).limit(1))
                    dept = dept_res.scalar_one_or_none()
                    if not dept:
                        continue

                    asset = Asset(
                        id=uuid.uuid4(),
                        asset_tag=m.identifier,
                        name=f"{m.machine_type.name} ({m.identifier})" if m.machine_type else m.identifier,
                        asset_type="MACHINE",
                        category=m.machine_type.category if m.machine_type else "Heavy Equipment",
                        serial_number=m.serial_number,
                        department_id=dept.id,
                        location_id=m.location_id,
                        location=m.location,
                        status=m.status,
                        machine_id=m.id,
                    )
                    db.add(asset)
                    await db.commit()
                    await db.refresh(asset)
                    summary.created_assets += 1

                m.asset_id = asset.id
                await db.commit()
                summary.linked_machines += 1
                summary.details.append(f"Linked Machine '{m.identifier}' to Asset '{asset.asset_tag}'")
            else:
                summary.skipped += 1

        return summary
