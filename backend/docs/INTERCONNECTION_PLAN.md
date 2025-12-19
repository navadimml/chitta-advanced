# Chitta Interconnection Plan: Making the Whole Greater Than the Sum

**Date**: December 2025
**Purpose**: Connect all parts of Chitta so they work together synergistically
**Principle**: מינימום המורכבות הנדרשת - minimum NECESSARY complexity

---

## Executive Summary

Chitta has excellent individual components working at ~55-60% of potential. The gap isn't missing features - it's **missing connections**. This plan creates the "neural pathways" that let data flow between components, making understanding truly evolve over time.

### The Vision

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         THE LIVING SYSTEM                                │
│                                                                          │
│   Parent         Parent         Conversation        Video                │
│   Journal  ───►  Message  ───►  Extraction    ◄───  Analysis            │
│      │              │               │                   │                │
│      │              │               │                   │                │
│      └──────────────┴───────┬───────┴───────────────────┘                │
│                             │                                            │
│                             ▼                                            │
│                    ┌─────────────────┐                                   │
│                    │  Understanding  │◄────── Temporal                   │
│                    │  (Facts, Stories,│        Anchoring                 │
│                    │   Milestones)   │                                   │
│                    └────────┬────────┘                                   │
│                             │                                            │
│              ┌──────────────┼──────────────┐                             │
│              │              │              │                             │
│              ▼              ▼              ▼                             │
│     ┌─────────────┐  ┌───────────┐  ┌──────────────┐                    │
│     │  Curiosity  │  │  Crystal  │  │  Clinical    │                    │
│     │   Engine    │◄─┤ Synthesis │──►   Gaps       │                    │
│     └──────┬──────┘  └─────┬─────┘  └──────┬───────┘                    │
│            │               │               │                             │
│            └───────────────┼───────────────┘                             │
│                            │                                             │
│                            ▼                                             │
│              ┌─────────────────────────┐                                 │
│              │      Turn Guidance      │                                 │
│              │  (Contextual Prompting) │                                 │
│              └────────────┬────────────┘                                 │
│                           │                                              │
│                           ▼                                              │
│              ┌─────────────────────────┐                                 │
│              │    LLM Response +       │                                 │
│              │  Professional Summaries │                                 │
│              └─────────────────────────┘                                 │
│                                                                          │
│              ┌─────────────────────────┐                                 │
│              │   Developmental         │                                 │
│              │   Timeline Display      │◄──── For Parents                │
│              └─────────────────────────┘                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Part 1: Current State Summary

### What's Working (Keep)

| Component | Status | Notes |
|-----------|--------|-------|
| Two-phase LLM architecture | 🟢 Solid | Don't touch |
| 8 perpetual curiosities | 🟢 Solid | Good foundation |
| Activation/certainty math | 🟢 Solid | Living system |
| Story extraction (capture_story) | 🟢 Solid | Stories are GOLD |
| Video analysis quality | 🟢 Solid | Gemini works well |
| Crystal synthesis | 🟢 Solid | Good holistic view |
| Clinical gap detection | 🟢 Solid | For summaries |

### What's Disconnected (Fix)

| Gap | Impact | Effort | Priority |
|-----|--------|--------|----------|
| Video → Curiosity Engine | High | Low | P1 |
| Parent Journal → Understanding | High | Medium | P2 |
| Temporal Anchoring | High | Medium | P3 |
| Story → Pattern Curiosity | Medium | Low | P4 |
| video_value → Scenario Framing | Medium | Low | P5 |
| Milestones → Timeline Display | High | Medium | P6 |
| Clinical Gaps → Turn Guidance | Medium | Low | P7 |
| Baseline Video Triggering | Low | Low | P8 |

---

## Part 2: Implementation Phases

### Phase 1: Connect Video Learnings (Week 1)

**Goal**: Video analysis results flow back into the living system

#### 1.1 Video Facts → Curiosity Engine

**File**: `backend/app/chitta/service.py`
**Location**: After video analysis (~line 1330)

```python
# CURRENT (disconnected):
for strength in analysis_result.get("strengths_observed", []):
    strength_fact = TemporalFact.from_observation(
        content=strength.get("strength", ""),
        domain="strengths",
        confidence=0.8,
    )
    gestalt.understanding.add_fact(strength_fact)
    # END - fact is orphaned from curiosity system

# NEW (connected):
for strength in analysis_result.get("strengths_observed", []):
    strength_fact = TemporalFact.from_observation(
        content=strength.get("strength", ""),
        domain="strengths",
        confidence=0.8,
    )
    gestalt.understanding.add_fact(strength_fact)
    # Connect to curiosity engine
    gestalt._curiosity_engine.on_fact_learned(strength_fact)

# Also capture general observations as facts
for observation in analysis_result.get("observations", []):
    if observation.get("domain"):
        obs_fact = TemporalFact.from_observation(
            content=observation.get("content", ""),
            domain=observation.get("domain", "general"),
            confidence=0.75,
        )
        gestalt.understanding.add_fact(obs_fact)
        gestalt._curiosity_engine.on_fact_learned(obs_fact)
```

#### 1.2 Video Questions → New Curiosities

**File**: `backend/app/chitta/service.py`
**Location**: After video analysis (~line 1348)

```python
# CURRENT (logged but lost):
new_questions = hypothesis_evidence.get("new_questions_raised", [])
for question in new_questions:
    logger.info(f"❓ New question from video: {question}")
    # END - question disappears into logs

# NEW (creates curiosities):
from .curiosity import create_question

new_questions = hypothesis_evidence.get("new_questions_raised", [])
for question in new_questions[:3]:  # Limit to top 3
    curiosity = create_question(
        focus=question,
        question=question,
        domain=cycle.focus_domain,  # Inherit from parent cycle
        activation=0.6,  # Start moderately active
    )
    gestalt._curiosity_engine.add_curiosity(curiosity)
    logger.info(f"🔮 New curiosity from video: {question}")
```

#### 1.3 Video Capacity → Understanding Essence

**File**: `backend/app/chitta/service.py`
**Location**: After video analysis (~line 1343)

```python
# CURRENT (logged but lost):
capacity = hypothesis_evidence.get("capacity_revealed", {})
if capacity.get("description"):
    logger.info(f"💪 Capacity revealed: {capacity.get('description')}")

# NEW (enriches essence):
capacity = hypothesis_evidence.get("capacity_revealed", {})
if capacity.get("description"):
    # Add as strength fact
    capacity_fact = TemporalFact.from_observation(
        content=f"כוח שנצפה: {capacity.get('description')}",
        domain="strengths",
        confidence=0.85,
    )
    gestalt.understanding.add_fact(capacity_fact)
    gestalt._curiosity_engine.on_fact_learned(capacity_fact)

    # If essence exists, add to core_qualities
    if gestalt.understanding.essence:
        gestalt.understanding.essence.core_qualities.append(
            capacity.get('description')
        )
```

---

### Phase 2: Connect Parent Journal (Week 1-2)

**Goal**: Parent journal entries enrich understanding

#### 2.1 Create Journal → Understanding Bridge

**File**: `backend/app/chitta/service.py` (new method)

```python
async def process_parent_journal_entry(
    self,
    family_id: str,
    entry_text: str,
    entry_type: str,  # "התקדמות" | "תצפית" | "אתגר"
) -> Dict[str, Any]:
    """
    Process a parent journal entry and feed it into understanding.

    Parent journal entries are GOLD - direct observations from daily life.
    We extract facts from them just like conversation messages.
    """
    gestalt = await self._load_gestalt(family_id)

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
        gestalt.child_name,
        mapping["domain_hint"]
    )

    # Add facts to understanding
    for fact_data in extracted.get("facts", []):
        fact = TemporalFact(
            content=fact_data["content"],
            domain=fact_data.get("domain", "general"),
            source="parent_journal",
            t_valid=datetime.now(),  # Journal entries are about NOW
            t_created=datetime.now(),
            confidence=0.8,  # High confidence - parent's direct observation
        )
        gestalt.understanding.add_fact(fact)
        gestalt._curiosity_engine.on_fact_learned(fact)

    # Add milestone if detected
    if extracted.get("milestone"):
        from .models import DevelopmentalMilestone
        milestone = DevelopmentalMilestone.create(
            description=extracted["milestone"]["description"],
            domain=extracted["milestone"].get("domain", "general"),
            milestone_type=extracted["milestone"].get("type", "observation"),
            source="parent_journal",
        )
        gestalt.understanding.add_milestone(milestone)

    # Create journal entry for the system journal
    from .models import JournalEntry
    entry = JournalEntry.create(
        summary=entry_text[:100] + "..." if len(entry_text) > 100 else entry_text,
        learned=[f["content"] for f in extracted.get("facts", [])],
        significance=mapping["significance"],
    )
    gestalt.journal.append(entry)

    # Persist
    await self._persist_gestalt(family_id, gestalt)

    return {
        "status": "processed",
        "facts_extracted": len(extracted.get("facts", [])),
        "milestone_detected": bool(extracted.get("milestone")),
    }

async def _extract_from_journal_entry(
    self,
    entry_text: str,
    child_name: Optional[str],
    domain_hint: Optional[str],
) -> Dict[str, Any]:
    """Lightweight LLM extraction from journal entry."""

    prompt = f"""
Extract developmental observations from this parent journal entry.

Child: {child_name or "the child"}
Entry: {entry_text}
{f"Domain hint: {domain_hint}" if domain_hint else ""}

Return JSON:
{{
  "facts": [
    {{"content": "observation in Hebrew", "domain": "motor|social|emotional|cognitive|language|sensory|regulation|strengths|concerns"}}
  ],
  "milestone": null or {{"description": "milestone description", "domain": "...", "type": "achievement|concern|regression"}}
}}

Be concise. Extract 1-3 key observations.
"""

    llm = self._get_llm()
    response = await llm.chat(
        messages=[LLMMessage(role="user", content=prompt)],
        temperature=0.2,
        max_tokens=500,
    )

    # Parse JSON response
    try:
        import json
        return json.loads(response.content)
    except:
        return {"facts": [], "milestone": None}
```

#### 2.2 Add API Endpoint

**File**: `backend/app/api/routes.py`

```python
@router.post("/family/{family_id}/journal")
async def create_journal_entry(
    family_id: str,
    entry: JournalEntryRequest,  # {text: str, type: str}
):
    """
    Create a parent journal entry and process it into understanding.
    """
    service = ChittaService()
    result = await service.process_parent_journal_entry(
        family_id=family_id,
        entry_text=entry.text,
        entry_type=entry.type,
    )
    return result
```

---

### Phase 3: Strengthen Temporal Anchoring (Week 2)

**Goal**: Facts and observations are anchored in time for developmental tracking

#### 3.1 Enhance notice Tool Prompting

**File**: `backend/app/chitta/tools.py`

```python
TOOL_NOTICE = {
    "name": "notice",
    "description": """Record an observation about the child.

Use this when you learn something about the child from the conversation.

**CRITICAL: ALWAYS include 'when' if the parent mentions ANY timing:**
- "אתמול" → when: "אתמול"
- "בגיל שנה" → when: "בגיל 12 חודשים"
- "בגיל שנתיים" → when: "בגיל 24 חודשים"
- "לפני חצי שנה" → when: "לפני 6 חודשים"
- "בדרך כלל" → when: "בדרך כלל"
- "עכשיו" → when: "עכשיו"
- "פעם היה... עכשיו..." → TWO notices with different 'when' values

This temporal information is ESSENTIAL for tracking development over time.
Without it, we can't show parents how their child has grown and changed.
""",
    "parameters": {
        "type": "object",
        "properties": {
            "observation": {
                "type": "string",
                "description": "What was observed or learned about the child"
            },
            "domain": {
                "type": "string",
                "description": "Developmental domain",
                "enum": ["motor", "social", "emotional", "cognitive", "language",
                        "sensory", "regulation", "essence", "strengths", "context",
                        "concerns", "general", "sleep", "feeding", "play",
                        "birth_history", "milestones", "medical"]
            },
            "when": {
                "type": "string",
                "description": "IMPORTANT: When was this true? Examples: 'אתמול', 'בגיל 12 חודשים', 'בדרך כלל', 'עכשיו'. ALWAYS provide if parent mentioned timing."
            },
            "confidence": {
                "type": "number",
                "description": "How confident (0-1). Default 0.7"
            }
        },
        "required": ["observation", "when"]  # Make 'when' required!
    }
}
```

#### 3.2 Enhance record_milestone Tool

**File**: `backend/app/chitta/tools.py`

```python
TOOL_RECORD_MILESTONE = {
    "name": "record_milestone",
    "description": """Record a developmental milestone with age.

**ALWAYS USE THIS** when parent mentions:
1. When something STARTED: "התחיל ללכת", "אמר מילה ראשונה"
2. When something STOPPED: "הפסיק לדבר", "כבר לא עושה..."
3. When something CHANGED: "פעם היה... עכשיו..."
4. Intervention timing: "התחיל טיפול", "עבר הערכה"

**Age conversion guide:**
- שנה = 12 months
- שנה וחצי = 18 months
- שנתיים = 24 months
- שנתיים וחצי = 30 months
- שלוש = 36 months

This builds the child's developmental timeline - CRITICAL for professional summaries!
""",
    "parameters": {
        "type": "object",
        "properties": {
            "description": {
                "type": "string",
                "description": "What happened - in Hebrew, clear and specific"
            },
            "age_months": {
                "type": "number",
                "description": "Age in months when it happened. Convert: 1 year=12, 1.5 years=18, 2 years=24, etc."
            },
            "age_description": {
                "type": "string",
                "description": "Age in words if exact months unknown: 'בגיל שנה', 'בערך בגיל שנתיים'"
            },
            "domain": {
                "type": "string",
                "enum": ["motor", "language", "social", "cognitive", "regulation", "birth_history", "medical"]
            },
            "milestone_type": {
                "type": "string",
                "enum": ["achievement", "concern", "regression", "intervention", "birth"],
                "description": "achievement=positive milestone, concern=worrying sign, regression=lost skill, intervention=therapy/evaluation, birth=pregnancy/birth related"
            }
        },
        "required": ["description", "milestone_type"]
    }
}
```

#### 3.3 Better Temporal Parsing

**File**: `backend/app/chitta/models.py` (enhance parse_temporal)

```python
def parse_temporal(when_str: Optional[str]) -> Optional[datetime]:
    """
    Parse temporal expressions into datetime.

    For relative expressions, we calculate from now.
    For age expressions, we return None (stored in age_months instead).
    """
    if not when_str:
        return None

    when_lower = when_str.lower().strip()
    now = datetime.now()

    # Exact/recent
    if when_lower in ["עכשיו", "היום", "now", "today"]:
        return now
    if when_lower in ["אתמול", "yesterday"]:
        return now - timedelta(days=1)
    if when_lower in ["שלשום"]:
        return now - timedelta(days=2)

    # Relative weeks
    if "שבוע" in when_lower:
        if "לפני" in when_lower:
            # "לפני שבוע", "לפני שבועיים"
            if "שבועיים" in when_lower:
                return now - timedelta(weeks=2)
            return now - timedelta(weeks=1)

    # Relative months
    if "חודש" in when_lower or "חודשים" in when_lower:
        if "לפני" in when_lower:
            # Try to extract number
            import re
            match = re.search(r'(\d+)', when_lower)
            if match:
                months = int(match.group(1))
                return now - timedelta(days=months * 30)
            if "חודשיים" in when_lower:
                return now - timedelta(days=60)
            return now - timedelta(days=30)

    # "Usually" or habitual - mark as ongoing (use today)
    if when_lower in ["בדרך כלל", "תמיד", "usually", "always"]:
        return now

    # Age-based expressions - return None, should use age_months instead
    if "בגיל" in when_lower or "גיל" in when_lower:
        return None  # Age-based, not date-based

    return None
```

---

### Phase 4: Connect Stories to Pattern Curiosity (Week 2)

**Goal**: Multi-domain stories automatically boost pattern detection

#### 4.1 Enhance capture_story Handler

**File**: `backend/app/chitta/gestalt.py`

```python
def _handle_capture_story(self, args: Dict[str, Any]):
    """Capture a story and its developmental signals."""
    story = Story.create(
        summary=args["summary"],
        reveals=args.get("reveals", []),
        domains=args.get("domains", []),
        significance=args.get("significance", 0.5),
    )
    self.stories.append(story)

    # Touch domains in curiosity engine
    for domain in story.domains:
        self._curiosity_engine.on_domain_touched(domain)

    # NEW: If story touches multiple domains, boost pattern curiosity
    if len(story.domains) >= 2:
        pattern_curiosity = self._get_pattern_curiosity()
        if pattern_curiosity:
            # Boost activation
            pattern_curiosity.boost_activation(0.15)
            # Add these domains to pattern's involved domains
            for domain in story.domains:
                if domain not in pattern_curiosity.domains_involved:
                    pattern_curiosity.domains_involved.append(domain)

    # NEW: If high significance, consider spawning hypothesis
    if story.significance >= 0.7 and len(story.reveals) >= 3:
        # This story reveals something deep - maybe worth exploring
        self._curiosity_engine.on_significant_story(story)

    # Add journal entry
    entry = JournalEntry.create(
        summary=f"Story captured: {story.summary}",
        learned=story.reveals,
        significance="notable" if story.significance > 0.7 else "routine",
    )
    self.journal.append(entry)

def _get_pattern_curiosity(self) -> Optional[Curiosity]:
    """Get the perpetual pattern curiosity."""
    for c in self._curiosity_engine._perpetual:
        if c.type == "pattern":
            return c
    return None
```

#### 4.2 Add on_significant_story to CuriosityEngine

**File**: `backend/app/chitta/curiosity.py`

```python
def on_significant_story(self, story: "Story"):
    """
    When a significant story is captured, consider spawning hypotheses.

    A story with 3+ reveals and high significance might contain
    patterns worth exploring.
    """
    # Check if story reveals suggest a cross-domain pattern
    if len(story.domains) >= 2:
        # Look for existing pattern curiosity about these domains
        existing = self._find_pattern_curiosity(story.domains)
        if existing:
            existing.boost_activation(0.2)
            existing.certainty = min(1.0, existing.certainty + 0.1)
        else:
            # Consider creating new pattern curiosity
            # Only if we don't have too many dynamic curiosities
            if len(self._dynamic) < 10:
                from .curiosity import create_pattern
                new_pattern = create_pattern(
                    focus=f"קשר בין {' ל'.join(story.domains[:2])}",
                    domains_involved=story.domains,
                    activation=0.6,
                    certainty=0.2,
                )
                self._dynamic.append(new_pattern)

def _find_pattern_curiosity(self, domains: List[str]) -> Optional[Curiosity]:
    """Find existing pattern curiosity involving these domains."""
    for c in self._dynamic:
        if c.type == "pattern":
            overlap = set(c.domains_involved) & set(domains)
            if len(overlap) >= 2:
                return c
    return None
```

---

### Phase 5: Use video_value in Scenario Framing (Week 2-3)

**Goal**: Video scenarios are framed based on WHY video would help

#### 5.1 Enhance Scenario Generation Prompt

**File**: `backend/app/chitta/service.py` (in generate_video_scenarios)

```python
async def generate_video_scenarios(
    self,
    family_id: str,
    cycle_id: str,
) -> List["VideoScenario"]:
    """Generate video scenarios with intent-aware framing."""

    gestalt = await self._load_gestalt(family_id)
    cycle = self._get_cycle(gestalt, cycle_id)

    if not cycle:
        return []

    # Build video_value context
    video_value_guidance = self._get_video_value_guidance(cycle)

    prompt = f"""
Generate a video filming scenario for this exploration.

## Child Context
{gestalt.child_name or "This child"}

## Exploration
Focus: {cycle.focus}
Theory: {cycle.theory or "N/A"}
Domain: {cycle.focus_domain}

## Video Intent
{video_value_guidance}

## Guidelines
...
"""

def _get_video_value_guidance(self, cycle) -> str:
    """Get guidance based on video_value type."""

    video_value = cycle.video_value
    reason = cycle.video_value_reason or ""

    if video_value == "calibration":
        return f"""
**Intent: CALIBRATION**
The parent made an absolute statement that we want to see in context.
{reason}

Frame the scenario to capture natural moments where this behavior might occur.
We're not testing - we're calibrating our understanding of what "always" or "never"
actually looks like for this child.

Parent-facing: "נשמח לראות איך זה נראה בפועל"
"""

    elif video_value == "chain":
        return f"""
**Intent: CHAIN REVELATION**
We suspect a connection between domains that video could reveal.
{reason}

Frame the scenario to capture sequences and transitions.
We're looking for the cascade: what happens first, then what follows.

Parent-facing: "נשמח לראות רגע שבו קורים כמה דברים ביחד"
"""

    elif video_value == "discovery":
        return f"""
**Intent: DISCOVERY (Unknown Unknowns)**
We want to see this child before forming strong theories.
{reason}

Frame as open observation - free play, natural interaction.
We're not looking for anything specific - we're opening our eyes.

Parent-facing: "נשמח להכיר אותו דרך צפייה במשחק חופשי"
"""

    elif video_value == "reframe":
        return f"""
**Intent: REFRAME**
Parent described something as a concern that might actually be a strength.
{reason}

Frame the scenario to capture this behavior in context.
We're looking for the function behind the form - what purpose does it serve?

Parent-facing: "נשמח לראות את הרגע הזה כדי להבין אותו טוב יותר"
"""

    elif video_value == "relational":
        return f"""
**Intent: RELATIONAL (Dyadic Patterns)**
The parent-child interaction itself is what we want to see.
{reason}

Frame for natural interaction, turn-taking, attunement.
We're watching the dance between parent and child.

Parent-facing: "נשמח לראות אתכם משחקים ביחד"
"""

    else:
        return """
**Intent: HYPOTHESIS TEST**
Standard hypothesis testing - looking for evidence that supports or contradicts.

Parent-facing: Frame based on the specific theory being tested.
"""
```

---

### Phase 6: Developmental Timeline Display (Week 3)

**Goal**: Parents can see their child's development over time

#### 6.1 Create Timeline Data Structure

**File**: `backend/app/chitta/service.py` (new method)

```python
async def get_developmental_timeline(
    self,
    family_id: str,
) -> Dict[str, Any]:
    """
    Build a developmental timeline for display.

    Combines:
    - Milestones (from record_milestone)
    - Significant facts with temporal data
    - Key stories
    - Video analysis discoveries
    """
    gestalt = await self._load_gestalt(family_id)

    timeline_items = []

    # 1. Milestones (most important)
    for milestone in gestalt.understanding.milestones:
        timeline_items.append({
            "type": "milestone",
            "description": milestone.description,
            "age_months": milestone.age_months,
            "age_description": milestone.age_description,
            "domain": milestone.domain,
            "milestone_type": milestone.milestone_type,
            "recorded_at": milestone.recorded_at.isoformat(),
            "icon": self._get_milestone_icon(milestone.milestone_type),
            "color": self._get_domain_color(milestone.domain),
        })

    # 2. Significant facts with t_valid
    for fact in gestalt.understanding.facts:
        if fact.t_valid and fact.confidence >= 0.7:
            # Only include facts with temporal anchoring
            timeline_items.append({
                "type": "observation",
                "description": fact.content,
                "timestamp": fact.t_valid.isoformat(),
                "domain": fact.domain,
                "source": fact.source,
                "icon": "👁️",
                "color": self._get_domain_color(fact.domain),
            })

    # 3. Significant stories
    for story in gestalt.stories:
        if story.significance >= 0.7:
            timeline_items.append({
                "type": "story",
                "description": story.summary,
                "timestamp": story.timestamp.isoformat(),
                "domains": story.domains,
                "reveals": story.reveals[:3],
                "icon": "📖",
                "color": "amber",
            })

    # 4. Video discoveries
    for cycle in gestalt.exploration_cycles:
        for scenario in cycle.video_scenarios:
            if scenario.status == "analyzed" and scenario.analysis_result:
                insights = scenario.analysis_result.get("insights", [])
                strengths = scenario.analysis_result.get("strengths_observed", [])
                if insights or strengths:
                    timeline_items.append({
                        "type": "video_discovery",
                        "description": insights[0] if insights else strengths[0].get("strength", ""),
                        "timestamp": scenario.analyzed_at.isoformat() if scenario.analyzed_at else None,
                        "domain": cycle.focus_domain,
                        "icon": "🎬",
                        "color": "teal",
                    })

    # Sort by age (milestones) or timestamp (others)
    # Milestones with age_months come first, sorted by age
    # Others sorted by timestamp

    milestones_with_age = [i for i in timeline_items if i.get("age_months")]
    others = [i for i in timeline_items if not i.get("age_months") and i.get("timestamp")]

    milestones_with_age.sort(key=lambda x: x["age_months"])
    others.sort(key=lambda x: x["timestamp"], reverse=True)

    return {
        "timeline": {
            "by_age": milestones_with_age,  # Sorted by child's age
            "by_date": others[:30],  # Recent observations, limited
        },
        "child_name": gestalt.child_name,
        "total_milestones": len(milestones_with_age),
        "domains_covered": list(set(
            i.get("domain") for i in timeline_items if i.get("domain")
        )),
    }

def _get_milestone_icon(self, milestone_type: str) -> str:
    return {
        "achievement": "🌟",
        "concern": "⚠️",
        "regression": "📉",
        "intervention": "🏥",
        "birth": "👶",
    }.get(milestone_type, "📌")

def _get_domain_color(self, domain: str) -> str:
    return {
        "motor": "blue",
        "language": "purple",
        "social": "pink",
        "emotional": "rose",
        "cognitive": "indigo",
        "sensory": "cyan",
        "regulation": "orange",
        "strengths": "green",
    }.get(domain, "gray")
```

#### 6.2 API Endpoint

**File**: `backend/app/api/routes.py`

```python
@router.get("/family/{family_id}/timeline")
async def get_timeline(family_id: str):
    """Get developmental timeline for display."""
    service = ChittaService()
    return await service.get_developmental_timeline(family_id)
```

#### 6.3 Frontend Component (Outline)

**File**: `src/components/DevelopmentalTimeline.jsx`

```jsx
// A new tab or section in ChildSpace
// Shows:
// 1. Age-based milestones (vertical timeline)
// 2. Recent observations (scrollable cards)
// 3. Domain filters
// 4. "Add milestone" quick action
```

---

### Phase 7: Clinical Gaps Inform Turn Guidance (Week 3)

**Goal**: Conversation naturally gathers clinical information when appropriate

#### 7.1 Enhance Turn Guidance with Clinical Context

**File**: `backend/app/chitta/formatting.py`

```python
def format_turn_guidance(
    captured_story: bool,
    spawned_curiosity: bool,
    added_evidence: bool,
    perceived_intent: str,
    active_curiosities: List = None,
    understanding = None,
    clinical_gaps: List[str] = None,
) -> str:
    """Generate contextual turn guidance including clinical gaps."""

    sections = []

    # Story reception (highest priority)
    if captured_story:
        sections.append("""
## THIS TURN: Story Received 📖
The parent shared something meaningful. This is GOLD.
- Honor what was shared - reflect it back
- Don't rush past this moment
- Maximum one gentle question, only if natural
""")

    # Emotion/concern response
    elif perceived_intent in ["emotional", "concern"]:
        sections.append("""
## THIS TURN: Holding Space 💙
The parent expressed something emotional.
- Acknowledge and validate
- Don't problem-solve too quickly
- Create space for more if they want to share
""")

    # Question response
    elif perceived_intent == "question":
        sections.append("""
## THIS TURN: Question Asked ❓
The parent asked something directly.
- Answer clearly and helpfully
- Then you may gently explore further
""")

    # Clinical gaps (background, not pushy)
    if clinical_gaps and not captured_story:
        # Only include if not in a story-receiving moment
        gaps_text = ", ".join(clinical_gaps[:2])
        sections.append(f"""
## BACKGROUND CONTEXT (do NOT interrogate)
Areas that would help professional summaries: {gaps_text}

If a NATURAL opportunity arises, you may gently explore.
Example: "אגב, לגבי ההתפתחות המוקדמת שלו..."

NEVER prioritize this over what the parent wants to share.
""")

    # High-activation curiosities
    if active_curiosities:
        top = [c for c in active_curiosities if c.activation > 0.7][:2]
        if top:
            curiosities_text = "\n".join(f"- {c.focus}" for c in top)
            sections.append(f"""
## ACTIVE CURIOSITIES
{curiosities_text}

These are what we're most wondering about.
Follow the parent's lead, but these inform your attention.
""")

    return "\n".join(sections) if sections else ""
```

#### 7.2 Integrate into Response Prompt Building

**File**: `backend/app/chitta/gestalt.py`

```python
def _build_response_prompt(self, context: TurnContext, extraction: ExtractionResult) -> str:
    """Build prompt for Phase 2 with clinical gap awareness."""

    # ... existing code ...

    # Get clinical gaps for context
    from .clinical_gaps import ClinicalGapDetector
    detector = ClinicalGapDetector()

    # Only include if we don't have critical gaps (otherwise too pushy)
    clinical_context = []
    for field in ["birth_history", "milestones"]:
        if not detector._has_data_for(field, self.understanding, None):
            clinical_context.append(field)

    # Build guidance with all context
    guidance = format_turn_guidance(
        captured_story=any(tc.name == "capture_story" for tc in extraction.tool_calls),
        spawned_curiosity=any(tc.name == "wonder" for tc in extraction.tool_calls),
        added_evidence=any(tc.name == "add_evidence" for tc in extraction.tool_calls),
        perceived_intent=extraction.perceived_intent,
        active_curiosities=context.curiosities,
        understanding=context.understanding,
        clinical_gaps=clinical_context if clinical_context else None,
    )

    # ... rest of prompt building ...
```

---

### Phase 8: Trigger Baseline Video (Week 3)

**Goal**: Suggest baseline video at the right time

#### 8.1 Check and Trigger in process_message

**File**: `backend/app/chitta/gestalt.py`

```python
async def process_message(self, message: str) -> Response:
    """Process message with baseline video check."""

    # ... existing two-phase processing ...

    # Check if we should suggest baseline video
    baseline_video_suggestion = None
    message_count = len(self.session_history)

    if self._curiosity_engine.should_suggest_baseline_video(message_count):
        # Only suggest if we have rapport but few hypotheses
        if not self._has_video_suggestions():
            baseline_video_suggestion = {
                "type": "baseline",
                "instruction": "צלמי 3-5 דקות של משחק חופשי רגיל ביחד",
                "why": "זה יעזור לנו להכיר אותו בדרך שמשלימה את מה שאת מספרת",
            }
            # Mark as suggested so we don't repeat
            self._curiosity_engine.mark_baseline_video_requested()

    return Response(
        text=response_text,
        curiosities=self.get_active_curiosities(),
        open_questions=self._curiosity_engine.get_gaps(),
        should_crystallize=should_crystallize,
        baseline_video_suggestion=baseline_video_suggestion,  # NEW
    )

def _has_video_suggestions(self) -> bool:
    """Check if we already have video suggestions pending."""
    for cycle in self.exploration_cycles:
        if cycle.video_scenarios:
            return True
    return False
```

---

## Part 3: Implementation Checklist

### Week 1: Video Connections
- [ ] 1.1 Video strengths → curiosity_engine.on_fact_learned()
- [ ] 1.2 Video new_questions → create_question curiosities
- [ ] 1.3 Video capacity → essence core_qualities
- [ ] 2.1 Parent journal → understanding bridge method
- [ ] 2.2 Journal API endpoint

### Week 2: Temporal & Stories
- [ ] 3.1 Enhance notice tool (require 'when')
- [ ] 3.2 Enhance record_milestone tool
- [ ] 3.3 Better temporal parsing
- [ ] 4.1 capture_story → pattern curiosity boost
- [ ] 4.2 on_significant_story method
- [ ] 5.1 video_value → scenario framing

### Week 3: Display & Guidance
- [ ] 6.1 Timeline data structure
- [ ] 6.2 Timeline API endpoint
- [ ] 6.3 Timeline frontend component
- [ ] 7.1 Turn guidance with clinical context
- [ ] 7.2 Integration into response prompt
- [ ] 8.1 Baseline video triggering

---

## Part 4: Success Metrics

### Before Implementation
- Video learnings: 60% utilized
- Parent journal: 20% utilized
- Temporal tracking: 15% utilized
- Overall interconnection: 55-60%

### After Implementation
- Video learnings: 95% utilized (feeds curiosity, spawns questions)
- Parent journal: 90% utilized (feeds understanding, creates milestones)
- Temporal tracking: 80% utilized (timeline view, temporal anchoring)
- Overall interconnection: 90%+

### How to Verify

1. **Video Integration Test**
   - Upload video → check if new curiosities spawned
   - Upload video → check if strengths appear in Understanding

2. **Journal Integration Test**
   - Create journal entry "היום הוא אמר מילה חדשה"
   - Check if fact added to Understanding
   - Check if curiosity about language boosted

3. **Temporal Test**
   - Send message "הוא התחיל ללכת בגיל שנה"
   - Check if milestone created with age_months=12
   - Check if appears in timeline

4. **Story → Pattern Test**
   - Share multi-domain story
   - Check if pattern curiosity activation increased
   - Check if domains_involved updated

---

## Part 5: Files to Modify

| File | Changes | Lines |
|------|---------|-------|
| `backend/app/chitta/service.py` | Video integration, journal processing, timeline, scenario framing | ~200 |
| `backend/app/chitta/gestalt.py` | Story handling, baseline video, response prompt | ~80 |
| `backend/app/chitta/curiosity.py` | on_significant_story, _find_pattern_curiosity | ~40 |
| `backend/app/chitta/tools.py` | Enhanced notice, record_milestone | ~50 |
| `backend/app/chitta/models.py` | parse_temporal enhancement | ~30 |
| `backend/app/chitta/formatting.py` | Turn guidance with clinical context | ~50 |
| `backend/app/api/routes.py` | New endpoints (journal, timeline) | ~30 |
| `src/components/DevelopmentalTimeline.jsx` | New component | ~200 |

**Total: ~680 lines of changes/additions**

---

## Part 6: Guiding Principles

Throughout implementation, maintain:

1. **פשוט (Simplicity)** - Each change should be minimal and focused
2. **Connection over creation** - We're connecting existing parts, not adding new systems
3. **LLM understanding, not keywords** - Detection happens through LLM comprehension
4. **Parent agency** - Nothing is forced, everything is offered
5. **Warm Hebrew** - All parent-facing text is natural and warm

---

## Conclusion

This plan transforms Chitta from a collection of good components into a **living, interconnected system** where:

- Every video analysis enriches curiosity
- Every parent journal entry deepens understanding
- Every story strengthens pattern detection
- Every milestone builds the developmental timeline
- Every turn is guided by the full context

The whole becomes greater than the sum of its parts because **data flows in all directions**, creating emergent understanding that grows richer with every interaction.

---

*Plan created with commitment to simplicity and respect for the vision.*
