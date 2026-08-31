"""migrate requisition statuses

Revision ID: 415d1feb1cc1
Revises: a1b2c3d4e5f6
Create Date: 2026-08-31 07:10:00.075197

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '415d1feb1cc1'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE machine_requisitions SET status = 'REVIEWED' WHERE status IN ('DEPT_APPROVED', 'EQUIPMENT_CHECK')")
    op.execute("UPDATE machine_requisitions SET status = 'AWAITING_ALLOCATION' WHERE status = 'APPROVED'")
    op.execute("UPDATE machine_requisitions SET status = 'ALLOCATED' WHERE status IN ('SCHEDULED', 'DISPATCHED')")
    op.execute("UPDATE machine_requisitions SET status = 'IN_USE' WHERE status = 'RETURN_REQUESTED'")
    op.execute("UPDATE machine_requisitions SET status = 'CLOSED' WHERE status = 'INSPECTED'")


def downgrade() -> None:
    op.execute("UPDATE machine_requisitions SET status = 'DEPT_APPROVED' WHERE status = 'REVIEWED'")
    op.execute("UPDATE machine_requisitions SET status = 'APPROVED' WHERE status = 'AWAITING_ALLOCATION'")
    op.execute("UPDATE machine_requisitions SET status = 'SCHEDULED' WHERE status IN ('ALLOCATED', 'PARTIALLY_ALLOCATED')")
