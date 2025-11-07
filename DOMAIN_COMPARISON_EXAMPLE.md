# Domain Comparison: Same Engine, Different Domains

This document shows **concrete, side-by-side examples** of how the same workflow engine handles two completely different domains:
- Child Development Assessment (current)
- Legal Case Management (hypothetical)

**Key Point**: The engine code is **IDENTICAL**. Only the domain configuration changes.

---

## Example 1: First User Message

### Child Development Domain

**User Message:**
> "שלום, הבן שלי יוני בן 3 וחצי, והוא לא ממש מדבר. אני מתחילה לדאוג."

**Domain Schema** (`domains/child_development/schema.py`):
```python
{
    "child_name": FieldDefinition(type="string", weight=0.01),
    "age": FieldDefinition(type="number", weight=0.03),
    "primary_concerns": FieldDefinition(type="array", options=["speech", "social", ...], weight=0.10),
    "concern_details": FieldDefinition(type="longtext", weight=0.40),
}
```

**Engine Extraction** (generic `extraction_service.py`):
```python
extracted = {
    "child_name": "יוני",
    "age": 3.5,
    "primary_concerns": ["speech"],
    "concern_details": "לא ממש מדבר. אני מתחילה לדאוג"
}
completeness = 0.14  # Based on field weights
```

**LLM Response** (using domain prompts):
> "נעים להכיר את יוני! אני מבינה את הדאגה, ואני כאן כדי לעזור. ספרי לי קצת יותר - מה יוני כן אומר? האם הוא משתמש במילים בודדות, או שהוא משלב מילים?"

---

### Legal Case Management Domain

**User Message:**
> "Hi, I'm Sarah Johnson. I was in a car accident 3 weeks ago on Highway 101. The other driver ran a red light and hit me. I have whiplash and my car is totaled."

**Domain Schema** (`domains/legal_case/schema.py`):
```python
{
    "client_name": FieldDefinition(type="string", weight=0.01),
    "case_type": FieldDefinition(type="enum", options=["personal_injury", "contract", ...], weight=0.05),
    "incident_description": FieldDefinition(type="longtext", weight=0.40),
    "damages_claimed": FieldDefinition(type="text", weight=0.15),
}
```

**Engine Extraction** (SAME `extraction_service.py`):
```python
extracted = {
    "client_name": "Sarah Johnson",
    "case_type": "personal_injury",
    "incident_description": "car accident 3 weeks ago on Highway 101. Other driver ran red light",
    "damages_claimed": "whiplash, car totaled"
}
completeness = 0.17  # Based on field weights
```

**LLM Response** (using domain prompts):
> "I'm sorry to hear about your accident, Sarah. Let's gather the information we need for your case. Can you tell me more about the injuries you sustained? You mentioned whiplash - have you seen a doctor, and what treatment have you received?"

---

## Example 2: Mid-Conversation Action Request

### Child Development Domain

**Context:**
- Completeness: 35%
- Data extracted: child name, age, some concerns mentioned

**User Message:**
> "אני רוצה לראות את הדוח עכשיו"

**Domain Actions** (`domains/child_development/actions.py`):
```python
{
    "view_report": ActionDefinition(
        requires=[PrerequisiteType.ANALYSIS_COMPLETE],  # Needs videos analyzed
        explanation_template="אני רוצה ליצור לך דוח מקיף! אבל קודם אני צריכה להכיר את {entity_name} טוב יותר דרך השיחה שלנו. כבר עברנו {completeness_pct}% מהראיון - בואי נמשיך."
    )
}
```

**Engine Prerequisite Check** (generic `prerequisite_service.py`):
```python
check = prerequisite_service.check_action(
    action="view_report",
    context={
        "completeness": 0.35,
        "analysis_complete": False,  # ❌ Not met
        "entity_name": "יוני"
    }
)

# Returns:
# {
#   "feasible": False,
#   "missing": ["ANALYSIS_COMPLETE"],
#   "explanation": "אני רוצה ליצור לך דוח מקיף! אבל קודם אני צריכה להכיר את יוני טוב יותר דרך השיחה שלנו. כבר עברנו 35% מהראיון - בואי נמשיך."
# }
```

**LLM Response**:
> "אני רוצה ליצור לך דוח מקיף! אבל קודם אני צריכה להכיר את יוני טוב יותר דרך השיחה שלנו. כבר עברנו 35% מהראיון - בואי נמשיך. ספרי לי - איך יוני משחק עם ילדים אחרים?"

---

### Legal Case Management Domain

**Context:**
- Completeness: 40%
- Data extracted: client name, incident type, basic damages

**User Message:**
> "Can I see the demand letter now?"

**Domain Actions** (`domains/legal_case/actions.py`):
```python
{
    "view_demand_letter": ActionDefinition(
        requires=[PrerequisiteType.INTAKE_COMPLETE, PrerequisiteType.DOCUMENTS_UPLOADED],
        explanation_template="I want to draft a strong demand letter for you! But first I need to complete gathering all the details of your {case_type} case. We're {completeness_pct}% through the intake. Let's continue - this information will make your demand letter much more effective."
    )
}
```

**Engine Prerequisite Check** (SAME `prerequisite_service.py`):
```python
check = prerequisite_service.check_action(
    action="view_demand_letter",
    context={
        "completeness": 0.40,
        "documents_uploaded": False,  # ❌ Not met
        "case_type": "personal injury"
    }
)

# Returns:
# {
#   "feasible": False,
#   "missing": ["INTAKE_COMPLETE", "DOCUMENTS_UPLOADED"],
#   "explanation": "I want to draft a strong demand letter for you! But first I need to complete gathering all the details of your personal injury case. We're 40% through the intake. Let's continue - this information will make your demand letter much more effective."
# }
```

**LLM Response**:
> "I want to draft a strong demand letter for you! But first I need to complete gathering all the details of your personal injury case. We're 40% through the intake. Let's continue - this information will make your demand letter much more effective. Tell me, besides the whiplash, did you sustain any other injuries?"

---

## Example 3: Completeness Calculation

### Child Development Domain

**Current Data**:
```python
{
    "child_name": "יוני",                    # weight: 0.01 → 0.01
    "age": 3.5,                               # weight: 0.03 → 0.03
    "gender": "male",                         # weight: 0.01 → 0.01
    "primary_concerns": ["speech", "social"], # weight: 0.10 → 0.10
    "concern_details": "300 characters of detailed examples and descriptions",  # weight: 0.40 → (300/1000)*0.40 = 0.12
    "strengths": "100 characters",            # weight: 0.10 → (100/300)*0.10 = 0.03
    "developmental_history": "",              # weight: 0.15 → 0.00
    "family_context": "",                     # weight: 0.07 → 0.00
    "daily_routines": "",                     # weight: 0.07 → 0.00
    "parent_goals": ""                        # weight: 0.06 → 0.00
}
```

**Completeness Engine** (generic `completeness_service.py`):
```python
def calculate_completeness(data: Dict, schema: BaseDomainSchema) -> float:
    score = 0.0

    for field_name, definition in schema.fields.items():
        value = data.get(field_name)

        if not value:
            continue

        if definition.type == "longtext":
            # Text fields: score based on length vs. target
            length = len(value)
            target_length = definition.target_length or 1000
            field_score = min(1.0, length / target_length) * definition.weight
        elif definition.type == "array":
            # Arrays: score based on having items
            field_score = definition.weight if len(value) > 0 else 0
        else:
            # Other fields: full weight if present
            field_score = definition.weight

        score += field_score

    return min(1.0, score)
```

**Result**: `completeness = 0.30` (30%)

**Status**: "Continue conversation - need more depth on concerns, history, and context"

---

### Legal Case Management Domain

**Current Data**:
```python
{
    "client_name": "Sarah Johnson",                     # weight: 0.01 → 0.01
    "case_type": "personal_injury",                     # weight: 0.05 → 0.05
    "incident_description": "400 characters of detailed accident description",  # weight: 0.40 → (400/1000)*0.40 = 0.16
    "damages_claimed": "150 characters",                # weight: 0.15 → (150/300)*0.15 = 0.075
    "timeline": "50 characters",                        # weight: 0.10 → (50/200)*0.10 = 0.025
    "witness_information": "",                          # weight: 0.08 → 0.00
    "police_report_filed": True,                        # weight: 0.02 → 0.02
    "insurance_details": "",                            # weight: 0.05 → 0.00
    "medical_treatment": "100 characters",              # weight: 0.14 → (100/300)*0.14 = 0.047
}
```

**Completeness Engine** (SAME calculation logic):

**Result**: `completeness = 0.377` (38%)

**Status**: "Continue conversation - need witness info, medical details, insurance information"

---

## Example 4: Context Cards Generation

### Child Development Domain

**Session State**:
- Completeness: 75%
- Videos uploaded: 0
- Analysis complete: False

**Domain Config** (`domains/child_development/card_templates.py`):
```python
{
    "interview_progress": {
        "threshold": "always",
        "template": {
            "title": "שיחת ההיכרות",
            "subtitle": "התקדמות: {completeness_pct}%",
            "icon": "message-circle",
            "status_fn": lambda c: "completed" if c >= 0.8 else "processing" if c >= 0.5 else "pending"
        }
    },
    "video_upload": {
        "threshold": "completeness >= 0.8",
        "template": {
            "title": "העלאת סרטון",
            "subtitle": "מוכן לשלב הבא",
            "icon": "video",
            "status": "action",
            "action": "upload_video"
        }
    }
}
```

**Engine Card Generator** (generic `card_generator.py`):
```python
def generate_cards(session_state, domain_config):
    cards = []

    for card_id, card_def in domain_config.card_templates.items():
        # Check if card should be shown
        if not eval_threshold(card_def.threshold, session_state):
            continue

        # Build card from template
        card = build_card_from_template(
            card_def.template,
            session_state,
            domain_config
        )
        cards.append(card)

    return cards
```

**Generated Cards**:
```python
[
    {
        "title": "שיחת ההיכרות",
        "subtitle": "התקדמות: 75%",
        "icon": "message-circle",
        "status": "processing"
    },
    {
        "title": "פרופיל: יוני",
        "subtitle": "גיל 3.5, 2 תחומי התפתחות",
        "icon": "user",
        "status": "active"
    },
    {
        "title": "העלאת סרטון",
        "subtitle": "מוכן לשלב הבא",
        "icon": "video",
        "status": "action",
        "action": "upload_video"
    }
]
```

---

### Legal Case Management Domain

**Session State**:
- Completeness: 72%
- Documents uploaded: 0
- Police report filed: Yes

**Domain Config** (`domains/legal_case/card_templates.py`):
```python
{
    "intake_progress": {
        "threshold": "always",
        "template": {
            "title": "Case Intake",
            "subtitle": "Progress: {completeness_pct}%",
            "icon": "clipboard",
            "status_fn": lambda c: "completed" if c >= 0.8 else "processing" if c >= 0.5 else "pending"
        }
    },
    "document_upload": {
        "threshold": "completeness >= 0.7",
        "template": {
            "title": "Upload Documents",
            "subtitle": "Police report, medical records, photos",
            "icon": "file-upload",
            "status": "action",
            "action": "upload_documents"
        }
    }
}
```

**Engine Card Generator** (SAME code):

**Generated Cards**:
```python
[
    {
        "title": "Case Intake",
        "subtitle": "Progress: 72%",
        "icon": "clipboard",
        "status": "processing"
    },
    {
        "title": "Case: Sarah Johnson",
        "subtitle": "Personal Injury - Car Accident",
        "icon": "briefcase",
        "status": "active"
    },
    {
        "title": "Upload Documents",
        "subtitle": "Police report, medical records, photos",
        "icon": "file-upload",
        "status": "action",
        "action": "upload_documents"
    }
]
```

---

## Example 5: Function Calling Schema

### Child Development Domain

**Domain Functions** (`domains/child_development/functions.py`):
```python
def get_extraction_functions(schema: ChildDevelopmentSchema):
    return [
        {
            "name": "extract_interview_data",
            "description": "Extract child development information from conversation",
            "parameters": {
                "type": "object",
                "properties": {
                    # Auto-generated from schema
                    "child_name": {"type": "string", "description": "שם הילד/ה"},
                    "age": {"type": "number", "description": "גיל בשנים"},
                    "gender": {
                        "type": "string",
                        "enum": ["male", "female", "unknown"],
                        "description": "מגדר"
                    },
                    "primary_concerns": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["speech", "social", "attention", "motor", "sensory", "emotional"]},
                        "description": "תחומי דאגה עיקריים"
                    },
                    "concern_details": {"type": "string", "description": "פירוט הדאגות והדוגמאות"},
                    "strengths": {"type": "string", "description": "חוזקות והתנהגויות חיוביות"},
                    # ... etc - ALL auto-generated from schema
                }
            }
        }
    ]
```

---

### Legal Case Management Domain

**Domain Functions** (`domains/legal_case/functions.py`):
```python
def get_extraction_functions(schema: LegalCaseSchema):
    return [
        {
            "name": "extract_case_data",
            "description": "Extract legal case information from conversation",
            "parameters": {
                "type": "object",
                "properties": {
                    # Auto-generated from schema
                    "client_name": {"type": "string", "description": "Client's full name"},
                    "case_type": {
                        "type": "string",
                        "enum": ["personal_injury", "contract", "family", "criminal"],
                        "description": "Type of legal case"
                    },
                    "incident_description": {"type": "string", "description": "Detailed description of the incident"},
                    "damages_claimed": {"type": "string", "description": "Damages and losses"},
                    "timeline": {"type": "string", "description": "Timeline of events"},
                    # ... etc - ALL auto-generated from schema
                }
            }
        }
    ]
```

**Key Point**: The function schemas are **automatically generated** from the domain schema. No manual duplication needed!

---

## The Engine Code (Same for Both)

### conversation_service.py

```python
async def process_message(session_id: str, message: str, domain: BaseDomain):
    """
    Main orchestrator - works for ANY domain
    """

    # 1. Load session state
    session = state_service.get_or_create_session(session_id)

    # 2. Get domain-specific extraction functions
    functions = domain.get_extraction_functions()

    # 3. Build contextual prompt (domain-aware)
    prompt = prompt_builder.build_prompt(session, domain)

    # 4. Call LLM with function calling
    llm_response = await llm.chat(
        messages=[
            {"role": "system", "content": prompt},
            *session.conversation_history,
            {"role": "user", "content": message}
        ],
        functions=functions
    )

    # 5. Process function calls (domain-agnostic)
    for func_call in llm_response.function_calls:
        extracted_data = func_call.arguments
        extraction_service.update_data(session_id, extracted_data, domain.schema)

    # 6. Calculate completeness (using domain weights)
    completeness = completeness_service.calculate(session.extracted_data, domain.schema)

    # 7. Generate context cards (using domain templates)
    cards = card_generator.generate(session, domain)

    # 8. Return response
    return {
        "response": llm_response.content,
        "completeness": completeness,
        "cards": cards
    }
```

**This exact code works for**:
- ✅ Child development
- ✅ Legal case management
- ✅ Medical intake
- ✅ Job interview screening
- ✅ Real estate assessment
- ✅ ... ANY domain with the same pattern

---

## Summary: Same Engine, Different Flavors

| Component | Child Development | Legal Case | Engine Code |
|-----------|------------------|------------|-------------|
| **Schema** | Child, age, concerns | Client, case type, incident | `extraction_service.py` - SAME |
| **Completeness** | Weights emphasize concern details (40%) | Weights emphasize incident description (40%) | `completeness_service.py` - SAME |
| **Actions** | view_video_guidelines, upload_video | view_demand_letter, schedule_deposition | `prerequisite_service.py` - SAME |
| **Prompts** | Hebrew, empathetic, child-focused | English, professional, legal-focused | `prompt_builder.py` - SAME |
| **Cards** | Hebrew titles, child development icons | English titles, legal icons | `card_generator.py` - SAME |

**The engine never changes. Only domain configuration changes.**

This is the power of proper abstraction: **write once, configure many times**.
