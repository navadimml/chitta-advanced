"""
Clinical Gaps - Awareness of Missing Information

Notices missing clinical data that professionals need for useful Letters.
Different recipient types have different requirements.

KEY PRINCIPLES:
1. From CLINICAL_LANGUAGE_DESIGN.md:
   - Parent-facing text uses everyday language ("איך עברה הלידה")
   - Letters use clinical precision ("היסטוריית לידה")

2. From CLAUDE.md - NO STRING MATCHING:
   - NEVER use keyword matching to detect data
   - The LLM extracts observations WITH domains via tools
   - Check domains, not content strings
"""

from dataclasses import dataclass
from typing import List, Optional, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from .models import Understanding
    from app.models.child import Child


class GapPriority(Enum):
    CRITICAL = "critical"      # Summary incomplete without this
    IMPORTANT = "important"    # Significantly better with this
    NICE_TO_HAVE = "nice"      # Helpful but not essential


@dataclass
class ClinicalGap:
    """
    A piece of missing clinical information.

    Uses TWO languages per design principle:
    - parent_description: For UI/conversation (everyday language)
    - clinical_term: For professional summaries (clinical precision)
    """
    field: str                    # Internal ID: "birth_history", "milestones", etc.
    priority: GapPriority
    parent_description: str       # For UI - everyday language
    clinical_term: str            # For professional summaries - clinical precision
    parent_question: str          # Natural question to ask in conversation
    domains_to_check: List[str]   # Which domains indicate we have this data


# === Clinical Vocabulary ===
# From CLINICAL_LANGUAGE_DESIGN.md - the mapping between clinical and parent language
# IMPORTANT: domains_to_check is how we detect data - NO string matching!

CLINICAL_VOCABULARY = {
    "child_age": {
        "clinical_term": "גיל כרונולוגי",
        "parent_description": "הגיל של הילד/ה",
        "parent_question": "בת/בן כמה?",
        "domains_to_check": [],  # Special handling - checked via child identity
    },
    "school_status": {
        "clinical_term": "מסגרת חינוכית",
        "parent_description": "גן או בית ספר",
        "parent_question": "באיזו מסגרת הילד/ה? גן? בית ספר?",
        "domains_to_check": ["context"],  # Educational context
    },
    "birth_history": {
        "clinical_term": "היסטוריית לידה",
        "parent_description": "איך עברה הלידה",
        "parent_question": "ספרי לי קצת על הלידה - איך היא הייתה?",
        # Note: LLM may use medical domain for birth info
        "domains_to_check": ["birth_history", "medical"],
    },
    "milestones": {
        "clinical_term": "אבני דרך התפתחותיות",
        "parent_description": "מתי התחילו ללכת, לדבר",
        "parent_question": "זוכרת מתי התחילו ללכת? ומה עם מילים ראשונות?",
        # Note: LLM may use motor/language domains for milestone observations
        "domains_to_check": ["milestones", "motor", "language"],
    },
    "language_milestones": {
        "clinical_term": "אבני דרך בשפה",
        "parent_description": "מתי התחילו לדבר",
        "parent_question": "מתי התחילו לדבר? זוכרת את המילים הראשונות?",
        # Note: LLM primarily uses language domain for speech milestones
        "domains_to_check": ["language", "milestones"],
    },
    "motor_milestones": {
        "clinical_term": "אבני דרך מוטוריות",
        "parent_description": "מתי התחילו לשבת, לזחול, ללכת",
        "parent_question": "זוכרת מתי התחילו לזוז? לשבת, לזחול, ללכת?",
        # Note: LLM primarily uses motor domain for physical milestones
        "domains_to_check": ["motor", "milestones"],
    },
    "family_developmental_history": {
        "clinical_term": "היסטוריה התפתחותית במשפחה",
        "parent_description": "האם יש דברים דומים במשפחה",
        "parent_question": "יש עוד מישהו במשפחה עם דברים דומים?",
        "domains_to_check": ["context"],  # Family history captured in context domain
    },
    "sleep": {
        "clinical_term": "דפוסי שינה",
        "parent_description": "איך השינה",
        "parent_question": "ספרי לי על השינה - נרדמים בקלות? ישנים טוב?",
        "domains_to_check": ["sleep"],
    },
    "social_markers": {
        "clinical_term": "סמנים חברתיים",
        "parent_description": "קשר עין ותקשורת",
        "parent_question": "יש קשר עין כשמדברים? מסתכלים עליך?",
        "domains_to_check": ["social"],
    },
    "social_communication": {
        "clinical_term": "תקשורת חברתית",
        "parent_description": "שיתוף והצבעה על דברים",
        "parent_question": "יש הצבעה על דברים כדי להראות לך?",
        "domains_to_check": ["social"],
    },
    "joint_attention": {
        "clinical_term": "תשומת לב משותפת",
        "parent_description": "להסתכל על דברים ביחד",
        "parent_question": "כשאת מראה משהו מעניין, יש מבט עליך ואז על הדבר?",
        "domains_to_check": ["social"],
    },
    "play_patterns": {
        "clinical_term": "דפוסי משחק",
        "parent_description": "איך המשחק",
        "parent_question": "יש משחקי דמיון? משחק עם ילדים אחרים?",
        "domains_to_check": ["play"],
    },
    "sensory_patterns": {
        "clinical_term": "דפוסים חושיים",
        "parent_description": "רגישות לרעשים, מגע, אורות",
        "parent_question": "יש דברים שמפריעים - רעשים חזקים, מגע מסוים, אורות?",
        "domains_to_check": ["sensory"],
    },
    "self_care": {
        "clinical_term": "עצמאות בתפקוד יומי",
        "parent_description": "עצמאות בפעולות יומיות",
        "parent_question": "יש אכילה עצמאית? התלבשות?",
        "domains_to_check": ["motor", "regulation"],
    },
    "feeding": {
        "clinical_term": "דפוסי אכילה",
        "parent_description": "איך האכילה",
        "parent_question": "ספרי לי על האכילה - יש קשיים עם אוכל מסוים?",
        "domains_to_check": ["feeding"],
    },
    "regression": {
        "clinical_term": "נסיגה התפתחותית",
        "parent_description": "דברים שהפסיקו לעשות",
        "parent_question": "יש דברים שפעם היו וכבר לא?",
        "domains_to_check": ["milestones"],  # Regressions are milestones with type="regression"
    },
}


def _make_gap(field: str, priority: GapPriority) -> ClinicalGap:
    """Create a ClinicalGap from vocabulary."""
    vocab = CLINICAL_VOCABULARY.get(field, {})
    return ClinicalGap(
        field=field,
        priority=priority,
        parent_description=vocab.get("parent_description", field),
        clinical_term=vocab.get("clinical_term", field),
        parent_question=vocab.get("parent_question", ""),
        domains_to_check=vocab.get("domains_to_check", []),
    )


@dataclass
class LetterReadiness:
    """Assessment of readiness to generate Letter for a recipient type."""
    status: str                   # "ready" | "partial" | "not_ready"
    missing_critical: List[ClinicalGap]
    missing_important: List[ClinicalGap]
    can_generate: bool            # True even if partial
    guidance_message: Optional[str]  # Hebrew message for UI (parent language!)


class ClinicalGaps:
    """
    Awareness of missing clinical data based on recipient type.

    Different professionals need different data:
    - Neurologist: birth history, milestones, family history
    - Speech therapist: language milestones, social communication
    - OT: sensory patterns, motor milestones, self-care

    IMPORTANT: Detection is DOMAIN-BASED only.
    The LLM extracts observations with domains via tools.
    We check domains, NOT content strings.
    """

    # Requirements defined by field ID - gaps are created from vocabulary
    # child_age is critical for ALL professionals - can't assess development without age
    REQUIREMENTS_BY_RECIPIENT = {
        "neurologist": {
            "critical": ["child_age", "birth_history", "milestones"],
            "important": ["family_developmental_history", "sleep", "regression", "school_status"],
            "nice_to_have": ["social_markers"],
        },
        "speech_therapist": {
            "critical": ["child_age", "language_milestones"],
            "important": ["social_communication", "play_patterns", "joint_attention", "school_status"],
            "nice_to_have": [],
        },
        "ot": {
            "critical": ["child_age", "sensory_patterns", "motor_milestones"],
            "important": ["self_care", "play_patterns", "school_status"],
            "nice_to_have": [],
        },
        "pediatrician": {
            "critical": ["child_age", "birth_history", "milestones"],
            "important": ["sleep", "feeding", "social_markers", "school_status"],
            "nice_to_have": [],
        },
        "default": {
            "critical": ["child_age"],
            "important": [],
            "nice_to_have": [],
        },
    }

    def check_readiness(
        self,
        recipient_type: str,
        understanding: "Understanding",
        child: Optional["Child"] = None,
        child_birth_date: Optional["date"] = None,
    ) -> LetterReadiness:
        """
        Check if we have enough data to generate a useful Letter.

        Args:
            child_birth_date: Optional birth date from Darshan (when child object not available)

        Returns readiness status with details about what's missing.
        """
        self._child_birth_date = child_birth_date  # Store for _has_data_for
        reqs = self.REQUIREMENTS_BY_RECIPIENT.get(
            recipient_type,
            self.REQUIREMENTS_BY_RECIPIENT["default"]
        )

        missing_critical = []
        missing_important = []

        for field in reqs.get("critical", []):
            if not self._has_data_for(field, understanding, child):
                missing_critical.append(_make_gap(field, GapPriority.CRITICAL))

        for field in reqs.get("important", []):
            if not self._has_data_for(field, understanding, child):
                missing_important.append(_make_gap(field, GapPriority.IMPORTANT))

        # Determine status
        if missing_critical:
            return LetterReadiness(
                status="partial",
                missing_critical=missing_critical,
                missing_important=missing_important,
                can_generate=True,  # Can still generate, just incomplete
                guidance_message=self._build_guidance_message(missing_critical, is_critical=True),
            )
        elif missing_important:
            return LetterReadiness(
                status="ready",  # Ready but could be better
                missing_critical=[],
                missing_important=missing_important,
                can_generate=True,
                guidance_message=self._build_guidance_message(missing_important, is_critical=False),
            )
        else:
            return LetterReadiness(
                status="ready",
                missing_critical=[],
                missing_important=[],
                can_generate=True,
                guidance_message=None,
            )

    def _has_data_for(
        self,
        field: str,
        understanding: "Understanding",
        child: Optional["Child"],
    ) -> bool:
        """
        Check if we have data for a specific field.

        DOMAIN-BASED ONLY - no string matching!
        The LLM extracts observations with domains, we just check domains.
        """
        # Special handling for child_age - check identity structure or Darshan birth_date
        if field == "child_age":
            if child and child.identity and child.identity.birth_date:
                return True
            # Also check birth_date passed from Darshan
            if getattr(self, '_child_birth_date', None):
                return True
            return False

        vocab = CLINICAL_VOCABULARY.get(field, {})
        domains_to_check = vocab.get("domains_to_check", [])

        # For milestone-related fields, skip observation check - handle in milestone section below
        # Motor/language OBSERVATIONS are not the same as developmental MILESTONES
        if field not in ["milestones", "language_milestones", "motor_milestones"]:
            # Check observations by domain
            for domain in domains_to_check:
                domain_observations = [f for f in understanding.observations
                              if getattr(f, 'domain', None) == domain]
                if domain_observations:
                    return True

        # Check structured milestones (for milestone-related fields)
        if field in ["milestones", "language_milestones", "motor_milestones", "regression"]:
            if hasattr(understanding, 'milestones') and understanding.milestones:
                if field == "language_milestones":
                    # Check for language-domain milestones
                    lang_ms = [m for m in understanding.milestones
                              if m.domain == "language"]
                    if lang_ms:
                        return True
                elif field == "motor_milestones":
                    # Check for motor-domain milestones
                    motor_ms = [m for m in understanding.milestones
                               if m.domain == "motor"]
                    if motor_ms:
                        return True
                elif field == "regression":
                    # Check for regression-type milestones OR regression domain observations
                    regressions = [m for m in understanding.milestones
                                  if getattr(m, 'milestone_type', None) == "regression"]
                    if regressions:
                        return True
                    # Also check observations with regression domain (including "no regression" reports)
                    regression_obs = [o for o in understanding.observations
                                     if getattr(o, 'domain', None) == "regression"]
                    if regression_obs:
                        return True
                else:
                    # General milestones - need DEVELOPMENTAL milestones (motor, language, etc.)
                    # NOT birth_history - those are tracked separately
                    developmental_ms = [m for m in understanding.milestones
                                       if getattr(m, 'domain', None) in ['motor', 'language', 'cognitive', 'social', 'adaptive']
                                       or (getattr(m, 'milestone_type', None) == 'achievement'
                                           and getattr(m, 'domain', None) not in ['birth_history', 'medical'])]
                    if developmental_ms:
                        return True

        # Check milestones for birth history
        if field == "birth_history":
            if hasattr(understanding, 'milestones') and understanding.milestones:
                # Check for birth-type milestones or birth_history domain
                birth_milestones = [m for m in understanding.milestones
                                   if getattr(m, 'milestone_type', None) == 'birth'
                                   or getattr(m, 'domain', None) in ['birth_history', 'medical']]
                if birth_milestones:
                    return True

        # Check child history structure (for birth history)
        if child and field == "birth_history":
            if child.history and child.history.birth:
                # Has birth history if any birth field is populated
                birth = child.history.birth
                if (birth.complications or
                    birth.premature is not None or
                    birth.weeks_gestation or
                    birth.early_medical):
                    return True

        # Check child family structure (for family history)
        if child and field == "family_developmental_history":
            if child.family and child.family.family_developmental_history:
                return True

        return False

    def _build_guidance_message(self, missing: List[ClinicalGap], is_critical: bool = True) -> str:
        """
        Build Hebrew message for UI about what's missing.

        IMPORTANT: Uses parent_description (everyday language), not clinical_term!
        """
        # Use parent-friendly descriptions
        items = [g.parent_description for g in missing[:3]]
        if len(missing) > 3:
            items.append(f"ועוד {len(missing) - 3} פרטים")

        if is_critical:
            return f"כדי שהסיכום יהיה שימושי יותר, היה עוזר לדעת על: {', '.join(items)}"
        else:
            return f"הסיכום יהיה עשיר יותר אם נדע גם על: {', '.join(items)}"

    def get_collection_context(
        self,
        recipient_type: str,
        missing_gaps: List,
    ) -> str:
        """
        Build context for LLM when parent is collecting missing info.

        This is injected into the response prompt when parent chose
        "Add in conversation" from the Share tab.

        Args:
            recipient_type: Type of professional (e.g., "neurologist")
            missing_gaps: Can be List[ClinicalGap] objects or List[dict] with
                         keys: field, description, question
        """
        # Handle both ClinicalGap objects and dicts (from session_flags)
        gap_descriptions_list = []
        for g in missing_gaps[:3]:
            if isinstance(g, dict):
                desc = g.get("description", g.get("parent_description", ""))
                question = g.get("question", g.get("parent_question", ""))
            else:
                desc = g.parent_description
                question = g.parent_question
            gap_descriptions_list.append(f"- {desc}: {question}")

        gap_descriptions = "\n".join(gap_descriptions_list)

        recipient_hebrew = {
            "neurologist": "נוירולוג",
            "speech_therapist": "קלינאית תקשורת",
            "ot": "מרפאה בעיסוק",
            "pediatrician": "רופא ילדים",
        }.get(recipient_type, "איש מקצוע")

        return f"""
## CONTEXT: PREPARING A SUMMARY

Parent is preparing a summary for a {recipient_hebrew}.
This info would make it more useful:
{gap_descriptions}

**CRITICAL CONVERSATION RULES:**
1. DO NOT parrot back what the parent said ("שמתי לב שאמרת...")
2. DO NOT follow a checklist or ask rapid-fire questions
3. ONE question at a time - let the conversation breathe
4. Respond to emotion first, practical info second
5. Be genuinely curious, not checking boxes

**CRITICAL - RECORD ALL ANSWERS (including negative ones):**
- When parent says "no" or "there wasn't" - STILL call notice() to record this!
- Example: Asked about regression, parent says "לא" → notice("אין נסיגה התפתחותית מדווחת", domain="regression")
- Example: Asked about sleep issues, parent says "ישן טוב" → notice("ההורה מדווח שהשינה תקינה", domain="sleep")
- Negative findings are just as important as positive ones for professionals!

**NATURAL FLOW:**
- If they mention something, acknowledge briefly ("הבנתי") then explore naturally
- Wait for them to share - don't push for the next item immediately
- Only move to new topic when current one feels complete
- If they gave key info, a simple "תודה" is enough - no need to label it as "חשוב"

**IMPORTANT - THIS OVERRIDES NORMAL PRINCIPLES:**
- You ARE following a specific agenda during this mode
- The items listed above are CURRENTLY still missing
- After acknowledging what the parent shared, ASK about the NEXT missing item
- Do NOT say "we're done" or "we covered everything" until this list is EMPTY
- The system will tell you separately when all items are collected
"""

    def format_gaps_for_letter(
        self,
        missing_gaps: List[ClinicalGap],
    ) -> str:
        """
        Format missing gaps for inclusion in Letter.

        Uses clinical_term for professional audience!
        """
        if not missing_gaps:
            return ""

        clinical_terms = [g.clinical_term for g in missing_gaps]
        return f"לא ידוע לנו עדיין: {', '.join(clinical_terms)}"
