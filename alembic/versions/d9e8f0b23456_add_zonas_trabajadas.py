"""add zonas_trabajadas to sesiones_tratamiento

Revision ID: d9e8f0b23456
Revises: c8f7e9a12345
Create Date: 2026-01-25 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9e8f0b23456'
down_revision: Union[str, None] = 'c8f7e9a12345'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sesiones_tratamiento', sa.Column('zonas_trabajadas', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('sesiones_tratamiento', 'zonas_trabajadas')
