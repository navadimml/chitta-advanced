"""
Dashboard Repository - Data Access for Team Dashboard.

Provides data access for:
- Cognitive turns (cognitive traces for dashboard)
- Expert corrections
- Missed signals
- Clinical notes
- Inference flags
- Certainty adjustments
- Expert evidence
- Dashboard-specific queries (children with stats, etc.)
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Tuple, Any, Dict, Sequence

from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base import BaseRepository
from app.db.models_dashboard import (
    CognitiveTurn,
    ExpertCorrection,
    MissedSignal,
    ClinicalNote,
    InferenceFlag,
    CertaintyAdjustment,
    ExpertEvidence,
)


# =============================================================================
# COGNITIVE TRACE REPOSITORIES
# =============================================================================


class CognitiveTurnRepository(BaseRepository[CognitiveTurn]):
    """Repository for cognitive turns (cognitive traces)."""

    def __init__(self, session: AsyncSession):
        super().__init__(CognitiveTurn, session)

    async def get_by_child(
        self,
        child_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[CognitiveTurn]:
        """Get cognitive turns for a child, ordered by turn number."""
        stmt = (
            select(self.model)
            .where(self.model.child_id == child_id)
            .order_by(self.model.turn_number)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_turn_id(self, turn_id: str) -> Optional[CognitiveTurn]:
        """Get a specific turn by turn_id."""
        stmt = select(self.model).where(self.model.turn_id == turn_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_turn(
        self,
        turn_id: str,
        turn_number: int,
        child_id: str,
        timestamp: datetime,
        parent_message: str,
        parent_role: Optional[str] = None,
        tool_calls: Optional[List[Dict]] = None,
        perceived_intent: Optional[str] = None,
        state_delta: Optional[Dict] = None,
        turn_guidance: Optional[str] = None,
        active_curiosities: Optional[List[str]] = None,
        response_text: Optional[str] = None,
    ) -> CognitiveTurn:
        """Create a new cognitive turn."""
        return await self.create(
            turn_id=turn_id,
            turn_number=turn_number,
            child_id=child_id,
            timestamp=timestamp,
            parent_message=parent_message,
            parent_role=parent_role,
            tool_calls=tool_calls,
            perceived_intent=perceived_intent,
            state_delta=state_delta,
            turn_guidance=turn_guidance,
            active_curiosities=active_curiosities,
            response_text=response_text,
        )

    async def count_by_child(self, child_id: str) -> int:
        """Count turns for a child."""
        stmt = (
            select(func.count())
            .select_from(self.model)
            .where(self.model.child_id == child_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()


class ExpertCorrectionRepository(BaseRepository[ExpertCorrection]):
    """Repository for expert corrections."""

    def __init__(self, session: AsyncSession):
        super().__init__(ExpertCorrection, session)

    async def get_by_turn(self, turn_id: str) -> Sequence[ExpertCorrection]:
        """Get all corrections for a turn."""
        stmt = (
            select(self.model)
            .where(self.model.turn_id == turn_id)
            .order_by(self.model.created_at)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_child(
        self,
        child_id: str,
        *,
        correction_type: Optional[str] = None,
        used_in_training: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[ExpertCorrection]:
        """Get corrections for a child."""
        stmt = select(self.model).where(self.model.child_id == child_id)

        if correction_type:
            stmt = stmt.where(self.model.correction_type == correction_type)
        if used_in_training is not None:
            stmt = stmt.where(self.model.used_in_training == used_in_training)

        stmt = stmt.order_by(desc(self.model.created_at))
        stmt = stmt.offset(offset).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create_correction(
        self,
        turn_id: str,
        child_id: str,
        target_type: str,
        correction_type: str,
        expert_reasoning: str,
        expert_id: uuid.UUID,
        expert_name: str,
        target_id: Optional[str] = None,
        original_value: Optional[Dict] = None,
        corrected_value: Optional[Dict] = None,
        severity: str = "medium",
    ) -> ExpertCorrection:
        """Create a new expert correction."""
        return await self.create(
            turn_id=turn_id,
            child_id=child_id,
            target_type=target_type,
            target_id=target_id,
            correction_type=correction_type,
            original_value=original_value,
            corrected_value=corrected_value,
            expert_reasoning=expert_reasoning,
            expert_id=expert_id,
            expert_name=expert_name,
            severity=severity,
        )

    async def mark_used_in_training(
        self,
        correction_id: uuid.UUID,
        training_batch_id: str,
    ) -> Optional[ExpertCorrection]:
        """Mark a correction as used in training."""
        correction = await self.get_by_id(correction_id)
        if not correction:
            return None

        correction.used_in_training = True
        correction.training_batch_id = training_batch_id
        await self.session.flush()
        await self.session.refresh(correction)
        return correction

    async def get_unused_for_training(
        self,
        limit: int = 100,
    ) -> Sequence[ExpertCorrection]:
        """Get corrections not yet used in training."""
        stmt = (
            select(self.model)
            .where(self.model.used_in_training == False)
            .order_by(self.model.created_at)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_correction_stats(self) -> Dict[str, Any]:
        """Get aggregated statistics on all corrections for analysis."""
        # Count by correction type
        type_stmt = (
            select(
                self.model.correction_type,
                func.count().label("count"),
            )
            .group_by(self.model.correction_type)
        )
        type_result = await self.session.execute(type_stmt)
        by_type = {row.correction_type: row.count for row in type_result}

        # Count by severity
        severity_stmt = (
            select(
                self.model.severity,
                func.count().label("count"),
            )
            .group_by(self.model.severity)
        )
        severity_result = await self.session.execute(severity_stmt)
        by_severity = {row.severity: row.count for row in severity_result}

        # Count by target type
        target_stmt = (
            select(
                self.model.target_type,
                func.count().label("count"),
            )
            .group_by(self.model.target_type)
        )
        target_result = await self.session.execute(target_stmt)
        by_target = {row.target_type: row.count for row in target_result}

        # Total count
        total_stmt = select(func.count()).select_from(self.model)
        total_result = await self.session.execute(total_stmt)
        total = total_result.scalar_one()

        # Unused count
        unused_stmt = (
            select(func.count())
            .select_from(self.model)
            .where(self.model.used_in_training == False)
        )
        unused_result = await self.session.execute(unused_stmt)
        unused = unused_result.scalar_one()

        return {
            "total": total,
            "unused_for_training": unused,
            "by_type": by_type,
            "by_severity": by_severity,
            "by_target_type": by_target,
        }

    async def get_all_with_context(
        self,
        used_in_training: Optional[bool] = None,
        correction_type: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> Sequence[ExpertCorrection]:
        """Get all corrections with optional filters for analysis."""
        stmt = select(self.model)

        if used_in_training is not None:
            stmt = stmt.where(self.model.used_in_training == used_in_training)
        if correction_type:
            stmt = stmt.where(self.model.correction_type == correction_type)
        if severity:
            stmt = stmt.where(self.model.severity == severity)

        stmt = stmt.order_by(desc(self.model.created_at))
        result = await self.session.execute(stmt)
        return result.scalars().all()


class MissedSignalRepository(BaseRepository[MissedSignal]):
    """Repository for missed signals."""

    def __init__(self, session: AsyncSession):
        super().__init__(MissedSignal, session)

    async def get_by_turn(self, turn_id: str) -> Sequence[MissedSignal]:
        """Get all missed signals for a turn."""
        stmt = (
            select(self.model)
            .where(self.model.turn_id == turn_id)
            .order_by(self.model.created_at)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_child(
        self,
        child_id: str,
        *,
        signal_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[MissedSignal]:
        """Get missed signals for a child."""
        stmt = select(self.model).where(self.model.child_id == child_id)

        if signal_type:
            stmt = stmt.where(self.model.signal_type == signal_type)

        stmt = stmt.order_by(desc(self.model.created_at))
        stmt = stmt.offset(offset).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create_missed_signal(
        self,
        turn_id: str,
        child_id: str,
        signal_type: str,
        content: str,
        why_important: str,
        expert_id: uuid.UUID,
        expert_name: str,
        domain: Optional[str] = None,
    ) -> MissedSignal:
        """Create a new missed signal record."""
        return await self.create(
            turn_id=turn_id,
            child_id=child_id,
            signal_type=signal_type,
            content=content,
            domain=domain,
            why_important=why_important,
            expert_id=expert_id,
            expert_name=expert_name,
        )

    async def get_signal_stats(self) -> Dict[str, Any]:
        """Get aggregated statistics on missed signals."""
        # Count by signal type
        type_stmt = (
            select(
                self.model.signal_type,
                func.count().label("count"),
            )
            .group_by(self.model.signal_type)
        )
        type_result = await self.session.execute(type_stmt)
        by_type = {row.signal_type: row.count for row in type_result}

        # Count by domain
        domain_stmt = (
            select(
                self.model.domain,
                func.count().label("count"),
            )
            .where(self.model.domain.isnot(None))
            .group_by(self.model.domain)
        )
        domain_result = await self.session.execute(domain_stmt)
        by_domain = {row.domain: row.count for row in domain_result}

        # Total count
        total_stmt = select(func.count()).select_from(self.model)
        total_result = await self.session.execute(total_stmt)
        total = total_result.scalar_one()

        return {
            "total": total,
            "by_signal_type": by_type,
            "by_domain": by_domain,
        }

    async def get_all(self) -> Sequence[MissedSignal]:
        """Get all missed signals for analysis."""
        stmt = select(self.model).order_by(desc(self.model.created_at))
        result = await self.session.execute(stmt)
        return result.scalars().all()


# =============================================================================
# EXISTING REPOSITORIES
# =============================================================================


class ClinicalNoteRepository(BaseRepository[ClinicalNote]):
    """Repository for clinical notes."""

    def __init__(self, session: AsyncSession):
        super().__init__(ClinicalNote, session)

    async def get_by_child(
        self,
        child_id: str,
        *,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        include_deleted: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[ClinicalNote]:
        """Get notes for a child, optionally filtered by target."""
        stmt = select(self.model).where(self.model.child_id == child_id)

        if target_type:
            stmt = stmt.where(self.model.target_type == target_type)
        if target_id:
            stmt = stmt.where(self.model.target_id == target_id)
        if not include_deleted:
            stmt = stmt.where(self.model.deleted_at.is_(None))

        stmt = stmt.order_by(desc(self.model.created_at))
        stmt = stmt.offset(offset).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create_note(
        self,
        child_id: str,
        target_type: str,
        target_id: str,
        content: str,
        author_id: uuid.UUID,
        author_name: str,
        note_type: str = "annotation",
    ) -> ClinicalNote:
        """Create a new clinical note."""
        return await self.create(
            child_id=child_id,
            target_type=target_type,
            target_id=target_id,
            content=content,
            note_type=note_type,
            author_id=author_id,
            author_name=author_name,
        )

    async def soft_delete(self, note_id: uuid.UUID) -> bool:
        """Soft delete a note."""
        note = await self.get_by_id(note_id)
        if not note:
            return False
        note.deleted_at = datetime.now(timezone.utc)
        await self.session.flush()
        return True


class InferenceFlagRepository(BaseRepository[InferenceFlag]):
    """Repository for inference flags."""

    def __init__(self, session: AsyncSession):
        super().__init__(InferenceFlag, session)

    async def get_by_child(
        self,
        child_id: str,
        *,
        include_resolved: bool = False,
        target_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[InferenceFlag]:
        """Get flags for a child."""
        stmt = select(self.model).where(self.model.child_id == child_id)

        if not include_resolved:
            stmt = stmt.where(self.model.resolved_at.is_(None))
        if target_type:
            stmt = stmt.where(self.model.target_type == target_type)

        stmt = stmt.order_by(desc(self.model.created_at))
        stmt = stmt.offset(offset).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create_flag(
        self,
        child_id: str,
        target_type: str,
        target_id: str,
        flag_type: str,
        reason: str,
        author_id: uuid.UUID,
        author_name: str,
        suggested_correction: Optional[str] = None,
    ) -> InferenceFlag:
        """Create a new inference flag."""
        return await self.create(
            child_id=child_id,
            target_type=target_type,
            target_id=target_id,
            flag_type=flag_type,
            reason=reason,
            suggested_correction=suggested_correction,
            author_id=author_id,
            author_name=author_name,
        )

    async def resolve(
        self,
        flag_id: uuid.UUID,
        resolved_by_id: uuid.UUID,
        resolved_by_name: str,
        resolution_notes: str,
    ) -> Optional[InferenceFlag]:
        """Resolve a flag."""
        flag = await self.get_by_id(flag_id)
        if not flag or flag.resolved_at:
            return None

        flag.resolved_at = datetime.now(timezone.utc)
        flag.resolved_by_id = resolved_by_id
        flag.resolved_by_name = resolved_by_name
        flag.resolution_notes = resolution_notes
        await self.session.flush()
        await self.session.refresh(flag)
        return flag

    async def count_unresolved(self, child_id: Optional[str] = None) -> int:
        """Count unresolved flags."""
        stmt = select(func.count()).select_from(self.model).where(
            self.model.resolved_at.is_(None)
        )
        if child_id:
            stmt = stmt.where(self.model.child_id == child_id)

        result = await self.session.execute(stmt)
        return result.scalar_one()


class CertaintyAdjustmentRepository(BaseRepository[CertaintyAdjustment]):
    """Repository for certainty adjustments."""

    def __init__(self, session: AsyncSession):
        super().__init__(CertaintyAdjustment, session)

    async def get_by_child(
        self,
        child_id: str,
        *,
        curiosity_focus: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[CertaintyAdjustment]:
        """Get adjustments for a child."""
        stmt = select(self.model).where(self.model.child_id == child_id)

        if curiosity_focus:
            stmt = stmt.where(self.model.curiosity_focus == curiosity_focus)

        stmt = stmt.order_by(desc(self.model.created_at))
        stmt = stmt.offset(offset).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create_adjustment(
        self,
        child_id: str,
        curiosity_focus: str,
        original_certainty: float,
        adjusted_certainty: float,
        reason: str,
        author_id: uuid.UUID,
        author_name: str,
    ) -> CertaintyAdjustment:
        """Record a certainty adjustment."""
        return await self.create(
            child_id=child_id,
            curiosity_focus=curiosity_focus,
            original_certainty=original_certainty,
            adjusted_certainty=adjusted_certainty,
            reason=reason,
            author_id=author_id,
            author_name=author_name,
        )


class ExpertEvidenceRepository(BaseRepository[ExpertEvidence]):
    """Repository for expert-added evidence."""

    def __init__(self, session: AsyncSession):
        super().__init__(ExpertEvidence, session)

    async def get_by_child(
        self,
        child_id: str,
        *,
        curiosity_focus: Optional[str] = None,
        include_unapplied_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[ExpertEvidence]:
        """Get expert evidence for a child."""
        stmt = select(self.model).where(self.model.child_id == child_id)

        if curiosity_focus:
            stmt = stmt.where(self.model.curiosity_focus == curiosity_focus)
        if include_unapplied_only:
            stmt = stmt.where(self.model.applied_at.is_(None))

        stmt = stmt.order_by(desc(self.model.created_at))
        stmt = stmt.offset(offset).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create_evidence(
        self,
        child_id: str,
        curiosity_focus: str,
        content: str,
        effect: str,
        author_id: uuid.UUID,
        author_name: str,
    ) -> ExpertEvidence:
        """Create new expert evidence."""
        return await self.create(
            child_id=child_id,
            curiosity_focus=curiosity_focus,
            content=content,
            effect=effect,
            author_id=author_id,
            author_name=author_name,
        )

    async def mark_applied(self, evidence_id: uuid.UUID) -> Optional[ExpertEvidence]:
        """Mark evidence as applied to Darshan."""
        evidence = await self.get_by_id(evidence_id)
        if not evidence:
            return None

        evidence.applied_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(evidence)
        return evidence


class DashboardRepository:
    """
    Composite repository for dashboard operations.

    Provides access to all dashboard-related sub-repositories
    and aggregate queries.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self._notes: Optional[ClinicalNoteRepository] = None
        self._flags: Optional[InferenceFlagRepository] = None
        self._adjustments: Optional[CertaintyAdjustmentRepository] = None
        self._evidence: Optional[ExpertEvidenceRepository] = None
        # Cognitive trace repositories
        self._cognitive_turns: Optional[CognitiveTurnRepository] = None
        self._corrections: Optional[ExpertCorrectionRepository] = None
        self._missed_signals: Optional[MissedSignalRepository] = None

    @property
    def notes(self) -> ClinicalNoteRepository:
        if self._notes is None:
            self._notes = ClinicalNoteRepository(self.session)
        return self._notes

    @property
    def flags(self) -> InferenceFlagRepository:
        if self._flags is None:
            self._flags = InferenceFlagRepository(self.session)
        return self._flags

    @property
    def adjustments(self) -> CertaintyAdjustmentRepository:
        if self._adjustments is None:
            self._adjustments = CertaintyAdjustmentRepository(self.session)
        return self._adjustments

    @property
    def evidence(self) -> ExpertEvidenceRepository:
        if self._evidence is None:
            self._evidence = ExpertEvidenceRepository(self.session)
        return self._evidence

    @property
    def cognitive_turns(self) -> CognitiveTurnRepository:
        if self._cognitive_turns is None:
            self._cognitive_turns = CognitiveTurnRepository(self.session)
        return self._cognitive_turns

    @property
    def corrections(self) -> ExpertCorrectionRepository:
        if self._corrections is None:
            self._corrections = ExpertCorrectionRepository(self.session)
        return self._corrections

    @property
    def missed_signals(self) -> MissedSignalRepository:
        if self._missed_signals is None:
            self._missed_signals = MissedSignalRepository(self.session)
        return self._missed_signals

    async def get_child_feedback_summary(self, child_id: str) -> Dict[str, Any]:
        """Get summary of all feedback for a child."""
        notes_count = await self.notes.count(filters={"child_id": child_id})
        flags_unresolved = await self.flags.count_unresolved(child_id)
        adjustments = await self.adjustments.get_by_child(child_id, limit=5)

        return {
            "notes_count": notes_count,
            "unresolved_flags_count": flags_unresolved,
            "recent_adjustments": [
                {
                    "curiosity_focus": adj.curiosity_focus,
                    "delta": adj.delta,
                    "created_at": adj.created_at.isoformat(),
                }
                for adj in adjustments
            ],
        }
