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

## Summary Table

| Concept | Definition | Ownership | Mutability |
|---------|------------|-----------|------------|
| Exploration Cycle | Focused exploration of one domain | Child | Mutable while active, frozen on complete |
| Hypothesis | Theory about what's happening NOW | Cycle | Mutable within cycle, frozen on complete |
| Evidence | Timestamped observation | Cycle(s) | Always immutable |
| Cycle Artifact | Output of one cycle (guidelines, analysis) | Cycle | Frozen with cycle |
| Synthesis Report | Cross-cycle longitudinal view | Child | Immutable once created |
| Pattern | Cross-cycle observation | Child.understanding | Mutable (grows over time) |

---

## Design Principles

1. **Time is first-class**: Every piece of understanding is anchored in time
2. **Cycles are asynchronous**: Conversation never blocks on a cycle
3. **Completion freezes**: A completed cycle is a historical record
4. **New concern = new cycle**: Don't reuse old hypotheses for new explorations
5. **Evidence is sacred**: Never modify what was observed
6. **Synthesis is cross-cycle**: Reports tell the longitudinal story
7. **Narrative over snapshot**: The journey matters as much as current state

---

*Document Version: 1.0*
*Last Updated: December 2024*
