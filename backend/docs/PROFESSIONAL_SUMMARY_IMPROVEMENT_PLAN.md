# Professional Summary Improvement Plan

## Executive Summary

This plan addresses the gap between what clinical professionals need in summaries and what Chitta currently collects and generates. It provides a **complete end-to-end flow** from data collection through conversation, to gap detection, user guidance, and summary generation.

---

## Part 1: The Problem

### What Professionals Need vs. What We Provide

When generating professional summaries for medical professionals (neurologist, OT, speech therapist), the output is:
- Missing critical medical information (birth history, milestones, family history)
- Using parent-focused language instead of clinically precise terminology
- Asking naive questions that real clinicians wouldn't find useful
- Missing social communication markers (eye contact, joint attention, play patterns)

**Example feedback from neurologist perspective:**
> "Where is the pregnancy and birth history? What about developmental milestones - when did walking and first words occur? Any family history of developmental differences? The language feels too parent-focused. I need facts I can chart, not feelings."

### Current Dead Ends

```
Dead End #1: Summary shows gaps but no action path
================================================
Parent clicks "Get Guidelines" → Summary includes open_questions
    → Parent sees "מה עוד לא ידוע לנו" → No action button → Dead end

Dead End #2: Gaps don't influence conversation
==============================================
CuriosityEngine.get_gaps() returns gaps → Passed to synthesis prompt
    → Becomes open_questions in output → NOT shown during conversation → Dead end

Dead End #3: Clinical gaps are invisible
========================================
"birth_history" is not a domain → Not tracked by curiosity system
    → LLM never knows to ask about it → Critical data never collected → Dead end
```

---

## Part 2: Root Cause Analysis

### 2.1 Data Collection Gap

**Current domains** (tools.py:45):
```
motor, social, emotional, cognitive, language, sensory, regulation,
essence, strengths, context, concerns, general
```

**Missing domains for clinical completeness:**
- `birth_history` - pregnancy, birth complications, prematurity
- `milestones` - walking age, first words, toilet training
- `medical` - diagnoses, evaluations, medications
- `sleep` - patterns, difficulties
- `feeding` - patterns, sensitivities
- `play` - imaginative, parallel, social play patterns

### 2.2 No Structured Milestone Collection

The `DevelopmentalMilestone` model exists as a **skeleton** (models.py:23-88) but is NOT implemented:
- No tool to extract milestones
- No guidance for LLM to capture milestone ages
- No display in ChildSpace

### 2.3 Curiosity System Doesn't Track Clinical Domains

The 5 perpetual curiosities (curiosity.py:126-163) are:
1. "מי הילד הזה?" (essence)
2. "מה הוא אוהב?" (strengths)
3. "מה ההקשר שלו?" (context)
4. "מה הביא אותם לכאן?" (concerns)
5. "אילו דפוסים מתגלים?" (pattern)

**Missing:**
- "מה היה קודם?" (birth/early history)
- "איך התפתח?" (milestones)
- "מה קורה בשינה ובאוכל?" (sleep/feeding)

### 2.4 Two Disconnected Systems

```
┌─────────────────────────┐         ┌─────────────────────────┐
│   CuriosityEngine       │         │   Turn Guidance         │
│                         │         │                         │
│  - Tracks what we're    │   ❌    │  - Tells LLM how to     │
│    curious about        │ ──────► │    respond              │
│  - Has activation/      │   NO    │  - Based on what was    │
│    certainty            │  LINK   │    just extracted       │
│  - get_gaps() exists    │         │  - Doesn't see gaps     │
└─────────────────────────┘         └─────────────────────────┘
```

### 2.5 Synthesis Doesn't Receive Full Context

The crystallization prompt (synthesis.py:824-1054) receives:
- Facts, Stories, Active explorations
- Strengths, Interests, Concerns

**NOT received:**
- `child.history.birth` (BirthHistory structure)
- `child.history.previous_evaluations`
- `child.family` (FamilyContext)
- Structured milestones

---

## Part 3: The Solution - End-to-End Flow

### Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA FLOW                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Conversation ──→ Extraction ──→ Understanding ──→ CuriosityEngine          │
│       │                              │                    │                  │
│       │                              │                    ▼                  │
│       │                              │         ┌──────────────────────┐     │
│       │                              │         │ ClinicalGapDetector  │     │
│       │                              │         │ - Checks all domains │     │
│       │                              │         │ - Returns priorities │     │
│       │                              │         └──────────┬───────────┘     │
│       │                              │                    │                  │
│       ▼                              ▼                    ▼                  │
│  ┌─────────┐                  ┌───────────┐        ┌───────────────┐        │
│  │Response │◄─────────────────│Turn Guide │◄───────│ Gap Context   │        │
│  │  Phase  │                  │           │        │ (for LLM)     │        │
│  └─────────┘                  └───────────┘        └───────────────┘        │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                              UI FLOW                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ChildSpace ──→ Share Tab ──→ Select Recipient ──→ Readiness Check          │
│                                                          │                   │
│                                        ┌─────────────────┼─────────────┐    │
│                                        │                 │             │    │
│                                        ▼                 ▼             ▼    │
│                                   [READY]           [PARTIAL]    [NOT_READY]│
│                                      │                 │             │      │
│                                      ▼                 ▼             ▼      │
│                                 Generate          Show Warning   Block +    │
│                                 Summary           + Options      Explain    │
│                                                       │                     │
│                                        ┌──────────────┴───────────┐         │
│                                        │                          │         │
│                                        ▼                          ▼         │
│                              [Create Anyway]           [Add in Chat]        │
│                                     │                        │              │
│                                     ▼                        ▼              │
│                            Summary with            Guided Collection        │
│                            "Unknown" sections      Mode                     │
│                                     │                        │              │
│                                     │                        ▼              │
│                                     │              Info collected →         │
│                                     │              Return to Share          │
│                                     │                        │              │
│                                     └────────────────────────┘              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Phase-by-Phase Flow

#### Phase 1: Detection (During Conversation)

```
Parent message → Extraction Phase (LLM + tools)
    ↓
System updates Understanding with new facts
    ↓
ClinicalGapDetector.check() runs
    - Checks for: birth history, milestones, family history, social markers, sleep
    - Returns: List[ClinicalGap] with priority (critical/important/nice_to_have)
    ↓
IF clinical gaps exist:
    - Create/boost perpetual curiosity for that domain
    - Set higher activation (0.8+) for critical gaps
    - Add to conversation context for response LLM
```

#### Phase 2: Guidance (During Response Generation)

```
Extraction complete → Build response context
    ↓
Get active curiosities (including clinical ones)
    ↓
Add to response prompt:
    - Top 5 curiosities with activation levels
    - If critical gaps AND natural opportunity: soft guidance
    ↓
LLM generates response (may naturally ask about history)
```

#### Phase 3: Summary Generation (When Requested)

```
Parent clicks Share → Selects "Neurologist"
    ↓
ClinicalGapDetector.check_readiness("neurologist") runs
    - For MEDICAL: check birth_history, milestones, family_history
    - Returns: READY | PARTIAL | NOT_READY
    ↓
IF PARTIAL:
    UI shows soft warning + two options:
    - [צור סיכום עם מה שיש] - Create with gaps
    - [הוסף פרטים בשיחה] - Open guided collection
```

#### Phase 4: Guided Collection Mode

```
Parent chooses "Add in Chat" → Chat opens with special context
    ↓
Session flag set: preparing_summary_for = "neurologist"
    ↓
Direct injection to response prompt:
    "Parent is preparing summary for neurologist.
     Critical missing: birth history, milestones.
     Goal: Collect naturally. Don't interrogate."
    ↓
LLM: "אני רואה שאת מכינה סיכום לנוירולוג.
     כדי שיהיה שימושי יותר, זה יעזור לדעת קצת על ההתחלה..."
    ↓
Parent shares → LLM extracts (notice with birth_history domain)
    ↓
Gap filled → Curiosity satisfied → LLM guides back to Share tab
```

#### Phase 5: Summary with Explicit Unknowns

```
IF parent chose "Create Anyway" AND gaps exist:
    ↓
Summary includes explicit "Unknown" sections:

    📋 מה לא ידוע לנו עדיין:
    • היסטוריית לידה והריון - לא שותף
    • גיל מילים ראשונות - לא ידוע

    [הוסף פרטים חסרים] ← Opens guided collection
```

---

## Part 4: Implementation Plan

### Phase 1: Expand Data Collection (Foundation)

#### 1.1 Add Clinical Domains to tools.py

```python
# In TOOL_NOTICE "domain" enum, add:
"sleep", "feeding", "play", "birth_history", "milestones", "medical"
```

**File:** `backend/app/chitta/tools.py`

#### 1.2 Implement DevelopmentalMilestone Tool

Create new tool `record_milestone` in tools.py:

```python
TOOL_RECORD_MILESTONE = {
    "name": "record_milestone",
    "description": """Record a developmental milestone with age.

Use when parent mentions WHEN something happened:
- "He started walking at 14 months"
- "First words around age 1"
- "Toilet trained at 3"
- "Started therapy at 2.5"

Also record regressions:
- "Lost words at 18 months"
- "Stopped playing with other kids around age 2"
""",
    "parameters": {
        "type": "object",
        "properties": {
            "description": {
                "type": "string",
                "description": "What happened"
            },
            "age_months": {
                "type": "number",
                "description": "Age in months when it happened (if known)"
            },
            "age_description": {
                "type": "string",
                "description": "Age in words if months unknown: 'בגיל שנה', 'בערך בגיל שנתיים'"
            },
            "domain": {
                "type": "string",
                "enum": ["motor", "language", "social", "cognitive", "regulation"]
            },
            "milestone_type": {
                "type": "string",
                "enum": ["achievement", "concern", "regression", "intervention"],
                "description": "achievement=positive, concern=worry, regression=lost skill, intervention=therapy started"
            }
        },
        "required": ["description", "domain"]
    }
}
```

**File:** `backend/app/chitta/tools.py`

#### 1.3 Add Milestones to Understanding Model

```python
# In Understanding class (models.py)
developmental_milestones: List[DevelopmentalMilestone] = field(default_factory=list)
```

**File:** `backend/app/chitta/models.py`

#### 1.4 Handle record_milestone in Gestalt

```python
# In gestalt.py _apply_tool_call()
elif tool_name == "record_milestone":
    milestone = DevelopmentalMilestone.create(
        description=args.get("description"),
        domain=args.get("domain"),
        milestone_type=args.get("milestone_type", "observation"),
        age_months=args.get("age_months"),
        age_description=args.get("age_description"),
    )
    self._understanding.developmental_milestones.append(milestone)
```

**File:** `backend/app/chitta/gestalt.py`

---

### Phase 2: Add Clinical Perpetual Curiosities

#### 2.1 Add to PERPETUAL_TEMPLATES

```python
# In curiosity.py PERPETUAL_TEMPLATES, add:
{
    "focus": "מה היה קודם?",
    "type": "discovery",
    "activation": 0.5,
    "certainty": 0.1,
    "domain": "birth_history",
},
{
    "focus": "איך התפתח עד עכשיו?",
    "type": "discovery",
    "activation": 0.4,
    "certainty": 0.1,
    "domain": "milestones",
},
{
    "focus": "מה קורה בשינה ובאוכל?",
    "type": "question",
    "activation": 0.3,
    "certainty": 0.1,
    "question": "איך נראים השינה והאכילה?",
    "domain": "sleep",
},
```

**File:** `backend/app/chitta/curiosity.py`

#### 2.2 Update Domain Gap Counting

```python
# In curiosity.py _count_domain_gaps()
# Add support for new domains:
if domain in ["birth_history", "milestones", "sleep", "feeding", "play", "medical"]:
    domain_facts = [f for f in understanding.facts if getattr(f, 'domain', None) == domain]
    # These domains start with more gaps (critical info)
    if len(domain_facts) == 0:
        return 5  # High gap count when empty
```

**File:** `backend/app/chitta/curiosity.py`

---

### Phase 3: Create ClinicalGapDetector

#### 3.1 New Module: clinical_gaps.py

```python
"""
Clinical Gap Detection

Detects missing clinical data that professionals need for useful summaries.
Different recipient types have different requirements.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, TYPE_CHECKING
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
    """A piece of missing clinical information."""
    field: str                    # "birth_history", "milestones", etc.
    priority: GapPriority
    hebrew_description: str       # For UI display
    collection_prompt: str        # Hint for LLM on how to ask


@dataclass
class SummaryReadiness:
    """Assessment of readiness to generate summary for a recipient type."""
    status: str                   # "ready" | "partial" | "not_ready"
    missing_critical: List[ClinicalGap]
    missing_important: List[ClinicalGap]
    can_generate: bool            # True even if partial
    guidance_message: Optional[str]  # Hebrew message for UI


class ClinicalGapDetector:
    """
    Detects missing clinical data based on recipient type.

    Different professionals need different data:
    - Neurologist: birth history, milestones, family history
    - Speech therapist: language milestones, social markers
    - OT: sensory patterns, motor milestones
    """

    REQUIREMENTS_BY_RECIPIENT = {
        "neurologist": {
            "critical": [
                ClinicalGap(
                    field="birth_history",
                    priority=GapPriority.CRITICAL,
                    hebrew_description="היסטוריית לידה והריון",
                    collection_prompt="Ask about pregnancy and birth - any complications?"
                ),
                ClinicalGap(
                    field="milestones",
                    priority=GapPriority.CRITICAL,
                    hebrew_description="אבני דרך התפתחותיות (הליכה, דיבור)",
                    collection_prompt="When did walking and first words happen?"
                ),
            ],
            "important": [
                ClinicalGap(
                    field="family_developmental_history",
                    priority=GapPriority.IMPORTANT,
                    hebrew_description="היסטוריה התפתחותית במשפחה",
                    collection_prompt="Any family members with similar patterns?"
                ),
                ClinicalGap(
                    field="sleep",
                    priority=GapPriority.IMPORTANT,
                    hebrew_description="דפוסי שינה",
                    collection_prompt="How is sleep? Any difficulties?"
                ),
            ],
            "nice_to_have": [
                ClinicalGap(
                    field="social_markers",
                    priority=GapPriority.NICE_TO_HAVE,
                    hebrew_description="קשר עין ותשומת לב משותפת",
                    collection_prompt="Eye contact and joint attention patterns?"
                ),
            ],
        },
        "speech_therapist": {
            "critical": [
                ClinicalGap(
                    field="language_milestones",
                    priority=GapPriority.CRITICAL,
                    hebrew_description="אבני דרך בשפה (מילים ראשונות, משפטים)",
                    collection_prompt="When did first words happen? Sentences?"
                ),
            ],
            "important": [
                ClinicalGap(
                    field="social_communication",
                    priority=GapPriority.IMPORTANT,
                    hebrew_description="תקשורת חברתית (קשר עין, הצבעה)",
                    collection_prompt="Eye contact? Pointing to share interest?"
                ),
                ClinicalGap(
                    field="play_patterns",
                    priority=GapPriority.IMPORTANT,
                    hebrew_description="דפוסי משחק (דמיון, עם ילדים אחרים)",
                    collection_prompt="How do they play? Imaginative play?"
                ),
            ],
        },
        "ot": {
            "critical": [
                ClinicalGap(
                    field="sensory_patterns",
                    priority=GapPriority.CRITICAL,
                    hebrew_description="דפוסים חושיים",
                    collection_prompt="Sensory sensitivities or seeking behaviors?"
                ),
                ClinicalGap(
                    field="motor_milestones",
                    priority=GapPriority.CRITICAL,
                    hebrew_description="אבני דרך מוטוריות",
                    collection_prompt="When did they sit, crawl, walk?"
                ),
            ],
            "important": [
                ClinicalGap(
                    field="self_care",
                    priority=GapPriority.IMPORTANT,
                    hebrew_description="עצמאות (אכילה, לבוש)",
                    collection_prompt="How independent with eating, dressing?"
                ),
            ],
        },
        # Default for general sharing
        "default": {
            "critical": [],
            "important": [],
            "nice_to_have": [],
        },
    }

    def check_readiness(
        self,
        recipient_type: str,
        understanding: "Understanding",
        child: Optional["Child"] = None,
    ) -> SummaryReadiness:
        """
        Check if we have enough data to generate a useful summary.

        Returns readiness status with details about what's missing.
        """
        reqs = self.REQUIREMENTS_BY_RECIPIENT.get(
            recipient_type,
            self.REQUIREMENTS_BY_RECIPIENT["default"]
        )

        missing_critical = []
        missing_important = []

        for gap in reqs.get("critical", []):
            if not self._has_data_for(gap.field, understanding, child):
                missing_critical.append(gap)

        for gap in reqs.get("important", []):
            if not self._has_data_for(gap.field, understanding, child):
                missing_important.append(gap)

        # Determine status
        if missing_critical:
            return SummaryReadiness(
                status="partial",
                missing_critical=missing_critical,
                missing_important=missing_important,
                can_generate=True,  # Can still generate, just incomplete
                guidance_message=self._build_guidance_message(missing_critical),
            )
        elif missing_important:
            return SummaryReadiness(
                status="ready",  # Ready but could be better
                missing_critical=[],
                missing_important=missing_important,
                can_generate=True,
                guidance_message=None,
            )
        else:
            return SummaryReadiness(
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
        """Check if we have data for a specific field."""

        # Check facts by domain
        if field in ["birth_history", "milestones", "sleep", "feeding",
                     "play", "medical", "sensory_patterns", "motor_milestones",
                     "language_milestones"]:
            domain_map = {
                "birth_history": "birth_history",
                "milestones": "milestones",
                "language_milestones": "milestones",
                "motor_milestones": "milestones",
                "sleep": "sleep",
                "feeding": "feeding",
                "play": "play",
                "medical": "medical",
                "sensory_patterns": "sensory",
            }
            target_domain = domain_map.get(field, field)
            domain_facts = [f for f in understanding.facts
                          if getattr(f, 'domain', None) == target_domain]
            if domain_facts:
                return True

        # Check structured milestones
        if field in ["milestones", "language_milestones", "motor_milestones"]:
            if hasattr(understanding, 'developmental_milestones'):
                if understanding.developmental_milestones:
                    return True

        # Check child history
        if child and field == "birth_history":
            if child.history and child.history.birth:
                if child.history.birth.complications or child.history.birth.premature:
                    return True

        if child and field == "family_developmental_history":
            if child.family and child.family.family_developmental_history:
                return True

        # Check for keywords in facts
        keyword_map = {
            "birth_history": ["לידה", "הריון", "פג", "שבוע"],
            "social_markers": ["קשר עין", "הצבעה", "תשומת לב משותפת"],
            "social_communication": ["קשר עין", "הצבעה", "מביט"],
            "play_patterns": ["משחק", "משחק דמיון", "משחק עם ילדים"],
            "self_care": ["אוכל לבד", "מתלבש", "עצמאי"],
        }

        if field in keyword_map:
            keywords = keyword_map[field]
            for fact in understanding.facts:
                content = fact.content.lower() if hasattr(fact, 'content') else ""
                if any(kw in content for kw in keywords):
                    return True

        return False

    def _build_guidance_message(self, missing: List[ClinicalGap]) -> str:
        """Build Hebrew message for UI about what's missing."""
        items = [g.hebrew_description for g in missing[:3]]
        if len(missing) > 3:
            items.append(f"ועוד {len(missing) - 3} פרטים")

        return f"כדי שהסיכום יהיה שימושי יותר, היה עוזר לדעת על: {', '.join(items)}"

    def get_collection_context(
        self,
        recipient_type: str,
        missing_gaps: List[ClinicalGap],
    ) -> str:
        """
        Build context for LLM when parent is collecting missing info.

        This is injected into the response prompt when parent chose
        "Add in conversation" from the Share tab.
        """
        gap_descriptions = "\n".join([
            f"- {g.hebrew_description}: {g.collection_prompt}"
            for g in missing_gaps[:3]
        ])

        recipient_hebrew = {
            "neurologist": "נוירולוג",
            "speech_therapist": "קלינאית תקשורת",
            "ot": "מרפאה בעיסוק",
            "pediatrician": "רופא ילדים",
        }.get(recipient_type, "איש מקצוע")

        return f"""
## GUIDED COLLECTION MODE

The parent is preparing a summary for a {recipient_hebrew}.
They chose to add missing information before generating the summary.

**What would make the summary more useful:**
{gap_descriptions}

**Your goal:**
- Collect this information naturally through conversation
- Don't make it feel like an interrogation or intake form
- Explain WHY this helps: "כדי שהסיכום יהיה שימושי ל{recipient_hebrew}..."
- When you have the info, let them know they can return to Share tab

**Example opening:**
"אני רואה שאת מכינה סיכום ל{recipient_hebrew}.
כדי שיהיה שימושי יותר, זה יעזור לי לדעת קצת על ההתחלה -
איך הייתה הלידה וההתפתחות המוקדמת?"

**After collecting:**
"תודה! עכשיו הסיכום יהיה הרבה יותר מועיל.
תוכלי לחזור ללשונית השיתוף ליצור אותו."
"""
```

**File:** `backend/app/chitta/clinical_gaps.py` (NEW)

---

### Phase 4: Connect Gaps to Conversation

#### 4.1 Pass Active Curiosities to Response Prompt

```python
# In gestalt.py _build_response_prompt()

# Get top curiosities including clinical ones
active_curiosities = self._curiosity_engine.get_top(5, self._understanding)
curiosities_context = format_curiosities(active_curiosities)

# Build prompt with curiosity context
prompt = f"""
{identity_section}

## WHAT WE'RE CURIOUS ABOUT (background context)
{curiosities_context}

## TURN GUIDANCE
{turn_guidance}

...
"""
```

**File:** `backend/app/chitta/gestalt.py`

#### 4.2 Add Guided Collection Mode

```python
# In gestalt.py _respond() method

# Check if in guided collection mode
preparing_for = self._session.get("preparing_summary_for")

clinical_context = ""
if preparing_for:
    detector = ClinicalGapDetector()
    readiness = detector.check_readiness(
        preparing_for, self._understanding, self._child
    )
    if readiness.missing_critical:
        clinical_context = detector.get_collection_context(
            preparing_for, readiness.missing_critical
        )

# Include in prompt
prompt = self._build_response_prompt(
    extraction_result=extraction,
    clinical_context=clinical_context,
)
```

**File:** `backend/app/chitta/gestalt.py`

---

### Phase 5: Update Synthesis with Full Context

#### 5.1 Pass Child History to Crystallization

```python
# In synthesis.py _build_crystallization_prompt()

# Format child history if available
history_text = self._format_child_history(child) if child else "לא סופקה היסטוריה"
family_text = self._format_family_context(child) if child else "לא סופק הקשר משפחתי"
milestones_text = self._format_milestones(understanding)

# Add to prompt
prompt = f"""
...

### Birth & Medical History
{history_text}

### Family Context
{family_text}

### Developmental Milestones
{milestones_text}

...
"""
```

**Helper functions:**

```python
def _format_child_history(self, child: Child) -> str:
    """Format birth and medical history for prompt."""
    parts = []
    if child.history and child.history.birth:
        b = child.history.birth
        if b.premature:
            parts.append(f"נולד בשבוע {b.weeks_gestation or '?'}")
        if b.complications:
            parts.append(f"סיבוכים בלידה: {b.complications}")
        if b.early_medical:
            parts.append(f"בעיות רפואיות מוקדמות: {b.early_medical}")

    if child.history and child.history.previous_evaluations:
        for ev in child.history.previous_evaluations:
            parts.append(f"הערכה ({ev.evaluator_type}): {ev.findings}")

    if child.history and child.history.previous_diagnoses:
        parts.append(f"אבחנות: {', '.join(child.history.previous_diagnoses)}")

    return '\n'.join(parts) if parts else "לא סופקה היסטוריה רפואית"

def _format_milestones(self, understanding: Understanding) -> str:
    """Format developmental milestones for prompt."""
    if not hasattr(understanding, 'developmental_milestones'):
        return "לא תועדו אבני דרך"

    if not understanding.developmental_milestones:
        return "לא תועדו אבני דרך"

    sorted_ms = sorted(
        understanding.developmental_milestones,
        key=lambda m: m.age_months or 999
    )

    lines = []
    for m in sorted_ms:
        age = f"{m.age_months} חודשים" if m.age_months else m.age_description
        lines.append(f"- {m.description} ({age})")

    return '\n'.join(lines)
```

**File:** `backend/app/chitta/synthesis.py`

#### 5.2 Enhance Medical Professional Summary Prompt

```python
# In synthesis.py, update professional_summaries guidance

"""
**For MEDICAL recipient (neurologist, developmental pediatrician):**

role_specific_section should include:

1. **Timeline** (if available):
   - Birth: "נולד בשבוע X" or "לידה תקינה" or "לא ידוע"
   - Milestones: "מילים ראשונות בגיל X, הליכה בגיל X"
   - Regressions: Any skills lost and when

2. **Observable markers**:
   - Eye contact quality
   - Joint attention
   - Play patterns (imaginative? with peers?)

3. **Sensory/motor patterns**:
   - What triggers reactions
   - How they respond
   - What helps

4. **Family history** (if shared):
   - Similar patterns in family members

**Format for medical:**
"נולד בשבוע X. אבני דרך: מילים ב-X חודשים, הליכה ב-X חודשים.
קשר עין: [תיאור]. תשומת לב משותפת: [תיאור]. משחק: [תיאור].
דפוסים חושיים: [תיאור]. היסטוריה משפחתית: [אם רלוונטי]."

**If information is missing, explicitly note:**
"לא ידוע לנו עדיין: היסטוריית לידה, גיל מילים ראשונות"
"""
```

**File:** `backend/app/chitta/synthesis.py`

---

### Phase 6: UI Updates for Gap-Aware Sharing

#### 6.1 Update ShareView Data Structure

```python
# In service.py _derive_share_options()

def _derive_share_options(self, gestalt: LivingGestalt) -> ShareView:
    """Derive the Share tab options with readiness per recipient."""

    detector = ClinicalGapDetector()

    # Check readiness for each recipient type
    readiness_by_type = {}
    for recipient_type in ["neurologist", "speech_therapist", "ot", "pediatrician"]:
        readiness = detector.check_readiness(
            recipient_type,
            gestalt.understanding,
            self._child,
        )
        readiness_by_type[recipient_type] = {
            "status": readiness.status,
            "missing_critical": [g.hebrew_description for g in readiness.missing_critical],
            "missing_important": [g.hebrew_description for g in readiness.missing_important],
            "can_generate": readiness.can_generate,
            "guidance_message": readiness.guidance_message,
        }

    return ShareView(
        recipient_types=get_recipient_types(),
        previous_summaries=[],
        can_generate=True,
        not_ready_reason=None,
        readiness_by_type=readiness_by_type,  # NEW
    )
```

**File:** `backend/app/chitta/service.py`

#### 6.2 Add API Endpoint for Starting Guided Collection

```python
# In routes.py

@router.post("/family/{family_id}/start-guided-collection")
async def start_guided_collection(
    family_id: str,
    recipient_type: str,
):
    """
    Start guided collection mode for preparing a summary.

    Sets session flag that triggers special prompting in chat.
    """
    session = await get_session(family_id)
    session["preparing_summary_for"] = recipient_type
    await save_session(family_id, session)

    return {"status": "ok", "mode": "guided_collection"}


@router.post("/family/{family_id}/end-guided-collection")
async def end_guided_collection(family_id: str):
    """End guided collection mode."""
    session = await get_session(family_id)
    session.pop("preparing_summary_for", None)
    await save_session(family_id, session)

    return {"status": "ok"}
```

**File:** `backend/app/api/routes.py`

---

## Part 5: Files Summary

| File | Changes |
|------|---------|
| `backend/app/chitta/tools.py` | Add domains (sleep, feeding, play, birth_history, milestones, medical) + record_milestone tool |
| `backend/app/chitta/models.py` | Add developmental_milestones to Understanding |
| `backend/app/chitta/curiosity.py` | Add 3 clinical perpetual curiosities, update gap counting |
| `backend/app/chitta/clinical_gaps.py` | NEW - ClinicalGapDetector class |
| `backend/app/chitta/gestalt.py` | Handle record_milestone, add guided collection mode, pass curiosities to prompt |
| `backend/app/chitta/formatting.py` | (Already has format_curiosities, may need updates) |
| `backend/app/chitta/synthesis.py` | Pass full history, enhance medical prompt, format milestones |
| `backend/app/chitta/service.py` | Update _derive_share_options with readiness |
| `backend/app/api/routes.py` | Add guided collection endpoints |

---

## Part 6: Implementation Order

| Step | What | Impact | Effort |
|------|------|--------|--------|
| 1 | Add domains to tools.py | Foundation | Low |
| 2 | Add clinical perpetual curiosities | Gaps visible to curiosity system | Low |
| 3 | Create ClinicalGapDetector | Core gap detection logic | Medium |
| 4 | Implement record_milestone tool | Structured milestone collection | Medium |
| 5 | Pass history to synthesis | Full context for LLM | Low |
| 6 | Add guided collection mode | Parent action path | Medium |
| 7 | Update Share UI with readiness | User sees gaps | Medium |
| 8 | Enhance medical summary prompt | Better output | Low |

**Recommended order:** 1 → 2 → 3 → 5 → 8 → 4 → 6 → 7

---

## Part 7: Success Criteria

After implementation, test with this scenario:

1. Create new child, have conversation WITHOUT mentioning birth/milestones
2. Go to Share → Neurologist
3. **Expected:** UI shows "הסיכום כמעט מוכן" with missing items listed
4. Click "הוסף פרטים בשיחה"
5. **Expected:** Chat opens, LLM asks about birth/milestones naturally
6. Provide info, return to Share
7. **Expected:** Readiness now shows "ready"
8. Generate summary
9. **Expected:** Summary includes timeline with milestones

**Summary quality check:**
- Contains birth history (or explicit "לא ידוע")
- Contains milestone ages
- Contains social markers
- Uses clinical precision for medical recipient
- Explicitly notes what's still unknown

---

## Philosophy Note

This plan maintains Chitta's core values:

- **Curiosity over checklists** - We add perpetual curiosities, not mandatory fields
- **Natural conversation** - LLM extracts opportunistically, doesn't interrogate
- **פשוט (simplicity)** - Minimum NECESSARY complexity for clinical utility
- **Parent agency** - Parent chooses whether to add info or generate with gaps

The changes add a **safety net** for clinical completeness without turning the conversation into an intake form. Parents always have the choice to proceed with incomplete data - we just make the gaps visible and actionable.
