"""
Exploration Repository - Curiosity and Understanding.

Handles:
- Explorations (questions, hypotheses, patterns)
- Exploration history (confidence tracking over time)
- Evidence (links observations to explorations)
- Stories (rich narratives from parents)
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Sequence, List

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.base import CuriosityType, ExplorationStatus, EvidenceRelation, StoryStatus
from app.db.models_exploration import (
    Exploration,
    ExplorationHistory,
    Evidence,
    Story,
    StoryDomain,
    StoryReveal,
)
from app.db.repositories.base import BaseRepository


class ExplorationRepository(BaseRepository[Exploration]):
    """Repository for Exploration operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Exploration, session)

    async def create_exploration(
        self,
        child_id: uuid.UUID,
        focus: str,
        exploration_type: CuriosityType,
        domain: str,
        *,
        subdomain: Optional[str] = None,
        certainty: float = 0.3,
        pull: float = 0.5,
        context: Optional[str] = None,
        parent_exploration_id: Optional[uuid.UUID] = None
    ) -> Exploration:
        """Create a new exploration."""
        now = datetime.now(timezone.utc)
        return await self.create(
            child_id=child_id,
            focus=focus,
            exploration_type=exploration_type.value,
            domain=domain,
            subdomain=subdomain,
            status=ExplorationStatus.ACTIVE.value,
            certainty=certainty,
            pull=pull,
            context=context,
            parent_exploration_id=parent_exploration_id,
            t_opened=now,
            last_activated=now,
            based_on_observations_through=now
        )

    async def get_active_explorations(
        self,
        child_id: uuid.UUID,
        *,
        domain: Optional[str] = None,
        exploration_type: Optional[CuriosityType] = None,
        min_pull: Optional[float] = None
    ) -> Sequence[Exploration]:
        """Get active explorations for a child."""
        stmt = select(Exploration).where(
            and_(
                Exploration.child_id == child_id,
                Exploration.status == ExplorationStatus.ACTIVE.value
            )
        )

        if domain:
            stmt = stmt.where(Exploration.domain == domain)
        if exploration_type:
            stmt = stmt.where(Exploration.exploration_type == exploration_type.value)
        if min_pull is not None:
            stmt = stmt.where(Exploration.pull >= min_pull)

        stmt = stmt.order_by(Exploration.pull.desc())

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_top_explorations(
        self,
        child_id: uuid.UUID,
        limit: int = 5
    ) -> Sequence[Exploration]:
        """Get top explorations by pull."""
        stmt = select(Exploration).where(
            and_(
                Exploration.child_id == child_id,
                Exploration.status == ExplorationStatus.ACTIVE.value
            )
        ).order_by(Exploration.pull.desc()).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_hypotheses(
        self,
        child_id: uuid.UUID,
        *,
        min_certainty: Optional[float] = None
    ) -> Sequence[Exploration]:
        """Get hypothesis-type explorations."""
        stmt = select(Exploration).where(
            and_(
                Exploration.child_id == child_id,
                Exploration.exploration_type == CuriosityType.HYPOTHESIS.value,
                Exploration.status == ExplorationStatus.ACTIVE.value
            )
        )

        if min_certainty is not None:
            stmt = stmt.where(Exploration.certainty >= min_certainty)

        stmt = stmt.order_by(Exploration.certainty.desc())

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_certainty(
        self,
        exploration_id: uuid.UUID,
        new_certainty: float,
        *,
        trigger_type: str = "evidence",
        trigger_observation_id: Optional[uuid.UUID] = None,
        trigger_note: Optional[str] = None
    ) -> Optional[Exploration]:
        """Update exploration certainty and record in history."""
        exploration = await self.get_by_id(exploration_id)
        if not exploration:
            return None

        old_certainty = exploration.certainty

        # Update exploration
        exploration.certainty = max(0.0, min(1.0, new_certainty))
        exploration.last_activated = datetime.now(timezone.utc)
        exploration.times_explored += 1
        exploration.based_on_observations_through = datetime.now(timezone.utc)

        # Record history
        history = ExplorationHistory(
            exploration_id=exploration_id,
            certainty=new_certainty,
            status=exploration.status,
            pull=exploration.pull,
            recorded_at=datetime.now(timezone.utc),
            trigger_type=trigger_type,
            trigger_observation_id=trigger_observation_id,
            trigger_note=trigger_note,
            certainty_delta=new_certainty - old_certainty
        )
        self.session.add(history)

        await self.session.flush()
        return exploration

    async def update_pull(
        self,
        exploration_id: uuid.UUID,
        new_pull: float
    ) -> Optional[Exploration]:
        """Update exploration pull (priority)."""
        return await self.update(
            exploration_id,
            pull=max(0.0, min(1.0, new_pull)),
            last_activated=datetime.now(timezone.utc)
        )

    async def satisfy_exploration(
        self,
        exploration_id: uuid.UUID,
        resolution_note: Optional[str] = None
    ) -> Optional[Exploration]:
        """Mark exploration as satisfied."""
        return await self.update(
            exploration_id,
            status=ExplorationStatus.SATISFIED.value,
            resolved_at=datetime.now(timezone.utc),
            resolution_note=resolution_note
        )

    async def supersede_exploration(
        self,
        exploration_id: uuid.UUID,
        superseded_by_id: uuid.UUID,
        resolution_note: Optional[str] = None
    ) -> Optional[Exploration]:
        """Mark exploration as superseded by another."""
        return await self.update(
            exploration_id,
            status=ExplorationStatus.SUPERSEDED.value,
            superseded_by_id=superseded_by_id,
            resolved_at=datetime.now(timezone.utc),
            resolution_note=resolution_note
        )

    async def get_stale_explorations(
        self,
        child_id: uuid.UUID,
        latest_observation_time: datetime
    ) -> Sequence[Exploration]:
        """Get explorations that might be stale based on new observations."""
        stmt = select(Exploration).where(
            and_(
                Exploration.child_id == child_id,
                Exploration.status == ExplorationStatus.ACTIVE.value,
                Exploration.based_on_observations_through < latest_observation_time
            )
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_with_evidence(
        self,
        exploration_id: uuid.UUID
    ) -> Optional[Exploration]:
        """Get exploration with evidence links loaded."""
        return await self.get_by_id(
            exploration_id,
            load_relations=["evidence_links", "history"]
        )


class ExplorationHistoryRepository(BaseRepository[ExplorationHistory]):
    """Repository for Exploration History operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(ExplorationHistory, session)

    async def get_exploration_history(
        self,
        exploration_id: uuid.UUID,
        *,
        limit: Optional[int] = None
    ) -> Sequence[ExplorationHistory]:
        """Get history for an exploration."""
        stmt = select(ExplorationHistory).where(
            ExplorationHistory.exploration_id == exploration_id
        ).order_by(ExplorationHistory.recorded_at.desc())

        if limit:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_certainty_at_time(
        self,
        exploration_id: uuid.UUID,
        point_in_time: datetime
    ) -> Optional[float]:
        """Get certainty value at a specific point in time."""
        stmt = select(ExplorationHistory).where(
            and_(
                ExplorationHistory.exploration_id == exploration_id,
                ExplorationHistory.recorded_at <= point_in_time
            )
        ).order_by(ExplorationHistory.recorded_at.desc()).limit(1)

        result = await self.session.execute(stmt)
        history = result.scalar_one_or_none()
        return history.certainty if history else None


class EvidenceRepository(BaseRepository[Evidence]):
    """Repository for Evidence operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Evidence, session)

    async def link_evidence(
        self,
        exploration_id: uuid.UUID,
        observation_id: uuid.UUID,
        relation: EvidenceRelation,
        *,
        strength: float = 0.5,
        note: Optional[str] = None
    ) -> Evidence:
        """Link an observation as evidence for an exploration."""
        return await self.create(
            exploration_id=exploration_id,
            observation_id=observation_id,
            relation=relation.value,
            strength=strength,
            note=note,
            linked_at=datetime.now(timezone.utc)
        )

    async def get_exploration_evidence(
        self,
        exploration_id: uuid.UUID
    ) -> Sequence[Evidence]:
        """Get all evidence for an exploration."""
        stmt = select(Evidence).where(
            Evidence.exploration_id == exploration_id
        ).options(selectinload(Evidence.observation))

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_supporting_evidence(
        self,
        exploration_id: uuid.UUID
    ) -> Sequence[Evidence]:
        """Get supporting evidence for an exploration."""
        stmt = select(Evidence).where(
            and_(
                Evidence.exploration_id == exploration_id,
                Evidence.relation == EvidenceRelation.SUPPORTS.value
            )
        ).options(selectinload(Evidence.observation))

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_contradicting_evidence(
        self,
        exploration_id: uuid.UUID
    ) -> Sequence[Evidence]:
        """Get contradicting evidence for an exploration."""
        stmt = select(Evidence).where(
            and_(
                Evidence.exploration_id == exploration_id,
                Evidence.relation == EvidenceRelation.CONTRADICTS.value
            )
        ).options(selectinload(Evidence.observation))

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def is_observation_linked(
        self,
        exploration_id: uuid.UUID,
        observation_id: uuid.UUID
    ) -> bool:
        """Check if observation is already linked to exploration."""
        stmt = select(func.count()).where(
            and_(
                Evidence.exploration_id == exploration_id,
                Evidence.observation_id == observation_id
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() > 0


class StoryRepository(BaseRepository[Story]):
    """Repository for Story operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Story, session)

    async def create_story(
        self,
        child_id: uuid.UUID,
        title: str,
        narrative: str,
        *,
        context: Optional[str] = None,
        occurred_at: Optional[datetime] = None,
        child_age_months: Optional[int] = None,
        source_session_id: Optional[uuid.UUID] = None,
        emotional_tone: Optional[str] = None,
        parent_interpretation: Optional[str] = None,
        domains: Optional[List[tuple[str, float]]] = None
    ) -> Story:
        """Create a new story with optional domains."""
        now = datetime.now(timezone.utc)
        story = await self.create(
            child_id=child_id,
            title=title,
            narrative=narrative,
            context=context,
            status=StoryStatus.CAPTURED.value,
            occurred_at=occurred_at,
            recorded_at=now,
            child_age_months=child_age_months,
            source_session_id=source_session_id,
            emotional_tone=emotional_tone,
            parent_interpretation=parent_interpretation
        )

        # Add domains if provided
        if domains:
            for domain_name, relevance in domains:
                domain = StoryDomain(
                    story_id=story.id,
                    domain=domain_name,
                    relevance=relevance
                )
                self.session.add(domain)

        await self.session.flush()
        return story

    async def get_child_stories(
        self,
        child_id: uuid.UUID,
        *,
        domain: Optional[str] = None,
        status: Optional[StoryStatus] = None,
        limit: Optional[int] = None
    ) -> Sequence[Story]:
        """Get stories for a child."""
        stmt = select(Story).where(Story.child_id == child_id)

        if status:
            stmt = stmt.where(Story.status == status.value)

        stmt = stmt.order_by(Story.recorded_at.desc())

        if limit:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        stories = result.scalars().all()

        # Filter by domain if specified (requires join)
        if domain:
            # This is inefficient but works for now
            filtered = []
            for story in stories:
                await self.session.refresh(story, ["domains"])
                if any(d.domain == domain for d in story.domains):
                    filtered.append(story)
            return filtered

        return stories

    async def get_with_reveals(
        self,
        story_id: uuid.UUID
    ) -> Optional[Story]:
        """Get story with domains and reveals loaded."""
        return await self.get_by_id(
            story_id,
            load_relations=["domains", "reveals"]
        )

    async def add_reveal(
        self,
        story_id: uuid.UUID,
        insight: str,
        domain: str,
        confidence: float = 0.5
    ) -> StoryReveal:
        """Add a reveal (insight) to a story."""
        reveal = StoryReveal(
            story_id=story_id,
            insight=insight,
            domain=domain,
            confidence=confidence
        )
        self.session.add(reveal)
        await self.session.flush()
        return reveal

    async def mark_integrated(
        self,
        story_id: uuid.UUID
    ) -> Optional[Story]:
        """Mark story as integrated into understanding."""
        return await self.update(
            story_id,
            status=StoryStatus.INTEGRATED.value
        )

    async def get_unintegrated_stories(
        self,
        child_id: uuid.UUID
    ) -> Sequence[Story]:
        """Get stories not yet integrated."""
        return await self.get_many_by_field("status", StoryStatus.CAPTURED.value)
