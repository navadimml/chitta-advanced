# Adaptive Extraction Schema Design

**Purpose**: Bridge between intelligent interview navigation and detailed summary/video guidelines
**Version**: 1.0
**Last Updated**: November 3, 2025

---

## Design Philosophy

### The Challenge

**Interview extraction needs to be:**
- ✅ Simple enough for real-time function calling
- ✅ Rich enough to capture clinical nuance
- ✅ Flexible enough to adapt to conversation flow
- ✅ Structured enough to inform video guidelines

**Summary needs:**
- ✅ ~100-200 discrete data points
- ✅ Very detailed nested structure for video guidelines
- ✅ Specific examples with 10+ sub-fields each

**The Solution**: Progressive narrative extraction that gets richer over time

---

## Extraction Schema (20 Fields)

### Basic Structure

```typescript
interface InterviewExtraction {
  // Basic Info (3 fields)
  child_name?: string;
  age?: number;
  gender?: string;

  // Primary Concerns (4 fields - BALANCED WITH STRENGTHS)
  primary_concerns: string[];  // ["speech", "social", "attention", etc.]
  concern_details: string;     // Rich narrative synthesis
  strengths: string;           // Equally important! What child loves/is good at
  strength_challenge_balance: string;  // AI's assessment of profile

  // Behavioral Details (3 fields)
  specific_examples: string;   // Narrative of specific situations with context
  frequency_intensity: string; // How often, how severe
  impact_assessment: string;   // On child's functioning + parent's emotional state

  // Developmental Context (4 fields)
  developmental_history: string;  // Milestones, pregnancy/birth, medical
  sensory_indicators?: string;    // Sensory patterns if relevant
  previous_assessments?: string;  // Prior diagnoses/evaluations
  previous_interventions?: string; // What's been tried, effectiveness

  // Environmental Context (3 fields)
  family_context: string;      // Siblings, family history, stressors
  educational_context: string; // School/daycare, adjustment, supports
  support_network?: string;    // Therapists, helpers, resources

  // Parent's Journey (3 fields)
  parent_emotional_state: string;     // How parent is coping
  parent_strategies_tried: string;    // What parent has attempted
  parent_hopes_and_needs: string;     // What they want from this process

  // Meta (optional)
  urgent_flags?: string[];     // Safety concerns, immediate needs
  interview_completeness?: number;  // Backend calculates, AI can suggest
}
```

---

## How It Works: Progressive Enrichment

### Turn 5-10: Foundation
```javascript
{
  child_name: "Yoni",
  age: 3.5,
  gender: "male",
  primary_concerns: ["speech", "social"],
  concern_details: "Speech: Limited to 3-4 words (mama, dada, water, more) at 3.5yo. Social: Prefers solitary play, doesn't engage with peers at playground.",
  strengths: "Loves trains, can focus on train play for extended periods",
  strength_challenge_balance: "Clear interest and sustained attention on preferred activities, but significant speech delay and peer interaction challenges"
}
```

**What this captures**:
- Basic facts
- Main concerns identified
- Initial strengths noted
- AI's initial assessment of profile

---

### Turn 15-20: Depth Added

```javascript
{
  child_name: "Yoni",
  age: 3.5,
  gender: "male",
  primary_concerns: ["speech", "social", "repetitive_behaviors"],
  concern_details: "Speech: Very limited expressive language - only 4 single words (mama, dada, water, more), no two-word combinations. Good comprehension (follows 2-step directions like 'get your shoes and bring them here'). Social: Avoids peer interaction at playground (ignores when called by other children), but strong eye contact and cuddling with parents during reading time. Play: Prefers organizing activities (lining up trains in rows, watching them go back and forth) over symbolic/imaginative play.",

  strengths: "Advanced visual-spatial skills (completes puzzles 2 age levels above), excellent memory (knows all Thomas train characters by name), sustained attention on preferred activities (can play with trains for 1+ hour), seeks physical comfort from parents (cuddles during reading), warm emotional connection with caregivers",

  strength_challenge_balance: "Profile shows relative strength in non-verbal/visual domains (puzzles, memory, organization) with significant challenges in verbal/social communication. Warm attachment to parents preserved. Pattern suggests language-based difficulty rather than pervasive social-emotional impairment.",

  specific_examples: "Example 1 - Speech: At dinner yesterday, wanted water but couldn't ask. Said 'water' and pointed. When parent asked 'do you want more water?', he said 'more' but didn't combine words. Example 2 - Social: At playground Tuesday, two children called 'Yoni, come play!' but he continued lining up sticks by himself. Example 3 - Play: Every day after preschool, immediately takes out trains and lines them up by color, watches them roll, lines them up again. Does this for 30-45 minutes.",

  frequency_intensity: "Speech limitation is constant (always uses single words, never combines). Peer avoidance happens 'most of the time' at playground/preschool. Train organizing is daily ritual, very strong preference. Parent rates speech concern as 8/10 severity, social as 6/10, repetitive play as 4/10.",

  impact_assessment: "Child: Frustration when can't communicate needs (sometimes cries when not understood). Isolated at preschool (teacher reports he plays alone while others play in groups). Parent: Mother feels 'very worried' about speech, frustrated with pediatrician's 'wait and see' advice, notices gap between Yoni and verbal older sister feels 'painful'. Family dinners are stressful when Yoni can't express himself.",

  developmental_history: "Pregnancy and birth: Normal, no complications. Milestones: Walked at 14 months (typical), but speech delay noted from age 2 (expected first words by 12-18 months, first word 'mama' came at 18 months, vocabulary hasn't grown since). No regression. Hearing and vision tested by pediatrician at age 3 checkup - both normal.",

  parent_strategies_tried: "Mother tried: Reading more books together (Yoni enjoys but doesn't increase speech), naming objects throughout day, limiting screen time, encouraging him to 'use words'. Father tried: Teaching specific phrases ('I want ___'), but Yoni doesn't imitate. Strategies have minimal impact so far.",

  parent_hopes_and_needs: "Mother wants: (1) To know if this is 'just a late talker' or something more serious, (2) Clear guidance on whether to pursue speech therapy now or wait, (3) Ways to help Yoni communicate and reduce his frustration. Very action-oriented, wants to 'do something' rather than wait."
}
```

**What this adds**:
- Rich narrative details
- Specific concrete examples with context
- Frequency/intensity/impact data
- Initial developmental history
- Parent's strategies and hopes
- **Strength-challenge balance analysis**

---

### Turn 30+: Complete Picture

```javascript
{
  // [All previous fields, now even more enriched]

  family_context: "Older sister Noa, age 6, very verbal ('talks non-stop' per mother), developmentally typical. Sister sometimes gets frustrated that Yoni doesn't respond to her verbally, but they play together with trains. Mother's side: No family history of speech/developmental delays. Father's side: Father's brother was 'a late talker' but caught up by kindergarten. Parents are married, stable home, middle-class, language-rich environment (lots of books, conversation).",

  educational_context: "Attends local preschool 3 days/week (9am-1pm), integrated setting (no special education). Teacher report: 'Yoni is sweet and follows routines well, but doesn't participate in circle time songs/activities and plays alone during free play. We've noticed he prefers solitary activities.' No special services currently provided. Teacher suggested speech evaluation but hasn't pushed it strongly.",

  support_network: "No current therapists or interventions. Pediatrician recommended 'wait and see' at 3-year checkup. Grandparents (maternal) nearby and supportive but 'old school' - tell mother 'boys talk later, don't worry'. Father works long hours, mother is primary caregiver and point person.",

  previous_assessments: "None. Pediatrician did hearing/vision screen at age 3 (normal) but no formal developmental evaluation or speech assessment.",

  previous_interventions: "None to date.",

  sensory_indicators: "Mother notes Yoni doesn't like loud noises (covers ears at vacuum cleaner, gets upset at loud restaurants). Prefers soft clothing (cuts tags off shirts). Otherwise no strong sensory sensitivities reported. Doesn't seek excessive sensory input.",

  parent_emotional_state: "Mother: Oscillates between worry and frustration. Worried that 'something is wrong', frustrated that pediatrician minimizes concerns, feels isolated because other preschool parents' kids are all talking. Sometimes feels guilty ('Is it something I did or didn't do?'). Father: More 'wait and see' mindset initially, but becoming concerned as gap widens with peers. Both parents united in wanting answers.",

  strength_challenge_balance: "Profile shows classic pattern of relative strength in non-verbal domains (visual-spatial, memory, sustained attention) with significant delay in expressive language and peer social engagement. Importantly, receptive language appears intact (follows 2-step directions) and social-emotional connection with parents is warm and appropriate (eye contact, cuddling, shared enjoyment). This pattern suggests specific language impairment rather than broader autism spectrum presentation. Strengths (puzzles, memory, focus, attachment) are clear assets to build upon in intervention.",

  interview_completeness: 90
}
```

**What this completes**:
- Full family and environmental context
- Educational setting details
- Support network mapping
- Assessment/intervention history
- Sensory profile
- Parent emotional journey
- Comprehensive strength-challenge analysis
- Completeness self-assessment

---

## Key Design Principles

### 1. Narrative Over Rigid Fields

**Why**: AI is better at narrative synthesis than filling checkboxes

**Example**:
```
❌ Rigid:
{
  concern_1_example_1_when: "dinnertime",
  concern_1_example_1_where: "kitchen table",
  concern_1_example_1_trigger: "wanted water",
  concern_1_example_1_behavior: "said 'water' and pointed",
  // [10 more fields per example]
}

✅ Narrative:
{
  specific_examples: "At dinner yesterday, wanted water but couldn't ask.
  Said 'water' and pointed. When parent asked 'do you want more water?',
  he said 'more' but didn't combine words. Parent understands his needs but
  worries about how he'll communicate with others."
}
```

**Advantage**: Captures context, nuance, and relationships that rigid fields miss.

---

### 2. Strength-Challenge Balance as First-Class Citizen

**Critical field**: `strength_challenge_balance`

This isn't optional "nice to have" - it's **essential diagnostic information** that helps differentiate:
- Pervasive developmental issues (few strengths)
- Specific difficulties (strengths in other domains)
- Child's cognitive profile and potential

**AI's job**: Continuously update this assessment as more information emerges.

---

### 3. Progressive Enrichment

**Not**: "Fill all 20 fields on first extraction"
**Instead**: "Extract what you know now, enrich later"

**Early extraction** might have:
- 8 fields filled
- Brief content

**Late extraction** might have:
- 18 fields filled
- Rich narrative details

**Backend**: Merges all extractions into one coherent profile

---

### 4. Parent's Journey is Data

**Traditional intake**: Child-focused only
**Our approach**: Child + Parent's experience

**Why it matters**:
- Parent's emotional state affects compliance with recommendations
- Parent's strategies-tried inform what hasn't worked
- Parent's hopes guide what report should prioritize
- Parent's frustrations (e.g., with "wait and see") are clinical context

**Fields dedicated to this**:
- `parent_emotional_state`
- `parent_strategies_tried`
- `parent_hopes_and_needs`

---

## How Summary Prompt Uses This

The summary/video prompt will receive:

```javascript
{
  "extracted_data": {
    // The 20-field extraction object (fully or partially filled)
  },
  "conversation_transcript": "...full Hebrew transcript...",
  "completeness": 90
}
```

**Summary's job**:
1. **Validate** extraction completeness
2. **Enrich** with specific quotes from transcript
3. **Organize** into the detailed 200-field schema for video guidelines
4. **Determine video count intelligently** based on:
   - Complexity of concerns
   - What needs visual observation
   - Parent's capacity
   - Clinical judgment (not fixed number!)

---

## Intelligent Video Count Determination

**NOT**: "Always create 3-4 video guidelines"
**INSTEAD**: AI reasons about how many videos are needed

### Decision Framework for Summary Prompt

**Factors to consider**:

1. **Concern Complexity**
   - Single, clear concern → Fewer videos (1-2)
   - Multiple clustering concerns → More videos (3-4)
   - Need to see different contexts → More videos

2. **Observability**
   - Concerns clearly observable in natural behavior → Essential videos
   - Concerns already well-described by parent → Less critical to film

3. **Parent Capacity**
   - Overwhelmed parent → Start with 1-2 most critical videos
   - Engaged, capable parent → Can handle 3-4 targeted videos

4. **Clinical Value**
   - Will this video add information that interview can't provide? → Yes = include
   - Is this just confirming what we already know? → Lower priority

### Examples

**Case 1: Simple, Single Concern**
```
Child: 3.5yo with speech delay only
Strengths: Good social engagement, typical play
Parent: Capable, organized

Videos needed: 2
1. Free play conversation (capture expressive language in natural context)
2. Following directions task (confirm receptive language intact)

Rationale: Speech can be clearly observed, need to see expressive + receptive.
Parent can handle 2 focused videos easily.
```

**Case 2: Complex, Multiple Concerns**
```
Child: 4yo with speech delay + social avoidance + sensory sensitivities
Strengths: Visual-spatial, focused interests
Parent: Anxious but motivated

Videos needed: 4
1. Peer interaction at playground (see social approach/avoidance patterns)
2. Mealtime routine (sensory responses to foods, family interaction)
3. Free play with preferred toys (quality of play, communication attempts)
4. Transition challenge (see regulation strategies, parental response)

Rationale: Multiple concerns need different contexts to observe.
Videos will show relationships between speech, social, sensory domains.
```

**Case 3: Well-Described Concern, Clear from Interview**
```
Child: 5yo with tantrum behavior at transitions
Strengths: Verbally advanced, socially engaged, academically strong
Parent: Already filmed tantrum on phone to show pediatrician

Videos needed: 1-2
1. Successful transition (parent's effective strategy in action)
2. Optional: Challenging transition (if parent willing and it adds value)

Rationale: Problem is clear from interview. More value in seeing what WORKS
than confirming what doesn't work. Don't burden parent with redundant filming.
```

---

## Summary

**Extraction schema (20 fields)**:
- ✅ Simple enough for real-time function calling
- ✅ Rich enough with narrative synthesis
- ✅ Progressive (gets richer over time)
- ✅ Balances strengths and challenges equally
- ✅ Includes parent's journey as data

**Video count determination**:
- ✅ Intelligently reasoned (not fixed)
- ✅ Based on complexity, observability, parent capacity, clinical value
- ✅ Range: 1-4 videos typically
- ✅ Each video has clear rationale

**Next step**: Refactor summary/video prompt to use this schema and intelligent video count reasoning.
