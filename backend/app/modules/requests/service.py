import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.modules.requests.models import (
    OperationalRequest,
    RequestMaterialItem,
    RequestActionLog,
    RequestComment,
    RequestAttachment,
    RequestType,
    RequestStatus,
    FulfillmentStatus,
)
from app.modules.requests.schemas import (
    RequestCreate,
    RequestUpdate,
    RequestTransition,
    RequestFulfill,
    RequestMaterialItemCreate,
    MaterialIssueRequest,
    MaterialReturnRequest,
    RequestCommentCreate,
    RequestResponse,
    RequestListResponse,
    RequestMaterialItemResponse,
    RequestActionLogResponse,
    RequestCommentResponse,
    RequestAttachmentResponse,
)
from app.modules.iam.models import User, Department, Location
from app.modules.work.models import WorkItem
from app.core.authz import AuthzGuard
from app.modules.audit.service import AuditService
from app.modules.iam.api import _get_user_permissions


class RequestService:

    @staticmethod
    def _generate_request_number(request_type: str) -> str:
        year = datetime.utcnow().year
        short_id = uuid.uuid4().hex[:6].upper()
        rt = (request_type or "OTHER").upper().strip()
        if rt == "MACHINE_REQUEST":
            return f"MR-{year}-{short_id}"
        elif rt == "EQUIPMENT_REQUEST":
            return f"EQ-{year}-{short_id}"
        elif rt == "VEHICLE_REQUEST":
            return f"VEH-{year}-{short_id}"
        elif rt == "MATERIAL_REQUEST":
            return f"MAT-{year}-{short_id}"
        elif rt == "PERSONNEL_REQUEST":
            return f"PRS-{year}-{short_id}"
        elif rt == "CONTRACTOR_REQUEST":
            return f"CON-{year}-{short_id}"
        else:
            return f"REQ-{year}-{short_id}"

    # ── CRUD Operations ──────────────────────────────────────────

    @staticmethod
    async def create_request(db: AsyncSession, data: RequestCreate, current_user: User) -> OperationalRequest:
        req_number = RequestService._generate_request_number(data.request_type)

        # Resolve location breadcrumb
        location_text = data.location
        if data.location_id and not location_text:
            loc_res = await db.execute(select(Location).where(Location.id == data.location_id))
            loc = loc_res.scalar_one_or_none()
            if loc:
                location_text = loc.breadcrumb or loc.name

        req = OperationalRequest(
            id=uuid.uuid4(),
            request_number=req_number,
            request_type=data.request_type.upper().strip(),
            title=data.title.strip(),
            purpose=data.purpose.strip(),
            description=data.description.strip() if data.description else None,
            priority=data.priority,
            status="DRAFT",
            fulfillment_status="UNALLOCATED",
            requester_id=current_user.id,
            department_id=data.department_id,
            collaborating_department_id=data.collaborating_department_id,
            location_id=data.location_id,
            location=location_text,
            required_from=data.required_from,
            required_to=data.required_to,
            estimated_duration_hours=data.estimated_duration_hours or 0.0,
            cost_centre=data.cost_centre,
            estimated_cost=data.estimated_cost or 0.0,
            work_item_id=data.work_item_id,
            job_card_id=data.job_card_id,
            machine_requisition_id=data.machine_requisition_id,
            type_specific_data=data.type_specific_data or {},
        )
        db.add(req)
        await db.commit()
        await db.refresh(req)

        # Add Material Items if present
        if data.material_items:
            for item in data.material_items:
                m_item = RequestMaterialItem(
                    id=uuid.uuid4(),
                    request_id=req.id,
                    material_name=item.material_name.strip(),
                    part_number=item.part_number.strip() if item.part_number else None,
                    quantity_requested=item.quantity_requested,
                    unit=item.unit.strip() if item.unit else "units",
                    store_location=item.store_location.strip() if item.store_location else None,
                    unit_cost=item.unit_cost or 0.0,
                )
                db.add(m_item)
            await db.commit()

        # Log creation action
        init_log = RequestActionLog(
            id=uuid.uuid4(),
            request_id=req.id,
            user_id=current_user.id,
            action="CREATE",
            from_status=None,
            to_status="DRAFT",
            notes=f"Created {req.request_type} '{req.title}' ({req.request_number})",
        )
        db.add(init_log)
        await db.commit()

        try:
            await AuditService.log_event(
                db=db,
                user=current_user,
                action="REQUEST_CREATE",
                resource="OPERATIONAL_REQUEST",
                resource_id=str(req.id),
                new_value={"number": req.request_number, "type": req.request_type, "title": req.title},
                reason=f"Created request {req.request_number}",
            )
        except Exception:
            pass

        return req

    @staticmethod
    async def get_request(db: AsyncSession, request_id: uuid.UUID, current_user: User) -> RequestResponse:
        res = await db.execute(select(OperationalRequest).where(OperationalRequest.id == request_id))
        req = res.scalar_one_or_none()
        if not req:
            raise HTTPException(status_code=404, detail="Request not found")

        # Explicitly query child collections for safety
        items_res = await db.execute(select(RequestMaterialItem).where(RequestMaterialItem.request_id == req.id))
        material_items = items_res.scalars().all()

        logs_res = await db.execute(select(RequestActionLog).where(RequestActionLog.request_id == req.id).order_by(RequestActionLog.created_at.desc()))
        action_logs = logs_res.scalars().all()

        comments_res = await db.execute(select(RequestComment).where(RequestComment.request_id == req.id).order_by(RequestComment.created_at.desc()))
        comments = comments_res.scalars().all()

        attach_res = await db.execute(select(RequestAttachment).where(RequestAttachment.request_id == req.id))
        attachments = attach_res.scalars().all()

        resp = RequestResponse.model_validate(req)
        resp.requester_name = f"{req.requester.first_name} {req.requester.last_name}" if req.requester else None
        resp.department_name = req.department.name if req.department else None
        resp.collaborating_department_name = req.collaborating_department.name if req.collaborating_department else None
        resp.location_breadcrumb = req.location_ref.breadcrumb if req.location_ref else (req.location or None)
        resp.approver_name = f"{req.approver.first_name} {req.approver.last_name}" if req.approver else None
        resp.fulfillment_user_name = f"{req.fulfillment_user.first_name} {req.fulfillment_user.last_name}" if req.fulfillment_user else None
        resp.work_item_reference = req.work_item.reference_number if req.work_item else None

        resp.material_items = [
            RequestMaterialItemResponse.model_validate(i) for i in material_items
        ]
        resp.action_logs = [
            RequestActionLogResponse(
                id=l.id,
                request_id=l.request_id,
                user_id=l.user_id,
                action=l.action,
                from_status=l.from_status,
                to_status=l.to_status,
                notes=l.notes,
                created_at=l.created_at,
                user_name=f"{l.user.first_name} {l.user.last_name}" if l.user else None,
            )
            for l in action_logs
        ]
        resp.comments = [
            RequestCommentResponse(
                id=c.id,
                request_id=c.request_id,
                user_id=c.user_id,
                comment=c.comment,
                created_at=c.created_at,
                user_name=f"{c.user.first_name} {c.user.last_name}" if c.user else None,
            )
            for c in comments
        ]
        resp.attachments = [
            RequestAttachmentResponse.model_validate(a) for a in attachments
        ]
        return resp

    @staticmethod
    async def list_requests(
        db: AsyncSession,
        current_user: User,
        request_type: Optional[str] = None,
        department_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        fulfillment_status: Optional[str] = None,
        priority: Optional[int] = None,
        work_item_id: Optional[uuid.UUID] = None,
        search_query: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[RequestListResponse]:
        query = select(OperationalRequest)

        if request_type:
            query = query.where(OperationalRequest.request_type == request_type.upper().strip())
        if department_id:
            query = query.where(OperationalRequest.department_id == department_id)
        if status:
            query = query.where(OperationalRequest.status == status.upper().strip())
        if fulfillment_status:
            query = query.where(OperationalRequest.fulfillment_status == fulfillment_status.upper().strip())
        if priority is not None:
            query = query.where(OperationalRequest.priority == priority)
        if work_item_id:
            query = query.where(OperationalRequest.work_item_id == work_item_id)

        if search_query:
            p = f"%{search_query.strip()}%"
            query = query.where(
                or_(
                    OperationalRequest.request_number.ilike(p),
                    OperationalRequest.title.ilike(p),
                    OperationalRequest.purpose.ilike(p),
                    OperationalRequest.location.ilike(p),
                )
            )

        query = query.order_by(OperationalRequest.created_at.desc()).limit(limit).offset(offset)
        res = await db.execute(query)
        requests = res.scalars().all()

        results = []
        for r in requests:
            row = RequestListResponse(
                id=r.id,
                request_number=r.request_number,
                request_type=r.request_type,
                title=r.title,
                purpose=r.purpose,
                priority=r.priority,
                status=r.status,
                fulfillment_status=r.fulfillment_status,
                requester_name=f"{r.requester.first_name} {r.requester.last_name}" if r.requester else None,
                department_id=r.department_id,
                department_name=r.department.name if r.department else None,
                collaborating_department_name=r.collaborating_department.name if r.collaborating_department else None,
                location_breadcrumb=r.location_ref.breadcrumb if r.location_ref else (r.location or None),
                required_from=r.required_from,
                required_to=r.required_to,
                work_item_id=r.work_item_id,
                created_at=r.created_at,
            )
            results.append(row)
        return results

    @staticmethod
    async def transition_lifecycle(
        db: AsyncSession, request_id: uuid.UUID, data: RequestTransition, current_user: User
    ) -> OperationalRequest:
        res = await db.execute(select(OperationalRequest).where(OperationalRequest.id == request_id))
        req = res.scalar_one_or_none()
        if not req:
            raise HTTPException(status_code=404, detail="Request not found")

        action = data.action.upper().strip()
        old_status = req.status
        new_status = old_status

        if action == "SUBMIT":
            if old_status not in ["DRAFT", "RETURNED_FOR_CORRECTION"]:
                raise HTTPException(status_code=400, detail=f"Cannot SUBMIT request from state {old_status}")
            new_status = "SUBMITTED"

        elif action == "REVIEW":
            if old_status != "SUBMITTED":
                raise HTTPException(status_code=400, detail=f"Cannot REVIEW request from state {old_status}")
            new_status = "UNDER_REVIEW"

        elif action == "APPROVE":
            if old_status not in ["SUBMITTED", "UNDER_REVIEW"]:
                raise HTTPException(status_code=400, detail=f"Cannot APPROVE request from state {old_status}")
            
            # Separation of Duties check
            if current_user.id == req.requester_id and not current_user.is_superuser:
                raise HTTPException(
                    status_code=409, detail="Separation of Duties violation: cannot approve your own request"
                )

            new_status = "APPROVED"
            req.approver_id = current_user.id
            req.approved_at = datetime.utcnow()
            req.fulfillment_status = "AWAITING_FULFILLMENT"

        elif action == "REJECT":
            if old_status not in ["SUBMITTED", "UNDER_REVIEW"]:
                raise HTTPException(status_code=400, detail=f"Cannot REJECT request from state {old_status}")
            new_status = "REJECTED"
            req.rejection_reason = data.rejection_reason or data.notes

        elif action == "RETURN_FOR_CORRECTION":
            if old_status not in ["SUBMITTED", "UNDER_REVIEW"]:
                raise HTTPException(status_code=400, detail=f"Cannot return request from state {old_status}")
            new_status = "RETURNED_FOR_CORRECTION"

        elif action == "CANCEL":
            if old_status in ["CLOSED", "FULFILLED"]:
                raise HTTPException(status_code=400, detail=f"Cannot cancel completed request")
            new_status = "CANCELLED"
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported action '{action}'")

        req.status = new_status
        await db.commit()
        await db.refresh(req)

        # Record Action Log
        log = RequestActionLog(
            id=uuid.uuid4(),
            request_id=req.id,
            user_id=current_user.id,
            action=action,
            from_status=old_status,
            to_status=new_status,
            notes=data.notes or f"Action {action} performed",
        )
        db.add(log)
        await db.commit()
        return req

    @staticmethod
    async def fulfill_request(
        db: AsyncSession, request_id: uuid.UUID, data: RequestFulfill, current_user: User
    ) -> OperationalRequest:
        res = await db.execute(select(OperationalRequest).where(OperationalRequest.id == request_id))
        req = res.scalar_one_or_none()
        if not req:
            raise HTTPException(status_code=404, detail="Request not found")

        if req.status != "APPROVED" and req.fulfillment_status not in ["AWAITING_FULFILLMENT", "PARTIALLY_FULFILLED"]:
            raise HTTPException(status_code=400, detail="Request must be APPROVED before fulfillment")

        target_fulfill = data.fulfillment_status.upper().strip()
        req.fulfillment_status = target_fulfill

        if target_fulfill in ["FULFILLED", "CLOSED"]:
            req.status = target_fulfill
            req.fulfillment_user_id = current_user.id
            req.fulfilled_at = datetime.utcnow()
        elif target_fulfill == "PARTIALLY_FULFILLED":
            req.status = "APPROVED"

        if data.actual_cost is not None:
            req.actual_cost = data.actual_cost

        await db.commit()
        await db.refresh(req)

        log = RequestActionLog(
            id=uuid.uuid4(),
            request_id=req.id,
            user_id=current_user.id,
            action="FULFILL",
            from_status=req.status,
            to_status=target_fulfill,
            notes=data.notes or f"Fulfillment updated to {target_fulfill}",
        )
        db.add(log)
        await db.commit()
        return req

    @staticmethod
    async def issue_material_items(
        db: AsyncSession, request_id: uuid.UUID, data: MaterialIssueRequest, current_user: User
    ) -> RequestMaterialItem:
        res = await db.execute(
            select(RequestMaterialItem).where(
                RequestMaterialItem.id == data.item_id,
                RequestMaterialItem.request_id == request_id
            )
        )
        item = res.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Material item not found on this request")

        item.quantity_issued += data.quantity
        await db.commit()
        await db.refresh(item)

        # Check total fulfillment status of all items
        req_res = await db.execute(select(OperationalRequest).where(OperationalRequest.id == request_id))
        req = req_res.scalar_one()

        items_res = await db.execute(select(RequestMaterialItem).where(RequestMaterialItem.request_id == request_id))
        all_items = items_res.scalars().all()

        total_req = sum(i.quantity_requested for i in all_items)
        total_issued = sum(i.quantity_issued for i in all_items)

        if total_issued >= total_req:
            req.fulfillment_status = "FULFILLED"
            req.status = "FULFILLED"
            req.fulfillment_user_id = current_user.id
            req.fulfilled_at = datetime.utcnow()
        else:
            req.fulfillment_status = "PARTIALLY_FULFILLED"

        await db.commit()

        log = RequestActionLog(
            id=uuid.uuid4(),
            request_id=request_id,
            user_id=current_user.id,
            action="ISSUE_MATERIAL",
            from_status=req.status,
            to_status=req.fulfillment_status,
            notes=f"Issued {data.quantity} {item.unit} of '{item.material_name}' (Total issued: {item.quantity_issued}/{item.quantity_requested})",
        )
        db.add(log)
        await db.commit()
        return item

    @staticmethod
    async def return_material_items(
        db: AsyncSession, request_id: uuid.UUID, data: MaterialReturnRequest, current_user: User
    ) -> RequestMaterialItem:
        res = await db.execute(
            select(RequestMaterialItem).where(
                RequestMaterialItem.id == data.item_id,
                RequestMaterialItem.request_id == request_id
            )
        )
        item = res.scalar_one_or_none()
        if not item:
            raise HTTPException(status_code=404, detail="Material item not found on this request")

        item.quantity_returned += data.quantity
        await db.commit()
        await db.refresh(item)

        log = RequestActionLog(
            id=uuid.uuid4(),
            request_id=request_id,
            user_id=current_user.id,
            action="RETURN_MATERIAL",
            from_status=None,
            to_status=None,
            notes=f"Returned {data.quantity} {item.unit} of '{item.material_name}' back to store",
        )
        db.add(log)
        await db.commit()
        return item

    @staticmethod
    async def add_comment(
        db: AsyncSession, request_id: uuid.UUID, data: RequestCommentCreate, current_user: User
    ) -> RequestComment:
        res = await db.execute(select(OperationalRequest).where(OperationalRequest.id == request_id))
        req = res.scalar_one_or_none()
        if not req:
            raise HTTPException(status_code=404, detail="Request not found")

        comment = RequestComment(
            id=uuid.uuid4(),
            request_id=req.id,
            user_id=current_user.id,
            comment=data.comment.strip(),
        )
        db.add(comment)
        await db.commit()
        await db.refresh(comment)
        return comment
