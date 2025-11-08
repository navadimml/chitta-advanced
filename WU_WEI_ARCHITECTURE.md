# Wu Wei Architecture: The Path of Least Resistance

**思考深處 (Thinking Deeply)**

> "The wise man does nothing, yet nothing is left undone" - Tao Te Ching

After stepping back and observing the water's flow, I see now: the question is not "how to support many domains" but "what are the unchanging patterns in THIS domain's evolution?"

---

## The Complete Journey (What IS)

```
SCREENING PHASE (Weeks 1-2)
  └─ Conversation → Extract data → Completeness → Video guidelines
       └─ Videos uploaded → Analysis → Reports generated

ONGOING PHASE (Months/Years)
  └─ Consultation → Questions answered → Journal entries
       └─ Follow-up observations → Updated insights → Expert connections
           └─ New concerns → Re-assessment → Updated recommendations
```

This is not a linear flow. It's a **living relationship**.

---

## The Invariants (What Doesn't Change)

After using different domains as a thinking tool, I see three unchanging patterns:

### 1. **The Conversation Never Stops**
- It's always conversation
- Context deepens over time
- Questions are answered naturally
- Data extraction happens opportunistically

### 2. **Prerequisites Create Natural Gates**
- Some things require other things first
- Not arbitrary - they're logical dependencies
- "Can't analyze videos without videos"
- "Can't give recommendations without understanding"

### 3. **Artifacts Emerge From Process**
- Reports materialize when ready
- Guidelines appear when context is sufficient
- Summaries form from accumulated knowledge
- These aren't "generated" - they **emerge**

### 4. **Context Cards Reflect State**
- They're the **visible face** of invisible state
- Show current progress and available actions
- Change dynamically as state evolves
- Guide user naturally through the journey

---

## What Actually Needs Abstraction?

Not "domain support" - but these:

### Current Problem 1: Schema is Hardcoded
```python
# interview_service.py
class ExtractedData(BaseModel):
    child_name: Optional[str] = None
    age: Optional[float] = None
    concerns: List[str] = []
    # ... 10 more hardcoded fields
```

**Wu Wei Solution**: Schema as Data
```python
# extraction_schema.yaml
fields:
  child_name:
    type: string
    weight: 0.01  # Used in completeness calculation
    description: "שם הילד/ה"

  age:
    type: number
    weight: 0.03
    description: "גיל בשנים"

  primary_concerns:
    type: array
    options: [speech, social, motor, attention, sensory]
    weight: 0.10
    description: "תחומי דאגה עיקריים"

  concern_details:
    type: longtext
    target_length: 1000  # For completeness scoring
    weight: 0.40  # THIS is what matters most
    description: "פירוט מפורט עם דוגמאות"
```

**Benefits:**
- ✅ Add new field? Edit YAML, not code
- ✅ Change completeness weights? Edit YAML
- ✅ Easy to understand what we're collecting
- ✅ Easy to test different configurations

### Current Problem 2: Actions are Hardcoded
```python
# prerequisites.py
PREREQUISITES = {
    Action.VIEW_VIDEO_GUIDELINES: {
        "requires": [PrerequisiteType.INTERVIEW_COMPLETE],
        "explanation_to_user": "כדי ליצור הנחיות צילום..."
    },
    # ... 15 more hardcoded actions
}
```

**Wu Wei Solution**: Action Graph as Data
```python
# action_graph.yaml
actions:
  view_video_guidelines:
    requires: [interview_complete]
    explanation: "כדי ליצור הנחיות צילום מותאמות אישית, אני צריכה קודם לסיים את הראיון."
    phase: screening
    category: workflow

  upload_video:
    requires: [interview_complete]
    explanation: "נהדר שאת מוכנה להעלות סרטונים! בואי נסיים קודם את הראיון."
    phase: screening
    category: workflow

  consultation:
    requires: []  # Always available
    explanation: null
    phase: both  # Works in screening AND ongoing
    category: support
```

**Benefits:**
- ✅ See entire action graph at a glance
- ✅ Add new action? Edit YAML
- ✅ Change prerequisites? Edit YAML
- ✅ Phase-aware (screening vs ongoing)

### Current Problem 3: Phases are Implicit
```python
# Currently no explicit phase concept
# "Interview complete" triggers video guidelines
# But what about transition to ongoing phase?
```

**Wu Wei Solution**: Explicit Phase State
```python
# Phase definition
phases:
  screening:
    name: "שלב סינון וניתוח"
    focus: "intensive data collection"
    extraction_priority: high
    completeness_threshold: 0.80
    artifacts:
      - video_guidelines
      - parent_report
      - professional_report
    transitions_to: ongoing
    transition_trigger: reports_generated

  ongoing:
    name: "ליווי מתמשך"
    focus: "consultation and support"
    extraction_priority: low  # Less structured
    completeness_threshold: null  # No threshold
    artifacts:
      - journal_entries
      - follow_up_summaries
      - expert_recommendations
    transitions_to: re_assessment
    transition_trigger: new_concerns_raised

  re_assessment:
    name: "הערכה מחודשת"
    focus: "targeted re-evaluation"
    # Like screening but focused on specific areas
```

**Benefits:**
- ✅ Clear phase transitions
- ✅ Different behavior per phase
- ✅ Long-term relationship modeling
- ✅ Re-assessment as natural evolution

---

## The Simple Architecture (Wu Wei Style)

```
┌────────────────────────────────────────────────────┐
│           CONFIGURATION (YAML)                     │
│  - extraction_schema.yaml  ← What to extract       │
│  - action_graph.yaml       ← Available actions     │
│  - phases.yaml             ← Phase transitions     │
│  - artifacts.yaml          ← Document lifecycle    │
│  - context_cards.yaml      ← UI cards              │
│  - deep_views.yaml         ← Interaction spaces    │
└────────────────────────────────────────────────────┘
                      ↓ loaded by
┌────────────────────────────────────────────────────┐
│           CONFIGURATION LAYER (Python)             │
│  - config_loader.py    ← Loads and validates YAML  │
│  - schema_registry.py  ← Manages extraction schema │
│  - action_registry.py  ← Manages action graph      │
│  - phase_manager.py    ← Manages phase transitions │
│  - card_generator.py   ← Generates context cards   │
│  - view_manager.py     ← Routes to deep views      │
└────────────────────────────────────────────────────┘
                      ↓ used by
┌────────────────────────────────────────────────────┐
│           EXISTING SERVICES (Unchanged)            │
│  - conversation_service.py                         │
│  - interview_service.py                            │
│  - prerequisite_service.py                         │
└────────────────────────────────────────────────────┘
                      ↓ rendered by
┌────────────────────────────────────────────────────┐
│           UI COMPONENTS (React)                    │
│  - ConversationTranscript.jsx                      │
│  - ContextualSurface.jsx                           │
│  - DeepViewManager.jsx  ← Routes to views          │
│  - deepviews/           ← 11+ modal components     │
└────────────────────────────────────────────────────┘
```

**Key Point**: The services barely change! They just read from config instead of hardcoded constants.

---

## Example: How It Works

### Before (Hardcoded)
```python
# interview_service.py
class ExtractedData(BaseModel):
    child_name: Optional[str] = None
    age: Optional[float] = None
    concerns: List[str] = []

def calculate_completeness(data):
    score = 0.0
    if data.child_name: score += 0.01
    if data.age: score += 0.03
    if data.concerns: score += 0.10
    # ... etc
```

### After (Configuration-Driven)
```python
# interview_service.py
class ExtractionSession:
    def __init__(self, schema: ExtractionSchema):
        self.schema = schema
        self.data = {}  # Dynamic based on schema

def calculate_completeness(session):
    score = 0.0
    for field_name, field_def in session.schema.fields.items():
        value = session.data.get(field_name)
        if value:
            score += calculate_field_score(value, field_def)
    return score
```

**What Changed**: Read schema from config instead of hardcoding fields.

**What Didn't Change**: The extraction logic, the completeness calculation pattern, the conversation flow.

---

## Adding New Features (Examples)

### Example 1: Add "Sibling Information" Field
**Before**: Modify `ExtractedData` class, update completeness calculation, update prompts → **3 files, 30 minutes**

**After**: Edit `extraction_schema.yaml`:
```yaml
sibling_information:
  type: text
  weight: 0.05
  description: "מידע על אחים"
  category: context
```
→ **1 file, 2 minutes**

### Example 2: Add "Schedule Expert Meeting" Action
**Before**: Add to `Action` enum, add to `PREREQUISITES`, update service logic → **3 files, 1 hour**

**After**: Edit `action_graph.yaml`:
```yaml
schedule_expert_meeting:
  requires: [reports_generated]
  explanation: "נעדכן קודם את הדוח, ואז נמצא את המומחה המתאים"
  phase: ongoing
  category: workflow
```
→ **1 file, 5 minutes**

### Example 3: Add "Re-Assessment" Phase
**Before**: Major refactoring, new state management, complex transitions → **Multiple files, days of work**

**After**: Edit `phases.yaml`:
```yaml
re_assessment:
  name: "הערכה מחודשת"
  focus: "targeted updates"
  extraction_priority: medium
  transitions_to: ongoing
  trigger: re_assessment_initiated
```
→ **1 file, 10 minutes**

---

## The Artifact System (What's Missing)

Currently implicit. Should be explicit:

```yaml
# artifacts.yaml
artifacts:
  video_guidelines:
    name: "הנחיות צילום מותאמות אישית"
    type: document
    generated_when: interview_completeness >= 0.80
    dependencies: [interview_data]
    template: video_guidelines_template.txt
    stored_in: session.artifacts.video_guidelines

  parent_report:
    name: "מדריך להורים"
    type: document
    generated_when: video_analysis_complete
    dependencies: [interview_data, video_analysis_results]
    template: parent_report_template.txt
    stored_in: session.artifacts.parent_report

  follow_up_summary:
    name: "סיכום מעקב"
    type: document
    generated_when: journal_entries >= 5
    dependencies: [journal_entries, previous_reports]
    template: follow_up_summary_template.txt
    stored_in: session.artifacts.follow_up_summary
    phase: ongoing
```

**Benefits:**
- ✅ Clear artifact lifecycle
- ✅ Explicit dependencies
- ✅ Easy to add new artifacts
- ✅ Template-based generation

---

## The Context Card System (The Visible State)

Context cards are **the window into the invisible state**. They should also be configuration-driven:

```yaml
# context_cards.yaml
card_templates:
  # Progress cards - always shown
  interview_progress:
    type: progress
    show_when: phase == "screening"
    title: "שיחת ההיכרות"
    subtitle: "התקדמות: {completeness_pct}%"
    icon: message-circle
    status:
      if: completeness >= 0.8
      then: completed
      elif: completeness >= 0.5
      then: processing
      else: pending
    priority: 100  # Higher = shown first
    action: null  # Not clickable

  # Profile card - shown when we have basic info
  child_profile:
    type: profile
    show_when: extracted_data.child_name != null AND extracted_data.age != null
    title: "פרופיל: {child_name}"
    subtitle: "גיל {age}, {concerns_count} תחומי התפתחות"
    icon: user
    status: active
    priority: 90
    action: null

  # Action cards - shown when prerequisites met
  video_upload_ready:
    type: action
    show_when: completeness >= 0.8 AND phase == "screening"
    title: "העלאת סרטון"
    subtitle: "מוכן לשלב הבא"
    icon: video
    status: action
    priority: 80
    action:
      type: open_deep_view
      view: video_upload

  # Status cards - dynamic based on activity
  video_analyzing:
    type: status
    show_when: artifacts.videos_uploaded > 0 AND artifacts.analysis_status == "processing"
    title: "ניתוח בתהליך"
    subtitle: "בדרך כלל לוקח 24 שעות"
    icon: loader
    status: processing
    priority: 95
    action: null

  # New artifact available
  report_ready:
    type: notification
    show_when: artifacts.parent_report.status == "ready" AND artifacts.parent_report.viewed == false
    title: "מדריך להורים מוכן!"
    subtitle: "הממצאים והמלצות"
    icon: file-text
    status: new
    priority: 100
    action:
      type: open_deep_view
      view: report
      params:
        report_id: parent_report

  # Ongoing phase cards
  journal_activity:
    type: metric
    show_when: phase == "ongoing"
    title: "יומן יוני"
    subtitle: "{journal_entries_this_week} רשומות השבוע"
    icon: book-open
    status: active
    priority: 70
    action:
      type: open_deep_view
      view: journal

  # Consultation available (always in ongoing)
  consultation_available:
    type: support
    show_when: phase == "ongoing"
    title: "יש שאלות?"
    subtitle: "התייעצי איתי בכל עת"
    icon: message-circle
    status: action
    priority: 60
    action:
      type: continue_conversation
```

### Card Generation Logic

```python
# conversation_service.py - now reads from config
def generate_context_cards(session: Session, config: CardConfig) -> List[Card]:
    """Generate cards based on current state and configuration"""

    cards = []
    context = {
        "phase": session.phase,
        "completeness": session.completeness,
        "completeness_pct": int(session.completeness * 100),
        "extracted_data": session.extracted_data,
        "artifacts": session.artifacts,
        "child_name": session.extracted_data.get("child_name"),
        "age": session.extracted_data.get("age"),
        "concerns_count": len(session.extracted_data.get("primary_concerns", [])),
        "journal_entries_this_week": get_recent_journal_count(session.id, days=7),
        # ... etc
    }

    for card_id, card_template in config.card_templates.items():
        # Evaluate show_when condition
        if not eval_condition(card_template.show_when, context):
            continue

        # Build card from template with context interpolation
        card = Card(
            id=card_id,
            type=card_template.type,
            title=interpolate(card_template.title, context),
            subtitle=interpolate(card_template.subtitle, context),
            icon=card_template.icon,
            status=eval_status(card_template.status, context),
            priority=card_template.priority,
            action=card_template.action
        )
        cards.append(card)

    # Sort by priority (highest first)
    cards.sort(key=lambda c: c.priority, reverse=True)

    # Return top 4 cards
    return cards[:4]
```

### Benefits of Card Configuration

**1. Easy to Add New Cards**
```yaml
# Want to show "Expert Consultation Available" card?
expert_consultation_ready:
  show_when: artifacts.reports_generated AND phase == "ongoing"
  title: "מציאת מומחים"
  subtitle: "מבוסס על הממצאים"
  icon: users
  status: action
  action:
    type: open_deep_view
    view: expert_finder
```
→ **Just add to YAML, no code changes!**

**2. Easy to Change Priority**
```yaml
# Want interview progress to show first?
interview_progress:
  priority: 100  # Change from 80 to 100
```

**3. Easy to A/B Test**
```yaml
# Experiment A: Show video upload at 70% completeness
video_upload_ready:
  show_when: completeness >= 0.7  # Changed from 0.8

# Experiment B: Different wording
  title: "מוכנה לצלם?"  # Instead of "העלאת סרטון"
```

**4. Phase-Aware Cards**
```yaml
# Screening phase cards
interview_progress: { show_when: phase == "screening" }
video_upload_ready: { show_when: phase == "screening" }

# Ongoing phase cards
journal_activity: { show_when: phase == "ongoing" }
consultation_available: { show_when: phase == "ongoing" }

# Both phases
child_profile: { show_when: extracted_data.child_name != null }
```

**5. Dynamic Card Content**
Cards automatically update as state changes:
- Completeness increases → progress card updates
- Videos uploaded → analysis card appears
- Report ready → notification card appears
- Phase changes → different cards shown

### Card Lifecycle Example

```
Initial state (completeness: 0%)
├─ [Pending] שיחת ההיכרות - התקדמות: 0%

After some conversation (completeness: 35%)
├─ [Processing] שיחת ההיכרות - התקדמות: 35%
├─ [Active] פרופיל: יוני - גיל 3.5, 2 תחומי התפתחות

Interview complete (completeness: 85%)
├─ [Completed] שיחת ההיכרות - התקדמות: 85%
├─ [Active] פרופיל: יוני - גיל 3.5, 2 תחומי התפתחות
├─ [Action] העלאת סרטון - מוכן לשלב הבא
├─ [New] הנחיות צילום - מותאמות במיוחד עבור יוני

Videos uploaded
├─ [Processing] ניתוח בתהליך - בדרך כלל לוקח 24 שעות
├─ [Active] פרופיל: יוני
├─ [Active] יומן יוני - 0 רשומות השבוע

Reports ready (transition to ongoing phase)
├─ [New] מדריך להורים מוכן! - הממצאים והמלצות
├─ [Action] מציאת מומחים - מבוסס על הממצאים
├─ [Active] יומן יוני - 2 רשומות השבוע
├─ [Action] יש שאלות? - התייעצי איתי בכל עת
```

---

## The Deep View System (Interaction Spaces)

Deep views are **where actions happen** - the modal interfaces for specific interactions. They're the **destination** when cards are clicked or actions are requested.

### Current Deep Views

```
deepviews/
├── ConsultationView.jsx         # Q&A with Chitta
├── DocumentUploadView.jsx       # Upload diagnostic reports
├── DocumentListView.jsx         # Browse uploaded documents
├── VideoUploadView.jsx          # Upload behavioral videos
├── VideoGalleryView.jsx         # Browse uploaded videos
├── FilmingInstructionView.jsx   # How to film videos
├── JournalView.jsx              # Add/view journal entries
├── ReportView.jsx               # View parent/professional reports
├── ExpertProfileView.jsx        # Browse/connect with experts
├── MeetingSummaryView.jsx       # Pre-meeting preparation
└── ShareView.jsx                # Share reports with others
```

### Deep Views Configuration

```yaml
# deep_views.yaml
views:
  # Artifact viewers - show generated content
  report:
    component: ReportView
    type: artifact_viewer
    title: "מדריך להורים"
    requires: [reports_generated]
    data_sources:
      - artifacts.parent_report
      - session.child_profile
    phase: both  # Available in screening and ongoing
    icon: file-text

  video_gallery:
    component: VideoGalleryView
    type: artifact_viewer
    title: "גלריית סרטונים"
    requires: [videos_uploaded]
    data_sources:
      - artifacts.videos
      - artifacts.video_analysis_results
    phase: both
    icon: film

  # Artifact creators - generate new content
  video_upload:
    component: VideoUploadView
    type: artifact_creator
    title: "העלאת סרטון"
    requires: [interview_complete]
    creates: behavioral_video
    guidance_artifact: video_guidelines
    phase: screening
    icon: video
    max_uploads: 3

  document_upload:
    component: DocumentUploadView
    type: artifact_creator
    title: "העלאת מסמכים"
    requires: []  # Can upload anytime
    creates: diagnostic_report
    accepted_formats: [pdf, jpg, png, doc, docx]
    max_size_mb: 10
    phase: both
    icon: file-up

  journal_entry:
    component: JournalView
    type: artifact_creator
    title: "יומן התפתחות"
    requires: []  # Can journal anytime
    creates: journal_entry
    categories: [behavior, speech, social, motor, emotional]
    phase: both
    icon: book-open

  # Guidance views - help user understand
  filming_instructions:
    component: FilmingInstructionView
    type: guidance
    title: "הנחיות צילום"
    requires: [interview_complete]
    data_sources:
      - artifacts.video_guidelines
    phase: screening
    icon: info

  # Consultation view - interactive conversation
  consultation:
    component: ConsultationView
    type: conversation
    title: "שאלות ותשובות"
    requires: []  # Always available
    mode: qa  # Question-answer mode vs interview mode
    phase: both
    icon: message-circle

  # Action views - perform specific actions
  expert_finder:
    component: ExpertProfileView
    type: action
    title: "מציאת מומחים"
    requires: []  # Can browse anytime
    enhanced_by: [reports_generated]  # Better matching with reports
    data_sources:
      - artifacts.reports
      - session.location
    phase: ongoing
    icon: users

  share_report:
    component: ShareView
    type: action
    title: "שיתוף דוח"
    requires: [reports_generated]
    data_sources:
      - artifacts.parent_report
      - artifacts.professional_report
    phase: ongoing
    icon: share-2
```

### How Deep Views Connect to the System

**1. Context Cards → Deep Views**
```yaml
# Card triggers view
context_cards.yaml:
  video_upload_ready:
    action:
      type: open_deep_view
      view: video_upload  # ← References deep_views.yaml

deep_views.yaml:
  video_upload:
    component: VideoUploadView  # ← React component to show
    requires: [interview_complete]
```

**2. Actions → Deep Views**
```yaml
# Action opens view
action_graph.yaml:
  view_report:
    requires: [reports_generated]
    opens_view: report  # ← Opens ReportView

deep_views.yaml:
  report:
    component: ReportView
    data_sources: [artifacts.parent_report]
```

**3. Artifacts → Deep Views**
```yaml
# Artifact availability enables view
artifacts.yaml:
  parent_report:
    generated_when: video_analysis_complete
    viewers: [report]  # ← Can be viewed in ReportView

deep_views.yaml:
  report:
    requires: [reports_generated]
    data_sources: [artifacts.parent_report]
```

**4. Phases → Deep Views**
```yaml
# Phase determines available views
phases.yaml:
  screening:
    available_views:
      - video_upload
      - filming_instructions
      - document_upload

  ongoing:
    available_views:
      - journal_entry
      - consultation
      - expert_finder
      - share_report
```

### View Manager Service

```python
# view_manager.py
class ViewManager:
    """Routes to appropriate deep view based on configuration"""

    def __init__(self, config: ViewConfig):
        self.config = config

    def can_open_view(self, view_id: str, session: Session) -> bool:
        """Check if view can be opened given current state"""
        view_def = self.config.views[view_id]

        # Check phase
        if view_def.phase not in ['both', session.phase]:
            return False

        # Check prerequisites
        for prereq in view_def.requires:
            if not self._check_prerequisite(prereq, session):
                return False

        return True

    def get_view_data(self, view_id: str, session: Session) -> Dict:
        """Gather data needed for view"""
        view_def = self.config.views[view_id]

        data = {
            "title": view_def.title,
            "icon": view_def.icon,
            "component": view_def.component
        }

        # Gather data from sources
        for source in view_def.data_sources:
            data[source] = self._resolve_data_source(source, session)

        # Add guidance artifact if specified
        if view_def.guidance_artifact:
            data["guidance"] = session.artifacts.get(view_def.guidance_artifact)

        return data

    def handle_view_result(self, view_id: str, result: Dict, session: Session):
        """Process result from view interaction"""
        view_def = self.config.views[view_id]

        # If view creates artifact, store it
        if view_def.type == "artifact_creator" and result.get("artifact"):
            artifact_type = view_def.creates
            artifact = Artifact(
                type=artifact_type,
                content=result["artifact"],
                session_id=session.id,
                created_in_view=view_id
            )
            session.artifacts.add(artifact)

        # If view is conversation, extract data
        if view_def.type == "conversation" and result.get("messages"):
            # Continue extraction from consultation messages
            self._extract_from_consultation(result["messages"], session)
```

### View Lifecycle Example

```
User clicks card → Backend checks prerequisites
                 ↓
              ✅ Allowed
                 ↓
         Generate view data
         (gather from artifacts, session, etc.)
                 ↓
         Return to frontend:
         {
           "view": "video_upload",
           "component": "VideoUploadView",
           "title": "העלאת סרטון",
           "guidance": <video_guidelines_content>,
           "remaining_uploads": 2
         }
                 ↓
         Frontend shows DeepViewManager
         → Renders VideoUploadView
                 ↓
         User uploads video
                 ↓
         Frontend sends result to backend
                 ↓
         Backend processes:
         - Creates video artifact
         - Checks if analysis should start
         - Updates session state
         - Regenerates context cards
                 ↓
         New cards appear:
         [Processing] ניתוח בתהליך...
```

### Benefits of View Configuration

**1. Add New View Type**
```yaml
# Want to add "Schedule Follow-up" view?
schedule_followup:
  component: ScheduleFollowupView
  type: action
  title: "קביעת פגישת מעקב"
  requires: [reports_generated]
  phase: ongoing
  data_sources:
    - session.calendar_availability
    - artifacts.reports
```
→ **Add to YAML + create React component**

**2. Change View Prerequisites**
```yaml
# Want to allow video upload at 70% completeness?
video_upload:
  requires: [interview_complete]  # Already checks completeness >= 80%

# In prerequisites.py config:
interview_complete:
  threshold: 0.70  # Changed from 0.80
```

**3. Phase-Specific Views**
```yaml
# Screening phase views
video_upload: { phase: screening }
filming_instructions: { phase: screening }

# Ongoing phase views
journal_entry: { phase: ongoing }
expert_finder: { phase: ongoing }

# Both phases
consultation: { phase: both }
document_upload: { phase: both }
```

**4. View-to-Artifact Linkage**
```yaml
# Clear relationship between views and artifacts
video_upload:
  creates: behavioral_video
  guidance_artifact: video_guidelines

report:
  requires: [reports_generated]
  data_sources: [artifacts.parent_report]

journal_entry:
  creates: journal_entry
  data_sources: [session.previous_entries]
```

### The Flow (All Together)

```
State Changes → Cards Updated → User Clicks Card
     ↓                                  ↓
Extraction    →    Action Triggered  → Open Deep View
     ↓                                  ↓
Completeness  →    Prerequisites      → View Interaction
     ↓             Checked                ↓
Phase         →    View Available?    → Artifact Created/Viewed
Transition         ↓                      ↓
     ↓             ✅                     State Updated
     └──────────────────────────────────────┘
              Cycle continues...
```

**Everything is connected:**
- **Extraction** → Completeness → Phase transitions
- **Completeness** → Prerequisites → Actions available
- **Actions** → Cards → Deep views
- **Deep views** → Artifacts → More cards
- **Artifacts** → New capabilities → New views

All configured in YAML. All flowing naturally. 🌊

---

## Migration: The Natural Way

### Week 1: Configuration Files
- Create YAML files for current behavior
- No code changes yet
- Just documenting what exists

### Week 2: Configuration Loader
- Create config loader service
- Load YAML into Python objects
- Services still use old hardcoded way

### Week 3: Migrate Interview Service
- Update to read from config
- Test that behavior is identical
- Gradual migration

### Week 4: Migrate Prerequisite Service
- Update to read action graph from config
- Test that all actions work the same
- Gradual migration

### Week 5: Add Phase System
- Implement phase manager
- Add phase transitions
- Enable screening → ongoing flow

### Week 6: Add Artifact System
- Implement artifact manager
- Explicit artifact generation
- Template-based creation

**Total**: 6 weeks for complete migration, zero breaking changes

---

## Why This is Wu Wei (Effortless Action)

1. **Follows the Natural Flow**
   - Not forcing new patterns
   - Making explicit what's implicit
   - Water finding its path

2. **Minimal Resistance**
   - Services barely change
   - Logic stays the same
   - Just reading from config

3. **Emergent Properties**
   - Easy to extend (add fields, actions, artifacts)
   - Easy to understand (YAML is clear)
   - Easy to test (config-driven)
   - Easy to evolve (just edit config)

4. **Not Over-Engineered**
   - No complex frameworks
   - No multi-domain support (not needed!)
   - No plugins, no microservices
   - Just: code + config

---

## What This Enables (Future)

Once configuration-driven:

1. **A/B Testing**
   ```yaml
   # Test different completeness thresholds
   experiment_a:
     interview_completeness_threshold: 0.80
   experiment_b:
     interview_completeness_threshold: 0.70
   ```

2. **Localization**
   ```yaml
   # Hebrew version
   fields:
     child_name:
       description: "שם הילד/ה"

   # English version
   fields:
     child_name:
       description: "Child's name"
   ```

3. **Different Workflows**
   ```yaml
   # Standard workflow
   screening → ongoing

   # Urgent workflow
   quick_screening → immediate_consultation → follow_up
   ```

4. **Easy Customization**
   - Different clinics might want different fields
   - Different completeness thresholds
   - Different artifact templates
   - All via config, no code changes

---

## The One-Page Summary

**Problem**: Schema, actions, phases hardcoded in Python → hard to change, hard to understand

**Solution**: Move to YAML configuration → easy to change, easy to understand

**Pattern**: Services read from config instead of hardcoded constants

**Benefit**: Add fields/actions/phases without touching code

**Philosophy**: Wu Wei - follow natural flow, minimal resistance, emergent simplicity

**Result**: Same great architecture, but flexible and maintainable

---

**Next Step**: Do you want me to create the actual YAML schemas and show how the services would adapt to use them? Or do you see a simpler path?

The way of water is to find the lowest point... 🌊
