import uuid
from datetime import datetime
from typing import List, Optional, Set
from sqlalchemy import select, func, or_, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.modules.iam.models import Location, Site, Organization, User
from app.modules.jobs.models import JobCard
from app.modules.fleet.models import Machine, MachineRequisition
from app.modules.iam.location_schemas import (
    LocationCreate,
    LocationUpdate,
    LocationResponse,
    LocationTreeNode,
    LocationSearchResult,
    LocationMigrationSummary,
)
from app.core.authz import AuthzGuard
from app.modules.audit.service import AuditService


class LocationService:

    @staticmethod
    async def _compute_breadcrumb(db: AsyncSession, name: str, parent_id: Optional[uuid.UUID], site_id: Optional[uuid.UUID]) -> tuple[str, int]:
        """Calculates breadcrumb path string and hierarchy depth level."""
        if parent_id:
            parent_res = await db.execute(select(Location).where(Location.id == parent_id))
            parent = parent_res.scalar_one_or_none()
            if not parent:
                raise HTTPException(status_code=404, detail="Parent location not found")
            level = parent.hierarchy_level + 1
            breadcrumb = f"{parent.breadcrumb} / {name}" if parent.breadcrumb else name
            return breadcrumb, level
        
        # Root level (Facility / Plant or Site level)
        level = 1
        if site_id:
            site_res = await db.execute(select(Site).where(Site.id == site_id))
            site = site_res.scalar_one_or_none()
            if site:
                return f"{site.name} / {name}", level
        
        return name, level

    @staticmethod
    async def _get_all_descendant_ids(db: AsyncSession, root_id: uuid.UUID) -> Set[uuid.UUID]:
        """Recursively gathers all descendant IDs of a location node."""
        descendants: Set[uuid.UUID] = set()
        queue = [root_id]
        
        while queue:
            curr_id = queue.pop(0)
            res = await db.execute(select(Location.id).where(Location.parent_id == curr_id))
            child_ids = res.scalars().all()
            for cid in child_ids:
                if cid not in descendants:
                    descendants.add(cid)
                    queue.append(cid)
        return descendants

    @staticmethod
    async def _recalculate_descendant_breadcrumbs(db: AsyncSession, location: Location):
        """Recursively updates breadcrumb strings of all child nodes after a rename or move."""
        res = await db.execute(select(Location).where(Location.parent_id == location.id))
        children = res.scalars().all()
        
        for child in children:
            child.breadcrumb = f"{location.breadcrumb} / {child.name}"
            child.hierarchy_level = location.hierarchy_level + 1
            if location.site_id:
                child.site_id = location.site_id
            if location.organization_id:
                child.organization_id = location.organization_id
            await LocationService._recalculate_descendant_breadcrumbs(db, child)

    @staticmethod
    async def _count_references(db: AsyncSession, location_id: uuid.UUID) -> int:
        """Counts operational entities referencing this location."""
        jc_count = await db.scalar(select(func.count(JobCard.id)).where(JobCard.location_id == location_id)) or 0
        machine_count = await db.scalar(select(func.count(Machine.id)).where(Machine.location_id == location_id)) or 0
        req_count = await db.scalar(select(func.count(MachineRequisition.id)).where(MachineRequisition.location_id == location_id)) or 0
        return int(jc_count + machine_count + req_count)

    # ── CRUD Operations ──────────────────────────────────────────

    @staticmethod
    async def create_location(db: AsyncSession, data: LocationCreate, current_user: Optional[User] = None) -> Location:
        # Check duplicate code within same parent
        dup_query = select(Location).where(
            Location.code == data.code,
            Location.parent_id == data.parent_id,
            Location.is_archived.is_(False),
        )
        if data.site_id:
            dup_query = dup_query.where(Location.site_id == data.site_id)
        dup_res = await db.execute(dup_query)
        if dup_res.scalar_one_or_none():
            raise HTTPException(status_code=409, detail=f"Location code '{data.code}' already exists in this hierarchy branch")

        breadcrumb, level = await LocationService._compute_breadcrumb(
            db=db, name=data.name, parent_id=data.parent_id, site_id=data.site_id
        )

        site_id = data.site_id
        org_id = data.organization_id

        # Inherit parent site/org if not explicitly set
        if data.parent_id and (not site_id or not org_id):
            p_res = await db.execute(select(Location).where(Location.id == data.parent_id))
            parent = p_res.scalar_one_or_none()
            if parent:
                site_id = site_id or parent.site_id
                org_id = org_id or parent.organization_id

        loc = Location(
            id=uuid.uuid4(),
            organization_id=org_id,
            site_id=site_id,
            parent_id=data.parent_id,
            code=data.code.upper().strip(),
            name=data.name.strip(),
            location_type=data.location_type.upper().strip(),
            description=data.description,
            breadcrumb=breadcrumb,
            hierarchy_level=level,
            gps_coordinates=data.gps_coordinates,
            barcode_or_nfc=data.barcode_or_nfc,
            criticality_rating=data.criticality_rating or "MEDIUM",
            is_active=True,
            is_archived=False,
        )
        db.add(loc)
        await db.commit()
        await db.refresh(loc)

        if current_user:
            await AuditService.log(
                db=db,
                actor=current_user,
                action="LOCATION_CREATE",
                resource="LOCATION",
                resource_id=str(loc.id),
                new_value={"code": loc.code, "name": loc.name, "breadcrumb": loc.breadcrumb, "type": loc.location_type},
                reason=f"Created location {loc.code} ({loc.name})",
            )

        return loc

    @staticmethod
    async def get_location(db: AsyncSession, location_id: uuid.UUID) -> LocationResponse:
        res = await db.execute(select(Location).where(Location.id == location_id))
        loc = res.scalar_one_or_none()
        if not loc:
            raise HTTPException(status_code=404, detail="Location not found")
        
        ref_count = await LocationService._count_references(db, location_id)
        children_count = await db.scalar(select(func.count(Location.id)).where(Location.parent_id == location_id, Location.is_archived.is_(False))) or 0
        
        resp = LocationResponse.model_validate(loc)
        resp.reference_count = ref_count
        resp.children_count = children_count
        return resp

    @staticmethod
    async def update_location(db: AsyncSession, location_id: uuid.UUID, data: LocationUpdate, current_user: Optional[User] = None) -> Location:
        res = await db.execute(select(Location).where(Location.id == location_id))
        loc = res.scalar_one_or_none()
        if not loc:
            raise HTTPException(status_code=404, detail="Location not found")

        old_state = {"name": loc.name, "code": loc.code, "parent_id": str(loc.parent_id) if loc.parent_id else None, "breadcrumb": loc.breadcrumb}
        name_changed = False
        parent_changed = False

        if data.code is not None:
            loc.code = data.code.upper().strip()

        if data.name is not None and data.name.strip() != loc.name:
            loc.name = data.name.strip()
            name_changed = True

        if data.parent_id is not None and data.parent_id != loc.parent_id:
            # Cycle Prevention
            if data.parent_id == location_id:
                raise HTTPException(status_code=400, detail="Cannot set location as its own parent")
            
            descendants = await LocationService._get_all_descendant_ids(db, location_id)
            if data.parent_id in descendants:
                raise HTTPException(status_code=400, detail="Hierarchy cycle detected: cannot set parent to a descendant location")
            
            loc.parent_id = data.parent_id
            parent_changed = True

        if data.location_type is not None:
            loc.location_type = data.location_type.upper().strip()
        if data.description is not None:
            loc.description = data.description
        if data.gps_coordinates is not None:
            loc.gps_coordinates = data.gps_coordinates
        if data.barcode_or_nfc is not None:
            loc.barcode_or_nfc = data.barcode_or_nfc
        if data.criticality_rating is not None:
            loc.criticality_rating = data.criticality_rating
        if data.is_active is not None:
            loc.is_active = data.is_active

        # Recalculate breadcrumbs if name or parent changed
        if name_changed or parent_changed:
            breadcrumb, level = await LocationService._compute_breadcrumb(
                db=db, name=loc.name, parent_id=loc.parent_id, site_id=loc.site_id
            )
            loc.breadcrumb = breadcrumb
            loc.hierarchy_level = level
            await LocationService._recalculate_descendant_breadcrumbs(db, loc)

        await db.commit()
        await db.refresh(loc)

        if current_user:
            await AuditService.log(
                db=db,
                actor=current_user,
                action="LOCATION_UPDATE",
                resource="LOCATION",
                resource_id=str(loc.id),
                previous_value=old_state,
                new_value={"name": loc.name, "code": loc.code, "parent_id": str(loc.parent_id) if loc.parent_id else None, "breadcrumb": loc.breadcrumb},
                reason=f"Updated location {loc.code}",
            )

        return loc

    @staticmethod
    async def list_locations(
        db: AsyncSession,
        site_id: Optional[uuid.UUID] = None,
        parent_id: Optional[uuid.UUID] = None,
        location_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        include_archived: bool = False,
    ) -> List[LocationResponse]:
        query = select(Location)
        if not include_archived:
            query = query.where(Location.is_archived.is_(False))
        if site_id:
            query = query.where(Location.site_id == site_id)
        if parent_id is not None:
            query = query.where(Location.parent_id == parent_id)
        if location_type:
            query = query.where(Location.location_type == location_type.upper())
        if is_active is not None:
            query = query.where(Location.is_active == is_active)

        query = query.order_by(Location.hierarchy_level.asc(), Location.name.asc())
        res = await db.execute(query)
        locations = res.scalars().all()

        results = []
        for loc in locations:
            resp = LocationResponse.model_validate(loc)
            resp.reference_count = await LocationService._count_references(db, loc.id)
            results.append(resp)
        return results

    @staticmethod
    async def search_locations(
        db: AsyncSession,
        query_str: str,
        location_type: Optional[str] = None,
        site_id: Optional[uuid.UUID] = None,
        limit: int = 25,
    ) -> List[LocationSearchResult]:
        """Fast typeahead and operational search across codes, names, barcodes, and breadcrumbs."""
        search_pattern = f"%{query_str.strip()}%"
        stmt = select(Location).where(
            Location.is_archived.is_(False),
            or_(
                Location.name.ilike(search_pattern),
                Location.code.ilike(search_pattern),
                Location.breadcrumb.ilike(search_pattern),
                Location.barcode_or_nfc.ilike(search_pattern),
            )
        )
        if site_id:
            stmt = stmt.where(Location.site_id == site_id)
        if location_type:
            stmt = stmt.where(Location.location_type == location_type.upper())

        stmt = stmt.order_by(Location.hierarchy_level.asc(), Location.name.asc()).limit(limit)
        res = await db.execute(stmt)
        locations = res.scalars().all()

        results = []
        for loc in locations:
            site_name = loc.site.name if loc.site else None
            results.append(
                LocationSearchResult(
                    id=loc.id,
                    code=loc.code,
                    name=loc.name,
                    location_type=loc.location_type,
                    breadcrumb=loc.breadcrumb,
                    hierarchy_level=loc.hierarchy_level,
                    site_name=site_name,
                    is_active=loc.is_active,
                    barcode_or_nfc=loc.barcode_or_nfc,
                )
            )
        return results

    @staticmethod
    async def get_hierarchy_tree(db: AsyncSession, site_id: Optional[uuid.UUID] = None, include_archived: bool = False) -> List[LocationTreeNode]:
        """Returns recursive nested hierarchy tree structure."""
        query = select(Location)
        if not include_archived:
            query = query.where(Location.is_archived.is_(False))
        if site_id:
            query = query.where(Location.site_id == site_id)
        query = query.order_by(Location.hierarchy_level.asc(), Location.name.asc())
        
        res = await db.execute(query)
        all_locs = res.scalars().all()

        # Build lookup table
        node_map = {}
        for loc in all_locs:
            node_map[loc.id] = LocationTreeNode(
                id=loc.id,
                code=loc.code,
                name=loc.name,
                location_type=loc.location_type,
                breadcrumb=loc.breadcrumb,
                hierarchy_level=loc.hierarchy_level,
                is_active=loc.is_active,
                is_archived=loc.is_archived,
                gps_coordinates=loc.gps_coordinates,
                barcode_or_nfc=loc.barcode_or_nfc,
                criticality_rating=loc.criticality_rating,
                children=[],
                reference_count=0,
            )

        roots = []
        for loc in all_locs:
            node = node_map[loc.id]
            if loc.parent_id and loc.parent_id in node_map:
                node_map[loc.parent_id].children.append(node)
            else:
                roots.append(node)

        return roots

    @staticmethod
    async def archive_location(db: AsyncSession, location_id: uuid.UUID, reason: Optional[str] = None, current_user: Optional[User] = None) -> Location:
        res = await db.execute(select(Location).where(Location.id == location_id))
        loc = res.scalar_one_or_none()
        if not loc:
            raise HTTPException(status_code=404, detail="Location not found")

        loc.is_archived = True
        loc.is_active = False
        loc.archived_at = datetime.utcnow()
        loc.archived_reason = reason or "Archived by administrator"

        await db.commit()
        await db.refresh(loc)

        if current_user:
            await AuditService.log(
                db=db,
                actor=current_user,
                action="LOCATION_ARCHIVE",
                resource="LOCATION",
                resource_id=str(loc.id),
                reason=reason or "Location archived",
            )
        return loc

    @staticmethod
    async def restore_location(db: AsyncSession, location_id: uuid.UUID, current_user: Optional[User] = None) -> Location:
        res = await db.execute(select(Location).where(Location.id == location_id))
        loc = res.scalar_one_or_none()
        if not loc:
            raise HTTPException(status_code=404, detail="Location not found")

        loc.is_archived = False
        loc.is_active = True
        loc.archived_at = None
        loc.archived_reason = None

        await db.commit()
        await db.refresh(loc)

        if current_user:
            await AuditService.log(
                db=db,
                actor=current_user,
                action="LOCATION_RESTORE",
                resource="LOCATION",
                resource_id=str(loc.id),
                reason="Location restored from archive",
            )
        return loc

    @staticmethod
    async def delete_location(db: AsyncSession, location_id: uuid.UUID, current_user: Optional[User] = None):
        """Prevents hard deletion if location has child locations or active operational references."""
        res = await db.execute(select(Location).where(Location.id == location_id))
        loc = res.scalar_one_or_none()
        if not loc:
            raise HTTPException(status_code=404, detail="Location not found")

        # 1. Check for child nodes
        child_count = await db.scalar(select(func.count(Location.id)).where(Location.parent_id == location_id)) or 0
        if child_count > 0:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot delete location '{loc.name}' because it contains {child_count} child location(s). Archive or reassign children first.",
            )

        # 2. Check operational references (Job Cards, Assets, Requisitions)
        ref_count = await LocationService._count_references(db, location_id)
        if ref_count > 0:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot delete location '{loc.name}' because it is actively referenced by {ref_count} operational record(s). Use Archive/Deactivate instead to preserve historical integrity.",
            )

        await db.delete(loc)
        await db.commit()

        if current_user:
            await AuditService.log(
                db=db,
                actor=current_user,
                action="LOCATION_DELETE",
                resource="LOCATION",
                resource_id=str(location_id),
                reason=f"Deleted unused location {loc.code}",
            )

    @staticmethod
    async def migrate_text_locations(db: AsyncSession, default_site_id: Optional[uuid.UUID] = None) -> LocationMigrationSummary:
        """
        Scans existing records (Job Cards, Machines, Requisitions) with string location fields.
        Maps them into the new Location hierarchy without destroying historical text data.
        """
        summary = LocationMigrationSummary()

        # Ensure default site if none provided
        if not default_site_id:
            site_res = await db.execute(select(Site).limit(1))
            site = site_res.scalar_one_or_none()
            default_site_id = site.id if site else None

        # 1. Job Cards
        jc_res = await db.execute(select(JobCard).where(JobCard.location_id.is_(None), JobCard.location.is_not(None)))
        job_cards = jc_res.scalars().all()
        summary.scanned_job_cards = len(job_cards)

        location_cache = {}

        for jc in job_cards:
            loc_text = (jc.location or "").strip()
            if not loc_text:
                continue

            if loc_text not in location_cache:
                # Check if matching location exists
                existing = await db.execute(select(Location).where(or_(Location.name == loc_text, Location.code == loc_text)))
                match = existing.scalar_one_or_none()
                if not match:
                    # Auto-provision location node
                    clean_code = "".join(c for c in loc_text.upper() if c.isalnum() or c in "_-")[:50] or f"LOC-{uuid.uuid4().hex[:6].upper()}"
                    match = Location(
                        id=uuid.uuid4(),
                        site_id=default_site_id,
                        code=clean_code,
                        name=loc_text,
                        location_type="AREA",
                        breadcrumb=loc_text,
                        hierarchy_level=1,
                        is_active=True,
                        is_archived=False,
                    )
                    db.add(match)
                    await db.commit()
                    await db.refresh(match)
                    summary.created_locations += 1
                    summary.details.append(f"Auto-created location '{loc_text}' (Code: {clean_code}) from Job Card {jc.job_number or jc.id}")
                else:
                    summary.matched_locations += 1

                location_cache[loc_text] = match.id

            jc.location_id = location_cache[loc_text]

        # 2. Machines
        m_res = await db.execute(select(Machine).where(Machine.location_id.is_(None), Machine.location.is_not(None)))
        machines = m_res.scalars().all()
        summary.scanned_machines = len(machines)

        for m in machines:
            loc_text = (m.location or "").strip()
            if not loc_text:
                continue

            if loc_text not in location_cache:
                existing = await db.execute(select(Location).where(or_(Location.name == loc_text, Location.code == loc_text)))
                match = existing.scalar_one_or_none()
                if not match:
                    clean_code = "".join(c for c in loc_text.upper() if c.isalnum() or c in "_-")[:50] or f"LOC-{uuid.uuid4().hex[:6].upper()}"
                    match = Location(
                        id=uuid.uuid4(),
                        site_id=default_site_id,
                        code=clean_code,
                        name=loc_text,
                        location_type="WORK_CENTER",
                        breadcrumb=loc_text,
                        hierarchy_level=1,
                        is_active=True,
                        is_archived=False,
                    )
                    db.add(match)
                    await db.commit()
                    await db.refresh(match)
                    summary.created_locations += 1
                    summary.details.append(f"Auto-created location '{loc_text}' for Machine {m.identifier}")
                else:
                    summary.matched_locations += 1

                location_cache[loc_text] = match.id

            m.location_id = location_cache[loc_text]

        # 3. Machine Requisitions
        req_res = await db.execute(select(MachineRequisition).where(MachineRequisition.location_id.is_(None), MachineRequisition.location.is_not(None)))
        requisitions = req_res.scalars().all()
        summary.scanned_requisitions = len(requisitions)

        for r in requisitions:
            loc_text = (r.location or "").strip()
            if not loc_text:
                continue

            if loc_text in location_cache:
                r.location_id = location_cache[loc_text]
                summary.matched_locations += 1

        await db.commit()
        return summary
