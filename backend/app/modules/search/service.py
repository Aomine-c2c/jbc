import uuid
from typing import Any

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authz import AuthzGuard
from app.modules.iam.api import _get_user_permissions
from app.modules.iam.models import Department, User
from app.modules.jobs.models import JobCard
from app.modules.requests.models import OperationalRequest
from app.modules.assets.models import Asset
from app.modules.work.models import WorkItem
from app.modules.contractors.models import ContractorCompany, ContractorWorker
from app.modules.search.schemas import GlobalSearchResponse, SearchGroup, SearchScopeItem


class GlobalSearchService:
    @staticmethod
    def _scope_query_for_user(query, model, current_user: User, *, allow_cross_department: bool = False):
        user_perms = _get_user_permissions(current_user)
        if getattr(current_user, "is_superuser", False) or "global_override" in user_perms:
            return query

        if hasattr(model, "department_id") and current_user.department_id is not None:
            if allow_cross_department:
                return query
            if "job_card:read:cross_department" in user_perms or "request:read:cross_department" in user_perms:
                return query
            query = query.where(model.department_id == current_user.department_id)
            return query

        return query

    @staticmethod
    def _tokenize_query(value: str) -> list[str]:
        tokens = [part.strip() for part in value.replace("OR", " ").replace("|", " ").split() if part.strip()]
        return [token for token in tokens if token]

    @staticmethod
    def _match_score(search: str, title: str | None, reference: str | None, description: str | None) -> float:
        haystacks = [
            title or "",
            reference or "",
            description or "",
        ]
        lowered = search.lower()
        score = 0.0
        if lowered in " ".join(haystacks).lower():
            score += 100
        if reference and lowered in reference.lower():
            score += 80
        if title and lowered in title.lower():
            score += 35
        if description and lowered in description.lower():
            score += 15
        return score

    @staticmethod
    async def _job_results(db: AsyncSession, current_user: User, query: str, limit: int = 8):
        needle = query.strip()
        if not needle:
            return []
        stmt = select(JobCard).where(JobCard.is_deleted.is_(False), JobCard.status.notin_(["CANCELLED", "REJECTED"]))
        stmt = GlobalSearchService._scope_query_for_user(stmt, JobCard, current_user)
        tokens = GlobalSearchService._tokenize_query(needle)
        if tokens:
            clauses = []
            for token in tokens:
                pattern = f"%{token}%"
                clauses.append(
                    or_(
                        JobCard.job_number.ilike(pattern),
                        JobCard.title.ilike(pattern),
                        JobCard.description.ilike(pattern),
                        JobCard.location.ilike(pattern),
                        JobCard.assigned_personnel.ilike(pattern),
                    )
                )
            stmt = stmt.where(or_(*clauses))
        rows = (await db.execute(stmt.order_by(JobCard.priority.desc(), JobCard.created_at.desc()).limit(limit))).scalars().all()
        results = []
        for row in rows:
            score = GlobalSearchService._match_score(needle, row.title, row.job_number, row.description)
            results.append(
                SearchScopeItem(
                    id=row.id,
                    reference=row.job_number or str(row.id),
                    title=row.title,
                    entity="job_cards",
                    entity_label="Job Cards",
                    department_id=row.department_id,
                    department_name=(row.department.name if getattr(row, "department", None) else None),
                    status=row.status,
                    priority=row.priority,
                    url=f"/job-cards/{row.id}",
                    relevance=score,
                    snippet=row.description,
                )
            )
        return sorted(results, key=lambda x: x.relevance, reverse=True)

    @staticmethod
    async def _request_results(db: AsyncSession, current_user: User, query: str, limit: int = 8):
        needle = query.strip()
        if not needle:
            return []
        stmt = select(OperationalRequest).where(OperationalRequest.status.notin_(["CANCELLED", "REJECTED"]))
        stmt = GlobalSearchService._scope_query_for_user(stmt, OperationalRequest, current_user)
        tokens = GlobalSearchService._tokenize_query(needle)
        if tokens:
            clauses = []
            for token in tokens:
                pattern = f"%{token}%"
                clauses.append(
                    or_(
                        OperationalRequest.request_number.ilike(pattern),
                        OperationalRequest.title.ilike(pattern),
                        OperationalRequest.purpose.ilike(pattern),
                        OperationalRequest.location.ilike(pattern),
                    )
                )
            stmt = stmt.where(or_(*clauses))
        rows = (await db.execute(stmt.order_by(OperationalRequest.created_at.desc()).limit(limit))).scalars().all()
        results = []
        for row in rows:
            score = GlobalSearchService._match_score(needle, row.title, row.request_number, row.purpose)
            results.append(
                SearchScopeItem(
                    id=row.id,
                    reference=row.request_number,
                    title=row.title,
                    entity="requests",
                    entity_label="Requests",
                    department_id=row.department_id,
                    department_name=(row.department.name if getattr(row, "department", None) else None),
                    status=row.status,
                    priority=row.priority,
                    url=f"/requests/{row.id}",
                    relevance=score,
                    snippet=row.purpose,
                )
            )
        return sorted(results, key=lambda x: x.relevance, reverse=True)

    @staticmethod
    async def _asset_results(db: AsyncSession, current_user: User, query: str, limit: int = 8):
        needle = query.strip()
        if not needle:
            return []
        stmt = select(Asset).where(Asset.is_archived.is_(False), Asset.status.notin_(["RETIRED", "OUT_OF_SERVICE"]))
        stmt = GlobalSearchService._scope_query_for_user(stmt, Asset, current_user)
        tokens = GlobalSearchService._tokenize_query(needle)
        if tokens:
            clauses = []
            for token in tokens:
                pattern = f"%{token}%"
                clauses.append(
                    or_(
                        Asset.asset_tag.ilike(pattern),
                        Asset.name.ilike(pattern),
                        Asset.serial_number.ilike(pattern),
                        Asset.barcode_or_nfc.ilike(pattern),
                        Asset.location.ilike(pattern),
                    )
                )
            stmt = stmt.where(or_(*clauses))
        rows = (await db.execute(stmt.order_by(Asset.name.asc()).limit(limit))).scalars().all()
        results = []
        for row in rows:
            score = GlobalSearchService._match_score(needle, row.name, row.asset_tag, row.notes)
            results.append(
                SearchScopeItem(
                    id=row.id,
                    reference=row.asset_tag,
                    title=row.name,
                    entity="assets",
                    entity_label="Assets",
                    department_id=row.department_id,
                    department_name=(row.department.name if getattr(row, "department", None) else None),
                    status=row.status,
                    priority=None,
                    url=f"/assets/{row.id}",
                    relevance=score,
                    snippet=row.notes,
                )
            )
        return sorted(results, key=lambda x: x.relevance, reverse=True)

    @staticmethod
    async def _work_results(db: AsyncSession, current_user: User, query: str, limit: int = 8):
        needle = query.strip()
        if not needle:
            return []
        stmt = select(WorkItem).where(WorkItem.status.notin_(["CANCELLED", "REJECTED"]))
        stmt = GlobalSearchService._scope_query_for_user(stmt, WorkItem, current_user)
        tokens = GlobalSearchService._tokenize_query(needle)
        if tokens:
            clauses = []
            for token in tokens:
                pattern = f"%{token}%"
                clauses.append(
                    or_(
                        WorkItem.reference_number.ilike(pattern),
                        WorkItem.title.ilike(pattern),
                        WorkItem.description.ilike(pattern),
                        WorkItem.location.ilike(pattern),
                    )
                )
            stmt = stmt.where(or_(*clauses))
        rows = (await db.execute(stmt.order_by(WorkItem.priority.desc(), WorkItem.created_at.desc()).limit(limit))).scalars().all()
        results = []
        for row in rows:
            score = GlobalSearchService._match_score(needle, row.title, row.reference_number, row.description)
            results.append(
                SearchScopeItem(
                    id=row.id,
                    reference=row.reference_number,
                    title=row.title,
                    entity="work_items",
                    entity_label="Work Items",
                    department_id=row.department_id,
                    department_name=(row.department.name if getattr(row, "department", None) else None),
                    status=row.status,
                    priority=row.priority,
                    url=f"/work-items/{row.id}",
                    relevance=score,
                    snippet=row.description,
                )
            )
        return sorted(results, key=lambda x: x.relevance, reverse=True)

    @staticmethod
    async def _contractor_results(db: AsyncSession, current_user: User, query: str, limit: int = 8):
        needle = query.strip()
        if not needle:
            return []
        stmt = select(ContractorCompany).where(ContractorCompany.is_archived.is_(False))
        tokens = GlobalSearchService._tokenize_query(needle)
        if tokens:
            clauses = []
            for token in tokens:
                pattern = f"%{token}%"
                clauses.append(
                    or_(
                        ContractorCompany.company_code.ilike(pattern),
                        ContractorCompany.name.ilike(pattern),
                        ContractorCompany.registration_number.ilike(pattern),
                    )
                )
            stmt = stmt.where(or_(*clauses))
        rows = (await db.execute(stmt.order_by(ContractorCompany.name.asc()).limit(limit))).scalars().all()
        results = []
        for row in rows:
            score = GlobalSearchService._match_score(needle, row.name, row.company_code, None)
            results.append(
                SearchScopeItem(
                    id=row.id,
                    reference=row.company_code,
                    title=row.name,
                    entity="contractors",
                    entity_label="Contractors",
                    department_id=None,
                    department_name=None,
                    status=row.status,
                    priority=None,
                    url=f"/contractors/companies/{row.id}",
                    relevance=score,
                    snippet=row.registration_number,
                )
            )
        return sorted(results, key=lambda x: x.relevance, reverse=True)

    @staticmethod
    async def _user_results(db: AsyncSession, current_user: User, query: str, limit: int = 8):
        if not getattr(current_user, "is_superuser", False):
            return []
        needle = query.strip()
        if not needle:
            return []
        tokens = GlobalSearchService._tokenize_query(needle)
        if not tokens:
            return []
        stmt = select(User).where(User.is_active.is_(True))
        clauses = []
        for token in tokens:
            pattern = f"%{token}%"
            clauses.append(
                or_(
                    User.email.ilike(pattern),
                    User.first_name.ilike(pattern),
                    User.last_name.ilike(pattern),
                    User.employee_number.ilike(pattern),
                )
            )
        stmt = stmt.where(or_(*clauses))
        rows = (await db.execute(stmt.order_by(User.last_name.asc()).limit(limit))).scalars().all()
        return [
            SearchScopeItem(
                id=row.id,
                reference=row.employee_number or row.email,
                title=f"{row.first_name} {row.last_name}",
                entity="users",
                entity_label="Users",
                department_id=row.department_id,
                department_name=(row.department.name if getattr(row, "department", None) else None),
                status="ACTIVE" if row.is_active else "INACTIVE",
                priority=None,
                url=f"/iam/users/{row.id}",
                relevance=GlobalSearchService._match_score(needle, f"{row.first_name} {row.last_name}", row.employee_number or row.email, row.email),
                snippet=row.email,
            )
            for row in rows
        ]

    @staticmethod
    async def search(db: AsyncSession, current_user: User, query: str, limit: int = 25):
        if not query or not query.strip():
            raise HTTPException(status_code=400, detail="Search query is required.")

        normalized = query.strip()
        groups = []
        all_items = []
        for runner in (
            GlobalSearchService._job_results,
            GlobalSearchService._work_results,
            GlobalSearchService._request_results,
            GlobalSearchService._asset_results,
            GlobalSearchService._contractor_results,
        ):
            items = await runner(db, current_user, normalized, limit=limit)
            all_items.extend(items)
            if items:
                entity_name = items[0].entity
                entity_label = items[0].entity_label
                groups.append(SearchGroup(entity=entity_name, entity_label=entity_label, total=len(items), items=items))

        # keep the direct `User` search only for privileged users and omit it from generic visibility policy.
        if getattr(current_user, "is_superuser", False):
            user_items = await GlobalSearchService._user_results(db, current_user, normalized, limit=limit)
            all_items.extend(user_items)
            if user_items:
                groups.append(SearchGroup(entity="users", entity_label="Users", total=len(user_items), items=user_items))

        ordered = sorted(all_items, key=lambda x: x.relevance, reverse=True)[:limit]
        return GlobalSearchResponse(query=normalized, total=len(ordered), groups=groups)
