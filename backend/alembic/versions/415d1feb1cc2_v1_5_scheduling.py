"""v1.5 scheduling

Revision ID: 415d1feb1cc2
Revises: 415d1feb1cc1
Create Date: 2026-08-31 07:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '415d1feb1cc2'
down_revision = '415d1feb1cc1'
branch_labels = None
depends_on = None

def upgrade() -> None:
    with op.batch_alter_table('machine_reservations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('actual_start_time', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('actual_end_time', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('reservation_type', sa.String(length=50), nullable=False, server_default='REQUISITION'))
        batch_op.alter_column('requisition_id', existing_type=sa.UUID(), nullable=True)

    # Migrate MACHINE status 'MAINTENANCE' -> 'UNDER_MAINTENANCE'
    op.execute("UPDATE machines SET status = 'UNDER_MAINTENANCE' WHERE status = 'MAINTENANCE'")

def downgrade() -> None:
    pass
