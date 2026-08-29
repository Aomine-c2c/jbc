"""add_work_packages_and_collaborators

Revision ID: debd9a6a4bcd
Revises: 48bcca2bf4fe
Create Date: 2026-08-26 18:52:47.789575

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'debd9a6a4bcd'
down_revision: Union[str, None] = '48bcca2bf4fe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _safe_add(table, col):
    try:
        op.add_column(table, col)
    except Exception:
        pass


def upgrade() -> None:
    op.create_table(
        'job_card_collaborators',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('job_card_id', sa.String(36), sa.ForeignKey('job_cards.id'), nullable=False),
        sa.Column('department_id', sa.String(36), sa.ForeignKey('departments.id'), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('added_by_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('notes', sa.String(1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_table(
        'work_packages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('job_card_id', sa.String(36), sa.ForeignKey('job_cards.id'), nullable=False),
        sa.Column('package_number', sa.String(20), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.String(4000), nullable=True),
        sa.Column('package_type', sa.String(50), nullable=False),
        sa.Column('owning_department_id', sa.String(36), sa.ForeignKey('departments.id'), nullable=False),
        sa.Column('responsible_supervisor_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('assigned_personnel', sa.String(1000), nullable=True),
        sa.Column('planned_start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('planned_end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('estimated_hours', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('actual_hours', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verified_by_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('work_performed', sa.String(4000), nullable=True),
        sa.Column('special_requirements', sa.String(2000), nullable=True),
        sa.Column('safety_notes', sa.String(2000), nullable=True),
        sa.Column('rejection_reason', sa.String(2000), nullable=True),
        sa.Column('prerequisite_wp_id', sa.String(36), sa.ForeignKey('work_packages.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_table(
        'work_package_action_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('work_package_id', sa.String(36), sa.ForeignKey('work_packages.id'), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('action', sa.String(80), nullable=False),
        sa.Column('state_from', sa.String(50), nullable=True),
        sa.Column('state_to', sa.String(50), nullable=True),
        sa.Column('details', sa.String(2000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    )
    try:
        op.create_table(
            'requisition_action_logs',
            sa.Column('id', sa.String(36), primary_key=True),
            sa.Column('requisition_id', sa.String(36), sa.ForeignKey('machine_requisitions.id'), nullable=False),
            sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('action', sa.String(50), nullable=False),
            sa.Column('state_from', sa.String(50), nullable=True),
            sa.Column('state_to', sa.String(50), nullable=True),
            sa.Column('details', sa.String(2000), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        )
    except Exception:
        pass

    _safe_add('job_cards', sa.Column('requesting_department_id', sa.String(36), nullable=True))
    _safe_add('job_cards', sa.Column('responsible_department_id', sa.String(36), nullable=True))
    _safe_add('job_cards', sa.Column('external_contractor', sa.String(500), nullable=True))

    for col in [
        sa.Column('requisition_number', sa.String(50), nullable=True),
        sa.Column('collaborating_department_id', sa.String(36), nullable=True),
        sa.Column('purpose', sa.String(2000), nullable=True),
        sa.Column('job_card_id', sa.String(36), nullable=True),
        sa.Column('machine_id', sa.String(36), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=True),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('required_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('estimated_duration_hours', sa.Float(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('operator_required', sa.Boolean(), nullable=True),
        sa.Column('operator_name', sa.String(255), nullable=True),
        sa.Column('special_requirements', sa.String(2000), nullable=True),
        sa.Column('safety_requirements', sa.String(2000), nullable=True),
        sa.Column('cost_centre', sa.String(100), nullable=True),
        sa.Column('estimated_cost', sa.Float(), nullable=True),
        sa.Column('actual_cost', sa.Float(), nullable=True),
        sa.Column('dept_approver_id', sa.String(36), nullable=True),
        sa.Column('dept_approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('equipment_checker_id', sa.String(36), nullable=True),
        sa.Column('equipment_checked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scheduler_id', sa.String(36), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('dispatcher_id', sa.String(36), nullable=True),
        sa.Column('dispatched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('returned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('inspector_id', sa.String(36), nullable=True),
        sa.Column('inspected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('inspection_notes', sa.String(2000), nullable=True),
        sa.Column('start_hour_meter', sa.Float(), nullable=True),
        sa.Column('end_hour_meter', sa.Float(), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.String(2000), nullable=True),
    ]:
        _safe_add('machine_requisitions', col)

    _safe_add('machine_reservations', sa.Column('start_time', sa.DateTime(timezone=True), nullable=True))
    _safe_add('machine_reservations', sa.Column('end_time', sa.DateTime(timezone=True), nullable=True))
    _safe_add('machine_types', sa.Column('category', sa.String(100), nullable=True))
    _safe_add('machines', sa.Column('serial_number', sa.String(100), nullable=True))
    _safe_add('machines', sa.Column('location', sa.String(255), nullable=True))
    _safe_add('machines', sa.Column('capacity_rating', sa.String(100), nullable=True))
    _safe_add('machines', sa.Column('current_hour_meter', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_table('work_package_action_logs')
    op.drop_table('work_packages')
    op.drop_table('job_card_collaborators')
