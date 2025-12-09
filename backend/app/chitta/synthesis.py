"""
Synthesis Service - On-Demand Deep Analysis

NOT background async processing. These are synchronous, on-demand operations:
- Synthesis: Called when user requests report or conditions are ripe
- Memory distillation: Called when session transitions (>4 hour gap)

DESIGN:
- Pattern detection uses STRONGEST model
- Memory distillation uses REGULAR model
- No background tasks, no queues
"""

import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

from .models import (
    Understanding,
    Pattern,
    SynthesisReport,
    ConversationMemory,
    Story,
    ExplorationCycle,
    Crystal,
    InterventionPathway,
    TemporalFact,
)
from .curiosity import CuriosityEngine

# Import LLM abstraction layer
from app.services.llm.factory import create_llm_provider
from app.services.llm.base import Message as LLMMessage


logger = logging.getLogger(__name__)


class SynthesisService:
    """
    Synthesis and memory management.

    NOT background processing. These are synchronous, on-demand operations:
    - Synthesis: Called when user requests report or conditions are ripe
    - Memory distillation: Called when session transitions (>4 hour gap)
    """

    def __init__(self):
        """Initialize with lazy-loaded LLM providers."""
        self._strongest_llm = None
        self._regular_llm = None

    def _get_strongest_llm(self):
        """Get strongest model for pattern detection and synthesis."""
        if self._strongest_llm is None:
            model = os.getenv("STRONG_LLM_MODEL", "gemini-2.5-pro")
            provider = os.getenv("LLM_PROVIDER", "gemini")
            self._strongest_llm = create_llm_provider(
                provider_type=provider,
                model=model,
                use_enhanced=True,
            )
        return self._strongest_llm

    def _get_regular_llm(self):
        """Get regular model for summarization tasks."""
        if self._regular_llm is None:
            model = os.getenv("LLM_MODEL", "gemini-2.5-flash")
            provider = os.getenv("LLM_PROVIDER", "gemini")
            self._regular_llm = create_llm_provider(
                provider_type=provider,
                model=model,
                use_enhanced=True,
            )
        return self._regular_llm

    async def synthesize(
        self,
        child_name: Optional[str],
        understanding: Understanding,
        exploration_cycles: List[ExplorationCycle],
        stories: List[Story],
        curiosity_engine: CuriosityEngine,
    ) -> SynthesisReport:
        """
        Create synthesis report with pattern detection.

        Uses STRONGEST model - this is the deep analysis.

        Called:
        - When user requests a report
        - When exploration cycles complete
        - When conditions suggest crystallization is ready
        """
        prompt = self._build_synthesis_prompt(
            child_name,
            understanding,
            exploration_cycles,
            stories,
            curiosity_engine,
        )

        try:
            llm = self._get_strongest_llm()
            response = await llm.chat(
                messages=[
                    LLMMessage(role="system", content=prompt),
                    LLMMessage(role="user", content="Please synthesize the understanding of this child."),
                ],
                functions=None,  # Text response
                temperature=0.3,  # Lower for analytical tasks
                max_tokens=4000,
            )

            return self._parse_synthesis_response(response.content, understanding, curiosity_engine)

        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            return self._create_fallback_synthesis(understanding, curiosity_engine)

    async def distill_memory_on_transition(
        self,
        session_history: List[Dict[str, str]],
        child_name: Optional[str],
        understanding: Understanding,
    ) -> ConversationMemory:
        """
        Distill session into memory when session transitions.

        Uses REGULAR model - summarization task.

        Called when:
        - New session starts and previous session exists
        - Gap > 4 hours between last message and new message

        NOT called as background task.
        """
        prompt = self._build_memory_distillation_prompt(
            session_history,
            child_name,
            understanding,
        )

        try:
            llm = self._get_regular_llm()
            response = await llm.chat(
                messages=[
                    LLMMessage(role="system", content=prompt),
                    LLMMessage(role="user", content="Please distill this conversation into memory."),
                ],
                functions=None,
                temperature=0.3,
                max_tokens=1000,
            )

            return ConversationMemory.create(
                summary=response.content or "Previous conversation session.",
                turn_count=len(session_history),
            )

        except Exception as e:
            logger.error(f"Memory distillation error: {e}")
            return ConversationMemory.create(
                summary=f"Previous session with {len(session_history)} turns.",
                turn_count=len(session_history),
            )

    def should_synthesize(
        self,
        exploration_cycles: List[ExplorationCycle],
        stories: List[Story],
        understanding: Understanding,
        last_synthesis: Optional[datetime] = None,
    ) -> bool:
        """Check if conditions suggest synthesis is ready."""
        completed_cycles = [c for c in exploration_cycles if c.status == "complete"]

        # Conditions for synthesis readiness:
        # - Multiple cycles have completed
        # - Multiple stories captured
        # - Significant time has passed since last synthesis
        # - Sufficient facts accumulated
        conditions_met = 0

        if len(completed_cycles) >= 2:
            conditions_met += 1

        if len(stories) >= 5:
            conditions_met += 1

        if len(understanding.facts) >= 10:
            conditions_met += 1

        if last_synthesis:
            days_since = (datetime.now() - last_synthesis).days
            if days_since >= 7:
                conditions_met += 1

        return conditions_met >= 2

    # ========================================
    # PROMPT BUILDING
    # ========================================

    def _build_synthesis_prompt(
        self,
        child_name: Optional[str],
        understanding: Understanding,
        exploration_cycles: List[ExplorationCycle],
        stories: List[Story],
        curiosity_engine: CuriosityEngine,
    ) -> str:
        """Build prompt for synthesis."""
        name = child_name or "this child"

        # Format facts
        facts_text = "\n".join([
            f"- [{f.domain or 'general'}] {f.content}"
            for f in understanding.facts[:20]
        ]) or "No facts recorded yet."

        # Format exploration cycles
        cycles_text = "\n".join([
            f"- [{c.curiosity_type}] {c.focus}: {c.status}"
            + (f" (confidence: {c.confidence})" if c.confidence else "")
            for c in exploration_cycles[:10]
        ]) or "No explorations yet."

        # Format stories
        stories_text = "\n".join([
            f"- {s.summary}\n  Reveals: {', '.join(s.reveals[:3])}"
            for s in stories[:10]
        ]) or "No stories captured yet."

        # Format open questions
        gaps = curiosity_engine.get_gaps()
        gaps_text = "\n".join([f"- {g}" for g in gaps]) or "No open questions."

        return f"""
# SYNTHESIS REQUEST

You are creating a synthesis of understanding about {name}.

## CURRENT FACTS

{facts_text}

## EXPLORATION CYCLES

{cycles_text}

## CAPTURED STORIES

{stories_text}

## OPEN QUESTIONS

{gaps_text}

## YOUR TASK

1. **Detect Patterns**: What themes appear across domains? What connections emerge?

2. **Assess Confidence**: For each area of understanding, how confident are we?

3. **Identify Gaps**: What significant questions remain?

4. **Crystallize Essence**: If enough understanding has emerged, describe who this child IS.
   - What makes them unique?
   - What are their core qualities?
   - What strengths do they show?

## OUTPUT FORMAT

Provide your synthesis in a clear structure:

ESSENCE:
[If ready, a 2-3 sentence narrative about who this child is]

PATTERNS:
- [Pattern 1]: [domains involved]
- [Pattern 2]: [domains involved]

CONFIDENCE BY DOMAIN:
- [domain]: [high/medium/low]

REMAINING QUESTIONS:
- [Question 1]
- [Question 2]
"""

    def _build_memory_distillation_prompt(
        self,
        session_history: List[Dict[str, str]],
        child_name: Optional[str],
        understanding: Understanding,
    ) -> str:
        """Build prompt for memory distillation."""
        name = child_name or "this child"

        # Format conversation
        conversation_text = "\n".join([
            f"{msg.get('role', 'unknown')}: {msg.get('content', '')[:200]}"
            for msg in session_history[-20:]  # Last 20 messages
        ]) or "No conversation recorded."

        # Current essence
        essence_text = "Getting to know this child."
        if understanding.essence and understanding.essence.narrative:
            essence_text = understanding.essence.narrative

        return f"""
# MEMORY DISTILLATION

Synthesize this conversation into memory for the next session.

## CHILD CONTEXT

{name}: {essence_text}

## CONVERSATION TO DISTILL

{conversation_text}

## YOUR TASK

Create a concise memory that:
1. Preserves key points discussed
2. Notes significant moments or stories shared
3. Captures emotional tone of the conversation
4. Identifies threads to follow up

This memory will be available in the next session to maintain continuity.

Keep it to 2-3 sentences focusing on what matters most.
"""

    # ========================================
    # RESPONSE PARSING
    # ========================================

    def _parse_synthesis_response(
        self,
        response_text: str,
        understanding: Understanding,
        curiosity_engine: CuriosityEngine,
    ) -> SynthesisReport:
        """Parse synthesis response from LLM."""
        # Extract sections from response
        essence_narrative = None
        patterns = []
        confidence_by_domain: Dict[str, float] = {}
        open_questions = []

        if not response_text:
            return self._create_fallback_synthesis(understanding, curiosity_engine)

        lines = response_text.split("\n")
        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detect sections
            if line.upper().startswith("ESSENCE:"):
                current_section = "essence"
                continue
            elif line.upper().startswith("PATTERNS:"):
                current_section = "patterns"
                continue
            elif line.upper().startswith("CONFIDENCE"):
                current_section = "confidence"
                continue
            elif line.upper().startswith("REMAINING"):
                current_section = "questions"
                continue

            # Parse content based on section
            if current_section == "essence" and not essence_narrative:
                essence_narrative = line
            elif current_section == "patterns" and line.startswith("-"):
                # Extract pattern
                pattern_text = line[1:].strip()
                if ":" in pattern_text:
                    desc, domains_part = pattern_text.split(":", 1)
                    domains = [d.strip() for d in domains_part.split(",")]
                    patterns.append(Pattern(
                        description=desc.strip(),
                        domains_involved=domains,
                        confidence=0.6,
                    ))
            elif current_section == "confidence" and line.startswith("-"):
                # Extract confidence
                conf_text = line[1:].strip()
                if ":" in conf_text:
                    domain, level = conf_text.split(":", 1)
                    level = level.strip().lower()
                    confidence_by_domain[domain.strip()] = {
                        "high": 0.8,
                        "medium": 0.5,
                        "low": 0.2,
                    }.get(level, 0.5)
            elif current_section == "questions" and line.startswith("-"):
                open_questions.append(line[1:].strip())

        # Fall back to curiosity engine gaps if no questions parsed
        if not open_questions:
            open_questions = curiosity_engine.get_gaps()

        return SynthesisReport(
            essence_narrative=essence_narrative,
            patterns=patterns,
            confidence_by_domain=confidence_by_domain,
            open_questions=open_questions,
        )

    def _create_fallback_synthesis(
        self,
        understanding: Understanding,
        curiosity_engine: CuriosityEngine,
    ) -> SynthesisReport:
        """Create fallback synthesis without LLM."""
        # Extract existing patterns
        patterns = list(understanding.patterns)

        # Calculate confidence by domain from facts
        confidence_by_domain: Dict[str, float] = {}
        for fact in understanding.facts:
            domain = fact.domain or "general"
            if domain not in confidence_by_domain:
                confidence_by_domain[domain] = 0.0
            confidence_by_domain[domain] = min(1.0, confidence_by_domain[domain] + 0.1)

        # Get open questions from curiosity engine
        open_questions = curiosity_engine.get_gaps()

        # Use existing essence if available
        essence_narrative = None
        if understanding.essence and understanding.essence.narrative:
            essence_narrative = understanding.essence.narrative

        return SynthesisReport(
            essence_narrative=essence_narrative,
            patterns=patterns,
            confidence_by_domain=confidence_by_domain,
            open_questions=open_questions,
        )

    # ========================================
    # CRYSTALLIZATION - Cached Synthesis
    # ========================================

    async def crystallize(
        self,
        child_name: Optional[str],
        understanding: Understanding,
        exploration_cycles: List[ExplorationCycle],
        stories: List[Story],
        curiosity_engine: CuriosityEngine,
        latest_observation_at: datetime,
        existing_crystal: Optional[Crystal] = None,
    ) -> Crystal:
        """
        Create or update a Crystal (cached synthesis).

        If existing_crystal is provided and stale, performs INCREMENTAL update:
        - Sends previous crystal + new observations
        - LLM updates rather than regenerates from scratch

        Uses STRONGEST model.

        Args:
            child_name: Name of the child
            understanding: Current understanding (facts, patterns)
            exploration_cycles: Active and completed exploration cycles
            stories: Captured stories
            curiosity_engine: The curiosity engine for open questions
            latest_observation_at: Timestamp of most recent observation
            existing_crystal: Previous crystal if available (for incremental update)

        Returns:
            Crystal: New or updated crystal
        """
        # Determine if this is incremental or fresh
        is_incremental = (
            existing_crystal is not None and
            existing_crystal.is_stale(latest_observation_at)
        )

        if is_incremental:
            return await self._incremental_crystallize(
                child_name=child_name,
                understanding=understanding,
                exploration_cycles=exploration_cycles,
                stories=stories,
                curiosity_engine=curiosity_engine,
                latest_observation_at=latest_observation_at,
                existing_crystal=existing_crystal,
            )
        else:
            return await self._fresh_crystallize(
                child_name=child_name,
                understanding=understanding,
                exploration_cycles=exploration_cycles,
                stories=stories,
                curiosity_engine=curiosity_engine,
                latest_observation_at=latest_observation_at,
            )

    async def _fresh_crystallize(
        self,
        child_name: Optional[str],
        understanding: Understanding,
        exploration_cycles: List[ExplorationCycle],
        stories: List[Story],
        curiosity_engine: CuriosityEngine,
        latest_observation_at: datetime,
    ) -> Crystal:
        """Create a fresh crystal from all observations."""
        prompt = self._build_crystallization_prompt(
            child_name=child_name,
            understanding=understanding,
            exploration_cycles=exploration_cycles,
            stories=stories,
            curiosity_engine=curiosity_engine,
            is_incremental=False,
            previous_crystal=None,
            new_observations=None,
        )

        try:
            llm = self._get_strongest_llm()
            response = await llm.chat(
                messages=[
                    LLMMessage(role="system", content=prompt),
                    LLMMessage(role="user", content="Please create a crystal synthesis of understanding for this child."),
                ],
                functions=None,
                temperature=0.3,
                max_tokens=6000,
            )

            crystal = self._parse_crystal_response(
                response_text=response.content,
                latest_observation_at=latest_observation_at,
                version=1,
            )
            return crystal

        except Exception as e:
            logger.error(f"Fresh crystallization error: {e}")
            return self._create_fallback_crystal(
                understanding=understanding,
                curiosity_engine=curiosity_engine,
                latest_observation_at=latest_observation_at,
            )

    async def _incremental_crystallize(
        self,
        child_name: Optional[str],
        understanding: Understanding,
        exploration_cycles: List[ExplorationCycle],
        stories: List[Story],
        curiosity_engine: CuriosityEngine,
        latest_observation_at: datetime,
        existing_crystal: Crystal,
    ) -> Crystal:
        """
        Update an existing crystal with new observations.

        This is more efficient than fresh crystallization because:
        1. We send the previous crystal as context
        2. We only include observations since the last crystallization
        3. The LLM updates rather than regenerates
        """
        # Get only new observations since last crystal
        new_facts = [
            f for f in understanding.facts
            if hasattr(f, 't_created') and f.t_created and f.t_created > existing_crystal.based_on_observations_through
        ]
        new_stories = [
            s for s in stories
            if hasattr(s, 'timestamp') and s.timestamp and s.timestamp > existing_crystal.based_on_observations_through
        ]

        new_observations = {
            "facts": new_facts,
            "stories": new_stories,
            "fact_count": len(new_facts),
            "story_count": len(new_stories),
        }

        prompt = self._build_crystallization_prompt(
            child_name=child_name,
            understanding=understanding,
            exploration_cycles=exploration_cycles,
            stories=stories,
            curiosity_engine=curiosity_engine,
            is_incremental=True,
            previous_crystal=existing_crystal,
            new_observations=new_observations,
        )

        try:
            llm = self._get_strongest_llm()
            response = await llm.chat(
                messages=[
                    LLMMessage(role="system", content=prompt),
                    LLMMessage(role="user", content="Please update the crystal with the new observations."),
                ],
                functions=None,
                temperature=0.3,
                max_tokens=6000,
            )

            crystal = self._parse_crystal_response(
                response_text=response.content,
                latest_observation_at=latest_observation_at,
                version=existing_crystal.version + 1,
                previous_version_summary=f"Updated with {len(new_facts)} new facts, {len(new_stories)} new stories",
            )
            return crystal

        except Exception as e:
            logger.error(f"Incremental crystallization error: {e}")
            # On error, keep the existing crystal
            return existing_crystal

    def _build_crystallization_prompt(
        self,
        child_name: Optional[str],
        understanding: Understanding,
        exploration_cycles: List[ExplorationCycle],
        stories: List[Story],
        curiosity_engine: CuriosityEngine,
        is_incremental: bool,
        previous_crystal: Optional[Crystal],
        new_observations: Optional[Dict[str, Any]],
    ) -> str:
        """Build prompt for crystallization (in English for token efficiency)."""
        name = child_name or "this child"

        # Format all facts
        facts_text = "\n".join([
            f"- [{f.domain or 'general'}] {f.content}"
            for f in understanding.facts[:30]
        ]) or "No facts recorded yet."

        # Format stories
        stories_text = "\n".join([
            f"- {s.summary}\n  Reveals: {', '.join(s.reveals[:3])}"
            for s in stories[:15]
        ]) or "No stories captured yet."

        # Format active explorations
        active_cycles = [c for c in exploration_cycles if c.status == "active"]
        cycles_text = "\n".join([
            f"- [{c.curiosity_type}] {c.focus}"
            + (f" (theory: {c.theory})" if c.theory else "")
            + (f" (confidence: {c.confidence})" if c.confidence else "")
            for c in active_cycles[:10]
        ]) or "No active explorations."

        # Format strengths and interests
        strengths = [f.content for f in understanding.facts if f.domain == "strengths"]
        interests = [f.content for f in understanding.facts if f.domain == "interests"]
        strengths_text = ", ".join(strengths[:5]) if strengths else "Not yet known"
        interests_text = ", ".join(interests[:5]) if interests else "Not yet known"

        # Format concerns from exploration cycles
        concerns = [c.focus for c in active_cycles if c.curiosity_type in ("hypothesis", "question")]
        concerns_text = ", ".join(concerns[:5]) if concerns else "None defined"

        # Open questions
        gaps = curiosity_engine.get_gaps()
        gaps_text = "\n".join([f"- {g}" for g in gaps]) or "No open questions."

        if is_incremental and previous_crystal:
            # Incremental update prompt
            new_facts_text = "\n".join([
                f"- [{f.domain or 'general'}] {f.content}"
                for f in new_observations.get("facts", [])
            ]) or "No new facts."

            new_stories_text = "\n".join([
                f"- {s.summary}"
                for s in new_observations.get("stories", [])
            ]) or "No new stories."

            previous_patterns = "\n".join([
                f"- {p.description} (domains: {', '.join(p.domains_involved)})"
                for p in previous_crystal.patterns
            ]) or "No patterns identified previously."

            previous_pathways = "\n".join([
                f"- {ip.hook} -> {ip.concern}: {ip.suggestion}"
                for ip in previous_crystal.intervention_pathways
            ]) or "No intervention pathways identified previously."

            return f"""
# Crystal Update - Child: {name}

You are updating an existing understanding with new information.

## Previous Crystal (version {previous_crystal.version})

### Who is this child
{previous_crystal.essence_narrative or "Still forming"}

### Temperament
{', '.join(previous_crystal.temperament) if previous_crystal.temperament else "Not defined"}

### Core Qualities
{', '.join(previous_crystal.core_qualities) if previous_crystal.core_qualities else "Not defined"}

### Identified Patterns
{previous_patterns}

### Intervention Pathways
{previous_pathways}

### Open Questions
{chr(10).join(['- ' + q for q in previous_crystal.open_questions]) if previous_crystal.open_questions else "None"}

---

## New Information Since Last Crystallization

### New Facts
{new_facts_text}

### New Stories
{new_stories_text}

---

## Your Task

Update the crystal based on the new information:
1. Does the new information strengthen/contradict/refine existing understanding?
2. Are there new patterns visible now?
3. Are there new intervention pathways?
4. Should the essence narrative be updated?

## Response Format

ESSENCE:
[Updated essence narrative - 2-3 sentences about who this child is. Write in Hebrew.]

TEMPERAMENT:
[Comma-separated list of temperament traits. Write in Hebrew.]

CORE_QUALITIES:
[Comma-separated list of core qualities. Write in Hebrew.]

PATTERNS:
- [Pattern description]: [domains involved, comma-separated]
- [Another pattern]: [domains]

INTERVENTION_PATHWAYS:
- [Strength/Interest] -> [Concern it can help]: [Concrete suggestion]

OPEN_QUESTIONS:
- [Question 1]
- [Question 2]

WHAT_CHANGED:
[Brief note on what changed in this update]
"""

        else:
            # Fresh crystallization prompt
            return f"""
# Crystallization - Child: {name}

You are creating a deep synthesis of the accumulated understanding about this child.
This is the first crystallization - build the foundation.

## Guiding Principle

This child is NOT "their problem". This child is a whole person:
- With strengths and interests
- With their own ways of connecting to the world
- With patterns that cross domains
- Strengths are the door - how to reach them

## Everything We Know

### Facts
{facts_text}

### Stories
{stories_text}

### Active Explorations
{cycles_text}

### Strengths
{strengths_text}

### Interests
{interests_text}

### Main Concerns
{concerns_text}

### Open Questions
{gaps_text}

---

## Your Task

Create a crystallization of understanding:

1. **Who is this child** - Essence narrative (2-3 sentences about who they are as a person)

2. **Patterns** - What crosses domains? What repeats in different places?

3. **Intervention Pathways** - How can strengths and interests help with concerns?

4. **Open Questions** - What is still unclear?

## Response Format

ESSENCE:
[Essence narrative - 2-3 sentences about who this child is as a whole person, not as "a problem". Write in Hebrew.]

TEMPERAMENT:
[Comma-separated list of temperament traits. Write in Hebrew, e.g.: רגיש, אנרגטי, זהיר]

CORE_QUALITIES:
[Comma-separated list of core qualities. Write in Hebrew, e.g.: סקרנות, התמדה, יצירתיות]

PATTERNS:
- [Pattern description]: [domains involved, comma-separated]
- [Another pattern]: [domains]

INTERVENTION_PATHWAYS:
- [Strength or interest] -> [Concern it can help with]: [Concrete suggestion]

OPEN_QUESTIONS:
- [Question that is still unclear to us]
- [Another question]
"""

    def _parse_crystal_response(
        self,
        response_text: str,
        latest_observation_at: datetime,
        version: int,
        previous_version_summary: Optional[str] = None,
    ) -> Crystal:
        """Parse LLM response into Crystal object."""
        if not response_text:
            return Crystal.create_empty()

        essence_narrative = None
        temperament = []
        core_qualities = []
        patterns = []
        intervention_pathways = []
        open_questions = []

        lines = response_text.split("\n")
        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detect sections
            if line.upper().startswith("ESSENCE:"):
                current_section = "essence"
                continue
            elif line.upper().startswith("TEMPERAMENT:"):
                current_section = "temperament"
                continue
            elif line.upper().startswith("CORE_QUALITIES:") or line.upper().startswith("CORE QUALITIES:"):
                current_section = "core_qualities"
                continue
            elif line.upper().startswith("PATTERNS:"):
                current_section = "patterns"
                continue
            elif line.upper().startswith("INTERVENTION_PATHWAYS:") or line.upper().startswith("INTERVENTION PATHWAYS:"):
                current_section = "pathways"
                continue
            elif line.upper().startswith("OPEN_QUESTIONS:") or line.upper().startswith("OPEN QUESTIONS:"):
                current_section = "questions"
                continue
            elif line.upper().startswith("WHAT_CHANGED:") or line.upper().startswith("WHAT CHANGED:"):
                current_section = "changed"
                continue

            # Parse content
            if current_section == "essence" and not essence_narrative:
                if line.startswith("[") and line.endswith("]"):
                    continue  # Skip placeholder
                essence_narrative = line

            elif current_section == "temperament":
                if line.startswith("[") and line.endswith("]"):
                    continue
                # Parse comma-separated list
                items = [t.strip() for t in line.split(",") if t.strip()]
                temperament.extend(items)

            elif current_section == "core_qualities":
                if line.startswith("[") and line.endswith("]"):
                    continue
                items = [t.strip() for t in line.split(",") if t.strip()]
                core_qualities.extend(items)

            elif current_section == "patterns" and line.startswith("-"):
                pattern_text = line[1:].strip()
                if ":" in pattern_text:
                    desc, domains_part = pattern_text.split(":", 1)
                    domains = [d.strip() for d in domains_part.split(",") if d.strip()]
                    patterns.append(Pattern(
                        description=desc.strip(),
                        domains_involved=domains,
                        confidence=0.6,
                    ))

            elif current_section == "pathways" and line.startswith("-"):
                pathway_text = line[1:].strip()
                # Parse: [hook] -> [concern]: [suggestion]
                if "->" in pathway_text:
                    parts = pathway_text.split("->")
                    if len(parts) == 2:
                        hook = parts[0].strip()
                        rest = parts[1].strip()
                        if ":" in rest:
                            concern, suggestion = rest.split(":", 1)
                            intervention_pathways.append(InterventionPathway(
                                hook=hook,
                                concern=concern.strip(),
                                suggestion=suggestion.strip(),
                                confidence=0.5,
                            ))

            elif current_section == "questions" and line.startswith("-"):
                question = line[1:].strip()
                if question and not (question.startswith("[") and question.endswith("]")):
                    open_questions.append(question)

            elif current_section == "changed" and previous_version_summary is None:
                if not (line.startswith("[") and line.endswith("]")):
                    previous_version_summary = line

        return Crystal(
            essence_narrative=essence_narrative,
            temperament=temperament,
            core_qualities=core_qualities,
            patterns=patterns,
            intervention_pathways=intervention_pathways,
            open_questions=open_questions,
            created_at=datetime.now(),
            based_on_observations_through=latest_observation_at,
            version=version,
            previous_version_summary=previous_version_summary,
        )

    def _create_fallback_crystal(
        self,
        understanding: Understanding,
        curiosity_engine: CuriosityEngine,
        latest_observation_at: datetime,
    ) -> Crystal:
        """Create a fallback crystal without LLM when errors occur."""
        # Extract what we can from raw data
        patterns = list(understanding.patterns) if understanding.patterns else []

        # Get open questions
        open_questions = curiosity_engine.get_gaps()

        # Get existing essence if any
        essence_narrative = None
        temperament = []
        core_qualities = []
        if understanding.essence:
            essence_narrative = understanding.essence.narrative
            temperament = understanding.essence.temperament or []
            core_qualities = understanding.essence.core_qualities or []

        return Crystal(
            essence_narrative=essence_narrative,
            temperament=temperament,
            core_qualities=core_qualities,
            patterns=patterns,
            intervention_pathways=[],  # Can't derive without LLM
            open_questions=open_questions,
            created_at=datetime.now(),
            based_on_observations_through=latest_observation_at,
            version=1,
            previous_version_summary="Created as fallback (LLM error)",
        )


# Singleton instance
_synthesis_service: Optional[SynthesisService] = None


def get_synthesis_service() -> SynthesisService:
    """Get or create the synthesis service singleton."""
    global _synthesis_service
    if _synthesis_service is None:
        _synthesis_service = SynthesisService()
    return _synthesis_service
