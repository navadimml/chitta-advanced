"""Add dashboard tables for expert review

Revision ID: e4b9c2d3f5a6
Revises: d3a7b8f1e29c
Create Date: 2025-12-24

Adds tables for the team dashboard:
- clinical_notes: Team-visible annotations on any element
- inference_flags: Flag incorrect AI inferences with resolution workflow
- certainty_adjustments: Audit trail for expert certainty adjustments
- expert_evidence: Evidence added by clinical experts
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'e4b9c2d3f5a6'
down_revision = 'd3a7b8f1e29c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================================================
    # Clinical Notes Table
    # ==========================================================================
    op.create_table(
        'clinical_notes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('child_id', sa.String(50), nullable=False),
        sa.Column('target_type', sa.String(50), nullable=False),
        sa.Column('target_id', sa.String(200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('note_type', sa.String(20), server_default='annotation', nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('author_name', sa.String(100), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_clinical_notes_child', 'clinical_notes', ['child_id'])
    op.create_index('ix_clinical_notes_target', 'clinical_notes', ['target_type', 'target_id'])
    op.create_index('ix_clinical_notes_author', 'clinical_notes', ['author_id'])

    # ==========================================================================
    # Inference Flags Table
    # ==========================================================================
    op.create_table(
        'inference_flags',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('child_id', sa.String(50), nullable=False),
        sa.Column('target_type', sa.String(50), nullable=False),
        sa.Column('target_id', sa.String(200), nullable=False),
        sa.Column('flag_type', sa.String(20), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('suggested_correction', sa.Text(), nullable=True),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('author_name', sa.String(100), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('resolved_by_name', sa.String(100), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_inference_flags_child', 'inference_flags', ['child_id'])
    op.create_index('ix_inference_flags_target', 'inference_flags', ['target_type', 'target_id'])
    op.create_index('ix_inference_flags_unresolved', 'inference_flags', ['child_id', 'resolved_at'])
    op.create_index('ix_inference_flags_author', 'inference_flags', ['author_id'])

    # ==========================================================================
    # Certainty Adjustments Table
    # ==========================================================================
    op.create_table(
        'certainty_adjustments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('child_id', sa.String(50), nullable=False),
        sa.Column('curiosity_focus', sa.String(500), nullable=False),
        sa.Column('original_certainty', sa.Float(), nullable=False),
        sa.Column('adjusted_certainty', sa.Float(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('author_name', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_certainty_adjustments_child', 'certainty_adjustments', ['child_id'])
    op.create_index('ix_certainty_adjustments_author', 'certainty_adjustments', ['author_id'])

    # ==========================================================================
    # Expert Evidence Table
    # ==========================================================================
    op.create_table(
        'expert_evidence',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('child_id', sa.String(50), nullable=False),
        sa.Column('curiosity_focus', sa.String(500), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('effect', sa.String(20), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('author_name', sa.String(100), nullable=False),
        sa.Column('applied_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_expert_evidence_child', 'expert_evidence', ['child_id'])
    op.create_index('ix_expert_evidence_curiosity', 'expert_evidence', ['child_id', 'curiosity_focus'])
    op.create_index('ix_expert_evidence_author', 'expert_evidence', ['author_id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('ix_expert_evidence_author', table_name='expert_evidence')
    op.drop_index('ix_expert_evidence_curiosity', table_name='expert_evidence')
    op.drop_index('ix_expert_evidence_child', table_name='expert_evidence')
    op.drop_table('expert_evidence')

    op.drop_index('ix_certainty_adjustments_author', table_name='certainty_adjustments')
    op.drop_index('ix_certainty_adjustments_child', table_name='certainty_adjustments')
    op.drop_table('certainty_adjustments')

    op.drop_index('ix_inference_flags_author', table_name='inference_flags')
    op.drop_index('ix_inference_flags_unresolved', table_name='inference_flags')
    op.drop_index('ix_inference_flags_target', table_name='inference_flags')
    op.drop_index('ix_inference_flags_child', table_name='inference_flags')
    op.drop_table('inference_flags')

    op.drop_index('ix_clinical_notes_author', table_name='clinical_notes')
    op.drop_index('ix_clinical_notes_target', table_name='clinical_notes')
    op.drop_index('ix_clinical_notes_child', table_name='clinical_notes')
    op.drop_table('clinical_notes')
