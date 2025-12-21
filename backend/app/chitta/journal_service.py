"""
Journal Service - Parent journal entry processing

Processes parent journal entries and feeds observations into understanding.
Parent journal entries are GOLD - direct observations from daily life.

Features:
- Extract facts from entries with temporal context
- Convert relative temporal expressions to absolute timestamps
- Detect and record developmental milestones
- Connect to curiosity engine for boost updates
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Awaitable
import logging
import re
import json

from .gestalt import Darshan
from .models import TemporalFact, DevelopmentalMilestone, JournalEntry
from app.services.llm.base import Message as LLMMessage

logger = logging.getLogger(__name__)


class JournalService:
    """Processes parent journal entries into structured understanding."""

    async def process_parent_journal_entry(
        self,
        darshan: Darshan,
        entry_text: str,
        entry_type: str,  # "התקדמות" | "תצפית" | "אתגר"
        persist_callback: Callable[[Darshan], Awaitable[None]],
        get_llm_callback: Callable,
    ) -> Dict[str, Any]:
        """
        Process a parent journal entry and feed it into understanding.

        Parent journal entries are GOLD - direct observations from daily life.
        We extract facts from them just like conversation messages.

        This connects the parent journal to the living system:
        - Facts extracted and added to Understanding (with ABSOLUTE timestamps)
        - Curiosity engine notified of new learnings
        - Milestones detected and recorded

        IMPORTANT: Relative temporal expressions ("היום", "אתמול") are converted
        to absolute timestamps at creation time so they retain meaning later.
        """
        entry_timestamp = datetime.now()  # When the journal entry was created

        # Map entry type to significance and domain hint
        type_mapping = {
            "התקדמות": {"significance": "notable", "domain_hint": "strengths"},
            "תצפית": {"significance": "routine", "domain_hint": None},
            "אתגר": {"significance": "notable", "domain_hint": "concerns"},
        }
        mapping = type_mapping.get(entry_type, {"significance": "routine", "domain_hint": None})

        # Use LLM to extract facts from journal entry (lightweight extraction)
        extracted = await self._extract_from_journal_entry(
            entry_text,
            darshan.child_name,
            mapping["domain_hint"],
            get_llm_callback,
        )

        facts_added = 0
        milestone_detected = False

        # Add facts to understanding AND connect to curiosity engine
        for fact_data in extracted.get("facts", []):
            # Convert relative temporal expression to ABSOLUTE timestamp
            when_str = fact_data.get("when")
            t_valid = self._parse_relative_temporal(when_str, entry_timestamp)

            fact = TemporalFact(
                content=fact_data["content"],
                domain=fact_data.get("domain", "general"),
                source="parent_journal",
                t_valid=t_valid,  # ABSOLUTE timestamp (when behavior happened)
                t_created=entry_timestamp,  # When we learned about it
                confidence=0.8,  # High confidence - parent's direct observation
            )
            darshan.understanding.add_fact(fact)
            # Connect to curiosity engine - this makes journal entries boost curiosities
            darshan._curiosities.on_observation_learned(fact)
            facts_added += 1

        # Add milestone if detected
        if extracted.get("milestone"):
            milestone = DevelopmentalMilestone.create(
                description=extracted["milestone"]["description"],
                domain=extracted["milestone"].get("domain", "general"),
                milestone_type=extracted["milestone"].get("type", "observation"),
                age_months=extracted["milestone"].get("age_months"),
                age_description=extracted["milestone"].get("age_description"),
                source="parent_journal",
            )
            darshan.understanding.add_milestone(milestone)
            milestone_detected = True
            logger.info(f"Milestone from journal: {milestone.description}")

        # Create system journal entry to track this
        entry = JournalEntry.create(
            summary=entry_text[:100] + "..." if len(entry_text) > 100 else entry_text,
            learned=[f["content"] for f in extracted.get("facts", [])],
            significance=mapping["significance"],
        )
        darshan.journal.append(entry)

        # Persist changes
        await persist_callback(darshan)

        logger.info(f"Journal entry processed: {facts_added} facts, milestone={milestone_detected}")

        return {
            "status": "processed",
            "facts_extracted": facts_added,
            "milestone_detected": milestone_detected,
            "extracted": extracted,  # For debugging/transparency
        }

    def _parse_relative_temporal(
        self,
        when_str: Optional[str],
        reference_time: datetime
    ) -> datetime:
        """
        Parse relative temporal expression into ABSOLUTE timestamp.

        Uses reference_time (entry creation) as the anchor point.
        "היום" at 3pm on June 15 -> June 15, 3pm
        "אתמול" at 3pm on June 15 -> June 14, 3pm
        "לפני שבוע" at 3pm on June 15 -> June 8, 3pm

        This ensures temporal meaning is preserved even when read later.

        Note: This is parsing specific Hebrew temporal keywords with well-defined
        meanings, not semantic understanding. Similar to parsing date formats.
        """
        if not when_str:
            return reference_time

        when_lower = when_str.lower().strip()

        # Today / Now
        if when_lower in ["היום", "עכשיו", "now", "today"]:
            return reference_time

        # Yesterday
        if when_lower in ["אתמול", "yesterday"]:
            return reference_time - timedelta(days=1)

        # Day before yesterday
        if when_lower in ["שלשום"]:
            return reference_time - timedelta(days=2)

        # Weeks ago
        if "שבוע" in when_lower:
            if "לפני" in when_lower:
                if "שבועיים" in when_lower:
                    return reference_time - timedelta(weeks=2)
                # Check for number
                match = re.search(r'(\d+)', when_lower)
                if match:
                    weeks = int(match.group(1))
                    return reference_time - timedelta(weeks=weeks)
                return reference_time - timedelta(weeks=1)

        # Months ago
        if "חודש" in when_lower or "חודשים" in when_lower:
            if "לפני" in when_lower:
                match = re.search(r'(\d+)', when_lower)
                if match:
                    months = int(match.group(1))
                    return reference_time - timedelta(days=months * 30)
                if "חודשיים" in when_lower:
                    return reference_time - timedelta(days=60)
                return reference_time - timedelta(days=30)

        # "Usually" / habitual - treat as ongoing, use reference time
        if when_lower in ["בדרך כלל", "תמיד", "usually", "always"]:
            return reference_time

        # Age-based expressions - these are about child's age, not calendar time
        # We can't convert to absolute date without knowing child's birthdate
        # So we use reference_time but this should really trigger milestone recording
        if "בגיל" in when_lower or "גיל" in when_lower:
            return reference_time  # Can't determine absolute time without birthdate

        # Default: use reference time
        return reference_time

    async def _extract_from_journal_entry(
        self,
        entry_text: str,
        child_name: Optional[str],
        domain_hint: Optional[str],
        get_llm_callback: Callable,
    ) -> Dict[str, Any]:
        """
        Lightweight LLM extraction from parent journal entry.

        Returns facts (with temporal expressions) and potential milestones.
        """
        prompt = f"""Extract developmental observations from this parent journal entry.

Child: {child_name or "the child"}
Entry: "{entry_text}"
{f"Context: This was marked as '{domain_hint}' by the parent" if domain_hint else ""}

Return JSON with:
1. "facts": Array of observations. Each has:
   - "content": The observation in Hebrew (concise)
   - "domain": One of: motor, social, emotional, cognitive, language, sensory, regulation, strengths, concerns, sleep, feeding, play
   - "when": Extract the EXACT temporal expression from the text:
     * "היום" if they say today
     * "אתמול" if yesterday
     * "לפני שבוע" / "לפני שבועיים" for weeks
     * "לפני חודש" for month
     * "בגיל X חודשים" for age-based (also triggers milestone)
     * null if no timing mentioned

2. "milestone": null OR an object if this describes a developmental milestone:
   - "description": What happened (Hebrew)
   - "domain": motor, language, social, cognitive, regulation
   - "type": "achievement" (positive), "concern" (worry), "regression" (lost skill)
   - "age_months": Age in months if mentioned (12=שנה, 18=שנה וחצי, 24=שנתיים)
   - "age_description": Original age text (e.g., "בגיל שנה וחצי")

Guidelines:
- Extract 1-3 key observations
- A milestone is something that marks development: first word, walking, lost a skill
- Extract "when" EXACTLY as written - we will convert to timestamp
- Be concise

Example input: "אתמול דני אמר 'אמא' בפעם הראשונה!"
Example output:
{{
  "facts": [
    {{"content": "אמר 'אמא' בפעם הראשונה", "domain": "language", "when": "אתמול"}}
  ],
  "milestone": {{
    "description": "אמר 'אמא' - מילה ראשונה",
    "domain": "language",
    "type": "achievement",
    "age_months": null,
    "age_description": null
  }}
}}

Return ONLY valid JSON, no other text."""

        try:
            llm = get_llm_callback()
            response = await llm.chat(
                messages=[LLMMessage(role="user", content=prompt)],
                temperature=0.2,  # Low temperature for structured extraction
                max_tokens=800,
            )

            # Parse JSON response
            content = response.content.strip()
            # Try to extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                return json.loads(json_match.group())
            return {"facts": [], "milestone": None}

        except Exception as e:
            logger.error(f"Error extracting from journal entry: {e}")
            # Fallback: create a simple fact from the entry
            return {
                "facts": [{"content": entry_text[:100], "domain": domain_hint or "general", "when": None}],
                "milestone": None
            }


# Singleton accessor
_journal_service: Optional[JournalService] = None


def get_journal_service() -> JournalService:
    """Get the singleton JournalService instance."""
    global _journal_service
    if _journal_service is None:
        _journal_service = JournalService()
    return _journal_service
