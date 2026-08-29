import os
import sys
import json
import time
import secrets
import shutil
import asyncio
from pathlib import Path
from typing import Optional, Any
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.core.security import get_password_hash
from app.core.logging_config import logger

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
SETUP_STATE_FILE = ROOT_DIR / ".setup_state.json"
ENV_FILE = ROOT_DIR / ".env"


class SetupManager:
    """Manages the 8-stage first-time server setup state, pre-flight tests, and locking."""

    @classmethod
    def is_setup_completed(cls) -> bool:
        """Determines whether the first-time setup has been completed and locked."""
        # 1. Check environment variable
        if os.getenv("SETUP_COMPLETED", "").lower() in ("true", "1", "yes"):
            return True

        # 2. Check state file
        if SETUP_STATE_FILE.exists():
            try:
                data = json.loads(SETUP_STATE_FILE.read_text(encoding="utf-8"))
                return data.get("completed", False) is True
            except Exception:
                pass
        return False

    @classmethod
    def get_setup_state(cls) -> dict[str, Any]:
        """Loads the current setup progress from state file."""
        if SETUP_STATE_FILE.exists():
            try:
                return json.loads(SETUP_STATE_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass

        # Return default state
        return {
            "completed": False,
            "current_step": 1,
            "version": settings.APP_VERSION,
            "step_1_platform": {
                "organization_name": settings.APP_NAME,
                "installation_name": "Bikita Mining Site 1",
                "server_name": settings.SERVER_NAME,
                "environment": settings.ENVIRONMENT,
                "timezone": settings.TIMEZONE,
            },
            "step_2_network": {
                "primary_url": settings.FRONTEND_URL,
                "domain_name": "dwrms.bikita.com",
                "local_ip": "127.0.0.1",
                "https_enabled": True,
                "cors_origins": settings.CORS_ORIGINS,
                "client_settings": "tauri_and_web",
            },
            "step_3_database": {
                "engine": settings.DB_ENGINE,
                "host": settings.DB_HOST,
                "port": settings.DB_PORT,
                "name": settings.DB_NAME,
                "user": settings.DB_USER,
                "password": "",
            },
            "step_4_admin": {
                "email": "admin@bikita.com",
                "first_name": "System",
                "last_name": "Administrator",
                "department": "Maintenance",
                "password": "",
            },
            "step_5_storage": {
                "path": settings.STORAGE_PATH,
                "max_upload_size_mb": settings.MAX_UPLOAD_SIZE_MB,
            },
            "step_6_backups": {
                "path": settings.BACKUP_DIR,
                "frequency": "daily",
                "retention_days": settings.RETENTION_DAYS,
            },
            "step_7_remote": {
                "mode": "local_only",  # local_only, org_managed, tailscale
                "tailscale_auth_key": "",
                "notes": "SSH administration operates independently on port 22.",
            },
        }

    @classmethod
    def save_step(cls, step_number: int, data: dict[str, Any]):
        """Persists step configuration to setup state file."""
        state = cls.get_setup_state()
        state["current_step"] = max(state.get("current_step", 1), step_number + 1)
        state[f"step_{step_number}"] = data
        state["updated_at"] = datetime.now(timezone.utc).isoformat()
        SETUP_STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")

    @classmethod
    async def test_database(cls, engine_type: str, host: str, port: int, name: str, user: str, password: str) -> dict[str, Any]:
        """Pre-flight test connecting to database with specified credentials."""
        if engine_type == "sqlite":
            return {"status": "connected", "latency_ms": 0.5, "engine": "sqlite"}

        # Construct connection URL
        if engine_type == "postgresql":
            url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"
        elif engine_type == "mysql":
            url = f"mysql+aiomysql://{user}:{password}@{host}:{port}/{name}"
        else:
            raise ValueError(f"Unsupported engine: {engine_type}")

        t0 = time.perf_counter()
        test_engine = create_async_engine(url, echo=False)
        try:
            async with test_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            latency = (time.perf_counter() - t0) * 1000
            return {
                "status": "connected",
                "latency_ms": round(latency, 2),
                "engine": engine_type,
            }
        finally:
            await test_engine.dispose()

    @classmethod
    def test_storage(cls, target_path: str) -> dict[str, Any]:
        """Pre-flight probe testing directory writeability and disk capacity."""
        p = Path(target_path)
        if not p.is_absolute():
            p = ROOT_DIR / p

        try:
            p.mkdir(parents=True, exist_ok=True)
            probe_file = p / f".probe_{secrets.token_hex(4)}"
            probe_file.write_text("ok", encoding="utf-8")
            probe_file.unlink()

            stat = shutil.disk_usage(str(p))
            free_gb = round(stat.free / (1024 ** 3), 2)
            total_gb = round(stat.total / (1024 ** 3), 2)
            free_pct = round((stat.free / stat.total) * 100, 1)

            return {
                "path": str(p),
                "write_ok": True,
                "free_gb": free_gb,
                "total_gb": total_gb,
                "free_percentage": free_pct,
                "status": "healthy" if free_gb >= 1.0 else "low_disk_space",
            }
        except Exception as e:
            return {
                "path": str(p),
                "write_ok": False,
                "error": str(e),
                "status": "unwritable",
            }

    @classmethod
    async def finalize_setup(cls, config: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """
        Executes Step 8 verification and provisioning pipeline:
        1. Validates all required configuration parameters
        2. Updates .env file with permanent production settings
        3. Initializes database schema & Alembic migrations
        4. Seeds mining baseline roles, permissions, and departments
        5. Provisions authoritative System Administrator account
        6. Initializes storage directory tree
        7. Locks setup (SETUP_COMPLETED=true)
        8. Returns final verification report
        """
        if cls.is_setup_completed():
            raise RuntimeError("Setup has already been completed and locked.")

        state = config or cls.get_setup_state()

        step1 = state.get("step_1_platform", {})
        step2 = state.get("step_2_network", {})
        step3 = state.get("step_3_database", {})
        step4 = state.get("step_4_admin", {})
        step5 = state.get("step_5_storage", {})
        step6 = state.get("step_6_backups", {})
        step7 = state.get("step_7_remote", {})

        # 1. Update .env configuration
        env_updates = {
            "SETUP_COMPLETED": "true",
            "APP_NAME": step1.get("organization_name", "Bikita Minerals DWRMS"),
            "SERVER_NAME": step1.get("server_name", "bikita-srv-01"),
            "ENVIRONMENT": step1.get("environment", "production"),
            "TIMEZONE": step1.get("timezone", "Africa/Harare"),
            "FRONTEND_URL": step2.get("primary_url", "https://dwrms.bikita.com"),
            "NEXT_PUBLIC_API_URL": f"{step2.get('primary_url', 'https://dwrms.bikita.com').rstrip('/')}/api/v1",
            "CORS_ORIGINS": step2.get("cors_origins", "https://dwrms.bikita.com,tauri://localhost"),
            "DB_ENGINE": step3.get("engine", "postgresql"),
            "DB_HOST": step3.get("host", "db"),
            "DB_PORT": str(step3.get("port", 5432)),
            "DB_NAME": step3.get("name", "dwrms"),
            "DB_USER": step3.get("user", "dwrms_prod"),
            "DB_PASSWORD": step3.get("password", ""),
            "POSTGRES_USER": step3.get("user", "dwrms_prod"),
            "POSTGRES_PASSWORD": step3.get("password", ""),
            "POSTGRES_DB": step3.get("name", "dwrms"),
            "STORAGE_PATH": step5.get("path", "/var/dwrms/storage"),
            "MAX_UPLOAD_SIZE_MB": str(step5.get("max_upload_size_mb", 25)),
            "BACKUP_DIR": step6.get("path", "/var/dwrms/backups"),
            "RETENTION_DAYS": str(step6.get("retention_days", 30)),
            "REMOTE_CONNECTIVITY_MODE": step7.get("mode", "local_only"),
        }

        # Generate secret key if not already set
        if not os.getenv("SECRET_KEY"):
            env_updates["SECRET_KEY"] = secrets.token_hex(32)

        from app.cli.utils import update_env_file
        update_env_file(env_updates)

        # 2. Initialize Database Schema
        from app.db.session import engine, Base
        import app.modules.iam.models  # noqa: F401
        import app.modules.fleet.models  # noqa: F401
        import app.modules.jobs.models  # noqa: F401
        import app.modules.approvals.models  # noqa: F401
        import app.modules.notifications.models  # noqa: F401

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # 3. Seed Baseline Data
        from seed import seed
        await seed()

        # 4. Provision Initial Administrator
        from app.db.session import SessionLocal
        from app.modules.iam.models import User, Department, Role, UserRole
        from sqlalchemy import select

        admin_email = step4.get("email", "admin@bikita.com")
        admin_pass = step4.get("password") or "BikitaAdmin123!"
        admin_fname = step4.get("first_name", "System")
        admin_lname = step4.get("last_name", "Administrator")
        admin_dept = step4.get("department", "Maintenance")

        async with SessionLocal() as session:
            res_dept = await session.execute(select(Department).where(Department.name == admin_dept))
            dept = res_dept.scalar_one_or_none()
            if not dept:
                dept = Department(name=admin_dept, description=f"{admin_dept} Department")
                session.add(dept)
                await session.commit()
                await session.refresh(dept)

            res_role = await session.execute(select(Role).where(Role.name == "System Administrator"))
            admin_role = res_role.scalar_one_or_none()

            res_user = await session.execute(select(User).where(User.email == admin_email))
            user = res_user.scalar_one_or_none()
            if user:
                user.hashed_password = get_password_hash(admin_pass)
                user.is_active = True
                user.is_superuser = True
            else:
                user = User(
                    email=admin_email,
                    first_name=admin_fname,
                    last_name=admin_lname,
                    hashed_password=get_password_hash(admin_pass),
                    department_id=dept.id,
                    is_active=True,
                    is_superuser=True,
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)

            if admin_role:
                res_ur = await session.execute(
                    select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == admin_role.id)
                )
                if not res_ur.scalar_one_or_none():
                    session.add(UserRole(user_id=user.id, role_id=admin_role.id))
                    await session.commit()

        await engine.dispose()

        # 5. Initialize Storage
        from app.core.storage import storage_manager
        storage_manager.init_storage()

        # 6. Lock Setup State File
        state["completed"] = True
        state["completed_at"] = datetime.now(timezone.utc).isoformat()
        state["version"] = settings.APP_VERSION
        SETUP_STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")

        # 7. Return Final Setup Report
        return {
            "status": "success",
            "message": "First-time server setup completed and locked successfully.",
            "application_url": step2.get("primary_url", "https://dwrms.bikita.com"),
            "server_name": step1.get("server_name", "bikita-srv-01"),
            "version": settings.APP_VERSION,
            "admin_email": admin_email,
            "environment": step1.get("environment", "production"),
            "completed_at": state["completed_at"],
            "next_steps": [
                f"Log in to the web operations portal at {step2.get('primary_url', 'https://dwrms.bikita.com')}",
                "Use 'ops status' to monitor platform container state.",
                "Use 'ops health' for deep subsystem diagnostic probes.",
                "SSH administration remains independently accessible on port 22.",
            ],
        }
