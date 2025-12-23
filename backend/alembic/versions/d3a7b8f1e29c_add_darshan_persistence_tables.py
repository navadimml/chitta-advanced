"""Add Darshan persistence tables

Revision ID: d3a7b8f1e29c
Revises: c16a8bc1e17f
Create Date: 2025-12-23

Adds tables and columns for Darshan/Chitta data persistence:
- investigations: Investigation context for curiosities
- investigation_evidence: Evidence collected during investigations
- Updates to curiosities table for additional fields
- darshan_journal: Session journal entries
- darshan_crystals: Crystal/portrait storage
- session_history: Conversation history
- shared_summaries: Shared professional summaries
- session_flags: Session state flags

NOTE: Many tables already exist from initial schema:
- child_understanding, temporal_facts, milestones, stories, etc.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'd3a7b8f1e29c'
down_revision = 'c16a8bc1e17f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================================================
    # Update Curiosities Table with additional fields
    # ==========================================================================
    # Add missing columns to curiosities
    op.add_column('curiosities', sa.Column('status', sa.String(20), server_default='wondering'))
    op.add_column('curiosities', sa.Column('theory', sa.Text(), nullable=True))
    op.add_column('curiosities', sa.Column('video_appropriate', sa.Boolean(), server_default='false'))
    op.add_column('curiosities', sa.Column('video_value', sa.String(50), nullable=True))
    op.add_column('curiosities', sa.Column('video_value_reason', sa.Text(), nullable=True))
    op.add_column('curiosities', sa.Column('question', sa.Text(), nullable=True))
    op.add_column('curiosities', sa.Column('domains_involved', sa.Text(), nullable=True))  # JSON array

    # Add index for status queries
    op.create_index('ix_curiosities_child_status', 'curiosities', ['child_id', 'status'])

    # ==========================================================================
    # Investigations Table
    # ==========================================================================
    op.create_table(
        'investigations',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('curiosity_id', sa.String(50), nullable=False),  # Reference to curiosities.id (UUID stored as string)
        sa.Column('status', sa.String(20), server_default='active'),  # active/complete/stale
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('video_accepted', sa.Boolean(), server_default='false'),
        sa.Column('video_declined', sa.Boolean(), server_default='false'),
        sa.Column('video_suggested_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('guidelines_status', sa.String(20), nullable=True),  # generating/ready/error
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_investigations_curiosity', 'investigations', ['curiosity_id'])

    # ==========================================================================
    # Investigation Evidence Table
    # ==========================================================================
    op.create_table(
        'investigation_evidence',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('investigation_id', sa.String(50), sa.ForeignKey('investigations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('effect', sa.String(20), server_default='supports'),  # supports/contradicts/transforms
        sa.Column('source', sa.String(50), server_default='conversation'),
        sa.Column('recorded_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_evidence_investigation', 'investigation_evidence', ['investigation_id'])

    # ==========================================================================
    # Update Video Scenarios - add investigation link
    # ==========================================================================
    op.add_column('video_scenarios', sa.Column(
        'investigation_id',
        sa.String(50),
        nullable=True
    ))
    op.create_index('ix_video_scenarios_investigation', 'video_scenarios', ['investigation_id'])

    # ==========================================================================
    # Darshan Journal Table (session-level journal entries)
    # ==========================================================================
    op.create_table(
        'darshan_journal',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('child_id', sa.String(50), nullable=False, index=True),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('learned', sa.Text(), nullable=True),  # What was learned
        sa.Column('significance', sa.Float(), default=0.5),
        sa.Column('entry_type', sa.String(30), default='observation'),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ==========================================================================
    # Crystal Table (Developmental Portrait)
    # ==========================================================================
    op.create_table(
        'darshan_crystals',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('child_id', sa.String(50), nullable=False, unique=True, index=True),
        sa.Column('portrait_data', sa.Text(), nullable=True),  # JSON portrait
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # ==========================================================================
    # Session History Table
    # ==========================================================================
    op.create_table(
        'session_history',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('child_id', sa.String(50), nullable=False, index=True),
        sa.Column('role', sa.String(20), nullable=False),  # user/assistant
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('turn_number', sa.Integer(), default=0),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_session_history_child_turn', 'session_history', ['child_id', 'turn_number'])

    # ==========================================================================
    # Shared Summaries Table
    # ==========================================================================
    op.create_table(
        'shared_summaries',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('child_id', sa.String(50), nullable=False, index=True),
        sa.Column('summary_type', sa.String(50), nullable=False),  # professional, parent, etc.
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', sa.Text(), nullable=True),  # JSON metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ==========================================================================
    # Session Flags Table
    # ==========================================================================
    op.create_table(
        'session_flags',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('child_id', sa.String(50), nullable=False, unique=True, index=True),
        sa.Column('guided_collection_mode', sa.Boolean(), server_default='false'),
        sa.Column('baseline_video_requested', sa.Boolean(), server_default='false'),
        sa.Column('flags_data', sa.Text(), nullable=True),  # JSON for additional flags
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('session_flags')
    op.drop_table('shared_summaries')
    op.drop_index('ix_session_history_child_turn', table_name='session_history')
    op.drop_table('session_history')
    op.drop_table('darshan_crystals')
    op.drop_table('darshan_journal')

    # Remove video_scenarios investigation link
    op.drop_index('ix_video_scenarios_investigation', table_name='video_scenarios')
    op.drop_column('video_scenarios', 'investigation_id')

    op.drop_index('ix_evidence_investigation', table_name='investigation_evidence')
    op.drop_table('investigation_evidence')
    op.drop_index('ix_investigations_curiosity', table_name='investigations')
    op.drop_table('investigations')

    # Remove curiosities additions
    op.drop_index('ix_curiosities_child_status', table_name='curiosities')
    op.drop_column('curiosities', 'domains_involved')
    op.drop_column('curiosities', 'question')
    op.drop_column('curiosities', 'video_value_reason')
    op.drop_column('curiosities', 'video_value')
    op.drop_column('curiosities', 'video_appropriate')
    op.drop_column('curiosities', 'theory')
    op.drop_column('curiosities', 'status')
