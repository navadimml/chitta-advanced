# Cognitive Dashboard Plan

**Version**: 1.0
**Date**: December 2024
**Status**: Design Complete, Ready for Implementation

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Problem](#2-the-problem)
3. [Core Insight: The Cognitive Debugger](#3-core-insight-the-cognitive-debugger)
4. [User Personas & The Bridge](#4-user-personas--the-bridge)
5. [Information Architecture](#5-information-architecture)
6. [UI Components](#6-ui-components)
7. [Hypothesis Lifecycle](#7-hypothesis-lifecycle)
8. [Evidence System](#8-evidence-system)
9. [Video Workflow](#9-video-workflow)
10. [Expert Correction System](#10-expert-correction-system)
11. [Analytics & Feedback Loop](#11-analytics--feedback-loop)
12. [Data Structures](#12-data-structures)
13. [API Endpoints](#13-api-endpoints)
14. [Implementation Phases](#14-implementation-phases)
15. [Open Questions](#15-open-questions)

---

## 1. Executive Summary

### What We're Building

An **internal explainability dashboard** that transforms expert review from passive observation into active AI improvement. The dashboard serves as a **cognitive debugger** - revealing not just what the AI concluded, but how it perceived, reasoned, and decided.

### Key Innovation

**The Turn Card**: Instead of showing flat events (observations, curiosities), we show complete cognitive cycles. Each conversation turn reveals:
- What the parent said
- What the AI perceived (tool calls)
- What changed in understanding
- How the AI responded
- Why it made each decision

### The Flywheel

```
Expert Reviews Turn → Flags Incorrect Decision → Provides Correction
        ↓
Correction Stored with Clinical Reasoning
        ↓
Patterns Detected Across Corrections
        ↓
Training Data Generated → AI Improves
        ↓
Better Decisions → Fewer Corrections Needed
```

---

## 2. The Problem

### Current State

We have a working AI (Chitta/Darshan) that:
- Converses with parents about their children
- Extracts observations via tool calls
- Spawns and manages curiosities
- Builds hypotheses and gathers evidence
- Suggests and analyzes videos
- Synthesizes patterns into a "Crystal"

But we have **no visibility** into:
- Whether extractions are accurate
- Whether hypotheses are clinically sound
- Whether video suggestions are timely
- Whether analyses are correct
- What systematic errors exist

### Why Simple Logging Isn't Enough

Logs show events chronologically. But experts need to understand **causality and context**:
- "Why did the AI think this was behavioral, not sensory?"
- "What evidence led to this hypothesis?"
- "Was video suggested at the right moment?"

---

## 3. Core Insight: The Cognitive Debugger

### The Fundamental Unit is the TURN

Each conversation turn is a complete cognitive cycle:

```
┌─────────────────────────────────────────────────┐
│                    TURN                         │
├─────────────────────────────────────────────────┤
│ INPUT:    Parent message                        │
│ PERCEIVE: Phase 1 - Tool calls (notice, wonder) │
│ UPDATE:   State changes (observations, etc.)    │
│ RESPOND:  Phase 2 - Text generation             │
│ OUTPUT:   AI response to parent                 │
└─────────────────────────────────────────────────┘
```

### What We Must Capture

For each turn, store:

1. **Pre-state**: What did the AI know before this message?
2. **Perception**: All tool calls made (with parameters and results)
3. **State delta**: What changed in understanding
4. **Response context**: Active curiosities, turn guidance
5. **Output**: The generated response

This is the **cognitive trace** - the AI's "working memory" made visible.

### Why This Matters

With cognitive traces, experts can:
- See exactly what triggered each decision
- Flag specific tool calls as incorrect
- Provide the correct alternative
- Explain why (clinical reasoning)

This transforms reviews into **structured training data**.

---

## 4. User Personas & The Bridge

### Two User Types

| Aspect | Child Development Expert | Developer |
|--------|-------------------------|-----------|
| **Goal** | Verify clinical accuracy | Verify mechanism correctness |
| **Thinks in** | Clinical concepts, child behavior | Code, parameters, state |
| **Asks** | "Is this interpretation correct?" | "Did the pipeline work right?" |
| **Vocabulary** | "Sensory processing", "self-regulation" | `domain="sensory"`, `effect="supports"` |

### The Bridge: Shared Vocabulary

Domain terms connect both worlds:

| Clinical Term | Code Representation |
|---------------|---------------------|
| חושי (sensory) | `domain="sensory"` |
| רגשי (emotional) | `domain="emotional"` |
| תומך (supports) | `effect="supports"` |
| סותר (contradicts) | `effect="contradicts"` |

When expert selects "חושי" from a dropdown, the system knows to set `domain="sensory"`.

### Design Principle: Semantic Translation + Progressive Disclosure

1. **Primary View**: Natural language (Hebrew) - everyone understands
2. **Corrections**: Via dropdowns using shared vocabulary
3. **Technical Details**: Expandable, hidden by default for clinicians
4. **Role-Based Defaults**: Different starting views per user type

---

## 5. Information Architecture

### Main Navigation

```
Dashboard
├── Timeline (default)      # Chronological cognitive trace
├── Hypotheses              # All hypotheses with lifecycle
├── Videos                  # Video gallery and analysis
├── Crystal                 # Current synthesis
├── Analytics               # Patterns from expert corrections
└── Settings                # View preferences
```

### Timeline View Hierarchy

```
Timeline
├── Turn Card (collapsed)
│   ├── Timestamp + Turn number
│   ├── Parent message (truncated)
│   ├── Quick summary (icons: +observations, +curiosities)
│   └── [Expand] button
│
└── Turn Card (expanded)
    ├── Parent message (full)
    ├── Perception Section
    │   ├── Observation cards (with correction buttons)
    │   ├── Curiosity cards (with correction buttons)
    │   └── [+ Add missed signal]
    ├── State Delta Section
    │   └── What changed (observations, curiosities, certainty)
    ├── Response Section
    │   ├── Active curiosities
    │   ├── Turn guidance
    │   └── AI response (with quality buttons)
    └── Technical Details (collapsed)
        ├── Raw tool calls
        ├── State diff
        └── Phase 2 context
```

### Special Timeline Elements

Certain events get enhanced treatment:

| Event Type | Visual | Expandable Content |
|------------|--------|-------------------|
| Hypothesis created | ◆ Diamond icon | Full lifecycle, evidence trail, video |
| Video uploaded | 🎬 Camera icon | Player, analysis, observations |
| Video analyzed | 🔍 Magnifier icon | Timeline observations, impact |
| Crystal created | 🔮 Crystal icon | Full synthesis text |
| Evidence added | (nested under hypothesis) | Effect, certainty change |

---

## 6. UI Components

### 6.1 Turn Card (Core Component)

**Collapsed State**:
```
┌─────────────────────────────────────────────────────────────────────┐
│ ● תור #3 · 15:52                                                    │
│   "דניאל לא אוהב להתלבש בבוקר, תמיד מתנגד"                          │
│   📌 +1 תצפית (התנהגותי)  ❓ +1 סקרנות                  [הרחב ▼]    │
└─────────────────────────────────────────────────────────────────────┘
```

**Expanded State**:
```
┌─────────────────────────────────────────────────────────────────────┐
│ ● תור #3 · 15:52                                        [צמצם ▲]   │
│                                                                     │
│ 💬 ההורה:                                                           │
│    "דניאל לא אוהב להתלבש בבוקר, תמיד מתנגד"                         │
│                                                                     │
│ ─────────────────────────────────────────────────────────────────── │
│                                                                     │
│ 🧠 מה הבינה צ'יטה:                                                  │
│                                                                     │
│ ┌─ תצפית ─────────────────────────────────────────────────────────┐ │
│ │ "מתנגד להתלבשות בבוקר"                                          │ │
│ │ תחום: התנהגותי                                   [שנה תחום ▼]   │ │
│ │                                                     [✓] [✗]     │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ ┌─ סקרנות חדשה ───────────────────────────────────────────────────┐ │
│ │ "מה גורם להתנגדות להתלבשות?"                                    │ │
│ │ סוג: שאלה | תחום: התנהגותי                                      │ │
│ │                                                     [✓] [✗]     │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ [+ הוסף משהו שפוספס]                                                │
│                                                                     │
│ ─────────────────────────────────────────────────────────────────── │
│                                                                     │
│ 💭 תשובת צ'יטה:                                                     │
│    "זה נשמע מאתגר. ספרי לי עוד - מה קורה כשמנסים להלביש אותו?"    │
│                                        [✓ תשובה מתאימה] [✗ בעיה]   │
│                                                                     │
│ ─────────────────────────────────────────────────────────────────── │
│                                                                     │
│                                         [🔧 פרטים טכניים ▶]         │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.2 Hypothesis Card

**In Timeline (Collapsed)**:
```
┌─────────────────────────────────────────────────────────────────────┐
│ ◆ 💡 השערה · תור #5 · 15:52                                         │
│                                                                     │
│ "מוזיקה קלאסית עוזרת לדניאל להירגע"                                 │
│                                                                     │
│ ודאות: ░░░░████████████████████░░░░  0.2 → 0.8  ✓ מאושר            │
│                                                                     │
│ 📊 ראיות: 3    🎬 וידאו: נותח                                       │
│                                                                     │
│        [ראיות ▼]  [וידאו ▼]  [מחזור חיים ▼]           [✓] [✗]      │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.3 Evidence Card

```
┌─────────────────────────────────────────────────────────────────────┐
│ ראיה #2 · תור #8 · שיחה                                             │
│                                                                     │
│ ההורה: "רק מוזיקה קלאסית עוזרת, פופ דווקא מעצבן אותו"               │
│                                                                     │
│ סיווג: ⚡ משנה את ההשערה                                            │
│ השערה עודכנה: "מוזיקה" → "מוזיקה קלאסית"                            │
│ השפעה על ודאות: +0.10                                               │
│                                                                     │
│                              [הסיווג נכון? ▼]  [השפעה מתאימה? ▼]    │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.4 Video Workflow Section

```
┌─────────────────────────────────────────────────────────────────────┐
│ ─────────────── וידאו ───────────────                               │
│                                                                     │
│ 1️⃣ הצעה · תור #9                                                    │
│    צ'יטה: "אולי תרצי לצלם רגע כזה?"                                 │
│    סיבה: ודאות 0.45, צריך אישור ויזואלי                             │
│    תגובה: הסכימה ✓                                  [נכון? ▼]      │
│                                                                     │
│ 2️⃣ הנחיות · 15:55                                                   │
│    להורה: "צלמי 3-5 דקות לפני ואחרי מוזיקה"                         │
│    פנימי: שינוי שפת גוף, זמן תגובה, משך השפעה      [הצג ▼]         │
│                                                    [מתאים? ▼]      │
│                                                                     │
│ 3️⃣ הועלה · 16:05                                                    │
│    📹 4:23 דקות                                    [צפה בוידאו]    │
│                                                                     │
│ 4️⃣ נותח · 16:08                                                     │
│    תצפיות: 3 חדשות                                                  │
│    השפעה: ודאות 0.6 → 0.8                          [פרטי ניתוח ▼]   │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.5 Video Analysis View

```
┌─────────────────────────────────────────────────────────────────────┐
│ 🎬 ניתוח וידאו                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │                      [Video Player]                             │ │
│ │                        2:15 / 4:23                              │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ ציר זמן:                                                            │
│ ├────────●──────────●───●─────────────────────────────────────────┤ │
│ 0:00    1:32       1:45 2:00                                  4:23 │
│         מוזיקה     תגובה רגיעה                                      │
│                                                                     │
│ ────────────── תצפיות ──────────────                                │
│                                                                     │
│ 📍 0:00-1:30 · לפני                                                 │
│    "דניאל עצבני, זז הרבה"                          [▶] [✓] [✗]     │
│                                                                     │
│ 📍 1:45 · תגובה ראשונית                                             │
│    "עוצר, מרים ראש, מחפש מקור צליל"                [▶] [✓] [✗]     │
│                                                                     │
│ 📍 2:00 · רגיעה                                                     │
│    "יושב, נשימה עמוקה"                             [▶] [✓] [✗]     │
│                                                                     │
│ [+ הוסף תצפית שפוספסה]                                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.6 Correction Dialog

```
┌─────────────────────────────────────────────────────────────────────┐
│ תיקון תצפית                                                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ צ'יטה הבינה: "מתנגד להתלבשות" → תחום התנהגותי                       │
│                                                                     │
│ מה לא נכון?                                                         │
│   ○ התחום שגוי                                                      │
│   ○ ההבנה לא מדויקת                                                 │
│   ○ פספסה משהו חשוב                                                 │
│   ○ המציאה משהו שלא נאמר                                            │
│                                                                     │
│ התחום הנכון:  [חושי           ▼]                                    │
│                                                                     │
│ הסבר קליני:                                                         │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ התנגדות להתלבשות בגיל 3 היא לעתים סימן לרגישות טקטילית.        │ │
│ │ הילד לא "מתנהג רע" - הוא חווה אי-נוחות חושית מהבגדים.          │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│                                        [ביטול]  [שמור תיקון]        │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.7 Add Missed Signal Dialog

```
┌─────────────────────────────────────────────────────────────────────┐
│ הוסף משהו שפוספס                                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ בתור #3, ההורה אמרה:                                                │
│ "דניאל לא אוהב להתלבש בבוקר, תמיד מתנגד"                            │
│                                                                     │
│ סוג:  ○ תצפית שפוספסה                                               │
│       ○ סקרנות שהיתה צריכה להיווצר                                  │
│       ○ השערה שהיתה צריכה להיווצר                                   │
│                                                                     │
│ תוכן:                                                               │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ "דניאל מחפש עקביות חושית - אותה תחושה מוכרת"                    │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ תחום:  [חושי           ▼]                                           │
│                                                                     │
│ הסבר למה זה חשוב:                                                   │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ התנגדות עקבית לפעולות הלבשה מרמזת על רגישות טקטילית.           │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│                                           [ביטול]  [הוסף]           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 7. Hypothesis Lifecycle

### States

```
wondering → investigating → [confirmed | refuted | transformed | dormant]
```

| State | Meaning | Visual |
|-------|---------|--------|
| wondering | Just spawned, no investigation | ○ Empty circle |
| investigating | Active evidence collection | ◐ Half-filled |
| confirmed | Evidence supports theory (certainty > 0.7) | ● Filled green |
| refuted | Evidence contradicts theory | ✗ Red X |
| transformed | Theory changed based on evidence | ↻ Refresh icon |
| dormant | No recent activity | ○ Gray |

### Lifecycle Visualization

```
  ודאות
   1.0 ┤
   0.8 ┤                                    ●━━━━● confirmed
   0.6 ┤                          ●━━━━━━━━●
   0.4 ┤              ●━━━━━━━━━●
   0.2 ┤   ●━━━━━━━━●
   0.0 ┼───┴────┴────┴────┴────┴────┴────┴───
       created  +evidence  +evidence  video  video
                          (transforms) suggested analyzed
```

### What Experts Review

For each hypothesis:

1. **Creation**: Was the trigger appropriate? Is the theory reasonable?
2. **Evidence classification**: Is each piece correctly labeled (supports/contradicts/transforms)?
3. **Certainty changes**: Are the deltas proportional to evidence strength?
4. **Video suggestion**: Was timing appropriate? Were guidelines clear?
5. **Video analysis**: Were observations accurate? Was impact correct?
6. **Final status**: Does the conclusion match the evidence?

---

## 8. Evidence System

### Evidence Types

| Effect | Meaning | Impact on Certainty |
|--------|---------|---------------------|
| supports | Confirms the theory | +0.1 to +0.2 |
| contradicts | Challenges the theory | -0.1 to -0.2 |
| transforms | Changes the theory itself | Variable, theory text updates |

### Evidence Sources

| Source | Description | Typical Weight |
|--------|-------------|----------------|
| conversation | From parent's words | Standard |
| video | From video analysis | Higher (visual confirmation) |
| expert | Added by dashboard reviewer | Highest |

### Expert Corrections on Evidence

Experts can:
1. **Change classification**: "This doesn't support, it contradicts"
2. **Adjust impact**: "This should have bigger/smaller effect"
3. **Add missed evidence**: "This quote was evidence but wasn't captured"
4. **Flag hallucination**: "This evidence isn't in the conversation"

---

## 9. Video Workflow

### Complete Lifecycle

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Hypothesis │───▶│  Suggestion │───▶│  Guidelines │───▶│   Upload    │───▶│  Analysis   │
│   Created   │    │   Offered   │    │  Generated  │    │  Received   │    │  Complete   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                         │                                                         │
                         │ declined                                                │
                         ▼                                                         ▼
                   [No Video]                                              [Evidence Added]
```

### Video Scenario Structure

```
VideoScenario {
  // Parent-facing (warm, concrete)
  title: "משחק עם מוזיקה"
  what_to_film: "צלמי 3-5 דקות לפני ואחרי..."
  rationale_for_parent: "זה יעזור לי להבין..."
  duration_suggestion: "5-7 דקות"

  // Internal (for analysis)
  target_hypothesis_id: "inv_xxx"
  what_we_hope_to_learn: "Visual confirmation of..."
  focus_points: ["body language change", "response time", ...]

  // Status tracking
  status: pending | uploaded | analyzed
  created_at, uploaded_at, analyzed_at
}
```

### Expert Review Points

| Stage | What to Review | Correction Options |
|-------|----------------|-------------------|
| Suggestion | Was timing right? | "Too early", "Too late", "Not needed" |
| Guidelines | Are instructions clear? Appropriate? | Edit text, flag issues |
| Upload | Does video match guidelines? | Flag mismatch |
| Analysis | Are observations accurate? | ✓/✗ each observation, add missed |
| Impact | Is certainty change proportional? | Adjust impact rating |

---

## 10. Expert Correction System

### Correction Types

| Type | Description | Data Captured |
|------|-------------|---------------|
| domain_change | Wrong developmental domain | original, corrected, reasoning |
| extraction_error | Observation text is wrong | original, corrected, reasoning |
| missed_signal | Should have noticed something | what was missed, why important |
| hallucination | AI invented something not said | what was invented, correct interpretation |
| evidence_reclassify | Wrong supports/contradicts label | original, corrected, reasoning |
| timing_issue | Video suggested too early/late | timing feedback |
| certainty_adjustment | Certainty delta too high/low | suggested adjustment |

### Correction Data Structure

```python
ExpertCorrection {
  id: str
  turn_id: str                    # Which turn
  target_type: str                # observation, curiosity, hypothesis, evidence, video
  target_id: str                  # Which specific element

  correction_type: str            # From types above
  original_value: Dict            # What AI did
  corrected_value: Dict           # What it should have been

  expert_reasoning: str           # Clinical explanation (GOLD for training)
  expert_id: str
  created_at: datetime

  # Training pipeline
  used_in_training: bool = False
  training_batch_id: Optional[str]
}
```

### The Value of Reasoning

The `expert_reasoning` field is crucial. It explains **why** the correction is correct in clinical terms. This becomes training data:

```
Correction: domain "behavioral" → "sensory"
Reasoning: "התנגדות להתלבשות בגיל 3 היא לעתים קרובות סימן לרגישות
           טקטילית. הילד לא מתנהג רע - הוא חווה אי-נוחות חושית."
```

This teaches the AI the clinical distinction, not just "use sensory instead of behavioral."

---

## 11. Analytics & Feedback Loop

### Pattern Detection

Aggregate corrections to find systematic errors:

```
┌─────────────────────────────────────────────────────────────────────┐
│ דפוסי שגיאות (127 ביקורות)                                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ⚠️ סיווג תחום שגוי                                     23 מקרים    │
│    חושי → התנהגותי: 15                                              │
│    רגשי → התנהגותי: 8                                               │
│    [צפה בדוגמאות]  [צור תיקון לפרומפט]                              │
│                                                                     │
│ ⚠️ סימנים שפוספסו                                      18 מקרים    │
│    ויסות עצמי דרך יצירה: 10                                         │
│    צורך בשגרה כחושי: 8                                              │
│    [צפה בדוגמאות]  [צור דוגמאות אימון]                              │
│                                                                     │
│ ⚠️ ודאות גבוהה מדי                                     12 מקרים    │
│    ראיה בודדת → ודאות 0.7+                                          │
│    [צפה בדוגמאות]  [התאם נוסחה]                                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Improvement Tracking

```
┌─────────────────────────────────────────────────────────────────────┐
│ 📈 מדדי שיפור (30 יום אחרונים)                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ דיוק סיווג תחום:     72% → 84%  ↑                                   │
│ סימנים שפוספסו:      34% → 19%  ↓                                   │
│ דיוק ניתוח וידאו:    68% → 79%  ↑                                   │
│ תזמון הצעת וידאו:    מוקדם ב-2 תורות בממוצע → מדויק                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Training Data Pipeline

1. Expert makes correction with reasoning
2. System validates correction (not empty, has reasoning)
3. Correction stored in `expert_corrections` table
4. Nightly job aggregates corrections by type
5. Patterns with >5 instances flagged for prompt improvement
6. Generate training examples from corrections
7. Test improved prompts against historical cases
8. Deploy if metrics improve

---

## 12. Data Structures

### New Models Required

#### CognitiveTurn

```python
@dataclass
class CognitiveTurn:
    """Complete cognitive trace for one conversation turn."""
    turn_id: str
    turn_number: int
    child_id: str
    timestamp: datetime

    # Input
    parent_message: str
    parent_role: str  # mother, father, clinician

    # Pre-state
    pre_understanding_hash: str  # For detecting changes
    active_curiosities_snapshot: List[Dict]

    # Phase 1: Perception
    tool_calls: List[ToolCallRecord]

    # State changes
    observations_added: List[str]  # IDs
    curiosities_spawned: List[str]  # IDs
    curiosities_updated: List[Dict]  # {id, field, old, new}
    evidence_added: List[Dict]  # {curiosity_id, evidence}

    # Phase 2: Response
    turn_guidance: str
    active_curiosities_for_response: List[str]
    response_text: str

    # Expert annotations (populated later)
    corrections: List[ExpertCorrection] = field(default_factory=list)
    notes: List[ClinicalNote] = field(default_factory=list)
```

#### ToolCallRecord

```python
@dataclass
class ToolCallRecord:
    """Record of a single tool call."""
    tool_name: str  # notice, wonder, add_evidence, etc.
    arguments: Dict[str, Any]
    result: Optional[Dict[str, Any]]

    # For UI mapping
    created_element_id: Optional[str]  # ID of observation/curiosity created
    created_element_type: Optional[str]  # observation, curiosity, evidence
```

#### ExpertCorrection

```python
@dataclass
class ExpertCorrection:
    """Expert correction to AI decision."""
    id: str
    turn_id: str
    target_type: str  # observation, curiosity, hypothesis, evidence, video
    target_id: str

    correction_type: str  # domain_change, missed_signal, etc.
    original_value: Dict[str, Any]
    corrected_value: Dict[str, Any]

    expert_reasoning: str
    expert_id: str
    created_at: datetime

    # Training
    severity: str = "medium"  # low, medium, high
    used_in_training: bool = False
    training_batch_id: Optional[str] = None
```

#### MissedSignal

```python
@dataclass
class MissedSignal:
    """Signal that expert says should have been caught."""
    id: str
    turn_id: str

    signal_type: str  # observation, curiosity, hypothesis
    content: str
    domain: str

    why_important: str
    expert_id: str
    created_at: datetime
```

### Database Tables

```sql
-- Cognitive traces
CREATE TABLE cognitive_turns (
    id UUID PRIMARY KEY,
    child_id UUID REFERENCES children(id),
    turn_number INTEGER,
    timestamp TIMESTAMPTZ,
    parent_message TEXT,
    parent_role VARCHAR(50),
    tool_calls JSONB,
    state_delta JSONB,
    turn_guidance TEXT,
    response_text TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Expert corrections
CREATE TABLE expert_corrections (
    id UUID PRIMARY KEY,
    turn_id UUID REFERENCES cognitive_turns(id),
    target_type VARCHAR(50),
    target_id VARCHAR(100),
    correction_type VARCHAR(50),
    original_value JSONB,
    corrected_value JSONB,
    expert_reasoning TEXT,
    expert_id UUID REFERENCES users(id),
    severity VARCHAR(20) DEFAULT 'medium',
    used_in_training BOOLEAN DEFAULT FALSE,
    training_batch_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Missed signals
CREATE TABLE missed_signals (
    id UUID PRIMARY KEY,
    turn_id UUID REFERENCES cognitive_turns(id),
    signal_type VARCHAR(50),
    content TEXT,
    domain VARCHAR(50),
    why_important TEXT,
    expert_id UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Correction patterns (aggregated)
CREATE TABLE correction_patterns (
    id UUID PRIMARY KEY,
    pattern_type VARCHAR(50),
    description TEXT,
    occurrence_count INTEGER,
    example_correction_ids UUID[],
    suggested_fix TEXT,
    status VARCHAR(20) DEFAULT 'identified',  -- identified, fixing, resolved
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 13. API Endpoints

### Timeline & Turns

```
GET  /api/dashboard/children/{child_id}/timeline
     ?from_turn=N&limit=50
     Returns: List of CognitiveTurn with nested data

GET  /api/dashboard/children/{child_id}/turns/{turn_id}
     Returns: Full CognitiveTurn with all expansions

GET  /api/dashboard/children/{child_id}/turns/{turn_id}/technical
     Returns: Raw tool calls, state diffs (developer view)
```

### Hypotheses

```
GET  /api/dashboard/children/{child_id}/hypotheses
     Returns: All hypotheses with lifecycle state

GET  /api/dashboard/children/{child_id}/hypotheses/{hypothesis_id}
     Returns: Full hypothesis with evidence trail, video workflow

GET  /api/dashboard/children/{child_id}/hypotheses/{hypothesis_id}/lifecycle
     Returns: Timeline of hypothesis evolution
```

### Videos

```
GET  /api/dashboard/children/{child_id}/videos
     Returns: All video scenarios with status

GET  /api/dashboard/children/{child_id}/videos/{video_id}
     Returns: Full video details with analysis

GET  /api/dashboard/children/{child_id}/videos/{video_id}/stream
     Returns: Video file stream for playback
```

### Corrections

```
POST /api/dashboard/corrections
     Body: ExpertCorrection
     Creates correction, links to turn/element

POST /api/dashboard/missed-signals
     Body: MissedSignal
     Creates missed signal record

GET  /api/dashboard/corrections?child_id=X&type=Y
     Returns: Filtered corrections

PATCH /api/dashboard/corrections/{id}
      Updates correction (e.g., mark used in training)
```

### Analytics

```
GET  /api/dashboard/analytics/patterns
     Returns: Aggregated correction patterns

GET  /api/dashboard/analytics/improvement
     ?days=30
     Returns: Improvement metrics over time

GET  /api/dashboard/analytics/patterns/{pattern_id}/examples
     Returns: Example corrections for a pattern
```

---

## 14. Implementation Phases

### Phase 1: Foundation (Backend)

**Goal**: Capture and store cognitive traces

**Tasks**:
1. Add `CognitiveTurn` model to `app/chitta/models.py`
2. Modify `gestalt.py` to capture tool calls during Phase 1
3. Create `cognitive_turns` table and migration
4. Store turns during `process_message()`
5. Create basic timeline API endpoint

**Files**:
- `app/chitta/models.py` - Add CognitiveTurn
- `app/chitta/gestalt.py` - Capture during processing
- `app/db/models_dashboard.py` - SQLAlchemy models
- `alembic/versions/xxx_cognitive_turns.py` - Migration
- `app/api/routes/dashboard.py` - Timeline endpoint

**Validation**: Can retrieve timeline with tool calls for a child

---

### Phase 2: Turn Cards (Frontend)

**Goal**: Display cognitive traces in reviewable format

**Tasks**:
1. Create TurnCard component (collapsed/expanded)
2. Create ObservationCard with domain selector
3. Create CuriosityCard
4. Create ResponseReview component
5. Implement timeline view with infinite scroll
6. Add technical details expansion

**Files**:
- `src/components/dashboard/Timeline.jsx`
- `src/components/dashboard/TurnCard.jsx`
- `src/components/dashboard/ObservationCard.jsx`
- `src/components/dashboard/CuriosityCard.jsx`
- `src/components/dashboard/TechnicalDetails.jsx`

**Validation**: Can browse timeline, expand turns, see perceptions and responses

---

### Phase 3: Corrections (Backend + Frontend)

**Goal**: Enable expert corrections with reasoning

**Tasks**:
1. Create correction models and tables
2. Create correction API endpoints
3. Create CorrectionDialog component
4. Create MissedSignalDialog component
5. Integrate correction buttons into cards
6. Store corrections with turn linkage

**Files**:
- `app/db/models_dashboard.py` - Correction models
- `alembic/versions/xxx_corrections.py` - Migration
- `app/api/routes/dashboard.py` - Correction endpoints
- `src/components/dashboard/CorrectionDialog.jsx`
- `src/components/dashboard/MissedSignalDialog.jsx`

**Validation**: Can flag observations, change domains, add reasoning, see saved corrections

---

### Phase 4: Hypotheses (Backend + Frontend)

**Goal**: Display hypothesis lifecycle with evidence

**Tasks**:
1. Enhance hypothesis data in timeline
2. Create HypothesisCard component
3. Create EvidenceTrail component
4. Create LifecycleGraph component
5. Add hypothesis-specific corrections
6. Link hypotheses to source turns

**Files**:
- `src/components/dashboard/HypothesisCard.jsx`
- `src/components/dashboard/EvidenceTrail.jsx`
- `src/components/dashboard/EvidenceCard.jsx`
- `src/components/dashboard/LifecycleGraph.jsx`

**Validation**: Can see hypothesis evolution, review evidence, correct classifications

---

### Phase 5: Video Workflow (Backend + Frontend)

**Goal**: Full video workflow visibility and review

**Tasks**:
1. Create video gallery view
2. Create VideoWorkflow component (suggestion → guidelines → upload → analysis)
3. Create VideoAnalysisView with timeline
4. Integrate video player with observation timestamps
5. Enable observation-level corrections on video analysis
6. Add missed observation input

**Files**:
- `src/components/dashboard/VideoGallery.jsx`
- `src/components/dashboard/VideoWorkflow.jsx`
- `src/components/dashboard/VideoAnalysisView.jsx`
- `src/components/dashboard/VideoPlayer.jsx`

**Validation**: Can watch video, see timestamped observations, correct analysis

---

### Phase 6: Analytics (Backend + Frontend)

**Goal**: Aggregate patterns and track improvement

**Tasks**:
1. Create pattern aggregation job
2. Create correction_patterns table
3. Create analytics API endpoints
4. Create PatternList component
5. Create ImprovementMetrics component
6. Create pattern detail view with examples

**Files**:
- `app/jobs/aggregate_patterns.py`
- `app/api/routes/dashboard.py` - Analytics endpoints
- `src/components/dashboard/Analytics.jsx`
- `src/components/dashboard/PatternList.jsx`
- `src/components/dashboard/ImprovementMetrics.jsx`

**Validation**: Can see aggregated patterns, view examples, track improvement over time

---

### Phase 7: Training Pipeline (Backend)

**Goal**: Generate training data from corrections

**Tasks**:
1. Create training example generator
2. Create prompt improvement suggestions
3. Create A/B testing framework for prompts
4. Create training batch management
5. Mark corrections as used in training
6. Track prompt version effectiveness

**Files**:
- `app/jobs/generate_training.py`
- `app/services/prompt_improvement.py`
- `app/db/models_training.py`

**Validation**: Can generate training examples, test improved prompts, measure improvement

---

## 15. Open Questions

### Technical

1. **Cognitive trace storage**: Store in main DB or separate analytics DB?
2. **Video storage**: Local filesystem or cloud (S3)?
3. **Real-time updates**: WebSocket for live session viewing?
4. **Performance**: How to handle children with 100+ turns efficiently?

### UX

1. **Default view**: Timeline or summary cards?
2. **Correction workflow**: Inline or modal dialogs?
3. **Video scrubbing**: How to sync observations with video playback?
4. **RTL handling**: How to handle mixed Hebrew/English in technical views?

### Process

1. **Reviewer assignment**: How to assign children to reviewers?
2. **Review completion**: How to mark a child as "fully reviewed"?
3. **Disagreement resolution**: What if two experts disagree on a correction?
4. **Training cadence**: How often to aggregate and apply corrections?

---

## Appendix: Glossary

| Term | Hebrew | Meaning |
|------|--------|---------|
| Turn | תור | One parent message + AI perception + AI response |
| Cognitive Trace | מעקב קוגניטיבי | Full record of AI's "thinking" for a turn |
| Hypothesis | השערה | Theory being tested (curiosity type=hypothesis) |
| Evidence | ראיה | Data supporting/contradicting a hypothesis |
| Certainty | ודאות | Confidence level 0-1 |
| Domain | תחום | Developmental area (sensory, emotional, etc.) |
| Crystal | קריסטל | Synthesized understanding of child |
| Correction | תיקון | Expert fix to AI decision |
| Missed Signal | אות שפוספס | Something AI should have noticed |

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Dec 2024 | Initial design document |

---

**Next Step**: Begin Phase 1 implementation - cognitive trace capture.
