# Living Gestalt Wiring Plan

## Overview

Wire the Living Gestalt model into Chitta, replacing flat `extracted_data` with a flowing, hypothesis-driven system that models change over time.

## Core Philosophy

- **Flow, not stages** - Conversation never ends, continuous relationship
- **Hypotheses, not facts** - Understanding held lightly, updated with evidence
- **Journey, not snapshots** - Track how understanding evolves
- **Two cognitive modes** - Fast conversation, deep reflection in background
- **Distillation, not deletion** - Old messages become structured understanding
- **Cycles, not artifacts** - Artifacts belong to exploration cycles

---

## Data Model

### Evidence

```python
class Evidence(BaseModel):
    """Immutable, timestamped observation."""
    id: str
    observed_at: datetime
    source: str  # "conversation", "video", "parent_update"
    content: str
    domain: Optional[str]
```

### Hypothesis

```python
class Hypothesis(BaseModel):
    """Evolving understanding about the child."""
    id: str
    theory: str  # "Maya struggles with transitions"
    domain: str

    # Evidence chain - the journey
    evidence: List[Evidence] = []

    # Current state
    status: str = "forming"  # "forming", "active", "weakening", "resolved"
    confidence: float = 0.5

    # Timestamps
    formed_at: datetime
    last_evidence_at: datetime

    # Resolution
    resolution: Optional[str] = None  # "confirmed", "refuted", "evolved", "outgrown"
    resolution_note: Optional[str] = None
    evolved_into: Optional[str] = None
```

### Pattern

```python
class Pattern(BaseModel):
    """Emergent theme across hypotheses."""
    id: str
    theme: str
    description: str
    related_hypotheses: List[str]
    confidence: float
    detected_at: datetime
    source: str  # "domain_knowledge", "reflection"
```

### Pending Insight

```python
class PendingInsight(BaseModel):
    """Insight from reflection, to share naturally."""
    id: str
    content: str
    importance: str  # "low", "medium", "high"
    share_when: str  # "next_turn", "when_relevant"
    created_at: datetime
    shared: bool = False
```

### Developmental Understanding

```python
class DevelopmentalUnderstanding(BaseModel):
    """Evolving understanding of this child."""
    hypotheses: List[Hypothesis] = []
    patterns: List[Pattern] = []
    pending_insights: List[PendingInsight] = []

    def active_hypotheses(self) -> List[Hypothesis]:
        return [h for h in self.hypotheses if h.status in ["forming", "active"]]

    def stale_hypotheses(self, days: int = 90) -> List[Hypothesis]:
        cutoff = datetime.now() - timedelta(days=days)
        return [h for h in self.active_hypotheses()
                if h.last_evidence_at < cutoff]

    def journey_for_domain(self, domain: str) -> List[Evidence]:
        relevant = [h for h in self.hypotheses if h.domain == domain]
        all_evidence = []
        for h in relevant:
            all_evidence.extend(h.evidence)
        return sorted(all_evidence, key=lambda e: e.observed_at)
```

---

## Exploration Cycles & Artifacts

Artifacts don't float freely - they belong to exploration cycles.

### Cycle Artifact

```python
class CycleArtifact(BaseModel):
    """Artifact produced within an exploration cycle."""
    id: str
    type: str  # "video_guidelines", "video_analysis", "synthesis_report"
    content: dict  # The actual artifact content

    # State
    status: str  # "draft", "ready", "fulfilled", "superseded", "needs_update"

    # What it's about
    related_hypothesis_ids: List[str]

    # Fulfillment tracking (for guidelines)
    expected_videos: int = 0
    uploaded_videos: int = 0

    # Timestamps
    created_at: datetime

    # Staleness
    superseded_by: Optional[str] = None
    superseded_reason: Optional[str] = None
```

### Exploration Cycle

```python
class ExplorationCycle(BaseModel):
    """A cycle of exploration around specific hypotheses."""
    id: str
    hypothesis_ids: List[str]  # What we're exploring

    # Lifecycle
    status: str  # "active", "evidence_gathering", "synthesizing", "complete"

    # Methods used
    conversation_method: Optional[ConversationMethod] = None
    video_method: Optional[VideoMethod] = None

    # Artifacts produced
    artifacts: List[CycleArtifact] = []

    # Timestamps
    created_at: datetime
    completed_at: Optional[datetime] = None

    def get_artifact(self, artifact_type: str) -> Optional[CycleArtifact]:
        return next((a for a in self.artifacts if a.type == artifact_type), None)

    def active_artifacts(self) -> List[CycleArtifact]:
        return [a for a in self.artifacts if a.status in ["ready", "needs_update"]]
```

### Cycle Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│  ACTIVE                                                      │
│  - Conversation happening                                    │
│  - Building understanding                                    │
│  - No artifacts yet                                          │
└──────────────────────┬──────────────────────────────────────┘
                       │ Enough understanding + parent agrees to video
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  EVIDENCE_GATHERING                                          │
│  - Guidelines artifact created (status: ready)               │
│  - Waiting for video uploads                                 │
│  - Can have needs_update if understanding changes            │
└──────────────────────┬──────────────────────────────────────┘
                       │ All videos uploaded
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  SYNTHESIZING                                                │
│  - Video analysis artifact created                           │
│  - Synthesis happening                                       │
│  - Report being generated                                    │
└──────────────────────┬──────────────────────────────────────┘
                       │ Report ready
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  COMPLETE                                                    │
│  - Synthesis report ready                                    │
│  - Hypotheses updated with evidence                          │
│  - Cycle done (but journey continues...)                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Cards: Derived from Cycle State

Cards reflect what's actionable NOW based on exploration cycles.

### Card Derivation Logic

```python
def derive_cards_from_gestalt(gestalt: Gestalt) -> List[Card]:
    cards = []

    for cycle in gestalt.exploration_cycles:
        cards.extend(derive_cards_for_cycle(cycle))

    # Sort by priority, return top N
    cards = sorted(cards, key=lambda c: c.priority, reverse=True)
    return cards[:4]


def derive_cards_for_cycle(cycle: ExplorationCycle) -> List[Card]:
    cards = []

    if cycle.status == "evidence_gathering":
        guidelines = cycle.get_artifact("video_guidelines")

        if guidelines:
            if guidelines.status == "ready":
                remaining = guidelines.expected_videos - guidelines.uploaded_videos
                if remaining > 0:
                    cards.append(Card(
                        card_id=f"upload_{cycle.id}",
                        title=t("cards.guidelines_ready.title"),
                        subtitle=t("cards.upload_videos.body", videos_remaining=remaining),
                        action="view_guidelines",
                        action_data={"cycle_id": cycle.id, "artifact_id": guidelines.id},
                        priority=9
                    ))

            elif guidelines.status == "needs_update":
                cards.append(Card(
                    card_id=f"updated_{cycle.id}",
                    title="עדכנתי את ההנחיות",
                    subtitle="כדאי להסתכל שוב לפני שממשיכים",
                    action="view_guidelines",
                    action_data={"cycle_id": cycle.id, "artifact_id": guidelines.id},
                    priority=10
                ))

            # superseded = no card (irrelevant)

    elif cycle.status == "synthesizing":
        analysis = cycle.get_artifact("video_analysis")

        if analysis and analysis.status == "ready":
            cards.append(Card(
                card_id=f"analysis_{cycle.id}",
                title="ניתוח הסרטונים מוכן",
                action="view_analysis",
                action_data={"cycle_id": cycle.id, "artifact_id": analysis.id},
                priority=10
            ))

    elif cycle.status == "complete":
        report = cycle.get_artifact("synthesis_report")

        if report and report.status == "ready":
            cards.append(Card(
                card_id=f"report_{cycle.id}",
                title=t("cards.report_ready.title"),
                action="view_report",
                action_data={"cycle_id": cycle.id, "artifact_id": report.id},
                priority=10
            ))

    return cards
```

### Card State Matrix

| Cycle Status | Artifact Type | Artifact Status | Card |
|--------------|---------------|-----------------|------|
| `active` | - | - | (none - still conversing) |
| `evidence_gathering` | guidelines | `ready` | "הנחיות מוכנות" |
| `evidence_gathering` | guidelines | `needs_update` | "עדכנתי הנחיות" |
| `evidence_gathering` | guidelines | `superseded` | (none - irrelevant) |
| `evidence_gathering` | guidelines | `fulfilled` | (none - done) |
| `synthesizing` | analysis | `processing` | "מנתח..." |
| `synthesizing` | analysis | `ready` | "ניתוח מוכן" |
| `complete` | report | `ready` | "דוח מוכן" |
| `complete` | report | `read` | (none - seen) |

---

## Artifact Staleness

When understanding changes, check if artifacts need updating:

```python
def check_artifact_staleness(cycle: ExplorationCycle, child: Child):
    """Check if cycle's artifacts need updating."""
    guidelines = cycle.get_artifact("video_guidelines")

    if not guidelines or guidelines.status in ["fulfilled", "superseded"]:
        return

    # Check if related hypotheses changed
    for hyp_id in guidelines.related_hypothesis_ids:
        hypothesis = child.understanding.get_hypothesis(hyp_id)

        if hypothesis and hypothesis.last_evidence_at > guidelines.created_at:
            if hypothesis.status in ["weakening", "resolved"]:
                guidelines.status = "superseded"
                guidelines.superseded_reason = f"Hypothesis resolved"
                return

    # Check for significant new hypotheses
    new_relevant = [
        h for h in child.understanding.active_hypotheses()
        if h.formed_at > guidelines.created_at
        and h.domain in get_guideline_domains(guidelines)
    ]

    if len(new_relevant) >= 2:
        guidelines.status = "needs_update"
```

---

## Conversation Memory

Gestalt captures child's journey. Memory captures relationship.

```python
class TopicCovered(BaseModel):
    topic: str
    discussed_at: datetime
    depth: str  # "mentioned", "explored", "deep_dive"

class ConversationMemory(BaseModel):
    """What we remember about conversing with this parent."""
    parent_style: Optional[str] = None
    emotional_patterns: Optional[str] = None
    vocabulary_preferences: List[str] = []
    topics_discussed: List[TopicCovered] = []
    rapport_notes: Optional[str] = None
    updated_at: datetime
```

---

## Context Window Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                    LLM Context                              │
├─────────────────────────────────────────────────────────────┤
│  System Prompt                                              │
├─────────────────────────────────────────────────────────────┤
│  Gestalt (Child Understanding)                              │
│  ├── Identity, essence, strengths                           │
│  ├── Active hypotheses with evidence                        │
│  ├── Active exploration cycles                              │
│  ├── Patterns detected                                      │
│  └── Pending insights                                       │
├─────────────────────────────────────────────────────────────┤
│  Conversation Memory (Relationship)                         │
│  ├── Parent's communication style                           │
│  ├── Topics already covered                                 │
│  └── Rapport notes                                          │
├─────────────────────────────────────────────────────────────┤
│  Recent Messages (Sliding Window - last 25)                 │
├─────────────────────────────────────────────────────────────┤
│  Current Message                                            │
└─────────────────────────────────────────────────────────────┘
```

Old messages are **distilled** into:
- Evidence in Hypotheses
- Patterns
- ConversationMemory

---

## Two Cognitive Modes

### Fast Path (Conversation)

```
Parent Message
    │
    ├── Load Child + UserSession
    ├── Build Gestalt
    ├── Build LLM Context (gestalt + memory + recent messages)
    ├── LLM Call (fast model, 1-2 sec)
    ├── Apply tool results
    ├── Queue reflection
    ├── Derive cards from cycles
    └── Return response + cards
```

### Deep Path (Reflection)

```
Reflection Queue
    │
    ├── Collect all pending for same child
    ├── Load Child + Session
    ├── Deep reasoning (30-60 sec)
    │   ├── Pattern detection
    │   ├── Hypothesis updates
    │   ├── Artifact staleness check
    │   └── Memory updates
    └── Save updates
```

---

## Implementation

### ChittaService

```python
class ChittaService:
    def __init__(self):
        self.fast_llm = GeminiFlash()
        self.reflection_queue = ReflectionQueue()

    async def process_message(self, child_id: str, user_id: str, message: str):
        child = await self.state_service.load_child(child_id)
        session = await self.state_service.load_session(user_id, child_id)

        gestalt = build_gestalt(child, session)

        llm_context = self.build_llm_context(
            gestalt=gestalt,
            memory=session.memory,
            recent_messages=session.recent_messages(25),
            current_message=message
        )

        response = await self.fast_llm.process(
            context=llm_context,
            tools=get_conversation_tools()
        )

        for tool_call in response.tool_calls:
            self.apply_tool_result(child, tool_call)

        await self.state_service.save_child(child)
        session.add_message("user", message)
        session.add_message("assistant", response.text)
        await self.state_service.save_session(session)

        await self.reflection_queue.put({
            "child_id": child_id,
            "session_id": session.session_id,
            "trigger_message": message,
            "timestamp": datetime.now()
        })

        cards = derive_cards_from_gestalt(gestalt)

        return ConversationResponse(message=response.text, cards=cards)
```

### ReflectionWorker

```python
class ReflectionWorker:
    def __init__(self):
        self.queue = ReflectionQueue()
        self.reasoning_llm = ClaudeOpus()

    async def run(self):
        while True:
            task = await self.queue.get()
            child_id = task["child_id"]

            # Collect all pending for same child
            all_tasks = [task]
            while not self.queue.empty():
                next_task = self.queue.peek()
                if next_task["child_id"] == child_id:
                    all_tasks.append(await self.queue.get())
                else:
                    break

            await self.reflect(child_id, all_tasks)

    async def reflect(self, child_id: str, tasks: list):
        child = await self.state_service.load_child(child_id)
        session = await self.state_service.load_session_by_id(tasks[0]["session_id"])

        recent_messages = [t["trigger_message"] for t in tasks]

        insights = await self.reasoning_llm.analyze(
            prompt=self.build_reflection_prompt(child, session, recent_messages),
            thinking=True
        )

        # Apply to understanding
        self.apply_understanding_updates(child, insights)

        # Apply to memory
        self.apply_memory_updates(session.memory, insights)

        # Check artifact staleness
        for cycle in child.active_exploration_cycles():
            check_artifact_staleness(cycle, child)

        await self.state_service.save_child(child)
        await self.state_service.save_session(session)
```

---

## Conversation Tools

```python
def get_conversation_tools() -> List[Tool]:
    return [
        Tool(name="add_evidence", ...),
        Tool(name="form_hypothesis", ...),
        Tool(name="quick_note", ...),
        Tool(name="update_identity", ...),
        Tool(name="mark_topic_discussed", ...),
        Tool(name="start_exploration_cycle", ...),
        Tool(name="update_cycle_status", ...),
    ]
```

---

## API: Strip Internal Fields

```python
def prepare_artifact_for_frontend(content: dict) -> dict:
    content = copy.deepcopy(content)
    content.pop("exploration_context", None)

    if "scenarios" in content:
        for scenario in content["scenarios"]:
            scenario.pop("analyst_context", None)

    return content
```

---

## Updated Models

### Child

```python
class Child(BaseModel):
    id: str
    identity: ChildIdentity
    family: FamilyContext
    history: DevelopmentalHistory
    understanding: DevelopmentalUnderstanding
    exploration_cycles: List[ExplorationCycle] = []

    def active_exploration_cycles(self) -> List[ExplorationCycle]:
        return [c for c in self.exploration_cycles if c.status != "complete"]
```

### UserSession

```python
class UserSession(BaseModel):
    session_id: str
    user_id: str
    child_id: str
    messages: List[ConversationMessage] = []
    memory: ConversationMemory
    active_cards: List[ActiveCard] = []
    created_at: datetime
    updated_at: datetime

    def recent_messages(self, n: int = 25) -> List[ConversationMessage]:
        return self.messages[-n:]

    def add_message(self, role: str, content: str):
        self.messages.append(ConversationMessage(role=role, content=content))
        self.updated_at = datetime.now()
        if len(self.messages) > 200:
            self.messages = self.messages[-100:]
```

---

## File Changes

### New Files
- `app/models/understanding.py` - Evidence, Hypothesis, Pattern, PendingInsight
- `app/models/exploration.py` - ExplorationCycle, CycleArtifact
- `app/models/memory.py` - ConversationMemory, TopicCovered
- `app/services/reflection_service.py` - ReflectionWorker
- `app/services/reflection_queue.py` - Queue
- `app/services/card_derivation.py` - derive_cards_from_gestalt

### Modified Files
- `app/models/child.py` - Add understanding, exploration_cycles
- `app/models/user_session.py` - Add memory, sliding window
- `app/chitta/service.py` - Wire everything
- `app/chitta/tools.py` - Cycle management tools
- `app/chitta/prompt.py` - Include cycles in context
- `app/chitta/gestalt.py` - Build from cycles
- `app/api/routes.py` - Use ChittaService

---

## Implementation Order

1. Data models (Evidence, Hypothesis, Pattern)
2. Exploration models (Cycle, CycleArtifact)
3. Memory model (ConversationMemory)
4. Update Child model
5. Update UserSession model
6. Reflection queue + worker
7. ChittaService with context building
8. Card derivation from cycles
9. Wire to routes
10. API transformation

---

## Summary

**Artifacts belong to exploration cycles.**

Cards appear based on:
1. Active cycle exists
2. Cycle has artifact in actionable state
3. Artifact not superseded or fulfilled

When understanding changes:
- Artifacts can become `superseded` (irrelevant)
- Artifacts can become `needs_update` (should regenerate)
- Cards naturally appear/disappear based on state

The journey continues. Multiple cycles can be active. Each cycle has its own artifacts and cards. Nothing is lost - just distilled and organized.
