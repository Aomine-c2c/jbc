"""V1.3 — Job Report & Work Execution Engine tables

Revision ID: a1b2c3d4e5f6
Revises: 74bd076d72cc
Create Date: 2026-08-29

Creates:
  - job_reports              (1:1 with job_cards, lockable after closure)
  - job_report_progress_updates  (execution timeline events)
  - job_report_materials     (materials / tools / equipment line items)
  - job_report_attachments   (typed file attachments)
  - job_report_amendments    (post-closure auditable corrections)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '74bd076d72cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── job_reports ───────────────────────────────────────────────────────────
    op.create_table(
        'job_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_card_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Immutability
        sa.Column('is_locked', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('locked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('locked_by_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Core execution data
        sa.Column('fault_found', sa.Text(), nullable=True),
        sa.Column('fault_code', sa.String(length=100), nullable=True),
        sa.Column('corrective_action', sa.Text(), nullable=True),
        sa.Column('technical_notes', sa.Text(), nullable=True),
        sa.Column('observations', sa.Text(), nullable=True),
        sa.Column('recommendations', sa.Text(), nullable=True),
        sa.Column('follow_up_required', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('follow_up_notes', sa.Text(), nullable=True),

        # Labour summary
        sa.Column('actual_labour_hours', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.Column('actual_cost', sa.Float(), nullable=False, server_default=sa.text('0.0')),

        # Department-specific configurable data
        sa.Column('dept_schema_type', sa.String(length=50), nullable=False, server_default='GENERIC'),
        sa.Column('dept_specific_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),

        sa.ForeignKeyConstraint(['job_card_id'], ['job_cards.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['locked_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_card_id'),
    )
    op.create_index('ix_job_reports_job_card_id', 'job_reports', ['job_card_id'], unique=True)

    # ── job_report_progress_updates ───────────────────────────────────────────
    op.create_table(
        'job_report_progress_updates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reported_by_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('update_type', sa.String(length=50), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('percentage_complete', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('hold_reason', sa.String(length=1000), nullable=True),

        sa.ForeignKeyConstraint(['report_id'], ['job_reports.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reported_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_job_report_progress_updates_report_id', 'job_report_progress_updates', ['report_id'])

    # ── job_report_materials ──────────────────────────────────────────────────
    op.create_table(
        'job_report_materials',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='SPARE_PART'),
        sa.Column('item_name', sa.String(length=255), nullable=False),
        sa.Column('item_code', sa.String(length=100), nullable=True),
        sa.Column('quantity', sa.Float(), nullable=False, server_default=sa.text('1.0')),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('unit_cost', sa.Float(), nullable=True),
        sa.Column('notes', sa.String(length=500), nullable=True),

        sa.ForeignKeyConstraint(['report_id'], ['job_reports.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_job_report_materials_report_id', 'job_report_materials', ['report_id'])

    # ── job_report_attachments ────────────────────────────────────────────────
    op.create_table(
        'job_report_attachments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('uploaded_by_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='PHOTO'),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_url', sa.String(length=1024), nullable=True),
        sa.Column('file_type', sa.String(length=100), nullable=True),
        sa.Column('file_size_kb', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.Column('caption', sa.String(length=500), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),

        sa.ForeignKeyConstraint(['report_id'], ['job_reports.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_job_report_attachments_report_id', 'job_report_attachments', ['report_id'])

    # ── job_report_amendments ─────────────────────────────────────────────────
    op.create_table(
        'job_report_amendments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amended_by_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('approved_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('field_name', sa.String(length=100), nullable=False),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('amendment_reason', sa.Text(), nullable=False),
        sa.Column('approval_status', sa.String(length=20), nullable=False, server_default='APPROVED'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),

        sa.ForeignKeyConstraint(['report_id'], ['job_reports.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['amended_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_job_report_amendments_report_id', 'job_report_amendments', ['report_id'])


def downgrade() -> None:
    op.drop_table('job_report_amendments')
    op.drop_table('job_report_attachments')
    op.drop_table('job_report_materials')
    op.drop_table('job_report_progress_updates')
    op.drop_table('job_reports')
