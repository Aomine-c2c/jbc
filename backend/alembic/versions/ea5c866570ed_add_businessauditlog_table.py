"""Add BusinessAuditLog table

Revision ID: ea5c866570ed
Revises: debd9a6a4bcd
Create Date: 2026-08-27 14:04:03.699416

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ea5c866570ed'
down_revision: Union[str, None] = 'debd9a6a4bcd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('business_audit_logs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=True),
    sa.Column('user_name', sa.String(length=255), nullable=True),
    sa.Column('department_name', sa.String(length=255), nullable=True),
    sa.Column('role_names', sa.String(length=500), nullable=True),
    sa.Column('action', sa.String(length=100), nullable=False),
    sa.Column('resource', sa.String(length=100), nullable=False),
    sa.Column('resource_id', sa.String(length=255), nullable=True),
    sa.Column('previous_value', sa.JSON(), nullable=True),
    sa.Column('new_value', sa.JSON(), nullable=True),
    sa.Column('reason', sa.Text(), nullable=True),
    sa.Column('ip_address', sa.String(length=50), nullable=True),
    sa.Column('user_agent', sa.String(length=1024), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_business_audit_logs_action'), 'business_audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_business_audit_logs_resource'), 'business_audit_logs', ['resource'], unique=False)
    op.create_index(op.f('ix_business_audit_logs_resource_id'), 'business_audit_logs', ['resource_id'], unique=False)
    op.create_index(op.f('ix_business_audit_logs_timestamp'), 'business_audit_logs', ['timestamp'], unique=False)
    op.create_index(op.f('ix_business_audit_logs_user_id'), 'business_audit_logs', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_business_audit_logs_user_id'), table_name='business_audit_logs')
    op.drop_index(op.f('ix_business_audit_logs_timestamp'), table_name='business_audit_logs')
    op.drop_index(op.f('ix_business_audit_logs_resource_id'), table_name='business_audit_logs')
    op.drop_index(op.f('ix_business_audit_logs_resource'), table_name='business_audit_logs')
    op.drop_index(op.f('ix_business_audit_logs_action'), table_name='business_audit_logs')
    op.drop_table('business_audit_logs')
