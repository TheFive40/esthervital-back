"""add primer_login column to usuarios

Revision ID: c8f7e9a12345
Revises: 5614aad60def
Create Date: 2024-01-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8f7e9a12345'
down_revision: Union[str, None] = '5614aad60def'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add primer_login column with default True
    op.add_column('usuarios', sa.Column('primer_login', sa.Boolean(), server_default='true', nullable=False))


def downgrade() -> None:
    op.drop_column('usuarios', 'primer_login')
