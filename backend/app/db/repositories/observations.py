"""
Observation Repository - Developmental Observations.

Handles observations - the facts we notice about a child.
Supports temporal queries critical for developmental tracking.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Sequence, List

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import ObservationSource
from app.db.models_core import Observation
from app.db.repositories.base import BaseRepository


class ObservationRepository(BaseRepository[Observation]):
    """Repository for Observation operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Observation, session)

    async def create_observation(
        self,
        child_id: uuid.UUID,
        content: str,
        domain: str,
        source_type: ObservationSource,
        *,
        subdomain: Optional[str] = None,
        source_message_id: Optional[uuid.UUID] = None,
        source_video_id: Optional[uuid.UUID] = None,
        source_journal_id: Optional[uuid.UUID] = None,
        recorded_by: Optional[uuid.UUID] = None,
        t_valid: Optional[datetime] = None,
        child_age_months: Optional[int] = None,
        confidence: float = 0.7,
        is_clinical: bool = False
    ) -> Observation:
        """Create a new observation."""
        now = datetime.now(timezone.utc)
        return await self.create(
            child_id=child_id,
            content=content,
            domain=domain,
            subdomain=subdomain,
            source_type=source_type.value,
            source_message_id=source_message_id,
            source_video_id=source_video_id,
            source_journal_id=source_journal_id,
            recorded_by=recorded_by,
            t_valid=t_valid or now,
            t_created=now,
            child_age_months=child_age_months,
            confidence=confidence,
            is_clinical=is_clinical
        )

    async def get_child_observations(
        self,
        child_id: uuid.UUID,
        *,
        domain: Optional[str] = None,
        subdomain: Optional[str] = None,
        source_type: Optional[ObservationSource] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        clinical_only: bool = False,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> Sequence[Observation]:
        """
        Get observations for a child with filters.

        Supports temporal and domain filtering.
        """
        stmt = select(Observation).where(Observation.child_id == child_id)

        if domain:
            stmt = stmt.where(Observation.domain == domain)
        if subdomain:
            stmt = stmt.where(Observation.subdomain == subdomain)
        if source_type:
            stmt = stmt.where(Observation.source_type == source_type.value)
        if since:
            stmt = stmt.where(Observation.t_created >= since)
        if until:
            stmt = stmt.where(Observation.t_created <= until)
        if clinical_only:
            stmt = stmt.where(Observation.is_clinical == True)

        stmt = stmt.order_by(Observation.t_created.desc())

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_observations_by_domain(
        self,
        child_id: uuid.UUID
    ) -> dict[str, Sequence[Observation]]:
        """Get observations grouped by domain."""
        all_obs = await self.get_child_observations(child_id)

        grouped = {}
        for obs in all_obs:
            if obs.domain not in grouped:
                grouped[obs.domain] = []
            grouped[obs.domain].append(obs)

        return grouped

    async def get_domain_counts(
        self,
        child_id: uuid.UUID
    ) -> dict[str, int]:
        """Get count of observations per domain."""
        stmt = select(
            Observation.domain,
            func.count(Observation.id).label("count")
        ).where(
            Observation.child_id == child_id
        ).group_by(Observation.domain)

        result = await self.session.execute(stmt)
        return {row.domain: row.count for row in result}

    async def get_observations_valid_at(
        self,
        child_id: uuid.UUID,
        point_in_time: datetime,
        *,
        domain: Optional[str] = None
    ) -> Sequence[Observation]:
        """
        Get observations that were valid at a specific point in time.

        This is key for temporal queries like "What did we know in March?"
        """
        stmt = select(Observation).where(
            and_(
                Observation.child_id == child_id,
                Observation.t_valid <= point_in_time,
                or_(
                    Observation.t_valid_end.is_(None),
                    Observation.t_valid_end > point_in_time
                )
            )
        )

        if domain:
            stmt = stmt.where(Observation.domain == domain)

        stmt = stmt.order_by(Observation.t_valid.desc())

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_observations_since(
        self,
        child_id: uuid.UUID,
        since: datetime,
        *,
        domain: Optional[str] = None
    ) -> Sequence[Observation]:
        """Get observations created since a timestamp."""
        stmt = select(Observation).where(
            and_(
                Observation.child_id == child_id,
                Observation.t_created > since
            )
        )

        if domain:
            stmt = stmt.where(Observation.domain == domain)

        stmt = stmt.order_by(Observation.t_created.asc())

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_latest_observation_time(
        self,
        child_id: uuid.UUID
    ) -> Optional[datetime]:
        """Get timestamp of most recent observation."""
        stmt = select(func.max(Observation.t_created)).where(
            Observation.child_id == child_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_observations_from_session(
        self,
        session_id: uuid.UUID
    ) -> Sequence[Observation]:
        """Get all observations extracted from a specific session's messages."""
        stmt = select(Observation).join(
            Observation.source_message
        ).where(
            Observation.source_message.has(session_id=session_id)
        ).order_by(Observation.t_created)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_observations_from_video(
        self,
        video_id: uuid.UUID
    ) -> Sequence[Observation]:
        """Get observations extracted from a video."""
        return await self.get_many_by_field("source_video_id", video_id)

    async def get_observations_from_journal(
        self,
        journal_id: uuid.UUID
    ) -> Sequence[Observation]:
        """Get observations extracted from a journal entry."""
        return await self.get_many_by_field("source_journal_id", journal_id)

    async def get_high_confidence_observations(
        self,
        child_id: uuid.UUID,
        min_confidence: float = 0.8,
        *,
        domain: Optional[str] = None
    ) -> Sequence[Observation]:
        """Get high confidence observations."""
        stmt = select(Observation).where(
            and_(
                Observation.child_id == child_id,
                Observation.confidence >= min_confidence
            )
        )

        if domain:
            stmt = stmt.where(Observation.domain == domain)

        stmt = stmt.order_by(Observation.confidence.desc())

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def mark_observation_ended(
        self,
        observation_id: uuid.UUID,
        ended_at: Optional[datetime] = None
    ) -> Optional[Observation]:
        """
        Mark an observation as no longer valid.

        Used when a behavior/characteristic is no longer observed.
        """
        return await self.update(
            observation_id,
            t_valid_end=ended_at or datetime.now(timezone.utc)
        )

    async def update_confidence(
        self,
        observation_id: uuid.UUID,
        new_confidence: float
    ) -> Optional[Observation]:
        """Update observation confidence."""
        return await self.update(observation_id, confidence=new_confidence)

    async def get_observations_by_recorder(
        self,
        child_id: uuid.UUID,
        recorder_id: uuid.UUID
    ) -> Sequence[Observation]:
        """Get observations recorded by a specific user."""
        stmt = select(Observation).where(
            and_(
                Observation.child_id == child_id,
                Observation.recorded_by == recorder_id
            )
        ).order_by(Observation.t_created.desc())

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def search_observations(
        self,
        child_id: uuid.UUID,
        query: str,
        *,
        limit: int = 50
    ) -> Sequence[Observation]:
        """Search observations by content."""
        stmt = select(Observation).where(
            and_(
                Observation.child_id == child_id,
                Observation.content.ilike(f"%{query}%")
            )
        ).order_by(Observation.t_created.desc()).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()
