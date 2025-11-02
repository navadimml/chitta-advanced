# Chitta + Graphiti: Architecture Integration Guide

## Critical Clarifications First

**Last Updated**: November 2, 2025

---

## 1. Context Cards ARE Actionable

### What I Missed

I incorrectly thought all actions happened through conversation. **Cards are clickable UI elements** that open deep views directly.

### How It Actually Works

```
┌─────────────────────────────────────┐
│  📍 פעיל עכשיו:                    │
│  ┌─────────────────────────────┐   │
│  │ 📄 מדריך להורים         [›]│   │ ← Clickable card
│  │    מוכן לצפייה              │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │ 🔍 מומחים מומלצים       [›]│   │ ← Clickable card
│  │    4 פרופילים             │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘

[User taps "מדריך להורים" card]
→ Opens ParentReportView (deep view)
→ NO conversation needed
```

### Dual Access Model

Every feature has **two entry points**:

1. **Via Conversation**: "Show me the parent report"
2. **Via Context Card**: Tap the "מדריך להורים" card

**Color Coding** indicates card type/urgency:
- 🟢 Green: Completed/Success
- 🟠 Orange: Pending/Needs attention
- 🔵 Blue: Action available
- 🟣 Purple: New/Important
- 🟡 Yellow: Processing

---

## 2. The Missing Critical Feature: Ongoing Consultation

### The Consultation Mode

During the **ongoing partnership** phase (which is 90% of usage), parents need to **consult with Chitta** regularly:

```
Parent: "Yoni had a meltdown today during dinner.
        He threw his plate when I asked him to eat vegetables.
        What should I do?"

Chitta: "אני שומע שהיה קשה היום. בואי נחשוב על זה ביחד.

        מהיומן שלך אני רואה ש-3 מתוך 4 ההתפרצויות האחרונות
        היו קשורות לאוכל. זה יכול להצביע על רגישות חושית
        למרקמים או טעמים מסוימים.

        גם הטיפולית התעסוקתית שלכם ציינה בפגישה האחרונה
        שיוני נוטה להימנע ממרקמים מסוימים.

        כמה דברים שאפשר לנסות:
        1. להציע ירקות במרקם שהוא כבר מכיר ואוהב
        2. לתת לו לגעת ולהריח את הירק לפני שמבקשים לאכול
        3. לא ללחוץ - פשוט לשים על הצלחת ללא ציפייה

        האם תרצי שאכין רשימה מפורטת יותר עם דוגמאות?"

[Context updates:]
┌─────────────────────────────────────┐
│  📍 פעיל עכשיו:                    │
│  🧠 התייעצות פעילה                │
│  📔 הוסף ליומן [לחץ]                │
│  📚 אסטרטגיות למצבי אוכל [›]       │
└─────────────────────────────────────┘
```

**Why This is Critical**:

Chitta has **all the context**:
- Interview history
- Journal entries over months
- Professional recommendations
- Pattern detection across time
- Previous similar situations

Parents don't need to explain everything again. Chitta already knows the child's profile.

### Consultation Entry Points

1. **Via Conversation**: "I need help with..."
2. **Via Context Card**: "🧠 התייעצות עם Chitta" card appears when patterns detected
3. **Via Lightbulb Suggestions**: "💡 שאל את Chitta על..." suggestion

---

## 3. Graphiti Integration: The Game Changer

### Why Graphiti Transforms Chitta

Graphiti solves **three fundamental challenges**:

1. **Temporal Memory**: Track child development over months/years
2. **Pattern Detection**: Automatically identify recurring issues or progress
3. **Context-Aware Retrieval**: When consulting, pull relevant historical context

### The Architecture Shift

**Before (Traditional State Management)**:
```
User State → Redux/Zustand Store → React Components
                ↓
        PostgreSQL Database
```

**After (Graphiti-Powered)**:
```
User Interaction → Graphiti Episodes → Neo4j Knowledge Graph
                        ↓
            Temporal Aware Queries → React Components
```

---

## Graphiti Data Model for Chitta

### Entity Types

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Child(BaseModel):
    """The child being supported."""
    name: str
    age: float
    gender: Optional[str] = None
    primary_concerns: Optional[list[str]] = None

class Parent(BaseModel):
    """The parent/caregiver."""
    relationship: Optional[str] = Field(None, description="Mother, Father, Guardian")
    communication_preferences: Optional[dict] = None

class Professional(BaseModel):
    """A healthcare professional in the care team."""
    specialty: str = Field(..., description="e.g., Speech Therapist, OT, Psychologist")
    name: str
    location: Optional[str] = None

class Observation(BaseModel):
    """A specific observation about the child's behavior."""
    category: str = Field(..., description="e.g., speech, motor, social, sensory")
    description: str
    context: Optional[str] = Field(None, description="When/where it occurred")
    severity: Optional[str] = Field(None, description="mild, moderate, severe")

class Milestone(BaseModel):
    """A developmental milestone achieved."""
    category: str = Field(..., description="speech, motor, social, emotional")
    description: str
    significance: Optional[str] = Field(None, description="major, minor")

class Concern(BaseModel):
    """A reported concern or difficulty."""
    area: str = Field(..., description="attention, communication, behavior, etc.")
    description: str
    impact: Optional[str] = Field(None, description="Impact on daily functioning")
    onset: Optional[datetime] = None

class Report(BaseModel):
    """An assessment report."""
    report_type: str = Field(..., description="parent, professional, summary")
    generated_date: datetime
    key_findings: Optional[list[str]] = None

class Strategy(BaseModel):
    """A coping strategy or intervention."""
    area: str = Field(..., description="Target area: sensory, behavioral, etc.")
    description: str
    effectiveness: Optional[str] = Field(None, description="helpful, neutral, unhelpful")
```

### Edge Types

```python
class HasConcern(BaseModel):
    """Parent reports a concern about Child."""
    first_mentioned: datetime
    frequency: Optional[str] = Field(None, description="daily, weekly, occasional")

class ShowsProgress(BaseModel):
    """Child demonstrates progress in an area."""
    observed_date: datetime
    degree: Optional[str] = Field(None, description="significant, moderate, slight")

class AchievedMilestone(BaseModel):
    """Child achieved a developmental milestone."""
    achieved_date: datetime
    celebrated: Optional[bool] = False

class TreatedBy(BaseModel):
    """Child is being treated by a Professional."""
    start_date: datetime
    frequency: Optional[str] = Field(None, description="2x/week, monthly, etc.")
    status: Optional[str] = Field(None, description="active, completed, planned")

class RecommendedFor(BaseModel):
    """Professional is recommended for Child based on assessment."""
    recommendation_date: datetime
    match_score: Optional[float] = Field(None, description="0.0-1.0")
    rationale: Optional[str] = None

class TriedStrategy(BaseModel):
    """Parent tried a coping strategy."""
    attempted_date: datetime
    outcome: Optional[str] = Field(None, description="helpful, unhelpful, needs more time")

class RelatedTo(BaseModel):
    """Relates two observations or concerns."""
    relationship_type: str = Field(..., description="causes, correlates_with, improves")
    confidence: Optional[float] = Field(None, description="0.0-1.0")
```

### Edge Type Map

```python
edge_type_map = {
    ("Parent", "Child"): ["ParentOf"],
    ("Parent", "Concern"): ["HasConcern"],
    ("Child", "Observation"): ["Exhibited"],
    ("Child", "Milestone"): ["AchievedMilestone"],
    ("Child", "Professional"): ["TreatedBy"],
    ("Professional", "Child"): ["RecommendedFor"],
    ("Parent", "Strategy"): ["TriedStrategy"],
    ("Observation", "Observation"): ["RelatedTo"],
    ("Concern", "Observation"): ["RelatedTo"],
    ("Observation", "Milestone"): ["ProgressToward"],
}
```

---

## Episode-Based Data Ingestion

### Every Interaction is an Episode

```python
from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType
from datetime import datetime

graphiti = Graphiti(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="password"
)

# Example 1: Interview Conversation
await graphiti.add_episode(
    name=f"interview_{child_id}_{timestamp}",
    episode_body="""
    Chitta: מה הגיל של יוני?
    Parent: הוא בן 3 וחצי.
    Chitta: ומה הדאגה העיקרית?
    Parent: הוא לא ממש מדבר. יש לו כמה מילים בודדות אבל לא משפטים.
    Chitta: מתי התחלת לשים לב לזה?
    Parent: בערך לפני חצי שנה, כשראינו שילדים בני גילו כבר מדברים הרבה יותר.
    """,
    source=EpisodeType.message,
    reference_time=datetime.now(),
    group_id=f"family_{parent_id}", # Namespace per family
    entity_types=entity_types,
    edge_types=edge_types,
    edge_type_map=edge_type_map
)

# Example 2: Journal Entry
await graphiti.add_episode(
    name=f"journal_{child_id}_{timestamp}",
    episode_body="Today Yoni said 'I love you' for the first time. I cried happy tears! He was looking right at me when he said it.",
    source=EpisodeType.text,
    reference_time=datetime.now(),
    group_id=f"family_{parent_id}",
    entity_types=entity_types,
    edge_types=edge_types,
    edge_type_map=edge_type_map
)

# Example 3: Professional Recommendation (Structured)
await graphiti.add_episode(
    name=f"expert_match_{child_id}_{timestamp}",
    episode_body={
        "professional": {
            "name": "Dr. Rachel Cohen",
            "specialty": "Speech-Language Pathologist",
            "location": "Tel Aviv",
            "experience_years": 15
        },
        "recommendation": {
            "match_score": 0.92,
            "rationale": "Specializes in early childhood speech delays with sensory integration focus",
            "availability": "2 slots/week",
            "insurance_accepted": True
        }
    },
    source=EpisodeType.json,
    reference_time=datetime.now(),
    group_id=f"family_{parent_id}",
    entity_types=entity_types,
    edge_types=edge_types,
    edge_type_map=edge_type_map
)
```

---

## Temporal Queries: The Power of Graphiti

### Pattern Detection Over Time

```python
# Find all observations related to speech in the last 3 months
speech_observations = await graphiti.search(
    query="observations about speech or talking in the last 3 months",
    group_id=f"family_{parent_id}",
    num_results=20
)

# Detect if there's been consistent progress
progress_pattern = await graphiti.search(
    query="Has there been improvement in speech over time?",
    center_node_uuid=child_node_uuid, # Focus on this specific child
    group_id=f"family_{parent_id}"
)

# Find strategies that were tried for similar concerns
similar_strategies = await graphiti.search(
    query="strategies tried for speech delays",
    group_id=f"family_{parent_id}",
    num_results=10
)
```

### Context-Aware Consultation

When parent asks for help, retrieve relevant context:

```python
async def consult_with_chitta(parent_query: str, child_id: str, parent_id: str):
    # Get child's node UUID
    child_node = await get_child_node(child_id)

    # Search for relevant context, centered on this child
    context = await graphiti.search(
        query=parent_query,
        center_node_uuid=child_node.uuid,
        group_id=f"family_{parent_id}",
        num_results=15
    )

    # Build LLM prompt with retrieved context
    system_prompt = f"""
    You are Chitta, consulting with a parent about their child.

    Context from knowledge graph:
    {format_context_for_llm(context)}

    Provide empathetic, actionable guidance based on this temporal context.
    Reference specific past observations and patterns when relevant.
    """

    # Generate response with context-aware LLM
    response = await llm.generate(
        system_prompt=system_prompt,
        user_message=parent_query
    )

    # Save this consultation as a new episode
    await graphiti.add_episode(
        name=f"consultation_{child_id}_{timestamp}",
        episode_body=f"Parent: {parent_query}\nChitta: {response}",
        source=EpisodeType.message,
        reference_time=datetime.now(),
        group_id=f"family_{parent_id}"
    )

    return response
```

---

## Generating "Active Now" Context Cards

```python
async def generate_active_now_cards(child_id: str, parent_id: str) -> list[ContextCard]:
    child_node = await get_child_node(child_id)

    cards = []

    # Query 1: Check for pending tasks
    pending_tasks = await graphiti.search(
        query="What tasks or actions are pending? What videos need to be uploaded?",
        center_node_uuid=child_node.uuid,
        group_id=f"family_{parent_id}",
        num_results=5
    )

    if has_pending_videos(pending_tasks):
        cards.append(ContextCard(
            icon="📹",
            title="סרטונים להעלאה",
            subtitle=f"נותרו {count_pending_videos(pending_tasks)} סרטונים",
            color="bg-orange-50 border-orange-200",
            action={"type": "view_video_instructions"},
            priority=8
        ))

    # Query 2: Check for new reports
    new_reports = await graphiti.search(
        query="Are there any new reports or assessments that haven't been viewed?",
        center_node_uuid=child_node.uuid,
        group_id=f"family_{parent_id}",
        num_results=3
    )

    if has_new_report(new_reports):
        cards.append(ContextCard(
            icon="🆕",
            title="מדריך חדש מוכן",
            subtitle="מבוסס על הראיון והסרטונים",
            color="bg-purple-50 border-purple-200",
            action={"type": "view_parent_report"},
            priority=9
        ))

    # Query 3: Check for upcoming meetings
    upcoming_meetings = await graphiti.search(
        query="Are there any upcoming meetings with professionals in the next 3 days?",
        center_node_uuid=child_node.uuid,
        group_id=f"family_{parent_id}",
        num_results=5
    )

    if has_upcoming_meeting(upcoming_meetings):
        meeting = extract_meeting_details(upcoming_meetings[0])
        cards.append(ContextCard(
            icon="📅",
            title=f"פגישה עם {meeting['professional']}",
            subtitle=format_meeting_time(meeting['datetime']),
            color="bg-blue-50 border-blue-200",
            action={"type": "prepare_meeting", "meeting_id": meeting['id']},
            priority=10
        ))

    # Query 4: Detect patterns suggesting consultation
    patterns = await graphiti.search(
        query="Are there recurring concerns or patterns in the last 2 weeks that might need attention?",
        center_node_uuid=child_node.uuid,
        group_id=f"family_{parent_id}",
        num_results=10
    )

    if detect_pattern_needing_consultation(patterns):
        cards.append(ContextCard(
            icon="🧠",
            title="Chitta מציע התייעצות",
            subtitle="שמתי לב לדפוס חוזר - בואו נדבר",
            color="bg-cyan-50 border-cyan-200",
            action={"type": "consultation", "pattern": extract_pattern(patterns)},
            priority=7
        ))

    # Sort by priority and return top 4
    return sorted(cards, key=lambda x: x.priority, reverse=True)[:4]
```

---

## Proactive Insights with Graphiti

### Milestone Detection

```python
async def detect_milestones(child_id: str, parent_id: str):
    """
    Automatically detect when a journal entry describes a milestone
    """
    child_node = await get_child_node(child_id)

    # Get recent journal entries
    recent_entries = await graphiti.search(
        query="journal entries from the last 7 days",
        center_node_uuid=child_node.uuid,
        group_id=f"family_{parent_id}",
        num_results=10
    )

    for entry in recent_entries:
        # Use LLM to analyze if this is a milestone
        is_milestone = await llm.classify(
            text=entry.fact,
            prompt="Is this a developmental milestone? Reply YES or NO and explain why."
        )

        if is_milestone.answer == "YES":
            # Add milestone to graph
            milestone_node = MilestoneNode(
                category=is_milestone.category,
                description=entry.fact,
                significance=is_milestone.significance
            )

            await graphiti.add_triplet(
                source_node=child_node,
                edge=AchievedMilestone(
                    achieved_date=entry.reference_time,
                    celebrated=False
                ),
                target_node=milestone_node
            )

            # Send proactive message to parent
            await send_system_message(
                parent_id=parent_id,
                message=f"🎉 זה נראה כמו אבן דרך משמעותית! סימנתי את זה כמיילסטון. {is_milestone.explanation}"
            )
```

### Pattern-Based Suggestions

```python
async def suggest_strategies(child_id: str, parent_id: str, current_concern: str):
    """
    Suggest strategies based on what worked for similar concerns in the past
    """
    child_node = await get_child_node(child_id)

    # Find similar past concerns
    similar_situations = await graphiti.search(
        query=f"past situations similar to: {current_concern}",
        center_node_uuid=child_node.uuid,
        group_id=f"family_{parent_id}",
        num_results=15
    )

    # Find strategies that were tried
    tried_strategies = await graphiti.search(
        query=f"strategies tried for {current_concern} and their outcomes",
        center_node_uuid=child_node.uuid,
        group_id=f"family_{parent_id}",
        num_results=10
    )

    # Analyze which strategies were helpful
    helpful_strategies = [
        s for s in tried_strategies
        if "helpful" in s.fact.lower() or "worked" in s.fact.lower()
    ]

    # Also get recommendations from professionals
    professional_advice = await graphiti.search(
        query=f"professional recommendations for {current_concern}",
        center_node_uuid=child_node.uuid,
        group_id=f"family_{parent_id}",
        num_results=5
    )

    # Generate contextual advice
    context = format_strategies_for_llm(
        similar_situations=similar_situations,
        helpful_strategies=helpful_strategies,
        professional_advice=professional_advice
    )

    response = await llm.generate(
        system_prompt=f"""
        Based on this child's history and what has worked before:
        {context}

        Provide specific, actionable suggestions for: {current_concern}
        Reference past successes and professional guidance.
        """,
        user_message=current_concern
    )

    return response
```

---

## Meeting Preparation with Temporal Context

```python
async def prepare_for_meeting(
    child_id: str,
    parent_id: str,
    professional_id: str,
    meeting_date: datetime
):
    """
    Generate a comprehensive meeting prep summary
    """
    child_node = await get_child_node(child_id)
    professional_node = await get_professional_node(professional_id)

    # Get professional's specialty
    specialty = professional_node.specialty

    # Find all observations relevant to this specialty
    relevant_observations = await graphiti.search(
        query=f"observations and progress related to {specialty} in the last 30 days",
        center_node_uuid=child_node.uuid,
        group_id=f"family_{parent_id}",
        num_results=20
    )

    # Get milestones in this area
    milestones = await graphiti.search(
        query=f"milestones achieved in {specialty} since last meeting",
        center_node_uuid=child_node.uuid,
        group_id=f"family_{parent_id}",
        num_results=10
    )

    # Find previous meeting notes with this professional
    last_meeting = await graphiti.search(
        query=f"last meeting with {professional_node.name}",
        center_node_uuid=child_node.uuid,
        group_id=f"family_{parent_id}",
        num_results=3
    )

    # Generate summary
    context = {
        "professional_name": professional_node.name,
        "specialty": specialty,
        "recent_observations": format_observations(relevant_observations),
        "milestones": format_milestones(milestones),
        "last_meeting_notes": format_last_meeting(last_meeting),
        "days_since_last_meeting": calculate_days_since(last_meeting)
    }

    summary = await llm.generate(
        system_prompt=f"""
        Create a meeting preparation summary for a parent.

        Professional: {context['professional_name']} ({context['specialty']})
        Last meeting was {context['days_since_last_meeting']} days ago.

        Include:
        1. Key updates to share (recent observations and milestones)
        2. Questions to ask based on patterns observed
        3. Topics to discuss (concerns or progress)
        4. Follow-up on recommendations from last meeting

        Context:
        {json.dumps(context, ensure_ascii=False, indent=2)}
        """,
        user_message="Generate meeting preparation summary"
    )

    # Save as episode
    await graphiti.add_episode(
        name=f"meeting_prep_{child_id}_{professional_id}_{timestamp}",
        episode_body=f"Meeting prep summary:\n{summary}",
        source=EpisodeType.text,
        reference_time=datetime.now(),
        group_id=f"family_{parent_id}"
    )

    return summary
```

---

## Architecture Overview

### System Components

```
┌──────────────────────────────────────────────────────┐
│                 Frontend (React)                     │
│  - Conversation UI                                   │
│  - Context Cards (Clickable)                         │
│  - Deep Views                                        │
└──────────────────────────────────────────────────────┘
                        ↕ (REST API / WebSocket)
┌──────────────────────────────────────────────────────┐
│              Backend Services (FastAPI)              │
│  ┌────────────────────────────────────────────────┐ │
│  │ Conversation Service                           │ │
│  │ - Intent recognition                           │ │
│  │ - Function calling                             │ │
│  │ - Context retrieval from Graphiti              │ │
│  └────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────┐ │
│  │ Context Surface Generator                      │ │
│  │ - Queries Graphiti for current state           │ │
│  │ - Generates 2-4 priority cards                 │ │
│  └────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────┐ │
│  │ Consultation Service                           │ │
│  │ - Retrieves temporal context                   │ │
│  │ - Generates context-aware advice               │ │
│  └────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────┐ │
│  │ Pattern Detection Service                      │ │
│  │ - Milestone detection                          │ │
│  │ - Recurring issue identification               │ │
│  └────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
                        ↕
┌──────────────────────────────────────────────────────┐
│           Graphiti + Neo4j Knowledge Graph           │
│  - All conversations (episodes)                      │
│  - All journal entries (episodes)                    │
│  - All observations, milestones, concerns            │
│  - All professional relationships                    │
│  - Temporal queries and pattern detection            │
│  - Namespace per family (group_id)                   │
└──────────────────────────────────────────────────────┘
                        ↕
┌──────────────────────────────────────────────────────┐
│                 LLM (Anthropic Claude)               │
│  - Conversation generation                           │
│  - Entity extraction from episodes                   │
│  - Context-aware consultations                       │
│  - Pattern analysis and insights                     │
└──────────────────────────────────────────────────────┘
```

---

## Implementation Roadmap

### Phase 1: Graphiti Foundation (Weeks 1-2)

**Goals:**
- Set up Neo4j + Graphiti
- Define custom schema (entities + edges)
- Implement episode ingestion for conversations
- Test basic temporal queries

**Deliverables:**
- Working Graphiti instance
- Schema definition file
- Episode ingestion service
- Basic query examples

### Phase 2: Conversation + Context Cards (Weeks 3-4)

**Goals:**
- Conversation service with Graphiti integration
- Context card generation from Graphiti queries
- Clickable cards that open deep views
- Color-coded card types

**Deliverables:**
- ConversationService with Graphiti backend
- ContextSurfaceGenerator service
- Card click handlers
- Updated ContextualSurface.jsx

### Phase 3: Consultation Mode (Weeks 5-6)

**Goals:**
- Implement consultation service
- Context-aware response generation
- Pattern detection for proactive suggestions
- Consultation history tracking

**Deliverables:**
- ConsultationService
- PatternDetectionService
- Consultation UI components
- Proactive suggestion system

### Phase 4: Long-Term Features (Weeks 7-10)

**Goals:**
- Journal with Graphiti episodes
- Milestone auto-detection
- Meeting preparation
- Care team coordination
- Progress tracking over time

**Deliverables:**
- JournalService with Graphiti
- MilestoneDetectionService
- MeetingPrepService
- CareTeamService
- Progress visualization

---

## Key Benefits of Graphiti for Chitta

1. **Temporal Memory**: Child development tracked over months/years
2. **Pattern Detection**: Automatically identify recurring issues or consistent progress
3. **Context-Aware Consultation**: Pull relevant history when advising parents
4. **Relationship Tracking**: Understand connections between observations, strategies, professionals
5. **Privacy**: Complete data isolation per family via `group_id`
6. **Scalability**: Efficient graph queries even with years of data
7. **Flexibility**: Hybrid data (text + JSON + messages)

---

## Next Steps

1. **Set up Graphiti infrastructure**
   - Deploy Neo4j (or FalkorDB)
   - Initialize Graphiti
   - Define custom schema

2. **Build core services**
   - Episode ingestion pipeline
   - Query abstraction layer
   - Context retrieval functions

3. **Integrate with frontend**
   - Update ContextualSurface to use Graphiti queries
   - Implement card click handlers
   - Build consultation interface

4. **Test with real data**
   - Simulate 3-month user journey
   - Validate pattern detection
   - Measure query performance

---

**Graphiti transforms Chitta from a smart chatbot into a truly intelligent companion with perfect memory.**
