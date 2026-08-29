"""Add JobCard extended completion fields

Revision ID: 74bd076d72cc
Revises: 3416e09ebcc3
Create Date: 2026-08-29 13:13:05.805754

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '74bd076d72cc'
down_revision: Union[str, None] = '3416e09ebcc3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('job_cards', sa.Column('equipment_used', sa.String(length=2000), nullable=True))
    op.add_column('job_cards', sa.Column('observations', sa.String(length=4000), nullable=True))
    op.add_column('job_cards', sa.Column('problems_encountered', sa.String(length=4000), nullable=True))
    op.add_column('job_cards', sa.Column('recommendations', sa.String(length=4000), nullable=True))


def downgrade() -> None:
    op.drop_column('job_cards', 'recommendations')
    op.drop_column('job_cards', 'problems_encountered')
    op.drop_column('job_cards', 'observations')
    op.drop_column('job_cards', 'equipment_used')
