"""Add target_label to inference_flags

Revision ID: 177d691d40b5
Revises: g5b8d1e2f3a7
Create Date: 2025-12-25 18:33:36.937986

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '177d691d40b5'
down_revision: Union[str, Sequence[str], None] = 'g5b8d1e2f3a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add target_label column to inference_flags table."""
    op.add_column('inference_flags', sa.Column('target_label', sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove target_label column from inference_flags table."""
    op.drop_column('inference_flags', 'target_label')
