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


# Singleton instance
_synthesis_service: Optional[SynthesisService] = None


def get_synthesis_service() -> SynthesisService:
    """Get or create the synthesis service singleton."""
    global _synthesis_service
    if _synthesis_service is None:
        _synthesis_service = SynthesisService()
    return _synthesis_service
