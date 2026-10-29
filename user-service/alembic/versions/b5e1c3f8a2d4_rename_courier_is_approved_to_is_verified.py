"""rename courier is_approved to is_verified

Revision ID: b5e1c3f8a2d4
Revises: aa41c74dac57
Create Date: 2026-10-30 00:15:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b5e1c3f8a2d4'
down_revision: Union[str, Sequence[str], None] = 'aa41c74dac57'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('couriers', 'is_approved', new_column_name='is_verified')


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('couriers', 'is_verified', new_column_name='is_approved')
