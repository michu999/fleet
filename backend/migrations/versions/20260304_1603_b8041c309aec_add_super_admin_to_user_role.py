"""add_super_admin_to_user_role

Revision ID: b8041c309aec
Revises: 3e14facaed1b
Create Date: 2026-03-04 16:03:13.750880+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8041c309aec'
down_revision: Union[str, None] = '3e14facaed1b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'SUPER_ADMIN'")


def downgrade() -> None:
    pass
