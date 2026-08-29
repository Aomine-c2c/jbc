import uuid
from typing import Optional
from fastapi import APIRouter, Depends, status, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.iam.models import User
from app.modules.jobs.service import (
    JobCardService,
    WorkPackageService,
    CollaboratorService,
    compute_job_calculations,
    compute_overall_completion_pct,
)
from app.modules.jobs.schemas import (
    JobCardCreate,
    JobCardUpdate,
    JobCardSubmit,
    JobCardApprove,
    JobCardReject,
    JobCardReturn,
    JobCardPlan,
    JobCardAssign,
    JobCardStart,
    JobCardHold,
    JobCardComplete,
    JobCardReview,
    JobCardVerify,
    JobCardConfirm,
    JobCardClose,
    JobCardCancel,
    JobCardAmendmentCreate,
    JobCardAttachmentCreate,
    JobCardAttachmentResponse,
    JobCardResponse,
    JobCardListResponse,
    WorkPackageCreate,
    WorkPackageUpdate,
    WorkPackageTransition,
    WorkPackageResponse,
    JobCardCollaboratorCreate,
    JobCardCollaboratorResponse,
)


def _get_current_user() -> User:
    """Lazy import of get_current_user to avoid circular imports."""
    from app.main import get_current_user as _gcu
    return _gcu


def _format_job_response(job) -> JobCardResponse:
    calc = compute_job_calculations(job)
    resp = JobCardResponse.model_validate(job)
    resp.calculations = calc
    resp.overall_completion_pct = compute_overall_completion_pct(
        getattr(job, "work_packages", []) or []
    )
    return resp


job_router = APIRouter(prefix="/api/v1/job-cards", tags=["job-cards"])
wp_router = APIRouter(prefix="/api/v1/work-packages", tags=["work-packages"])


@job_router.post("", response_model=JobCardResponse, status_code=status.HTTP_201_CREATED)
async def create_job_card(
    data: JobCardCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    job = await JobCardService.create(db, data, current_user)
    return _format_job_response(job)


@job_router.get("", response_model=list[JobCardListResponse])
async def list_job_cards(
    department_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    jobs = await JobCardService.list(db, department_id, current_user)
    return jobs


@job_router.get("/{job_id}", response_model=JobCardResponse)
async def get_job_card(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    job = await JobCardService.get(db, job_id, current_user)
    return _format_job_response(job)


@job_router.get("/{job_id}/report", response_model=JobCardResponse)
async def get_digital_job_report(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    job = await JobCardService.get(db, job_id, current_user)
    return _format_job_response(job)


@job_router.patch("/{job_id}", response_model=JobCardResponse)
async def update_job_card(
    job_id: uuid.UUID,
    data: JobCardUpdate,
    x_draft_timestamp: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    job = await JobCardService.update(db, job_id, data, current_user, x_draft_timestamp)
    return _format_job_response(job)


@job_router.post("/{job_id}/submit", response_model=JobCardResponse)
async def submit_job_card(
    job_id: uuid.UUID,
    data: Optional[JobCardSubmit] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    job = await JobCardService.submit(db, job_id, data, current_user)
    return _format_job_response(job)


@job_router.post("/{job_id}/approve", response_model=JobCardResponse)
async def approve_job_card(
    job_id: uuid.UUID,
    data: JobCardApprove,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    job = await JobCardService.approve(db, job_id, data, current_user)
    return _format_job_response(job)


@job_router.post("/{job_id}/reject", response_model=JobCardResponse)
async def reject_job_card(
    job_id: uuid.UUID,
    data: JobCardReject,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    job = await JobCardService.reject(db, job_id, data, current_user)
    return _format_job_response(job)


@job_router.post("/{job_id}/return", response_model=JobCardResponse)
async def return_job_card(
    job_id: uuid.UUID,
    data: JobCardReturn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    job = await JobCardService.return_for_correction(db, job_id, data, current_user)
    return _format_job_response(job)


@job_router.post("/{job_id}/plan", response_model=JobCardResponse)
async def plan_job_card(
    job_id: uuid.UUID,
    data: JobCardPlan,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    job = await JobCardService.plan(db, job_id, data, current_user)
    return _format_job_response(job)


@job_router.post("/{job_id}/assign", response_model=JobCardResponse)
async def assign_job_card(
    job_id: uuid.UUID,
    data: JobCardAssign,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    job = await JobCardService.assign(db, job_id, data, current_user)
    return _format_job_response(job)


@job_router.post("/{job_id}/start", response_model=JobCardResponse)
async def start_job_card(
    job_id: uuid.UUID,
    data: Optional[JobCardStart] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    job = await JobCardService.start(db, job_id, data, current_user)
    return _format_job_response(job)


@job_router.post("/{job_id}/hold", response_model=JobCardResponse)
async def hold_job_card(
    job_id: uuid.UUID,
    data: JobCardHold,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    job = await JobCardService.hold(db, job_id, data, current_user)
    return _format_job_response(job)


@job_router.post("/{job_id}/complete", response_model=JobCardResponse)
async def complete_job_card(
    job_id: uuid.UUID,
    data: JobCardComplete,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    job = await JobCardService.complete(db, job_id, data, current_user)
    return _format_job_response(job)


@job_router.post("/{job_id}/review", response_model=JobCardResponse)
async def review_job_card(
    job_id: uuid.UUID,
    data: Optional[JobCardReview] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    job = await JobCardService.review(db, job_id, data, current_user)
    return _format_job_response(job)


@job_router.post("/{job_id}/verify", response_model=JobCardResponse)
async def verify_job_card(
    job_id: uuid.UUID,
    data: JobCardVerify,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    job = await JobCardService.verify(db, job_id, data, current_user)
    return _format_job_response(job)


@job_router.post("/{job_id}/confirm", response_model=JobCardResponse)
async def confirm_job_card(
    job_id: uuid.UUID,
    data: JobCardConfirm,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    job = await JobCardService.confirm(db, job_id, data, current_user)
    return _format_job_response(job)


@job_router.post("/{job_id}/close", response_model=JobCardResponse)
async def close_job_card(
    job_id: uuid.UUID,
    data: Optional[JobCardClose] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    job = await JobCardService.close(db, job_id, data, current_user)
    return _format_job_response(job)


@job_router.post("/{job_id}/cancel", response_model=JobCardResponse)
async def cancel_job_card(
    job_id: uuid.UUID,
    data: JobCardCancel,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    job = await JobCardService.cancel(db, job_id, data, current_user)
    return _format_job_response(job)


@job_router.post("/{job_id}/amend", response_model=JobCardResponse)
async def amend_job_card(
    job_id: uuid.UUID,
    data: JobCardAmendmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    job = await JobCardService.amend(db, job_id, data, current_user)
    return _format_job_response(job)


@job_router.post("/{job_id}/attachments", response_model=JobCardAttachmentResponse, status_code=status.HTTP_201_CREATED)
async def add_job_attachment(
    job_id: uuid.UUID,
    data: JobCardAttachmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await JobCardService.add_attachment(db, job_id, data, current_user)


# ── Collaborator Endpoints ─────────────────────────────────────────────────

@job_router.get("/{job_id}/collaborators", response_model=list[JobCardCollaboratorResponse])
async def list_collaborators(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await CollaboratorService.list(db, job_id)


@job_router.post(
    "/{job_id}/collaborators",
    response_model=JobCardCollaboratorResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_collaborator(
    job_id: uuid.UUID,
    data: JobCardCollaboratorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await CollaboratorService.add(db, job_id, data, current_user)


# ── Work Package Endpoints (scoped under /job-cards/{id}/work-packages) ────

@job_router.get("/{job_id}/work-packages", response_model=list[WorkPackageResponse])
async def list_work_packages(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await WorkPackageService.list(db, job_id, current_user)


@job_router.post(
    "/{job_id}/work-packages",
    response_model=WorkPackageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_work_package(
    job_id: uuid.UUID,
    data: WorkPackageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await WorkPackageService.create(db, job_id, data, current_user)


# ── Work Package CRUD & Transitions (top-level /work-packages/{id}) ─────────

@wp_router.get("/{wp_id}", response_model=WorkPackageResponse)
async def get_work_package(
    wp_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await WorkPackageService.get(db, wp_id, current_user)


@wp_router.patch("/{wp_id}", response_model=WorkPackageResponse)
async def update_work_package(
    wp_id: uuid.UUID,
    data: WorkPackageUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await WorkPackageService.update(db, wp_id, data, current_user)


@wp_router.post("/{wp_id}/submit", response_model=WorkPackageResponse)
async def submit_work_package(
    wp_id: uuid.UUID,
    data: Optional[WorkPackageTransition] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await WorkPackageService.transition(db, wp_id, "submit", data or WorkPackageTransition(), current_user)


@wp_router.post("/{wp_id}/approve", response_model=WorkPackageResponse)
async def approve_work_package(
    wp_id: uuid.UUID,
    data: Optional[WorkPackageTransition] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await WorkPackageService.transition(db, wp_id, "approve", data or WorkPackageTransition(), current_user)


@wp_router.post("/{wp_id}/start", response_model=WorkPackageResponse)
async def start_work_package(
    wp_id: uuid.UUID,
    data: Optional[WorkPackageTransition] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await WorkPackageService.transition(db, wp_id, "start", data or WorkPackageTransition(), current_user)


@wp_router.post("/{wp_id}/hold", response_model=WorkPackageResponse)
async def hold_work_package(
    wp_id: uuid.UUID,
    data: WorkPackageTransition,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await WorkPackageService.transition(db, wp_id, "hold", data, current_user)


@wp_router.post("/{wp_id}/resume", response_model=WorkPackageResponse)
async def resume_work_package(
    wp_id: uuid.UUID,
    data: Optional[WorkPackageTransition] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await WorkPackageService.transition(db, wp_id, "resume", data or WorkPackageTransition(), current_user)


@wp_router.post("/{wp_id}/complete", response_model=WorkPackageResponse)
async def complete_work_package(
    wp_id: uuid.UUID,
    data: WorkPackageTransition,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await WorkPackageService.transition(db, wp_id, "complete", data, current_user)


@wp_router.post("/{wp_id}/verify", response_model=WorkPackageResponse)
async def verify_work_package(
    wp_id: uuid.UUID,
    data: Optional[WorkPackageTransition] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await WorkPackageService.transition(db, wp_id, "verify", data or WorkPackageTransition(), current_user)


@wp_router.post("/{wp_id}/reject", response_model=WorkPackageResponse)
async def reject_work_package(
    wp_id: uuid.UUID,
    data: WorkPackageTransition,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await WorkPackageService.transition(db, wp_id, "reject", data, current_user)


@wp_router.post("/{wp_id}/cancel", response_model=WorkPackageResponse)
async def cancel_work_package(
    wp_id: uuid.UUID,
    data: WorkPackageTransition,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_get_current_user()),
):
    return await WorkPackageService.transition(db, wp_id, "cancel", data, current_user)
