from typing import Any, Optional
import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.setup_manager import SetupManager

logger = logging.getLogger(__name__)
setup_router = APIRouter(prefix="/api/v1/setup", tags=["setup"])


# ── Pydantic Request Models ──────────────────────────────────

class TestDBRequest(BaseModel):
    engine: str = Field(default="postgresql", description="Database engine (postgresql, mysql, sqlite)")
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    name: str = Field(default="dwrms", description="Database name")
    user: str = Field(default="postgres", description="Database username")
    password: str = Field(default="", description="Database password")


class TestStorageRequest(BaseModel):
    path: str = Field(default="./storage", description="Storage directory path")


class StepDataRequest(BaseModel):
    step_number: int = Field(ge=1, le=7, description="Step number (1-7)")
    data: dict[str, Any] = Field(description="Configuration dictionary for this step")


class FinalizeSetupRequest(BaseModel):
    config: Optional[dict[str, Any]] = None


# ── API Endpoints ────────────────────────────────────────────

@setup_router.get("/status")
async def get_setup_status():
    """Returns current first-time setup state and whether setup is completed."""
    completed = SetupManager.is_setup_completed()
    if completed:
        return {
            "is_completed": True,
            "message": "Platform setup has already been completed and locked.",
        }

    state = SetupManager.get_setup_state()
    # Mask passwords if any exist in draft state
    if "step_3_database" in state and "password" in state["step_3_database"]:
        state["step_3_database"]["password"] = "******" if state["step_3_database"]["password"] else ""
    if "step_4_admin" in state and "password" in state["step_4_admin"]:
        state["step_4_admin"]["password"] = ""

    return {
        "is_completed": False,
        "current_step": state.get("current_step", 1),
        "state": state,
    }


@setup_router.post("/test-db")
async def test_database_connection(req: TestDBRequest):
    """Pre-flight test validating database credentials and measuring latency."""
    if SetupManager.is_setup_completed():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Setup is completed and locked.")

    try:
        res = await SetupManager.test_database(
            engine_type=req.engine,
            host=req.host,
            port=req.port,
            name=req.name,
            user=req.user,
            password=req.password,
        )
        return res
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database connection failed: {str(e)}",
        )


@setup_router.post("/test-storage")
async def test_storage_capacity(req: TestStorageRequest):
    """Pre-flight probe testing storage write access and disk capacity."""
    if SetupManager.is_setup_completed():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Setup is completed and locked.")

    res = SetupManager.test_storage(req.path)
    if not res.get("write_ok"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Storage path is unwritable: {res.get('error', 'Unknown error')}",
        )
    return res


@setup_router.post("/step/{step_number}")
async def save_setup_step(step_number: int, req: dict[str, Any]):
    """Persists progress for a specific setup step (1-7)."""
    if SetupManager.is_setup_completed():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Setup is completed and locked.")

    if not (1 <= step_number <= 7):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Step number must be between 1 and 7.")

    SetupManager.save_step(step_number, req)
    return {"status": "saved", "step": step_number, "next_step": step_number + 1}


@setup_router.post("/finalize")
async def finalize_setup(req: FinalizeSetupRequest):
    """Executes Step 8 verification checklist, provisions admin, and locks setup."""
    if SetupManager.is_setup_completed():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Setup is already completed and locked.")

    try:
        report = await SetupManager.finalize_setup(req.config)
        return report
    except Exception as e:
        logger.exception(f"Setup finalization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Setup finalization failed: {str(e)}",
        )
