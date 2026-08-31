import uuid
from datetime import datetime
import enum
from sqlalchemy import String, Boolean, ForeignKey, DateTime, Integer, JSON, func, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Scope(str, enum.Enum):
    OWN = "OWN"
    ASSIGNED = "ASSIGNED"
    LOCATION = "LOCATION"
    SITE = "SITE"
    DEPARTMENT = "DEPARTMENT"
    CROSS_DEPARTMENT = "CROSS_DEPARTMENT"
    GLOBAL = "GLOBAL"


# ── Organization & Site Structure ─────────────────────────────

class Organization(Base):
    """
    Top-level organizational entity (e.g. Bikita Minerals Ltd).
    """
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    industry_type: Mapped[str] = mapped_column(String(100), default="Mining & Mineral Processing")
    country: Mapped[str] = mapped_column(String(100), default="Zimbabwe")
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    sites = relationship("Site", back_populates="organization", lazy="selectin", cascade="all, delete-orphan")


class Site(Base):
    """
    Physical site, plant, or facility location (e.g. Bikita Mine Site, Masvingo Depot).
    """
    __tablename__ = "sites"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True, index=True
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    site_type: Mapped[str] = mapped_column(String(50), default="MINE_SITE")
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    gps_coordinates: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    organization = relationship("Organization", back_populates="sites")
    departments = relationship("Department", back_populates="site", lazy="selectin")
    locations = relationship("Location", back_populates="site", lazy="selectin", cascade="all, delete-orphan")


# ── Physical & Spatial Location Hierarchy ─────────────────────

class Location(Base):
    """
    Flexible, scalable physical and spatial hierarchy node.
    Supports arbitrary depth: Site -> Facility/Plant -> Area -> Section -> Specific Location.
    Features self-referential parent-child relationships with recursive path breadcrumb.
    """
    __tablename__ = "locations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True, index=True
    )
    site_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.id"), nullable=True, index=True
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    
    code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    location_type: Mapped[str] = mapped_column(String(50), nullable=False, default="AREA")
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    
    # Path & search helpers
    breadcrumb: Mapped[str | None] = mapped_column(String(1024), nullable=True, index=True)
    hierarchy_level: Mapped[int] = mapped_column(Integer, default=1)
    
    # Physical / GIS Metadata
    gps_coordinates: Mapped[str | None] = mapped_column(String(100), nullable=True)
    barcode_or_nfc: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    criticality_rating: Mapped[str | None] = mapped_column(String(50), default="MEDIUM")
    
    # Lifecycle / Archiving
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    parent = relationship("Location", remote_side=[id], back_populates="children")
    children = relationship("Location", back_populates="parent", lazy="selectin", cascade="all")
    organization = relationship("Organization", lazy="selectin")
    site = relationship("Site", back_populates="locations", lazy="selectin")


# ── Department, Section & Team Structure ──────────────────────

class Department(Base):
    """
    Functional department (e.g. Mechanical, Instrumentation, IT, Safety, Mining).
    """
    __tablename__ = "departments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.id"), nullable=True, index=True
    )
    code: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    hod_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    sla_hours_default: Mapped[int] = mapped_column(Integer, default=24)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    site = relationship("Site", back_populates="departments")
    sections = relationship("Section", back_populates="department", lazy="selectin", cascade="all, delete-orphan")
    positions = relationship("Position", back_populates="department", lazy="selectin")
    users = relationship("User", back_populates="department", lazy="selectin", foreign_keys="User.department_id")


class Section(Base):
    """
    Operational section within a department (e.g. Crushing & Screening, Concentrator Plant).
    """
    __tablename__ = "sections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    supervisor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    department = relationship("Department", back_populates="sections")
    teams = relationship("Team", back_populates="section", lazy="selectin", cascade="all, delete-orphan")
    users = relationship("User", back_populates="section", lazy="selectin", foreign_keys="User.section_id")


class Team(Base):
    """
    Field execution or shift crew (e.g. Shift Alpha, Rapid Response, Callout Crew).
    """
    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sections.id"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    shift_pattern: Mapped[str] = mapped_column(String(50), default="DAY_SHIFT")
    team_lead_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    section = relationship("Section", back_populates="teams")
    users = relationship("User", back_populates="team", lazy="selectin", foreign_keys="User.team_id")


# ── Position (Job Title / Operational Specialty) ───────────────

class Position(Base):
    """
    Job position / operational title (e.g. Senior Mechanical Fitter, SCADA Engineer).
    Decoupled from system RBAC permissions.
    """
    __tablename__ = "positions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True, index=True
    )
    skill_level: Mapped[str] = mapped_column(String(50), default="JOURNEYMAN")
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    department = relationship("Department", back_populates="positions")
    users = relationship("User", back_populates="position", lazy="selectin")


# ── User & Employee Profile ────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Organizational Placement
    site_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.id"), nullable=True, index=True
    )
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id"), nullable=True, index=True
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True, index=True
    )
    section_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sections.id"), nullable=True, index=True
    )
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True, index=True
    )
    position_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("positions.id"), nullable=True, index=True
    )
    
    # Supervisory Hierarchy (Self-referential)
    supervisor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    
    # Operational Attributes
    employee_number: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=True, index=True)
    phone_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    shift_pattern: Mapped[str | None] = mapped_column(String(50), nullable=True, default="DAY_SHIFT")
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    site = relationship("Site", foreign_keys=[site_id], lazy="selectin")
    location = relationship("Location", foreign_keys=[location_id], lazy="selectin")
    department = relationship("Department", back_populates="users", foreign_keys=[department_id])
    section = relationship("Section", back_populates="users", foreign_keys=[section_id])
    team = relationship("Team", back_populates="users", foreign_keys=[team_id])
    position = relationship("Position", back_populates="users", foreign_keys=[position_id])
    
    # Self-referential supervisory relationship
    supervisor = relationship("User", remote_side=[id], backref="subordinates", foreign_keys=[supervisor_id])
    
    roles = relationship("UserRole", back_populates="user", lazy="selectin", cascade="all, delete-orphan")
    profile = relationship("EmployeeProfile", back_populates="user", uselist=False, lazy="selectin", cascade="all, delete-orphan")


class EmployeeProfile(Base):
    """
    Extended operational & safety compliance attributes.
    """
    __tablename__ = "employee_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False, index=True
    )
    national_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    emergency_contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    medical_clearance_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    mine_induction_expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    skills_and_certifications: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="profile")


# ── System RBAC Roles & Permissions ────────────────────────────

class Role(Base):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)

    permissions = relationship("Permission", secondary="role_permissions", back_populates="roles", overlaps="role_permissions")
    user_roles = relationship("UserRole", back_populates="role", lazy="selectin")
    role_permissions = relationship("RolePermission", back_populates="role", lazy="selectin", overlaps="permissions")


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    roles = relationship("Role", secondary="role_permissions", back_populates="permissions", overlaps="role_permissions")
    role_permissions = relationship("RolePermission", back_populates="permission", lazy="selectin", overlaps="roles")


class RolePermission(Base):
    __tablename__ = "role_permissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    permission_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("permissions.id"), nullable=False)
    scope: Mapped[Scope] = mapped_column(Enum(Scope), nullable=False, default=Scope.OWN)
    
    role = relationship("Role", back_populates="role_permissions", lazy="selectin", overlaps="permissions,roles")
    permission = relationship("Permission", back_populates="role_permissions", lazy="selectin", overlaps="permissions,roles")


class UserRole(Base):
    __tablename__ = "user_roles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)

    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="user_roles", lazy="selectin")
