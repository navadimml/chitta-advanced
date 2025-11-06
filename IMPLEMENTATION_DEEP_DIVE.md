# Chitta Implementation Deep Dive

**Purpose**: Detailed implementation of conversation-first architecture with technical dependencies

---

## Core Insight: There's No "Interview Mode"

**Wrong Mental Model**:
```
Interview Mode → User must answer questions
Question interrupts → Switch modes, handle question, return to interview
```

**Right Mental Model**:
```
ALWAYS Conversation → LLM continuously extracts relevant data
User asks question → Answer it, extraction continues
Interview "complete" → When we have enough data, not when user "finishes"
```

**Key**: The interview is invisible to the user. They're just having a conversation. The backend is extracting structured data from that conversation.

---

## Example: User Asks Question Mid-Interview

```
Chitta: "Tell me about [child]'s speech development. Does he use 2-3 word phrases?"

User: "Yes, but I have a question - is it normal for him to avoid eye contact?"

[Current Code Would: Try to extract this as speech data, fail]

[Correct Approach:]
1. LLM recognizes: User asking question, not answering
2. Respond to question naturally
3. Continue extraction after
4. BOTH messages saved to Graphiti (full context preserved)

Chitta: "That's a really important observation. Eye contact develops differently
        for every child, and some are more comfortable with it than others.
        It's one of the things I'll look at in the videos to get a fuller picture.

        Thanks for mentioning it - I've noted that concern.

        Back to speech - does he combine words into phrases like 'want juice' or
        'go outside'?"

[Extraction continues, question answered, no mode switch needed]
```

**Key Points**:
1. No "filtering" - the question is valid conversation
2. Saved to Graphiti as context (valuable information!)
3. LLM naturally returns to data collection
4. User doesn't perceive any disruption

---

## The Single-Agent Architecture

**Not multiple specialized agents**, but **one conversational LLM with function calling + structured extraction**.

### Why Single Agent?

❌ **Multi-Agent Complexity**:
```
Agent 1: Interview conductor
Agent 2: Question answerer
Agent 3: Intent router
→ Coordination overhead, context handoff issues
```

✅ **Single Agent with Tools**:
```
One LLM with:
- Function calling (actions: upload_video, view_report, etc.)
- Structured extraction (interview data)
- Full conversation history
→ Unified context, no handoff
```

---

## The LLM System Prompt

```python
SYSTEM_PROMPT = """
You are Chitta, an empathetic AI assistant helping parents understand their child's development.

Your capabilities:
1. **Conversational**: Answer any question naturally and warmly
2. **Data Collection**: Extract child development information from conversation
3. **Action Facilitation**: Help users take actions when prerequisites are met
4. **Guidance**: When users want something not yet possible, explain gently and guide forward

Conversation principles:
- Always respond naturally, never robotic
- Handle tangents and questions gracefully - they're not interruptions
- Extract data opportunistically from natural conversation
- Never force a rigid interview structure
- When returning to data collection, do it naturally ("Thanks for sharing that. Now...")

Current conversation state:
- Child name: {child_name or "unknown"}
- Age: {age or "unknown"}
- Concerns discussed: {concerns}
- Interview completeness: {completeness}%
- Videos uploaded: {video_count}/3
- Analysis status: {analysis_status}

Available actions: {available_actions}
Prerequisites not met: {blocked_actions}
"""
```

---

## LLM Function Calling Schema

### Functions Available to LLM

```python
AVAILABLE_FUNCTIONS = [
    {
        "name": "extract_interview_data",
        "description": "Extract structured child development data from conversation",
        "parameters": {
            "type": "object",
            "properties": {
                "child_name": {"type": "string"},
                "age": {"type": "number"},
                "gender": {"type": "string"},
                "primary_concerns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Categories: speech, social, attention, motor, sensory, emotional"
                },
                "concern_details": {"type": "string"},
                "developmental_history": {"type": "string"},
                "family_context": {"type": "string"},
                "urgent_flags": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }
    },
    {
        "name": "user_wants_action",
        "description": "User wants to perform an action (view report, upload video, etc.)",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["view_report", "upload_video", "view_guidelines",
                             "journal_entry", "find_experts", "ask_question"]
                },
                "context": {"type": "string"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "user_is_stuck",
        "description": "User seems confused or stuck, needs guidance",
        "parameters": {
            "type": "object",
            "properties": {
                "confusion_type": {
                    "type": "string",
                    "enum": ["process_unclear", "technical_issue", "emotional", "other"]
                }
            }
        }
    }
]
```

---

## Message Processing Flow

### Every User Message Goes Through This:

```python
async def process_message(family_id: str, message: str) -> Response:
    """
    Single entry point for all messages
    """

    # 1. Load context from Graphiti
    context = await load_family_context(family_id)

    # 2. Build conversation history
    history = await get_conversation_history(family_id, last_n=20)

    # 3. Call LLM with function calling
    llm_response = await llm.chat_completion(
        messages=[
            {"role": "system", "content": build_system_prompt(context)},
            *history,
            {"role": "user", "content": message}
        ],
        functions=AVAILABLE_FUNCTIONS,
        function_call="auto"  # LLM decides when to call
    )

    # 4. Handle function calls (if any)
    if llm_response.function_call:
        await handle_function_call(
            llm_response.function_call,
            family_id,
            context
        )

    # 5. Save to Graphiti as episode
    await graphiti.add_episode(
        name=f"conversation_{family_id}_{timestamp}",
        episode_body=f"User: {message}\nChitta: {llm_response.content}",
        source=EpisodeType.message,
        group_id=f"family_{family_id}",
        reference_time=datetime.now()
    )

    # 6. Generate context cards based on current state
    cards = await generate_context_cards(context, llm_response)

    # 7. Generate suggestions
    suggestions = await generate_suggestions(context)

    return {
        "response": llm_response.content,
        "cards": cards,
        "suggestions": suggestions,
        "ui_updates": extract_ui_updates(llm_response)
    }
```

---

## Interview Data Extraction (Continuous)

### How It Works:

```python
async def handle_extract_interview_data(function_args: dict, family_id: str):
    """
    Called whenever LLM identifies interview-relevant information
    """

    # Load existing data
    current_data = await graphiti.get_entity(
        entity_type="InterviewData",
        group_id=f"family_{family_id}"
    )

    # Merge new data (additive, never overwrite)
    updated_data = merge_interview_data(current_data, function_args)

    # Update in Graphiti
    await graphiti.update_entity(
        entity_type="InterviewData",
        entity_id=current_data.uuid,
        new_data=updated_data,
        group_id=f"family_{family_id}"
    )

    # Check if interview is "complete enough"
    completeness = calculate_completeness(updated_data)

    # If complete, generate video guidelines
    if completeness >= 0.8 and not current_data.get('guidelines_generated'):
        await trigger_guideline_generation(family_id, updated_data)

    return completeness
```

### Example: Multi-Turn Extraction

```
Turn 1:
User: "My son Yoni is 3 and a half"
LLM: [calls extract_interview_data(child_name="Yoni", age=3.5)]
      "Nice to meet Yoni! Tell me what brings you here today?"

Turn 2:
User: "He's not really talking much"
LLM: [calls extract_interview_data(primary_concerns=["speech"])]
      "I understand. Can you give me an example of what he does say?"

Turn 5:
User: "Is it normal for him to line up his toys?"
LLM: [calls extract_interview_data(primary_concerns=["speech", "repetitive_behaviors"])]
      [Does NOT call user_wants_action - this is just conversation]
      "Some children find comfort in organizing objects - it can be a way of
      making sense of their environment. I'd love to see this in a video if
      possible. Does he do this often?"

Turn 8:
User: "Yes, every day. Should I be worried?"
LLM: [No function call - just empathetic response]
      "It's understandable to wonder. Repetitive behaviors can be part of normal
      development, especially when children are learning to process the world.
      The videos will help me see the full picture. For now, tell me about his
      social interactions - does he play with other children?"
```

**Key**: Extraction happens continuously, opportunistically, without disrupting conversation flow.

---

## Handling "User Wants Action"

### When LLM Detects Intent:

```python
async def handle_user_wants_action(action: str, context: dict, family_id: str):
    """
    User wants to do something - check if possible
    """

    # Check prerequisites
    can_do, missing = check_prerequisites(action, context)

    if can_do:
        # Facilitate action
        return await facilitate_action(action, family_id, context)

    else:
        # Explain what's needed, generate helpful response
        explanation = await llm.generate(
            prompt=f"""
            User wants to: {action}
            Missing prerequisites: {missing}
            Current state: {context.summary}

            Generate a warm, helpful response that:
            1. Acknowledges their request
            2. Explains what's needed first (naturally)
            3. Offers to help them get there
            4. Suggests concrete next step

            Be empathetic and natural, not technical.
            """,
            context=context
        )

        return {
            "response": explanation,
            "blocked_action": action,
            "needs": missing
        }
```

### Example: User Wants Report Early

```
Turn 15 (Interview ~40% complete):
User: "Can I see the report now?"

LLM: [calls user_wants_action(action="view_report")]

Backend:
  check_prerequisites("view_report", context)
  → Returns: (False, ["interview_complete", "videos_analyzed"])

LLM generates:
  "I'm excited to create your personalized report! To do that well, I need
   to understand Yoni better first. We're making great progress - we've talked
   about speech and play patterns. Can you tell me about how he interacts with
   other children? That'll help me give you more accurate guidance."

Cards Generated:
  [Interview Progress] "40% complete - a few more questions"
  [Why These Questions?] "Learn about our process"
```

---

## Context Card Generation (Dynamic)

### Cards Are Generated FRESH Each Turn:

```python
async def generate_context_cards(context: dict, llm_response: dict) -> List[Card]:
    """
    AI decides what cards to show based on current state
    """

    # Get what's currently possible
    possible_actions = get_available_actions(context)

    # Get recent activity (from Graphiti)
    recent = await graphiti.search(
        query="recent activities and notable events",
        center_node_uuid=context.child_node_uuid,
        group_id=context.group_id,
        num_results=10
    )

    # LLM decides what's most relevant
    card_prompt = f"""
    Generate 2-4 context cards for the user based on current state.

    Current state:
    - Interview completeness: {context.interview_completeness}%
    - Videos uploaded: {context.videos_uploaded}/3
    - Analysis status: {context.analysis_status}
    - Last activity: {context.last_activity}

    Available actions: {possible_actions}
    Recent context: {format_recent(recent)}
    Recent conversation: {llm_response.content}

    Prioritize:
    1. Time-sensitive (new report ready, analysis complete)
    2. Blocking prerequisites (must do to progress)
    3. User's apparent interest (from conversation)
    4. Helpful resources

    Return 2-4 cards, most important first.
    Format: [{{"title": "...", "subtitle": "...", "action": "...", "status": "..."}}]
    """

    cards = await llm.generate_structured(
        prompt=card_prompt,
        schema=CardSchema,
        context=context
    )

    return cards[:4]  # Max 4
```

### Card Examples by State:

```python
# Interview ongoing (20%)
cards = [
    {
        "title": "מדברים על יוני",
        "subtitle": "עוד כמה דקות של שיחה",
        "status": "progress",
        "action": null  # No action - informational
    },
    {
        "title": "שאלה לגבי התהליך?",
        "subtitle": "מוזמנת לשאול",
        "status": "action",
        "action": "ask_process_question"
    }
]

# Interview complete, no videos
cards = [
    {
        "title": "הנחיות צילום",
        "subtitle": "3 תרחישים מותאמים ליוני",
        "status": "new",
        "action": "view_guidelines"
    },
    {
        "title": "העלאת סרטון",
        "subtitle": "מוכנה להתחיל?",
        "status": "action",
        "action": "upload_video"
    },
    {
        "title": "יומן יוני",
        "subtitle": "תעדי תצפיות יומיומיות",
        "status": "action",
        "action": "journal"
    }
]

# Videos uploaded, analyzing
cards = [
    {
        "title": "ניתוח בתהליך",
        "subtitle": "בדרך כלל לוקח 24 שעות",
        "status": "processing",
        "action": null
    },
    {
        "title": "יומן יוני",
        "subtitle": "3 רשומות השבוע",
        "status": "progress",
        "action": "journal"
    },
    {
        "title": "יש שאלות?",
        "subtitle": "התייעצי איתי בינתיים",
        "status": "action",
        "action": "consultation"
    }
]

# Reports ready
cards = [
    {
        "title": "מדריך להורים מוכן!",
        "subtitle": "הממצאים והמלצות",
        "status": "new",
        "action": "view_parent_report"
    },
    {
        "title": "דוח מקצועי",
        "subtitle": "לשיתוף עם מומחים",
        "status": "action",
        "action": "view_professional_report"
    },
    {
        "title": "מציאת מומחים",
        "subtitle": "מבוסס על הממצאים",
        "status": "action",
        "action": "find_experts"
    }
]
```

**Note**: NO "Continue Conversation" card. User is ALWAYS in conversation. Cards show ACTIONS or STATUS, not conversation state.

---

## Interview Completeness Calculation

```python
def calculate_interview_completeness(data: dict) -> float:
    """
    Not a checklist, but a richness score
    """

    score = 0.0

    # Core data (30% weight)
    if data.get('child_name'): score += 0.10
    if data.get('age'): score += 0.10
    if data.get('gender'): score += 0.05
    if data.get('primary_concerns'): score += 0.05

    # Detailed concerns (30% weight)
    concern_detail_length = len(data.get('concern_details', ''))
    score += min(0.30, concern_detail_length / 500 * 0.30)

    # Developmental context (20% weight)
    dev_history_length = len(data.get('developmental_history', ''))
    score += min(0.20, dev_history_length / 300 * 0.20)

    # Family/environmental context (10% weight)
    family_context_length = len(data.get('family_context', ''))
    score += min(0.10, family_context_length / 200 * 0.10)

    # Conversation richness (10% weight)
    # Based on number of conversational turns with relevant content
    relevant_turns = data.get('relevant_turn_count', 0)
    score += min(0.10, relevant_turns / 15 * 0.10)

    return min(1.0, score)
```

**Key**: Not "have you answered question 5?" but "do we have enough rich context?"

---

## When to Generate Video Guidelines

```python
async def check_and_generate_guidelines(family_id: str, interview_data: dict):
    """
    Called after every interview data update
    """

    completeness = calculate_interview_completeness(interview_data)

    # Threshold: 80% complete
    if completeness >= 0.80 and not interview_data.get('guidelines_generated'):

        # Generate personalized guidelines using LLM
        guidelines = await llm.generate(
            prompt=f"""
            Based on this interview data, generate 3 personalized video filming
            scenarios that will help assess this child's development:

            Child: {interview_data}

            For each scenario, provide:
            - Title
            - What to film (specific to this child's concerns)
            - Duration (3-5 minutes)
            - Tips for best results
            - What we're looking for

            Prioritize scenarios based on primary concerns: {interview_data.primary_concerns}
            """,
            context=interview_data
        )

        # Save to Graphiti
        await graphiti.add_entity(
            entity_type="VideoGuidelines",
            entity_data=guidelines,
            group_id=f"family_{family_id}"
        )

        # Mark as generated
        interview_data['guidelines_generated'] = True

        # Notify user via conversation
        await add_system_message(
            family_id,
            "תודה רבה! בהתבסס על מה שסיפרת לי, הכנתי 3 תרחישי צילום מותאמים ליוני. רוצה לראות אותם?"
        )

    return completeness
```

---

## No Separate Agent Orchestrator

**Single LLM does everything**:

```python
# ONE LLM instance
llm = LLMFactory.create(
    provider="anthropic",
    model="claude-3-5-sonnet-20241022"
)

# ALL requests go through it
async def process_message(message):
    response = await llm.chat_completion(
        messages=build_context(message),
        functions=AVAILABLE_FUNCTIONS
    )
    return response
```

**Why no agent orchestrator?**
- Simpler: No coordination logic
- Faster: No agent handoffs
- Unified context: One conversation thread
- Easier to debug: Single call chain
- More natural: LLM sees full conversation

---

## Summary: The Implementation

### Components:

1. **One LLM** (Claude/GPT-4)
   - Handles all conversation
   - Calls functions when needed
   - Extracts data continuously

2. **Function Calling** (3 functions)
   - `extract_interview_data`: Continuous extraction
   - `user_wants_action`: Intent detection
   - `user_is_stuck`: Guidance triggers

3. **Graphiti Backend**
   - Stores all episodes
   - Maintains entity graph
   - Provides context for LLM

4. **Context Card Generator**
   - LLM-based (same LLM)
   - Regenerated each turn
   - Max 4 cards, prioritized

5. **Prerequisite Checker**
   - Simple Python logic
   - Checks data dependencies
   - Returns (feasible, missing)

### Data Flow:

```
User Message
  ↓
Load Context (Graphiti)
  ↓
LLM Chat Completion (with functions)
  ↓
Handle Function Calls
  ↓
Save Episode (Graphiti)
  ↓
Generate Cards (LLM)
  ↓
Return Response
```

**No agents, no complex orchestration, just one smart LLM with tools.**

---

Read the full technical specification in this document. Ready to implement Phase 1?
