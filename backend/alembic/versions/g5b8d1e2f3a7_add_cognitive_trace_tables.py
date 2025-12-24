"""Add cognitive trace tables for dashboard

Revision ID: g5b8d1e2f3a7
Revises: f43e4d0dc9a5
Create Date: 2025-12-24

Adds tables for cognitive dashboard:
- cognitive_turns: Complete cognitive trace for each conversation turn
- expert_corrections: Structured corrections to AI decisions
- missed_signals: Signals that expert says should have been caught
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'g5b8d1e2f3a7'
down_revision = 'f43e4d0dc9a5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================================================
    # Cognitive Turns Table
    # ==========================================================================
    op.create_table(
        'cognitive_turns',
        sa.Column('id', sa.String(36), primary_key=True),  # UUID as string for SQLite compatibility
        sa.Column('turn_id', sa.String(50), nullable=False, unique=True),
        sa.Column('turn_number', sa.Integer(), nullable=False),
        sa.Column('child_id', sa.String(50), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        # Input
        sa.Column('parent_message', sa.Text(), nullable=False),
        sa.Column('parent_role', sa.String(50), nullable=True),
        # Phase 1: Perception
        sa.Column('tool_calls', sa.Text(), nullable=True),  # JSON stored as text
        sa.Column('perceived_intent', sa.String(50), nullable=True),
        # State changes
        sa.Column('state_delta', sa.Text(), nullable=True),  # JSON stored as text
        # Phase 2: Response
        sa.Column('turn_guidance', sa.Text(), nullable=True),
        sa.Column('active_curiosities', sa.Text(), nullable=True),  # JSON stored as text
        sa.Column('response_text', sa.Text(), nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_cognitive_turns_turn_id', 'cognitive_turns', ['turn_id'], unique=True)
    op.create_index('ix_cognitive_turns_child', 'cognitive_turns', ['child_id'])
    op.create_index('ix_cognitive_turns_child_number', 'cognitive_turns', ['child_id', 'turn_number'])
    op.create_index('ix_cognitive_turns_timestamp', 'cognitive_turns', ['timestamp'])

    # ==========================================================================
    # Expert Corrections Table
    # ==========================================================================
    op.create_table(
        'expert_corrections',
        sa.Column('id', sa.String(36), primary_key=True),  # UUID as string
        # Link to turn
        sa.Column('turn_id', sa.String(50), nullable=False),
        sa.Column('child_id', sa.String(50), nullable=False),
        # Target element
        sa.Column('target_type', sa.String(50), nullable=False),
        sa.Column('target_id', sa.String(200), nullable=True),
        # Correction details
        sa.Column('correction_type', sa.String(50), nullable=False),
        sa.Column('original_value', sa.Text(), nullable=True),  # JSON stored as text
        sa.Column('corrected_value', sa.Text(), nullable=True),  # JSON stored as text
        # Expert reasoning
        sa.Column('expert_reasoning', sa.Text(), nullable=False),
        # Author
        sa.Column('expert_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('expert_name', sa.String(100), nullable=False),
        # Training pipeline
        sa.Column('severity', sa.String(20), server_default='medium', nullable=False),
        sa.Column('used_in_training', sa.Boolean(), server_default=sa.text('0'), nullable=False),
        sa.Column('training_batch_id', sa.String(50), nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_expert_corrections_turn', 'expert_corrections', ['turn_id'])
    op.create_index('ix_expert_corrections_child', 'expert_corrections', ['child_id'])
    op.create_index('ix_expert_corrections_type', 'expert_corrections', ['correction_type'])
    op.create_index('ix_expert_corrections_unused', 'expert_corrections', ['used_in_training'])

    # ==========================================================================
    # Missed Signals Table
    # ==========================================================================
    op.create_table(
        'missed_signals',
        sa.Column('id', sa.String(36), primary_key=True),  # UUID as string
        # Link to turn
        sa.Column('turn_id', sa.String(50), nullable=False),
        sa.Column('child_id', sa.String(50), nullable=False),
        # What was missed
        sa.Column('signal_type', sa.String(50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('domain', sa.String(50), nullable=True),
        # Expert explanation
        sa.Column('why_important', sa.Text(), nullable=False),
        # Author
        sa.Column('expert_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('expert_name', sa.String(100), nullable=False),
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_missed_signals_turn', 'missed_signals', ['turn_id'])
    op.create_index('ix_missed_signals_child', 'missed_signals', ['child_id'])
    op.create_index('ix_missed_signals_type', 'missed_signals', ['signal_type'])


def downgrade() -> None:
    # Drop missed_signals
    op.drop_index('ix_missed_signals_type', table_name='missed_signals')
    op.drop_index('ix_missed_signals_child', table_name='missed_signals')
    op.drop_index('ix_missed_signals_turn', table_name='missed_signals')
    op.drop_table('missed_signals')

    # Drop expert_corrections
    op.drop_index('ix_expert_corrections_unused', table_name='expert_corrections')
    op.drop_index('ix_expert_corrections_type', table_name='expert_corrections')
    op.drop_index('ix_expert_corrections_child', table_name='expert_corrections')
    op.drop_index('ix_expert_corrections_turn', table_name='expert_corrections')
    op.drop_table('expert_corrections')

    # Drop cognitive_turns
    op.drop_index('ix_cognitive_turns_timestamp', table_name='cognitive_turns')
    op.drop_index('ix_cognitive_turns_child_number', table_name='cognitive_turns')
    op.drop_index('ix_cognitive_turns_child', table_name='cognitive_turns')
    op.drop_index('ix_cognitive_turns_turn_id', table_name='cognitive_turns')
    op.drop_table('cognitive_turns')
