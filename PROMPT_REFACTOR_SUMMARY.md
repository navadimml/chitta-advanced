# Chitta Interview & Summary Prompts: Complete Refactor Summary

**Date**: November 3, 2025
**Branch**: `claude/update-interview-prompts-011CUkZgkN94PZ9gHjxVGucJ`

---

## 🎯 What We Accomplished

We completely refactored Chitta's interview and summary system to leverage AI intelligence rather than rigid rules, while integrating critical clinical insights.

---

## 📋 The Journey: From Problem to Solution

### Initial Problems Identified

1. **Field Coverage Gap**: Original extraction (7 fields) was too shallow for detailed summary needs (~200 fields)
2. **Navigation Too Loose**: Interview prompt lacked systematic depth requirements
3. **Missing Clinical Balance**: Strengths weren't emphasized as diagnostic data
4. **Video Introduction Premature**: Videos mentioned during interview before parent knew about them
5. **Fixed Video Count**: Summary prompt created 2-4 videos regardless of complexity

### Key Insights

1. **AI Reasoning vs Rigid Rules**: Trust AI's clinical intelligence to adapt, don't constrain with mechanical checklists
2. **Neurologist's Wisdom**: Strengths are essential diagnostic information, not optional "being nice"
3. **Progressive Extraction**: Capture structure during interview, enrich in summary (not extract from scratch)
4. **Intelligent Video Count**: Reason about how many videos needed (1-4) based on complexity, not fixed number

---

## 📁 Files Created/Modified

### 1. Analysis Documents (Understanding the Problems)

**FIELD_COVERAGE_ANALYSIS.md**
- Compared extraction (7 fields) vs summary needs (200 fields)
- Identified the gap between what interview captures vs what summary needs
- Recommended hybrid approach: structured outline + transcript enrichment

**INTERVIEW_NAVIGATION_ANALYSIS.md**
- Analyzed whether AI really drills deep into concerns
- Found: Good examples but lacking systematic framework
- Identified missing: depth requirements, coverage tracking, pivot triggers

**INTELLIGENT_INTERVIEW_NAVIGATION.md**
- Detailed walkthrough of how AI should think at each phase
- 40+ example turns showing AI's internal reasoning
- Demonstrated adaptive thinking vs script-following

---

### 2. Enhanced Interview Prompt (The Core Change)

**INTERVIEW_SYSTEM_PROMPT_ENHANCED.md** (708 lines)

**What's New:**

#### A. Clinical Reasoning Framework (7 Dimensions)
AI reasons about each turn using:
1. **Severity Assessment** - How significant is this concern?
2. **Pattern Recognition** - Are concerns clustering?
3. **Strength-Challenge Balance** - Essential diagnostic info
4. **Information Density** - Rich or sparse parent responses?
5. **Parent's Emotional State** - Stuck, flowing, overwhelmed?
6. **Clinical Significance** - Does this detail matter?
7. **Coverage Self-Check** - Do I have enough for video guidelines?

#### B. Strength Emphasis (Neurologist Insight)
- Explains WHY strengths matter clinically
- Pervasive issues → few strengths; Specific issues → clear strengths
- Strengths woven throughout (not separate section)
- Every extraction includes concerns + strengths balanced

#### C. One Question Per Turn - With Intelligence
- Default: One main question (conversational rhythm)
- Smart adaptations: clarifying options, contextual prompts, admin bundling
- Clear rules: When to adapt vs when to stay focused
- Test: "Would this feel like conversation or interrogation?"

#### D. Adaptive Navigation Phases
- Phase 1: Landscape (all concerns before drilling)
- Phase 2: Strengths (integrated throughout)
- Phase 3: Selective Deep Dive (AI prioritizes + adapts depth)
- Phase 4: Context (efficient gap filling)
- Phase 5: Wrap-Up (end on hope + strengths)

#### E. Progressive Extraction
Shows how extraction gets richer:
- Turn 5-10: Foundation (basic info, main concerns)
- Turn 15-20: Depth (detailed examples, impact, strengths)
- Turn 30+: Complete picture (all context, parent journey)

#### F. Video Introduction Guidance
- **Important**: Videos NOT mentioned during interview
- After interview completion, backend generates guidelines
- Introduction script explains WHY videos (things hard to describe in words)
- Sets expectations (short, focused, [number] determined intelligently)

**Key Fixes**:
- ✅ Removed premature video mentions from interview dialogue
- ✅ Added proper video introduction with context

---

### 3. Extraction Schema Design (The Bridge)

**ADAPTIVE_EXTRACTION_SCHEMA_DESIGN.md**

**20-Field Schema** (vs original 7):

```typescript
{
  // Basic (3)
  child_name, age, gender

  // Concerns & Strengths - BALANCED (4)
  primary_concerns, concern_details,
  strengths, strength_challenge_balance

  // Behavioral (3)
  specific_examples, frequency_intensity, impact_assessment

  // Developmental (4)
  developmental_history, sensory_indicators,
  previous_assessments, previous_interventions

  // Environmental (3)
  family_context, educational_context, support_network

  // Parent's Journey (3)
  parent_emotional_state, parent_strategies_tried,
  parent_hopes_and_needs
}
```

**Key Principles**:
1. **Narrative synthesis** (not rigid nested structures)
2. **Progressive enrichment** (gets richer over time)
3. **Strength-challenge balance** as first-class citizen
4. **Parent's journey** included as clinical data

**Intelligent Video Count Framework**:
- AI reasons through: complexity, observability, parent capacity, clinical value
- Examples: Simple case (2 videos), Complex case (4 videos), Clear case (1 video)
- Each video must have clear rationale for why it adds value

---

### 4. Refactored Summary/Video Prompt (The Output)

**SUMMARY_VIDEO_SYSTEM_PROMPT_REFACTORED.md** (547 lines)

**Major Changes**:

#### A. Input Change
**Before**: Receives raw transcript only
**After**: Receives extraction + transcript + completeness

```json
{
  "extracted_data": { /* 20-field structured data */ },
  "conversation_transcript": "...",
  "completeness": 90
}
```

#### B. Role Change
**Before**: "Extract everything from transcript"
**After**: "Validate & enrich extracted data"

New job:
1. ✅ Validate extraction completeness
2. ✅ Enrich with quotes from transcript
3. ✅ Organize into detailed schema
4. ✅ Determine video count intelligently
5. ✅ Generate focused video guidelines

#### C. Intelligent Video Count (NOT Fixed)

**Decision Framework**:
```
1. Concern Complexity
   - Single concern → 1-2 videos
   - Multiple clustering → 3-4 videos

2. Observability
   - Highly observable → Essential to film
   - Well-described → Less critical

3. Parent Capacity
   - Overwhelmed → 1-2 most critical
   - Organized → Can handle 3-4

4. Clinical Value
   - Adds info interview can't? → Include
   - Just confirming known? → Lower priority
```

**Three Detailed Examples**:
1. **Single concern** (speech delay) → 2 videos
2. **Complex, multiple concerns** (speech + social + sensory + repetitive) → 4 videos
3. **Clear from interview** (tantrum at transitions) → 1 video

#### D. Video Guideline Quality

Each video includes:
- **Rationale** (Hebrew) - WHY this video is important clinically
- **Instruction** (Hebrew) - WHAT to film, HOW to film it
- **Observable Indicators** (Hebrew) - What to look for (2-4 specific items)
- **Practical Tips** (optional, Hebrew)
- **Privacy Considerations** (optional, Hebrew)

#### E. Maintains Full Summary Structure
- All original detailed fields preserved
- child_details, difficulties_detailed, medical_developmental_history, etc.
- Strength-challenge balance throughout

---

## 🔄 How The System Now Works

### Step 1: Interview Phase

**AI conducts intelligent interview**:
- Uses 7-dimension reasoning framework
- Asks one main question per turn (with smart flexibility)
- Balances problems with strengths exploration
- Extracts continuously (20-field schema)
- Adapts depth based on severity, patterns, parent state
- NO mention of videos during interview

**Output**: Rich 20-field extraction + full transcript

---

### Step 2: Completion Check

**Backend calculates completeness** (e.g., 85%)

When reaches ~80%:
- Backend triggers summary/video generation
- Passes extraction + transcript to analyzer

---

### Step 3: Analysis & Video Guidelines

**Analyzer (summary prompt)**:
1. Validates extracted data
2. Enriches with transcript quotes
3. Organizes into detailed 200-field schema
4. **Intelligently determines video count** (1-4 based on reasoning)
5. Generates focused, practical video guidelines

**Output**: Complete JSON with analysis_summary + video_guidelines

---

### Step 4: Video Introduction to Parent

**Chitta explains the WHY**:
```
"כדי שנוכל להבין את [child] עוד יותר לעומק, השלב הבא הוא לצלם כמה סרטונים
קצרים... למה? כי יש דברים שקשה לתאר במילים, וראיית [child] בפעולה נותנת
לנו מידע חשוב שלא יכול לצאת רק משיחה."
```

- Sets expectations
- Explains value
- Variable number based on needs

---

## ✨ Key Improvements Summary

### Before → After

| Aspect | Before | After |
|--------|--------|-------|
| **Interview Navigation** | Rigid 5 stages | Intelligent adaptive phases |
| **Extraction** | 7 simple fields | 20 narrative fields |
| **Reasoning** | Mechanical rules | 7-dimension clinical framework |
| **Strengths** | Optional nice-to-have | Essential diagnostic data |
| **Question Pattern** | Rigidly one per turn | One with smart flexibility |
| **Video Introduction** | Mentioned prematurely | Explained with context after interview |
| **Video Count** | Fixed 2-4 | Intelligently determined 1-4 |
| **Summary Input** | Raw transcript only | Extraction + transcript |
| **Summary Role** | Extract from scratch | Validate & enrich |

---

## 📊 Architecture Alignment

### The Flow

```
┌─────────────────────────────────────────────────────────┐
│  INTERVIEW (Enhanced Prompt)                            │
│  - Intelligent reasoning (7 dimensions)                 │
│  - Adaptive depth based on context                      │
│  - Strength-challenge balance                           │
│  - Progressive extraction (20 fields)                   │
│  - No video mentions yet                                │
└────────────────┬────────────────────────────────────────┘
                 │
                 ↓ [Extraction + Transcript]
┌─────────────────────────────────────────────────────────┐
│  BACKEND                                                 │
│  - Receives 20-field extraction                         │
│  - Stores in Graphiti knowledge graph                   │
│  - Calculates completeness (~80% triggers next phase)   │
└────────────────┬────────────────────────────────────────┘
                 │
                 ↓ [Complete data package]
┌─────────────────────────────────────────────────────────┐
│  ANALYZER (Refactored Summary Prompt)                   │
│  - Validates & enriches extraction                      │
│  - Organizes into detailed 200-field schema             │
│  - Intelligently determines video count (1-4)           │
│  - Generates focused video guidelines                   │
└────────────────┬────────────────────────────────────────┘
                 │
                 ↓ [JSON: summary + video_guidelines]
┌─────────────────────────────────────────────────────────┐
│  CHITTA (Next Conversation Phase)                       │
│  - Explains WHY videos with context                     │
│  - Presents [number] personalized guidelines            │
│  - Parent feels informed and empowered                  │
└─────────────────────────────────────────────────────────┘
```

---

## 🎓 Clinical Insights Integrated

### 1. Neurologist's Wisdom
> "We should look at strengths also, otherwise all kids would be diagnosed for something."

**Implementation**:
- Strengths as first-class citizen in extraction
- `strength_challenge_balance` field in every extraction
- Strengths woven throughout interview (not separate section)
- Video guidelines include strengths-focused observations

### 2. AI Intelligence Over Rules
**Recognition**: Rigid rules fight against AI's reasoning capabilities

**Implementation**:
- Reasoning frameworks instead of mechanical checklists
- "Think about" instead of "You must do"
- Examples of good clinical thinking
- Trust AI judgment on depth and coverage

### 3. Progressive Data Capture
**Recognition**: Function calling enables continuous extraction

**Implementation**:
- Extract early and often (not just at milestones)
- Enrichment over time (Turn 5 → 20 → 30+)
- Backend merges all extractions
- Graphiti builds knowledge graph continuously

---

## 📝 All Files on Branch

**Analysis**:
1. `FIELD_COVERAGE_ANALYSIS.md` - Gap identification
2. `INTERVIEW_NAVIGATION_ANALYSIS.md` - Navigation issues
3. `INTELLIGENT_INTERVIEW_NAVIGATION.md` - Reasoning walkthrough

**Core Prompts**:
4. `INTERVIEW_SYSTEM_PROMPT_REFACTORED.md` - Original base version
5. `INTERVIEW_SYSTEM_PROMPT_ENHANCED.md` - ⭐ **New enhanced version**
6. `ADAPTIVE_EXTRACTION_SCHEMA_DESIGN.md` - Bridge design
7. `SUMMARY_VIDEO_SYSTEM_PROMPT_REFACTORED.md` - ⭐ **New refactored version**

**Summary**:
8. `PROMPT_REFACTOR_SUMMARY.md` - This document

---

## ✅ Ready for Implementation

### What's Complete

- ✅ Enhanced interview prompt with intelligent reasoning
- ✅ 20-field adaptive extraction schema
- ✅ Refactored summary/video prompt with intelligent video count
- ✅ Video introduction guidance
- ✅ All prompts aligned with function calling architecture
- ✅ Clinical insights integrated throughout
- ✅ Hebrew templates included
- ✅ Detailed examples and reasoning walkthroughs

### What's Next (Implementation)

1. **Update interview prompt in backend** → Use INTERVIEW_SYSTEM_PROMPT_ENHANCED.md
2. **Implement 20-field extraction** → Use ADAPTIVE_EXTRACTION_SCHEMA_DESIGN.md schema
3. **Update summary/video analyzer** → Use SUMMARY_VIDEO_SYSTEM_PROMPT_REFACTORED.md
4. **Test end-to-end flow**:
   - Interview → Extraction → Summary → Video Guidelines
   - Verify strength-challenge balance maintained
   - Confirm video count varies intelligently
5. **Validate with real conversations** → Iterate based on results

---

## 🎯 Success Metrics

When implemented successfully, you should see:

✅ **Interview feels natural** (not mechanical questionnaire)
✅ **Strengths captured** alongside concerns (balanced profile)
✅ **Depth adapts** to concern complexity (not one-size-fits-all)
✅ **Video count varies** (1-4 based on clinical reasoning)
✅ **Parents understand process** (videos introduced with context)
✅ **Data flows efficiently** (extraction → summary without redundant work)

---

**The system now leverages AI intelligence while maintaining clinical rigor. Ready for implementation!** 🚀
