"""add_parent_type_to_users

Revision ID: c16a8bc1e17f
Revises: a0a1110fee82
Create Date: 2025-12-22 12:31:18.333661

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c16a8bc1e17f'
down_revision: Union[str, Sequence[str], None] = 'a0a1110fee82'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('parent_type', sa.String(10), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'parent_type')
