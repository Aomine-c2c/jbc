import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.modules.materials.models import (
    MaterialCatalogItem,
    MaterialRequirement,
    MaterialTransaction,
    MaterialRequirementStatus,
    MaterialTransactionType,
)
from app.modules.materials.schemas import (
    MaterialCatalogCreate,
    MaterialCatalogUpdate,
    MaterialRequirementCreate,
    MaterialRequirementApprove,
    MaterialIssueRequest,
    MaterialUsageRequest,
    MaterialReturnRequest,
    MaterialRequirementResponse,
    MaterialRequirementListResponse,
    MaterialTransactionResponse,
    MaterialCatalogResponse,
)
from app.modules.materials.adapters import inventory_adapter
from app.modules.iam.models import User, Department
from app.modules.work.models import WorkItem
from app.core.authz import AuthzGuard
from app.modules.audit.service import AuditService


class MaterialService:

    @staticmethod
    def _generate_requirement_number() -> str:
        year = datetime.utcnow().year
        short_id = uuid.uuid4().hex[:6].upper()
        return f"MTR-{year}-{short_id}"

    # ── Material Catalog Management ──────────────────────────────

    @staticmethod
    async def create_catalog_item(
        db: AsyncSession, data: MaterialCatalogCreate, current_user: User
    ) -> MaterialCatalogItem:
        existing = await db.execute(
            select(MaterialCatalogItem).where(MaterialCatalogItem.part_number == data.part_number.strip())
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail=f"Part number '{data.part_number}' already exists in catalog")

        item = MaterialCatalogItem(
            id=uuid.uuid4(),
            part_number=data.part_number.strip(),
            name=data.name.strip(),
            description=data.description.strip() if data.description else None,
            category=data.category.strip() if data.category else None,
            unit_of_measure=data.unit_of_measure.strip() if data.unit_of_measure else "units",
            default_unit_cost=data.default_unit_cost or 0.0,
            primary_store=data.primary_store.strip() if data.primary_store else None,
            is_active=data.is_active,
            external_erp_id=data.external_erp_id.strip() if data.external_erp_id else None,
        )
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item

    @staticmethod
    async def list_catalog(
        db: AsyncSession,
        search_query: Optional[str] = None,
        category: Optional[str] = None,
        is_active: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> List[MaterialCatalogItem]:
        query = select(MaterialCatalogItem).where(MaterialCatalogItem.is_active == is_active)
        if category:
            query = query.where(MaterialCatalogItem.category == category.strip())
        if search_query:
            p = f"%{search_query.strip()}%"
            query = query.where(
                or_(
                    MaterialCatalogItem.part_number.ilike(p),
                    MaterialCatalogItem.name.ilike(p),
                    MaterialCatalogItem.description.ilike(p),
                    MaterialCatalogItem.category.ilike(p),
                )
            )
        query = query.order_by(MaterialCatalogItem.name.asc()).limit(limit).offset(offset)
        res = await db.execute(query)
        return list(res.scalars().all())

    # ── Material Requirements Tracking ───────────────────────────

    @staticmethod
    async def create_requirement(
        db: AsyncSession, data: MaterialRequirementCreate, current_user: User
    ) -> MaterialRequirement:
        mat_name = data.material_name.strip()
        part_num = data.part_number.strip() if data.part_number else None
        uom = data.unit.strip() if data.unit else "units"
        u_cost = data.unit_cost or 0.0
        cat = data.category.strip() if data.category else None

        # Auto-fill from catalog if linked
        if data.catalog_item_id:
            c_res = await db.execute(
                select(MaterialCatalogItem).where(MaterialCatalogItem.id == data.catalog_item_id)
            )
            c_item = c_res.scalar_one_or_none()
            if c_item:
                mat_name = c_item.name
                part_num = c_item.part_number
                uom = c_item.unit_of_measure
                u_cost = c_item.default_unit_cost
                cat = c_item.category

        req_num = MaterialService._generate_requirement_number()

        req = MaterialRequirement(
            id=uuid.uuid4(),
            requirement_number=req_num,
            catalog_item_id=data.catalog_item_id,
            material_name=mat_name,
            part_number=part_num,
            category=cat,
            unit=uom,
            unit_cost=u_cost,
            quantity_required=data.quantity_required,
            quantity_approved=0.0,
            quantity_issued=0.0,
            quantity_used=0.0,
            quantity_returned=0.0,
            status="REQUESTED",
            store_location=data.store_location.strip() if data.store_location else None,
            purpose=data.purpose.strip() if data.purpose else None,
            work_item_id=data.work_item_id,
            job_card_id=data.job_card_id,
            asset_id=data.asset_id,
            request_id=data.request_id,
            department_id=data.department_id,
            requester_id=current_user.id,
            notes=data.notes,
        )
        db.add(req)
        await db.commit()
        await db.refresh(req)

        try:
            await AuditService.log_event(
                db=db,
                user=current_user,
                action="MATERIAL_REQUIREMENT_CREATE",
                resource="MATERIAL_REQUIREMENT",
                resource_id=str(req.id),
                new_value={"number": req.requirement_number, "material": req.material_name, "qty": req.quantity_required},
                reason=f"Requested material {req.material_name}",
            )
        except Exception:
            pass

        return req

    @staticmethod
    async def approve_requirement(
        db: AsyncSession, requirement_id: uuid.UUID, data: MaterialRequirementApprove, current_user: User
    ) -> MaterialRequirement:
        res = await db.execute(select(MaterialRequirement).where(MaterialRequirement.id == requirement_id))
        req = res.scalar_one_or_none()
        if not req:
            raise HTTPException(status_code=404, detail="Material requirement not found")

        # Separation of Duties check
        if current_user.id == req.requester_id and not current_user.is_superuser:
            raise HTTPException(
                status_code=409, detail="Separation of Duties violation: cannot approve your own material request"
            )

        req.quantity_approved = data.quantity_approved
        req.approver_id = current_user.id
        req.approved_at = datetime.utcnow()
        req.status = "APPROVED"

        if data.notes:
            req.notes = f"{req.notes or ''}\nApproval Notes: {data.notes}".strip()

        await db.commit()
        await db.refresh(req)
        return req

    @staticmethod
    async def issue_material(
        db: AsyncSession, requirement_id: uuid.UUID, data: MaterialIssueRequest, current_user: User
    ) -> MaterialTransaction:
        res = await db.execute(
            select(MaterialRequirement)
            .where(MaterialRequirement.id == requirement_id)
            .with_for_update()
        )
        req = res.scalar_one_or_none()
        if not req:
            raise HTTPException(status_code=404, detail="Material requirement not found")

        # Over-issue prevention safeguard
        approved_target = req.quantity_approved if req.quantity_approved > 0 else req.quantity_required
        available_to_issue = approved_target - req.quantity_issued

        if data.quantity > available_to_issue:
            raise HTTPException(
                status_code=400,
                detail=f"Over-issue prevented: Requested issue quantity ({data.quantity}) exceeds remaining approved allocation ({available_to_issue})"
            )

        # Emit ERP Goods Issue via adapter
        erp_res = await inventory_adapter.post_goods_issue(
            requirement_id=str(req.id),
            part_number=req.part_number or req.material_name,
            quantity=data.quantity,
            unit=req.unit,
            store_location=data.store_location or req.store_location,
        )

        total_c = data.quantity * (req.unit_cost or 0.0)

        tx = MaterialTransaction(
            id=uuid.uuid4(),
            requirement_id=req.id,
            catalog_item_id=req.catalog_item_id,
            transaction_type="ISSUE",
            quantity=data.quantity,
            unit=req.unit,
            unit_cost=req.unit_cost,
            total_cost=total_c,
            store_location=data.store_location or req.store_location,
            batch_or_serial=data.batch_or_serial,
            issued_by_id=current_user.id,
            received_by_id=data.received_by_id,
            notes=data.notes,
            external_reference=erp_res.get("external_document_number"),
        )
        db.add(tx)

        req.quantity_issued += data.quantity
        if req.quantity_issued >= approved_target:
            req.status = "ISSUED"
        else:
            req.status = "PARTIALLY_ISSUED"

        await db.commit()
        await db.refresh(tx)
        return tx

    @staticmethod
    async def record_usage(
        db: AsyncSession, requirement_id: uuid.UUID, data: MaterialUsageRequest, current_user: User
    ) -> MaterialTransaction:
        res = await db.execute(select(MaterialRequirement).where(MaterialRequirement.id == requirement_id))
        req = res.scalar_one_or_none()
        if not req:
            raise HTTPException(status_code=404, detail="Material requirement not found")

        available_in_hand = req.quantity_issued - req.quantity_used - req.quantity_returned
        if data.quantity > available_in_hand:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot record consumption ({data.quantity}) exceeding materials currently issued on site ({available_in_hand})"
            )

        total_c = data.quantity * (req.unit_cost or 0.0)

        tx = MaterialTransaction(
            id=uuid.uuid4(),
            requirement_id=req.id,
            catalog_item_id=req.catalog_item_id,
            transaction_type="USAGE",
            quantity=data.quantity,
            unit=req.unit,
            unit_cost=req.unit_cost,
            total_cost=total_c,
            store_location=req.store_location,
            issued_by_id=None,
            received_by_id=current_user.id,
            notes=data.notes,
        )
        db.add(tx)

        req.quantity_used += data.quantity
        if (req.quantity_used + req.quantity_returned) >= req.quantity_issued:
            req.status = "CONSUMED"
        else:
            req.status = "IN_USE"

        await db.commit()
        await db.refresh(tx)
        return tx

    @staticmethod
    async def return_material(
        db: AsyncSession, requirement_id: uuid.UUID, data: MaterialReturnRequest, current_user: User
    ) -> MaterialTransaction:
        res = await db.execute(select(MaterialRequirement).where(MaterialRequirement.id == requirement_id))
        req = res.scalar_one_or_none()
        if not req:
            raise HTTPException(status_code=404, detail="Material requirement not found")

        available_in_hand = req.quantity_issued - req.quantity_used - req.quantity_returned
        if data.quantity > available_in_hand:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot return quantity ({data.quantity}) exceeding unconsumed materials on site ({available_in_hand})"
            )

        erp_res = await inventory_adapter.post_goods_return(
            requirement_id=str(req.id),
            part_number=req.part_number or req.material_name,
            quantity=data.quantity,
            unit=req.unit,
            store_location=data.store_location or req.store_location,
            reason=data.notes,
        )

        total_c = data.quantity * (req.unit_cost or 0.0)

        tx = MaterialTransaction(
            id=uuid.uuid4(),
            requirement_id=req.id,
            catalog_item_id=req.catalog_item_id,
            transaction_type="RETURN",
            quantity=data.quantity,
            unit=req.unit,
            unit_cost=req.unit_cost,
            total_cost=total_c,
            store_location=data.store_location or req.store_location,
            issued_by_id=current_user.id,
            received_by_id=None,
            notes=data.notes,
            external_reference=erp_res.get("external_document_number"),
        )
        db.add(tx)

        req.quantity_returned += data.quantity
        if req.quantity_returned == req.quantity_issued:
            req.status = "RETURNED"
        elif (req.quantity_used + req.quantity_returned) >= req.quantity_issued:
            req.status = "CONSUMED"

        await db.commit()
        await db.refresh(tx)
        return tx

    @staticmethod
    async def get_requirement(
        db: AsyncSession, requirement_id: uuid.UUID, current_user: User
    ) -> MaterialRequirementResponse:
        res = await db.execute(select(MaterialRequirement).where(MaterialRequirement.id == requirement_id))
        req = res.scalar_one_or_none()
        if not req:
            raise HTTPException(status_code=404, detail="Material requirement not found")

        tx_res = await db.execute(
            select(MaterialTransaction)
            .where(MaterialTransaction.requirement_id == req.id)
            .order_by(MaterialTransaction.created_at.desc())
        )
        transactions = tx_res.scalars().all()

        resp = MaterialRequirementResponse.model_validate(req)
        resp.requester_name = f"{req.requester.first_name} {req.requester.last_name}" if req.requester else None
        resp.approver_name = f"{req.approver.first_name} {req.approver.last_name}" if req.approver else None
        resp.department_name = req.department.name if req.department else None
        resp.work_item_reference = req.work_item.reference_number if req.work_item else None
        resp.asset_name = req.asset.name if req.asset else None

        resp.transactions = [
            MaterialTransactionResponse(
                id=t.id,
                requirement_id=t.requirement_id,
                catalog_item_id=t.catalog_item_id,
                transaction_type=t.transaction_type,
                quantity=t.quantity,
                unit=t.unit,
                unit_cost=t.unit_cost,
                total_cost=t.total_cost,
                store_location=t.store_location,
                batch_or_serial=t.batch_or_serial,
                issued_by_id=t.issued_by_id,
                received_by_id=t.received_by_id,
                issued_by_name=f"{t.issued_by.first_name} {t.issued_by.last_name}" if t.issued_by else None,
                received_by_name=f"{t.received_by.first_name} {t.received_by.last_name}" if t.received_by else None,
                notes=t.notes,
                external_reference=t.external_reference,
                created_at=t.created_at,
            )
            for t in transactions
        ]
        return resp

    @staticmethod
    async def list_requirements(
        db: AsyncSession,
        current_user: User,
        department_id: Optional[uuid.UUID] = None,
        work_item_id: Optional[uuid.UUID] = None,
        job_card_id: Optional[uuid.UUID] = None,
        asset_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        search_query: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[MaterialRequirementListResponse]:
        query = select(MaterialRequirement)
        if department_id:
            query = query.where(MaterialRequirement.department_id == department_id)
        if work_item_id:
            query = query.where(MaterialRequirement.work_item_id == work_item_id)
        if job_card_id:
            query = query.where(MaterialRequirement.job_card_id == job_card_id)
        if asset_id:
            query = query.where(MaterialRequirement.asset_id == asset_id)
        if status:
            query = query.where(MaterialRequirement.status == status.upper().strip())

        if search_query:
            p = f"%{search_query.strip()}%"
            query = query.where(
                or_(
                    MaterialRequirement.requirement_number.ilike(p),
                    MaterialRequirement.material_name.ilike(p),
                    MaterialRequirement.part_number.ilike(p),
                    MaterialRequirement.store_location.ilike(p),
                )
            )

        query = query.order_by(MaterialRequirement.created_at.desc()).limit(limit).offset(offset)
        res = await db.execute(query)
        reqs = res.scalars().all()

        results = []
        for r in reqs:
            row = MaterialRequirementListResponse(
                id=r.id,
                requirement_number=r.requirement_number,
                material_name=r.material_name,
                part_number=r.part_number,
                category=r.category,
                unit=r.unit,
                unit_cost=r.unit_cost,
                quantity_required=r.quantity_required,
                quantity_approved=r.quantity_approved,
                quantity_issued=r.quantity_issued,
                quantity_used=r.quantity_used,
                quantity_returned=r.quantity_returned,
                status=r.status,
                store_location=r.store_location,
                department_name=r.department.name if r.department else None,
                requester_name=f"{r.requester.first_name} {r.requester.last_name}" if r.requester else None,
                work_item_id=r.work_item_id,
                created_at=r.created_at,
            )
            results.append(row)
        return results
