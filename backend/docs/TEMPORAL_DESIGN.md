# Temporal Design: Exploration Cycles, Hypotheses & Synthesis

> **Purpose**: This document explains how Chitta models the passage of time in child development observation. The app is a never-ending conversation that can span years - we must preserve the narrative of growth, not just current state.

---

## Core Principles

1. **Child development understanding is a journey, not a destination**
2. **Conversation is never blocked** - cycles run in parallel, asynchronously
3. **Each moment in time is preserved** - completed cycles are frozen snapshots
4. **The narrative matters** - synthesis reports tell the longitudinal story

---

## The Exploration Cycle

### Definition

An **Exploration Cycle** is a focused, asynchronous container for exploring a specific aspect of the child's development.

```
Cycle = {
    focus: "What we're exploring" (narrow, domain-specific)
    hypotheses: "Theories about what's happening NOW"
    evidence: "Observations collected"
    artifacts: "Outputs generated (guidelines, analysis)"
    status: active → evidence_gathering → synthesizing → complete
}
```

### Key Properties

1. **Narrow Focus**: Each cycle explores ONE domain/concern cluster
   - Good: "transitions during morning routine"
   - Bad: "everything about Maya"

2. **Asynchronous**: Cycles don't block conversation
   - A cycle can wait for video while conversation continues
   - Multiple cycles run in parallel

3. **Immutable on Completion**: When complete, a cycle becomes a frozen historical record

---

## CRITICAL: One Domain = One Cycle

### The Wrong Model

```python
# ❌ WRONG: One cycle with hypotheses from multiple domains
cycle = {
    id: "c1",
    focus_domain: "behavioral",  # Misleading - contains multiple domains!
    hypotheses: [
        {theory: "difficulty with transitions", domain: "behavioral"},
        {theory: "struggles with peer interaction", domain: "social"},
        {theory: "sensitive to noise", domain: "sensory"}
    ]
}
```

**Problem**: This conflates different clinical phenomena. Transitions, social interaction, and sensory processing are DIFFERENT domains requiring DIFFERENT exploration approaches and DIFFERENT evidence.

### The Correct Model

```python
# ✅ CORRECT: Separate cycle per domain
cycles = [
    {
        id: "c1-transitions",
        focus_domain: "behavioral",
        focus_description: "Morning routine transitions",
        hypotheses: [
            {theory: "difficulty with transitions", domain: "behavioral"}
        ]
    },
    {
        id: "c2-social",
        focus_domain: "social",
        focus_description: "Peer interaction patterns",
        hypotheses: [
            {theory: "struggles with peer interaction", domain: "social"}
        ]
    },
    {
        id: "c3-sensory",
        focus_domain: "sensory",
        focus_description: "Noise sensitivity",
        hypotheses: [
            {theory: "sensitive to noise", domain: "sensory"}
        ]
    }
]
```

### Why Separate Cycles Matter

| Aspect | Multi-Domain Cycle (Wrong) | Domain-Specific Cycles (Correct) |
|--------|---------------------------|----------------------------------|
| Evidence targeting | Generic video for "everything" | Video specific to each domain |
| Closure triggers | When does it close? Confusing | Clear per-domain understanding |
| Cross-cycle patterns | Can't detect patterns across time | "Sensory appears in multiple contexts" becomes visible |
| Longitudinal narrative | One blob of "concerns" | Clear evolution per domain |

### Implementation Rule

When creating cycles or adding hypotheses:

```python
# When parent mentions multiple concerns:
# "בבוקר זה סיוט להוציא אותו. והוא לא משחק עם ילדים אחרים בכלל"

# ❌ WRONG: Add both to one "general" cycle
cycle.add_hypothesis({domain: "behavioral", theory: "transition difficulty"})
cycle.add_hypothesis({domain: "social", theory: "peer interaction"})

# ✅ CORRECT: Create separate cycles
create_cycle(domain="behavioral", focus="Morning transitions")
    .add_hypothesis({domain: "behavioral", theory: "transition difficulty"})

create_cycle(domain="social", focus="Peer interaction")
    .add_hypothesis({domain: "social", theory: "peer interaction"})
```

### When Domains Overlap

If a single observation relates to multiple domains, the EVIDENCE can be shared, but the HYPOTHESES remain in their respective cycles:

```python
# Parent says: "בבוקר כשיש רעש הוא לא יכול לעבור לפעילות אחרת"
# This mentions: sensory (noise) + transitions (activity switch)

# Evidence is shared across cycles:
evidence = {
    content: "Parent reports noise impacts transitions",
    applies_to_cycles: ["c1-transitions", "c3-sensory"]
}

# But each cycle maintains its own hypothesis:
# c1-transitions: "Transitions are difficult" (general)
# c3-sensory: "Sensory triggers affect transitions" (more specific)

# Over time, a PATTERN emerges (at Child level):
pattern = {
    theme: "Sensory input impacts self-regulation",
    supporting_cycles: ["c1-transitions", "c3-sensory"]
}
```

---

### Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│  ACTIVE                                                          │
│  "We're forming theories about motor coordination"               │
│  - Hypotheses being created and refined                         │
│  - Evidence being collected from conversation                    │
│  - Parent sharing observations                                   │
└────────────────────────┬────────────────────────────────────────┘
                         │ Parent agrees to video / guidelines ready
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  EVIDENCE_GATHERING                                              │
│  "We're collecting video observations"                          │
│  ⚡ CONVERSATION CONTINUES - not blocked here                   │
│  - Video guidelines available                                    │
│  - Waiting for parent to film                                   │
│  - Other cycles can be active simultaneously                    │
└────────────────────────┬────────────────────────────────────────┘
                         │ Video uploaded
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  SYNTHESIZING                                                    │
│  "We're analyzing and creating insights"                        │
│  - Video analysis running                                        │
│  - Evidence being processed                                      │
└────────────────────────┬────────────────────────────────────────┘
                         │ Analysis complete
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  COMPLETE (frozen)                                               │
│  "This is what we understood at this point in time"             │
│  - All data immutable                                            │
│  - Hypotheses frozen at their final state                       │
│  - Evidence preserved with timestamps                            │
│  - Can be referenced but never modified                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Parallel Cycles: The Natural Flow

### Real Conversation Example

```
Turn 1 - Parent: "הילד שלי מתקשה במעברים וגם בדיבור"

    → Cycle 1 (transitions): created, active
    → Cycle 2 (speech): created, active

Turn 5 - App suggests video for transitions, parent agrees

    → Cycle 1: moves to evidence_gathering (waiting for video)
    → Cycle 2: still active (conversation continues)

Turn 8 - Parent: "גם שמתי לב שהוא לא אוהב רעשים חזקים"

    → Cycle 3 (sensory): created, active
    → Cycle 1: still waiting for video
    → Cycle 2: still exploring through conversation

Turn 12 - Parent uploads transition video

    → Cycle 1: moves to synthesizing → complete
    → Cycle 2: still active
    → Cycle 3: still active

Turn 20 - Parent requests "show me how Maya is doing"

    → Synthesis Report generated across Cycles 1, 2, 3
```

### Visual Timeline

```
Time ───────────────────────────────────────────────────────────────►

Cycle 1 (transitions)
    ████████░░░░░░░░████████  ← active, waiting, complete

Cycle 2 (speech)
    ░░░░████████████████████████████  ← started later, still active

Cycle 3 (sensory)
    ░░░░░░░░░░░░████████░░░░░░████  ← started later, waiting for video

Conversation
    ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬  ← never blocked
```

---

## Hypotheses: Cycle-Owned, Not Shared

### The Wrong Model (Current)

```python
# ❌ WRONG: Hypotheses as shared, mutable objects
class Child:
    understanding = {
        hypotheses: [  # Flat list, shared across time
            {id: "h1", theory: "motor delay", confidence: 0.7}
        ]
    }
    cycles: [
        {id: "c1", hypothesis_ids: ["h1"]},  # Just a reference
        {id: "c2", hypothesis_ids: ["h1"]},  # Same reference!
    ]
```

**Problem**: When cycle 2 updates the hypothesis, cycle 1's "understanding" changes retroactively. The past is rewritten.

### The Correct Model

```python
# ✅ CORRECT: Hypotheses owned by their cycle
class Child:
    exploration_cycles: [
        {
            id: "c1",
            status: "complete",
            hypotheses: [  # Owned by this cycle, frozen
                {theory: "motor delay", confidence: 0.8}
            ]
        },
        {
            id: "c2",
            status: "active",
            hypotheses: [  # New hypotheses for new cycle
                {theory: "social reciprocity emerging", confidence: 0.6}
            ]
        }
    ]
```

**Benefit**: Each cycle is self-contained. Cycle 1 shows what we understood then. Cycle 2 shows what we're exploring now.

---

## When Concerns Return: New Cycle, New Hypothesis

### Scenario

**Month 1 (Cycle 1)**: Motor concerns
- Hypothesis: "Maya shows motor coordination challenges"
- Resolution: OT recommended, cycle complete

**Month 14 (Cycle 3)**: Motor concerns resurface
- **This is NOT the same hypothesis**
- New hypothesis: "Motor regression during transition stress"
- Different theory, different context, different evidence needed

### Why Separate Hypotheses Matter

| Aspect | "Motor delay" (Cycle 1) | "Motor regression under stress" (Cycle 3) |
|--------|-------------------------|-------------------------------------------|
| Theory | Developmental delay | Stress response |
| Evidence needed | General motor tasks | Motor during/after stressors |
| Intervention | OT for skill building | Stress management + motor support |

These are **fundamentally different clinical pictures**. Treating them as the same hypothesis conflates different phenomena.

---

## Evidence: Cross-Cycle When Appropriate

Evidence is timestamped and immutable, but a single observation can inform multiple cycles:

```python
video_analysis:
    video_id: "morning_routine_v1"
    evidence_items: [
        {
            observation: "transition difficulty at 2:30",
            applies_to_cycles: ["c1-transitions"]
        },
        {
            observation: "covered ears when blender started at 1:45",
            applies_to_cycles: ["c3-sensory"]
        }
    ]
```

One video can provide evidence for multiple parallel cycles.

---

## Two Types of Outputs

### 1. Cycle Artifacts (Cycle-Owned)

Products of a single cycle's exploration:

| Type | Description | Belongs To |
|------|-------------|------------|
| `video_guidelines` | What to film for THIS cycle's hypotheses | One cycle |
| `video_analysis` | Analysis of video for THIS cycle | One cycle |
| `cycle_summary` | What we understood in THIS cycle | One cycle |

These are **frozen with their cycle** when it completes.

### 2. Synthesis Reports (Child-Owned, Cross-Cycle)

Longitudinal views across multiple cycles:

```python
class SynthesisReport:
    id: str
    created_at: datetime

    # What this report covers
    cycle_ids: List[str]  # Which cycles are included
    time_span: {start: datetime, end: datetime}

    # Snapshot of cycle states at report time
    cycle_snapshots: [
        {cycle_id: "c1", status: "complete", key_finding: "..."},
        {cycle_id: "c2", status: "active", current_focus: "..."},
        {cycle_id: "c3", status: "evidence_gathering", waiting_for: "..."},
    ]

    # The narrative
    content: {
        narrative: str,           # The story of this child
        developments: [...],      # What changed
        current_focus: str,       # Where we are now
        recommendations: [...]    # What to consider
    }

    # Metadata
    audience: "parent" | "clinician"
    triggered_by: "scheduled" | "milestone" | "user_request"
```

**Key difference**: Synthesis reports live at the **Child level**, not owned by any single cycle.

---

## Updated Data Model

```
Child
│
├── exploration_cycles: List[ExplorationCycle]
│   │
│   ├── Cycle 1 (complete)
│   │   ├── hypotheses: [owned, frozen]
│   │   ├── evidence: [timestamped]
│   │   └── artifacts: [video_guidelines, video_analysis]
│   │
│   ├── Cycle 2 (active)
│   │   ├── hypotheses: [owned, mutable]
│   │   ├── evidence: [accumulating]
│   │   └── artifacts: []
│   │
│   └── Cycle 3 (evidence_gathering)
│       ├── hypotheses: [owned, mutable]
│       ├── evidence: [waiting for video]
│       └── artifacts: [video_guidelines]
│
├── synthesis_reports: List[SynthesisReport]  # NEW
│   └── Report (Jul 2024)
│       ├── cycle_ids: [c1, c2, c3]
│       └── narrative: "Over the past 6 months..."
│
└── understanding: DevelopmentalUnderstanding
    └── patterns: List[Pattern]  # Cross-cycle observations
        └── "Motor concerns appear during life transitions"
```

---

## Patterns: Cross-Cycle Observations

While hypotheses are cycle-owned, patterns are observations **about** cycles:

```python
Pattern = {
    observation: "Motor concerns appear during life transitions"
    supporting_cycles: ["c1", "c5", "c8"]
    type: "recurring_trigger"
}
```

Patterns live in `child.understanding.patterns` because they are **meta-observations** about the journey, not theories within a cycle.

| Patterns | Hypotheses |
|----------|------------|
| Observations about cycles | Theories within a cycle |
| Cross-temporal | Time-bounded |
| Descriptive | Theoretical |
| Never "resolve" | Can be resolved |

---

## How This Guides Conversation

### The LLM Needs to Know

1. **Active cycles** and their current state
2. **What's pending** (waiting for video, waiting for appointment)
3. **Completed cycles** for context (but not to carry forward hypotheses)
4. **When to start new cycles** (new concern = new cycle)
5. **How to connect evidence** to the right cycle(s)

### Example Conversation Guidance

**Starting a new exploration**:
```
"You mentioned speech concerns. Let me start exploring that with you.
Meanwhile, the video you're preparing for transitions - take your time,
there's no rush."
```

**Cycle completed**:
```
"I've finished analyzing the morning routine video. We learned a lot
about how Maya handles transitions. Would you like me to summarize
what we found?"
```

**Cross-cycle insight**:
```
"I notice that across our conversations, transitions seem to be a
recurring theme - morning routine, going to gan, switching activities.
Would you like to explore that pattern together?"
```

---

## Cycle Closure: Evidence-Driven, Not Parent-Confirmed

### The Authority Bias Problem

Parents tend to agree with AI-based systems due to perceived authority. Asking "Does this match your experience?" creates false confirmation - parents will often agree even if they have reservations.

**Solution**: Parent is INFORMED of conclusions, not asked to CONFIRM them.

### Cycle Closure Triggers

A cycle closes automatically when ANY of these conditions are met:

| Trigger | Condition | Example |
|---------|-----------|---------|
| **Confidence Threshold** | Any hypothesis reaches >90% or <10% | H2 "control issues" hits 92% after 3 supporting evidence pieces |
| **Convergence** | 2+ hypotheses point same direction | Both "transitions" and "control" hypotheses indicate regulation challenges |
| **Staleness** | No new evidence for 30+ days | Cycle on "speech" hasn't had new info in 6 weeks |
| **LLM Soft Trigger** | "Sufficient understanding" reached | ≥70% confidence on lead hypothesis + ≥3 evidence pieces |

### What Happens at Closure

```
When cycle closes:
├── All hypotheses FROZEN at current state
│   ├── Resolved hypotheses: marked with resolution ("confirmed", "refuted", "inconclusive")
│   └── Active hypotheses: frozen as "inconclusive at cycle end"
├── Cycle status → "complete"
├── Completed_at timestamp set
└── Cycle becomes immutable historical record
```

### Parent Communication at Closure

The parent is INFORMED, not asked to confirm:

```
❌ WRONG (asks for confirmation):
   "נראה שהבנתי שהקושי של יואב קשור לתחושת שליטה. האם זה נכון?"

✅ CORRECT (informs):
   "למדתי הרבה על שגרת הבוקר של יואב.
    נראה שהאתגר קשור יותר לתחושת שליטה מאשר למעברים עצמם.
    אם בעתיד תרצי לחזור לנושא הזה - אני כאן."
```

### Parent Reopen Mechanism

If the parent disagrees with a conclusion or wants to revisit:

1. Parent can express renewed concern at any time
2. System creates a NEW cycle (old one stays frozen)
3. New cycle may reference patterns from previous cycles
4. This preserves the temporal narrative - what we understood THEN vs NOW

```
Turn 15: Parent says "אני עדיין מודאגת מהמעברים, משהו השתנה"

System:
├── Cycle 1 (transitions): stays COMPLETE (frozen at month 2)
├── NEW Cycle 4 (transitions-revisited): ACTIVE
│   └── May reference: "Parent expressed renewed concern after 12 months"
└── Conversation continues in new context
```

### Video as Evidence, Not Cycle Driver

**Key principle**: Video analysis is an evidence SOURCE, not a cycle completion trigger.

#### The Wrong Model (Current Implementation)

```python
# ❌ WRONG: Video as state machine driver
# This is the current LINEAR flow:

cycle.status = "active"
    ↓ parent_agrees_to_video()
cycle.status = "evidence_gathering"
    ↓ video_uploaded()
cycle.status = "synthesizing"
    ↓ analysis_complete()
cycle.status = "complete"

# Problem: Video upload FORCES cycle completion
# What if we need more exploration? Too late!
```

#### The Correct Model

```python
# ✅ CORRECT: Video as just another evidence source

# Cycle remains ACTIVE while exploring
cycle.status = "active"

# Parent films video → video analysis produces EVIDENCE
video_analysis = analyze_video(video)
for observation in video_analysis.observations:
    evidence = Evidence(
        content=observation,
        source="video",
        applies_to_cycles=["c1", "c3"]  # Can inform multiple cycles!
    )

    # Evidence feeds into hypothesis confidence
    for cycle_id in evidence.applies_to_cycles:
        cycle = get_cycle(cycle_id)
        for hypothesis in cycle.hypotheses:
            if relevant(evidence, hypothesis):
                hypothesis.add_evidence(evidence, effect="supports")
                # This might push confidence high enough to trigger closure

# Cycle closure is driven by EVIDENCE THRESHOLDS, not video upload
if cycle.check_closure_triggers():  # confidence > 90%?
    cycle.close()
```

#### Evidence Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                      EVIDENCE SOURCES                            │
└──────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
  │ Conversation │      │    Video    │      │ Parent      │
  │ Observations │      │  Analysis   │      │ Updates     │
  └─────────────┘      └─────────────┘      └─────────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              ▼
                    ┌──────────────────┐
                    │  EVIDENCE ITEMS  │
                    │  (timestamped)   │
                    └──────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌─────────┐     ┌─────────┐     ┌─────────┐
        │ Cycle 1 │     │ Cycle 2 │     │ Cycle 3 │
        │ social  │     │ sensory │     │ motor   │
        └─────────┘     └─────────┘     └─────────┘
              │               │               │
              ▼               ▼               ▼
        ┌─────────┐     ┌─────────┐     ┌─────────┐
        │Hypothesis│    │Hypothesis│    │Hypothesis│
        │confidence│    │confidence│    │confidence│
        └─────────┘     └─────────┘     └─────────┘
              │               │               │
              └───────────────┼───────────────┘
                              ▼
                    ┌──────────────────┐
                    │ CLOSURE TRIGGERS │
                    │ • confidence>90% │
                    │ • convergence    │
                    │ • staleness      │
                    └──────────────────┘
```

#### What This Enables

| Scenario | Old (Linear) Model | New (Evidence) Model |
|----------|-------------------|---------------------|
| Need more exploration after video | ❌ Cycle already closed | ✅ Cycle stays active, more evidence gathered |
| Cycle can close without video | ❌ Must wait for video | ✅ Conversation evidence can trigger closure |
| One video informs multiple domains | ❌ Video belongs to one cycle | ✅ Evidence items distributed to relevant cycles |
| Parent provides update without video | ❌ No effect on cycle | ✅ Update becomes evidence, affects confidence |

#### Implementation Implications

1. **Remove linear state machine**: Cycle status should NOT automatically advance on video upload
2. **Video analysis produces evidence items**: Each observation becomes an `Evidence` object
3. **Evidence updates hypothesis confidence**: Same as conversation-based evidence
4. **Closure triggers check all evidence**: Not just "video complete"
5. **Status "evidence_gathering" is OPTIONAL**: Cycle can stay "active" throughout

---

## Summary Table

| Concept | Definition | Ownership | Mutability |
|---------|------------|-----------|------------|
| Exploration Cycle | Focused exploration of one domain | Child | Mutable while active, frozen on complete |
| Hypothesis | Theory about what's happening NOW | Cycle | Mutable within cycle, frozen on complete |
| Evidence | Timestamped observation | Cycle(s) | Always immutable |
| Cycle Artifact | Output of one cycle (guidelines, analysis) | Cycle | Frozen with cycle |
| Synthesis Report | Cross-cycle longitudinal view | Child | Immutable once created |
| Pattern | Cross-cycle observation | Child.understanding | Mutable (grows over time) |
| Cycle Closure | Evidence-driven automatic completion | System | Triggered by thresholds, not parent confirmation |

---

## Design Principles

1. **Time is first-class**: Every piece of understanding is anchored in time
2. **Cycles are asynchronous**: Conversation never blocks on a cycle
3. **Completion freezes**: A completed cycle is a historical record
4. **New concern = new cycle**: Don't reuse old hypotheses for new explorations
5. **Evidence is sacred**: Never modify what was observed
6. **Synthesis is cross-cycle**: Reports tell the longitudinal story
7. **Narrative over snapshot**: The journey matters as much as current state
8. **Inform, don't confirm**: Parent is informed of conclusions, not asked to approve them (avoids authority bias)
9. **Evidence-driven closure**: Cycles close based on confidence thresholds, not parent confirmation
10. **One domain = one cycle**: Each domain (social, sensory, motor, etc.) requires its own exploration cycle
11. **Video is evidence, not workflow**: Video analysis produces evidence items that feed into hypothesis confidence, not a state machine trigger

---

*Document Version: 1.2*
*Last Updated: December 2025*
*Changes:*
- *v1.2: Added "One Domain = One Cycle" section, expanded "Video as Evidence" with implementation details*
- *v1.1: Added cycle closure model (evidence-driven, no parent confirmation)*
