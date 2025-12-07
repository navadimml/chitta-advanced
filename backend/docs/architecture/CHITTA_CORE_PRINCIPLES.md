# Chitta: Core Principles & Architecture Guide

**A comprehensive guide for developers joining the Chitta project**

---

## Table of Contents

1. [The Heart of Chitta](#1-the-heart-of-chitta)
2. [The Living Gestalt](#2-the-living-gestalt)
3. [Curiosity-Driven Architecture](#3-curiosity-driven-architecture)
4. [Understanding: Essence, Facts & Patterns](#4-understanding-essence-facts--patterns)
5. [The Journal: Temporal Backbone](#5-the-journal-temporal-backbone)
6. [Exploration Cycles](#6-exploration-cycles)
7. [Conversation Dynamics](#7-conversation-dynamics)
8. [Tools & Dynamic Context](#8-tools--dynamic-context)
9. [Context Cards & The Space](#9-context-cards--the-space)
10. [Multilanguage & i18n](#10-multilanguage--i18n)
11. [Domain Separation (Wu Wei)](#11-domain-separation-wu-wei)
12. [Practical Development Guide](#12-practical-development-guide)

---

## 1. The Heart of Chitta

### What Chitta Is

Chitta is a **lens for seeing children clearly**. It helps parents and clinicians build understanding of a child's development through conversation, observation, and synthesis.

**Chitta is NOT:**
- A diagnostic tool
- A replacement for professionals
- An assessment platform
- An AI that "knows better"

**Chitta IS:**
- A warm, knowledgeable companion
- A guide who helps parents see their child clearly
- A lens for understanding development
- A conversation partner who builds insight together

### The Fundamental Shift

Traditional child development apps work like this:
```
Collect Data → Run Assessment → Generate Report → Done
```

Chitta works like this:
```
Observe → Wonder → Hypothesize → Explore → Understand → Wonder Again...
```

**The conversation IS the product.** Every exchange builds understanding. There is no "done" state—only deeper insight.

### Stories Are Gold

The most valuable data isn't checkboxes or structured fields. It's **stories**:

> "Yesterday at the park, she saw another child crying and went over to pat his back..."

This single story reveals:
- Empathy and social awareness
- Emotional recognition in others
- Prosocial behavior initiation
- Comfort with approaching unfamiliar children
- Response to distress in others

A skilled observer (Chitta) sees all of this in one story. No form can capture it.

---

## 2. The Living Gestalt

### The Core Insight

The Gestalt is not a data structure. **The Gestalt is the observing intelligence.**

It's the layer that:
- Watches the conversation unfold
- Notices when something needs exploration
- Sees patterns emerging across observations
- Knows what's missing and is curious about it
- Decides when understanding has crystallized

This is the "seeing the whole child" layer. Everything else—cycles, facts, artifacts—are its **tools for building understanding**.

### The Gestalt as Active Intelligence

```
┌─────────────────────────────────────────────────────────────────┐
│                    THE LIVING GESTALT                           │
│                  (The Observing Intelligence)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  "I am building understanding of this child."                   │
│                                                                 │
│  I HOLD:                                                        │
│  ├── Understanding    - What I know (essence, facts, patterns) │
│  ├── Curiosities      - What I'm curious about (always present)│
│  ├── Cycles           - Focused investigations I've spawned    │
│  ├── Journal          - The story of how I came to understand  │
│  └── Artifacts        - What I've created for the parent       │
│                                                                 │
│  I DO:                                                          │
│  ├── Notice gaps      → spawn exploration                       │
│  ├── Notice patterns  → form cross-cutting insights            │
│  ├── Notice readiness → suggest artifacts                       │
│  └── Notice change    → update understanding                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Child-First, Not Problem-First

Traditional apps ask: "What's wrong? What are you worried about?"
This frames the child through their difficulty.

**Chitta asks differently:** "Tell me about your child. What are they like?"

The concern still comes. But it lands in context—one aspect of a whole person, not the defining frame.

```
Daniel is not "speech delay." Daniel is:
├── A careful observer who processes internally
├── Loves dinosaurs and creates elaborate scenarios
├── Connects deeply with few people
├── Laughs at physical comedy
└── Happens to also have speech emerging slowly

The difficulty is real. But it's not the whole child.
```

### The Gestalt vs. The Data Container

**Old approach (data container):**
```python
class Gestalt:
    name: str
    age: float
    concerns: List[str]
    completeness: float  # "40% done"
```

**New approach (observing intelligence):**
```python
class LivingGestalt:
    # What I know about this child
    understanding: Understanding      # Essence + Facts + Patterns

    # What I'm curious about (always present, varying activation)
    curiosities: List[Curiosity]

    # Focused investigations I've spawned
    exploration_cycles: List[ExplorationCycle]

    # The story of how I came to understand
    journal: Journal

    # What I've created
    artifacts: List[Artifact]

    # Methods - the Gestalt DOES things
    def notice(self, observation) -> None: ...
    def spawn_exploration(self, curiosity) -> Cycle: ...
    def synthesize(self) -> Understanding: ...
    def suggest_artifact(self) -> Optional[Artifact]: ...
```

### Completeness Is Misleading

We don't measure "completeness" (as if understanding has an end). Instead, we track:

- **Curiosity activation**: What are we most curious about right now?
- **Understanding confidence**: How well do we know this child's essence?
- **Gaps**: What do we know we don't know?
- **Open questions**: What are we still wondering about?

---

## 3. Curiosity-Driven Architecture

### The Core Insight

**Curiosity is the primitive, not hypothesis.**

The Gestalt is curious about this child. It explores its curiosities through cycles. Understanding emerges.

A hypothesis is one *type* of curiosity. But not all exploration is hypothesis-testing. Sometimes we're just wondering. Sometimes we're following a thread. Sometimes we're discovering who this child is.

### Four Types of Curiosity

```
┌─────────────────────────────────────────────────────────────────┐
│                    TYPES OF CURIOSITY                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. DISCOVERY                                                   │
│     "Who is this child?"                                        │
│     "What does Daniel love?"                                    │
│     "What's the family context?"                                │
│                                                                 │
│     → No theory to test. Open receiving. Building foundation.   │
│                                                                 │
│  2. QUESTION                                                    │
│     "What makes grandmother different?"                         │
│     "Why does he respond to music but not speech?"              │
│                                                                 │
│     → Something specific to understand. Following a thread.     │
│                                                                 │
│  3. HYPOTHESIS                                                  │
│     "Motor challenges may cause the frustration"                │
│     "Speech is context-dependent, not delayed"                  │
│                                                                 │
│     → Theory to test. Gathering confirming/refuting evidence.   │
│                                                                 │
│  4. PATTERN                                                     │
│     "Caution appears across multiple contexts"                  │
│     "Safety seems to unlock expression"                         │
│                                                                 │
│     → Cross-cutting theme to investigate. Connecting dots.      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Curiosity Activation (The Flow Model)

Instead of rigid phases, the Gestalt maintains **perpetual curiosities** with varying activation:

```
THE GESTALT'S CURIOSITIES (always present, varying activation)

┌────────────────────────────────────────────────────────────────┐
│                                                                │
│  WHO IS THIS CHILD?                          [████████░░] 80%  │
│  (essence, personality, what makes them them)                  │
│  → Currently exploring: Daniel's careful observation style     │
│                                                                │
│  WHAT DO THEY LOVE?                          [██████░░░░] 60%  │
│  (strengths, interests, what lights them up)                   │
│  → Discovered: dinosaurs, lining up cars                       │
│  → Still curious: music? physical play?                        │
│                                                                │
│  WHAT'S THE CONTEXT?                         [████░░░░░░] 40%  │
│  (family, history, environment)                                │
│  → Know: grandmother exists, seems important                   │
│  → Missing: birth history, siblings, previous evaluations      │
│                                                                │
│  WHAT BROUGHT THEM HERE?                     [██████████] 100% │
│  (the concern that initiated contact)                          │
│  → Speech delay (captured)                                     │
│                                                                │
│  WHAT'S REALLY GOING ON?                     [████░░░░░░] 40%  │
│  (deeper understanding, patterns, meaning)                     │
│  → Emerging: slow-to-warm temperament                          │
│  → Active hypothesis: speech is context-dependent              │
│  → Thread following: grandmother relationship                  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

**No rigid phases. Natural flow guided by active curiosity.**

The Gestalt flows toward whatever curiosity is most relevant in the moment:
- Early conversation: "Who is this child?" is highly activated
- Parent mentions concern: Captured, but we bridge back to foundation
- Pattern emerges: "What's really going on?" activates, spawns cycle
- Gap noticed: "What's the context?" activates, Chitta asks naturally

### Curiosities Spawn Explorations

When a curiosity becomes focused enough, it spawns an **Exploration Cycle**:

```python
class Curiosity:
    """Something the Gestalt wants to understand"""

    type: str                    # "discovery" | "question" | "hypothesis" | "pattern"
    focus: str                   # What specifically we're curious about
    activation: float            # 0-1, how active is this curiosity right now

    # For discovery
    aspect: Optional[str]        # "essence" | "strengths" | "context"
    gaps: List[str]              # What's missing

    # For question
    question: Optional[str]      # The specific question

    # For hypothesis
    theory: Optional[str]        # The theory to test
    confidence: float            # Current confidence

    # For pattern
    observation: Optional[str]   # The pattern observed
    supporting_evidence: List[str]

# When curiosity crystallizes → spawn cycle
if curiosity.activation > threshold and curiosity.is_specific_enough():
    cycle = gestalt.spawn_exploration(curiosity)
```

### Proactive Artifact Suggestions

**Parents don't know what they don't know.** Chitta must proactively suggest artifacts when conditions are ripe:

```python
# Chitta evaluates readiness continuously
def check_artifact_readiness(gestalt: LivingGestalt) -> List[Suggestion]:
    suggestions = []

    # Video guidelines - when hypothesis needs observation
    for cycle in gestalt.active_cycles:
        if cycle.curiosity_type == "hypothesis" and cycle.needs_observation():
            suggestions.append(Suggestion(
                type="video_guidelines",
                reason=f"To explore: {cycle.theory}",
                cycle_id=cycle.id
            ))

    # Synthesis report - when enough progress
    if gestalt.has_multiple_completed_cycles() or gestalt.time_since_last_synthesis() > 30:
        suggestions.append(Suggestion(
            type="synthesis_report",
            reason="Enough understanding to synthesize"
        ))

    # Observation guide - when parent is uncertain
    if gestalt.parent_expressed_uncertainty():
        suggestions.append(Suggestion(
            type="observation_guide",
            reason="Help parent know what to notice"
        ))

    return suggestions
```

### Ephemeral vs. Persistent

The app has intermittent interaction. Parents come and go—days between sessions. This shapes what should be chat vs. artifact:

```
EPHEMERAL (Chat Messages)              PERSISTENT (Artifacts in The Space)
"Useful in THIS moment"                "Useful BEYOND this conversation"
─────────────────────────              ─────────────────────────────────
• Clarifications                       • Video guidelines
• Back-and-forth dialogue              • Summaries of understanding
• Emotional acknowledgments            • Reports for professionals
• Questions to gather info             • Recommendations
• Conversational flow                  • Insights to revisit

RULE: If useful beyond this moment → MUST become artifact
```

---

## 4. Understanding: Essence, Facts & Patterns

### The Two Layers of Understanding

Understanding has two complementary layers:

```
┌─────────────────────────────────────────────────────────────────┐
│                         ESSENCE                                  │
│                   (The Whole Child)                              │
│                                                                 │
│     "Daniel is a careful observer who takes the world in        │
│      before he engages. He connects deeply but slowly.          │
│      Music opens him. Safety unlocks his voice."                │
│                                                                 │
│         ▲                    ▲                    ▲              │
│         │                    │                    │              │
│    synthesized          synthesized          synthesized        │
│      from                 from                 from             │
│         │                    │                    │              │
├─────────┴────────────────────┴────────────────────┴─────────────┤
│                         FACTS                                    │
│               (Temporal Observations)                            │
│                                                                 │
│  "speech context-     "music opens      "careful with           │
│   dependent"           connection"       new people"            │
│  (Sep 22→)            (Sep 15→)         (Sep 15→)               │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                        PATTERNS                                  │
│              (Cross-cutting Themes)                              │
│                                                                 │
│  "Safety enables expression across domains"                     │
│  "Sensory pathways are his language of connection"              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Facts** are queryable evidence with temporal validity.
**Patterns** are connections across facts.
**Essence** is the synthesis—the *understanding* that emerges from holding all of it.

### Essence: The Whole Child

The Essence cannot be decomposed into temporal facts. It's Chitta's **felt sense** of who this child is.

```python
class Essence:
    """The holistic sense of who this child is"""

    # The living narrative - who is this child?
    narrative: str                   # Free-form, deepens over time

    # Structured aspects
    core_qualities: List[str]        # "Careful observer", "Deep connector"
    temperament: str                 # "Slow-to-warm, high sensitivity"
    strengths: List[str]             # "Focus", "Visual memory", "Music"
    what_lights_them_up: List[str]   # "Dinosaurs", "Lining things up"
    sensitivities: List[str]         # "Noise", "Pressure to perform"

    # How they move through the world
    approach_style: str              # "Observes before engaging"
    connection_style: str            # "Deep with few, slow with new"

    # Meta
    confidence: float                # How well do we know this child?
    updated_at: datetime
```

**Essence evolves but doesn't have validity periods—it deepens:**

```
Week 1: "Daniel is a quiet child who seems slow to engage."

Week 3: "Daniel is a careful observer. He watches before he acts.
         This isn't shyness—it's how he processes."

Week 6: "Daniel is a deeply perceptive child who takes the world
         in fully before responding. His caution is wisdom—he
         observes, understands, then engages on his own terms.
         Music is his gateway. When safe, he's spontaneous."
```

### Facts: Temporal Observations

Facts are specific observations with **bi-temporal tracking** (inspired by Graphiti):

```python
class TemporalFact:
    """A fact about the child with temporal validity"""

    id: str

    # The fact itself
    subject: str              # "Daniel"
    predicate: str            # "has_difficulty_with"
    object: str               # "speech"
    description: str          # Full natural language

    # Categorization
    aspect: str               # "speech", "motor", "social", "essence"
    fact_type: str            # "observation", "pattern", "confirmed_hypothesis"

    # Temporal validity (when was this TRUE in the world?)
    t_valid: datetime         # When this became true
    t_invalid: Optional[datetime]  # When this stopped being true

    # System tracking (when did WE know this?)
    t_created: datetime       # When we recorded this
    t_expired: Optional[datetime]  # When we updated our knowledge

    # Provenance
    confidence: float
    source_type: str          # "parent_report", "video_analysis", "pattern"
    source_id: str            # Journal entry ID, cycle ID

    # Relationships
    supersedes: Optional[str]     # ID of fact this replaces
    superseded_by: Optional[str]  # ID of fact that replaced this
```

**This enables powerful queries:**

| Question | Query |
|----------|-------|
| "How is Daniel's speech now?" | `facts.where(aspect="speech", t_invalid=None)` |
| "How was it in October?" | `facts.where(aspect="speech", t_valid <= oct, t_invalid > oct)` |
| "How has speech evolved?" | `facts.where(aspect="speech").order_by(t_valid)` |
| "What did we believe that was wrong?" | `facts.where(t_invalid IS NOT NULL)` |

### Patterns: Cross-Cutting Themes

Patterns are observations that connect facts across domains:

```python
class Pattern:
    """A theme that appears across observations"""

    observation: str              # "Safety enables expression"
    supporting_facts: List[str]   # Fact IDs that support this
    domains_touched: List[str]    # ["speech", "social", "play"]

    first_observed_at: datetime
    last_confirmed_at: datetime
    confidence: float
```

### The Complete Understanding Structure

```python
class Understanding:
    """Everything we know about this child"""

    # THE WHOLE (holistic, narrative)
    essence: Essence

    # THE CONTEXT (stable background)
    context: Context              # Family, history, environment

    # THE EVIDENCE (temporal, queryable)
    facts: List[TemporalFact]

    # THE CONNECTIONS (emerging themes)
    patterns: List[Pattern]

    # THE CONCERNS (what brought them here)
    concerns: List[Concern]

    # THE UNKNOWNS (honest gaps)
    open_questions: List[str]
    gaps: List[str]               # What we know we don't know
```

---

## 5. The Journal: Temporal Backbone

### Understanding vs. Journal

**Understanding** = What I know about this child **right now**. (Current state, mutable)

**Journal** = How I came to understand what I understand. (History, immutable)

```
UNDERSTANDING (mutable, current)        JOURNAL (immutable, temporal)
┌────────────────────────────────┐     ┌────────────────────────────────┐
│                                │     │ Sep 15: First met. Speech      │
│  Daniel is a careful observer  │     │   concern. But grandmother     │
│  who needs safety to open up.  │     │   story revealed connection    │
│  Speech emerges when safe.     │     │   capacity...                  │
│                                │     │                                │
│                                │     │ Sep 22: Video showed careful   │
│                                │     │   watching. Not avoidance—     │
│                                │     │   observation.                 │
│                                │     │                                │
│                                │     │ Oct 3: Gan started. Stress →   │
│                                │     │   regression. Aha! Context     │
│                                │     │   matters!                     │
└────────────────────────────────┘     └────────────────────────────────┘
         ▲                                         │
         │         derived from                    │
         └─────────────────────────────────────────┘
```

Understanding is the **destination**. Journal is the **journey**.

### Journal Entry Structure

```python
class JournalEntry:
    """A single entry in the Gestalt's journal"""

    id: str
    timestamp: datetime
    session_id: str

    # What happened
    summary: str                      # Chitta's synthesis of this session

    # What changed
    learned: List[str]                # New information acquired
    updated: Dict[str, str]           # Understanding aspects updated
    patterns_noted: List[str]         # Patterns observed

    # Exploration activity
    cycles_spawned: List[str]         # New explorations started
    cycles_progressed: List[str]      # Evidence added
    cycles_closed: List[str]          # Explorations completed

    # Artifacts
    artifacts_created: List[str]
    artifacts_suggested: List[str]

    # Curiosity state
    curiosities_activated: List[str]
    curiosities_satisfied: List[str]

    # Relational
    parent_state: Optional[str]       # How parent seemed
```

### What the Journal Enables

| Question | Where to look |
|----------|---------------|
| "Who is Daniel?" | Understanding (current) |
| "How did we learn that?" | Journal |
| "What should we explore next?" | Curiosities + Understanding gaps |
| "How has he changed?" | Journal over time + Facts timeline |
| "What do we tell the doctor?" | Understanding (current) |
| "What have we discussed?" | Journal (history) |

### The Flow of Time

```
Session 1 (Sep 15)
    │
    ├── Conversation happens
    ├── Gestalt observes, learns, spawns cycles
    ├── At end: Journal entry created
    │           "First meeting. Learned about Daniel..."
    │
    ▼

Session 2 (Sep 22)
    │
    ├── Chitta opens: References last entry, time gap
    ├── Conversation happens
    ├── Video uploaded, analyzed
    ├── At end: Journal entry created
    │           "Video revealed careful observation..."
    │
    ▼

[2 weeks pass]

    │
    ▼

Session 3 (Oct 3)
    │
    ├── Chitta opens: "It's been two weeks! How are things?"
    ├── Parent shares: Daniel started gan, regression
    ├── Gestalt notices: Pattern! Stress → regression
    ├── At end: Journal entry created
    │
    ▼

[Parent asks: "How has Daniel changed since we started?"]
    │
    ├── Chitta reads journal Sep 15 → Oct 3
    ├── Queries facts timeline for "speech"
    └── Synthesizes the arc naturally
```

---

## 6. Exploration Cycles

### What Is an Exploration Cycle?

An **Exploration Cycle** is a focused investigation spawned by a curiosity. It's the Gestalt's tool for pursuing a specific line of inquiry.

```python
class ExplorationCycle:
    """A focused investigation of a curiosity"""

    id: str
    created_at: datetime
    completed_at: Optional[datetime]

    # What spawned this cycle
    curiosity_type: str          # "discovery" | "question" | "hypothesis" | "pattern"
    focus: str                   # What we're exploring
    spawned_from: str            # Curiosity ID that spawned this

    # The content (depends on type)
    # For hypothesis cycles:
    theory: Optional[str]
    confidence: float

    # For question cycles:
    question: Optional[str]

    # For pattern cycles:
    pattern: Optional[str]

    # Collected during exploration
    evidence: List[Evidence]     # Timestamped observations
    artifacts: List[Artifact]    # Video guidelines, analyses

    # Videos uploaded for this cycle
    videos: List[Video]

    # Lifecycle
    status: str                  # "active" | "evidence_gathering" | "complete"
```

### Cycles Are Asynchronous

**Key Property**: Conversation is NEVER blocked. Cycles run in parallel.

```
Time ─────────────────────────────────────────────────►

Cycle 1 (discovery: essence)
    ████████████████████  ← ongoing foundation building

Cycle 2 (hypothesis: speech context-dependent)
    ░░░░████████░░░░████████  ← active, waiting for video, complete

Cycle 3 (question: grandmother connection)
    ░░░░░░░░████████████████  ← started later, still exploring

Conversation
    ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬  ← NEVER blocked
```

### Evidence-Driven Closure

Cycles close based on evidence, not parent confirmation:

| Trigger | Condition |
|---------|-----------|
| Confidence Threshold | Hypothesis reaches >90% or <10% |
| Question Answered | Sufficient understanding of the question |
| Pattern Confirmed | Pattern holds across multiple observations |
| Staleness | No new evidence for 30+ days |

```python
# Parent is INFORMED, not asked to confirm (avoids authority bias)
# ❌ WRONG: "נראה שהבנתי... האם זה נכון?"
# ✅ CORRECT: "למדתי הרבה על... אם תרצי לחזור לנושא - אני כאן."
```

### When Cycles Close

On completion, cycles become **frozen historical records**:

1. All data becomes immutable
2. Insights extracted → added to Understanding as Facts
3. Journal entry created documenting what was learned
4. If concern resurfaces later → NEW cycle (don't reopen old one)

### Synthesis Reports

When understanding crystallizes across multiple cycles:

```python
class SynthesisReport:
    """Cross-cycle longitudinal view"""

    id: str
    created_at: datetime

    # What this report covers
    cycle_ids: List[str]
    time_span: {start: datetime, end: datetime}

    # Snapshot at report time
    cycle_snapshots: List[CycleSnapshot]

    # The narrative
    content: {
        narrative: str,           # The story of this child
        developments: List[str],  # What changed
        current_focus: str,       # Where we are now
        recommendations: List[str]
    }

    audience: str                 # "parent" | "clinician"
```

Synthesis reports live at **Child level**—they're cross-cycle artifacts.

---

## 7. Conversation Dynamics

### Chitta Initiates

Chitta is not a passive chatbot waiting for input. **Chitta opens** every session based on context:

```python
def compute_session_opening(gestalt: LivingGestalt, session: Session) -> Opening:
    last_entry = gestalt.journal.latest()
    time_gap = now() - last_entry.timestamp

    # What's pending?
    pending_artifacts = gestalt.get_pending_artifacts()  # Videos to upload
    ready_artifacts = gestalt.get_ready_artifacts()      # Analysis complete

    # What's ripe?
    artifact_suggestions = gestalt.compute_artifact_suggestions()

    return Opening(
        reconnection=compute_reconnection(time_gap, last_entry),
        pending_mention=pending_artifacts,
        ready_mention=ready_artifacts,
        proactive_suggestion=artifact_suggestions[0] if any else None,
        continuation=compute_natural_continuation(last_entry)
    )
```

### Example Openings

**After 2 days, nothing pending:**
```
"היי, מה נשמע? חשבתי על מה שסיפרת על דניאל וסבתא.
יש משהו מיוחד בחיבור הזה. איך הוא היום?"
```

**After 1 week, video pending:**
```
"היי! עבר קצת זמן. איך דניאל? איך את?
אגב, הספקת לצלם משהו מהגן? אין לחץ, סתם שואלת."
```

**After 3 days, analysis ready:**
```
"היי! יש לי משהו מעניין. צפיתי בסרטון ששלחת
ויש כמה דברים ששמתי לב אליהם. רוצה לשמוע?"
```

**After 2 weeks, synthesis ready:**
```
"היי, שמחה לראות אותך! אחרי כל מה שלמדתי על דניאל,
אני חושבת שיש לי תמונה די ברורה. רוצה שאכין לך
סיכום? משהו שתוכלי גם לשתף עם הגננת?"
```

### The Decision Flow (Each Turn)

```
┌─────────────────────────────────────────────────────────────────┐
│              CHITTA'S DECISION FLOW (Each Turn)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. RECEIVE                                                     │
│     What did parent say? What's the intent?                     │
│     (Story? Question? Emotion? Answer? Redirect?)               │
│                                                                 │
│  2. RESPOND APPROPRIATELY                                       │
│     Match their energy. Receive what they brought.              │
│     - Story → Reflect, honor, extract meaning                   │
│     - Question → Answer with domain + child-specific knowledge  │
│     - Emotion → Acknowledge, hold space                         │
│     - Answer → Receive, integrate, appreciate                   │
│                                                                 │
│  3. LEARN                                                       │
│     What did I just learn? Update understanding.                │
│     - New information about child                               │
│     - Evidence for active explorations                          │
│     - Patterns forming                                          │
│                                                                 │
│  4. FLOW FORWARD                                                │
│     What's the natural next step?                               │
│     - Follow thread they opened                                 │
│     - Bridge to active curiosity (if natural)                   │
│     - Ask about gap (if relevant)                               │
│     - Simply be present (if they need space)                    │
│                                                                 │
│  DON'T:                                                         │
│     - Interrogate                                               │
│     - List questions                                            │
│     - Force topic changes                                       │
│     - Ignore what they brought                                  │
│     - Hallucinate knowledge                                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### The Bridging Skill

When parent pivots to concern before foundation is built:

```
Parent: "דניאל, בן 3.5, ואני ממש מודאגת מהדיבור שלו."

Chitta DOESN'T say: "ספרי לי על הדיבור."
         (Following too quickly, missing foundation)

Chitta DOESN'T say: "נגיע לזה. קודם ספרי לי מה הוא אוהב."
         (Dismissive, ignores what they brought)

Chitta DOES say: "דניאל, בן 3.5, ואת מודאגת מהדיבור.
                 אני שומעת. נגיע לזה.
                 קודם, עזרי לי להכיר אותו - מה הוא כן אוהב?"

→ Acknowledge → Promise to return → Bridge to what's needed
```

### Stories Are Gold

When parent shares a story, **receive it fully**:

```
Parent: "אתמול משהו קרה - סבתא באה והוא בדרך כלל מתעלם
        ממנה שעה. אבל היא התחילה לזמזם והוא הרים את המבט,
        באמת הסתכל עליה, והביא לה את האוטו האהוב עליו."

Chitta: "וואו. הרגע הזה חשוב.

        הוא שמע את הזמזום, הרים את המבט, באמת הסתכל עליה,
        ואז יזם - הביא לה את האוטו האהוב עליו.
        זה חיבור. זו יוזמה. זה שיתוף.

        המוזיקה פתחה משהו.

        זה אומר לי הרבה על מי שדניאל הוא.
        ספרי לי עוד עליו - מה הוא אוהב מלבד האוטואים?"

→ Receive fully → Reflect meaning → Save it → Bridge forward
```

---

## 8. Tools & Dynamic Context

### The Two-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                LAYER 1: THE GESTALT ENGINE                      │
│                    (Backend, Persistent)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  The "soul" that persists between turns:                        │
│  ├── Understanding (essence, facts, patterns)                  │
│  ├── Curiosities (what we're curious about)                    │
│  ├── Cycles (active explorations)                              │
│  ├── Journal (the story of learning)                           │
│  └── Artifacts (what we've created)                            │
│                                                                 │
│  Computes:                                                      │
│  ├── compute_active_curiosities()                              │
│  ├── compute_turn_guidance(message)                            │
│  └── observe_turn(turn) → updates                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ constructs
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                LAYER 2: THE CONVERSATION AGENT                  │
│                    (LLM, Stateless)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Chitta's "presence" each turn:                                 │
│  ├── Receives dynamic context from Gestalt                     │
│  ├── Responds to parent's message                              │
│  ├── Uses tools to act on understanding                        │
│  └── Returns response + tool calls                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Dynamic Context (Built Each Turn)

```python
class Context:
    """What Chitta knows this turn"""

    # WHO AM I?
    identity: str                     # System identity, voice, principles

    # WHO IS THIS CHILD?
    understanding: RenderedUnderstanding  # Essence, facts, patterns

    # WHAT AM I CURIOUS ABOUT?
    active_curiosities: List[Curiosity]   # Prioritized

    # WHAT AM I EXPLORING?
    active_cycles: List[CycleSummary]     # Current investigations

    # WHAT JUST HAPPENED?
    recent_conversation: List[Turn]       # Last N turns

    # WHAT CAN I DO?
    available_tools: List[Tool]           # Relevant to current state

    # WHAT SHOULD I ATTEND TO?
    turn_guidance: TurnGuidance           # Dynamic guidance for THIS turn
```

### Turn Guidance (The Key Innovation)

Each turn, the Gestalt computes **specific guidance** for Chitta:

```python
class TurnGuidance:
    """What Chitta should attend to THIS turn"""

    # What the parent seems to be doing
    parent_intent: str        # "sharing_story", "asking_question", etc.

    # How to receive this
    reception_guidance: str

    # What I'm curious about that's relevant
    relevant_curiosities: List[str]

    # What I should try to learn (if natural)
    learning_opportunities: List[str]

    # What I should NOT do
    constraints: List[str]

    # Suggested direction (not forced)
    suggested_direction: Optional[str]
```

**Example Turn Guidance:**

```yaml
Turn Guidance (Turn 7):

Parent said: "אתמול משהו קרה - סבתא באה..."

Parent intent: sharing_meaningful_story

Reception guidance: |
  This is GOLD. Receive it fully. Reflect what it reveals.
  The grandmother thread is important - note it as a curiosity.

Relevant curiosities:
  - "Who is Daniel?" → This reveals connection capacity
  - "What makes grandmother different?" (NEW - spawn thread)
  - "Does music open something?" (NEW - hypothesis forming)

Learning opportunities:
  - What was grandmother doing differently?
  - Is music a pattern?

Constraints:
  - Don't rush past this moment
  - Don't immediately ask about other topics
  - Let the story breathe

Suggested direction: |
  Reflect the meaning. Note music as possible key.
  Wonder about grandmother. Then continue naturally.
```

### Tools for Acting on Curiosity

```python
TOOLS = {
    # OBSERVATION - Chitta notices and records
    "observe": {
        "description": "Record something noticed in what parent shared",
        "params": ["observation", "reveals", "curiosities_touched"]
    },

    # CURIOSITY - Chitta pursues understanding
    "spawn_exploration": {
        "description": "Start focused exploration of a curiosity",
        "params": ["curiosity_type", "focus", "initial_content"]
    },

    "add_evidence": {
        "description": "Add evidence to active exploration",
        "params": ["cycle_id", "evidence", "effect"]
    },

    # UNDERSTANDING - Chitta updates her model
    "update_understanding": {
        "description": "Update accumulated understanding",
        "params": ["aspect", "content", "confidence"]
    },

    "add_fact": {
        "description": "Add a temporal fact",
        "params": ["subject", "predicate", "object", "aspect"]
    },

    # ARTIFACTS - Chitta creates persistent outputs
    "suggest_artifact": {
        "description": "Suggest creating an artifact",
        "params": ["type", "reason", "cycle_id"]
    },

    # INTERNAL - Chitta thinks
    "note_pattern": {
        "description": "Note pattern emerging across observations",
        "params": ["pattern", "supporting_observations"]
    },

    "adjust_curiosity": {
        "description": "Adjust curiosity activation",
        "params": ["curiosity", "direction", "reason"]
    }
}
```

### Preventing Hallucination

The LLM can only know what the Gestalt tells it. The context explicitly states:

```yaml
WHAT I KNOW ABOUT DANIEL:
  essence: |
    A careful observer who takes time to warm up.
    Connects through sensory pathways, especially music.

  facts:
    - "speech context-dependent" (Sep 22→, confidence: 0.9)
    - "music opens connection" (Sep 15→, confidence: 0.85)

  patterns:
    - "Safety → openness across domains"

WHAT I DON'T KNOW (gaps):
  - Birth history
  - Siblings
  - Previous evaluations
  - What specifically about speech concerns parent
```

**Chitta can only speak to what's in "WHAT I KNOW" and must be curious about "WHAT I DON'T KNOW."**

---

## 9. Context Cards & The Space

### Context Cards Are Actionable

Cards are not just information displays—they're **entry points to action**.

```
┌─────────────────────────────────────────────────────────────────┐
│  📊 Video Analysis Ready                                        │
│                                                                 │
│  We analyzed Daniel's play video and noticed some              │
│  interesting patterns around fine motor activities.            │
│                                                                 │
│  [View Full Analysis]  [Discuss in Chat]  [Add to Report]      │
└─────────────────────────────────────────────────────────────────┘
```

Clicking any action:
- Opens the relevant artifact, OR
- Injects context into conversation, OR
- Triggers a generation

### Dual Access Model

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│   CONVERSATION                    CARDS                      │
│   ┌──────────────┐               ┌──────────────────┐       │
│   │              │               │ 📹 Upload Video  │       │
│   │  Natural     │               │                  │       │
│   │  dialogue    │←── sync ────→│ We're curious    │       │
│   │  with        │               │ about fine motor │       │
│   │  Chitta      │               │ [Upload Now]     │       │
│   │              │               └──────────────────┘       │
│   │              │               ┌──────────────────┐       │
│   │              │               │ 📄 Report Ready  │       │
│   │              │←── sync ────→│                  │       │
│   │              │               │ [View] [Share]   │       │
│   └──────────────┘               └──────────────────┘       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### The Space: Artifact Organization

All generated artifacts live in **The Space**—an organized area where parents can:

- View current and past reports
- Access video analyses
- See timeline of child's journey
- Share specific artifacts with professionals

```
THE SPACE
├── Reports/
│   ├── Parent Report (Nov 28, 2024) ← current
│   └── Parent Report (Oct 15, 2024) ← previous version
├── Video Analyses/
│   ├── Play Session Analysis (Nov 20)
│   └── Interaction Video Analysis (Nov 5)
├── Guidelines/
│   └── Video Filming Guide (Nov 15)
└── Timeline/
    └── Daniel's Journey (visual timeline)
```

---

## 10. Multilanguage & i18n

### Principle: Language Is Separate from Logic

All user-facing text, LLM guidance, and domain terminology lives in configuration, not code.

### Structure

```
config/i18n/
├── _schema.yaml      # Defines structure and required keys
├── he.yaml           # Hebrew translations
├── en.yaml           # English translations
└── ar.yaml           # Arabic (future)
```

### Usage in Code

```python
# ❌ WRONG - Hardcoded text
def respond_to_blocked_action():
    return "לא ניתן ליצור דוח כרגע"

# ✅ RIGHT - i18n lookup
from app.services.i18n_service import get_i18n

def respond_to_blocked_action(language: str):
    i18n = get_i18n(language)
    return i18n.get(
        "blocked_actions.parent_report.insufficient_understanding",
        completeness=gestalt.completeness,
        required=0.6
    )
```

### LLM Guidance via i18n

Even guidance for the AI is localized:

```yaml
# he.yaml
blocked_actions:
  parent_report:
    insufficient_understanding: |
      **Parent Report**: Cannot generate yet (completeness: {completeness})

      **Your response should**:
      - Acknowledge their request warmly
      - Explain naturally that a meaningful report needs more understanding
      - Look at "What We Still Need" in the Gestalt
      - Continue the conversation in its natural rhythm

      **Tone**: Warm, collaborative. "Let's make sure the report really
      captures [child]" not "I can't do that yet"
```

---

## 11. Domain Separation (Wu Wei)

### The Two Layers

```
┌─────────────────────────────────────────────────────────────────┐
│  DOMAIN LAYER (Configuration)                                   │
│  - Child development concepts                                   │
│  - Clinical workflows                                           │
│  - Specific features                                            │
│  - All text in any language                                     │
│  📝 YAML files + Data schemas                                   │
└─────────────────────────────────────────────────────────────────┘
                     ↓ uses ↓
┌─────────────────────────────────────────────────────────────────┐
│  FRAMEWORK LAYER (Code)                                         │
│  - Prerequisites engine                                         │
│  - Lifecycle processor                                          │
│  - LLM orchestration                                            │
│  - Exploration cycle management                                 │
│  🐍 Python code - KEEP GENERIC                                  │
└─────────────────────────────────────────────────────────────────┘
```

### The Decision Tree

```
Need to add a feature?
│
├─ Is it domain-specific? (e.g., "filming decision", "therapy type")
│  └─ ❌ NO PYTHON CODE
│     ✅ Add to data schema
│     ✅ Configure in YAML
│
└─ Is it a general mechanism? (e.g., "hypothesis lifecycle")
   └─ ✅ YES, modify framework code
      But first: Can existing mechanisms handle it?
```

### Anti-Patterns to Avoid

```python
# ❌ The Premature Enum
class FilmingDecision(Enum):
    WANTS_VIDEOS = "wants_videos"
    REPORT_ONLY = "report_only"

# ✅ Just use strings in configuration
filming_preference: Optional[str] = None  # "wants_videos" | "report_only"
```

```python
# ❌ Domain logic in code
if parent_agreed_to_filming:
    generate_guidelines()
else:
    show_report_option()

# ✅ Domain logic in YAML
# lifecycle_events.yaml
generate_guidelines:
  when:
    filming_preference: "wants_videos"
    has_active_hypothesis: true
  artifact: "video_guidelines"
```

```python
# ❌ Hardcoded text
return "מעולה! בואי נתחיל"

# ✅ i18n lookup
return i18n.get("responses.lets_begin")
```

---

## 12. Practical Development Guide

### Adding a New Feature: Checklist

1. **Is this domain-specific?**
   - [ ] Yes → Use configuration (YAML + schema)
   - [ ] No → Consider framework code (rare)

2. **Does it need new data?**
   - [ ] Add field to appropriate data schema
   - [ ] Document the field's purpose

3. **Does it trigger based on conditions?**
   - [ ] Define in lifecycle_events.yaml
   - [ ] Use prerequisites, not if/else

4. **Does it show UI to user?**
   - [ ] Define in context_cards.yaml
   - [ ] Make actions clickable

5. **Does it involve text?**
   - [ ] Add to i18n YAML files
   - [ ] Support all languages from start

6. **Does it relate to hypotheses?**
   - [ ] Connect it to exploration cycle
   - [ ] Explain WHY, not just WHAT

7. **Does it relate to cycles?**
   - [ ] Determine which cycle it belongs to
   - [ ] Add timestamps for temporal tracking
   - [ ] Consider if artifact should persist in The Space

### Key Files Map

| Category | File | Purpose |
|----------|------|---------|
| **Core Service** | `app/chitta/service.py` | Main conversation orchestration |
| **Cycles** | `app/chitta/cycles.py` | Exploration cycle management |
| **Tools** | `app/chitta/tools.py` | Function definitions for AI |
| **Prompts** | `app/chitta/prompt.py` | System prompt construction |
| **Domain Config** | `config/workflows/lifecycle_events.yaml` | When things happen |
| **Domain Config** | `config/workflows/context_cards.yaml` | What user sees |
| **i18n** | `config/i18n/*.yaml` | All text content |
| **Data Models** | `app/models/child.py` | Child entity with cycles |
| **Data Models** | `app/models/cycle.py` | ExplorationCycle, Hypothesis, Evidence |
| **Data Models** | `app/models/user_session.py` | Session state |

### Development Mantras

```
Before I code, I ask:
  "Can I configure this instead?"

Before I add, I ask:
  "Does this already exist?"

Before I complicate, I ask:
  "What is the minimum needed?"

Before I write text, I ask:
  "Is this in i18n?"

Before I check a threshold, I ask:
  "Should a cycle's hypothesis drive this instead?"

Before I put info in chat, I ask:
  "Will this be useful beyond this moment? → Make it an artifact."

Before I create a hypothesis, I ask:
  "Which cycle does this belong to? One domain = one cycle."
```

### Quality Indicators

**The Gestalt is good when:**
- Reading it, you feel you "know" this child
- Exploration cycles tell a clear temporal story
- Each cycle has a focused domain
- Cross-cycle patterns reveal deeper understanding
- Timestamps enable developmental timeline views

**The conversation is good when:**
- It feels like talking to a knowledgeable friend
- Parents share stories freely
- Questions emerge from curiosity, not checklists
- Parents learn something about their child
- Useful guidance becomes artifacts, not lost in chat

**The code is good when:**
- Domain logic lives in YAML
- Framework code is reusable
- No hardcoded text
- Cycles own their hypotheses
- Artifacts persist what matters
- Every piece of data has timestamps
- Tests verify behavior, not implementation

---

## Summary: The Way of Chitta

1. **Build understanding, not checklists**
   - Stories over forms
   - Patterns over data points
   - Cycles over snapshots

2. **Let curiosity drive**
   - Tools exist to explore, not collect
   - Questions emerge from wonder
   - The conversation never ends

3. **Respect time**
   - Every observation is timestamped
   - Cycles freeze moments of understanding
   - The journey matters as much as current state

4. **Separate concerns**
   - Domain in configuration
   - Framework in code
   - Language in i18n
   - Ephemeral in chat, persistent in artifacts

5. **Trust emergence**
   - Simple components, smart interactions
   - Let patterns reveal themselves across cycles
   - Don't force intelligence, allow it

6. **Be proactively helpful**
   - Parents don't know what they don't know
   - Suggest artifacts when conditions are ripe
   - Persist what matters beyond the conversation

7. **Remember the purpose**
   - Help people see children clearly
   - Support, don't replace professionals
   - Create space for understanding

---

**The water finds its way. We don't need to push it.**

---

*Version: 4.0 - Living Gestalt & Curiosity-Driven Architecture*
*Last updated: December 2025*

*Changes from v3.0:*
- *Gestalt reimagined as the "observing intelligence" rather than a data structure*
- *Replaced hypothesis-driven with curiosity-driven architecture (4 types: Discovery, Question, Hypothesis, Pattern)*
- *Replaced Graphiti with Exploration Cycles for temporal modeling*
- *Added Understanding structure: Essence (holistic) + Facts (temporal, bi-temporal) + Patterns (cross-cutting)*
- *Added Journal as temporal backbone distinct from Understanding*
- *Added two-layer architecture: Gestalt Engine (persistent) + Conversation Agent (stateless LLM)*
- *Added Turn Guidance for dynamic per-turn LLM context*
- *Added Conversation Dynamics: Chitta initiates, bridging skill, stories are gold*
- *Added proactive artifact suggestions*
- *Added ephemeral vs. persistent (intermittent interaction model)*
- *Timestamps everywhere for timeline support*
