import uuid
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status, Header, Request, Cookie
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt, JWTError
from starlette.middleware.base import BaseHTTPMiddleware

from app.db.session import get_db
from app.core.config import settings
from app.core.logging_config import setup_logging, logger, request_id_ctx, user_id_ctx, client_ip_ctx
from app.core.storage import storage_manager
from app.modules.iam.models import User

# Initialize structured logging subsystem
setup_logging()


def _split_origins() -> list[str]:
    return [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]


# ── Request ID Tracing Middleware ───────────────────────────

class RequestTracingMiddleware(BaseHTTPMiddleware):
    """Infects request correlation ID and contextual telemetry into execution stack."""

    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        client_ip = request.client.host if request.client else "-"
        
        request_id_token = request_id_ctx.set(req_id)
        client_ip_token = client_ip_ctx.set(client_ip)

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = req_id
            return response
        finally:
            request_id_ctx.reset(request_id_token)
            client_ip_ctx.reset(client_ip_token)


# ── JWT Dependency (defined BEFORE router imports) ──────────

MOCK_PERMISSIONS: dict[str, set[str]] = {
    "admin": {"global_override"},
    "viewer": set(),
    "creator": {"job_card:create"},
    "manager": {"job_card:approve"},
    "supervisor": {"job_card:assign", "job_card:verify"},
    "tech": {"job_card:start", "job_card:complete"},
    "requester": {"requisition:create", "requisition:submit"},
    "hod": {"requisition:approve"},
    "coord": {"requisition:reserve", "requisition:return"},
    "operator": {"requisition:dispatch"},
}


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    access_token: Optional[str] = Cookie(default=None, alias="dwrms_access_token"),
) -> User:
    """Extract and validate the current user from a bearer token or secure cookie."""
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
    elif access_token:
        token = access_token
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 1) Try real JWT decode
    try:
        payload = jwt.decode(token, settings.get_secret_key, algorithms=[settings.ALGORITHM])
        if payload.get("type") == "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh tokens cannot be used as access tokens",
                headers={"WWW-Authenticate": "Bearer"},
            )
        subject = payload.get("sub")
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        from sqlalchemy.orm import selectinload
        from app.modules.iam.models import UserRole, Role, RolePermission
        result = await db.execute(
            select(User)
            .options(
                selectinload(User.roles)
                .selectinload(UserRole.role)
                .selectinload(Role.role_permissions)
                .selectinload(RolePermission.permission),
                selectinload(User.profile)
            )
            .where(User.id == uuid.UUID(subject))
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id_ctx.set(str(user.id))
        return user
    except JWTError:
        pass

    # 2) Mock-token handling for tests
    if settings.ENVIRONMENT not in {"production", "staging"} and settings.ALLOW_TEST_TOKENS and token.startswith("mock_"):
        role = token.removeprefix("mock_").removesuffix("_token")
        perms = MOCK_PERMISSIONS.get(role, set())
        mock_dept = uuid.UUID("00000000-0000-0000-0000-000000000001")
        user = User(
            id=uuid.uuid4(),
            email=f"mock_{role}@test.com",
            first_name="Mock",
            last_name=role.capitalize(),
            hashed_password="",
            department_id=mock_dept,
            is_active=True,
        )
        user.mock_permissions = perms
        user_id_ctx.set(str(user.id))
        return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


# ── Lifespan Startup / DB & Storage Auto-initialization ──────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize persistent storage paths
    try:
        storage_manager.init_storage()
    except Exception as e:
        logger.warning(f"Storage init deferred/warning: {e}")

    # 2. Schema changes are applied by Alembic before the service starts.
    # Demo data is intentionally opt-in so production never creates a known
    # default administrator account.
    if settings.SEED_DEMO_DATA:
        if settings.ENVIRONMENT in {"production", "staging"}:
            raise RuntimeError("Demo data seeding is forbidden in production/staging environments")
        try:
            from seed import seed
            await seed()
        except Exception as e:
            logger.warning(f"Demo data seed failed: {e}")
    
    # 3. Security guard: test tokens must never be enabled in production/staging
    if settings.ALLOW_TEST_TOKENS and settings.ENVIRONMENT in {"production", "staging"}:
        raise RuntimeError("ALLOW_TEST_TOKENS is enabled in a production/staging environment. This is a critical security misconfiguration.")
        
    # 4. Start background notification / escalation loop
    import asyncio
    from app.modules.notifications.worker import escalation_worker_loop
    worker_task = asyncio.create_task(escalation_worker_loop())
    
    logger.info(f"DWRMS Application Core initialized ({settings.ENVIRONMENT})")
    yield
    worker_task.cancel()
    logger.info("DWRMS Application Core shutdown complete")


# ── App Definition & Middlewares ────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
)

app.add_middleware(RequestTracingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|100\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|.*\.ts\.net)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.core.middleware import AuditLogMiddleware
app.add_middleware(AuditLogMiddleware)

from app.core.idempotency import IdempotencyMiddleware
app.add_middleware(IdempotencyMiddleware)

from app.core.csrf import CsrfProtectionMiddleware
app.add_middleware(CsrfProtectionMiddleware)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# ── Exception Handlers ──────────────────────────────────────

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP_ERROR",
            "detail": exc.detail,
            "request_id": request_id_ctx.get(),
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    if settings.ENVIRONMENT == "production":
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "VALIDATION_ERROR",
                "detail": "Invalid request payload attributes",
                "request_id": request_id_ctx.get(),
            },
        )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "VALIDATION_ERROR",
            "detail": exc.errors(),
            "request_id": request_id_ctx.get(),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    req_id = request_id_ctx.get()
    logger.error(f"Unhandled server exception [{req_id}]: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "detail": "An unexpected system error occurred. Please reference the request ID when reporting.",
            "request_id": req_id,
        },
    )


# ── Top-Level Health Routing Aliases ────────────────────────

@app.get("/health", include_in_schema=False)
async def root_health_redirect():
    return RedirectResponse(url="/api/v1/health")


@app.get("/readiness", include_in_schema=False)
async def root_readiness_redirect():
    return RedirectResponse(url="/api/v1/readiness")


@app.get("/version", include_in_schema=False)
async def root_version_redirect():
    return RedirectResponse(url="/api/v1/version")


# ── API Routers ─────────────────────────────────────────────

from app.api.v1.system import system_router
from app.api.v1.storage import storage_router
from app.api.v1.setup import setup_router
from app.api.v1.platform import platform_router
from app.api.v1.events import events_router
from app.api.v1.export import export_router
from app.api.v1.org import org_router as v1_org_router
from app.modules.iam.api import iam_router
from app.modules.iam.org_api import org_router
from app.modules.iam.location_api import location_router
from app.modules.jobs.api import job_router, wp_router
from app.modules.fleet.api import fleet_router
from app.modules.dashboard.api import dashboard_router
from app.modules.search.api import search_router
from app.modules.approvals.api import approvals_router
from app.modules.notifications.api import router as notifications_router
from app.modules.audit.api import audit_router
from app.modules.work.api import router as work_router
from app.modules.assets.api import router as assets_router
from app.modules.requests.api import router as requests_router
from app.modules.materials.api import router as materials_router
from app.modules.contractors.api import router as contractors_router
from app.modules.sla.api import router as sla_router
from app.modules.workflow.api import router as workflow_router

app.include_router(system_router)
app.include_router(storage_router)
app.include_router(setup_router)
app.include_router(platform_router)
app.include_router(events_router)
app.include_router(export_router)
app.include_router(v1_org_router)
app.include_router(org_router)
app.include_router(location_router)
app.include_router(iam_router)
app.include_router(job_router)
app.include_router(wp_router)
app.include_router(fleet_router)
app.include_router(dashboard_router)
app.include_router(search_router)
app.include_router(approvals_router)
app.include_router(notifications_router)
app.include_router(audit_router)
app.include_router(work_router, prefix="/api/v1")
app.include_router(assets_router, prefix="/api/v1")
app.include_router(requests_router, prefix="/api/v1")
app.include_router(materials_router, prefix="/api/v1")
app.include_router(contractors_router, prefix="/api/v1")
app.include_router(sla_router, prefix="/api/v1")
app.include_router(workflow_router, prefix="/api/v1")

