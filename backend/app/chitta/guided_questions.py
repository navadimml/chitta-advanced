"""
Guided Question Generator - LLM-powered personalized questions for guided collection.

Instead of hardcoded templates, we use LLM to generate natural, personalized questions
that incorporate child's name, gender, age, and what we already know.
"""

import logging
import os
from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from app.services.llm.factory import create_llm_provider
from app.services.llm.base import Message as LLMMessage

from .models import Understanding
from .clinical_gaps import ClinicalGap, CLINICAL_VOCABULARY

logger = logging.getLogger(__name__)


@dataclass
class ChildContext:
    """Context about the child for question generation."""
    name: Optional[str]
    gender: Optional[str]  # "male" or "female"
    age_months: Optional[int]

    def age_description(self) -> str:
        """Format age as human-readable string."""
        if self.age_months is None:
            return "unknown"

        years = self.age_months // 12
        months = self.age_months % 12

        if years > 0 and months > 0:
            return f"{years} years and {months} months"
        elif years > 0:
            return f"{years} years"
        else:
            return f"{months} months"


class GuidedQuestionGenerator:
    """
    Generate personalized questions for guided collection using LLM.

    Instead of hardcoded templates like "איך הוא ישן?" that don't adapt,
    we generate questions that:
    - Use correct gender (היא/הוא)
    - Include child's name
    - Reference what we already know
    - Sound natural and conversational
    """

    def __init__(self):
        self._llm = None

    def _get_llm(self):
        """Get LLM provider (lazy init)."""
        if self._llm is None:
            model = os.getenv("LLM_MODEL", "gemini-2.5-flash")
            provider = os.getenv("LLM_PROVIDER", "gemini")
            self._llm = create_llm_provider(
                provider_type=provider,
                model=model,
                use_enhanced=True,
            )
        return self._llm

    async def generate_opening_question(
        self,
        gaps: List[ClinicalGap],
        child_context: ChildContext,
        understanding: Understanding,
        recipient_type: str,
    ) -> str:
        """
        Generate a personalized opening question for guided collection.

        Args:
            gaps: List of clinical gaps to address (we'll focus on the first one)
            child_context: Child's name, gender, age
            understanding: What we already know about the child
            recipient_type: Who we're preparing the summary for

        Returns:
            Natural Hebrew question to ask the parent
        """
        if not gaps:
            return "הי! יש משהו שתרצי לספר לי לפני שנכין את הסיכום?"

        first_gap = gaps[0]
        clinical_terms = [CLINICAL_VOCABULARY.get(g.field, {}).get("clinical_term", g.field) for g in gaps[:3]]

        prompt = self._build_prompt(
            first_gap=first_gap,
            all_clinical_terms=clinical_terms,
            child_context=child_context,
            understanding=understanding,
            recipient_type=recipient_type,
        )

        try:
            llm = self._get_llm()
            response = await llm.chat(
                messages=[
                    LLMMessage(role="system", content=prompt),
                    LLMMessage(role="user", content="Generate the Hebrew question."),
                ],
                functions=None,  # Text response only
                temperature=0.7,
                max_tokens=4000,  # Hebrew needs higher token limit to prevent truncation
            )

            question = response.content.strip()

            # Basic validation - should start with Hebrew or "הי"
            if question and (question[0] >= '\u0590' or question.startswith('"הי')):
                # Strip any surrounding quotes the LLM might add
                question = question.strip('"\'')
                return question
            else:
                logger.warning(f"LLM returned unexpected format: {question[:100]}")
                return self._fallback_question(first_gap, child_context)

        except Exception as e:
            logger.error(f"Error generating question: {e}")
            return self._fallback_question(first_gap, child_context)

    def _build_prompt(
        self,
        first_gap: ClinicalGap,
        all_clinical_terms: List[str],
        child_context: ChildContext,
        understanding: Understanding,
        recipient_type: str,
    ) -> str:
        """Build the prompt for question generation."""

        # Format what we know
        existing_knowledge = self._format_existing_knowledge(understanding)

        # Recipient type in Hebrew
        recipient_hebrew = {
            "neurologist": "נוירולוג",
            "speech_therapist": "קלינאית תקשורת",
            "ot": "מרפאה בעיסוק",
            "psychologist": "פסיכולוג",
            "pediatrician": "רופא ילדים",
            "psychiatrist": "פסיכיאטר",
        }.get(recipient_type, recipient_type)

        # Get clinical term for the first gap
        first_clinical_term = CLINICAL_VOCABULARY.get(first_gap.field, {}).get("clinical_term", first_gap.field)

        return f"""## Role
You are Chitta - a warm, knowledgeable guide helping parents understand their child's development.
You speak natural Hebrew like a supportive friend, not a clinical form.

## Context
A parent is preparing a summary for a {recipient_hebrew} ({recipient_type}).
We need to gather more information about: {', '.join(all_clinical_terms)}

## Child Information
- Name: {child_context.name or 'not yet known'}
- Age: {child_context.age_description()}
- Gender: {child_context.gender or 'not specified'}

## What We Already Know
{existing_knowledge}

## Your Task
Generate ONE natural Hebrew question to ask the parent about: {first_clinical_term} ({first_gap.field})

## Critical Requirements
1. Use the child's NAME in the question (if known)
2. Use correct GENDER agreement for the CHILD in Hebrew:
   - For girls (female): היא, שלה, אותה, לה (she, her, hers)
   - For boys (male): הוא, שלו, אותו, לו (he, him, his)
3. Use GENDER-NEUTRAL language when addressing the PARENT (we don't know if they're mother or father):
   - AVOID gendered imperatives like "ספרי" (feminine) or "ספר" (masculine)
   - USE neutral phrasing like: "רציתי לשאול", "אפשר לדעת", "מה קורה עם..."
   - Or first-person: "בואו נדבר על..." (let's talk about)
4. Sound conversational - like asking a friend, not filling a form
5. If relevant context exists from what we know, weave it in naturally
6. Start with "הי!" (Hi!) for a warm opening
7. Keep it short - one question, maybe with a follow-up

## Examples of Good Questions (for a girl named מיכל)
- "הי! לפני שנכין את הסיכום, רציתי לשאול - איך מיכל ישנה בלילות?"
- "הי! אפשר לשמוע קצת על הלידה של מיכל - איך היא הייתה?"
- "הי! מתי מיכל התחילה ללכת? ומה עם מילים ראשונות?"

## Examples of Good Questions (for a boy named יונתן)
- "הי! לפני שנכין את הסיכום, רציתי לשאול - איך יונתן ישן בלילות?"
- "הי! אפשר לשמוע קצת על הלידה של יונתן - איך היא הייתה?"
- "הי! מתי יונתן התחיל ללכת? ומה עם מילים ראשונות?"

## Output Format
Return ONLY the Hebrew question. No explanations, no English, no prefixes."""

    def _format_existing_knowledge(self, understanding: Understanding) -> str:
        """Format what we already know about the child."""
        sections = []

        # Essence/narrative
        if understanding.essence and understanding.essence.narrative:
            sections.append(f"- Overall: {understanding.essence.narrative[:200]}")

        # Recent observations by domain
        domain_counts = {}
        for obs in understanding.observations[-20:]:  # Recent observations
            domain = obs.domain or "general"
            if domain not in domain_counts:
                domain_counts[domain] = 0
            domain_counts[domain] += 1

        if domain_counts:
            domains_str = ", ".join([f"{d} ({c})" for d, c in sorted(domain_counts.items(), key=lambda x: -x[1])[:5]])
            sections.append(f"- Observations in: {domains_str}")

        # Milestones
        if understanding.milestones:
            milestone_summary = f"- {len(understanding.milestones)} developmental milestones recorded"
            sections.append(milestone_summary)

        # Patterns
        if understanding.patterns:
            pattern_count = len(understanding.patterns)
            sections.append(f"- {pattern_count} patterns noticed")

        if sections:
            return "\n".join(sections)
        else:
            return "We're just getting to know this child - no observations yet."

    def _fallback_question(self, gap: ClinicalGap, child_context: ChildContext) -> str:
        """Generate a basic fallback question if LLM fails."""
        # Use the parent_question from vocabulary as fallback
        question = gap.parent_question or f"ספרי לי על {gap.parent_description}"

        # Try to use child name if available
        if child_context.name:
            name = child_context.name
            # Simple gender adjustment for common patterns
            if child_context.gender == "female":
                question = question.replace("הוא ", "היא ").replace("שלו", "שלה").replace(" לו ", " לה ")

        return f"הי! {question}"


def calculate_age_months(birth_date: Optional[date]) -> Optional[int]:
    """Calculate age in months from birth date."""
    if not birth_date:
        return None

    today = date.today()
    months = (today.year - birth_date.year) * 12 + (today.month - birth_date.month)
    if today.day < birth_date.day:
        months -= 1
    return max(0, months)
