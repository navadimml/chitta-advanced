# Chitta's Wu Wei Architecture: Conversation-First, Dependency-Based Design

**Document Version**: 3.5
**Date**: November 18, 2025
**Status**: Implemented & Simplified (פשוט - נטול חלקים עודפים)

**Latest Update**: Wu Wei v3.5 - Event-Driven Card Architecture + Domain-Agnostic Context

---

## Version History

- **v1.0** (Nov 9, 2025): Phase-based workflow (`phases.yaml`) - Traditional stage gates
- **v2.0** (Nov 9, 2025): Wu Wei dependency graph - Separate `artifacts`, `capabilities`, `lifecycle_events` sections
- **v3.0** (Nov 11, 2025): **Simplified Wu Wei** - Unified `moments` structure (50% less configuration, 100% functionality)
- **v3.5** (Nov 18, 2025): **Event-Driven Cards** - Cards unified with moments, domain-agnostic context, accurate message timing

### What's New in v3.0

**Before (v2.0)** - Three redundant sections:
```yaml
artifacts:
  baseline_video_guidelines:
    prerequisites: { knowledge_is_rich: true }
    unlocks: [video_upload]
    event: guidelines_ready  # Links to separate section

lifecycle_events:
  guidelines_ready:
    message: "ההנחיות מוכנות!"
    ui_context: {...}

capabilities:
  video_upload:
    prerequisites: { ... }  # DUPLICATE!
```

**After (v3.0)** - One unified section:
```yaml
moments:
  guidelines_ready:
    when: { knowledge_is_rich: true }
    artifact: "baseline_video_guidelines"
    message: "ההנחיות מוכנות!"
    ui: { type: "card", default: "..." }
    unlocks: ["upload_videos"]
```

**Result**: 208 lines (down from 360), zero redundancy, same functionality.

### What's New in v3.5

**Event-Driven Card Architecture** - Cards now unified with moments:

**Before (v3.0)** - Cards duplicated prerequisites:
```yaml
# lifecycle_events.yaml
moments:
  guidelines_ready:
    when: { knowledge_is_rich: true }
    artifact: "baseline_video_guidelines"
    unlocks: ["view_video_guidelines"]

# context_cards.yaml (separate file)
cards:
  guidelines_ready_card:
    display_conditions:  # ❌ DUPLICATE prerequisites
      artifacts.baseline_video_guidelines.exists: true
      user_actions.viewed_guidelines: false
    content:
      title: "ההנחיות מוכנות! 🎬"
```

**After (v3.5)** - Cards live IN moments:
```yaml
moments:
  guidelines_ready:
    when: { knowledge_is_rich: true }
    artifact: "baseline_video_guidelines"

    # 🌟 Card displays when moment triggers (event-driven)
    card:
      card_type: success
      title: "ההנחיות מוכנות! 🎬"
      body: "הכנתי לך הנחיות..."
      actions: [view_video_guidelines]
```

**Domain-Agnostic Context** - Backend no longer hardcodes fields:
```python
# Before: Domain-specific field extraction
context = {
    "child_name": extracted_data.get("child_name"),  # ❌ Hardcoded
    "primary_concerns": extracted_data.get("primary_concerns"),
}

# After: Generic structure passing
context = {
    "extracted_data": session.extracted_data,  # ✅ Cards pick what they need
    "artifacts": session.artifacts,
}
```

**Accurate Message Timing** - User messages saved BEFORE lifecycle checks:
- Fixes off-by-one message_count bug
- Ensures knowledge_is_rich triggers at correct time
- Moments appear when they should

**Result**: Zero card duplication, domain-agnostic backend, accurate prerequisites.

---

## Table of Contents

1. [Philosophy: The Essence of Wu Wei](#philosophy-the-essence-of-wu-wei)
2. [The Problem with Stage-Based Thinking](#the-problem-with-stage-based-thinking)
3. [The Solution: Continuous Conversation + Dependency Graph](#the-solution-continuous-conversation--dependency-graph)
4. [Core Principles](#core-principles)
5. [Technical Architecture](#technical-architecture)
6. [User Experience Journey](#user-experience-journey)
7. [Implementation Guide](#implementation-guide)
8. [Examples & Scenarios](#examples--scenarios)

---

## Philosophy: The Essence of Wu Wei

### What is Wu Wei?

**Wu Wei** (無為) means "effortless action" or "action through non-action" in Taoist philosophy. It's the art of accomplishing goals by working with natural forces rather than against them.

In Chitta's context, Wu Wei means:

- **Natural flow** over forced progression
- **Parent agency** over system control
- **Gentle guidance** over rigid gates
- **Emerging capabilities** over locked stages
- **Conversation primacy** over workflow steps

### Wu Wei Applied to Chitta

Traditional software forces users through rigid workflows:
```
Step 1 → Complete Step 1 → Unlock Step 2 → Complete Step 2 → Unlock Step 3
```

Chitta flows naturally like conversation:
```
Conversation (ongoing)
    ↓
Knowledge accumulates
    ↓
Capabilities emerge when ready
    ↓
Parent explores freely
    ↓
Chitta guides gently when needed
```

**Key insight**: Parents don't complete "stages" - they have **conversations** that naturally accumulate **knowledge**, which gradually **unlocks capabilities**.

---

## The Problem with Stage-Based Thinking

### What We Were Doing Wrong

**Stage-based architecture** (the old way):

```yaml
stages:
  - interview:
      required: true
      locked_until: "start"
      blocks: [guidelines, upload, analysis]

  - guidelines_preparation:
      required: true
      locked_until: "interview complete"
      blocks: [upload, analysis]

  - video_upload:
      required: true
      locked_until: "guidelines viewed"
      blocks: [analysis]

  - analysis:
      locked_until: "videos uploaded"
```

**Problems with this approach:**

1. **❌ False boundaries**: There's no clear "interview ending" - conversation is continuous
2. **❌ Parent feels constrained**: Can't explore or ask "what's next?" during "interview"
3. **❌ Rigid progression**: Must complete A before B, even if parent wants to skip
4. **❌ Chitta can't adapt**: Locked into stage-specific behaviors
5. **❌ Artificial gates**: "You can't do X until Y is complete" feels restrictive
6. **❌ Poor UX**: Progress bars like "76%" feel incomplete when parent feels done

### The "Interview" Misconception

We were thinking:
> "Interview is a phase that must be completed before moving to the next phase"

**Reality**:
> "Interview is just the **first conversation**. Conversation never stops. Knowledge accumulates continuously. The parent can ask about filming or uploading **at any time**, and Chitta responds based on **what's available**, not what **stage** we're in."

---

## The Solution: Continuous Conversation + Dependency Graph

### The New Mental Model

**Three core concepts:**

1. **Conversation**: Always ongoing, never "complete"
2. **Knowledge**: Accumulates continuously from conversation
3. **Capabilities**: Unlock when prerequisites (knowledge) are met

```
                    CONVERSATION (continuous)
                           ↓
                    KNOWLEDGE GRAPH
                (what we know about family)
                           ↓
                  PREREQUISITE CHECKING
                (do we have enough to do X?)
                           ↓
                   CAPABILITIES UNLOCK
              (cards appear, actions available)
                           ↓
                    PARENT EXPLORES
                  (uses capabilities freely)
                           ↓
              More conversation, more knowledge...
```

### No Phases, Only Dependencies

Instead of:
```python
if phase == "interview":
    allow_conversation()
    block_guidelines()
    block_upload()
```

We have:
```python
# Check what's possible based on current knowledge
capabilities = {
    "generate_guidelines": check_prerequisites("video_guidelines", knowledge),
    "upload_video": check_prerequisites("video_upload", knowledge),
    "view_report": check_prerequisites("assessment_report", knowledge),
    "ask_questions": True,  # ALWAYS available
}

# Show what's available, hide what's not
# Parent can ask about anything, Chitta guides based on readiness
```

---

## Core Principles

### 1. Conversation Never Stops

**Principle**: Conversation is the **primary mode** of interaction, not a phase.

**Implications**:
- Breadcrumb always shows: "משוחחים עם צ'יטה 💬"
- Input area is always available (except during backend processing)
- Parent can ask "מה הלאה?" or "איך זה עובד?" **at any point**
- Other activities (uploading, viewing reports) are **contextual additions**, not replacements

**Example**:
```
Parent is viewing video guidelines deep view
Input area still visible at bottom: "יש לך שאלות?"
Parent can ask: "למה צריך לצלם את זה?"
Chitta responds conversationally while guidelines still open
```

### 2. Knowledge Accumulates Continuously

**Principle**: Every conversation turn adds to what we know about the family.

**Implications**:
- No "interview complete" checkpoint
- No minimum required before moving forward
- Quality of knowledge matters more than quantity
- Knowledge informs **prerequisite checking**, not stage gates

**Example**:
```python
# Knowledge state at any moment
knowledge = {
    "child_name": "דניאל",
    "age": 3.5,
    "primary_concerns": ["speech"],
    "concern_details": "אומר רק מילים בודדות, לא משפטים. התחיל לדבר מאוחר.",
    "strengths": "אוהב לבנות, משחק יפה לבד",
    "developmental_history": "",
    "family_context": "",
}

# Enough for guidelines? Check prerequisites
can_generate_guidelines = (
    knowledge.child_name and
    knowledge.age and
    len(knowledge.primary_concerns) > 0 and
    len(knowledge.concern_details) > 100
)
# → True! Offer to generate
```

### 3. Prerequisites Enable, Don't Gate

**Principle**: Prerequisites determine what's **recommended** or **ready**, not what's **blocked**.

**Implications**:
- Parent can ask about anything anytime
- Chitta responds contextually based on readiness
- "Not ready yet" → gentle guidance back, not hard block
- Prerequisites are **qualitative** (enough knowledge?) not **quantitative** (76%?)

**Example**:
```
Parent: "רוצה לראות דוח"

# Check prerequisites
has_videos = uploaded_videos_count > 0
has_analysis = video_analysis_complete

if has_analysis and report_exists:
    Chitta: "בטח! הדוח מוכן. פותחת לך עכשיו"

elif has_videos:
    Chitta: "הסרטונים שלך בניתוח. הדוח יהיה מוכן בקרוב!"

elif can_generate_guidelines:
    Chitta: "אני יכולה להכין לך קודם הנחיות לצילום, ואז נעלה סרטונים. בסדר?"

else:
    Chitta: "בואי נשוחח עוד קצת כדי שאוכל להכין לך הנחיות מותאמות"
```

**Note**: No harsh blocks, just **conversational redirection** based on what's ready.

### 4. Capabilities Emerge Gradually

**Principle**: New actions become available as prerequisites are met, not at stage transitions.

**Implications**:
- Cards appear/disappear based on **dependency rules**, not phase
- Actions unlock organically during conversation
- Parent discovers capabilities naturally
- No sudden "you're now in upload phase" transitions

**Example**:
```yaml
# Dependency rules for cards
guidelines_offer_card:
  shows_when:
    - video_guidelines.prerequisites_met: true
    - video_guidelines.exists: false
    - conversation_depth: sufficient

guidelines_ready_card:
  shows_when:
    - video_guidelines.exists: true
    - user_viewed: false

upload_available_card:
  shows_when:
    - video_guidelines.exists: true
    - user_viewed_guidelines: true
    - uploaded_videos_count: 0
```

**User sees**: Cards naturally appear as they talk, creating a sense of **emerging progress** rather than **locked gates**.

### 5. Chitta Guides, Doesn't Control

**Principle**: Chitta **steers** conversation toward needed information but respects parent agency.

**Implications**:
- Proactive suggestions, not demands
- Parent can ignore suggestions and explore
- Chitta adapts to parent's path
- No "you must do X" - only "would you like to do X?"

**Example**:
```
# Chitta has enough for guidelines but parent keeps talking

Chitta detects: Prerequisites met for video_guidelines

# Chitta doesn't STOP conversation or FORCE transition
# Instead, naturally offers when appropriate:

Parent: "הוא גם לא ממש אוהב לשתף צעצועים"
Chitta: "מבינה. זה מתקשר למה ששיתפת על החברתי.

        דרך אגב, יש לי כבר מספיק מידע כדי להכין לך הנחיות צילום מותאמות.
        רוצה שאכין? או שיש עוד משהו שחשוב לך לשתף?"

# Parent chooses:
Option A: "כן, תכיני" → Generate
Option B: "עוד רגע, יש לי עוד משהו" → Continue conversation
Option C: "מה זה הנחיות?" → Explain, then offer again
```

### 6. Radical Simplicity in UX

**Principle**: User should never think "what do I do now?" - it should be obvious.

**Implications**:
- One clear primary action per state
- Minimal visual complexity
- Conversational prompts instead of UI instructions
- Actions reveal themselves naturally

**Example**:
```
State: Guidelines ready, not viewed yet

What user sees:
1. Conversation ongoing (can still chat)
2. ONE prominent card: "ההנחיות מוכנות! 🎬" [לחצי לצפייה]
3. Chitta's message: "הכנתי לך הנחיות! לחצי על הכרטיס למטה"

No confusion about "what next?" - it's obvious: click the card.
```

### 7. Proactive Surfacing (Parents Don't Know What Exists)

**Principle**: Parents don't know the internal structure of the app - they cannot ask for everything.

**THE CRITICAL INSIGHT:**

A parent using Chitta for the first time:
- ❌ Doesn't know video guidelines exist
- ❌ Doesn't know they should upload videos
- ❌ Doesn't know a report will be generated
- ❌ Doesn't know what questions they can ask
- ❌ Doesn't know what actions are available

**We cannot rely on parents asking for everything.**

**Solution - Two Information Channels:**

#### Channel 1: Conversation Window (What Chitta Says)

Chitta **proactively offers** capabilities when ready:

```
# Prerequisites met for guidelines
# DON'T wait for parent to ask "can you make guidelines?"
# DO proactively offer:

Chitta: "יש לי מספיק מידע כדי להכין לך הנחיות צילום מותאמות
         במיוחד לדניאל. רוצה שאכין?"
```

#### Channel 2: Context Cards (Visual Actions)

Cards appear **automatically** when actions are available:

```yaml
guidelines_ready_card:
  appears_automatically: true  # Parent doesn't search for it
  content:
    title: "ההנחיות מוכנות! 🎬"
    body: "הנחיות צילום מותאמות לדניאל"
    action: "לחצי לצפייה"  # Clear what to do
```

**Together**: Parent **always knows** what's happening and what they can do.

#### The "Three Questions" Test

At any moment, parent should be able to answer these **without asking**:

1. **"What's happening right now?"**
   - Answer in: Chitta's latest message OR card title
   - Example: "מכינה עבורך..." OR "הכנתי לך הנחיות!"

2. **"What can I do now?"**
   - Answer in: Card action button OR Chitta's prompt
   - Example: [לחצי לצפייה] OR "רוצה שאכין?"

3. **"What's next in the process?"**
   - Answer in: Chitta's guidance OR next card appearing
   - Example: "אחרי שתקראי את ההנחיות, נוכל להעלות סרטונים"

**If parent can't answer these → UX failure.**

#### Proactive Card Sequencing

Cards appear **in logical sequence**, creating **breadcrumbs**:

```
1. Card appears: "מוכנ/ה להנחיות צילום? 🎬"
   ↓ Parent clicks "כן"

2. Card changes: "מכינה עבורך... ⏳"
   ↓ Wait (5 seconds)

3. Card changes: "ההנחיות מוכנות! 🎬"
   ↓ Parent clicks "לחצי לצפייה"

4. Opens: Guidelines deep view
   ↓ Parent reads, closes

5. New card: "מוכנ/ה להעלות סרטונים? 📹"
   ↓ Next step is clear
```

**Parent never wonders "what now?"** - each step leads naturally to the next.

#### Contextual Relevance

**Only show what's relevant to current context:**

```python
def get_visible_cards(state: FamilyState) -> List[Card]:
    """Show ONLY cards relevant to current state"""

    visible = []

    # Has guidelines but not viewed? Show that!
    if state.artifacts["video_guidelines"].exists and not state.user_actions["viewed_guidelines"]:
        visible.append(guidelines_ready_card)
        # DON'T show upload card yet - not relevant

    # Viewed guidelines? NOW show upload
    elif state.user_actions["viewed_guidelines"] and state.uploaded_videos_count == 0:
        visible.append(upload_video_card)
        # DON'T show guidelines again - already viewed

    return visible
```

**Result**: Parent sees **1-2 cards maximum**, focused on **what matters now**.

---

## Technical Architecture

### State Model

**OLD (phase-based)**:
```python
class InterviewState:
    phase: Literal["screening", "preparing", "guidelines_ready", "uploading"]
    extracted_data: ExtractedData
    completeness: float  # 0.0 to 1.0
```

**NEW (dependency-based)**:
```python
class FamilyState:
    # Conversation is always active
    conversation_active: bool = True

    # Knowledge accumulates
    extracted_data: ExtractedData
    conversation_history: List[Message]

    # Artifacts that can be generated
    artifacts: Dict[str, Artifact] = {
        "interview_summary": Artifact(exists=False, status=None),
        "video_guidelines": Artifact(exists=False, status=None),
        "assessment_report": Artifact(exists=False, status=None),
    }

    # User actions tracked
    user_actions: Dict[str, bool] = {
        "viewed_guidelines": False,
        "uploaded_first_video": False,
        "viewed_first_report": False,
    }

    # Metadata
    created_at: datetime
    last_active: datetime

class Artifact:
    exists: bool
    status: Optional[Literal["generating", "ready"]]
    content: Optional[str]
    generated_at: Optional[datetime]
    prerequisites_met: bool  # Calculated dynamically
```

### v3.0: Unified Moments Structure (פשוט - נטול חלקים עודפים)

**Configuration file**: `backend/config/workflows/lifecycle_events.yaml`

#### The Simplification Principle

Wu Wei v3.0 eliminates redundancy by merging three sections into one:

**Moments** = When + What + Message + UI + Unlocks

```yaml
moments:
  guidelines_ready:
    # WHEN does this happen? (Prerequisites)
    when:
      knowledge_is_rich: true

    # WHAT artifact gets generated? (Optional)
    artifact: "baseline_video_guidelines"

    # WHAT message does Chitta send? (Optional)
    message: "ההנחיות מוכנות! 📹"

    # WHAT UI guidance? (Optional, platform-aware)
    ui:
      type: "card"  # card, button, modal, banner, etc.
      default: "תראי את הכרטיס 'הנחיות צילום' ב'פעיל עכשיו' למטה"
      mobile: "לחצי על 'הנחיות' בתפריט התחתון"  # Only if different

    # WHAT capabilities unlock? (Optional)
    unlocks:
      - upload_videos
```

#### Always Available Capabilities

```yaml
always_available:
  - conversation      # Talk to Chitta anytime
  - journaling        # Record observations
  - consultation      # Get answers and guidance
```

#### Key Differences from v2.0

| Aspect | v2.0 (Redundant) | v3.0 (Unified) |
|--------|------------------|----------------|
| **Prerequisites** | Defined in both `artifacts` AND `capabilities` | Defined once in `when` |
| **Event mapping** | Artifact has `event:` field linking to separate section | Moment ID IS the event name |
| **Message location** | Separate `lifecycle_events` section | Directly in moment |
| **UI guidance** | Nested `ui_context` with card-specific fields | Flat `ui` with platform fields |
| **Total sections** | 7 (artifacts, capabilities, lifecycle_events, prerequisite_rules, state_indicators, metadata, philosophy) | 3 (always_available, moments, metadata) |

### v3.5: Event-Driven Card Architecture

**Two Types of Cards**:

1. **Event-Triggered Cards** (in `lifecycle_events.yaml`)
   - One-time celebrations/transitions
   - Display when moment triggers
   - Live IN the moment definition
   - No separate display_conditions needed

2. **State-Driven Cards** (in `context_cards.yaml`)
   - Persistent indicators/reminders
   - Display while conditions are true
   - Examples: conversation_depth, video_guidelines_reminder

**Example:**

```yaml
# lifecycle_events.yaml
moments:
  guidelines_ready:
    when: { knowledge_is_rich: true }
    artifact: "baseline_video_guidelines"

    # 🌟 Card appears when moment triggers (event-driven)
    card:
      card_type: success
      priority: 100
      title: "ההנחיות מוכנות! 🎬"
      body: "הכנתי לך הנחיות צילום מותאמות ל{child_name}."
      actions: [view_video_guidelines]
      dismissible: false
```

**Backend Flow:**

```python
# 1. Moment triggers
lifecycle_result = await lifecycle_manager.process_lifecycle_events(...)

# 2. Extract event cards
event_cards = self._extract_event_cards(lifecycle_result)

# 3. Generate state cards
state_cards = card_generator.get_visible_cards(context)

# 4. Merge: Event cards first (higher priority)
context_cards = event_cards + state_cards

# 5. Send to frontend
return {"ui_data": {"cards": context_cards}}
```

**Domain-Agnostic Context:**

Backend passes generic structures, cards resolve fields via placeholders:

```python
# Backend (domain-agnostic)
context = {
    "extracted_data": session.extracted_data,  # Whole object
    "artifacts": session.artifacts,
    "message_count": len(conversation_history),
}

# Card YAML (domain-specific)
title: "פרופיל: {child_name}"  # Resolved from extracted_data.child_name
body: "גיל {age}"               # Resolved from extracted_data.age
```

**Message Timing Fix:**

User messages now saved BEFORE lifecycle checks for accurate message_count:

```python
# 1. Extract data from user message
# 2. 💾 Save user message (NEW: moved before lifecycle)
# 3. 🔄 Refresh session (get updated count)
# 4. ✅ Check lifecycle events (sees correct message_count)
# 5. Generate response
# 6. 💾 Save assistant response
```
| **Lines of config** | 360 | 208 |

#### Example: Complete Moment

```yaml
moments:
  report_ready:
    when:
      baseline_video_analysis.exists: true
      OR:
        conversation_knowledge_is_rich: true

    artifact: "baseline_parent_report"

    message: |
      הדוח מוכן! 📄

      זה היה תהליך עשיר - תודה שהשקעת את הזמן לשתף ולצלם.
      מעכשיו אני כאן בשבילך לכל שאלה. 💙

    ui:
      type: "card"
      default: "לחצי על הכרטיס 'מדריך להורים' ב'פעיל עכשיו' למטה"

    unlocks:
      - view_reports
      - find_experts
      - start_re_assessment
```

#### How It Works

```python
# LifecycleManager simplified in v3.0
moments = config.get("moments", {})

for moment_id, moment_config in moments.items():
    # Check prerequisites from 'when' field
    prerequisites = moment_config.get("when")
    prereqs_met = evaluate_prerequisites(prerequisites, context)

    # If prerequisites just became met (transition)
    if prereqs_met and not previously_met:

        # Generate artifact if defined
        artifact_id = moment_config.get("artifact")
        if artifact_id:
            generate_artifact(artifact_id, moment_config, context)

        # Send message if defined
        message = moment_config.get("message")
        if message:
            send_message(message.format(child_name=child_name))

        # Include UI guidance if defined
        ui_context = moment_config.get("ui")
        if ui_context:
            include_ui_guidance(ui_context, platform)

        # Unlock capabilities if defined
        unlocks = moment_config.get("unlocks", [])
        unlock_capabilities(unlocks)
```

**Benefits**:
- ✅ Everything about a moment in ONE place
- ✅ No redundant prerequisite definitions
- ✅ No separate event mapping needed
- ✅ Flatter, simpler structure
- ✅ Easy to understand and modify
- ✅ 50% less configuration

### Prerequisite System

**Core function**:
```python
def check_prerequisites(
    capability: str,
    state: FamilyState
) -> PrerequisiteCheck:
    """
    Check if prerequisites are met for a capability.

    Returns:
        PrerequisiteCheck with:
            - met: bool (are prerequisites satisfied?)
            - missing: List[str] (what's missing?)
            - readiness: Literal["ready", "need_more", "optional"]
            - suggestion: str (what to tell parent)
    """

    if capability == "video_guidelines":
        has_basic = state.extracted_data.child_name and state.extracted_data.age
        has_concerns = len(state.extracted_data.primary_concerns) > 0
        has_details = len(state.extracted_data.concern_details or "") > 100

        if has_basic and has_concerns and has_details:
            return PrerequisiteCheck(
                met=True,
                readiness="ready",
                suggestion="יש לי מספיק מידע להכין הנחיות. רוצה?"
            )
        else:
            missing = []
            if not has_basic:
                missing.append("שם וגיל")
            if not has_concerns:
                missing.append("תחומי דאגה")
            if not has_details:
                missing.append("עוד פרטים על הדאגות")

            return PrerequisiteCheck(
                met=False,
                missing=missing,
                readiness="need_more",
                suggestion=f"בואי נשוחח עוד קצת על: {', '.join(missing)}"
            )

    elif capability == "video_upload":
        # Can ALWAYS upload, but better with guidelines
        has_guidelines = state.artifacts["video_guidelines"].exists

        return PrerequisiteCheck(
            met=True,  # Never blocked
            readiness="optional" if not has_guidelines else "ready",
            suggestion=(
                "אפשר להעלות עכשיו, אבל אני ממליצה קודם לקרוא את ההנחיות"
                if not has_guidelines else
                "מוכנ/ה להעלות סרטונים?"
            )
        )
```

### Artifact Generation

**Triggered by user intent + prerequisites**:

```python
async def handle_user_intent(
    family_id: str,
    intent: Intent,
    state: FamilyState
):
    """
    Handle user expressing intent to do something.

    User can express intent via:
    - Direct question: "איך מעלים סרטון?"
    - Direct request: "תכיני לי הנחיות"
    - Function call: check_interview_completeness
    - Chitta suggestion: "רוצה שאכין הנחיות?"
    """

    if intent.type == "generate_guidelines":
        # Check prerequisites
        prereq_check = check_prerequisites("video_guidelines", state)

        if prereq_check.met:
            # Start generation
            state.artifacts["video_guidelines"].status = "generating"

            # Show loading card
            await send_card_update(family_id, "preparing_guidelines_card")

            # Generate with strong model
            guidelines = await generate_video_guidelines_artifact(
                family_id=family_id,
                model="gemini-2.0-flash-exp",
                extracted_data=state.extracted_data
            )

            # Store artifact
            state.artifacts["video_guidelines"] = Artifact(
                exists=True,
                status="ready",
                content=guidelines,
                generated_at=datetime.now()
            )

            # Notify user
            await send_message(
                family_id,
                "הכנתי לך! 🎉 לחצי על הכרטיס למטה כדי לראות את ההנחיות"
            )

            # Show ready card
            await send_card_update(family_id, "guidelines_ready_card")

        else:
            # Prerequisites not met - guide conversationally
            await send_message(
                family_id,
                prereq_check.suggestion
            )
```

### Qualitative Progress Indicators

**Replace percentage with conversational hints:**

```python
def get_knowledge_depth_indicator(data: ExtractedData) -> dict:
    """Get qualitative indicator of conversation depth"""

    if not data.child_name:
        return {
            "emoji": "👋",
            "text": "התחלנו להכיר",
            "level": "minimal"
        }

    if not data.primary_concerns or len(data.concern_details or "") < 100:
        return {
            "emoji": "💭",
            "text": f"מכירים את {data.child_name}...",
            "level": "growing"
        }

    if len(data.concern_details or "") < 300:
        return {
            "emoji": "💭",
            "text": "השיחה מתעמקת",
            "level": "developing"
        }

    return {
        "emoji": "💙",
        "text": f"הכרנו את {data.child_name}",
        "level": "rich"
    }
```

### Card System (Dependency-Based)

**Configuration** (`context_cards.yaml`):

```yaml
cards:
  conversation_depth_hint:
    name: "רמז על עומק השיחה"
    card_type: info
    priority: 30

    display_conditions:
      conversation_active: true

    content:
      title: "{knowledge_depth_indicator}"
      body: "תודה על השיתוף 💙"

    dismissible: true

  guidelines_offer:
    name: "הצעה להכנת הנחיות"
    card_type: suggestion
    priority: 80

    display_conditions:
      artifacts.video_guidelines.prerequisites_met: true
      artifacts.video_guidelines.exists: false
      user_declined_offer: false

    content:
      title: "מוכנ/ה להנחיות צילום? 🎬"
      body: "יש לי מספיק מידע כדי להכין לך הנחיות מותאמות"

    actions:
      - name: "כן, תכיני"
        triggers: generate_guidelines
      - name: "עוד רגע"
        dismisses_card: true

  guidelines_preparing:
    name: "מכינה הנחיות"
    card_type: loading
    priority: 100

    display_conditions:
      artifacts.video_guidelines.status: "generating"

    content:
      title: "מכינה עבורך... ⏳"
      body: |
        ✨ הנחיות צילום מותאמות
        רגע קטן...

    dismissible: false
    auto_replaces_with: "guidelines_ready"

  guidelines_ready:
    name: "הנחיות מוכנות"
    card_type: success
    priority: 100

    display_conditions:
      artifacts.video_guidelines.exists: true
      user_actions.viewed_guidelines: false

    content:
      title: "ההנחיות מוכנות! 🎬"
      body: "הנחיות צילום מותאמות ל{child_name}"

    actions:
      - name: "לחצי לצפייה"
        opens_view: "guidelines_deep_view"
        tracks_action: "viewed_guidelines"

  upload_available:
    name: "אפשר להעלות"
    card_type: primary
    priority: 90

    display_conditions:
      artifacts.video_guidelines.exists: true
      user_actions.viewed_guidelines: true
      uploaded_videos_count: 0

    content:
      title: "מוכנ/ה להעלות? 📹"
      body: "קראת את ההנחיות - אפשר להתחיל"

    actions:
      - name: "העלי סרטונים"
        opens_view: "video_upload_view"
```

### Proactive Suggestion System

```python
async def suggest_next_capability(
    family_id: str,
    state: FamilyState
) -> Optional[str]:
    """
    Proactively suggest next capability when prerequisites are met.

    This ensures parent doesn't have to ask - Chitta offers.
    """

    # Check what's ready but not yet offered
    if not state.artifacts["video_guidelines"].exists:
        prereq_check = check_prerequisites("video_guidelines", state)
        if prereq_check.met and not state.user_actions.get("offered_guidelines"):
            state.user_actions["offered_guidelines"] = True
            return "generate_guidelines"

    elif state.artifacts["video_guidelines"].exists and not state.user_actions["viewed_guidelines"]:
        return "view_guidelines"

    elif state.user_actions["viewed_guidelines"] and state.uploaded_videos_count == 0:
        if not state.user_actions.get("offered_upload"):
            state.user_actions["offered_upload"] = True
            return "upload_video"

    elif state.uploaded_videos_count > 0 and state.analysis_status == "complete":
        if not state.user_actions.get("offered_report"):
            state.user_actions["offered_report"] = True
            return "view_report"

    return None


def inject_proactive_suggestion(
    base_response: str,
    suggestion: Optional[str],
    state: FamilyState
) -> str:
    """
    Inject proactive suggestion into Chitta's response.
    Makes capabilities discoverable without parent asking.
    """

    if not suggestion:
        return base_response

    suggestions = {
        "generate_guidelines": f"\n\nדרך אגב - יש לי מספיק מידע כדי להכין לך הנחיות צילום מותאמות ל{state.extracted_data.child_name}. רוצה שאכין?",

        "view_guidelines": f"\n\nהכנתי לך הנחיות צילום! לחצי על הכרטיס למטה כדי לקרוא",

        "upload_video": f"\n\nקראת את ההנחיות? מוכנ/ה להעלות סרטונים?",

        "view_report": f"\n\nהדוח מוכן! רוצה לראות אותו?"
    }

    return base_response + suggestions.get(suggestion, "")
```

---

## User Experience Journey

### Journey 1: First-Time Parent (Natural Flow)

**Parent opens Chitta, has NEVER used it before:**

```
1. Chitta: "שלום! אני צ'יטה. אני כאן לעזור לך להבין את ההתפתחות
            של הילד/ה שלך. בואי נתחיל - ספרי לי על הילד/ה"

   What parent knows:
   ✅ What Chitta is
   ✅ What to do next (ספרי לי)
   ✅ How to proceed (input box visible)

2. Parent: "יש לי בן בן 3, דניאל"
   Chitta: "נעים להכיר את דניאל! מה מעסיק אותך?"

3. Parent: "הוא לא ממש מדבר טוב"
   Chitta: "ספרי לי עוד - איך זה בא לידי ביטוי?"

   [Card appears: "השיחה מתעמקת 💭"]

4. Parent: "הוא אומר רק מילים בודדות"
   Chitta: "מבינה. עוד משהו חשוב?"

5. Parent: "הוא אוהב לבנות, משחק יפה לבד"
   Chitta: "נהדר! יש עוד משהו?"

6. Parent: "זה בעצם הכל"

   [Prerequisites met! ✓]

   Chitta: "תודה על השיתוף! יש לי מספיק מידע כדי להכין לך
           הנחיות צילום מותאמות לדניאל. רוצה שאכין?"

   [Card appears: "מוכנ/ה להנחיות צילום? 🎬" [כן]]

   What parent knows:
   ✅ Chitta CAN create guidelines (didn't know this existed!)
   ✅ What guidelines are (הנחיות צילום)
   ✅ They're personalized (לדניאל)
   ✅ How to proceed (click כן)
   ✅ It's optional (רוצה? not "you must")

7. Parent clicks "כן"

   Chitta: "מכינה... רגע קטן"
   [Card: "מכינה עבורך... ⏳"]

   What parent knows:
   ✅ Something is being prepared
   ✅ It will take a moment
   ✅ No action needed

8. [5 seconds later]

   Chitta: "מוכן! הכנתי לך הנחיות שמתמקדות בדיבור ותקשורת של דניאל.
           לחצי על הכרטיס למטה כדי לקרוא"

   [Card: "ההנחיות מוכנות! 🎬" [לחצי לצפייה]]

   What parent knows:
   ✅ Guidelines ready
   ✅ What they focus on (דיבור ותקשורת)
   ✅ How to view (לחצי על הכרטיס)

9. Parent clicks → Guidelines open

10. Parent reads, closes view

    [New card: "מוכנ/ה להעלות? 📹"]

    Chitta: "קראת את ההנחיות? מוכנ/ה להעלות סרטונים?"
```

**Key points:**
- ✅ Parent NEVER had to ask what's possible
- ✅ Each step was surfaced proactively
- ✅ Clear what to do at every moment
- ✅ Natural conversation flow maintained

### Journey 2: Curious Parent (Explores Before Ready)

```
1. Parent: "איך מעלים סרטון?"  ← Jumps ahead!

2. Chitta checks prerequisites:
   - has_guidelines? No
   - has_knowledge? No
   - can_upload? Yes (not blocked!)

3. Chitta: "שאלה טובה! אפשר להעלות סרטונים בכל רגע.

           אבל אני ממליצה קודם שנכיר קצת - זה יעזור לי להכין
           לך הנחיות ממש מותאמות לצרכים של הילד/ה שלך.

           רוצה שנתחיל? ספרי לי על הילד/ה"

   What parent knows:
   ✅ Can upload anytime (not blocked)
   ✅ Better to talk first (gentle guidance)
   ✅ Why it's better (הנחיות מותאמות)
   ✅ What to do (ספרי לי)

4. Parent: "אוקיי. יש לי בת..."
   [Conversation continues]
```

**Key point**: Question answered honestly, gently guided back. No harsh block.

### Journey 3: Rushed Parent

```
1. Parent: "רוצה פשוט להעלות סרטון"

2. Chitta: "בסדר גמור! אני יכולה לפתוח לך את העלאת הסרטונים עכשיו.

           או - אם יש לך 2 דקות, אני יכולה להכין לך הנחיות קצרות
           שיעזרו לצלם בצורה הכי מועילה. מה נוח לך?"

3. Parent: "בואי תכיני משהו מהיר"
   [Quick 2-minute conversation]

4. Chitta: "מספיק! אני מכינה לך הנחיות קצרות"
   [Generates concise guidelines]

5. Parent uploads without reading
   → Works! Analysis proceeds

6. Later: "מה הם חיפשו?"
   Chitta: "יש לך הנחיות שהכנתי - רוצה לראות?"
```

**Key point**: Urgency respected, value offered, never forced.

---

## Implementation Guide

### Phase 1: Remove Phase System

**Files to modify:**

1. **`backend/app/services/interview_service.py`**
```python
# REMOVE:
class InterviewState:
    phase: str = "screening"

# ADD:
class InterviewState:
    conversation_active: bool = True
    artifacts: Dict[str, Artifact] = field(default_factory=dict)
    user_actions: Dict[str, bool] = field(default_factory=dict)
```

2. **`backend/app/services/conversation_service.py`**
```python
# REMOVE all phase checks:
if session.phase == "screening":
    ...

# REPLACE with prerequisite checks:
prereq_check = check_prerequisites("video_guidelines", state)
if prereq_check.met:
    ...
```

### Phase 2: Add Prerequisite System

Update **`backend/app/services/prerequisite_service.py`**:

```python
from typing import Dict, List, Literal
from dataclasses import dataclass

@dataclass
class PrerequisiteCheck:
    met: bool
    missing: List[str]
    readiness: Literal["ready", "need_more", "optional"]
    suggestion: str

class PrerequisiteService:
    def check_video_guidelines(self, state: FamilyState) -> PrerequisiteCheck:
        has_basic = state.extracted_data.child_name and state.extracted_data.age
        has_concerns = len(state.extracted_data.primary_concerns) > 0
        has_details = len(state.extracted_data.concern_details or "") > 100

        if has_basic and has_concerns and has_details:
            return PrerequisiteCheck(
                met=True,
                missing=[],
                readiness="ready",
                suggestion=f"יש לי מספיק מידע להכין הנחיות. רוצה?"
            )
        # ... handle not ready case
```

### Phase 3: Add Artifact System

Create **`backend/app/services/artifact_service.py`**:

```python
class ArtifactService:
    async def generate_video_guidelines(
        self,
        family_id: str,
        extracted_data: ExtractedData,
        model: str = "gemini-2.0-flash-exp"
    ) -> str:
        # Set status
        self.set_artifact_status(family_id, "video_guidelines", "generating")

        # Build prompt
        prompt = self._build_guidelines_prompt(extracted_data)

        # Use strong model
        strong_llm = create_llm_provider(model=model)
        result = await strong_llm.chat(
            messages=[Message(role="user", content=prompt)],
            temperature=0.5,
            max_tokens=3000
        )

        # Store
        self.store_artifact(family_id, "video_guidelines", result.content)

        return result.content
```

### Phase 4: Add Qualitative Progress

Create **`backend/app/services/knowledge_indicator_service.py`**:

```python
def get_knowledge_depth_indicator(data: ExtractedData) -> dict:
    if not data.child_name:
        return {"emoji": "👋", "text": "התחלנו להכיר"}

    if len(data.concern_details or "") < 100:
        return {"emoji": "💭", "text": f"מכירים את {data.child_name}..."}

    if len(data.concern_details or "") < 300:
        return {"emoji": "💭", "text": "השיחה מתעמקת"}

    return {"emoji": "💙", "text": f"הכרנו את {data.child_name}"}
```

### Phase 5: Update Card System

Modify **`backend/config/workflows/context_cards.yaml`**:

Replace phase-based conditions:
```yaml
# OLD:
display_conditions:
  phase: guidelines_ready

# NEW:
display_conditions:
  artifacts.video_guidelines.exists: true
  user_actions.viewed_guidelines: false
```

### Phase 6: Add Proactive Suggestions

In **`conversation_service.py`**, add:

```python
# After generating response
suggestion = await suggest_next_capability(family_id, state)
if suggestion:
    response = inject_proactive_suggestion(response, suggestion, state)
```

### Phase 7: Update Frontend

**`src/App.jsx`**:

```javascript
// OLD:
const [completeness, setCompleteness] = useState(0);
<div>השלמנו {completeness}% מהראיון</div>

// NEW:
const [knowledgeIndicator, setKnowledgeIndicator] = useState({
  emoji: "👋",
  text: "התחלנו להכיר"
});

<div className="text-sm text-gray-500">
  {knowledgeIndicator.emoji} {knowledgeIndicator.text}
</div>
```

---

## Examples & Scenarios

### Complete User Flow Example

```
INITIAL STATE:
- No knowledge collected
- No artifacts exist
- Cards: None

Parent: "שלום"
Chitta: "שלום! אני צ'יטה. ספרי לי על הילד/ה שלך"
Cards: [conversation_depth: "התחלנו להכיר 👋"]

---

AFTER SHARING NAME + AGE:
- Knowledge: name=דניאל, age=3.5
- Artifacts: None
- Cards: [conversation_depth: "מכירים את דניאל... 💭"]

---

AFTER SHARING CONCERNS:
- Knowledge: concerns=[speech], details="אומר מילים בודדות"
- Prerequisites MET: video_guidelines
- Chitta: "דרך אגב - יש לי מספיק מידע להכין הנחיות. רוצה?"
- Cards: [guidelines_offer: "מוכנ/ה להנחיות? 🎬"]

---

PARENT CLICKS "כן":
- Artifact status: video_guidelines = "generating"
- Chitta: "מכינה... רגע קטן"
- Cards: [guidelines_preparing: "מכינה עבורך... ⏳"]

---

5 SECONDS LATER:
- Artifact: video_guidelines = "ready"
- Chitta: "מוכן! לחצי על הכרטיס"
- Cards: [guidelines_ready: "ההנחיות מוכנות! 🎬"]

---

PARENT CLICKS CARD:
- Opens: Guidelines deep view
- User action: viewed_guidelines = true
- Conversation continues in background

---

PARENT CLOSES VIEW:
- Cards: [upload_available: "מוכנ/ה להעלות? 📹"]
- Chitta: "קראת את ההנחיות? מוכנ/ה להעלות?"

---

And so on... Flow continues naturally based on dependencies!
```

---

## Summary: Wu Wei Principles

**What changes:**
- ✅ Remove rigid phases → Dependency graph
- ✅ Remove "interview complete" → Continuous conversation
- ✅ Remove percentage → Qualitative hints
- ✅ Add prerequisite checking
- ✅ Add artifact generation (triggered, not forced)
- ✅ Cards based on dependencies
- ✅ Proactive surfacing of capabilities

**What stays true to Wu Wei:**
- 🌊 Natural flow - no forcing
- 🌊 Parent has agency - explores freely
- 🌊 Chitta guides - suggests when ready
- 🌊 Prerequisites enable - don't gate
- 🌊 Conversation primary - activities are context
- 🌊 Proactive surfacing - parent never guesses
- 🌊 Two channels - conversation + cards
- 🌊 Clear next steps - always obvious

**Result**: Parents experience Chitta as a **helpful, intelligent guide** that flows naturally with their needs, not a rigid system forcing them through hoops.

---

**Conversation flows like water 🌊**
**Knowledge accumulates like spring 💧**
**Capabilities emerge like flowers 🌸**
**Parents explore like wind 🍃**
**Chitta guides like the moon 🌙**

**Not forced. Not gated. Just... flowing.**

---

**End of Document** 💙
