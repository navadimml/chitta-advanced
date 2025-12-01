# Chitta: Core Principles & Architecture Guide

**A comprehensive guide for developers joining the Chitta project**

---

## Table of Contents

1. [The Heart of Chitta](#1-the-heart-of-chitta)
2. [The Living Gestalt](#2-the-living-gestalt)
3. [Hypothesis-Driven Architecture](#3-hypothesis-driven-architecture)
4. [The Tool Philosophy](#4-the-tool-philosophy)
5. [Data Architecture](#5-data-architecture)
6. [Temporal Memory with Graphiti](#6-temporal-memory-with-graphiti)
7. [Context Cards & The Space](#7-context-cards--the-space)
8. [Multilanguage & i18n](#8-multilanguage--i18n)
9. [Domain Separation (Wu Wei)](#9-domain-separation-wu-wei)
10. [Practical Development Guide](#10-practical-development-guide)

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

### What Is a Gestalt?

The Gestalt is a **synthesized, whole understanding** of a child that is greater than the sum of its parts. It's not a report or a database—it's a living picture.

### The Six Components of Understanding

```
┌─────────────────────────────────────────────────────────────────┐
│                    THE LIVING GESTALT                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. OBSERVATIONS                                                │
│     Raw data: stories, videos, facts shared by parents          │
│     "Daniel looked at his mom when she called his name"         │
│                                                                 │
│  2. PATTERNS                                                    │
│     Recurring themes across observations                        │
│     "Daniel consistently responds to voices but not to         │
│      environmental sounds"                                      │
│                                                                 │
│  3. HYPOTHESES                                                  │
│     Working theories to explore                                 │
│     "Could Daniel be filtering sounds by social relevance?"     │
│                                                                 │
│  4. EXPLORATIONS                                                │
│     Active investigations of hypotheses                         │
│     "Asked about response to music → loves it, dances"          │
│     "Requested video of response to doorbell → no response"     │
│                                                                 │
│  5. INSIGHTS                                                    │
│     Validated understanding                                     │
│     "Daniel's auditory processing is selective—strong for       │
│      social sounds, weaker for environmental"                   │
│                                                                 │
│  6. OPEN QUESTIONS                                              │
│     What we're still wondering                                  │
│     "How does this affect him in group settings?"               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
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

**New approach (living understanding):**
```python
class LivingGestalt:
    observations: List[Observation]
    patterns: List[Pattern]
    hypotheses: List[Hypothesis]  # Active theories
    explorations: List[Exploration]  # How we're testing them
    insights: List[Insight]  # What we've learned
    open_questions: List[Question]  # What we're still wondering
```

### Completeness Is Misleading

We don't measure "completeness" (as if understanding has an end). Instead, we track:

- **Confidence areas**: Where we have solid understanding
- **Uncertainty areas**: Where we need more observation
- **Emerging patterns**: What's starting to take shape
- **Active hypotheses**: What we're currently exploring

---

## 3. Hypothesis-Driven Architecture

### The Core Insight

**Tools don't exist to fill checkboxes. They exist to explore hypotheses.**

When a pattern emerges from conversation, Chitta forms a hypothesis. This hypothesis creates *curiosity*—a desire to explore. Tools are the means of exploration.

### How Hypotheses Drive Everything

```
┌─────────────────────────────────────────────────────────────────┐
│                    HYPOTHESIS LIFECYCLE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. EMERGENCE                                                   │
│     Pattern detected in conversation or videos                  │
│     "Parent mentioned frustration with blocks three times"      │
│                                                                 │
│  2. FORMATION                                                   │
│     Hypothesis crystalizes                                      │
│     "Daniel may be experiencing fine motor challenges that      │
│      lead to frustration when tasks require precision"          │
│                                                                 │
│  3. EXPLORATION OPTIONS                                         │
│     What tools could help investigate?                          │
│     - Conversation: "How does Daniel handle crayons/puzzles?"   │
│     - Video: "Could you film him during a drawing activity?"    │
│     - Observation: Watch for motor patterns in existing videos  │
│                                                                 │
│  4. ACTIVE EXPLORATION                                          │
│     Tools used, data gathered                                   │
│     - Parent confirms: "Yes, he avoids scissors completely"     │
│     - Video shows: Avoidance of small-piece toys                │
│                                                                 │
│  5. RESOLUTION                                                  │
│     Hypothesis becomes insight OR generates new hypotheses      │
│     Insight: "Fine motor challenges → frustration cycle"        │
│     New hypothesis: "Is this affecting his drawing interest?"   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Tool Readiness via Hypotheses

**Old approach (threshold-based):**
```python
if completeness >= 0.4:
    enable_video_guidelines()  # Magic number!
```

**New approach (hypothesis-based):**
```python
if has_active_hypothesis_needing_observation():
    # We have something specific to explore via video
    enable_video_guidelines(
        focus=active_hypothesis.observation_needs,
        reason=active_hypothesis.why_video_helps
    )
```

### Video Guidelines as Hypothesis Exploration

When we generate video guidelines, we're not just "getting more data." We're specifically asking to observe something related to our current hypotheses.

**Old approach:**
```
Guidelines: "Film Daniel playing alone for 3-5 minutes"
```

**New approach:**
```
Guidelines:
"We've noticed Daniel gets frustrated with blocks and may
avoid precise tasks. To understand better:

1. Film him during a drawing or coloring activity (2-3 min)
   - We're curious about: Does he grip the crayon firmly or
     loosely? Does he press hard? Does he seem frustrated?

2. Film him playing with Lego or puzzles (2-3 min)
   - We're curious about: Does he avoid small pieces? Does he
     ask for help? What happens if a piece doesn't fit?

This will help us understand if there's a pattern around fine
motor activities that we can help with."
```

See the difference? The guidelines **explain the hypothesis** and **what we're looking for**. They're exploration tools, not data collection checklists.

---

## 4. The Tool Philosophy

### Tools Are Real Actions

Every tool in Chitta triggers actual backend operations. The AI decides *when* to use them based on conversation context and active hypotheses.

### The Tool Categories

```python
# 1. UNDERSTANDING TOOLS - Build the Gestalt
update_child_understanding()   # Extract info from conversation
capture_story()                # Capture meaningful moments
detect_milestone()             # Mark significant points

# 2. HYPOTHESIS TOOLS - Form and explore theories
form_hypothesis()              # Crystalize a working theory
explore_hypothesis()           # Initiate investigation

# 3. OBSERVATION TOOLS - Gather specific data
request_video_observation()    # Request targeted video
analyze_video()                # Analyze uploaded video

# 4. GENERATION TOOLS - Create artifacts
generate_video_guidelines()    # Personalized filming guide
generate_parent_report()       # Synthesis of understanding

# 5. QUERY TOOLS - Answer questions
ask_developmental_question()   # Parent asks about development
ask_about_app()                # Parent asks about process
```

### Prerequisites Are Natural Language

We don't use code to block tools. We describe when they're appropriate:

```python
"generate_video_guidelines": {
    "description": """Generate personalized video guidelines.

    Use when:
    - You have active hypotheses that would benefit from observation
    - Parent has shown interest in video observation
    - You can articulate WHAT to film and WHY

    Don't use when:
    - You're just collecting data without specific curiosity
    - Parent prefers conversation-only
    - Guidelines already exist for current hypotheses
    """
}
```

The AI reads this and decides. No state machines required.

---

## 5. Data Architecture

### Child-Centric Model

Everything orbits around the **Child** entity. Understanding accumulates over time, across conversations, across users.

```
┌─────────────────────────────────────────────────────────────────┐
│                           CHILD                                  │
│                   (The invariant core)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  IDENTITY                                                       │
│  ├── name, age, gender                                         │
│  └── birth_date (for age calculation)                          │
│                                                                 │
│  LIVING GESTALT                                                 │
│  ├── observations[]                                            │
│  ├── patterns[]                                                │
│  ├── hypotheses[]                                              │
│  ├── explorations[]                                            │
│  ├── insights[]                                                │
│  └── open_questions[]                                          │
│                                                                 │
│  DEVELOPMENTAL DATA                                             │
│  ├── concerns, strengths                                       │
│  ├── history, family_context                                   │
│  └── parent_goals                                              │
│                                                                 │
│  ARTIFACTS                                                      │
│  ├── video_guidelines                                          │
│  ├── parent_report                                             │
│  └── video_analyses[]                                          │
│                                                                 │
│  MEDIA                                                          │
│  ├── videos[]                                                  │
│  └── journal_entries[] (stories)                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
           │
           │ accessed by
           ▼
┌─────────────────────────────────────────────────────────────────┐
│                       USER SESSION                              │
│              (Per-user interaction context)                     │
├─────────────────────────────────────────────────────────────────┤
│  session_id, user_id, child_id                                 │
│  messages[] (this user's conversation)                         │
│  active_cards[] (UI state)                                     │
│  dismissed_moments{}                                           │
└─────────────────────────────────────────────────────────────────┘
```

### Why Separation Matters

**Mom's session:** Her questions, her UI state, her dismissed cards
**Dad's session:** His questions, his perspective, his UI state
**Child's data:** Unified, complete, built from both conversations

When Dad mentions something Mom already shared, Chitta knows—it's in the Child's Gestalt.

---

## 6. Temporal Memory with Graphiti

### Why Temporal Awareness Matters

Child development unfolds over months and years. A snapshot misses the story. Graphiti gives us:

1. **Temporal Memory**: "Daniel's speech improved significantly between sessions"
2. **Pattern Detection**: "This concern appeared 3 months ago, strengthened over time"
3. **Context-Aware Retrieval**: "What did we observe about motor skills last month?"

### The Knowledge Graph Structure

```
┌────────────────────────────────────────────────────────────────────┐
│                    GRAPHITI KNOWLEDGE GRAPH                        │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ENTITY TYPES                                                      │
│  ├── Child (central node)                                         │
│  ├── DevelopmentalConcern                                         │
│  ├── Strength                                                     │
│  ├── Observation (timestamped)                                    │
│  ├── Hypothesis                                                   │
│  ├── Insight                                                      │
│  ├── Artifact                                                     │
│  └── FamilyMember                                                 │
│                                                                    │
│  EDGE TYPES                                                        │
│  ├── HAS_CONCERN (Child → DevelopmentalConcern)                   │
│  ├── HAS_STRENGTH (Child → Strength)                              │
│  ├── OBSERVED_IN (Observation → Child, timestamped)               │
│  ├── SUPPORTS (Observation → Hypothesis)                          │
│  ├── CONTRADICTS (Observation → Hypothesis)                       │
│  ├── LED_TO (Hypothesis → Insight)                                │
│  ├── GENERATED (Hypothesis → VideoGuidelines)                     │
│  └── RELATED_TO (any → any)                                       │
│                                                                    │
│  TEMPORAL QUERIES                                                  │
│  ├── "Observations about motor skills from last 3 months"         │
│  ├── "How has speech concern evolved over time?"                  │
│  └── "What hypotheses led to current insights?"                   │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Episode-Based Ingestion

Every conversation turn becomes an "episode" in Graphiti:

```python
episode = {
    "source": "conversation",
    "content": "Parent described Daniel responding to music",
    "timestamp": "2024-11-28T10:30:00Z",
    "entities": [
        {"type": "Observation", "content": "responds to music"},
        {"type": "Strength", "content": "auditory engagement"}
    ],
    "edges": [
        {"from": "Daniel", "to": "responds_to_music", "type": "OBSERVED_IN"}
    ]
}
```

### Pattern Detection

Graphiti can detect patterns across time:

```python
# Query: "What patterns emerged in the last month?"
patterns = graphiti.detect_patterns(
    child_id="daniel_123",
    time_window="30d",
    min_observations=3
)

# Result:
# Pattern: "Fine motor avoidance"
#   - Observation 1: "Avoids scissors" (Nov 5)
#   - Observation 2: "Frustrated with blocks" (Nov 12)
#   - Observation 3: "Won't do puzzles" (Nov 20)
#   - Confidence: HIGH
```

---

## 7. Context Cards & The Space

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

## 8. Multilanguage & i18n

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

## 9. Domain Separation (Wu Wei)

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
│  - Graphiti integration                                         │
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

## 10. Practical Development Guide

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
   - [ ] Connect it to hypothesis lifecycle
   - [ ] Explain WHY, not just WHAT

### Key Files Map

| Category | File | Purpose |
|----------|------|---------|
| **Core Service** | `app/chitta/service.py` | Main conversation orchestration |
| **Gestalt** | `app/chitta/gestalt.py` | Child understanding structure |
| **Tools** | `app/chitta/tools.py` | Function definitions for AI |
| **Prompts** | `app/chitta/prompt.py` | System prompt construction |
| **Domain Config** | `config/workflows/lifecycle_events.yaml` | When things happen |
| **Domain Config** | `config/workflows/context_cards.yaml` | What user sees |
| **i18n** | `config/i18n/*.yaml` | All text content |
| **Data Models** | `app/models/child.py` | Child entity |
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
  "Should a hypothesis drive this instead?"
```

### Quality Indicators

**The Gestalt is good when:**
- Reading it, you feel you "know" this child
- Specific stories are captured, not just categories
- Hypotheses explain the "why" of observations
- Open questions drive next conversations

**The conversation is good when:**
- It feels like talking to a knowledgeable friend
- Parents share stories freely
- Questions emerge from curiosity, not checklists
- Parents learn something about their child

**The code is good when:**
- Domain logic lives in YAML
- Framework code is reusable
- No hardcoded text
- Hypotheses drive tool usage
- Tests verify behavior, not implementation

---

## Summary: The Way of Chitta

1. **Build understanding, not checklists**
   - Stories over forms
   - Patterns over data points
   - Hypotheses over thresholds

2. **Let curiosity drive**
   - Tools exist to explore, not collect
   - Questions emerge from wonder
   - The conversation never ends

3. **Separate concerns**
   - Domain in configuration
   - Framework in code
   - Language in i18n

4. **Trust emergence**
   - Simple components, smart interactions
   - Let patterns reveal themselves
   - Don't force intelligence, allow it

5. **Remember the purpose**
   - Help people see children clearly
   - Support, don't replace professionals
   - Create space for understanding

---

**The water finds its way. We don't need to push it.**

---

*Version: 3.0 - Living Gestalt & Hypothesis-Driven Architecture*
*Last updated: November 2024*
