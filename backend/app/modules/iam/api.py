from uuid import UUID

import secrets

from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.modules.iam.models import Department, User, Role, UserRole, RolePermission, Permission, Scope
from app.modules.iam.schemas import (
    DepartmentCreate, DepartmentUpdate, DepartmentResponse,
    UserCreate, UserUpdate, UserResponse, UserListResponse,
    LoginRequest, TokenResponse, RefreshRequest, TokenRefreshResponse, MeResponse,
    RoleResponse, UserRolesUpdate,
)
from app.core.security import (
    verify_password, get_password_hash, create_access_token,
    create_refresh_token, decode_token,
)
from app.core.config import settings
from app.core.authz import AuthzGuard
from app.modules.audit.service import AuditService


iam_router = APIRouter(prefix="/api/v1/iam", tags=["iam"])


# ── Departments (with lazy auth import) ──────────────────────

def _get_current_user():
    """Lazy import to avoid circular dependency."""
    from app.main import get_current_user as gcu
    return gcu


@iam_router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    data: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    user_perms = _get_user_permissions(current_user)
    if not AuthzGuard.check_permission(current_user, "settings:manage", user_perms):
        raise HTTPException(status_code=403, detail="Not enough privileges to manage departments")

    existing = await db.execute(select(Department).where(Department.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Department already exists")
    dept = Department(name=data.name, description=data.description)
    db.add(dept)
    await db.commit()
    await db.refresh(dept)
    
    await AuditService.log_event(
        db=db,
        action="CREATE",
        resource="DEPARTMENT",
        resource_id=str(dept.id),
        user=current_user,
        new_value=data.model_dump()
    )
    
    return dept


@iam_router.get("/departments", response_model=list[DepartmentResponse])
async def list_departments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    result = await db.execute(select(Department).order_by(Department.name))
    return result.scalars().all()


@iam_router.get("/departments/{department_id}", response_model=DepartmentResponse)
async def get_department(
    department_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    result = await db.execute(select(Department).where(Department.id == department_id))
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    return dept


@iam_router.patch("/departments/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: UUID,
    data: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    user_perms = _get_user_permissions(current_user)
    if not AuthzGuard.check_permission(current_user, "settings:manage", user_perms):
        raise HTTPException(status_code=403, detail="Not enough privileges to manage departments")

    result = await db.execute(select(Department).where(Department.id == department_id))
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
        
    previous_value = {"name": dept.name, "description": dept.description}
        
    if data.name is not None:
        dept.name = data.name
    if data.description is not None:
        dept.description = data.description
    await db.commit()
    await db.refresh(dept)
    
    await AuditService.log_event(
        db=db,
        action="UPDATE",
        resource="DEPARTMENT",
        resource_id=str(dept.id),
        user=current_user,
        previous_value=previous_value,
        new_value={"name": dept.name, "description": dept.description}
    )
    
    return dept


# ── Users (with lazy auth import) ────────────────────────────

@iam_router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    user_perms = _get_user_permissions(current_user)
    if not AuthzGuard.check_permission(current_user, "users:manage", user_perms, resource_dept_id=data.department_id):
        raise HTTPException(status_code=403, detail="Not enough privileges")

    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="User already exists")

    new_user = User(
        email=data.email,
        first_name=data.first_name,
        last_name=data.last_name,
        hashed_password=get_password_hash(data.password),
        department_id=data.department_id,
        section_id=data.section_id,
        team_id=data.team_id,
        position_id=data.position_id,
        supervisor_id=data.supervisor_id,
        employee_number=data.employee_number,
        phone_number=data.phone_number,
        shift_pattern=data.shift_pattern,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    await AuditService.log_event(
        db=db,
        action="CREATE",
        resource="USER",
        resource_id=str(new_user.id),
        user=current_user,
        new_value={"email": new_user.email, "department_id": str(new_user.department_id)}
    )
    
    return new_user


@iam_router.get("/users", response_model=list[UserListResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    result = await db.execute(
        select(User)
        .options(selectinload(User.department), selectinload(User.roles).selectinload(UserRole.role))
        .order_by(User.email)
    )
    users = result.scalars().all()
    out = []
    for u in users:
        out.append(UserListResponse(
            id=u.id,
            email=u.email,
            first_name=u.first_name,
            last_name=u.last_name,
            department_id=u.department_id,
            department_name=u.department.name if u.department else None,
            position_id=u.position_id,
            employee_number=u.employee_number,
            roles=[ur.role.name for ur in u.roles if ur.role],
            is_active=u.is_active,
            created_at=u.created_at
        ))
    return out


@iam_router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(User)
        .options(selectinload(User.profile))
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@iam_router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    user_perms = _get_user_permissions(current_user)

    result = await db.execute(select(User).where(User.id == user_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
        
    if not AuthzGuard.check_permission(current_user, "users:manage", user_perms, resource_dept_id=existing.department_id):
        raise HTTPException(status_code=403, detail="Not enough privileges to edit this user")
    
    if data.department_id is not None and data.department_id != existing.department_id:
        if not AuthzGuard.check_permission(current_user, "users:manage", user_perms, resource_dept_id=data.department_id):
            raise HTTPException(status_code=403, detail="Not enough privileges to move user to this department")

    previous_value = {
        "first_name": existing.first_name,
        "last_name": existing.last_name,
        "department_id": str(existing.department_id) if existing.department_id else None,
        "is_active": existing.is_active
    }

    if data.first_name is not None:
        existing.first_name = data.first_name
    if data.last_name is not None:
        existing.last_name = data.last_name
    if data.department_id is not None:
        existing.department_id = data.department_id
    if data.section_id is not None:
        existing.section_id = data.section_id
    if data.team_id is not None:
        existing.team_id = data.team_id
    if data.position_id is not None:
        existing.position_id = data.position_id
    if data.supervisor_id is not None:
        if data.supervisor_id == user_id:
            raise HTTPException(status_code=400, detail="User cannot be their own supervisor")
        existing.supervisor_id = data.supervisor_id
    if data.employee_number is not None:
        existing.employee_number = data.employee_number
    if data.phone_number is not None:
        existing.phone_number = data.phone_number
    if data.shift_pattern is not None:
        existing.shift_pattern = data.shift_pattern
    if data.is_active is not None:
        existing.is_active = data.is_active

    await db.commit()
    await db.refresh(existing)
    
    await AuditService.log_event(
        db=db,
        action="UPDATE",
        resource="USER",
        resource_id=str(existing.id),
        user=current_user,
        previous_value=previous_value,
        new_value={"is_active": existing.is_active}
    )
    
    return existing


# ── Roles ───────────────────────────────────────────────────

@iam_router.get("/roles", response_model=list[RoleResponse])
async def list_roles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    result = await db.execute(select(Role).order_by(Role.name))
    return result.scalars().all()


@iam_router.get("/users/{user_id}/roles", response_model=list[RoleResponse])
async def get_user_roles(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    result = await db.execute(
        select(Role).join(UserRole).where(UserRole.user_id == user_id).order_by(Role.name)
    )
    return result.scalars().all()


@iam_router.put("/users/{user_id}/roles", response_model=list[RoleResponse])
async def update_user_roles(
    user_id: UUID,
    data: UserRolesUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    user_perms = _get_user_permissions(current_user)
    # Get user to check their department
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if not AuthzGuard.check_permission(current_user, "users:manage", user_perms, resource_dept_id=target_user.department_id):
        raise HTTPException(status_code=403, detail="Not enough privileges to edit this user's roles")

    # Clear existing roles
    await db.execute(UserRole.__table__.delete().where(UserRole.user_id == user_id))
    
    # Add new roles
    for role_id in data.role_ids:
        db.add(UserRole(user_id=user_id, role_id=role_id))
        
    await db.commit()
    
    await AuditService.log_event(
        db=db,
        action="UPDATE_ROLES",
        resource="USER",
        resource_id=str(user_id),
        user=current_user,
        new_value={"roles": [str(rid) for rid in data.role_ids]}
    )
    
    # Return updated roles
    result = await db.execute(
        select(Role).join(UserRole).where(UserRole.user_id == user_id).order_by(Role.name)
    )
    return result.scalars().all()



# ── Auth ────────────────────────────────────────────────────

def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Set browser credentials without exposing them to JavaScript storage."""
    secure = settings.ENVIRONMENT in {"production", "staging"}
    cookie_options = {"httponly": True, "secure": secure, "samesite": "lax", "path": "/"}
    response.set_cookie("dwrms_access_token", access_token, max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, **cookie_options)
    response.set_cookie("dwrms_refresh_token", refresh_token, max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400, **cookie_options)
    response.set_cookie(
        "dwrms_csrf_token",
        secrets.token_urlsafe(32),
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        httponly=False,
        secure=secure,
        samesite="lax",
        path="/",
    )


@iam_router.post("/auth/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    from app.core.auth_provider import get_auth_provider
    
    auth_provider = get_auth_provider()
    db_user = await auth_provider.authenticate(db, data.username, data.password)

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )

    if not db_user.is_active:
        raise HTTPException(status_code=403, detail="User is disabled")
        
    if not db_user.department_id:
        raise HTTPException(status_code=403, detail="Account pending administrator approval")

    await AuditService.log_event(
        db=db,
        action="LOGIN",
        resource="AUTH",
        user=db_user,
        reason="Successful login"
    )

    access_token = create_access_token(subject=str(db_user.id))
    refresh_token = create_refresh_token(subject=str(db_user.id))
    _set_auth_cookies(response, access_token, refresh_token)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@iam_router.post("/auth/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    data: RefreshRequest,
    response: Response,
    refresh_cookie: str | None = Cookie(default=None, alias="dwrms_refresh_token"),
):
    token = data.refresh_token or refresh_cookie
    if not token:
        raise HTTPException(status_code=401, detail="Refresh token required")
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    subject = payload.get("sub")
    if not subject:
        raise HTTPException(status_code=401, detail="Invalid token")
    access_token = create_access_token(subject=subject)
    if refresh_cookie:
        # Cookie clients receive a renewed access cookie. Bearer-token clients
        # retain the existing response contract.
        response.set_cookie(
            "dwrms_access_token",
            access_token,
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            httponly=True,
            secure=settings.ENVIRONMENT in {"production", "staging"},
            samesite="lax",
            path="/",
        )
    return TokenRefreshResponse(access_token=access_token)


@iam_router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    for name in ("dwrms_access_token", "dwrms_refresh_token", "dwrms_csrf_token"):
        response.delete_cookie(name, path="/")


@iam_router.get("/users/me", response_model=MeResponse)
async def get_current_user_me(current_user: User = Depends(_get_current_user())):
    return current_user


@iam_router.get("/auth/me/permissions", response_model=list[str])
async def get_current_user_permissions(current_user: User = Depends(_get_current_user())):
    return list(_get_user_permissions(current_user).keys())


# ── Helpers ─────────────────────────────────────────────────

def _get_user_permissions(user: User) -> dict[str, list[Scope]]:
    """Collect all permission names mapped to scopes granted to a user through their roles."""
    perms = {}
    try:
        for ur in (user.roles or []):
            if not ur.role:
                continue
            for rp in (ur.role.role_permissions or []):
                if not rp.permission:
                    continue
                perm_name = rp.permission.name
                if perm_name not in perms:
                    perms[perm_name] = []
                if rp.scope:
                    perms[perm_name].append(rp.scope)
    except Exception as e:
        print(f"DEBUG _get_user_permissions error: {e}")
    if getattr(user, "is_superuser", False):
        perms["global_override"] = []
    # Check for mock permissions attached by get_current_user
    mock_perms = getattr(user, "mock_permissions", None)
    if mock_perms:
        for p in mock_perms:
            if p not in perms:
                perms[p] = []
    return perms
