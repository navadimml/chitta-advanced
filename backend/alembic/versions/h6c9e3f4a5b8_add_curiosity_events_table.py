"""Add curiosity events table for event sourcing

Revision ID: h6c9e3f4a5b8
Revises: 24031b75921d
Create Date: 2025-12-26

Adds the curiosity_events table for event sourcing architecture.
Events are immutable and append-only, tracking all changes to the
curiosity system with full provenance for explainability.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'h6c9e3f4a5b8'
down_revision = '24031b75921d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create curiosity_events table."""
    op.create_table(
        'curiosity_events',
        # Primary key (UUID as string for SQLite compatibility)
        sa.Column('id', sa.String(36), primary_key=True),

        # Temporal
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False,
                  comment="When this event occurred"),

        # Context
        sa.Column('session_id', sa.String(50), nullable=False,
                  comment="Session in which this event occurred"),
        sa.Column('child_id', sa.String(50), nullable=False,
                  comment="Child this event belongs to"),

        # Event classification
        sa.Column('event_type', sa.String(50), nullable=False,
                  comment="Type of event (observation_added, curiosity_created, etc.)"),
        sa.Column('entity_type', sa.String(30), nullable=False,
                  comment="Type of entity affected (observation, curiosity, pattern, etc.)"),
        sa.Column('entity_id', sa.String(100), nullable=False,
                  comment="ID of the entity affected by this event"),

        # State changes (stored as JSON)
        sa.Column('changes_json', sa.Text(), nullable=True,
                  comment="JSON object mapping field names to {from, to} changes"),

        # Provenance (REQUIRED for explainability)
        sa.Column('reasoning', sa.Text(), nullable=False,
                  comment="WHY this change was made - natural language explanation"),
        sa.Column('evidence_refs_json', sa.Text(), nullable=True,
                  comment="JSON array of observation/evidence IDs that led to this decision"),

        # Cascade tracking
        sa.Column('triggered_by', sa.String(36), nullable=True,
                  comment="Parent event ID if this was triggered as part of a cascade"),

        # Audit timestamps
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False,
                  comment="When this record was created in the database"),
    )

    # Primary queries
    op.create_index('ix_curiosity_events_child', 'curiosity_events', ['child_id'])
    op.create_index('ix_curiosity_events_session', 'curiosity_events', ['session_id'])
    op.create_index('ix_curiosity_events_entity', 'curiosity_events', ['entity_id'])

    # Time-based queries
    op.create_index('ix_curiosity_events_timestamp', 'curiosity_events', ['timestamp'])
    op.create_index('ix_curiosity_events_child_time', 'curiosity_events', ['child_id', 'timestamp'])

    # Type-based queries
    op.create_index('ix_curiosity_events_type', 'curiosity_events', ['event_type'])
    op.create_index('ix_curiosity_events_child_type', 'curiosity_events', ['child_id', 'event_type'])

    # Cascade tracking
    op.create_index('ix_curiosity_events_triggered_by', 'curiosity_events', ['triggered_by'])


def downgrade() -> None:
    """Drop curiosity_events table."""
    # Drop all indexes first
    op.drop_index('ix_curiosity_events_triggered_by', table_name='curiosity_events')
    op.drop_index('ix_curiosity_events_child_type', table_name='curiosity_events')
    op.drop_index('ix_curiosity_events_type', table_name='curiosity_events')
    op.drop_index('ix_curiosity_events_child_time', table_name='curiosity_events')
    op.drop_index('ix_curiosity_events_timestamp', table_name='curiosity_events')
    op.drop_index('ix_curiosity_events_entity', table_name='curiosity_events')
    op.drop_index('ix_curiosity_events_session', table_name='curiosity_events')
    op.drop_index('ix_curiosity_events_child', table_name='curiosity_events')

    # Drop table
    op.drop_table('curiosity_events')
