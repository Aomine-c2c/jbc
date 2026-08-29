import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status

from app.modules.iam.models import (
    Organization,
    Site,
    Department,
    Section,
    Team,
    Position,
    User,
    UserRole,
    Role,
)
from app.modules.iam.org_schemas import (
    OrganizationCreate,
    OrganizationUpdate,
    SiteCreate,
    SiteUpdate,
    SectionCreate,
    SectionUpdate,
    TeamCreate,
    TeamUpdate,
    PositionCreate,
    PositionUpdate,
    UserPlacementUpdate,
    ChainOfCommandResponse,
    ChainOfCommandStep,
    OrganizationHierarchyTree,
    SiteNode,
    DepartmentNode,
    SectionNode,
    TeamNode,
    MemberNode,
)


class OrgService:

    @staticmethod
    async def ensure_default_org_and_site(db: AsyncSession) -> tuple[Organization, Site]:
        """
        Idempotently creates the default Organization and Site records if none exist,
        and links unassigned departments.
        """
        # 1. Organization
        result = await db.execute(select(Organization).limit(1))
        org = result.scalar_one_or_none()
        if not org:
            org = Organization(
                id=uuid.uuid4(),
                code="BIKITA_MINERALS",
                name="Bikita Minerals (Pvt) Ltd",
                description="Lithium & Tantalite Mining and Processing Operations",
                industry_type="Mining & Mineral Processing",
                country="Zimbabwe",
                currency="USD",
                is_active=True,
            )
            db.add(org)
            await db.commit()
            await db.refresh(org)

        # 2. Site
        result = await db.execute(select(Site).where(Site.organization_id == org.id).limit(1))
        site = result.scalar_one_or_none()
        if not site:
            site = Site(
                id=uuid.uuid4(),
                organization_id=org.id,
                code="BIKITA_MINE_SITE",
                name="Bikita Mine Site & Processing Plant",
                site_type="MINE_SITE",
                address="Bikita District, Masvingo Province, Zimbabwe",
                is_active=True,
            )
            db.add(site)
            await db.commit()
            await db.refresh(site)

        # 3. Associate any unlinked departments to default site
        await db.execute(
            update(Department)
            .where(Department.site_id.is_(None))
            .values(site_id=site.id)
        )
        await db.commit()

        return org, site

    # ── Organizations ──────────────────────────────────────────

    @staticmethod
    async def list_organizations(db: AsyncSession) -> List[Organization]:
        result = await db.execute(select(Organization).order_by(Organization.name.asc()))
        return list(result.scalars().all())

    @staticmethod
    async def create_organization(db: AsyncSession, data: OrganizationCreate) -> Organization:
        existing = await db.execute(select(Organization).where(Organization.code == data.code))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail=f"Organization with code '{data.code}' already exists.")
        
        org = Organization(**data.model_dump())
        db.add(org)
        await db.commit()
        await db.refresh(org)
        return org

    # ── Sites ──────────────────────────────────────────────────

    @staticmethod
    async def list_sites(db: AsyncSession, org_id: Optional[uuid.UUID] = None) -> List[Site]:
        query = select(Site)
        if org_id:
            query = query.where(Site.organization_id == org_id)
        query = query.order_by(Site.name.asc())
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def create_site(db: AsyncSession, data: SiteCreate) -> Site:
        existing = await db.execute(select(Site).where(Site.code == data.code))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail=f"Site with code '{data.code}' already exists.")
        
        site = Site(**data.model_dump())
        db.add(site)
        await db.commit()
        await db.refresh(site)
        return site

    # ── Sections ───────────────────────────────────────────────

    @staticmethod
    async def list_sections(db: AsyncSession, dept_id: Optional[uuid.UUID] = None) -> List[Section]:
        query = select(Section)
        if dept_id:
            query = query.where(Section.department_id == dept_id)
        query = query.order_by(Section.name.asc())
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def create_section(db: AsyncSession, data: SectionCreate) -> Section:
        section = Section(**data.model_dump())
        db.add(section)
        await db.commit()
        await db.refresh(section)
        return section

    # ── Teams ──────────────────────────────────────────────────

    @staticmethod
    async def list_teams(db: AsyncSession, section_id: Optional[uuid.UUID] = None) -> List[Team]:
        query = select(Team)
        if section_id:
            query = query.where(Team.section_id == section_id)
        query = query.order_by(Team.name.asc())
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def create_team(db: AsyncSession, data: TeamCreate) -> Team:
        team = Team(**data.model_dump())
        db.add(team)
        await db.commit()
        await db.refresh(team)
        return team

    # ── Positions ──────────────────────────────────────────────

    @staticmethod
    async def list_positions(db: AsyncSession, dept_id: Optional[uuid.UUID] = None) -> List[Position]:
        query = select(Position)
        if dept_id:
            query = query.where(Position.department_id == dept_id)
        query = query.order_by(Position.title.asc())
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def create_position(db: AsyncSession, data: PositionCreate) -> Position:
        existing = await db.execute(select(Position).where(Position.code == data.code))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail=f"Position code '{data.code}' already exists.")
        
        pos = Position(**data.model_dump())
        db.add(pos)
        await db.commit()
        await db.refresh(pos)
        return pos

    # ── User Placement & Hierarchy ─────────────────────────────

    @staticmethod
    async def update_user_placement(
        db: AsyncSession,
        user_id: uuid.UUID,
        data: UserPlacementUpdate,
    ) -> User:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        # Prevent circular supervisor assignment
        if data.supervisor_id and data.supervisor_id == user_id:
            raise HTTPException(status_code=400, detail="A user cannot be their own supervisor.")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)

        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def get_user_chain_of_command(
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> ChainOfCommandResponse:
        """
        Traverses upward through the supervisor relationship to resolve
        the complete escalation and reporting hierarchy.
        """
        result = await db.execute(select(User).where(User.id == user_id))
        target_user = result.scalar_one_or_none()
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found.")

        chain: List[ChainOfCommandStep] = []
        visited = set()
        curr_user = target_user
        level = 1

        while curr_user.supervisor_id and curr_user.supervisor_id not in visited:
            visited.add(curr_user.id)
            sup_res = await db.execute(select(User).where(User.id == curr_user.supervisor_id))
            supervisor = sup_res.scalar_one_or_none()
            if not supervisor:
                break

            # Fetch position title
            pos_title = None
            if supervisor.position_id:
                pos_res = await db.execute(select(Position).where(Position.id == supervisor.position_id))
                pos = pos_res.scalar_one_or_none()
                if pos:
                    pos_title = pos.title

            # Fetch department name
            dept_name = None
            if supervisor.department_id:
                dept_res = await db.execute(select(Department).where(Department.id == supervisor.department_id))
                dept = dept_res.scalar_one_or_none()
                if dept:
                    dept_name = dept.name

            # Primary role name
            role_res = await db.execute(
                select(Role.name)
                .join(UserRole, UserRole.role_id == Role.id)
                .where(UserRole.user_id == supervisor.id)
                .limit(1)
            )
            role_name = role_res.scalar_one_or_none() or "USER"

            chain.append(
                ChainOfCommandStep(
                    level=level,
                    user_id=supervisor.id,
                    name=f"{supervisor.first_name} {supervisor.last_name}",
                    email=supervisor.email,
                    position_title=pos_title,
                    department_name=dept_name,
                    role=role_name,
                )
            )
            curr_user = supervisor
            level += 1

        return ChainOfCommandResponse(
            target_user_id=target_user.id,
            target_user_name=f"{target_user.first_name} {target_user.last_name}",
            chain=chain,
        )

    @staticmethod
    async def get_organization_hierarchy_tree(
        db: AsyncSession,
    ) -> OrganizationHierarchyTree:
        """
        Assembles the comprehensive multi-tier organizational tree:
        Organization -> Sites -> Departments -> Sections -> Teams -> Members.
        """
        org, _ = await OrgService.ensure_default_org_and_site(db)

        # Load all users with roles and positions
        users_res = await db.execute(select(User).where(User.is_active == True))
        all_users = users_res.scalars().all()

        user_roles_map = {}
        for u in all_users:
            r_res = await db.execute(
                select(Role.name).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == u.id)
            )
            user_roles_map[u.id] = list(r_res.scalars().all())

        positions_res = await db.execute(select(Position))
        positions_map = {p.id: p.title for p in positions_res.scalars().all()}

        def make_member_node(u: User) -> MemberNode:
            return MemberNode(
                id=str(u.id),
                name=f"{u.first_name} {u.last_name}",
                email=u.email,
                position_title=positions_map.get(u.position_id) if u.position_id else None,
                roles=user_roles_map.get(u.id, []),
                shift_pattern=u.shift_pattern,
                supervisor_id=str(u.supervisor_id) if u.supervisor_id else None,
            )

        # Load sites for org
        sites_res = await db.execute(select(Site).where(Site.organization_id == org.id))
        sites = sites_res.scalars().all()

        site_nodes = []
        for s in sites:
            # Departments under site
            dept_res = await db.execute(select(Department).where(Department.site_id == s.id))
            depts = dept_res.scalars().all()

            dept_nodes = []
            for d in depts:
                # Sections under department
                sec_res = await db.execute(select(Section).where(Section.department_id == d.id))
                secs = sec_res.scalars().all()

                sec_nodes = []
                for sec in secs:
                    # Teams under section
                    team_res = await db.execute(select(Team).where(Team.section_id == sec.id))
                    teams = team_res.scalars().all()

                    team_nodes = []
                    for t in teams:
                        team_users = [u for u in all_users if u.team_id == t.id]
                        team_nodes.append(
                            TeamNode(
                                id=str(t.id),
                                code=t.code,
                                name=t.name,
                                shift_pattern=t.shift_pattern or "DAY_SHIFT",
                                team_lead_id=str(t.team_lead_id) if t.team_lead_id else None,
                                members=[make_member_node(u) for u in team_users],
                            )
                        )

                    sec_unassigned = [u for u in all_users if u.section_id == sec.id and not u.team_id]
                    sec_nodes.append(
                        SectionNode(
                            id=str(sec.id),
                            code=sec.code,
                            name=sec.name,
                            supervisor_id=str(sec.supervisor_id) if sec.supervisor_id else None,
                            teams=team_nodes,
                            unassigned_members=[make_member_node(u) for u in sec_unassigned],
                        )
                    )

                dept_unassigned = [u for u in all_users if u.department_id == d.id and not u.section_id]
                dept_nodes.append(
                    DepartmentNode(
                        id=str(d.id),
                        code=d.code,
                        name=d.name,
                        hod_id=str(d.hod_id) if d.hod_id else None,
                        sla_hours_default=d.sla_hours_default or 24,
                        sections=sec_nodes,
                        unassigned_members=[make_member_node(u) for u in dept_unassigned],
                    )
                )

            site_nodes.append(
                SiteNode(
                    id=str(s.id),
                    code=s.code,
                    name=s.name,
                    site_type=s.site_type,
                    departments=dept_nodes,
                )
            )

        return OrganizationHierarchyTree(
            id=str(org.id),
            code=org.code,
            name=org.name,
            industry_type=org.industry_type,
            country=org.country,
            sites=site_nodes,
            unassigned_departments=[],
        )
