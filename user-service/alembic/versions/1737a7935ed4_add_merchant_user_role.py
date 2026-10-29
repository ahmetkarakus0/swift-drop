"""add merchant user role

Revision ID: 1737a7935ed4
Revises: 7a3947d251f2
Create Date: 2026-10-29 17:23:40.587970

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1737a7935ed4'
down_revision: Union[str, Sequence[str], None] = '7a3947d251f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'merchant' AFTER 'courier'")


def downgrade() -> None:
    """Downgrade schema."""
    # Postgres cannot drop an enum value, so the type is rebuilt without it.
    merchants = op.get_bind().scalar(sa.text("SELECT count(*) FROM users WHERE role = 'merchant'"))
    if merchants:
        raise RuntimeError(
            f"Cannot remove the 'merchant' role: {merchants} user(s) still have it. "
            "Change or delete them first."
        )
    op.execute("ALTER TYPE user_role RENAME TO user_role_old")
    op.execute("CREATE TYPE user_role AS ENUM ('customer', 'courier', 'admin')")
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE user_role USING role::text::user_role")
    op.execute("DROP TYPE user_role_old")
