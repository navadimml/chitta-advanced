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
    ExplorationCycle,
    Crystal,
    InterventionPathway,
    ExpertRecommendation,
    ProfessionalSummary,
    TemporalFact,
    PortraitSection,
)
from .portrait_schema import PortraitOutput
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
        """Create a fresh crystal from all observations using structured output."""
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
        """Build prompt for crystallization - focuses on guidance, not schema."""
        name = child_name or "הילד"

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
                f"- {p.description}: {', '.join(p.domains_involved)}"
                for p in previous_crystal.patterns
            ]) or "No patterns identified previously."

            previous_pathways = "\n".join([
                f"- {ip.hook} -> {ip.concern}: {ip.suggestion}"
                for ip in previous_crystal.intervention_pathways
            ]) or "No intervention pathways identified previously."

            return f"""
# Crystal Update - Child: {name}

You are updating an existing understanding with new information.

## CRITICAL: Parent-Friendly Language

You are writing for PARENTS, not clinicians. Avoid clinical jargon.

❌ NEVER USE:
- עיבוד רגשי (emotional processing)
- רגישות חושית (sensory sensitivity)
- גמישות קוגניטיבית (cognitive flexibility)
- ויסות עצמי (self-regulation)
- מעברים (transitions - use concrete examples)

✅ ALWAYS USE:
- Simple, concrete everyday language
- Situations parents see at home: "כשצריך לעבור ממשחק לאוכל"
- Feelings parents recognize: "להרגיע את הלב"
- Objects and activities from their world

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
[Updated essence narrative - 2-3 sentences about who this child is. Write in warm Hebrew, no clinical terms.]

TEMPERAMENT:
[Comma-separated list in everyday Hebrew. NOT: רגיש חושית. YES: רגיש לרעשים, זהיר עם דברים חדשים]

CORE_QUALITIES:
[Comma-separated list in everyday Hebrew. e.g.: סקרן, מתאמץ, יצירתי]

PATTERNS:
- [What we noticed in EVERYDAY language]: [areas involved]
- [Another observation]: [areas]

INTERVENTION_PATHWAYS:
- [What he loves] -> [Challenge in parent words]: [Concrete tip with example]

OPEN_QUESTIONS:
- [Question in parent words]
- [Another question]

EXPERT_RECOMMENDATIONS:
Update existing recommendations or add new ones based on new information.
Only include if professional help would genuinely benefit this child.

IMPORTANT: Match based on WHAT THE CHILD LOVES, not what they struggle with.
Ask: "What professional would USE this child's interests as a bridge?"

⚠️ HEBREW ONLY: Write everything in Hebrew. Do NOT add English translations in parentheses.
❌ NOT: ריפוי בעיסוק (Occupational Therapy)
✅ YES: ריפוי בעיסוק

Format for each recommendation:
---EXPERT---
PROFESSION: [profession in Hebrew]
SPECIALIZATION: [A REAL specialization that RESONATES with this child's strengths. Be creative! e.g., "טיפול באומנות", "מוזיקה טיפולית", "טיפול בעזרת בעלי חיים", "טיפול בתנועה"]
WHY_THIS_MATCH: [Connect child's strength to why this professional type would reach them]
RECOMMENDED_APPROACH: [What approach would work]
WHY_THIS_APPROACH: [Based on how THIS child opens up]
WHAT_TO_LOOK_FOR: [2-3 things, comma-separated]
SUMMARY_FOR_PROFESSIONAL: [A gift to the clinician - show three threads: (1) What parents shared, (2) What we noticed - patterns/behaviors, (3) What remains open to explore. Frame as offerings, invite exploration, leave room for clinician to discover.]
PRIORITY: [when_ready | soon | important]
---END_EXPERT---

WHAT_CHANGED:
[Brief note on what changed in this update]
"""

        else:
            # Fresh crystallization prompt - Expert-guided portrait creation
            return f"""
# Portrait Creation for {name}

You are creating a PORTRAIT - a living image of who this child is - not a report.

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
- "The humming during meals AND the need for routine before bed - same pattern"
- "His interest in organizing things AND his difficulty with transitions - related"
- "This isn't bad behavior - this is age-appropriate given his profile"

**Recognition is the foundation, insight is the gift. The best portrait does BOTH.**

### Clinical Knowledge as Lens, Not Voice
You SEE with clinical precision. You SPEAK with parental warmth.
Your knowledge is the lens through which you understand - not the voice through which you communicate.

---

## 2. LANGUAGE PRINCIPLES

### The Grandma Test
Would a grandmother understand every word? If not, rewrite.

### Situational Language
Describe HOW the child moves through the world, not what they "have":
- ❌ "יש לו רגישות חושית" (clinical label)
- ✅ "כשיש רעש חזק הוא מכסה את האוזניים ומחפש פינה שקטה" (situation)

### Forbidden Terms (NEVER use these):
- עיבוד רגשי, רגישות חושית, גמישות קוגניטיבית
- ויסות עצמי, מעברים (use concrete examples instead)
- Any English in parentheses

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
- BAD: "הוא רגיש לרעשים" (Single observation, no chain)

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

### professional_summaries - HOLISTIC-FIRST SUMMARIES (CRITICAL)

Each expert_recommendation needs summaries for THREE recipient types.
Every recipient gets the WHOLE child - holistic understanding is Chitta's core value.
The lens (emphasis) changes based on who's receiving.

**Your role: Help the professional know WHERE TO LOOK**
You are not the one who names. You are the one who prepares the ground.
The summary should make them think: "This helps me know where to look. Now let me see for myself."

**The Three Threads (present in ALL summaries):**
1. **who_this_child_is** - 2-3 sentences about who this child IS as a whole person
2. **strengths_and_interests** - what opens them up, what they love (the bridge for any professional)
3. **what_parents_shared** - parent observations in THEIR words
4. **what_we_noticed** - patterns, connections (framed as offerings, not findings)
5. **what_remains_open** - questions worth exploring

**The Three Recipient Types:**

**1. teacher** - Getting the summary to help with daily functioning
- role_specific_section: Practical strategies, what works at home, daily tips
- invitation: "We hope you can help us understand how he is in the classroom setting"
- Focus: Concrete, actionable, "here's what helps"

**2. specialist** - Getting the summary to guide assessment
- role_specific_section: Investigation questions, "worth checking if...", areas to explore
- invitation: "We'd value your professional perspective on these patterns"
- Focus: Opens doors for clinical investigation, doesn't close them

**3. medical** - Getting the summary for developmental context
- role_specific_section: Observable patterns, developmental markers, timeline
- invitation: "This background might be helpful context for your evaluation"
- Focus: Factual observations, developmental history, no interpretations

**Framing principles:**
- Hypotheses are OFFERINGS, not findings ("שמנו לב ש..." not "יש לו...")
- Pattern recognition OPENS questions, not closes them
- Invite them in - leave room to discover, confirm, refine, or disagree
- Say "here is what's worth understanding" not "here is what's wrong"

**The Test:** Does this summary OPEN doors or CLOSE them?

**WRONG (closes doors):**
"בן 3.5, מציג דפוס של רגישות חושית שמשפיעה על ההשתתפות החברתית. זקוק לכלים לוויסות."

**RIGHT (opens doors):**
"בן 3.5, מוזיקלי ויצירתי מאוד - בונה לגו במשך שעות.
ההורים שיתפו שכשיש רעש חזק הוא מכסה את האוזניים. בגן קשה לו להישאר בפעילות קבוצתית כשיש המולה.
שמנו לב לקשר אפשרי - שווה לבדוק."

---

## 5. FRAMING CHALLENGES

Challenges are not "something wrong with this child" but "a situation that's hard FOR him".
The child is whole. The environment/situation creates difficulty.

- ❌ "הוא מתקשה בויסות" (deficit framing)
- ✅ "יש מצבים שמציפים אותו" (situational framing)

---

## 6. HYPOTHESES AND CONFIDENCE

Never state mechanisms as facts. Show uncertainty:
- ❌ "זה בגלל רגישות חושית" (stating mechanism as fact)
- ✅ "ייתכן שזה קשור לאיך שהוא קולט רעשים" (hypothesis)

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

1. **Gift or Verdict?** Does this feel like a gift to the parent or a verdict on their child?
2. **Child or Patient?** Does this describe a child or a patient?
3. **Share or Hide?** Would a parent want to share this with grandma, or hide it?
4. **Open or Close?** Does this open doors for the child or close them?
5. **Evidence Visible?** Can parents see WHERE you saw what you're describing?

---

## WHAT WE KNOW ABOUT THIS CHILD

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

## YOUR OUTPUT

Create the portrait. Write everything in warm, everyday Hebrew.
The schema is provided - just fill in the fields with thoughtful, parent-friendly content.

Remember:
- portrait_sections: 3-5 thematic cards with meaningful titles (not generic)
- narrative: 2-3 sentences about WHO this child IS
- temperament: everyday descriptions (רגיש לרעשים, not רגישות חושית)
- patterns: cross-domain insights with domains tagged
- intervention_pathways: connect what they love to what's hard
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
