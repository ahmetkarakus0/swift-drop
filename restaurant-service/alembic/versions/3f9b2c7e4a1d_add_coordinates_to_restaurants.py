"""add coordinates to restaurants

Revision ID: 3f9b2c7e4a1d
Revises: 168009178b8b
Create Date: 2026-11-03 07:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3f9b2c7e4a1d'
down_revision: Union[str, Sequence[str], None] = '168009178b8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('restaurants', sa.Column('latitude', sa.Float(), nullable=True))
    op.add_column('restaurants', sa.Column('longitude', sa.Float(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('restaurants', 'longitude')
    op.drop_column('restaurants', 'latitude')
