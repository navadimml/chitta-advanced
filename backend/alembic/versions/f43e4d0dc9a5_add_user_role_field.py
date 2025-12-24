"""add_user_role_field

Revision ID: f43e4d0dc9a5
Revises: e4b9c2d3f5a6
Create Date: 2025-12-24 13:50:09.710613

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f43e4d0dc9a5'
down_revision: Union[str, Sequence[str], None] = 'e4b9c2d3f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add role field to users table."""
    # Add role column with default 'parent' for existing users
    op.add_column('users', sa.Column('role', sa.String(length=20), nullable=False, server_default='parent'))

    # Remove the server default after adding the column (optional, keeps model clean)
    # op.alter_column('users', 'role', server_default=None)


def downgrade() -> None:
    """Remove role field from users table."""
    op.drop_column('users', 'role')
