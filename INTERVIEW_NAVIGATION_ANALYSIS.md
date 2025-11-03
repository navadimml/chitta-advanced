# Interview Navigation Analysis: Does the AI Really Drill Deep?

## Your Concern: "How does the refactored prompt navigate the interview intelligently to cover all areas?"

---

## What the Current Refactored Prompt Says

### Navigation Guidance (Line 99-131)

**Critical Rule** (Line 101-103):
> "Your primary guide is the challenges from step 3. If the main concern was tantrums, focus on behavior/emotions questions. If it was homework struggles, focus on learning/organization and attention."

**Areas to Cover** (listed, but not mandated):
- Communication
- Social/Play
- Behavior/Emotions
- Attention/Focus
- Learning/Organization
- Sensory Sensitivities
- Daily Routines
- Developmental/Medical History
- Environment/Support

**The Problem**:
- ❌ No explicit tracking of what's been covered
- ❌ No systematic way to know when to pivot
- ❌ No depth guidelines per area
- ❌ Relies on LLM's implicit reasoning

---

## Let's Test: Would This Work?

### Scenario 1: Parent with Multiple Concerns

```
Turn 1:
Parent: "My son Yoni is 3.5 and he's not talking, he doesn't play with kids,
         and he has meltdowns constantly."

Current prompt guidance:
- Extract: concerns = ["speech", "social", "behavioral"]
- Ask follow-up about... which one?
- No clear rule on priority or depth per concern
```

**Questions:**
1. Does the AI know to explore ALL THREE concerns deeply?
2. Does it know how many follow-up questions per concern?
3. Does it know when it has "enough" detail?

**Answer from current prompt**: ❌ **Unclear**

The prompt says:
> "For each challenge mentioned: 1. Ask for specific example, 2. Choose 1-2 clarifying questions, 3. Ask about frequency/intensity, 4. Ask about duration/impact, 5. Ask about previous help"

But it doesn't say:
- Must complete all 5 sub-questions for EACH concern
- How to transition between concerns
- How to know when a concern is "sufficiently explored"

---

### Scenario 2: Drilling into Specifics

```
Turn 10:
Parent: "He has meltdowns all the time."

Current prompt says: "Ask for a specific example"

AI might ask: "Can you give me an example?"
Parent: "Yesterday he screamed when I turned off the TV."

Then what?
```

**The detailed summary needs:**
- When it occurs (times of day, situations)
- Where it occurs (home, school, public)
- With whom (parents, siblings, peers)
- What triggers it (specific triggers)
- What the behavior looks like (screaming? hitting? duration?)
- Parent's response (what do you do?)
- Outcome (how does it end?)
- Frequency (how often?)
- Duration of episodes (minutes? hours?)
- Impact on daily life

**Current prompt guidance**:
> "Choose 1-2 clarifying questions: When/where? With who? What triggers it? How do you respond?"

**Problem**: "Choose 1-2" means 8 questions might NOT be asked!

---

## The Real Question: Backend State Tracking

Looking at the architecture docs, I need to check if the BACKEND tracks coverage...

**From GRAPHITI_INTEGRATION_GUIDE.md:**
- Graphiti builds knowledge graph
- Backend can query: "What do we know about X?"
- Backend calculates completeness %

**So the intended flow might be:**

```python
# Backend tracking (hypothetical)
def get_next_question_guidance(graph, conversation_history):
    coverage = {
        "basic_info": graph.has_all(["name", "age", "gender"]),
        "concerns": {
            "identified": graph.count_entities(type="concern"),
            "detailed_examples": graph.count_entities(type="specific_example"),
            "frequency_known": graph.has_attribute("concern", "frequency"),
            "triggers_known": graph.has_attribute("concern", "triggers")
        },
        "strengths": graph.has_entities(type="strength"),
        "developmental_history": graph.has_info_about("milestones"),
        "family_context": graph.has_info_about("siblings")
    }

    completeness = calculate_completeness(coverage)

    # Generate guidance for next question
    if completeness < 30:
        return "Focus on primary concerns, get specific examples"
    elif completeness < 60:
        return "You have main concerns. Now explore: triggers, frequency, impact"
    elif completeness < 80:
        return "Main concerns covered. Fill gaps: history, environment, family"
    else:
        return "Interview nearly complete. Wrap up gracefully"
```

**But this isn't in the current interview prompt!**

---

## Gap Analysis: What's Missing from Interview Prompt

### ❌ Missing: Explicit Depth Requirements

**Current**: "Choose 1-2 clarifying questions"
**Needed**: "For each concern, you MUST gather:
  1. At least 2 specific examples with full context (when/where/who/trigger/behavior/response/outcome)
  2. Frequency and intensity (offer ranges if parent unsure)
  3. Duration since onset and any changes over time
  4. Impact on child's daily functioning
  5. Impact on parent/family
  6. What parent has tried and how effective it was"

---

### ❌ Missing: Coverage Tracking

**Current**: No mechanism to track which areas have been explored
**Needed**: "Check your memory (via Graphiti query) to see what areas you've covered. Prioritize areas with gaps."

**Example backend query**:
```python
coverage = graphiti.get_coverage_summary(user_id)
# Returns: {"concerns": 85%, "history": 40%, "family": 20%, "environment": 10%}
# AI knows to focus on environment and family next
```

---

### ❌ Missing: Pivot Triggers

**Current**: Vague guidance "follow the parent's lead"
**Needed**: Clear rules:
- "After 3-4 follow-ups on a single concern, check if there are other concerns to explore"
- "If parent gives brief answers repeatedly, pivot to a different area"
- "If parent seems emotionally stuck on one topic, acknowledge and gently pivot"

---

### ❌ Missing: Minimal Viable Coverage

**Current**: Relies on 80% completeness threshold (undefined calculation)
**Needed**: "Interview is complete when you have:
  - ✅ Basic info (name, age, gender)
  - ✅ At least 1-2 primary concerns with detailed examples
  - ✅ 2+ specific behavioral examples per concern
  - ✅ Basic developmental history
  - ✅ Basic family context
  - ✅ Current support/educational setting info
  - ✅ Parent's hopes/goals"

---

## Real-World Test: Would This Happen?

### Realistic Interview Flow with Current Prompt

```
Turn 1: Name/age ✅
Turn 2: "What brings you here?" → "He doesn't talk"
Turn 3: Extract concern=["speech"], ask for example ✅
Turn 4: Parent gives example
Turn 5: AI asks... what?

Option A (Good): "How often does this happen?"
Option B (Good): "Does he understand what you say to him?"
Option C (Miss): "How is he with other kids?" [Pivoted too early]

Let's say AI picks B...
Turn 6: Parent answers about comprehension
Turn 7: AI asks... what?

Option A (Good): "Can you tell me about his play with other children?" [Exploring related area]
Option B (Miss): "How's his sleep?" [Random pivot]
Option C (Good): "How does this affect daily life at home?" [Impact question]
```

**The Problem**: Current prompt gives examples but not a SYSTEMATIC approach.

An experienced human interviewer uses mental frameworks:
1. **Per-concern drill**: Example → Context → Frequency → Impact → History → Response
2. **Breadth check**: "Any other concerns?" before going too deep on one
3. **Coverage map**: Mental checklist of areas to cover
4. **Time management**: Sense of when to pivot vs when to drill

**Current AI prompt**: Has examples, but lacks the framework.

---

## Proposed Solutions

### Solution 1: Add Explicit Navigation Framework to Prompt

```markdown
### Systematic Interview Navigation

#### Phase 1: Concerns Identification (First ~5 turns)
1. Get basic info (name, age, gender)
2. Ask open: "What brings you here?"
3. Listen for ALL concerns mentioned
4. Extract each concern as separate entity
5. Ask: "Is there anything else you're worried about?" to ensure completeness

#### Phase 2: Deep Dive per Concern (~3-5 turns per concern)
For EACH concern identified, follow this sequence:
1. **Specific Example**: "Can you give me a specific example of when this happens?"
2. **Context**: Ask 2-3 of: When? Where? With whom? What triggers it?
3. **Behavior Detail**: "What exactly does [child] do/say?"
4. **Response**: "What do you usually do? What happens after?"
5. **Frequency/Intensity**: "How often?" (offer ranges). "How intense?" (offer scale)
6. **Duration**: "How long has this been going on?" "Any changes recently?"
7. **Impact**: "How does this affect [child's] daily life?" "How does it affect you?"

**Navigation Rule**: Complete ALL 7 sub-questions for primary concerns (2-3 concerns max).
For secondary concerns, ask only 1-3.

#### Phase 3: Developmental Context (~5-8 turns)
After main concerns are explored, gather context:
- Strengths: "Before we focus only on challenges, tell me what [child] loves to do"
- Developmental history: "Any delays in milestones?" "Pregnancy/birth issues?"
- Family: "Siblings?" "Family history of similar issues?"
- Environment: "How's [educational setting]?" "Any support there?"
- Previous help: "Have you tried therapy?" "Any diagnoses?"

**Navigation Rule**: Ask 1-2 questions per area. If parent says "no issues", move on quickly.

#### Phase 4: Wrap-up (~2 turns)
- Parent hopes: "What would you most like to see happen?"
- Natural conclusion
```

---

### Solution 2: Backend-Driven Navigation Prompts

Each turn, backend analyzes graph and adds to system message:

```
[System context for Turn 10]
Current coverage:
- Basic info: ✅ Complete
- Primary concerns: 85% (speech: detailed, social: needs examples)
- History: 40% (missing: medical history, previous treatments)
- Family: 20% (missing: siblings info, family history)

Suggested focus for next 3 turns:
1. Get specific social interaction examples
2. Ask about medical/developmental history
3. Ask about family context

Current completeness: 55%
```

AI reads this and naturally focuses on gaps.

---

### Solution 3: Hybrid (Recommended)

**Interview Prompt**: Add explicit navigation framework (Solution 1)
**Backend**: Track coverage and inject gentle guidance (Solution 2)
**LLM**: Uses both to navigate intelligently

---

## My Assessment: **Navigation IS Too Loose**

The current refactored prompt:
- ✅ Has good content guidelines (what topics to cover)
- ✅ Has good tone guidelines (how to ask)
- ❌ Lacks systematic navigation (when to drill vs when to pivot)
- ❌ Lacks depth requirements (how many follow-ups per concern)
- ❌ Lacks coverage tracking (what's been covered vs what's missing)

**This could lead to:**
- Inconsistent interview depth
- Missing important areas
- Either too shallow OR too deep on random topics
- Completeness calculation being unreliable

**We need to strengthen the navigation framework.**
