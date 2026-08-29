"""Add Industrial Operations Core tables (organizations, sites, sections, teams, positions, employee_profiles)

Revision ID: 7a8b9c0d1e2f
Revises: ea5c866570ed
Create Date: 2026-08-28 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a8b9c0d1e2f'
down_revision: Union[str, None] = 'ea5c866570ed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=1024), nullable=True),
        sa.Column('industry_type', sa.String(length=100), server_default='Mining & Mineral Processing', nullable=False),
        sa.Column('country', sa.String(length=100), server_default='Zimbabwe', nullable=False),
        sa.Column('currency', sa.String(length=10), server_default='USD', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('1'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_organizations_code'), 'organizations', ['code'], unique=True)

    # 2. Create sites table
    op.create_table(
        'sites',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=True),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('site_type', sa.String(length=50), server_default='MINE_SITE', nullable=False),
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('gps_coordinates', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('1'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_sites_code'), 'sites', ['code'], unique=True)

    # 3. Create positions table
    op.create_table(
        'positions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('department_id', sa.UUID(), nullable=True),
        sa.Column('skill_level', sa.String(length=50), server_default='JOURNEYMAN', nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('1'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_positions_code'), 'positions', ['code'], unique=True)

    # 4. Create sections table
    op.create_table(
        'sections',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('department_id', sa.UUID(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=1024), nullable=True),
        sa.Column('supervisor_id', sa.UUID(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('1'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
        sa.ForeignKeyConstraint(['supervisor_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_sections_code'), 'sections', ['code'], unique=False)

    # 5. Create teams table
    op.create_table(
        'teams',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('section_id', sa.UUID(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('shift_pattern', sa.String(length=50), server_default='DAY_SHIFT', nullable=False),
        sa.Column('team_lead_id', sa.UUID(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('1'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['section_id'], ['sections.id'], ),
        sa.ForeignKeyConstraint(['team_lead_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_teams_code'), 'teams', ['code'], unique=False)

    # 6. Create employee_profiles table
    op.create_table(
        'employee_profiles',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('national_id', sa.String(length=100), nullable=True),
        sa.Column('emergency_contact_name', sa.String(length=255), nullable=True),
        sa.Column('emergency_contact_phone', sa.String(length=50), nullable=True),
        sa.Column('medical_clearance_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('mine_induction_expiry', sa.DateTime(timezone=True), nullable=True),
        sa.Column('skills_and_certifications', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_employee_profiles_user_id'), 'employee_profiles', ['user_id'], unique=True)

    # 7. Extend departments table
    with op.batch_alter_table('departments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('site_id', sa.UUID(), nullable=True))
        batch_op.add_column(sa.Column('code', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('hod_id', sa.UUID(), nullable=True))
        batch_op.add_column(sa.Column('sla_hours_default', sa.Integer(), server_default='24', nullable=True))
        batch_op.create_foreign_key('fk_departments_site_id', 'sites', ['site_id'], ['id'])
        batch_op.create_foreign_key('fk_departments_hod_id', 'users', ['hod_id'], ['id'])

    # 8. Extend users table
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('section_id', sa.UUID(), nullable=True))
        batch_op.add_column(sa.Column('team_id', sa.UUID(), nullable=True))
        batch_op.add_column(sa.Column('position_id', sa.UUID(), nullable=True))
        batch_op.add_column(sa.Column('supervisor_id', sa.UUID(), nullable=True))
        batch_op.add_column(sa.Column('employee_number', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('phone_number', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('shift_pattern', sa.String(length=50), server_default='DAY_SHIFT', nullable=True))
        batch_op.create_foreign_key('fk_users_section_id', 'sections', ['section_id'], ['id'])
        batch_op.create_foreign_key('fk_users_team_id', 'teams', ['team_id'], ['id'])
        batch_op.create_foreign_key('fk_users_position_id', 'positions', ['position_id'], ['id'])
        batch_op.create_foreign_key('fk_users_supervisor_id', 'users', ['supervisor_id'], ['id'])


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('shift_pattern')
        batch_op.drop_column('phone_number')
        batch_op.drop_column('employee_number')
        batch_op.drop_column('supervisor_id')
        batch_op.drop_column('position_id')
        batch_op.drop_column('team_id')
        batch_op.drop_column('section_id')

    with op.batch_alter_table('departments', schema=None) as batch_op:
        batch_op.drop_column('sla_hours_default')
        batch_op.drop_column('hod_id')
        batch_op.drop_column('code')
        batch_op.drop_column('site_id')

    op.drop_table('employee_profiles')
    op.drop_table('teams')
    op.drop_table('sections')
    op.drop_table('positions')
    op.drop_table('sites')
    op.drop_table('organizations')
