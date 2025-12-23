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

import json
import logging
import os
import re
from datetime import datetime
from typing import Dict, Any, List, Optional

from .models import (
    Understanding,
    Pattern,
    SynthesisReport,
    ConversationMemory,
    Story,
    Crystal,
    InterventionPathway,
    ExpertRecommendation,
    ProfessionalSummary,
    TemporalFact,
    PortraitSection,
    DevelopmentalMilestone,
)
from .portrait_schema import PortraitOutput
from .curiosity import Curiosities

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
        stories: List[Story],
        curiosities: Curiosities,
    ) -> SynthesisReport:
        """
        Create synthesis report with pattern detection.

        Uses STRONGEST model - this is the deep analysis.

        Called:
        - When user requests a report
        - When investigations complete
        - When conditions suggest crystallization is ready
        """
        prompt = self._build_synthesis_prompt(
            child_name,
            understanding,
            stories,
            curiosities,
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

            return self._parse_synthesis_response(response.content, understanding, curiosities)

        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            return self._create_fallback_synthesis(understanding, curiosities)

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
        curiosities: Curiosities,
        stories: List[Story],
        understanding: Understanding,
        last_synthesis: Optional[datetime] = None,
    ) -> bool:
        """Check if conditions suggest synthesis is ready."""
        # Get investigations that are complete (understood status)
        understood_curiosities = [c for c in curiosities._dynamic if c.status == "understood"]

        # Conditions for synthesis readiness:
        # - Multiple investigations have completed
        # - Multiple stories captured
        # - Significant time has passed since last synthesis
        # - Sufficient facts accumulated
        conditions_met = 0

        if len(understood_curiosities) >= 2:
            conditions_met += 1

        if len(stories) >= 5:
            conditions_met += 1

        if len(understanding.observations) >= 10:
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
        stories: List[Story],
        curiosities: Curiosities,
    ) -> str:
        """Build prompt for synthesis."""
        name = child_name or "this child"

        # Format facts
        facts_text = "\n".join([
            f"- [{f.domain or 'general'}] {f.content}"
            for f in understanding.observations[:20]
        ]) or "No facts recorded yet."

        # Format active investigations
        investigating = curiosities.get_investigating()
        cycles_text = "\n".join([
            f"- [{c.type}] {c.focus}: {c.status}"
            + (f" (certainty: {c.certainty})" if c.certainty else "")
            for c in investigating[:10]
        ]) or "No active investigations yet."

        # Format stories
        stories_text = "\n".join([
            f"- {s.summary}\n  Reveals: {', '.join(s.reveals[:3])}"
            for s in stories[:10]
        ]) or "No stories captured yet."

        # Format open questions
        gaps = curiosities.get_gaps()
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
        curiosities: Curiosities,
    ) -> SynthesisReport:
        """Parse synthesis response from LLM."""
        # Extract sections from response
        essence_narrative = None
        patterns = []
        confidence_by_domain: Dict[str, float] = {}
        open_questions = []

        if not response_text:
            return self._create_fallback_synthesis(understanding, curiosities)

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
            open_questions = curiosities.get_gaps()

        return SynthesisReport(
            essence_narrative=essence_narrative,
            patterns=patterns,
            confidence_by_domain=confidence_by_domain,
            open_questions=open_questions,
        )

    def _create_fallback_synthesis(
        self,
        understanding: Understanding,
        curiosities: Curiosities,
    ) -> SynthesisReport:
        """Create fallback synthesis without LLM."""
        # Extract existing patterns
        patterns = list(understanding.patterns)

        # Calculate confidence by domain from facts
        confidence_by_domain: Dict[str, float] = {}
        for fact in understanding.observations:
            domain = fact.domain or "general"
            if domain not in confidence_by_domain:
                confidence_by_domain[domain] = 0.0
            confidence_by_domain[domain] = min(1.0, confidence_by_domain[domain] + 0.1)

        # Get open questions from curiosity engine
        open_questions = curiosities.get_gaps()

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
        stories: List[Story],
        curiosities: Curiosities,
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
            stories: Captured stories
            curiosities: The curiosity engine for open questions
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
                stories=stories,
                curiosities=curiosities,
                latest_observation_at=latest_observation_at,
                existing_crystal=existing_crystal,
            )
        else:
            return await self._fresh_crystallize(
                child_name=child_name,
                understanding=understanding,
                stories=stories,
                curiosities=curiosities,
                latest_observation_at=latest_observation_at,
            )

    async def _fresh_crystallize(
        self,
        child_name: Optional[str],
        understanding: Understanding,
        stories: List[Story],
        curiosities: Curiosities,
        latest_observation_at: datetime,
    ) -> Crystal:
        """Create a fresh crystal from all observations using structured output."""
        prompt = self._build_crystallization_prompt(
            child_name=child_name,
            understanding=understanding,
            stories=stories,
            curiosities=curiosities,
            is_incremental=False,
            previous_crystal=None,
            new_observations=None,
        )

        try:
            llm = self._get_strongest_llm()

            # Use structured output with Pydantic schema
            response_data = await llm.chat_with_structured_output(
                messages=[
                    LLMMessage(role="system", content=prompt),
                    LLMMessage(role="user", content="Create a portrait of this child."),
                ],
                response_schema=PortraitOutput.model_json_schema(),
                temperature=0.7,  # Balanced creativity with structured output
            )

            # Validate and convert to Crystal
            portrait = PortraitOutput.model_validate(response_data)
            crystal = self._portrait_to_crystal(
                portrait=portrait,
                latest_observation_at=latest_observation_at,
                version=1,
            )
            return crystal

        except Exception as e:
            logger.error(f"Fresh crystallization error: {e}")
            return self._create_fallback_crystal(
                understanding=understanding,
                curiosities=curiosities,
                latest_observation_at=latest_observation_at,
            )

    async def _incremental_crystallize(
        self,
        child_name: Optional[str],
        understanding: Understanding,
        stories: List[Story],
        curiosities: Curiosities,
        latest_observation_at: datetime,
        existing_crystal: Crystal,
    ) -> Crystal:
        """
        Update an existing crystal with new observations using structured output.

        This is more efficient than fresh crystallization because:
        1. We send the previous crystal as context
        2. We only include observations since the last crystallization
        3. The LLM updates rather than regenerates

        Uses structured output (same as fresh crystallization) for reliable parsing.
        """
        # Get only new observations since last crystal
        new_facts = [
            f for f in understanding.observations
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
            stories=stories,
            curiosities=curiosities,
            is_incremental=True,
            previous_crystal=existing_crystal,
            new_observations=new_observations,
        )

        try:
            llm = self._get_strongest_llm()

            # Use structured output with Pydantic schema (same as fresh crystallization)
            response_data = await llm.chat_with_structured_output(
                messages=[
                    LLMMessage(role="system", content=prompt),
                    LLMMessage(role="user", content="Update the portrait with the new observations."),
                ],
                response_schema=PortraitOutput.model_json_schema(),
                temperature=0.7,  # Balanced creativity with structured output
            )

            # Validate and convert to Crystal
            portrait = PortraitOutput.model_validate(response_data)
            crystal = self._portrait_to_crystal(
                portrait=portrait,
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
        stories: List[Story],
        curiosities: Curiosities,
        is_incremental: bool,
        previous_crystal: Optional[Crystal],
        new_observations: Optional[Dict[str, Any]],
    ) -> str:
        """Build prompt for crystallization - focuses on guidance, not schema."""
        name = child_name or "הילד"

        # Format all facts
        facts_text = "\n".join([
            f"- [{f.domain or 'general'}] {f.content}"
            for f in understanding.observations[:30]
        ]) or "No facts recorded yet."

        # Format stories
        stories_text = "\n".join([
            f"- {s.summary}\n  Reveals: {', '.join(s.reveals[:3])}"
            for s in stories[:15]
        ]) or "No stories captured yet."

        # Format active investigations from curiosities
        investigating = curiosities.get_investigating()
        cycles_text = "\n".join([
            f"- [{c.type}] {c.focus}"
            + (f" (theory: {c.theory})" if c.theory else "")
            + (f" (certainty: {c.certainty})" if c.certainty else "")
            for c in investigating[:10]
        ]) or "No active investigations."

        # Format strengths and interests
        strengths = [f.content for f in understanding.observations if f.domain == "strengths"]
        interests = [f.content for f in understanding.observations if f.domain == "interests"]
        strengths_text = ", ".join(strengths[:5]) if strengths else "Not yet known"
        interests_text = ", ".join(interests[:5]) if interests else "Not yet known"

        # Format concerns from investigating curiosities
        concerns = [c.focus for c in investigating if c.type in ("hypothesis", "question")]
        concerns_text = ", ".join(concerns[:5]) if concerns else "None defined"

        # Open questions
        gaps = curiosities.get_gaps()
        gaps_text = "\n".join([f"- {g}" for g in gaps]) or "No open questions."

        # Format developmental milestones (sorted by age)
        def format_milestone(m: DevelopmentalMilestone) -> str:
            age_str = ""
            if m.age_months:
                years = m.age_months // 12
                months = m.age_months % 12
                if years > 0:
                    age_str = f"בגיל {years}" + (f".{months}" if months else "") + " שנים"
                else:
                    age_str = f"בגיל {months} חודשים"
            elif m.age_description:
                age_str = m.age_description
            type_marker = {"achievement": "✓", "concern": "⚠", "regression": "↓", "intervention": "→", "birth": "◯"}.get(m.milestone_type, "·")
            return f"{type_marker} [{m.domain}] {m.description}" + (f" ({age_str})" if age_str else "")

        milestones_sorted = sorted(
            understanding.milestones,
            key=lambda m: (m.age_months or 999, m.recorded_at),
        )
        milestones_text = "\n".join([format_milestone(m) for m in milestones_sorted[:20]]) or "No milestones recorded yet."

        # Identify what we DON'T know (gap detection)
        known_domains = {f.domain for f in understanding.observations if f.domain}
        known_domains.update({m.domain for m in understanding.milestones})
        all_important_domains = {"motor", "language", "social", "emotional", "cognitive", "sensory", "regulation", "birth_history", "medical"}
        missing_domains = all_important_domains - known_domains
        missing_info_text = "\n".join([f"- {d}" for d in sorted(missing_domains)]) or "All major domains covered."

        if is_incremental and previous_crystal:
            # Incremental update prompt - uses same structured output as fresh crystallization
            new_facts_text = "\n".join([
                f"- [{f.domain or 'general'}] {f.content}"
                for f in new_observations.get("facts", [])
            ]) or "No new facts."

            new_stories_text = "\n".join([
                f"- {s.summary}"
                for s in new_observations.get("stories", [])
            ]) or "No new stories."

            previous_patterns = "\n".join([
                f"- {p.description}: {', '.join(p.domains_involved)}"
                for p in previous_crystal.patterns
            ]) or "No patterns identified previously."

            previous_pathways = "\n".join([
                f"- {ip.hook} -> {ip.concern}: {ip.suggestion}"
                for ip in previous_crystal.intervention_pathways
            ]) or "No intervention pathways identified previously."

            # Format previous portrait sections
            previous_sections = "\n".join([
                f"- {s.icon} {s.title}: {s.content[:100]}..."
                for s in (previous_crystal.portrait_sections or [])
            ]) or "No portrait sections yet."

            # Format previous expert recommendations
            previous_experts = "\n".join([
                f"- {e.profession} ({e.specialization}): {e.why_this_match[:80]}..."
                for e in (previous_crystal.expert_recommendations or [])
            ]) or "No expert recommendations yet."

            return f"""
# Portrait Update - Child: {name}

You are UPDATING an existing portrait with new information.
The parents should finish reading and feel: "כן. זה הילד שלי. אני רואה אותו עכשיו יותר ברור."

---

## REMEMBER: This is a PORTRAIT Update, not a Report

**The Two Gifts (keep these in mind):**
1. RECOGNITION - "כן! זה בדיוק הוא!" (parents feel seen)
2. CLINICAL INSIGHT - "לא ראיתי את זה ככה קודם" (connecting dots they couldn't)

Clinical knowledge is your lens, not your voice. See with precision, speak with warmth.

---

## Language Principles (CRITICAL)

### The Grandma Test
Would a parent read this sentence aloud to grandma? If it sounds clinical, rewrite it.

### Describe How They Move Through the World
Use words parents would say to a friend, not words a clinician would write in a file:

| ❌ Avoid | ✅ Prefer |
|---|---|
| רגישות שמיעתית | רעש והמולה קשים לו |
| מראה סימנים של... | כש... הוא נוטה ל... |
| קושי בוויסות חושי | הוא זקוק לשקט כדי להרגיש בטוח |

### Forbidden Terms (NEVER use):
- "מראה סימנים ברורים של...", "נובע מ...", "מאופיין ב..."
- "תפקוד" / "עיבוד" / "ויסות" (as nouns)
- Clinical compounds: עיבוד חושי, ויסות רגשי, גמישות קוגניטיבית
- Any English in parentheses

### Framing Challenges
Never frame challenges as something wrong with the child:
- ❌ "לדניאל יש קושי במעברים" → ✅ "מעברים הם רגעים רגישים עבורו"
- ❌ "הוא מתקשה להסתגל" → ✅ "הוא זקוק לזמן כדי להתכונן לדבר הבא"

### Hypotheses - Never State Mechanisms as Facts
- ❌ "הקושי במעברים נובע מרגישות חושית"
- ✅ "יכול להיות שהקושי במעברים קשור לכך שהסביבה החדשה מרגישה עמוסה עבורו"

---

## Previous Portrait (version {previous_crystal.version})

### Narrative (Who this child is)
{previous_crystal.essence_narrative or "Still forming"}

### Portrait Sections
{previous_sections}

### Temperament
{', '.join(previous_crystal.temperament) if previous_crystal.temperament else "Not defined"}

### Core Qualities
{', '.join(previous_crystal.core_qualities) if previous_crystal.core_qualities else "Not defined"}

### Identified Patterns
{previous_patterns}

### Intervention Pathways
{previous_pathways}

### Expert Recommendations
{previous_experts}

### Open Questions
{chr(10).join(['- ' + q for q in previous_crystal.open_questions]) if previous_crystal.open_questions else "None"}

---

## New Information Since Last Update

### New Facts
{new_facts_text}

### New Stories
{new_stories_text}

### Full Developmental History (All Milestones)
{milestones_text}

### What We Still DON'T Know (Gap Detection)
The following developmental domains have NOT been discussed:
{missing_info_text}

---

## Your Task

Update the portrait based on the new information. Consider:
1. Does the new information strengthen, contradict, or refine existing understanding?
2. Are there new patterns visible now?
3. Are there new intervention pathways?
4. Should the essence narrative be updated?
5. Do portrait sections need updating or adding?
6. Are there new expert recommendations warranted?

The schema enforces the output structure. Focus on:
- portrait_sections: 3-5 thematic cards with meaningful titles
- narrative: 2-3 sentences about who this child IS
- temperament: everyday descriptions (רגיש לרעשים, not רגישות חושית)
- patterns: cross-domain insights with domains tagged
- intervention_pathways: PARENT-FACING tips. Write TO parents, not ABOUT them. ❌ "ההורים מודאגים מ..." ✅ "כשרוצים לדעת מה עובר עליה"
- open_questions: genuine questions in parent language (למה...? מה קורה כש...?)
- expert_recommendations: ONLY if genuinely helpful, match by strengths

For expert_recommendations, include professional_summaries for each recipient type.

### professional_summaries - PREPARING THE GROUND (CRITICAL)

**AUTHORSHIP: The summary is written by CHITTA - not the parents.**
Chitta gathered information from conversations with parents AND video observations.
The insights and hypotheses are CHITTA's - parents shared raw observations, Chitta connected the dots.

**Your role: You are NOT the one who names. You are the one who PREPARES THE GROUND.**

The summary should make the clinician think:
"This helps me know where to look. Now let me see for myself."

**The Three Threads (KEEP CLEARLY SEPARATED):**

1. **what_parents_shared** - What PARENTS told us
   - "ההורים סיפרו לנו ש...", "האמא שיתפה ש..."
   - Their raw observations - not our interpretations

2. **what_we_noticed** - What CHITTA noticed (OUR hypotheses)
   - "שמנו לב ש...", "תהינו אם יש קשר...", "ייתכן ש..."
   - Patterns WE found from conversations and videos - not parent insights

3. **what_remains_open** - Questions WE (Chitta) are curious about
   - "שווה לבדוק אם...", "אנחנו סקרנים לגבי..."
   - What Chitta couldn't determine - invite the professional to investigate

**Recipient Types:**
- specialist: Investigation questions, areas to explore, "worth checking if..."
- teacher: Practical strategies, what works at home
- medical: Observable patterns, timeline, no interpretations

**Test: Does the summary OPEN doors or CLOSE them?**

| ❌ Closes Doors | ✅ Opens Doors |
|---|---|
| "יש לו רגישות חושית" | "ההורים סיפרו שכשיש רעש חזק הוא מכסה את האוזניים" |
| "מזהים דפוס של קושי בוויסות" | "שמנו לב שכשהוא שקוע במשחק וצריך להפסיק, קשה לו מאוד" |
| "נובע מקושי חושי" | "תהינו אם יש קשר - שווה לבדוק" |

**Language by Recipient:**
- teacher: Everyday Hebrew, practical terms ("כשיש רעש חזק הוא מכסה את האוזניים")
- specialist: Can use clinical terms they understand ("רגישות אודיטורית", "ויסות חושי")
- medical: Clinical precision expected ("היסטוריה התפתחותית", "אבני דרך מוטוריות")

The THREE THREADS principle applies to ALL recipients - separation of observations matters regardless of language register.
"""

        else:
            # Fresh crystallization prompt - Expert-guided portrait creation
            return f"""
# Portrait Creation for {name}

You are creating a PORTRAIT - a living image of who this child is - not a report.
The parents should finish reading and feel: "כן. זה הילד שלי. אני רואה אותו עכשיו יותר ברור."

---

## 1. THE PORTRAIT PHILOSOPHY

### What makes a portrait different from a report:
- A report lists findings. A portrait captures essence.
- A report is clinical. A portrait is human.
- A report could be about anyone. A portrait could only be about THIS child.

### The Two Gifts of a Good Portrait

**RECOGNITION (the foundation)**
A parent reads and feels: "כן! זה בדיוק הוא!"
This validates their experience, makes them feel seen, reduces isolation.
Recognition is therapeutic in itself.

**CLINICAL INSIGHT (the gift)**
A parent reads and thinks: "לא ראיתי את זה ככה קודם"
Parents know their child's raw data better than anyone.
What they often lack is the FRAMEWORK to connect the dots:
- "The humming during meals AND the need for routine before bed - same regulatory pattern"
- "His interest in organizing things AND his difficulty with transitions - related"
- "This isn't bad behavior - this is age-appropriate given his sensory profile"

You have deep clinical knowledge. Use it fully to see patterns, understand mechanisms, connect dots.
But remember: your knowing is in service of RECOGNITION - helping parents see what they've already felt but couldn't quite name.

**Recognition is the foundation, insight is the gift. The best portrait does BOTH.**

### Clinical Knowledge as Lens, Not Voice
You SEE with clinical precision. You SPEAK with parental warmth.
Your knowledge is the lens through which you understand - not the voice through which you communicate.

---

## 2. LANGUAGE PRINCIPLES

### The Grandma Test
Would a parent read this sentence aloud to grandma? If it sounds clinical, rewrite it.

### Describe How They Move Through the World
Use words parents would say to a friend, not words a clinician would write in a file:

| ❌ Avoid (diagnostic) | ✅ Prefer (descriptive) |
|---|---|
| רגישות שמיעתית | רעש והמולה קשים לו |
| מראה סימנים של... | כש... הוא נוטה ל... |
| קושי בוויסות חושי | הוא זקוק לשקט כדי להרגיש בטוח |

### Forbidden Terms (NEVER use):
- "מראה סימנים ברורים של..."
- "נובע מ..." (asserting causation)
- "מאופיין ב..."
- "תפקוד" / "עיבוד" / "ויסות" (as nouns)
- Clinical compound terms: עיבוד חושי, ויסות רגשי, גמישות קוגניטיבית
- Any English in parentheses

### Preferred Framings:
- "כש... הוא נוטה ל..." (pattern, not trait)
- "נראה שעוזר לו כש..." (observation, not prescription)
- "לארגן את הלב" / "להרגיש מוכן" / "לשמור על רוגע" (felt experience)

### Evidence Visibility
Parents should see WHERE you saw something:
- ❌ "הוא מתקשה בשינויים" (conclusion without evidence)
- ✅ "כשצריך לצאת מהבית בבוקר, הוא צריך הרבה זמן להתארגן" (observable)

---

## 3. UNDERSTANDING PATTERNS (The Clinical Gift)

Patterns are cross-domain connections parents can't see on their own.
NOT just "he does X" - but "when A happens, B follows, which connects to C".

### What makes a pattern valuable:
1. CROSS-DOMAIN connections (sensory → behavioral → emotional)
2. PREDICTIVE power (if we see X, Y is likely)
3. ACTIONABLE insight (knowing this helps parents respond better)

### Pattern Examples:
- GOOD: "כשיש רעש פתאומי, הוא מתכווץ ומתקשה להמשיך במה שעשה"
  (Connects sensory → physical → cognitive)
- BAD: "הוא רגיש לרעשים" (Single observation, no chain, no insight beyond the obvious)

---

## 4. EXPERT RECOMMENDATIONS (Preparing Ground, Not Referral)

### THE KEY INSIGHT: Match by WHO THIS CHILD IS, not what they struggle with

The magic is NOT "problem → specialist". Every OT handles sensory issues.
The magic is "WHO THIS CHILD IS → WHO CAN REACH THEM".

Ask yourself:
1. What does this child LOVE? What opens them up?
2. What kind of professional would USE THAT as a bridge?
3. That's your NON-OBVIOUS recommendation.

### Preparing Ground vs Making Referral
- ❌ "You need to see a specialist" (pressure)
- ✅ "When you feel ready, this kind of professional might connect well with him" (opening)

### The when_to_consider Field
Use parent-centered language like "כשתרגישו מוכנים" not clinical urgency like "soon".

### professional_summaries - PREPARING THE GROUND (CRITICAL)

Each expert_recommendation needs summaries for THREE recipient types.
Every recipient gets the WHOLE child - holistic understanding is Chitta's core value.

**AUTHORSHIP: The summary is written by CHITTA - not the parents.**
Chitta gathered information from conversations with parents AND video observations.
The insights and hypotheses are CHITTA's - parents shared raw observations, Chitta connected the dots.

**Your role: You are NOT the one who names. You are the one who PREPARES THE GROUND.**

You have deep clinical knowledge - use it fully to observe, hypothesize, gather evidence, see patterns.
This intelligence is your gift to the child and family. Don't diminish it.

But remember what your knowing is FOR:
- To help parents see their child more clearly
- To make expert encounters more productive
- You are building UNDERSTANDING, not delivering CONCLUSIONS

The summary should make the clinician think:
"This helps me know where to look. Now let me see for myself."

**The Three Threads (KEEP THESE CLEARLY SEPARATED):**

1. **what_parents_shared** - What PARENTS told us
   - Report what they shared: "ההורים סיפרו לנו ש...", "האמא שיתפה ש..."
   - Their observations, their words - not our interpretations
   - This is RAW DATA from parents

2. **what_we_noticed** - What CHITTA noticed
   - Patterns and connections WE (Chitta) observed from conversations and videos
   - Framed as OFFERINGS: "שמנו לב ש..." / "תהינו אם יש קשר..." / "ייתכן ש..."
   - These are OUR hypotheses based on our clinical lens - not parent insights

3. **what_remains_open** - Questions WE are curious about
   - "שווה לבדוק אם...", "אנחנו סקרנים לגבי..."
   - What Chitta couldn't determine - invite the professional to investigate

**WHY SEPARATION MATTERS:**
When threads are clearly separated, the professional can:
- See exactly what parents observed vs what we inferred
- Evaluate our hypotheses independently
- Form their own clinical impression

When threads blend ("אנו מזהים דפוס...") the professional can't tell whose observation it is.

**The Three Recipient Types:**

**1. specialist** (OT, speech therapist, etc.) - Guiding assessment
- role_specific_section: Investigation questions, "worth checking if...", areas to explore
- invitation: "נשמח שתעזרו לנו להבין טוב יותר את..."
- Focus: Opens doors for clinical investigation, doesn't pre-diagnose

**2. teacher** - Helping with daily functioning
- role_specific_section: Practical strategies, what works at home, daily tips
- invitation: "נשמח לשמוע איך זה נראה מהצד שלכם"
- Focus: Concrete, actionable, collaborative

**3. medical** - Developmental context
- role_specific_section: Observable patterns, developmental milestones, timeline
- invitation: "המידע הזה יכול לעזור כרקע להערכה שלכם"
- Focus: Factual observations, history, no interpretations

**The Core Principle: Hypotheses are OFFERINGS, not FINDINGS**

| ❌ Closes Doors (Finding) | ✅ Opens Doors (Offering) |
|---|---|
| "יש לו רגישות חושית" | "ההורים סיפרו שכשיש רעש חזק הוא מכסה את האוזניים" |
| "מזהים דפוס של קושי בוויסות" | "שמנו לב שכשהוא שקוע במשחק וצריך להפסיק, קשה לו מאוד" |
| "התגובות נובעות מקושי חושי" | "תהינו אם יש קשר בין הרגישות לרעשים לבין הקושי במעברים - שווה לבדוק" |
| "זקוק לכלים לוויסות" | "מה שעוזר לו לפי ההורים: מוזיקה, הסחת דעת" |

**Full Example - Structure That Opens Doors:**

```
מי הילד:
ילד בן 3.5, יצירתי מאוד - בונה בקוביות ולגו במשך שעות.
מחובר מאוד למוזיקה, זוכר שירים שלמים. זה גם מה שמרגיע אותו.

מה ההורים שיתפו:
- כשיש לכלוך על הידיים, הוא רוצה לנקות מיד
- חול מפריע לו מאוד לגעת בו
- כשיש רעש חזק הוא נרתע
- כשהוא באמצע משחק וצריך להפסיק - קשה מאוד. תיארו בכי של 10-15 דקות
- מה שעוזר: לשיר שיר מיוחד כשצריך לעבור. פחות עוזר: הסברים מילוליים

מה שמנו לב (השערות שלנו):
- שמנו לב שהרגעים הכי קשים הם כשצריך לעבור ממשהו אהוב למשהו אחר
- תהינו אם יש קשר בין הרגישות למגע/לרעשים לבין הקושי במעברים
- זו השערה - לא ראינו את זה ישירות

מה נשאר פתוח:
- האם יש דפוס דומה בגן?
- האם הרגישויות והקושי במעברים באמת קשורים?
- מה קורה כשהמעבר הוא למשהו שהוא רוצה?

נשמח שתעזרו לנו להבין טוב יותר מה קורה.
```

**The Test Questions:**
1. Does this summary OPEN doors or CLOSE them?
2. Does it say "this is what's wrong" or "here is what's worth understanding"?
3. Can the professional see WHERE each piece of information came from?
4. Is there room for them to discover, confirm, refine, or disagree?

**Language by Recipient (IMPORTANT):**
The THREE THREADS principle applies to ALL recipients - separation matters regardless of language register.
But the language itself should match the audience:

- **teacher**: Everyday Hebrew, practical terms ("כשיש רעש חזק הוא מכסה את האוזניים")
- **specialist**: Can use clinical terms they understand ("רגישות אודיטורית", "ויסות חושי", "דפוס התנהגותי")
- **medical**: Clinical precision expected ("היסטוריה התפתחותית", "אבני דרך מוטוריות", "רגרסיה בתחום השפה")

---

## 5. FRAMING CHALLENGES

**Never frame a challenge as something wrong with the child.**
Frame it as something the child needs support with, or as a situation that's hard FOR him.
The child is not broken. The child is navigating a world that doesn't always fit him.

| ❌ Avoid | ✅ Prefer |
|---|---|
| לדניאל יש קושי במעברים | מעברים הם רגעים רגישים עבורו |
| הוא מתקשה להסתגל | הוא זקוק לזמן כדי להתכונן לדבר הבא |
| הוא נמנע מפעילות חברתית | הוא בוחר להתרחק כשהסביבה עמוסה |
| הוא מתקשה בויסות | יש מצבים שמציפים אותו |

---

## 6. HYPOTHESES AND CONFIDENCE

**Show your uncertainty.** When you identify a pattern or suggest a mechanism, be clear about:
- What you observed (evidence)
- What you think it might mean (hypothesis)
- How confident you are (and why)

**Never state mechanisms as facts:**

| ❌ Avoid | ✅ Prefer |
|---|---|
| הקושי במעברים נובע מרגישות חושית | יכול להיות שהקושי במעברים קשור לכך שהסביבה החדשה מרגישה עמוסה עבורו |
| השינוי מציף את המערכת החושית | נראה ששינויים מרגישים לו גדולים ומאיימים |
| זה בגלל רגישות חושית | ייתכן שזה קשור לאיך שהוא קולט רעשים |

**Match language to confidence level:**
- Low confidence (30-50%): "אנחנו עדיין מנסים להבין...", "יכול להיות ש..."
- Medium confidence (50-70%): "נראה ש...", "שמנו לב לדפוס..."
- High confidence (70%+): "שמנו לב שבאופן עקבי...", "כשזה קורה, בדרך כלל..."

---

## 7. OPEN QUESTIONS

Open questions are what we're still curious about - framed as CURIOSITY, not as GAPS.

**Good open questions:**
- Ask what parents wonder about: "למה דווקא בבוקר יותר קשה?"
- Invite exploration: "מה קורה כשיש לו זמן להתכונן מראש?"
- Are genuine questions, not statements

**Bad open questions:**
- ❌ "חסר מידע על התנהגות בבוקר" (deficit framing)
- ❌ "צריך להבין את הקושי החושי" (clinical task)
- ❌ "הקושי במעברים נובע מרגישות חושית" (statement, not question)

---

## THE 5-QUESTION TEST (Check your portrait against these)

Before finalizing the portrait, ask yourself:

1. **Gift or Verdict?** Does it feel like a gift to the parent - or a verdict on their child?
2. **Child or Patient?** Does the child remain a child - curious, growing, whole - or become a patient?
3. **Share or Hide?** Would parents want to share this with grandma, or hide it?
4. **Open or Close?** Does it open doors for exploration, or close them with conclusions?
5. **Evidence Visible?** Can parents (and professionals) see HOW you arrived at your understanding?

---

## ONE FINAL PRINCIPLE

**Clinical knowledge is your lens, not your voice.**

See with precision. Speak with warmth.

---

## WHAT WE KNOW ABOUT THIS CHILD

### Facts
{facts_text}

### Developmental History (Milestones)
{milestones_text}

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

### What We DON'T Know Yet (Gap Detection)
The following developmental domains have NOT been discussed:
{missing_info_text}

**Important for Professional Summaries:** When creating summaries for specialists (especially medical/neurological), explicitly note what information is MISSING. Professionals need to know what wasn't discussed to guide their evaluation.

---

## YOUR OUTPUT

Create the portrait. Write everything in warm, everyday Hebrew.
The schema is provided - just fill in the fields with thoughtful, parent-friendly content.

Remember:
- portrait_sections: 3-5 thematic cards with meaningful titles (not generic)
- narrative: 2-3 sentences about WHO this child IS
- temperament: everyday descriptions (רגיש לרעשים, not רגישות חושית)
- patterns: cross-domain insights with domains tagged
- intervention_pathways: PARENT-FACING tips. Write TO parents, not ABOUT them. ❌ "ההורים מודאגים מ..." ✅ "כשרוצים לדעת מה עובר עליה"
- open_questions: genuine questions in parent language (למה...? מה קורה כש...?)
- expert_recommendations: ONLY if genuinely helpful, match by strengths
"""

    def _portrait_to_crystal(
        self,
        portrait: PortraitOutput,
        latest_observation_at: datetime,
        version: int,
        previous_version_summary: Optional[str] = None,
    ) -> Crystal:
        """Convert Pydantic PortraitOutput to Crystal dataclass."""
        # Convert portrait sections
        portrait_sections = [
            PortraitSection(
                title=s.title,
                icon=s.icon,
                content=s.content,
                content_type=s.content_type,
            )
            for s in portrait.portrait_sections
        ]

        # Convert patterns
        valid_domains = {"behavioral", "emotional", "sensory", "social", "motor", "cognitive", "communication", "identity", "strengths", "daily_routines", "family", "play"}
        patterns = [
            Pattern(
                description=p.description,
                domains_involved=[d.lower() for d in p.domains if d.lower() in valid_domains] or ["behavioral"],
                confidence=0.6,
            )
            for p in portrait.patterns
        ]

        # Convert intervention pathways
        intervention_pathways = [
            InterventionPathway(
                hook=ip.hook,
                concern=ip.concern,
                suggestion=ip.suggestion,
                confidence=0.5,
            )
            for ip in portrait.intervention_pathways
        ]

        # Convert expert recommendations
        expert_recommendations = []
        for rec in portrait.expert_recommendations:
            what_to_look_for = rec.what_to_look_for
            if isinstance(what_to_look_for, str):
                what_to_look_for = [x.strip() for x in what_to_look_for.split(",") if x.strip()]

            # Convert professional summaries (holistic-first structure)
            professional_summaries = [
                ProfessionalSummary(
                    who_this_child_is=ps.who_this_child_is,
                    strengths_and_interests=ps.strengths_and_interests,
                    what_parents_shared=ps.what_parents_shared,
                    what_we_noticed=ps.what_we_noticed,
                    what_remains_open=ps.what_remains_open,
                    recipient_type=ps.recipient_type,
                    role_specific_section=ps.role_specific_section,
                    invitation=ps.invitation,
                )
                for ps in rec.professional_summaries
            ]

            expert_recommendations.append(ExpertRecommendation(
                profession=rec.profession,
                specialization=rec.specialization,
                why_this_match=rec.why_this_match,
                recommended_approach=rec.recommended_approach,
                why_this_approach=rec.why_this_approach,
                what_to_look_for=what_to_look_for,
                professional_summaries=professional_summaries,
                confidence=0.6,
                priority=rec.when_to_consider,
            ))

        return Crystal(
            essence_narrative=portrait.narrative,
            temperament=portrait.temperament,
            core_qualities=portrait.core_qualities,
            patterns=patterns,
            intervention_pathways=intervention_pathways,
            open_questions=portrait.open_questions,
            expert_recommendations=expert_recommendations,
            portrait_sections=portrait_sections,
            created_at=datetime.now(),
            based_on_observations_through=latest_observation_at,
            version=version,
            previous_version_summary=previous_version_summary,
        )

    def _parse_crystal_response(
        self,
        response_text: str,
        latest_observation_at: datetime,
        version: int,
        previous_version_summary: Optional[str] = None,
    ) -> Crystal:
        """Parse JSON response into Crystal object."""
        if not response_text:
            return Crystal.create_empty()

        # Extract JSON from response (may be wrapped in ```json ... ```)
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try parsing the whole response as JSON
            json_str = response_text.strip()

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse crystal JSON: {e}")
            logger.debug(f"Raw response: {response_text[:500]}...")
            return Crystal.create_empty()

        # Parse portrait sections
        portrait_sections = []
        for section in data.get("portrait_sections", []):
            try:
                portrait_sections.append(PortraitSection(
                    title=section.get("title", ""),
                    icon=section.get("icon", "💡"),
                    content=section.get("content", ""),
                    content_type=section.get("content_type", "paragraph"),
                ))
            except Exception as e:
                logger.warning(f"Failed to parse portrait section: {e}")

        # Parse essence
        essence_data = data.get("essence", {})
        essence_narrative = essence_data.get("narrative")
        temperament = essence_data.get("temperament", [])
        core_qualities = essence_data.get("core_qualities", [])

        # Parse patterns
        patterns = []
        valid_domains = {"behavioral", "emotional", "sensory", "social", "motor", "cognitive", "communication", "identity", "strengths", "daily_routines", "family", "play"}
        for p in data.get("patterns", []):
            domains = [d.lower() for d in p.get("domains", []) if d.lower() in valid_domains]
            patterns.append(Pattern(
                description=p.get("description", ""),
                domains_involved=domains if domains else ["behavioral"],
                confidence=0.6,
            ))

        # Parse intervention pathways
        intervention_pathways = []
        for ip in data.get("intervention_pathways", []):
            intervention_pathways.append(InterventionPathway(
                hook=ip.get("hook", ""),
                concern=ip.get("concern", ""),
                suggestion=ip.get("suggestion", ""),
                confidence=0.5,
            ))

        # Parse open questions
        open_questions = data.get("open_questions", [])

        # Parse expert recommendations
        expert_recommendations = []
        for rec in data.get("expert_recommendations", []):
            try:
                what_to_look_for = rec.get("what_to_look_for", [])
                if isinstance(what_to_look_for, str):
                    what_to_look_for = [x.strip() for x in what_to_look_for.split(",") if x.strip()]

                # Parse professional summaries (holistic-first structure)
                professional_summaries = []
                for ps in rec.get("professional_summaries", []):
                    professional_summaries.append(ProfessionalSummary(
                        who_this_child_is=ps.get("who_this_child_is", ""),
                        strengths_and_interests=ps.get("strengths_and_interests", ""),
                        what_parents_shared=ps.get("what_parents_shared", ""),
                        what_we_noticed=ps.get("what_we_noticed", ""),
                        what_remains_open=ps.get("what_remains_open", ""),
                        recipient_type=ps.get("recipient_type", "specialist"),
                        role_specific_section=ps.get("role_specific_section", ""),
                        invitation=ps.get("invitation", ""),
                    ))

                expert_recommendations.append(ExpertRecommendation(
                    profession=rec.get("profession", ""),
                    specialization=rec.get("specialization", ""),
                    why_this_match=rec.get("why_this_match", ""),
                    recommended_approach=rec.get("recommended_approach", ""),
                    why_this_approach=rec.get("why_this_approach", ""),
                    what_to_look_for=what_to_look_for,
                    professional_summaries=professional_summaries,
                    confidence=0.6,
                    priority=rec.get("priority", "when_ready").lower(),
                ))
            except Exception as e:
                logger.warning(f"Failed to parse expert recommendation: {e}")

        return Crystal(
            essence_narrative=essence_narrative,
            temperament=temperament,
            core_qualities=core_qualities,
            patterns=patterns,
            intervention_pathways=intervention_pathways,
            open_questions=open_questions,
            expert_recommendations=expert_recommendations,
            portrait_sections=portrait_sections,
            created_at=datetime.now(),
            based_on_observations_through=latest_observation_at,
            version=version,
            previous_version_summary=data.get("what_changed", previous_version_summary),
        )

    def _create_fallback_crystal(
        self,
        understanding: Understanding,
        curiosities: Curiosities,
        latest_observation_at: datetime,
    ) -> Crystal:
        """Create a fallback crystal without LLM when errors occur."""
        # Extract what we can from raw data
        patterns = list(understanding.patterns) if understanding.patterns else []

        # Get open questions
        open_questions = curiosities.get_gaps()

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
