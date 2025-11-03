# Video Analysis Workflow - Chitta Advanced

**Version:** 2.0 (Hybrid Approach)
**Last Updated:** 2025-11-03

---

## Overview

The Chitta video analysis system uses a **hybrid two-phase approach** to analyze videos submitted by parents:

1. **Phase 1: Individual Video Analysis** - Each video analyzed separately against its specific purpose
2. **Phase 2: Video Integration** - All individual analyses synthesized into comprehensive profile

This approach balances **guideline-specific depth** with **cross-context pattern recognition**.

---

## Why Hybrid? (Design Rationale)

### ❌ Alternative Rejected: Single Unified Analysis
**Approach:** Analyze all videos together in one prompt

**Problems:**
- Loses guideline-specific focus
- Must wait for all videos before starting
- Poor quality control (can't isolate problems)
- Context window limitations
- All-or-nothing (can't provide partial insights)

### ❌ Alternative Rejected: Individual Only
**Approach:** Analyze each video separately, no integration

**Problems:**
- Misses cross-context patterns
- Can't assess pervasiveness (critical diagnostic feature)
- No synthesis of overall clinical picture
- Requires manual integration

### ✅ **Our Solution: Hybrid (Individual → Integration)**

**Advantages:**
- ✅ Maintains guideline-specific focus (each video has purpose)
- ✅ Supports incremental uploads (parents upload over time)
- ✅ Quality control per video (can request re-upload if needed)
- ✅ Captures cross-context patterns (integration phase)
- ✅ Enables progressive parent engagement
- ✅ Mirrors clinical reasoning (observe → synthesize)

---

## Complete Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    CHITTA VIDEO ANALYSIS WORKFLOW                │
└─────────────────────────────────────────────────────────────────┘

Step 1: PARENT INTERVIEW
├─ Prompt: interview_analysis_prompt.md
├─ Input: Parent's responses to interview questions
└─ Output: analysis_summary.json
    ├─ Child profile
    ├─ Parent's reported concerns
    ├─ Detailed difficulties by domain
    └─ video_guidelines.json ← CRITICAL
        ├─ VS_001: Guideline 1 (rationale, instruction, indicators)
        ├─ VS_002: Guideline 2
        └─ VS_003: Guideline 3

                    ↓

Step 2: VIDEO GUIDELINES DELIVERED TO PARENT
├─ Parent receives 2-4 specific filming instructions
├─ Each guideline has:
│   ├─ Rationale: WHY we want this video
│   ├─ Instruction: WHAT to film
│   └─ Indicators: WHAT to look for
└─ Parent films videos over time (days/weeks)

                    ↓

Step 3a: INDIVIDUAL VIDEO ANALYSIS (Video 1)
├─ Prompt: individual_video_analysis_prompt.md
├─ Input:
│   ├─ analysis_summary.json (interview data)
│   ├─ this_video_guideline: VS_001
│   ├─ video_context: {video_number: 1, total: 3}
│   └─ video_file
├─ Process:
│   ├─ Analyze video against SPECIFIC guideline purpose
│   ├─ Assess if video captured target behaviors
│   ├─ Document observations, strengths, challenges
│   └─ Integrate with interview data
└─ Output: VA_001.json (individual video analysis)

                    ↓

Step 3b: INDIVIDUAL VIDEO ANALYSIS (Video 2)
├─ Prompt: individual_video_analysis_prompt.md
├─ Input:
│   ├─ analysis_summary.json
│   ├─ this_video_guideline: VS_002
│   ├─ video_context: {video_number: 2, total: 3, previous: [VA_001_summary]}
│   └─ video_file
└─ Output: VA_002.json

                    ↓

Step 3c: INDIVIDUAL VIDEO ANALYSIS (Video 3)
├─ Prompt: individual_video_analysis_prompt.md
├─ Input:
│   ├─ analysis_summary.json
│   ├─ this_video_guideline: VS_003
│   ├─ video_context: {video_number: 3, total: 3, previous: [VA_001, VA_002]}
│   └─ video_file
└─ Output: VA_003.json

                    ↓

Step 4: VIDEO INTEGRATION ANALYSIS
├─ Prompt: video_integration_prompt.md
├─ Input:
│   ├─ analysis_summary.json (interview)
│   ├─ all_video_guidelines: [VS_001, VS_002, VS_003]
│   └─ individual_video_analyses: [VA_001, VA_002, VA_003]
├─ Process:
│   ├─ Assess guideline coverage (did we get what we needed?)
│   ├─ Identify pervasive vs. context-specific patterns
│   ├─ Synthesize strength profile across videos
│   ├─ Synthesize challenge profile across videos
│   ├─ Compare to parent interview (confirmations, extensions, discrepancies)
│   ├─ Recognize DSM-5 informed patterns
│   └─ Generate recommendations
└─ Output: integration_analysis.json
    ├─ Cross-context patterns
    ├─ Integrated strength/challenge profile
    ├─ Clinical synthesis
    ├─ Sufficiency assessment
    └─ Recommendations for next steps

                    ↓

Step 4a: GENERATE CLARIFICATION QUESTIONS ← NEW INTEGRATION LOOP
├─ Prompt: video_clarification_questions_prompt.md
├─ Input:
│   ├─ analysis_summary.json (interview)
│   ├─ integration_analysis.json (from Step 4)
│   └─ individual_video_analyses
├─ Process:
│   ├─ Identify discrepancies needing clarification
│   ├─ Identify new findings needing parent context
│   ├─ Identify pervasiveness questions
│   ├─ Identify ambiguities needing parent explanation
│   ├─ Prioritize questions by clinical significance
│   └─ Generate 3-7 targeted questions for parent
└─ Output: clarification_questions.json
    ├─ 3-7 prioritized questions
    ├─ Each with context, rationale, expected answer type
    └─ OR: no questions needed (proceed to reports)

                    ↓

Step 4b: PARENT ANSWERS CLARIFICATION QUESTIONS
├─ Parent receives questions via conversational interface
├─ Chitta presents each question with:
│   ├─ Context (what we observed in video)
│   ├─ Why this matters (builds trust)
│   └─ Question (clear, empathetic, in Hebrew if needed)
├─ Parent provides answers (open text, multiple choice, etc.)
└─ Output: parent_clarification_answers.json

                    ↓

Step 4c: INTEGRATE CLARIFICATION ANSWERS
├─ Prompt: video_clarification_integration_prompt.md
├─ Input:
│   ├─ original_integration_analysis.json
│   ├─ clarification_questions.json (what was asked)
│   ├─ parent_clarification_answers.json (parent responses)
│   ├─ analysis_summary.json (for reference)
│   └─ individual_video_analyses (for reference)
├─ Process:
│   ├─ Analyze what each clarification revealed
│   ├─ Resolve discrepancies based on parent context
│   ├─ Update pervasiveness assessments
│   ├─ Refine strength/challenge profiles
│   ├─ Update DSM-5 pattern synthesis
│   ├─ Adjust diagnostic considerations
│   └─ Refine recommendations
└─ Output: updated_integration_analysis.json (v2)
    ├─ Updated cross-context patterns
    ├─ Resolved discrepancies
    ├─ Clarified pervasiveness
    ├─ Refined clinical synthesis
    ├─ Increased confidence
    └─ Updated recommendations

                    ↓

Step 5: REPORT GENERATION
├─ Input:
│   ├─ analysis_summary.json (interview)
│   ├─ updated_integration_analysis.json (video synthesis with clarifications)
│   └─ individual_video_analyses (for specific examples)
├─ Outputs:
│   ├─ Parent Report (מדריך להורים)
│   │   ├─ Clear, compassionate explanations
│   │   ├─ Strengths emphasized
│   │   ├─ Concrete examples from videos
│   │   └─ Actionable guidance
│   │
│   └─ Professional Report (דוח מקצועי)
│       ├─ Clinical detail
│       ├─ DSM-5 informed patterns
│       ├─ Diagnostic considerations
│       └─ Recommendations for assessment/intervention

                    ↓

Step 6: EXPERT RECOMMENDATIONS
└─ Based on integrated findings, recommend appropriate professionals
```

---

## Phase 1: Individual Video Analysis

### Purpose
Analyze each video **in depth** against its **specific purpose** while maintaining flexibility to observe beyond the guideline.

### Prompt Used
`individual_video_analysis_prompt.md`

### Key Features

#### 1. **Guideline-Informed Focus**
Each video analysis knows:
- **WHY** this video was requested (rationale)
- **WHAT** was supposed to be filmed (instruction)
- **WHAT** we hoped to observe (potential indicators)

This enables **prioritized, purpose-driven analysis** rather than generic observation.

#### 2. **Video Guideline Assessment**
Every individual analysis includes explicit assessment:
- ✅ Did we successfully capture target behaviors?
- ✅ Was the context appropriate?
- ✅ Is this video sufficient or do we need re-upload?
- ✅ What quality is the capture?

**Benefit:** Quality control per video. Can request re-upload of Video 2 while proceeding with Videos 1 & 3.

#### 3. **Intelligent Reasoning Framework**
Analysts apply 5-question framework to each observation:
1. Clinical significance?
2. Frequency & intensity?
3. Context relevance?
4. Integration with interview?
5. Diagnostic differentiation value?

**Benefit:** Prioritizes meaningful observations, avoids over-reporting typical behaviors.

#### 4. **Developmental Context**
Explicit guidance on age-appropriate expectations.

**Benefit:** Reduces false positives (flagging typical behavior as concerning).

#### 5. **Strength-Informed Mandate**
Strengths are **required**, not optional. Minimum 2-3 specific strengths per video.

**Benefit:** Ensures balanced, clinically informative analysis.

#### 6. **Integration with Interview**
Every observation linked back to:
- Confirms parent report?
- New finding?
- Discrepancy?

**Benefit:** Coherent narrative across data sources.

### Output
`VA_XXX.json` - Complete individual video analysis

**Key sections:**
- `video_guideline_assessment` - Did we get what we needed?
- `prioritized_observations` - Most significant findings
- `core_observational_metrics` - Detailed behavioral data
- `observed_strengths_and_positive_behaviors` - Strength profile
- `interview_data_integration` - Links to parent report
- `justification_evidence` - Timestamp-based evidence

---

## Phase 2: Video Integration

### Purpose
Synthesize individual analyses into **comprehensive clinical picture** by identifying patterns across contexts.

### Prompt Used
`video_integration_prompt.md`

### Key Features

#### 1. **Guideline Coverage Assessment**
- Were all guidelines adequately addressed?
- Is video evidence sufficient for conclusions?
- Are there critical gaps?
- Recommendation: proceed to report | need additional video

**Benefit:** Ensures evidence base is solid before generating reports.

#### 2. **Cross-Context Pattern Recognition**

Identifies three pattern types:

**a) Pervasive Patterns** (across ALL/MOST videos)
- Example: Limited eye contact in home (V1), playground (V2), structured task (V3)
- **Interpretation:** Core, stable characteristic → More clinically significant

**b) Context-Specific Patterns** (in SOME videos, not others)
- Example: Regulated during structured activity (V1), dysregulated during unstructured play (V2)
- **Interpretation:** Environmental/situational triggers → Informs intervention, shows what supports work

**c) Compensatory Patterns** (strategies child uses)
- Example: Uses gestures when verbal unclear (across videos)
- **Interpretation:** Child's coping mechanism → Build on this strength

**Benefit:** Pattern of pervasiveness is itself diagnostic. Pervasive challenges + limited strengths → more significant developmental concern.

#### 3. **Integrated Strength Profile**
Synthesizes strengths across videos:
- Core competencies (consistent across contexts)
- Context-specific strengths (when supported)
- Compensatory strategies
- **Strength-challenge balance** (diagnostic significance)

**Benefit:** Comprehensive understanding of child's resources and intervention leverage points.

#### 4. **Integrated Challenge Profile**
Synthesizes challenges:
- Pervasive vs. context-specific
- Severity assessment (considering age)
- Functional impact

**Benefit:** Nuanced understanding of when/where child struggles.

#### 5. **Interview Comparison Synthesis**
- Parent concerns strongly confirmed (across videos)
- Parent concerns partially confirmed (context-specific)
- New patterns beyond parent report
- Discrepancies (with explanations)

**Benefit:** Validates parent experience, adds observational depth, explains variability.

#### 6. **DSM-5 Informed Pattern Synthesis**
Synthesizes behavioral indicators across videos:
- ASD pattern: pervasive | context-specific | minimal
- ADHD pattern: pervasive | context-specific | minimal
- Anxiety, sensory, motor, language patterns

**NOT diagnosis.** Observable patterns that inform clinical reasoning.

**Benefit:** Structured clinical reasoning about differential considerations.

#### 7. **Recommendations**
Based on integrated picture:
- Video evidence sufficiency
- Professional referral priorities
- Intervention focus areas
- Parent guidance priorities

**Benefit:** Clear next steps based on comprehensive data.

### Output
`integration_analysis.json` - Comprehensive synthesis

**Key sections:**
- `guideline_coverage_assessment`
- `cross_context_behavioral_patterns`
- `integrated_strength_profile`
- `integrated_challenge_profile`
- `integrated_interview_comparison`
- `dsm5_informed_pattern_synthesis`
- `clinical_synthesis`
- `recommendations`

---

## Data Flow Example

### Example Case: Child with Reported Peer Interaction Difficulties

**Interview Output (analysis_summary.json):**
```json
{
  "child": {"name": "Yoni", "age_years": 4.5, "gender": "Male"},
  "difficulties_detailed": [
    {
      "area": "אינטראקציה חברתית",
      "description": "הורה דיווח שיוני מתקשה ליצור קשר עם ילדים אחרים. הוא משחק לבד בגן."
    }
  ],
  "video_guidelines": [
    {
      "guideline_id": "VS_001",
      "rationale_for_suggestion": "Parent reported peer interaction difficulties. This video will establish baseline social-communication functioning in familiar, comfortable setting with family member.",
      "instruction_for_parent": "Film Yoni during free play at home with you or sibling for 5-10 minutes.",
      "potential_observable_indicators": ["Eye contact quality", "Joint attention", "Communication quality", "Engagement level"]
    },
    {
      "guideline_id": "VS_002",
      "rationale_for_suggestion": "Parent reported peer interaction difficulties. This video will directly observe social approach, peer response, and communication attempts in naturalistic peer context.",
      "instruction_for_parent": "Film Yoni at playground or park with other children present for 5-10 minutes.",
      "potential_observable_indicators": ["Social approach behaviors", "Response to peer initiations", "Parallel vs interactive play", "Communication attempts with peers"]
    },
    {
      "guideline_id": "VS_003",
      "rationale_for_suggestion": "To assess frustration tolerance, emotional regulation, and task persistence, which often co-occur with social communication challenges.",
      "instruction_for_parent": "Film Yoni during a mildly challenging task (puzzle, homework, learning new skill) for 5-10 minutes.",
      "potential_observable_indicators": ["Frustration management", "Persistence", "Help-seeking behavior", "Emotional regulation"]
    }
  ]
}
```

**Individual Analysis 1 (VA_001.json) - Home Free Play:**
```json
{
  "video_analysis_id": "VA_001",
  "guideline_id": "VS_001",
  "video_guideline_assessment": {
    "successfully_captured_target_behaviors": true,
    "explanation": "Video captured 8 minutes of natural play with mother. Multiple opportunities for eye contact, joint attention, and communication were observable.",
    "quality_of_capture": "excellent"
  },
  "prioritized_observations": {
    "most_clinically_significant_findings": [
      {
        "observation": "Child demonstrates age-appropriate eye contact and joint attention with mother during play",
        "clinical_significance": "Suggests social communication skills are intact in familiar, comfortable context with caregiver. This is IMPORTANT for differential - indicates skills are present but may be context-specific.",
        "relation_to_guideline": "directly_addresses",
        "relation_to_interview": "contrasts_with_parent_concern_in_peer_context"
      }
    ]
  },
  "observed_strengths_and_positive_behaviors": [
    {
      "specific_strength": "Strong symbolic play abilities - created elaborate narrative with toy figures",
      "clinical_relevance": "Indicates intact cognitive and imaginative capacities"
    }
  ]
}
```

**Individual Analysis 2 (VA_002.json) - Playground with Peers:**
```json
{
  "video_analysis_id": "VA_002",
  "guideline_id": "VS_002",
  "video_guideline_assessment": {
    "successfully_captured_target_behaviors": true,
    "explanation": "Video captured 10 minutes at playground with 4-5 peers present. Multiple opportunities for peer interaction observable.",
    "quality_of_capture": "good"
  },
  "prioritized_observations": {
    "most_clinically_significant_findings": [
      {
        "observation": "Child did not approach peers despite multiple opportunities. Played alone on swings for 7/10 minutes. When peer approached, child moved away without verbal response.",
        "clinical_significance": "CONFIRMS parent's report of peer interaction difficulties. Contrasts sharply with comfortable social engagement with mother in VA_001, suggesting CONTEXT-SPECIFIC social challenge.",
        "relation_to_guideline": "directly_addresses",
        "relation_to_interview": "confirms_parent_report"
      }
    ]
  },
  "observed_strengths_and_positive_behaviors": [
    {
      "specific_strength": "Strong gross motor skills - confident climbing, swinging, running",
      "clinical_relevance": "Motor abilities intact; social difficulties not due to physical limitations"
    }
  ]
}
```

**Integration Analysis (integration_analysis.json):**
```json
{
  "cross_context_behavioral_patterns": {
    "context_specific_patterns": [
      {
        "pattern_description": "Strong social communication with mother (VA_001: good eye contact, joint attention, reciprocal play) but minimal social engagement with peers (VA_002: avoidance, no approach, no verbal interaction)",
        "contexts_where_observed": ["VA_002"],
        "contexts_where_NOT_observed": ["VA_001"],
        "contextual_factors": "Familiar caregiver vs. unfamiliar peers",
        "clinical_interpretation": "This context-specific pattern suggests SELECTIVE social difficulty specific to peer interactions rather than global social communication impairment. Child demonstrates capacity for social engagement when comfortable. This pattern is more consistent with social anxiety or peer-specific social skills deficit than pervasive ASD-type social communication disorder.",
        "strength_or_challenge": "challenge"
      }
    ]
  },
  "integrated_strength_profile": {
    "core_strengths_across_contexts": [
      {
        "strength_domain": "Cognitive",
        "specific_strength": "Strong symbolic play and imaginative abilities",
        "consistency": "pervasive",
        "leverage_potential": "Can use play-based social skills intervention; child has cognitive resources for learning peer interaction strategies"
      }
    ]
  },
  "clinical_synthesis": {
    "diagnostic_considerations": {
      "patterns_most_consistent_with": "Context-specific social anxiety or peer interaction skills deficit. Social communication capacities appear intact (demonstrated with mother) but not utilized in peer contexts.",
      "differential_considerations": [
        "Social Anxiety Disorder - selective social withdrawal in peer contexts",
        "Pragmatic language challenges specific to peer interaction",
        "Less consistent with: ASD (would expect more pervasive social communication differences across contexts)"
      ]
    }
  },
  "recommendations": {
    "professional_referral_considerations": [
      {
        "professional_type": "Child Psychologist specializing in social skills",
        "rationale": "Context-specific peer interaction difficulties with intact baseline social communication skills suggests targeted social skills intervention and possible anxiety management",
        "priority": "high"
      }
    ]
  }
}
```

**Key Insight from Integration:**
The **pattern of context-specificity** (good social communication with mom, poor with peers) is itself the most diagnostic finding. This wouldn't be clear from any single video but emerges clearly from cross-context comparison.

---

## Technical Implementation

### Workflow Orchestration

```python
# Pseudo-code for video analysis workflow

async def analyze_videos_hybrid(child_id, analysis_summary, video_files):
    """
    Hybrid video analysis workflow
    """
    # Phase 1: Individual analyses
    individual_analyses = []

    for i, video_file in enumerate(video_files):
        video_guideline = analysis_summary['video_guidelines'][i]

        # Analyze individual video
        analysis = await analyze_individual_video(
            child=analysis_summary['child'],
            analysis_summary=analysis_summary,
            this_video_guideline=video_guideline,
            video_context={
                'video_number': i + 1,
                'total_videos_requested': len(video_files),
                'previous_video_summaries': [
                    summarize_for_context(va) for va in individual_analyses
                ]
            },
            video_file=video_file,
            prompt_template='individual_video_analysis_prompt.md'
        )

        individual_analyses.append(analysis)

        # Optional: Provide parent with immediate mini-feedback
        await send_parent_mini_feedback(analysis.key_insights)

    # Phase 2: Integration
    integration_analysis = await integrate_video_analyses(
        child=analysis_summary['child'],
        analysis_summary=analysis_summary,
        all_video_guidelines=analysis_summary['video_guidelines'],
        individual_video_analyses=individual_analyses,
        prompt_template='video_integration_prompt.md'
    )

    # Check sufficiency
    if integration_analysis['guideline_coverage_assessment']['sufficiency_for_conclusions'] == 'insufficient':
        # Request additional videos
        return {
            'status': 'need_more_videos',
            'recommendations': integration_analysis['recommendations']['if_additional_video_needed']
        }

    # Phase 3: Generate reports
    reports = await generate_reports(
        analysis_summary=analysis_summary,
        integration_analysis=integration_analysis,
        individual_analyses=individual_analyses
    )

    return {
        'status': 'complete',
        'individual_analyses': individual_analyses,
        'integration_analysis': integration_analysis,
        'reports': reports
    }
```

---

## Prompt Usage

### Individual Video Analysis

**When to use:** For each video uploaded by parent

**Input:**
```json
{
  "child": {
    "name": "Yoni",
    "age_years": 4.5,
    "gender": "Male"
  },
  "analysis_summary": { /* full interview summary */ },
  "this_video_guideline": {
    "guideline_id": "VS_002",
    "rationale_for_suggestion": "...",
    "instruction_for_parent": "...",
    "potential_observable_indicators": [...]
  },
  "video_context": {
    "video_number": 2,
    "total_videos_requested": 3,
    "previous_video_summaries": [...]  // optional
  }
}
```

**Prompt:** `individual_video_analysis_prompt.md`

**Output:** `VA_XXX.json`

### Video Integration

**When to use:** After all (or most) videos are analyzed individually

**Input:**
```json
{
  "child": {...},
  "analysis_summary": { /* interview */ },
  "all_video_guidelines": [VS_001, VS_002, VS_003],
  "individual_video_analyses": [VA_001, VA_002, VA_003]
}
```

**Prompt:** `video_integration_prompt.md`

**Output:** `integration_analysis.json`

---

## Phase 2.5: Clarification Loop (NEW)

### Purpose
After video integration, ask parent targeted clarification questions to:
- Resolve discrepancies between parent report and video observations
- Gather context for ambiguous observations
- Assess pervasiveness of patterns beyond what videos show
- Confirm/disconfirm new findings observed in videos

### Why This Matters

**Clinically:**
- Videos provide LIMITED time samples (10-30 minutes total)
- Parent knows child across ALL contexts and time
- Discrepancies often reflect context-specificity (diagnostically valuable!)
- Parent's perspective explains "why" behind behaviors

**Example Impact:**
- Video shows "mild attention difficulty during puzzle"
- Parent clarifies: "That puzzle is his FAVORITE - his attention is much worse with homework!"
- **Result:** Changes interpretation from "mild attention issue" to "significant ADHD pattern, even preferred tasks show difficulty"

### Clarification Questions Prompt

**When to use:** After integration analysis is complete

**Input:**
```json
{
  "analysis_summary": { /* interview */ },
  "integration_analysis": { /* from Step 4 */ },
  "individual_video_analyses": [ /* all videos */ ]
}
```

**Prompt:** `video_clarification_questions_prompt.md`

**Output:** `clarification_questions.json`
- 3-7 prioritized questions
- Each with clinical rationale
- OR: "no questions needed" (proceed to reports)

**Question Categories:**
1. **Discrepancy resolution** (parent said X, video showed Y)
2. **New finding confirmation** (observed in video, not mentioned in interview)
3. **Pervasiveness assessment** (does this happen in other contexts?)
4. **Context/frequency calibration** (was video typical or unusual?)
5. **Parent interpretation** (what was child feeling/experiencing?)
6. **Developmental history** (when did this start, has it changed?)

**Prioritization Framework:**
- **HIGH:** Discrepancies, new findings, pervasiveness for diagnostic patterns
- **MEDIUM:** Contextual clarifications, frequency questions
- **LOW:** Parent interpretation (nice to have)

### Parent Answers Questions

**UX Flow:**
1. Chitta presents each question conversationally
2. Provides context: "In Video 2, we noticed [behavior]..."
3. Explains why it matters: "This helps us understand..."
4. Asks question clearly, empathetically
5. Parent responds (open text, multiple choice, rating, etc.)

**Parent burden:** Keep to 3-7 questions max, respect parent's time

### Clarification Integration Prompt

**When to use:** After parent provides clarification answers

**Input:**
```json
{
  "original_integration_analysis": { /* from Step 4 */ },
  "clarification_questions_asked": { /* what we asked */ },
  "parent_clarification_answers": [ /* parent responses */ ],
  "analysis_summary": { /* for reference */ },
  "individual_video_analyses": [ /* for reference */ ]
}
```

**Prompt:** `video_clarification_integration_prompt.md`

**Output:** `updated_integration_analysis.json` (v2)

**What Gets Updated:**

1. **Cross-Context Patterns** - Patterns may move from "context-specific" to "pervasive" or vice versa based on parent clarification
2. **Interview Comparison** - Discrepancies get resolved with parent's context
3. **Strength/Challenge Profiles** - Confirmed or adjusted based on frequency/pervasiveness
4. **DSM-5 Pattern Synthesis** - Updated pervasiveness classifications
5. **Clinical Synthesis** - Refined with new insights, typically increased confidence
6. **Recommendations** - Adjusted based on clarified understanding

**Example Integration:**

**Original (from videos):**
```json
{
  "pattern": "Limited peer interaction observed in playground video",
  "pervasiveness": "unknown"
}
```

**Parent Clarification:**
"Yes, this happens at school, with cousins, everywhere. He never approaches other kids."

**Updated Integration:**
```json
{
  "pattern": "Pervasive limited peer interaction across all contexts (confirmed by parent: school, playground, family gatherings)",
  "pervasiveness": "pervasive_across_all_contexts",
  "parent_clarification": {
    "confirmed_pervasive": true,
    "additional_contexts": ["school", "family gatherings", "cousins"],
    "pattern_description": "Never initiates with peers across all settings"
  },
  "clinical_significance": "HIGH - pervasive social initiation deficit warrants comprehensive social-communication assessment"
}
```

### Benefits of Clarification Loop

**1. Resolves Ambiguities**
- Videos show WHAT, parents explain WHY and WHEN
- Context turns confusion into clarity

**2. Establishes Pervasiveness**
- Critical for differential diagnosis
- Pervasive vs. context-specific determines intervention approach

**3. Increases Confidence**
- More data = more accurate understanding
- Typically confidence goes from "moderate" to "high"

**4. Improves Reports**
- More accurate recommendations
- Parents feel heard and understood
- Clinicians get comprehensive picture

**5. Builds Parent Awareness**
- Questions draw parent attention to patterns
- Helps parents become better observers
- Strengthens parent-Chitta partnership

### When to Skip Clarification

**Don't ask questions if:**
- Video observations fully align with interview (no discrepancies)
- Context is entirely clear from videos
- No new clinically significant patterns observed
- Pervasiveness already well-established in interview
- Time-sensitive situation where delay harmful

**In these cases:** Proceed directly to report generation

---

## Benefits of This Approach

### 1. **Clinical Rigor**
- ✅ Guideline-specific depth AND cross-context patterns
- ✅ Quality control per video
- ✅ Pervasiveness assessment (critical for diagnosis)

### 2. **User Experience**
- ✅ Parents can upload videos incrementally (over days/weeks)
- ✅ Optional immediate feedback after each video
- ✅ Progressive engagement (not all-or-nothing)

### 3. **Flexibility**
- ✅ Works with 1 video, 2 videos, or 5 videos
- ✅ Can handle incomplete video sets (integration assesses sufficiency)
- ✅ Can request specific video re-uploads

### 4. **Cost Efficiency**
- ✅ Individual analyses can be parallelized
- ✅ Integration is relatively lightweight (synthesizes JSON, not re-analyzing videos)

### 5. **Clinical Accuracy**
- ✅ Reduces false positives (reasoning framework, developmental context)
- ✅ Emphasizes strengths (diagnostic balance)
- ✅ Captures pervasiveness (cross-context integration)
- ✅ Explains discrepancies (parent report vs. video)

---

## Future Enhancements

### Potential Additions:
1. **Adaptive Video Requests**: After VA_001, integration could request additional targeted videos
2. **Parent Real-Time Guidance**: After individual analysis, provide parent with specific filming tips for next video
3. **Video Quality Pre-Check**: Automated check for video quality before analysis
4. **Strength-Challenge Visualizations**: Generate visual profiles of strength-challenge balance
5. **Longitudinal Tracking**: Compare video analyses over time (3 months later, 6 months later)

---

## Related Documents

- `individual_video_analysis_prompt.md` - Prompt for Phase 1 (individual video analysis)
- `video_integration_prompt.md` - Prompt for Phase 2 (cross-video integration)
- `video_clarification_questions_prompt.md` - Prompt for Phase 2.5a (generate clarification questions)
- `video_clarification_integration_prompt.md` - Prompt for Phase 2.5b (integrate clarification answers)
- `interview_analysis_prompt.md` - Generates video guidelines from interview
- `summary_generation_prompt.md` - Uses integration output to create parent/professional reports

---

**Questions or suggestions?** This workflow is designed to be clinically robust while remaining practical and user-friendly. Feedback welcome!
