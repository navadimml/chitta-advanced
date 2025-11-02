# Chitta + Graphiti: Architecture Integration Guide

## Critical Clarifications First

**Last Updated**: November 2, 2025

---

## 0. Architecture Decisions: Flexibility First

### AI Model Abstraction

**Critical Principle**: The AI models should be **abstracted for easy replacement** in the future.

```python
# services/llm/base.py
from abc import ABC, abstractmethod
from typing import Optional, AsyncIterator
from pydantic import BaseModel

class Message(BaseModel):
    role: str  # "system", "user", "assistant"
    content: str

class LLMResponse(BaseModel):
    content: str
    model: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None

class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers"""

    @abstractmethod
    async def generate(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMResponse:
        """Generate a single response"""
        pass

    @abstractmethod
    async def stream(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream response token by token"""
        pass
```

**Provider Implementations**:

```python
# services/llm/anthropic_provider.py
from anthropic import AsyncAnthropic
from .base import BaseLLMProvider, Message, LLMResponse

class AnthropicProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    async def generate(self, messages: list[Message], temperature: float = 0.7, max_tokens: int = 4096, **kwargs) -> LLMResponse:
        response = await self.client.messages.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in messages if m.role != "system"],
            system=next((m.content for m in messages if m.role == "system"), None),
            temperature=temperature,
            max_tokens=max_tokens
        )
        return LLMResponse(
            content=response.content[0].text,
            model=self.model,
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            finish_reason=response.stop_reason
        )

    async def stream(self, messages: list[Message], temperature: float = 0.7, max_tokens: int = 4096, **kwargs):
        async with self.client.messages.stream(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in messages if m.role != "system"],
            system=next((m.content for m in messages if m.role == "system"), None),
            temperature=temperature,
            max_tokens=max_tokens
        ) as stream:
            async for text in stream.text_stream:
                yield text

# services/llm/openai_provider.py
from openai import AsyncOpenAI
from .base import BaseLLMProvider, Message, LLMResponse

class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def generate(self, messages: list[Message], temperature: float = 0.7, max_tokens: int = 4096, **kwargs) -> LLMResponse:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return LLMResponse(
            content=response.choices[0].message.content,
            model=self.model,
            tokens_used=response.usage.total_tokens,
            finish_reason=response.choices[0].finish_reason
        )

    async def stream(self, messages: list[Message], temperature: float = 0.7, max_tokens: int = 4096, **kwargs):
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
```

**LLM Service Factory**:

```python
# services/llm/factory.py
from typing import Literal
from .base import BaseLLMProvider
from .anthropic_provider import AnthropicProvider
from .openai_provider import OpenAIProvider

LLMProviderType = Literal["anthropic", "openai"]

class LLMFactory:
    @staticmethod
    def create(
        provider: LLMProviderType,
        api_key: str,
        model: Optional[str] = None
    ) -> BaseLLMProvider:
        if provider == "anthropic":
            return AnthropicProvider(api_key, model or "claude-3-5-sonnet-20241022")
        elif provider == "openai":
            return OpenAIProvider(api_key, model or "gpt-4o")
        else:
            raise ValueError(f"Unknown provider: {provider}")

# Usage in application
from services.llm.factory import LLMFactory

llm = LLMFactory.create(
    provider=settings.LLM_PROVIDER,  # From environment variable
    api_key=settings.LLM_API_KEY,
    model=settings.LLM_MODEL
)
```

**Why This Matters**:
- Switch providers via environment variable (no code changes)
- Test with different models easily
- Future-proof as new models emerge
- Can use multiple providers for different tasks (e.g., Claude for conversation, GPT-4 for structured extraction)

### Graph Database Flexibility

**Critical Decision**: The graph database choice is **not finalized yet**.

**Options Under Consideration**:

1. **Neo4j** - Industry standard, mature ecosystem
2. **FalkorDB** - Very fast, resource-efficient, Redis-based

**FalkorDB Advantages**:
- **Speed**: 10x-30x faster for certain query patterns
- **Memory Efficiency**: Uses significantly less RAM than Neo4j
- **Resource Effective**: Critical for scaling the app
- **Redis Integration**: Can leverage Redis ecosystem
- **Cost**: Lower infrastructure costs at scale

**Architecture Must Support Both**:

```python
# services/graph/base.py
from abc import ABC, abstractmethod

class BaseGraphDB(ABC):
    """Abstract interface for graph database operations"""

    @abstractmethod
    async def initialize_graphiti(self, **kwargs):
        """Initialize Graphiti with this graph DB"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if database is healthy"""
        pass
```

**Implementation Example**:

```python
# services/graph/neo4j_adapter.py
from graphiti_core import Graphiti
from .base import BaseGraphDB

class Neo4jAdapter(BaseGraphDB):
    def __init__(self, uri: str, user: str, password: str):
        self.uri = uri
        self.user = user
        self.password = password

    async def initialize_graphiti(self, **kwargs):
        return Graphiti(
            neo4j_uri=self.uri,
            neo4j_user=self.user,
            neo4j_password=self.password,
            **kwargs
        )

    async def health_check(self) -> bool:
        # Neo4j specific health check
        pass

# services/graph/falkordb_adapter.py
from graphiti_core import Graphiti
from .base import BaseGraphDB

class FalkorDBAdapter(BaseGraphDB):
    def __init__(self, host: str, port: int, password: Optional[str] = None):
        self.host = host
        self.port = port
        self.password = password

    async def initialize_graphiti(self, **kwargs):
        # FalkorDB connection for Graphiti
        # Note: Check Graphiti docs for FalkorDB support
        return Graphiti(
            # FalkorDB-specific initialization
            **kwargs
        )

    async def health_check(self) -> bool:
        # FalkorDB specific health check
        pass
```

**Database Selection via Configuration**:

```python
# config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # LLM Configuration
    LLM_PROVIDER: Literal["anthropic", "openai"] = "anthropic"
    LLM_API_KEY: str
    LLM_MODEL: Optional[str] = None

    # Graph Database Configuration
    GRAPH_DB_TYPE: Literal["neo4j", "falkordb"] = "neo4j"
    GRAPH_DB_URI: str
    GRAPH_DB_USER: Optional[str] = None
    GRAPH_DB_PASSWORD: Optional[str] = None

    class Config:
        env_file = ".env"
```

**Why This Matters**:
- Can benchmark Neo4j vs FalkorDB with real data
- Switch databases without code changes
- Optimize for cost vs performance based on scale
- Future-proof for new graph databases

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

    # Generate response with context-aware LLM (using abstraction)
    messages = [
        Message(role="system", content=system_prompt),
        Message(role="user", content=parent_query)
    ]
    llm_response = await llm.generate(messages=messages)
    response = llm_response.content

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
        # Use LLM to analyze if this is a milestone (using abstraction)
        messages = [
            Message(role="system", content="Analyze if this observation is a developmental milestone. Reply in JSON format: {\"is_milestone\": \"YES\" or \"NO\", \"category\": \"speech/motor/social/etc\", \"significance\": \"major/minor\", \"explanation\": \"why this is/isn't a milestone\"}"),
            Message(role="user", content=entry.fact)
        ]
        llm_response = await llm.generate(messages=messages, temperature=0.3)
        is_milestone = json.loads(llm_response.content)

        if is_milestone["is_milestone"] == "YES":
            # Add milestone to graph
            milestone_node = MilestoneNode(
                category=is_milestone["category"],
                description=entry.fact,
                significance=is_milestone["significance"]
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
                message=f"🎉 זה נראה כמו אבן דרך משמעותית! סימנתי את זה כמיילסטון. {is_milestone['explanation']}"
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

    # Generate contextual advice (using abstraction)
    context = format_strategies_for_llm(
        similar_situations=similar_situations,
        helpful_strategies=helpful_strategies,
        professional_advice=professional_advice
    )

    messages = [
        Message(role="system", content=f"""
        Based on this child's history and what has worked before:
        {context}

        Provide specific, actionable suggestions for: {current_concern}
        Reference past successes and professional guidance.
        """),
        Message(role="user", content=current_concern)
    ]
    llm_response = await llm.generate(messages=messages)

    return llm_response.content
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

    # Generate meeting prep summary (using abstraction)
    messages = [
        Message(role="system", content=f"""
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
        """),
        Message(role="user", content="Generate meeting preparation summary")
    ]
    llm_response = await llm.generate(messages=messages)
    summary = llm_response.content

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
│      Graphiti + Graph Database (Neo4j/FalkorDB)      │
│  - All conversations (episodes)                      │
│  - All journal entries (episodes)                    │
│  - All observations, milestones, concerns            │
│  - All professional relationships                    │
│  - Temporal queries and pattern detection            │
│  - Namespace per family (group_id)                   │
│                                                       │
│  Database Choice: Neo4j OR FalkorDB                  │
│  - Neo4j: Mature, feature-rich                       │
│  - FalkorDB: 10x-30x faster, lower memory usage      │
└──────────────────────────────────────────────────────┘
                        ↕
┌──────────────────────────────────────────────────────┐
│              LLM Provider (Abstracted)               │
│  Options: Claude, GPT-4, Gemini, etc.                │
│  - Conversation generation                           │
│  - Entity extraction from episodes                   │
│  - Context-aware consultations                       │
│  - Pattern analysis and insights                     │
│  Switchable via environment variable                 │
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

## Graph Database Comparison: Neo4j vs FalkorDB

### Decision Criteria

The choice between Neo4j and FalkorDB should be based on:
- **Scale**: How many families will use the app?
- **Budget**: Infrastructure costs at scale
- **Performance Requirements**: Query latency expectations
- **Feature Needs**: Do we need advanced Neo4j features?

### Neo4j

**Strengths**:
- ✅ **Mature Ecosystem**: Battle-tested in production
- ✅ **Rich Features**: Graph algorithms, full-text search, APOC procedures
- ✅ **Excellent Tooling**: Neo4j Browser, Bloom visualization, monitoring tools
- ✅ **Large Community**: Extensive documentation, Stack Overflow support
- ✅ **Enterprise Support**: Commercial support options available
- ✅ **Cypher Query Language**: Powerful, expressive graph query language
- ✅ **Graphiti Compatibility**: Official support confirmed

**Weaknesses**:
- ❌ **Memory Usage**: Can consume 4-8GB RAM for moderate datasets
- ❌ **Cost at Scale**: JVM overhead, higher infrastructure costs
- ❌ **Startup Time**: Slower to initialize
- ❌ **Resource Heavy**: Requires dedicated server for production

**Best For**:
- Enterprise deployments with complex graph analytics needs
- Teams comfortable with JVM stack
- When budget isn't a primary constraint
- Need for advanced graph algorithms out of the box

### FalkorDB

**Strengths**:
- ✅ **Speed**: 10x-30x faster for many query patterns (compared to Neo4j)
- ✅ **Memory Efficient**: Uses 50-80% less RAM than Neo4j
- ✅ **Redis-Based**: Can leverage Redis ecosystem (caching, pub/sub)
- ✅ **Fast Startup**: Nearly instant initialization
- ✅ **Cost Effective**: Lower infrastructure costs at scale
- ✅ **Cypher Compatible**: Supports openCypher standard
- ✅ **Lightweight**: Can run on smaller instances

**Weaknesses**:
- ❌ **Newer**: Less battle-tested in production (though stable)
- ❌ **Smaller Community**: Fewer resources, examples, plugins
- ❌ **Graphiti Compatibility**: May require adapter development (check docs)
- ❌ **Fewer Features**: Not all Neo4j advanced features available

**Best For**:
- Startups and scale-ups optimizing for cost
- High-throughput, low-latency requirements
- Already using Redis infrastructure
- Simpler graph queries (most of Chitta's needs)

### Performance Comparison (Estimated)

| Operation | Neo4j | FalkorDB | Winner |
|-----------|-------|----------|---------|
| **Simple read** (e.g., get child profile) | 5-10ms | <1ms | 🏆 FalkorDB |
| **Pattern match** (e.g., find related observations) | 20-50ms | 5-15ms | 🏆 FalkorDB |
| **Deep traversal** (e.g., 4+ hops) | 50-200ms | 10-50ms | 🏆 FalkorDB |
| **Write + index** | 10-30ms | 2-8ms | 🏆 FalkorDB |
| **Complex aggregation** | 100-500ms | 30-150ms | 🏆 FalkorDB |
| **Graph algorithms** (PageRank, etc.) | ✅ Rich library | ⚠️ Limited | 🏆 Neo4j |
| **Full-text search** | ✅ Built-in | ⚠️ Via Redis | 🏆 Neo4j |

### Resource Usage Comparison (Estimated)

**Scenario**: 1,000 active families, 3 months of data each

| Resource | Neo4j | FalkorDB |
|----------|-------|----------|
| **RAM** | 6-8 GB | 1.5-2.5 GB |
| **Disk** | 10-15 GB | 8-12 GB |
| **CPU** (idle) | 5-10% | 1-3% |
| **CPU** (load) | 40-60% | 15-30% |
| **Monthly cost** (AWS) | ~$150-200 | ~$40-60 |

### Recommendation for Chitta

**Start with FalkorDB** for these reasons:

1. **Chitta's Query Patterns Are Simple**:
   - Most queries are 1-3 hop traversals
   - Don't need complex graph algorithms
   - Pattern matching is straightforward

2. **Cost Matters for Long-Term Sustainability**:
   - Each family generates months/years of data
   - 3x-4x cost savings at scale is significant
   - Can host multiple databases on same Redis instance

3. **Performance Is Critical for UX**:
   - Context cards need <100ms generation
   - Consultation responses should be near-instant
   - FalkorDB's speed improves perceived responsiveness

4. **Migration Path Exists**:
   - Both use openCypher (query compatibility)
   - Can export/import graph data if needed
   - Switch later if requirements change

**When to Consider Neo4j Instead**:

- Need advanced graph analytics (e.g., community detection among professionals)
- Team has Neo4j expertise already
- Enterprise client requires Neo4j specifically
- Budget allows for higher infrastructure costs

### Implementation Strategy

**Phase 1**: Build abstraction layer (already designed above)

**Phase 2**: Deploy with FalkorDB initially
```bash
# docker-compose.yml
services:
  falkordb:
    image: falkordb/falkordb:latest
    ports:
      - "6379:6379"
    volumes:
      - falkor_data:/data
    environment:
      - FALKORDB_PASSWORD=your_secure_password
```

**Phase 3**: Benchmark with real data (3-month user simulation)

**Phase 4**: Decide to keep FalkorDB or migrate to Neo4j based on:
- Query performance metrics
- Cost analysis
- Feature needs discovered during testing

**Phase 5**: If migrating to Neo4j, switch adapter in config:
```env
GRAPH_DB_TYPE=neo4j  # Change from "falkordb"
GRAPH_DB_URI=bolt://localhost:7687
```

### Graphiti Compatibility Note

**Important**: Verify Graphiti's support for FalkorDB before finalizing decision:

```python
# Check if Graphiti supports FalkorDB directly
# If not, may need custom adapter:

class FalkorDBGraphitiAdapter:
    """Adapter to use FalkorDB with Graphiti"""

    def __init__(self, redis_client):
        self.redis = redis_client
        self.graph = self.redis.graph("chitta_knowledge_graph")

    async def add_episode(self, episode_data):
        # Convert Graphiti episode format to FalkorDB Cypher queries
        # Execute via FalkorDB's openCypher interface
        pass
```

**Recommendation**: Test Graphiti + FalkorDB integration early in Phase 1.

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

### 1. Build Abstraction Layers (Week 1)

**LLM Abstraction**:
- ✅ Implement `BaseLLMProvider` interface
- ✅ Create `AnthropicProvider` and `OpenAIProvider`
- ✅ Build `LLMFactory` for provider selection
- ✅ Set up environment-based configuration
- 🔧 Test provider switching

**Graph DB Abstraction**:
- ✅ Implement `BaseGraphDB` interface
- ✅ Create `Neo4jAdapter` and `FalkorDBAdapter`
- ✅ Verify Graphiti compatibility with both databases
- 🔧 Set up Docker Compose for local development

### 2. Set up Graphiti Infrastructure (Week 1-2)

**Initial Setup with FalkorDB** (recommended):
```bash
# Start FalkorDB
docker run -p 6379:6379 falkordb/falkordb:latest

# Or with docker-compose
docker-compose up falkordb
```

**Alternative Neo4j Setup**:
```bash
docker run -p 7687:7687 -p 7474:7474 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest
```

**Tasks**:
- Initialize Graphiti with chosen database
- Define custom schema (entities + edges)
- Test basic episode ingestion
- Verify temporal queries work

### 3. Build Core Services (Week 2-3)

**Episode Ingestion Pipeline**:
```python
# services/graphiti_service.py
class GraphitiService:
    def __init__(self, graphiti_client, llm_provider):
        self.graphiti = graphiti_client
        self.llm = llm_provider

    async def ingest_conversation(self, conversation, child_id, parent_id):
        # Convert conversation to episode format
        # Use LLM to extract entities
        # Add to Graphiti
        pass
```

**Query Abstraction Layer**:
- Build high-level query functions
- Wrap Graphiti search with domain-specific methods
- Add caching for frequent queries

**Context Retrieval Functions**:
- `get_child_context(child_id, timeframe)`
- `get_consultation_context(query, child_id)`
- `detect_patterns(child_id, area, timeframe)`

### 4. Integrate with Frontend (Week 3-4)

**Update ContextualSurface**:
- Replace mock data with Graphiti queries
- Implement card generation logic
- Add card click handlers

**Build Consultation Interface**:
- Create ConsultationView component
- Integrate with streaming LLM responses
- Display historical context references

**Deep View Updates**:
- Populate deep views with Graphiti data
- Add temporal navigation (e.g., "show journal from last month")

### 5. Test with Real Data (Week 4-5)

**Simulation**:
- Create realistic 3-month user journey dataset
- Ingest into Graphiti
- Test all query patterns

**Performance Benchmarking**:
- Measure context card generation time (target: <100ms)
- Test consultation response latency
- Monitor memory usage with growing dataset

**Validation**:
- Verify pattern detection accuracy
- Test milestone auto-detection
- Validate consultation quality with historical context

### 6. Decision Point: Database Selection (End of Week 5)

**Metrics to Compare**:
- Query performance (FalkorDB vs Neo4j)
- Resource usage (RAM, CPU, disk)
- Cost estimates at scale (1k, 10k, 100k families)
- Feature gaps (if any)

**Decision**:
- Keep FalkorDB if performance and cost are satisfactory
- Migrate to Neo4j if advanced features are needed
- Document rationale

### 7. Production Readiness (Week 6+)

**Infrastructure**:
- Set up production database cluster
- Configure backups and replication
- Set up monitoring and alerting

**Security**:
- Implement row-level security via `group_id`
- Encrypt sensitive data
- Set up audit logging

**Optimization**:
- Index frequently queried patterns
- Implement query result caching
- Add rate limiting

---

## Environment Configuration Template

```env
# .env.example

# LLM Configuration
LLM_PROVIDER=anthropic  # or "openai"
LLM_API_KEY=sk-ant-xxxxx
LLM_MODEL=claude-3-5-sonnet-20241022  # or "gpt-4o"

# Graph Database Configuration
GRAPH_DB_TYPE=falkordb  # or "neo4j"
GRAPH_DB_URI=localhost:6379  # FalkorDB uses Redis protocol
GRAPH_DB_PASSWORD=your_secure_password

# Alternative for Neo4j:
# GRAPH_DB_TYPE=neo4j
# GRAPH_DB_URI=bolt://localhost:7687
# GRAPH_DB_USER=neo4j
# GRAPH_DB_PASSWORD=password

# Graphiti Configuration
GRAPHITI_EMBEDDING_MODEL=text-embedding-3-small  # For semantic search
GRAPHITI_MAX_CONTEXT_NODES=15

# Application Settings
LOG_LEVEL=INFO
REDIS_CACHE_URL=redis://localhost:6380  # Separate from graph DB
```

---

**Summary**:

Chitta's architecture is designed for **flexibility and future-proofing**:

1. **LLM Abstraction**: Switch between Claude, GPT-4, Gemini via config
2. **Graph DB Abstraction**: Choose Neo4j or FalkorDB based on benchmarks
3. **Graphiti Integration**: Perfect temporal memory for child development
4. **Cost Optimization**: FalkorDB recommended for 3x-4x cost savings
5. **Migration Path**: Can switch providers/databases without code changes

**Graphiti transforms Chitta from a smart chatbot into a truly intelligent companion with perfect memory.**
