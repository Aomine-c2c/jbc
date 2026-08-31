"""
Job Report Service Layer

Handles create, read, update, lock, and amendment operations for JobReport
and its child entities (progress updates, materials, attachments, amendments).

Key invariant: Once is_locked=True, direct field edits are blocked.
All post-closure corrections must go through ReportService.amend().
"""
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.jobs.report_models import (
    JobReport,
    JobReportProgressUpdate,
    JobReportMaterial,
    JobReportAttachment,
    JobReportAmendment,
    PROGRESS_UPDATE_TYPES,
    MATERIAL_CATEGORIES,
    ATTACHMENT_CATEGORIES,
    DEPT_SCHEMA_TYPES,
)
from app.modules.jobs.report_schemas import (
    JobReportUpdate,
    JobReportProgressUpdateCreate,
    JobReportMaterialCreate,
    JobReportAttachmentCreate,
    JobReportAmendmentCreate,
)
from app.modules.jobs.dept_schemas import validate_dept_data, get_dept_schema_fields
from app.modules.iam.models import User


class ReportService:

    # ── Get or Create ─────────────────────────────────────────

    @staticmethod
    async def get_or_create(db: AsyncSession, job_card_id: uuid.UUID, dept_schema_type: str = "GENERIC") -> JobReport:
        """
        Retrieve the JobReport for the given job card, creating it if it doesn't exist.
        Called automatically by JobCardService.start().
        """
        result = await db.execute(
            select(JobReport).where(JobReport.job_card_id == job_card_id)
        )
        report = result.scalar_one_or_none()

        if report is None:
            report = JobReport(
                job_card_id=job_card_id,
                dept_schema_type=dept_schema_type,
            )
            db.add(report)
            await db.flush()

        return report

    @staticmethod
    async def get(db: AsyncSession, job_card_id: uuid.UUID) -> JobReport:
        """Get the JobReport for a job card, raising 404 if not found."""
        result = await db.execute(
            select(JobReport).where(JobReport.job_card_id == job_card_id)
        )
        report = result.scalar_one_or_none()
        if report is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job report not found. The job card may not have been started yet.",
            )
        return report

    # ── Update ────────────────────────────────────────────────

    @staticmethod
    async def update(
        db: AsyncSession,
        job_card_id: uuid.UUID,
        data: JobReportUpdate,
        user: User,
    ) -> JobReport:
        """
        Update report fields. Blocked if the report is locked (post-closure).
        Use ReportService.amend() for post-closure corrections.
        """
        report = await ReportService.get(db, job_card_id)

        if report.is_locked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "This report is locked because the Job Card has been CLOSED. "
                    "Use the amendment process to make corrections."
                ),
            )

        update_data = data.model_dump(exclude_unset=True)

        # Validate dept-specific data if being updated
        if "dept_specific_data" in update_data and update_data["dept_specific_data"] is not None:
            schema_type = update_data.get("dept_schema_type", report.dept_schema_type)
            update_data["dept_specific_data"] = validate_dept_data(
                schema_type, update_data["dept_specific_data"]
            )

        for field, value in update_data.items():
            setattr(report, field, value)

        await db.flush()
        return report

    # ── Lock (called by JobCardService.close()) ───────────────

    @staticmethod
    async def lock(db: AsyncSession, job_card_id: uuid.UUID, user: User) -> JobReport | None:
        """
        Lock the report after the Job Card is closed.
        After this point, only JobReportAmendment records can modify history.
        Safe to call even if no report exists (returns None).
        """
        result = await db.execute(
            select(JobReport).where(JobReport.job_card_id == job_card_id)
        )
        report = result.scalar_one_or_none()

        if report is not None and not report.is_locked:
            report.is_locked = True
            report.locked_at = datetime.now(timezone.utc)
            report.locked_by_id = user.id
            await db.flush()

        return report

    # ── Progress Updates ──────────────────────────────────────

    @staticmethod
    async def add_progress(
        db: AsyncSession,
        job_card_id: uuid.UUID,
        data: JobReportProgressUpdateCreate,
        user: User,
    ) -> JobReportProgressUpdate:
        """Add a progress update to the job execution timeline."""
        report = await ReportService.get(db, job_card_id)

        if report.is_locked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot add progress updates to a locked (closed) job report.",
            )

        if data.update_type not in PROGRESS_UPDATE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid update_type. Must be one of: {PROGRESS_UPDATE_TYPES}",
            )

        if data.update_type == "PAUSE" and not data.hold_reason:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="hold_reason is required when update_type is PAUSE.",
            )

        update = JobReportProgressUpdate(
            report_id=report.id,
            reported_by_id=user.id,
            update_type=data.update_type,
            notes=data.notes,
            hold_reason=data.hold_reason,
            percentage_complete=data.percentage_complete,
        )
        db.add(update)
        await db.flush()
        return update

    # ── Materials & Resources ─────────────────────────────────

    @staticmethod
    async def add_material(
        db: AsyncSession,
        job_card_id: uuid.UUID,
        data: JobReportMaterialCreate,
        user: User,
    ) -> JobReportMaterial:
        """Add a material, spare, tool, or equipment entry to the report."""
        report = await ReportService.get(db, job_card_id)

        if report.is_locked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot add materials to a locked (closed) job report.",
            )

        if data.category not in MATERIAL_CATEGORIES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid category. Must be one of: {MATERIAL_CATEGORIES}",
            )

        material = JobReportMaterial(
            report_id=report.id,
            **data.model_dump(),
        )
        db.add(material)
        await db.flush()
        return material

    @staticmethod
    async def delete_material(
        db: AsyncSession,
        job_card_id: uuid.UUID,
        material_id: uuid.UUID,
        user: User,
    ) -> None:
        """Remove a material entry (blocked if report is locked)."""
        report = await ReportService.get(db, job_card_id)

        if report.is_locked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot remove materials from a locked (closed) job report.",
            )

        result = await db.execute(
            select(JobReportMaterial).where(
                JobReportMaterial.id == material_id,
                JobReportMaterial.report_id == report.id,
            )
        )
        material = result.scalar_one_or_none()
        if material is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material entry not found.")

        await db.delete(material)
        await db.flush()

    # ── Attachments ───────────────────────────────────────────

    @staticmethod
    async def add_attachment(
        db: AsyncSession,
        job_card_id: uuid.UUID,
        data: JobReportAttachmentCreate,
        user: User,
    ) -> JobReportAttachment:
        """Add a categorised file attachment to the report."""
        report = await ReportService.get(db, job_card_id)

        if report.is_locked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot add attachments to a locked (closed) job report.",
            )

        if data.category not in ATTACHMENT_CATEGORIES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid category. Must be one of: {ATTACHMENT_CATEGORIES}",
            )

        attachment = JobReportAttachment(
            report_id=report.id,
            uploaded_by_id=user.id,
            **data.model_dump(),
        )
        db.add(attachment)
        await db.flush()
        return attachment

    # ── Post-Closure Amendments ───────────────────────────────

    @staticmethod
    async def amend(
        db: AsyncSession,
        job_card_id: uuid.UUID,
        data: JobReportAmendmentCreate,
        user: User,
    ) -> JobReportAmendment:
        """
        Create an auditable amendment record for a locked report.
        Captures the old value, new value, and justification reason.
        The actual field on the report is also updated to reflect the correction.
        """
        report = await ReportService.get(db, job_card_id)

        # Amendments are only for locked reports; for unlocked reports use update()
        # We allow amendments on both locked and unlocked reports for flexibility,
        # but a locked report MUST use this path.
        old_value = str(getattr(report, data.field_name, None))

        # Apply the correction to the report itself
        allowed_text_fields = {
            "fault_found", "fault_code", "corrective_action", "technical_notes",
            "observations", "recommendations", "follow_up_notes",
        }
        if data.field_name in allowed_text_fields:
            setattr(report, data.field_name, data.new_value)
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Field '{data.field_name}' cannot be amended via this process.",
            )

        amendment = JobReportAmendment(
            report_id=report.id,
            amended_by_id=user.id,
            field_name=data.field_name,
            old_value=old_value,
            new_value=data.new_value,
            amendment_reason=data.amendment_reason,
            approval_status="APPROVED",
        )
        db.add(amendment)
        await db.flush()
        return amendment

    # ── Department Schema Metadata ────────────────────────────

    @staticmethod
    def get_dept_fields(dept_schema_type: str) -> list[dict]:
        """Return the field metadata for a department type (used by frontend)."""
        if dept_schema_type not in DEPT_SCHEMA_TYPES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unknown dept_schema_type: {dept_schema_type}",
            )
        return get_dept_schema_fields(dept_schema_type)
