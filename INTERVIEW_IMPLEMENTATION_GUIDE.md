# Interview Implementation Guide

**Last Updated**: November 2, 2025

This guide shows how to implement the refactored interview system using LLM function calling.

---

## Overview

The interview conductor uses **continuous extraction** instead of rigid stages:

```
❌ Old: Stage gates → Extract at milestones → Move to next stage
✅ New: Continuous conversation → Extract whenever data appears → Backend tracks completeness
```

---

## Backend Implementation

### 1. Function Definitions

The LLM has access to these functions:

```python
# backend/app/services/llm_functions.py

INTERVIEW_FUNCTIONS = [
    {
        "name": "extract_interview_data",
        "description": "Extract structured child development data from conversation",
        "parameters": {
            "type": "object",
            "properties": {
                "child_name": {
                    "type": "string",
                    "description": "Child's name if mentioned"
                },
                "age": {
                    "type": "number",
                    "description": "Child's exact age in years (can be decimal like 3.5)"
                },
                "gender": {
                    "type": "string",
                    "enum": ["male", "female", "unknown"],
                    "description": "Child's gender"
                },
                "primary_concerns": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": [
                            "speech", "social", "attention", "motor",
                            "sensory", "emotional", "behavioral", "learning"
                        ]
                    },
                    "description": "Categories of concerns mentioned"
                },
                "concern_details": {
                    "type": "string",
                    "description": "Detailed description of concerns with examples"
                },
                "strengths": {
                    "type": "string",
                    "description": "Child's interests, favorite activities, what they're good at"
                },
                "developmental_history": {
                    "type": "string",
                    "description": "Pregnancy, birth, developmental milestones, medical history"
                },
                "family_context": {
                    "type": "string",
                    "description": "Siblings, family history, educational setting, support"
                },
                "urgent_flags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Safety concerns requiring immediate attention"
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
                    "enum": ["view_report", "upload_video", "view_guidelines", "consultation"],
                    "description": "The action the user wants to perform"
                }
            },
            "required": ["action"]
        }
    },
    {
        "name": "user_is_stuck",
        "description": "User seems confused or wants to pause",
        "parameters": {
            "type": "object",
            "properties": {
                "confusion_type": {
                    "type": "string",
                    "enum": ["unclear_question", "wants_pause", "off_topic", "other"],
                    "description": "Type of confusion or issue"
                }
            },
            "required": ["confusion_type"]
        }
    }
]
```

### 2. Message Processing Flow

```python
# backend/app/services/conversation_service.py

async def process_message(family_id: str, message: str):
    """
    Process a user message with continuous extraction.
    """

    # 1. Load family context from Graphiti
    context = await graphiti.search(
        query=f"family:{family_id}",
        limit=50
    )

    # 2. Get recent conversation history
    history = await get_conversation_history(family_id, last_n=20)

    # 3. Calculate current completeness
    completeness = calculate_completeness(context)

    # 4. Build system prompt with current state
    system_prompt = build_interview_prompt(
        child_name=context.get('child_name', 'unknown'),
        age=context.get('age', 'unknown'),
        gender=context.get('gender', 'unknown'),
        concerns=context.get('primary_concerns', []),
        completeness=completeness
    )

    # 5. Call LLM with function calling
    llm_response = await llm.chat_completion(
        messages=[
            {"role": "system", "content": system_prompt},
            *history,
            {"role": "user", "content": message}
        ],
        functions=INTERVIEW_FUNCTIONS,
        function_call="auto"  # LLM decides when to call
    )

    # 6. Handle function calls if any
    if llm_response.function_call:
        await handle_function_call(
            function_name=llm_response.function_call.name,
            arguments=llm_response.function_call.arguments,
            family_id=family_id
        )

    # 7. Save conversation to Graphiti
    await graphiti.add_episode(
        name=f"conversation_{family_id}_{datetime.now().isoformat()}",
        episode_body=f"User: {message}\nChitta: {llm_response.content}",
        source_description="Interview conversation",
        reference_time=datetime.now()
    )

    # 8. Generate context cards based on updated state
    updated_context = await graphiti.search(query=f"family:{family_id}", limit=50)
    cards = generate_context_cards(updated_context, completeness)

    # 9. Check if video instructions should be generated
    if completeness >= 80 and not context.get('video_instructions_generated'):
        await generate_video_instructions(family_id, updated_context)

    return {
        "response": llm_response.content,
        "cards": cards,
        "completeness": calculate_completeness(updated_context)
    }
```

### 3. Function Call Handlers

```python
# backend/app/services/function_handlers.py

async def handle_function_call(function_name: str, arguments: dict, family_id: str):
    """
    Handle LLM function calls.
    """

    if function_name == "extract_interview_data":
        await handle_extract_interview_data(family_id, arguments)

    elif function_name == "user_wants_action":
        await handle_user_wants_action(family_id, arguments)

    elif function_name == "user_is_stuck":
        await handle_user_stuck(family_id, arguments)


async def handle_extract_interview_data(family_id: str, data: dict):
    """
    Save extracted interview data to Graphiti.
    Extraction is ADDITIVE - merges with existing data.
    """

    # Build facts from extracted data
    facts = []

    if data.get("child_name"):
        facts.append(f"Child's name is {data['child_name']}")

    if data.get("age"):
        facts.append(f"Child is {data['age']} years old")

    if data.get("gender"):
        facts.append(f"Child's gender is {data['gender']}")

    if data.get("primary_concerns"):
        concerns_str = ", ".join(data['primary_concerns'])
        facts.append(f"Primary concerns: {concerns_str}")

    if data.get("concern_details"):
        facts.append(f"Concern details: {data['concern_details']}")

    if data.get("strengths"):
        facts.append(f"Child's strengths: {data['strengths']}")

    if data.get("developmental_history"):
        facts.append(f"Developmental history: {data['developmental_history']}")

    if data.get("family_context"):
        facts.append(f"Family context: {data['family_context']}")

    # Add episode to Graphiti
    await graphiti.add_episode(
        name=f"interview_extraction_{family_id}_{datetime.now().isoformat()}",
        episode_body="\n".join(facts),
        source_description="Interview data extraction",
        reference_time=datetime.now()
    )

    # Handle urgent flags
    if data.get("urgent_flags"):
        await handle_urgent_flags(family_id, data['urgent_flags'])


async def handle_user_wants_action(family_id: str, data: dict):
    """
    User wants to perform an action - check prerequisites.
    """

    action = data['action']

    # Check if action is feasible
    prerequisites_met, missing = await check_prerequisites(family_id, action)

    if not prerequisites_met:
        # Backend signals to LLM that prerequisites aren't met
        # LLM will respond gracefully
        return {
            "feasible": False,
            "missing": missing,
            "message": f"Action '{action}' requires: {', '.join(missing)}"
        }

    return {
        "feasible": True,
        "action": action
    }


async def handle_user_stuck(family_id: str, data: dict):
    """
    User is stuck or wants to pause.
    """

    confusion_type = data['confusion_type']

    # Log the confusion for analytics
    await log_user_stuck(family_id, confusion_type)

    if confusion_type == "wants_pause":
        # Save current state
        await save_conversation_checkpoint(family_id)
```

### 4. Completeness Calculation

```python
# backend/app/services/completeness.py

def calculate_completeness(context: dict) -> int:
    """
    Calculate interview completeness percentage.
    Based on data richness, not stage completion.
    """

    score = 0
    max_score = 100

    # Basic information (20 points)
    if context.get('child_name'):
        score += 5
    if context.get('age'):
        score += 10  # Essential
    if context.get('gender'):
        score += 5

    # Primary concerns (30 points)
    concerns = context.get('primary_concerns', [])
    if concerns:
        score += 15
    if context.get('concern_details') and len(context['concern_details']) > 100:
        score += 15  # Detailed description

    # Strengths (10 points)
    if context.get('strengths'):
        score += 10

    # Developmental areas (20 points)
    areas_covered = 0
    for area in ['communication', 'social', 'behavior', 'attention', 'learning', 'sensory', 'daily_routines']:
        if area in context.get('raw_text', '').lower():
            areas_covered += 1
    score += min(20, areas_covered * 3)

    # History (10 points)
    if context.get('developmental_history'):
        score += 5
    if context.get('family_context'):
        score += 5

    # Examples and specificity (10 points)
    if 'example' in context.get('raw_text', '').lower():
        score += 5
    if len(context.get('raw_text', '')) > 500:  # Rich conversation
        score += 5

    return min(100, score)
```

---

## Frontend Integration

### Message Sending with Function Awareness

```javascript
// src/api/client.js

export async function sendMessage(message) {
  const response = await fetch('/api/conversation/message', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message })
  });

  const data = await response.json();

  return {
    response: data.response,           // Chitta's text response
    cards: data.cards,                 // Updated context cards
    completeness: data.completeness    // Interview progress percentage
  };
}
```

### No Frontend Tracking Needed

The frontend does NOT:
- ❌ Track stages
- ❌ Decide when to extract
- ❌ Calculate completeness
- ❌ Store interview state

The frontend ONLY:
- ✅ Sends messages
- ✅ Displays responses
- ✅ Shows context cards from backend
- ✅ Shows completeness progress bar

---

## Example Conversation Flow

### Turn 1: Name Collection

**User**: "השם שלו יוני"

**LLM Processing**:
```python
# LLM decides to call extract_interview_data
function_call = {
    "name": "extract_interview_data",
    "arguments": {
        "child_name": "Yoni",
        "gender": "male"  # Inferred from Hebrew masculine form
    }
}

response = "נעים להכיר את יוני! בן כמה הוא?"
```

**Backend saves to Graphiti**:
```
Facts added:
- Child's name is Yoni
- Child's gender is male
```

### Turn 4: Concern with Question

**User**: "הוא לא ממש מדבר, רק מילים בודדות. זה תקין?"

**LLM Processing**:
```python
# Extract the concern
function_call = {
    "name": "extract_interview_data",
    "arguments": {
        "primary_concerns": ["speech"],
        "concern_details": "Limited speech at age 3.5, mostly single words"
    }
}

# Answer the question AND continue interview
response = """דיבור מתפתח בקצב שונה לכל ילד. חלק מהילדים לוקחים יותר זמן.
זה בדיוק מה שאני כאן כדי לעזור לך להבין טוב יותר.

תוכל/י לתת לי דוגמה למילים שהוא כן אומר?"""
```

**Key**: Question is answered naturally AND data is extracted

### Turn 10: Multiple Concerns

**User**: "כן, הוא אומר אמא, אבא, מים. ואני רואה שהוא מסדר את הצעצועים בשורות כל הזמן"

**LLM Processing**:
```python
# Extract both speech details and new concern
function_call = {
    "name": "extract_interview_data",
    "arguments": {
        "primary_concerns": ["speech", "repetitive_behaviors"],
        "concern_details": "Says mama, dada, water - approximately 3 single words. Lines up toys in rows frequently"
    }
}

response = """הבנתי. 'אמא', 'אבא', 'מים' - זה יפה שיש לו מילים בסיסיות.

לגבי הסידור של הצעצועים - חלק מהילדים מוצאים נוחות בארגון חפצים.
זה יכול להיות דרך להבין את הסביבה. זה קורה כל יום?"""
```

### Completeness Triggers

When completeness reaches ~80%:

**Backend**:
```python
if completeness >= 80 and not video_instructions_generated:
    # Generate personalized video guidelines
    await generate_video_instructions(family_id, context)

    # Update cards
    cards = [
        {
            "title": "Upload Video",
            "subtitle": "Ready for next step",
            "status": "action",
            "action": "upload_video"
        },
        {
            "title": "Video Guidelines",
            "subtitle": "Personalized instructions ready",
            "status": "new",
            "action": "view_guidelines"
        }
    ]
```

**LLM natural wrap-up**:
```
"תודה רבה על השיתוף! קיבלתי תמונה ברורה של יוני והדברים שמעסיקים אותך.
עכשיו אני מכין עבורך הנחיות מותאמות לצילום סרטון שיעזור לי להבין את יוני עוד יותר טוב."
```

---

## Key Differences from Old System

### Old (Stage-Based)

```python
# Frontend controls flow
if stage == "collect_name":
    ask_name()
    if name_received:
        stage = "collect_age"

# Extract at milestones
if stage == "STAGE_2_COMPLETED":
    extract_all_data()

# Rigid progression
can_proceed = (stage_1_complete and stage_2_complete)
```

### New (Continuous)

```python
# Backend calculates state
completeness = calculate_completeness(graphiti_context)

# Extract whenever data appears
if user_mentioned_concern:
    extract_interview_data(concern)  # Immediate

# Natural progression
if completeness >= 80:
    generate_video_instructions()  # Automatic
```

---

## Testing the Interview Flow

### Manual Test Script

```python
# tests/test_interview_flow.py

async def test_continuous_extraction():
    family_id = "test_family_1"

    # Turn 1: Name
    r1 = await process_message(family_id, "השם שלה מיה")
    assert "מיה" in get_context(family_id)['child_name']

    # Turn 2: Age
    r2 = await process_message(family_id, "היא בת 4")
    assert get_context(family_id)['age'] == 4

    # Turn 3: Concern
    r3 = await process_message(family_id, "היא לא משחקת עם ילדים אחרים")
    context = get_context(family_id)
    assert "social" in context['primary_concerns']

    # Turn 4: Question (should be answered AND extracted)
    r4 = await process_message(family_id, "זה תקין?")
    assert r4['response']  # Got an answer
    assert "social" in get_context(family_id)['primary_concerns']  # Still tracked

    # Check completeness increases
    assert r4['completeness'] > r1['completeness']


async def test_prerequisite_blocking():
    family_id = "test_family_2"

    # Try to view report before interview complete
    r1 = await process_message(family_id, "Show me the report")
    assert "interview" in r1['response'].lower()  # Explains need for interview
    assert not any(c['action'] == 'view_report' for c in r1['cards'])

    # Complete interview (mock)
    await mock_complete_interview(family_id)

    # Try again
    r2 = await process_message(family_id, "Show me the report")
    assert any(c['action'] == 'view_report' for c in r2['cards'])
```

---

## Production Checklist

- [ ] Implement `extract_interview_data` handler
- [ ] Implement completeness calculator
- [ ] Implement prerequisite checker
- [ ] Test continuous extraction with real LLM
- [ ] Test question answering mid-interview
- [ ] Verify Graphiti episode additive behavior
- [ ] Load test with 100+ conversations
- [ ] Monitor function calling costs
- [ ] Set up fallback if function calling fails
- [ ] Create admin panel to view extracted data

---

This implementation preserves the excellent conversational tone of the original interview prompt while enabling the conversation-first architecture with continuous extraction.
