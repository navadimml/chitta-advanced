# Curiosity & Exploration Cycle Redesign

## Context

Based on deep analysis of video's value, we identified that the current system treats video as a simple "yes/no" flag on hypotheses. This misses the richer understanding of WHEN and WHY video adds value.

### Video's Five Gifts (Feasible at 1fps)

| Gift | What It Reveals |
|------|-----------------|
| **Unknown unknowns** | What parent didn't notice or think to mention |
| **Chain revelation** | Cross-domain patterns (sequences over seconds) |
| **Calibration** | What "always/never" actually means |
| **Reframing** | Strengths hidden in concerns |
| **Relational** | Dyadic parent-child patterns |

**Removed:** Micropatterns (sub-second timing) - not feasible at 1 frame/second.

---

## Current Architecture Gaps

### 1. Binary Video Decision
**Current:** `video_appropriate: bool = True/False`
**Problem:** Doesn't capture WHY video is valuable

### 2. Hypothesis-Only Video
**Current:** Video scenarios only linked to hypothesis testing
**Problem:** Misses discovery, calibration, baseline opportunities

### 3. No Baseline Video Concept
**Current:** Video only after hypothesis forms
**Problem:** Unknown unknowns require seeing BEFORE theorizing

---

## Design Principles

### LLM-Driven, Not Rule-Based

All detection happens through the LLM during extraction phase, not through code pattern matching.

```python
# ❌ WRONG - string matching in code
def detect_calibration_trigger(self, parent_message: str):
    if "אף פעם" in parent_message:
        return True

# ✅ RIGHT - LLM decides during extraction via tool use
# The LLM understands context and clinical significance
# It uses the `wonder` tool with video_value field when appropriate
```

The LLM understands nuance:
- "הוא אף פעם לא מסתכל בעיניים" → Clinically significant, video could calibrate
- "הוא אף פעם לא אוכל ברוקולי" → Not clinically significant, no video needed

---

## Proposed Changes

### A. Enhanced `wonder` Tool

Add a `video_value` field to the wonder tool that the LLM can use when it recognizes video would help:

```python
TOOL_WONDER = {
    "name": "wonder",
    "description": """Spawn a new curiosity about the child.
    ...existing description...

    VIDEO VALUE:
    When you notice that video observation could add value beyond conversation,
    specify why in video_value. Only use when video provides something
    conversation cannot:

    - "calibration": Parent made absolute claim ("never", "always") about
      clinically significant behavior. Video could show the actual picture.
    - "chain": Multiple domains seem connected. Video could reveal the chain.
    - "discovery": We've never seen this child. Baseline observation could
      reveal things we don't know to ask about.
    - "reframe": Parent describes concern that might actually be a strength
      when seen in context.
    - "relational": The parent-child interaction pattern itself is the question.

    Leave empty if conversation is sufficient.
    """,
    "parameters": {
        "type": "object",
        "properties": {
            # ...existing fields...
            "about": {"type": "string"},
            "type": {"type": "string", "enum": ["discovery", "question", "hypothesis", "pattern"]},
            "certainty": {"type": "number"},
            "domain": {"type": "string"},
            "theory": {"type": "string"},
            "video_appropriate": {"type": "boolean"},

            # NEW FIELD
            "video_value": {
                "type": "string",
                "enum": ["calibration", "chain", "discovery", "reframe", "relational"],
                "description": "Why video would add value beyond conversation. Leave empty if not needed."
            },
            "video_value_reason": {
                "type": "string",
                "description": "Brief explanation of what video could reveal that conversation cannot."
            }
        },
        "required": ["about", "type"]
    }
}
```

### B. Enhanced Curiosity Model

```python
@dataclass
class Curiosity:
    # ...existing fields...
    focus: str
    type: str  # discovery | question | hypothesis | pattern
    activation: float
    certainty: float
    theory: Optional[str] = None
    video_appropriate: bool = False
    question: Optional[str] = None
    domains_involved: List[str] = field(default_factory=list)
    domain: Optional[str] = None

    # === NEW FIELD ===
    video_value: Optional[str] = None  # calibration | chain | discovery | reframe | relational
    video_value_reason: Optional[str] = None  # Why video would help
```

**Factory function update:**

```python
def create_hypothesis(
    focus: str,
    theory: str,
    domain: str,
    video_appropriate: bool = True,
    video_value: Optional[str] = None,  # NEW
    video_value_reason: Optional[str] = None,  # NEW
    activation: float = 0.7,
    certainty: float = 0.3,
) -> Curiosity:
    """Create a hypothesis-type curiosity."""
    return Curiosity(
        focus=focus,
        type="hypothesis",
        activation=activation,
        certainty=certainty,
        theory=theory,
        video_appropriate=video_appropriate,
        video_value=video_value,
        video_value_reason=video_value_reason,
        domain=domain,
    )
```

### C. Enhanced ExplorationCycle

```python
@dataclass
class ExplorationCycle:
    # ...existing fields...

    # === NEW FIELD ===
    video_value: Optional[str] = None  # Why video is valuable for this cycle
    video_value_reason: Optional[str] = None
```

### D. Baseline Video Request (New Model)

For early-relationship discovery before hypotheses form:

```python
@dataclass
class BaselineVideoRequest:
    """
    Early-relationship request for a baseline video.

    Not tied to any hypothesis - captures unknown unknowns.
    Suggested after initial rapport, before strong theories form.
    """
    id: str
    status: str = "pending"  # pending | accepted | declined | uploaded | analyzed

    # Timing
    suggested_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None

    # Parent-facing (simple, warm)
    parent_instruction: str = "צלמי 3-5 דקות של משחק חופשי רגיל ביחד"
    why_helpful: str = "זה עוזר לנו להכיר אותו בדרך שמשלימה את מה שאת מספרת"

    # Video
    video_path: Optional[str] = None
    uploaded_at: Optional[datetime] = None

    # Analysis results
    analysis_result: Optional[Dict[str, Any]] = None
    analyzed_at: Optional[datetime] = None
    discoveries: List[str] = field(default_factory=list)  # What we learned

    @classmethod
    def create(cls) -> "BaselineVideoRequest":
        return cls(
            id=generate_id(),
            suggested_at=datetime.now(),
        )

    def accept(self):
        self.status = "accepted"
        self.accepted_at = datetime.now()

    def decline(self):
        self.status = "declined"
```

### E. CuriosityEngine Updates

```python
class CuriosityEngine:
    # ...existing code...

    # NEW: Track baseline video
    baseline_video_request: Optional[BaselineVideoRequest] = None

    def should_suggest_baseline_video(self, message_count: int) -> bool:
        """
        Should we suggest baseline video?

        Simple heuristic:
        - Not already done/requested
        - After some rapport (message 3+)
        - Before heavy theorizing (message <15)
        - Few hypotheses formed
        """
        if self.baseline_video_request is not None:
            return False  # Already suggested

        if message_count < 3 or message_count > 15:
            return False

        hypothesis_count = len([c for c in self._dynamic if c.type == "hypothesis"])
        return hypothesis_count < 3

    def get_curiosities_with_video_value(self) -> List[Curiosity]:
        """Get curiosities where video would add value."""
        return [c for c in self._dynamic if c.video_value is not None]
```

---

## Video Scenario Generation by Intent

When generating video scenarios, use the `video_value` to guide framing:

```python
def generate_scenario_for_intent(
    cycle: ExplorationCycle,
    child_context: str,
) -> VideoScenario:
    """Generate scenario based on video value intent."""

    intent = cycle.video_value

    if intent == "calibration":
        # Focus on the specific behavior being calibrated
        # Parent-facing: "נשמח לראות איך זה נראה בפועל"
        pass

    elif intent == "chain":
        # Look for cross-domain connections
        # Parent-facing: "נשמח לראות רגע שבו X ו-Y קורים"
        pass

    elif intent == "discovery":
        # Open observation, no specific focus
        # Parent-facing: "משחק חופשי רגיל"
        pass

    elif intent == "reframe":
        # Look for strengths in reported concern
        # Parent-facing: Focus on context where behavior happens
        pass

    elif intent == "relational":
        # Focus on interaction quality
        # Parent-facing: "שחקי איתו כמו שאת רגילה"
        pass
```

---

## Integration Flow

```
Message arrives
    ↓
Phase 1: Extraction (LLM with tools)
    - LLM uses `wonder` tool
    - If LLM recognizes video would help, it sets video_value + video_value_reason
    - This is LLM judgment, not code pattern matching
    ↓
Apply Learnings
    - Create Curiosity with video_value if provided
    - Check if baseline video should be suggested
    ↓
Phase 2: Response
    - If curiosity has video_value, consider suggesting video
    - Frame based on video_value intent
```

---

## Examples

### Example 1: Calibration

Parent says: "הוא אף פעם לא מסתכל לי בעיניים"

LLM uses wonder tool:
```json
{
  "about": "קשר עין",
  "type": "question",
  "domain": "social",
  "question": "איך נראה קשר העין בפועל?",
  "video_appropriate": true,
  "video_value": "calibration",
  "video_value_reason": "ההורה מתאר 'אף פעם' - וידאו יכול להראות את התמונה המלאה"
}
```

### Example 2: Chain

Parent mentions sensory sensitivity AND social avoidance in same conversation.

LLM uses wonder tool:
```json
{
  "about": "קשר בין רגישות חושית להתנהגות חברתית",
  "type": "pattern",
  "domains_involved": ["sensory", "social"],
  "video_appropriate": true,
  "video_value": "chain",
  "video_value_reason": "יכול להיות קשר בין עומס חושי לנסיגה חברתית - וידאו יכול לחשוף את הרצף"
}
```

### Example 3: Reframe

Parent says: "הוא מתנדנד כל הזמן, זה מטריד אותי"

LLM uses wonder tool:
```json
{
  "about": "התנדנדות",
  "type": "hypothesis",
  "domain": "regulation",
  "theory": "יכול להיות שההתנדנדות עוזרת לו להתרכז או להירגע",
  "video_appropriate": true,
  "video_value": "reframe",
  "video_value_reason": "מה שנראה כמו בעיה עשוי להיות אסטרטגיית ויסות עצמי יעילה"
}
```

---

## Implementation Priority

1. **Add video_value field to wonder tool** - LLM can now express WHY video helps
2. **Add video_value to Curiosity model** - Store the intent
3. **Add BaselineVideoRequest model** - New capability
4. **Update CuriosityEngine** - Baseline video suggestion
5. **Update scenario generation** - Intent-based framing
6. **Update serialization** - Persist video_value

---

## What This Enables

### 1. Smarter Video Requests
Not just "yes/no" but WHY - better decisions about when to ask.

### 2. Better Parent Communication
Different intents = different framing:
- Calibration: "נשמח לראות איך זה נראה בפועל"
- Chain: "ראינו כמה דברים שאולי קשורים..."
- Discovery: "עוד לא ראינו אותו - זה יעזור לנו להכיר"

### 3. Better Video Analysis
When we know the intent, we know what to look for.

### 4. Baseline Video Early
Capture unknown unknowns before theories form.

---

## Files to Modify

| File | Changes |
|------|---------|
| `tools.py` | Add video_value, video_value_reason to wonder tool |
| `curiosity.py` | Add video_value fields to Curiosity, update factories |
| `models.py` | Add BaselineVideoRequest, add video_value to ExplorationCycle |
| `service.py` | Handle video_value when processing wonder tool calls |
| `gestalt.py` | Check baseline video timing |

---

## Open Questions

1. Should baseline video be proactively suggested or wait for natural moment?
2. How to prioritize when multiple curiosities have video_value?
3. Should we limit video requests (e.g., max 1 per session)?
