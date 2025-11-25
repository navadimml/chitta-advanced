# Wu Wei Developer Guide
## Adding Domain Features Without Breaking the Architecture

> **פשוט - נטול חלקים עודפים**
> *Simple - devoid of excess parts*
>
> כזה שמתוכנן בדיוק כדי למלא את מטרתו.
> *Designed exactly to fulfill its purpose.*
>
> אנו רואים יופי בכל דבר המכיל את מינימום המורכבות הנדרשת.
> *We see beauty in anything containing the minimum necessary complexity.*

---

## Core Principle: Use, Don't Add

**Before adding ANY new code, ask:**
> "Does the architecture already support this through configuration?"

**Wu Wei already provides:**
- ✅ Prerequisites (any field, any condition)
- ✅ Lifecycle moments (trigger when prerequisites met)
- ✅ Cards (show/hide based on conditions)
- ✅ Data extraction (LLM extracts structured data)
- ✅ Actions (generic handler + YAML config)

**Therefore:**
- ❌ Don't add new state fields for domain logic
- ❌ Don't add new action types to enums
- ❌ Don't hardcode responses in Python
- ❌ Don't create new mechanisms

**Instead:**
- ✅ Add fields to `ExtractedData` schema
- ✅ Configure prerequisites in YAML
- ✅ Define moments in YAML
- ✅ Use existing mechanisms

---

## The Two Layers

```
┌─────────────────────────────────────────────┐
│  DOMAIN LAYER (Configuration)              │
│  - Child development concepts              │
│  - Clinical workflows                      │
│  - Specific features                       │
│  - Hebrew content                          │
│  📝 YAML files + ExtractedData schema     │
└─────────────────────────────────────────────┘
              ↓ uses ↓
┌─────────────────────────────────────────────┐
│  FRAMEWORK LAYER (Code)                    │
│  - Prerequisites engine                    │
│  - Lifecycle processor                     │
│  - Card generator                          │
│  - LLM extraction                          │
│  🐍 Python code - KEEP GENERIC            │
└─────────────────────────────────────────────┘
```

**Rule:** Domain concepts go in YAML. Framework stays generic in Python.

---

## Decision Tree: Should I Modify Python Code?

```
Need to add a feature?
│
├─ Is it domain-specific? (e.g., "filming decision", "therapy type")
│  └─ ❌ NO PYTHON CODE
│     ✅ Add to ExtractedData schema
│     ✅ Configure in YAML
│
└─ Is it a general mechanism? (e.g., "status-based card content")
   └─ ✅ YES, modify framework code
      But first: Can existing mechanisms handle it?
```

---

## Practical Examples

### Example 1: Adding "Filming Decision" Feature

**❌ WRONG WAY (Pollutes Framework):**

```python
# ❌ DON'T DO THIS - Adding to general state model
class FamilyState:
    filming_decision: str  # Domain-specific in framework!

# ❌ DON'T DO THIS - Domain-specific enum
class ActionType(Enum):
    AGREE_TO_FILMING = "agree_to_filming"  # Too specific!

# ❌ DON'T DO THIS - Hardcoded handler
def handle_action(action):
    if action == "agree_to_filming":
        return "מעולה! מתחילה הנחיות..."  # Domain text in code!
```

**✅ RIGHT WAY (Wu Wei):**

```python
# ✅ ExtractedData schema (domain data structure)
class ExtractedData(BaseModel):
    # General child info
    child_name: Optional[str] = None
    age: Optional[int] = None

    # Domain-specific fields here (not in FamilyState!)
    filming_preference: Optional[str] = None  # "wants_videos" | "report_only"
```

```yaml
# ✅ lifecycle_events.yaml (domain configuration)
moments:
  offer_filming:
    when:
      knowledge_is_rich: true
      filming_preference: null
    message: "[Gentle persuasion text]"
    ui:
      type: "conversation"

  generate_guidelines:
    when:
      filming_preference: "wants_videos"
    artifact: "baseline_video_guidelines"
    message: "מעולה! מתחילה הנחיות..."
```

**Why this is better:**
- Python code stays generic (prerequisites, moments)
- Domain logic in configuration (YAML)
- Easy to change without touching code
- Easy to add more preferences without new enums

---

### Example 2: Adding "Therapy Type" Field

**Need:** Track if parent wants speech therapy, occupational therapy, or both.

**❌ WRONG:**
```python
class TherapyDecision(Enum):  # New enum!
    SPEECH = "speech"
    OCCUPATIONAL = "ot"
    BOTH = "both"

class FamilyState:
    therapy_type: TherapyDecision  # Domain field in state!
```

**✅ RIGHT:**
```python
# ExtractedData schema
class ExtractedData(BaseModel):
    therapy_preferences: Optional[List[str]] = None  # ["speech", "ot"]
```

```yaml
# lifecycle_events.yaml
recommend_speech_therapy:
  when:
    speech_concerns: true
    therapy_preferences: null
  message: "Based on {child_name}'s speech patterns, would you like speech therapy recommendations?"

recommend_ot:
  when:
    sensory_concerns: true
    therapy_preferences: null
  message: "Would occupational therapy be helpful for {child_name}?"
```

**Principle:** Data structure in schema, logic in YAML, framework stays generic.

---

### Example 3: Adding New Card

**Need:** Show card when parent completes 30-day check-in.

**❌ WRONG:**
```python
# conversation_service.py
if days_since_start == 30 and not shown_checkin_card:
    return {
        "show_card": True,
        "card_type": "30_day_checkin"  # Hardcoded!
    }
```

**✅ RIGHT:**
```yaml
# context_cards.yaml
thirty_day_checkin_card:
  name: "מעקב 30 יום"
  priority: 95

  display_conditions:
    days_since_start: ">= 30"
    completed_30_day_checkin: false

  content:
    title: "עבר חודש! 🎉"
    body: "בואי נעשה מעקב קצר..."

  actions: [start_checkin]
```

**The framework already handles:**
- Checking prerequisites (`days_since_start >= 30`)
- Showing cards when conditions met
- Hiding after action taken
- Priority ordering

**You just configure it.**

---

## Common Mistakes & Fixes

### Mistake 1: "I need a new action type"

**❌ Wrong thought process:**
> "Parent can agree to filming, so I need `ActionType.AGREE_TO_FILMING` enum."

**✅ Right thought process:**
> "Parent makes a decision. The extraction function already captures decisions. I just need to define what field to extract to."

```python
# No new enum needed!
# extract_interview_data already handles this

# Just add to schema:
filming_preference: Optional[str] = None

# And configure what to extract in prompt:
"When parent responds about filming, extract to 'filming_preference'"
```

---

### Mistake 2: "I need special state for this feature"

**❌ Wrong:**
```python
class FamilyState:
    is_high_priority_case: bool  # Domain logic!
    therapy_urgency: str
    follow_up_needed: bool
```

**✅ Right:**
```python
class ExtractedData(BaseModel):
    # All domain fields here
    urgency_level: Optional[str] = None
    needs_immediate_followup: bool = False
```

**Rule:** If it's about the child/family (domain), it goes in `ExtractedData`. If it's about the system (framework), it goes in state.

---

### Mistake 3: "I need conditional behavior in code"

**❌ Wrong:**
```python
if parent_agreed_to_filming:
    generate_guidelines()
    show_upload_card()
else:
    show_report_option()
```

**✅ Right:**
```yaml
# lifecycle_events.yaml handles branching
generate_guidelines:
  when:
    filming_preference: "wants_videos"
  artifact: "baseline_video_guidelines"

offer_report_only:
  when:
    filming_preference: "report_only"
  message: "רוצה דוח מסכם?"
```

**The framework evaluates all moments every turn. Prerequisites create the branching logic automatically.**

---

## Step-by-Step: Adding a New Feature

### Feature: "Parent wants to involve grandparents in the process"

#### Step 1: Define the Data (Schema)
```python
# app/core/models.py - ExtractedData
class ExtractedData(BaseModel):
    # ... existing fields ...

    # New field
    involve_grandparents: bool = False
    grandparent_relationship: Optional[str] = None  # "maternal" | "paternal" | "both"
```

#### Step 2: Define When It Matters (Prerequisites)
```yaml
# lifecycle_events.yaml
offer_grandparent_guide:
  when:
    involve_grandparents: true
    artifacts.grandparent_guide.exists: false
  artifact: "grandparent_guide"
  message: "נהדר! אכין מדריך מיוחד לסבא וסבתא..."
```

#### Step 3: Define What Parent Sees (Cards)
```yaml
# context_cards.yaml
grandparent_guide_card:
  name: "מדריך לסבא וסבתא"
  priority: 80

  display_conditions:
    involve_grandparents: true
    artifacts.grandparent_guide.status: "ready"

  content:
    title: "המדריך לסבא וסבתא מוכן! 👴👵"
    body: "הכנתי מדריך מיוחד לעזור להם להבין ולתמוך..."

  actions: [view_grandparent_guide, share_guide]
```

#### Step 4: Guide the LLM (Prompt)
```python
# comprehensive_prompt_builder.py
# Add to system prompt when building context:

if not extracted_data.involve_grandparents:
    prompt += """
    If parent mentions grandparents being involved or wanting to help,
    ask if they'd like guidance for grandparents to extract to 'involve_grandparents' field.
    """
```

#### Step 5: Test
```python
# Test that extraction works
# Test that moment triggers
# Test that card appears
```

**That's it. No new enums, no new handlers, no framework changes.**

---

## When DO You Modify Framework Code?

**Only when adding general mechanisms that many features will use.**

### Example: Status-Based Card Content

**Problem:** Many cards need different content based on artifact status (generating, ready, error).

**Solution:** Add to framework (not domain-specific).

```python
# card_generator.py
# This is framework code because it's a GENERAL pattern
if "content_by_status" in card:
    status_value = context.get(f"{card_id}_status", "pending")
    content = card["content_by_status"][status_value]
```

**Why this is OK:**
- Not domain-specific ("status-based content" is general)
- Reusable by any card
- Makes configuration simpler

**Rule:** If 3+ different domain features would need it, it's framework. If it's specific to one feature, it's domain configuration.

---

## Anti-Patterns to Avoid

### 1. The "Special Case" Anti-Pattern
```python
# ❌ BAD
if artifact_id == "video_guidelines":
    # Special handling for video guidelines
    do_something_special()
elif artifact_id == "parent_report":
    # Different special handling
    do_something_else()
```

**Why bad:** Every new artifact needs code changes.

**Fix:** Make artifact behavior configurable.
```yaml
# ✅ GOOD
artifacts:
  video_guidelines:
    requires_rich_knowledge: true
    estimated_time_minutes: 5

  parent_report:
    requires_rich_knowledge: true
    estimated_time_minutes: 10
```

### 2. The "Premature Enum" Anti-Pattern
```python
# ❌ BAD
class ReportType(Enum):
    INITIAL = "initial"
    FOLLOWUP = "followup"
    SUMMARY = "summary"
```

**Why bad:** Every new report type needs enum change + code changes.

**Fix:** Use strings in configuration.
```yaml
# ✅ GOOD
generate_report:
  when:
    report_type: "initial"  # Just a string, not an enum
```

### 3. The "Business Logic in Routes" Anti-Pattern
```python
# ❌ BAD - routes.py
@router.post("/generate-report")
async def generate_report(family_id: str):
    if state.filming_agreed:
        # Include video analysis
    else:
        # Skip videos

    if state.urgency == "high":
        # Priority processing
```

**Why bad:** Domain logic hardcoded in API layer.

**Fix:** Let lifecycle system handle it.
```yaml
# ✅ GOOD - lifecycle_events.yaml
generate_full_report:
  when:
    filming_preference: "wants_videos"
    video_analysis_complete: true
  artifact: "comprehensive_report"

generate_conversation_report:
  when:
    filming_preference: "report_only"
  artifact: "conversation_based_report"
```

---

## Quick Reference Checklist

**Before making changes, ask:**

- [ ] Does this feature relate to child development domain? → ExtractedData + YAML
- [ ] Does this feature change when something happens? → Lifecycle moment
- [ ] Does this feature show something to user? → Context card
- [ ] Does this feature need user input? → LLM extraction
- [ ] Is this a new general pattern? → Maybe framework code (rare!)

**Red flags (probably doing it wrong):**

- 🚩 Adding enum with domain-specific values
- 🚩 Adding field to FamilyState for domain concept
- 🚩 Hardcoding Hebrew text in Python
- 🚩 `if feature_name == "specific_feature"` in framework code
- 🚩 Adding handler method for specific domain action

**Green lights (probably doing it right):**

- ✅ Adding field to ExtractedData
- ✅ Adding moment to lifecycle_events.yaml
- ✅ Adding card to context_cards.yaml
- ✅ Adding prerequisite condition
- ✅ Configuring in YAML, not coding in Python

---

## Philosophy Summary

### הדיוק הנדרש, לא יותר
*The required precision, no more.*

**Ask:** What is the MINIMUM change needed?
- Not "what's the safest way?" (adding new everything)
- Not "what's the most flexible?" (overengineering)
- But "what exactly fulfills this need?"

### יופי נשען על צורך
*Beauty rests on necessity.*

**Beautiful code:**
- Uses what exists
- Adds only what's missing
- Configures rather than codes
- Separates domain from framework

**Ugly code:**
- Duplicates mechanisms
- Adds "just in case"
- Mixes concerns
- Hardcodes domain logic

### העיקרון המנחה
*The guiding principle:*

> When you want to add something new, first understand what already exists.
> The architecture is like water - it flows around obstacles.
> Don't add rocks (code). Adjust the riverbed (configuration).

---

## Real-World Example: The Filming Decision Feature

**User request:** "Parent should choose whether to film or just get a report."

**Wrong approach (First instinct):**
```python
# ❌ 15 files changed, 200 lines of code
class FilmingDecision(Enum): ...
class FamilyState:
    filming_decision: FilmingDecision
def handle_filming_agreement(): ...
def handle_filming_decline(): ...
# + 10 more changes
```

**Right approach (Wu Wei):**
```python
# ✅ 1 schema field
filming_preference: Optional[str] = None
```

```yaml
# ✅ 3 YAML configurations
moments:
  offer_filming: { when: { filming_preference: null }, message: "..." }
  generate_guidelines: { when: { filming_preference: "wants_videos" }, ... }
  offer_report: { when: { filming_preference: "report_only" }, ... }
```

**Result:**
- 1 Python change vs. 15
- 20 YAML lines vs. 200 code lines
- Easy to modify vs. refactoring needed
- Clear vs. scattered logic

**This is Wu Wei.**

---

## Summary: The Developer's Mantra

```
Before I code, I ask:
  "Can I configure this instead?"

Before I add, I ask:
  "Does this already exist?"

Before I complicate, I ask:
  "What is the minimum needed?"

Beautiful software = Minimum necessary complexity
```

**The architecture is your ally. Trust it. Use it. Don't fight it.**

---

*Written with the principle: מינימום המורכבות הנדרשת - Minimum necessary complexity*
