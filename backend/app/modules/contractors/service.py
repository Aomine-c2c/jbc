import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.modules.contractors.models import (
    ContractorCompany,
    ContractorWorker,
    ContractorAssignment,
    ContractorWorkerAssignment,
    ContractorDocument,
    ContractorCompanyStatus,
    ContractorWorkerStatus,
    ContractorVerificationStatus,
)
from app.modules.contractors.schemas import (
    ContractorCompanyCreate,
    ContractorCompanyUpdate,
    ContractorCompanyResponse,
    ContractorCompanyListResponse,
    ContractorWorkerCreate,
    ContractorWorkerUpdate,
    ContractorWorkerResponse,
    ContractorWorkerListResponse,
    ContractorAssignmentCreate,
    ContractorAssignmentVerify,
    ContractorAssignmentResponse,
    ContractorAssignmentListResponse,
    ContractorDocumentCreate,
    ContractorDocumentResponse,
)
from app.modules.iam.models import User
from app.modules.work.models import WorkItem
from app.modules.jobs.models import JobCard
from app.modules.audit.service import AuditService


class ContractorService:

    @staticmethod
    def _generate_company_code() -> str:
        year = datetime.utcnow().year
        short_id = uuid.uuid4().hex[:6].upper()
        return f"CON-{year}-{short_id}"

    @staticmethod
    def _generate_worker_code() -> str:
        year = datetime.utcnow().year
        short_id = uuid.uuid4().hex[:6].upper()
        return f"CW-{year}-{short_id}"

    @staticmethod
    def _generate_assignment_number() -> str:
        year = datetime.utcnow().year
        short_id = uuid.uuid4().hex[:6].upper()
        return f"CAS-{year}-{short_id}"

    # ── Contractor Company Operations ────────────────────────────

    @staticmethod
    async def create_company(
        db: AsyncSession, data: ContractorCompanyCreate, current_user: User
    ) -> ContractorCompany:
        code = data.company_code.strip() if data.company_code else ContractorService._generate_company_code()

        existing = await db.execute(
            select(ContractorCompany).where(ContractorCompany.company_code == code)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail=f"Company code '{code}' already exists")

        company = ContractorCompany(
            id=uuid.uuid4(),
            company_code=code,
            name=data.name.strip(),
            registration_number=data.registration_number.strip() if data.registration_number else None,
            primary_contact_name=data.primary_contact_name.strip() if data.primary_contact_name else None,
            contact_email=data.contact_email.strip() if data.contact_email else None,
            contact_phone=data.contact_phone.strip() if data.contact_phone else None,
            service_categories=data.service_categories or [],
            status=data.status or "ACTIVE",
            safety_induction_valid_until=data.safety_induction_valid_until,
            notes=data.notes,
        )
        db.add(company)
        await db.commit()
        await db.refresh(company)

        try:
            await AuditService.log_event(
                db=db,
                user=current_user,
                action="CONTRACTOR_COMPANY_CREATE",
                resource="CONTRACTOR_COMPANY",
                resource_id=str(company.id),
                new_value={"code": company.company_code, "name": company.name},
                reason=f"Registered contractor company {company.name}",
            )
        except Exception:
            pass

        return company

    @staticmethod
    async def update_company(
        db: AsyncSession, company_id: uuid.UUID, data: ContractorCompanyUpdate, current_user: User
    ) -> ContractorCompany:
        res = await db.execute(select(ContractorCompany).where(ContractorCompany.id == company_id))
        company = res.scalar_one_or_none()
        if not company:
            raise HTTPException(status_code=404, detail="Contractor company not found")

        if data.name is not None:
            company.name = data.name.strip()
        if data.registration_number is not None:
            company.registration_number = data.registration_number.strip()
        if data.primary_contact_name is not None:
            company.primary_contact_name = data.primary_contact_name.strip()
        if data.contact_email is not None:
            company.contact_email = data.contact_email.strip()
        if data.contact_phone is not None:
            company.contact_phone = data.contact_phone.strip()
        if data.service_categories is not None:
            company.service_categories = data.service_categories
        if data.status is not None:
            company.status = data.status
        if data.safety_induction_valid_until is not None:
            company.safety_induction_valid_until = data.safety_induction_valid_until
        if data.notes is not None:
            company.notes = data.notes

        await db.commit()
        await db.refresh(company)
        return company

    @staticmethod
    async def archive_company(
        db: AsyncSession, company_id: uuid.UUID, reason: Optional[str], current_user: User
    ) -> ContractorCompany:
        res = await db.execute(select(ContractorCompany).where(ContractorCompany.id == company_id))
        company = res.scalar_one_or_none()
        if not company:
            raise HTTPException(status_code=404, detail="Contractor company not found")

        company.is_archived = True
        company.archived_at = datetime.utcnow()
        company.archived_reason = reason
        company.status = "INACTIVE"
        await db.commit()
        await db.refresh(company)
        return company

    @staticmethod
    async def get_company(
        db: AsyncSession, company_id: uuid.UUID, current_user: User
    ) -> ContractorCompanyResponse:
        res = await db.execute(select(ContractorCompany).where(ContractorCompany.id == company_id))
        company = res.scalar_one_or_none()
        if not company:
            raise HTTPException(status_code=404, detail="Contractor company not found")

        w_count_res = await db.execute(
            select(func.count(ContractorWorker.id)).where(ContractorWorker.contractor_company_id == company.id)
        )
        w_count = w_count_res.scalar() or 0

        a_count_res = await db.execute(
            select(func.count(ContractorAssignment.id)).where(ContractorAssignment.contractor_company_id == company.id)
        )
        a_count = a_count_res.scalar() or 0

        resp = ContractorCompanyResponse.model_validate(company)
        resp.worker_count = w_count
        resp.assignment_count = a_count
        return resp

    @staticmethod
    async def list_companies(
        db: AsyncSession,
        current_user: User,
        status: Optional[str] = None,
        include_archived: bool = False,
        search_query: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ContractorCompanyListResponse]:
        query = select(ContractorCompany)
        if not include_archived:
            query = query.where(ContractorCompany.is_archived == False)
        if status:
            query = query.where(ContractorCompany.status == status.upper().strip())
        if search_query:
            p = f"%{search_query.strip()}%"
            query = query.where(
                or_(
                    ContractorCompany.company_code.ilike(p),
                    ContractorCompany.name.ilike(p),
                    ContractorCompany.primary_contact_name.ilike(p),
                    ContractorCompany.contact_email.ilike(p),
                )
            )

        query = query.order_by(ContractorCompany.name.asc()).limit(limit).offset(offset)
        res = await db.execute(query)
        companies = res.scalars().all()

        results = []
        for c in companies:
            row = ContractorCompanyListResponse(
                id=c.id,
                company_code=c.company_code,
                name=c.name,
                primary_contact_name=c.primary_contact_name,
                contact_phone=c.contact_phone,
                service_categories=c.service_categories or [],
                status=c.status,
                safety_induction_valid_until=c.safety_induction_valid_until,
                worker_count=len(c.workers),
                is_archived=c.is_archived,
                created_at=c.created_at,
            )
            results.append(row)
        return results

    # ── Contractor Worker Operations ─────────────────────────────

    @staticmethod
    async def create_worker(
        db: AsyncSession, data: ContractorWorkerCreate, current_user: User
    ) -> ContractorWorker:
        c_res = await db.execute(select(ContractorCompany).where(ContractorCompany.id == data.contractor_company_id))
        company = c_res.scalar_one_or_none()
        if not company:
            raise HTTPException(status_code=404, detail="Contractor company not found")

        code = data.worker_code.strip() if data.worker_code else ContractorService._generate_worker_code()

        worker = ContractorWorker(
            id=uuid.uuid4(),
            contractor_company_id=data.contractor_company_id,
            worker_code=code,
            full_name=data.full_name.strip(),
            skill_or_role=data.skill_or_role.strip(),
            certification_records=data.certification_records or [],
            certification_expiry=data.certification_expiry,
            status=data.status or "ACTIVE",
            phone_number=data.phone_number.strip() if data.phone_number else None,
            badge_number=data.badge_number.strip() if data.badge_number else None,
            notes=data.notes,
        )
        db.add(worker)
        await db.commit()
        await db.refresh(worker)
        return worker

    @staticmethod
    async def list_workers(
        db: AsyncSession,
        current_user: User,
        company_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        skill: Optional[str] = None,
        search_query: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ContractorWorkerListResponse]:
        query = select(ContractorWorker)
        if company_id:
            query = query.where(ContractorWorker.contractor_company_id == company_id)
        if status:
            query = query.where(ContractorWorker.status == status.upper().strip())
        if skill:
            query = query.where(ContractorWorker.skill_or_role.ilike(f"%{skill.strip()}%"))
        if search_query:
            p = f"%{search_query.strip()}%"
            query = query.where(
                or_(
                    ContractorWorker.worker_code.ilike(p),
                    ContractorWorker.full_name.ilike(p),
                    ContractorWorker.skill_or_role.ilike(p),
                    ContractorWorker.badge_number.ilike(p),
                )
            )

        query = query.order_by(ContractorWorker.full_name.asc()).limit(limit).offset(offset)
        res = await db.execute(query)
        workers = res.scalars().all()

        results = []
        for w in workers:
            row = ContractorWorkerListResponse(
                id=w.id,
                worker_code=w.worker_code,
                full_name=w.full_name,
                skill_or_role=w.skill_or_role,
                company_name=w.company.name if w.company else None,
                status=w.status,
                certification_expiry=w.certification_expiry,
                phone_number=w.phone_number,
                badge_number=w.badge_number,
                created_at=w.created_at,
            )
            results.append(row)
        return results

    # ── Contractor Work Assignment Operations ────────────────────

    @staticmethod
    async def create_assignment(
        db: AsyncSession, data: ContractorAssignmentCreate, current_user: User
    ) -> ContractorAssignment:
        c_res = await db.execute(select(ContractorCompany).where(ContractorCompany.id == data.contractor_company_id))
        company = c_res.scalar_one_or_none()
        if not company:
            raise HTTPException(status_code=404, detail="Contractor company not found")

        assignment_num = ContractorService._generate_assignment_number()

        assignment = ContractorAssignment(
            id=uuid.uuid4(),
            assignment_number=assignment_num,
            contractor_company_id=data.contractor_company_id,
            work_item_id=data.work_item_id,
            job_card_id=data.job_card_id,
            work_scope=data.work_scope.strip(),
            assignment_date=datetime.utcnow(),
            start_date=data.start_date,
            completion_date=data.completion_date,
            supervisor_id=current_user.id,
            verification_status="PENDING",
            cost_agreed=data.cost_agreed or 0.0,
            actual_cost=0.0,
        )
        db.add(assignment)

        # Link specific workers if supplied
        if data.worker_ids:
            for w_id in data.worker_ids:
                w_link = ContractorWorkerAssignment(
                    id=uuid.uuid4(),
                    assignment_id=assignment.id,
                    contractor_worker_id=w_id,
                )
                db.add(w_link)

        await db.commit()
        await db.refresh(assignment)
        return assignment

    @staticmethod
    async def verify_assignment(
        db: AsyncSession, assignment_id: uuid.UUID, data: ContractorAssignmentVerify, current_user: User
    ) -> ContractorAssignment:
        res = await db.execute(select(ContractorAssignment).where(ContractorAssignment.id == assignment_id))
        assignment = res.scalar_one_or_none()
        if not assignment:
            raise HTTPException(status_code=404, detail="Contractor assignment not found")

        assignment.verification_status = data.verification_status
        assignment.verified_by_id = current_user.id
        assignment.verified_at = datetime.utcnow()
        if data.performance_rating is not None:
            assignment.performance_rating = data.performance_rating
        if data.performance_notes is not None:
            assignment.performance_notes = data.performance_notes
        if data.actual_cost is not None:
            assignment.actual_cost = data.actual_cost

        await db.commit()
        await db.refresh(assignment)
        return assignment

    @staticmethod
    async def get_assignment(
        db: AsyncSession, assignment_id: uuid.UUID, current_user: User
    ) -> ContractorAssignmentResponse:
        res = await db.execute(select(ContractorAssignment).where(ContractorAssignment.id == assignment_id))
        assignment = res.scalar_one_or_none()
        if not assignment:
            raise HTTPException(status_code=404, detail="Contractor assignment not found")

        resp = ContractorAssignmentResponse.model_validate(assignment)
        resp.company_name = assignment.company.name if assignment.company else None
        resp.work_item_reference = assignment.work_item.reference_number if assignment.work_item else None
        resp.supervisor_name = f"{assignment.supervisor.first_name} {assignment.supervisor.last_name}" if assignment.supervisor else None
        resp.verified_by_name = f"{assignment.verified_by.first_name} {assignment.verified_by.last_name}" if assignment.verified_by else None

        resp.assigned_workers = [
            ContractorWorkerListResponse(
                id=w_link.worker.id,
                worker_code=w_link.worker.worker_code,
                full_name=w_link.worker.full_name,
                skill_or_role=w_link.worker.skill_or_role,
                company_name=assignment.company.name if assignment.company else None,
                status=w_link.worker.status,
                certification_expiry=w_link.worker.certification_expiry,
                phone_number=w_link.worker.phone_number,
                badge_number=w_link.worker.badge_number,
                created_at=w_link.worker.created_at,
            )
            for w_link in assignment.assigned_workers
            if w_link.worker
        ]
        return resp

    @staticmethod
    async def list_assignments(
        db: AsyncSession,
        current_user: User,
        company_id: Optional[uuid.UUID] = None,
        work_item_id: Optional[uuid.UUID] = None,
        verification_status: Optional[str] = None,
        search_query: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ContractorAssignmentListResponse]:
        query = select(ContractorAssignment)
        if company_id:
            query = query.where(ContractorAssignment.contractor_company_id == company_id)
        if work_item_id:
            query = query.where(ContractorAssignment.work_item_id == work_item_id)
        if verification_status:
            query = query.where(ContractorAssignment.verification_status == verification_status.upper().strip())

        if search_query:
            p = f"%{search_query.strip()}%"
            query = query.where(
                or_(
                    ContractorAssignment.assignment_number.ilike(p),
                    ContractorAssignment.work_scope.ilike(p),
                )
            )

        query = query.order_by(ContractorAssignment.created_at.desc()).limit(limit).offset(offset)
        res = await db.execute(query)
        assignments = res.scalars().all()

        results = []
        for a in assignments:
            row = ContractorAssignmentListResponse(
                id=a.id,
                assignment_number=a.assignment_number,
                company_name=a.company.name if a.company else "Unknown Company",
                work_scope=a.work_scope,
                verification_status=a.verification_status,
                supervisor_name=f"{a.supervisor.first_name} {a.supervisor.last_name}" if a.supervisor else None,
                performance_rating=a.performance_rating,
                assignment_date=a.assignment_date,
                start_date=a.start_date,
                completion_date=a.completion_date,
                work_item_reference=a.work_item.reference_number if a.work_item else None,
            )
            results.append(row)
        return results
