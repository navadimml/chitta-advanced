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
│  - extraction_schema.yaml                          │
│  - action_graph.yaml                               │
│  - phases.yaml                                     │
│  - artifacts.yaml                                  │
└────────────────────────────────────────────────────┘
                      ↓ loaded by
┌────────────────────────────────────────────────────┐
│           CONFIGURATION LAYER (Python)             │
│  - config_loader.py  ← Loads and validates YAML    │
│  - schema_registry.py ← Manages extraction schema  │
│  - action_registry.py ← Manages action graph       │
│  - phase_manager.py   ← Manages phase transitions  │
└────────────────────────────────────────────────────┘
                      ↓ used by
┌────────────────────────────────────────────────────┐
│           EXISTING SERVICES (Unchanged)            │
│  - conversation_service.py                         │
│  - interview_service.py                            │
│  - prerequisite_service.py                         │
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
