"""add_video_feedback_table

Revision ID: 24031b75921d
Revises: 177d691d40b5
Create Date: 2025-12-25 19:25:37.736514

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '24031b75921d'
down_revision: Union[str, Sequence[str], None] = '177d691d40b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add video_feedback table."""
    op.create_table('video_feedback',
        sa.Column('child_id', sa.String(length=50), nullable=False),
        sa.Column('video_id', sa.String(length=100), nullable=False),
        sa.Column('quality', sa.String(length=20), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('author_id', sa.UUID(), nullable=True),
        sa.Column('author_name', sa.String(length=100), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_video_feedback_child', 'video_feedback', ['child_id'], unique=False)
    op.create_index('ix_video_feedback_video', 'video_feedback', ['video_id'], unique=False)
    op.create_index('ix_video_feedback_child_video', 'video_feedback', ['child_id', 'video_id'], unique=True)


def downgrade() -> None:
    """Remove video_feedback table."""
    op.drop_index('ix_video_feedback_child_video', table_name='video_feedback')
    op.drop_index('ix_video_feedback_video', table_name='video_feedback')
    op.drop_index('ix_video_feedback_child', table_name='video_feedback')
    op.drop_table('video_feedback')
