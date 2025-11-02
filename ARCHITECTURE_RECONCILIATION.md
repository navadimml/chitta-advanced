# Chitta Architecture: Reconciling Structure with Conversation-First

**The Core Challenge**: How to maintain a conversation-first interface while respecting technical dependencies in the screening process.

---

## The Fundamental Insight

The tension isn't "conversation-first OR stage-based" - it's that **Chitta has two modes**:

1. **Screening Mode** (Structured): Interview → Videos → Analysis → Reports
   - **Dependencies are technical, not arbitrary**
   - Can't generate video instructions without interview data
   - Can't analyze videos that don't exist
   - These are REAL constraints, not just UI flow

2. **Companion Mode** (Open): Ongoing support after screening
   - Journal anytime
   - Consult whenever needed
   - No linear path

**The mistake in current code**: Treating technical dependencies as "UI stages" instead of "backend prerequisites".

---

## The Right Mental Model

### NOT: Stage Machine (Current Code)
```
Frontend: if (stage === 'video_upload') { showUploadUI(); }
```
❌ Problem: Frontend controls flow, feels like a wizard

### NOT: Pure Conversation (Naive Interpretation)
```
User: "Show me my report"
AI: "Here it is!" [but no data exists yet]
```
❌ Problem: Ignores technical realities

### YES: Conversation Over Prerequisite Graph
```
Backend: Maintains dependency graph
User: Can ask for anything
AI: Understands intent + checks prerequisites
  ↓
If possible: Facilitates action
If not yet: Explains + offers path forward
  ↓
Context Cards: Show what's currently actionable
```
✅ This respects both conversation-first AND technical constraints

---

## The Architecture

### 1. **Prerequisite Graph** (Backend, Not "Stages")

Think of it as a **capability dependency graph**, not a linear workflow:

```python
# Not stages, but prerequisites
PREREQUISITES = {
    'generate_video_instructions': {
        'requires': ['interview_complete'],
        'data_needed': ['child_profile', 'concerns', 'age']
    },
    'upload_video': {
        'requires': ['video_instructions_generated'],
        'provides': ['video_available']
    },
    'analyze_videos': {
        'requires': ['interview_complete', 'videos_uploaded'],
        'minimum_videos': 3,
        'provides': ['analysis_complete']
    },
    'view_reports': {
        'requires': ['analysis_complete'],
        'provides': ['reports_available']
    },
    # These have minimal prerequisites
    'consultation': {
        'requires': [], # Always available
        'enhanced_by': ['interview_complete', 'reports_available']
    },
    'journal_entry': {
        'requires': [], # Always available
    }
}
```

**Key Insight**: These aren't UI states - they're **data dependencies**. The graph lives in the backend and is invisible to the user.

---

### 2. **Intent Router** (Backend LLM-Based)

Understands what the user wants from natural language:

```python
async def route_intent(user_message: str, context: dict) -> Intent:
    """
    Use LLM to understand user intent, then check prerequisites
    """
    # LLM with function calling
    intent = await llm.extract_intent(
        message=user_message,
        context=context,
        functions=[
            "upload_video",
            "view_report",
            "ask_question",
            "journal_entry",
            "continue_interview",
            # ... all possible intents
        ]
    )

    # Check if action is possible
    if intent.action:
        can_do, missing = check_prerequisites(intent.action, context)
        intent.feasible = can_do
        intent.missing_prerequisites = missing

    return intent
```

**Example**:
```
User: "I want to see my child's report"
↓
Intent: { action: "view_report", feasible: False, missing: ["analysis_complete"] }
↓
AI Response: "I'm working on your report! To complete it, I need to analyze the videos. Have you uploaded all 3 videos yet?"
↓
Context Cards: [Upload Video 1, Upload Video 2, Upload Video 3]
```

---

### 3. **Conversation Controller** (Backend LLM)

Generates appropriate responses based on intent + feasibility:

```python
async def generate_response(intent: Intent, context: dict) -> Response:
    """
    Generate contextual response based on what's possible
    """
    if intent.feasible:
        # User can do this - facilitate it
        return await facilitate_action(intent, context)

    else:
        # User can't do this yet - explain gracefully
        return await explain_and_guide(intent, context)


async def explain_and_guide(intent: Intent, context: dict) -> Response:
    """
    Gracefully handle impossible requests
    """
    # Build explanation prompt
    prompt = f"""
    User wants to: {intent.action}
    Missing prerequisites: {intent.missing_prerequisites}
    Current state: {context.summary}

    Generate a warm, helpful response that:
    1. Acknowledges their request
    2. Explains what's needed first (naturally, not technically)
    3. Offers to help them get there
    4. Suggests concrete next step
    """

    response = await llm.generate(prompt, context)

    # Generate relevant context cards
    cards = await generate_cards_for_prerequisites(
        intent.missing_prerequisites,
        context
    )

    return {
        "response": response,
        "cards": cards,
        "suggestions": ["Continue interview", "Ask a question"]
    }
```

**Examples**:

```
User: "Upload video" [interview not done]
→ AI: "I'd love to see [child name] in action! First, let me understand their development with a few questions. What's [child name]'s age?"
→ Cards: [Continue Interview]

User: "See my report" [videos not analyzed]
→ AI: "Your report is almost ready! I'm analyzing the videos now (usually 24h). Want to add observations to [child]'s journal while we wait?"
→ Cards: [Journal, Timeline, Check Status]

User: "I have a question" [anytime]
→ AI: "Of course! What's on your mind?"
→ Cards: [Common Questions, Journal, Resources]
```

---

### 4. **Context Card Generator** (Backend AI)

Dynamically generates 2-4 cards based on current possibilities:

```python
async def generate_context_cards(context: dict) -> List[Card]:
    """
    AI-curated cards showing what's most relevant RIGHT NOW
    """
    # Get what's currently possible
    possible_actions = get_available_actions(context)

    # Get recent activity from Graphiti
    recent_context = await graphiti.search(
        query="recent activities and pending actions",
        center_node=child_node,
        num_results=10
    )

    # LLM decides what's most relevant
    cards_prompt = f"""
    Based on user state and recent activity, generate 2-4 context cards.

    Available actions: {possible_actions}
    Recent context: {recent_context}

    Prioritize:
    1. Blocking prerequisites (must do to progress)
    2. Time-sensitive items (analysis complete, new report)
    3. Ongoing activities (journal with recent entries)
    4. Helpful resources

    Return max 4 cards, most important first.
    """

    cards = await llm.generate_structured(cards_prompt, CardSchema)

    return cards[:4]  # Never more than 4
```

**Dynamic Examples**:

```
State: Interview 80% done
Cards:
  1. [Continue Interview] - "Just a few more questions"
  2. [Ask Question] - "Have a concern? Ask me"

State: Interview done, no videos
Cards:
  1. [View Video Guidelines] - "See what to film"
  2. [Upload Video] - "Ready to record?"
  3. [Journal Entry] - "Add daily observations"

State: All videos uploaded, analyzing
Cards:
  1. [Processing] - "Analysis in progress (~22h left)"
  2. [Journal] - "3 entries this week"
  3. [Consultation] - "Have questions? Ask me"

State: Reports ready
Cards:
  1. [NEW: Parent Report] - "Your guide is ready!"
  2. [Professional Report] - "For specialists"
  3. [Find Experts] - "Based on findings"
  4. [Journal] - "Continue tracking progress"
```

---

### 5. **Frontend** (Minimal, Trusts Backend)

```javascript
async function handleSend(message) {
  // Send to backend
  const response = await api.sendMessage(familyId, message);

  // Just render what backend says
  setMessages(prev => [...prev,
    { sender: 'user', text: message },
    { sender: 'chitta', text: response.response }
  ]);

  // Update context cards (AI-curated by backend)
  setCards(response.cards);

  // Update suggestions
  setSuggestions(response.suggestions);
}
```

**No stage management. No completion checking. Just render.**

---

## Example: Complete User Journey

### Scenario 1: User Jumps Ahead

```
[State: Interview 30% done]

User: "I want to see my report now"

Backend:
  1. Intent Router: extract_intent() → "view_report"
  2. Check Prerequisites: Missing ["interview_complete", "videos_analyzed"]
  3. Conversation Controller: explain_and_guide()

AI: "I'm excited to create your personalized report! To do that well, I need to understand [child name] better. We've covered age and speech concerns - can you tell me about [his/her] social interactions?"

Cards:
  [Continue Interview] "3-5 more minutes"
  [Why These Questions?] "Understanding our process"

User: [continues conversation naturally]
```

---

### Scenario 2: Prerequisites Met

```
[State: Interview done, guidelines generated, 0 videos]

User: "What should I do next?"

Backend:
  1. Intent Router: "request_guidance"
  2. Check State: interview_complete=True, videos=0
  3. Generate Cards: Most relevant actions

AI: "Great progress! I've created 3 personalized filming scenarios for [child name]. Each one helps me see different aspects of [his/her] development. Ready to start with the first one?"

Cards:
  [Scenario 1: Free Play] "3-5 min | Most important"
  [Scenario 2: Mealtime] "3-5 min"
  [Scenario 3: Focused Activity] "3-5 min"

User: [clicks card or says "yes"]
```

---

### Scenario 3: Consultation (Always Available)

```
[State: Any - even during interview]

User: "Is it normal for a 3-year-old to not use full sentences?"

Backend:
  1. Intent Router: "ask_question" (no prerequisites needed!)
  2. Graphiti: Retrieve context (if any exists)
  3. LLM: Generate informed answer

AI: "That's a great question! At 3, there's a wide range of normal. Some children are using 3-4 word phrases, others are making short sentences. What you're describing isn't automatically concerning, but it's worth noticing. Tell me more - does [child name] use any 2-word combinations?"

Cards:
  [Continue Conversation]
  [Add to Journal] "Track this observation"

[Conversation continues naturally, doesn't interrupt screening flow]
```

---

## The Razor-Sharp Principle

> **"The conversation is primary. Technical dependencies are respected through graceful AI guidance, not by blocking the user. The backend maintains a prerequisite graph, the LLM understands intent and feasibility, and the UI simply reflects what's currently relevant."**

---

## Architecture Comparison

### ❌ Current Code (Stage Machine)
```
Frontend decides: if (stage === 'X') { show Y }
User: Forced through linear path
AI: Just answers within current stage
```

### ✅ Proposed (Conversation Over Prerequisites)
```
Backend knows: What's technically possible right now
User: Can say/ask anything
AI: Routes intent, checks feasibility, responds naturally
Frontend: Renders conversation + AI-curated cards
```

---

## Implementation Strategy

### Phase 1: Backend Enhancement (2 weeks)

1. **Build Prerequisite Graph**
```python
# services/prerequisites.py
def check_can_do(action: str, context: dict) -> Tuple[bool, List[str]]:
    """Returns (feasible, missing_prerequisites)"""
```

2. **Add Intent Router**
```python
# services/intent_router.py
async def route_intent(message: str, context: dict) -> Intent:
    """LLM-based intent extraction + feasibility check"""
```

3. **Enhance Conversation Controller**
```python
# Already exists, enhance to use intent + prerequisites
```

4. **Dynamic Card Generation**
```python
# services/card_generator.py
async def generate_cards(context: dict) -> List[Card]:
    """AI-curated cards based on current possibilities"""
```

### Phase 2: Frontend Simplification (1 week)

1. **Remove Stage Management**
   - Delete `JourneyEngine.js`
   - Remove `setStage()` calls
   - Trust backend entirely

2. **Simplify App.jsx**
```javascript
// Just conversation + cards, no stage logic
const response = await api.sendMessage(message);
setMessages(prev => [...prev, userMsg, assistantMsg]);
setCards(response.cards); // Backend decides
```

3. **Keep UI Components** (they're perfect)
   - ContextualSurface
   - ConversationTranscript
   - DeepViewManager
   - All animations and styles

### Phase 3: Graphiti Integration (1-2 weeks)

- Replace localStorage with Graphiti episodes
- Backend becomes single source of truth
- Multi-device support automatic

---

## Testing the Philosophy

**Good Test**: Can the user have this conversation?

```
User: "My child just said 'I love you' for the first time!"
AI: "That's wonderful! What a special moment 🥰 Would you like to add this to [child]'s journal?"
[Even if in middle of interview - conversation should handle this]
```

**Another Test**: Does blocking feel natural?

```
User: "Show me the report"
AI: [interview not done]

Bad: "Error: Cannot access reports in stage 1"
Good: "I can't wait to create your report! First, let me get to know [child] - tell me about [him/her]?"
```

If the AI's explanation feels natural and helpful (not restrictive), we've succeeded.

---

## Summary

**The Solution**: Not stage machine OR conversation-first, but **conversation-first interface over a prerequisite graph**.

- Backend tracks what's technically possible (dependency graph)
- LLM understands user intent from natural language
- AI checks feasibility and responds gracefully
- Context cards show what's currently actionable
- User never feels blocked, just guided naturally

**This respects both**:
- ✅ Technical dependencies (can't analyze non-existent videos)
- ✅ Conversation-first (user can ask/do anything, AI guides)
- ✅ AI-curated (backend decides cards, not hardcoded)
- ✅ Your original vision

The "stages" aren't gone - they're just invisible, handled naturally through conversation rather than explicit UI navigation.
