"""
Synthesis Repository - Crystallized Understanding.

Handles:
- Patterns (cross-domain connections)
- Crystals (synthesized understanding)
- Portrait sections (structured output)
- Intervention pathways (recommendations)
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Sequence, List

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.base import PatternStatus, CrystalStatus
from app.db.models_synthesis import (
    Pattern,
    PatternDomain,
    Crystal,
    CrystalPattern,
    PortraitSection,
    InterventionPathway,
)
from app.db.repositories.base import BaseRepository


class PatternRepository(BaseRepository[Pattern]):
    """Repository for Pattern operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Pattern, session)

    async def create_pattern(
        self,
        child_id: uuid.UUID,
        description: str,
        pattern_type: str,
        domains: List[tuple[str, Optional[str]]],  # [(domain, manifestation), ...]
        *,
        significance: Optional[str] = None,
        confidence: float = 0.5
    ) -> Pattern:
        """Create a new pattern with domains."""
        now = datetime.now(timezone.utc)
        pattern = await self.create(
            child_id=child_id,
            description=description,
            pattern_type=pattern_type,
            significance=significance,
            status=PatternStatus.EMERGING.value,
            confidence=confidence,
            evidence_count=0,
            detected_at=now,
            based_on_observations_through=now
        )

        # Add domains
        for domain_name, manifestation in domains:
            domain = PatternDomain(
                pattern_id=pattern.id,
                domain=domain_name,
                manifestation=manifestation
            )
            self.session.add(domain)

        await self.session.flush()
        return pattern

    async def get_active_patterns(
        self,
        child_id: uuid.UUID,
        *,
        pattern_type: Optional[str] = None,
        min_confidence: Optional[float] = None
    ) -> Sequence[Pattern]:
        """Get active patterns for a child."""
        stmt = select(Pattern).where(
            and_(
                Pattern.child_id == child_id,
                Pattern.status.in_([
                    PatternStatus.EMERGING.value,
                    PatternStatus.ESTABLISHED.value,
                    PatternStatus.EVOLVING.value
                ])
            )
        )

        if pattern_type:
            stmt = stmt.where(Pattern.pattern_type == pattern_type)
        if min_confidence is not None:
            stmt = stmt.where(Pattern.confidence >= min_confidence)

        stmt = stmt.order_by(Pattern.confidence.desc())

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_established_patterns(
        self,
        child_id: uuid.UUID
    ) -> Sequence[Pattern]:
        """Get established (high confidence) patterns."""
        stmt = select(Pattern).where(
            and_(
                Pattern.child_id == child_id,
                Pattern.status == PatternStatus.ESTABLISHED.value
            )
        ).order_by(Pattern.confidence.desc())

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_pattern_confidence(
        self,
        pattern_id: uuid.UUID,
        new_confidence: float,
        *,
        increment_evidence: bool = True
    ) -> Optional[Pattern]:
        """Update pattern confidence."""
        pattern = await self.get_by_id(pattern_id)
        if not pattern:
            return None

        pattern.confidence = max(0.0, min(1.0, new_confidence))
        pattern.last_confirmed_at = datetime.now(timezone.utc)
        pattern.based_on_observations_through = datetime.now(timezone.utc)

        if increment_evidence:
            pattern.evidence_count += 1

        # Auto-promote to established if confidence high enough
        if pattern.confidence >= 0.8 and pattern.status == PatternStatus.EMERGING.value:
            pattern.status = PatternStatus.ESTABLISHED.value

        await self.session.flush()
        return pattern

    async def resolve_pattern(
        self,
        pattern_id: uuid.UUID,
        evolution_note: Optional[str] = None
    ) -> Optional[Pattern]:
        """Mark pattern as resolved."""
        return await self.update(
            pattern_id,
            status=PatternStatus.RESOLVED.value,
            resolved_at=datetime.now(timezone.utc),
            evolution_note=evolution_note
        )

    async def get_patterns_by_domain(
        self,
        child_id: uuid.UUID,
        domain: str
    ) -> Sequence[Pattern]:
        """Get patterns involving a specific domain."""
        stmt = select(Pattern).join(PatternDomain).where(
            and_(
                Pattern.child_id == child_id,
                PatternDomain.domain == domain
            )
        ).order_by(Pattern.confidence.desc())

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_with_domains(
        self,
        pattern_id: uuid.UUID
    ) -> Optional[Pattern]:
        """Get pattern with domains loaded."""
        return await self.get_by_id(pattern_id, load_relations=["domains"])


class CrystalRepository(BaseRepository[Crystal]):
    """Repository for Crystal operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Crystal, session)

    async def create_crystal(
        self,
        child_id: uuid.UUID,
        essence: str,
        based_on_observations_through: datetime,
        *,
        strengths_narrative: Optional[str] = None,
        growth_areas_narrative: Optional[str] = None,
        wonder_narrative: Optional[str] = None,
        richness_score: float = 0.0,
        observation_count: int = 0,
        story_count: int = 0,
        pattern_count: int = 0,
        model_used: Optional[str] = None,
        child_age_months: Optional[int] = None,
        pattern_ids: Optional[List[uuid.UUID]] = None
    ) -> Crystal:
        """Create a new crystal (versioned)."""
        # Get current version number
        stmt = select(func.coalesce(func.max(Crystal.version), 0)).where(
            Crystal.child_id == child_id
        )
        result = await self.session.execute(stmt)
        current_version = result.scalar_one()

        # Get previous crystal for linking
        previous_crystal = await self.get_latest_crystal(child_id)

        now = datetime.now(timezone.utc)
        crystal = await self.create(
            child_id=child_id,
            version=current_version + 1,
            previous_version_id=previous_crystal.id if previous_crystal else None,
            essence=essence,
            strengths_narrative=strengths_narrative,
            growth_areas_narrative=growth_areas_narrative,
            wonder_narrative=wonder_narrative,
            status=CrystalStatus.FORMING.value,
            richness_score=richness_score,
            synthesized_at=now,
            based_on_observations_through=based_on_observations_through,
            child_age_months_at_synthesis=child_age_months,
            observation_count=observation_count,
            story_count=story_count,
            pattern_count=pattern_count,
            model_used=model_used
        )

        # Link patterns
        if pattern_ids:
            for pattern_id in pattern_ids:
                link = CrystalPattern(
                    crystal_id=crystal.id,
                    pattern_id=pattern_id,
                    weight=1.0
                )
                self.session.add(link)

        await self.session.flush()
        return crystal

    async def get_latest_crystal(
        self,
        child_id: uuid.UUID
    ) -> Optional[Crystal]:
        """Get the most recent crystal for a child."""
        stmt = select(Crystal).where(
            Crystal.child_id == child_id
        ).order_by(Crystal.version.desc()).limit(1)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_stable_crystal(
        self,
        child_id: uuid.UUID
    ) -> Optional[Crystal]:
        """Get the latest stable crystal for a child."""
        stmt = select(Crystal).where(
            and_(
                Crystal.child_id == child_id,
                Crystal.status == CrystalStatus.STABLE.value
            )
        ).order_by(Crystal.version.desc()).limit(1)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_crystal_history(
        self,
        child_id: uuid.UUID,
        *,
        limit: int = 10
    ) -> Sequence[Crystal]:
        """Get crystal version history for a child."""
        stmt = select(Crystal).where(
            Crystal.child_id == child_id
        ).order_by(Crystal.version.desc()).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def mark_stable(
        self,
        crystal_id: uuid.UUID
    ) -> Optional[Crystal]:
        """Mark crystal as stable."""
        return await self.update(
            crystal_id,
            status=CrystalStatus.STABLE.value
        )

    async def mark_stale(
        self,
        crystal_id: uuid.UUID
    ) -> Optional[Crystal]:
        """Mark crystal as stale (needs refresh)."""
        return await self.update(
            crystal_id,
            status=CrystalStatus.STALE.value
        )

    async def is_crystal_stale(
        self,
        crystal_id: uuid.UUID,
        latest_observation_time: datetime
    ) -> bool:
        """Check if crystal is stale based on observation time."""
        crystal = await self.get_by_id(crystal_id)
        if not crystal:
            return True
        return crystal.based_on_observations_through < latest_observation_time

    async def get_with_patterns(
        self,
        crystal_id: uuid.UUID
    ) -> Optional[Crystal]:
        """Get crystal with patterns loaded."""
        return await self.get_by_id(crystal_id, load_relations=["patterns"])


class PortraitSectionRepository(BaseRepository[PortraitSection]):
    """Repository for Portrait Section operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(PortraitSection, session)

    async def create_section(
        self,
        child_id: uuid.UUID,
        section_type: str,
        section_key: str,
        title: str,
        content: str,
        based_on_observations_through: datetime,
        *,
        crystal_id: Optional[uuid.UUID] = None,
        title_he: Optional[str] = None,
        content_he: Optional[str] = None,
        clinical_notes: Optional[str] = None,
        icd_codes: Optional[str] = None,
        audience: str = "parent",
        order: int = 0
    ) -> PortraitSection:
        """Create a new portrait section."""
        return await self.create(
            child_id=child_id,
            crystal_id=crystal_id,
            section_type=section_type,
            section_key=section_key,
            order=order,
            title=title,
            title_he=title_he,
            content=content,
            content_he=content_he,
            clinical_notes=clinical_notes,
            icd_codes=icd_codes,
            audience=audience,
            generated_at=datetime.now(timezone.utc),
            based_on_observations_through=based_on_observations_through
        )

    async def get_child_portrait(
        self,
        child_id: uuid.UUID,
        *,
        audience: str = "parent"
    ) -> Sequence[PortraitSection]:
        """Get all portrait sections for a child."""
        stmt = select(PortraitSection).where(
            and_(
                PortraitSection.child_id == child_id,
                PortraitSection.audience == audience
            )
        ).order_by(PortraitSection.order)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_section_by_key(
        self,
        child_id: uuid.UUID,
        section_key: str,
        *,
        audience: str = "parent"
    ) -> Optional[PortraitSection]:
        """Get specific portrait section."""
        stmt = select(PortraitSection).where(
            and_(
                PortraitSection.child_id == child_id,
                PortraitSection.section_key == section_key,
                PortraitSection.audience == audience
            )
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_section(
        self,
        child_id: uuid.UUID,
        section_key: str,
        content: str,
        based_on_observations_through: datetime,
        *,
        content_he: Optional[str] = None,
        audience: str = "parent"
    ) -> Optional[PortraitSection]:
        """Update or create a portrait section."""
        existing = await self.get_section_by_key(child_id, section_key, audience=audience)

        if existing:
            existing.content = content
            if content_he:
                existing.content_he = content_he
            existing.generated_at = datetime.now(timezone.utc)
            existing.based_on_observations_through = based_on_observations_through
            await self.session.flush()
            return existing
        else:
            return await self.create_section(
                child_id=child_id,
                section_type="domain_summary",
                section_key=section_key,
                title=section_key.replace("_", " ").title(),
                content=content,
                content_he=content_he,
                audience=audience,
                based_on_observations_through=based_on_observations_through
            )


class InterventionPathwayRepository(BaseRepository[InterventionPathway]):
    """Repository for Intervention Pathway operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(InterventionPathway, session)

    async def create_pathway(
        self,
        child_id: uuid.UUID,
        domain: str,
        recommendation: str,
        *,
        crystal_id: Optional[uuid.UUID] = None,
        rationale: Optional[str] = None,
        priority: str = "medium",
        specialist_type: Optional[str] = None
    ) -> InterventionPathway:
        """Create a new intervention pathway."""
        return await self.create(
            child_id=child_id,
            crystal_id=crystal_id,
            domain=domain,
            recommendation=recommendation,
            rationale=rationale,
            priority=priority,
            specialist_type=specialist_type,
            status="suggested",
            suggested_at=datetime.now(timezone.utc)
        )

    async def get_child_pathways(
        self,
        child_id: uuid.UUID,
        *,
        status: Optional[str] = None,
        priority: Optional[str] = None
    ) -> Sequence[InterventionPathway]:
        """Get intervention pathways for a child."""
        stmt = select(InterventionPathway).where(
            InterventionPathway.child_id == child_id
        )

        if status:
            stmt = stmt.where(InterventionPathway.status == status)
        if priority:
            stmt = stmt.where(InterventionPathway.priority == priority)

        # Order by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        stmt = stmt.order_by(InterventionPathway.suggested_at.desc())

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def accept_pathway(
        self,
        pathway_id: uuid.UUID,
        parent_response: Optional[str] = None
    ) -> Optional[InterventionPathway]:
        """Mark pathway as accepted."""
        return await self.update(
            pathway_id,
            status="accepted",
            accepted_at=datetime.now(timezone.utc),
            parent_response=parent_response
        )

    async def complete_pathway(
        self,
        pathway_id: uuid.UUID
    ) -> Optional[InterventionPathway]:
        """Mark pathway as completed."""
        return await self.update(pathway_id, status="completed")
