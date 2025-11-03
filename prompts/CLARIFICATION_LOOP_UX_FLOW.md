# Video Clarification Loop - User Experience Flow

**Status:** ⚠️ SUPERSEDED by CLARIFICATION_LOOP_CONVERSATIONAL_DESIGN.md
**Note:** This document explored a structured modal approach. Final decision: **Conversational-only design**

**See:** `CLARIFICATION_LOOP_CONVERSATIONAL_DESIGN.md` for the approved conversational approach

**Purpose:** Document the parent-facing experience of the video clarification loop
**Audience:** Product designers, UX developers, implementation team

---

## ⚠️ Design Decision Update

After review, we decided to use a **pure conversational approach** instead of the deep view modal described in this document.

**Reasons:**
- ✅ Maintains design consistency (everything in chat)
- ✅ Simpler mental model for parents
- ✅ No component switching
- ✅ More human and natural
- ✅ Aligned with Chitta's caring, conversational philosophy

**This document is preserved for reference but should NOT be implemented.**

---

---

## Overview

After parent uploads videos and Chitta analyzes them, Chitta may ask **3-7 targeted clarification questions** to better understand the child. This creates a collaborative feedback loop that:
- Shows parent that Chitta is paying attention
- Resolves ambiguities
- Improves accuracy of recommendations
- Builds trust and partnership

---

## When Does This Happen?

**Trigger:** After all (or most) videos have been analyzed and integrated

**Timeline Example:**
- **Monday:** Parent uploads Video 1 → Chitta analyzes
- **Wednesday:** Parent uploads Video 2 → Chitta analyzes
- **Friday:** Parent uploads Video 3 → Chitta analyzes
- **Friday evening:** Chitta integrates all 3 videos
- **Friday night:** Chitta generates clarification questions
- **Saturday morning:** Parent receives notification with questions
- **Saturday:** Parent answers questions at their convenience
- **Saturday evening:** Chitta updates analysis with clarifications
- **Sunday:** Reports are ready for parent

---

## Parent Experience: Step by Step

### Step 1: Notification

**What parent sees:**

```
┌─────────────────────────────────────────────────────┐
│  🔔 Chitta has reviewed your videos!                │
│                                                      │
│  I've analyzed all 3 videos of Yoni and integrated  │
│  them with your interview. I have a few questions   │
│  that will help me give you the most accurate       │
│  guidance possible.                                  │
│                                                      │
│  It should only take 5-10 minutes. Ready?          │
│                                                      │
│  [Yes, let's do it] [Remind me later]              │
└─────────────────────────────────────────────────────┘
```

**Design considerations:**
- Friendly, conversational tone
- Set time expectation (5-10 minutes)
- Allow deferral (respect parent's schedule)
- Emphasize benefit ("most accurate guidance")

---

### Step 2: Question Introduction

**What parent sees:**

```
┌─────────────────────────────────────────────────────┐
│  Great! I have 5 questions about what I observed    │
│  in the videos. Each question will help me better   │
│  understand Yoni's unique patterns.                 │
│                                                      │
│  Progress: ●○○○○ (1 of 5)                           │
│                                                      │
│  [Start]                                            │
└─────────────────────────────────────────────────────┘
```

**Design considerations:**
- Show total number of questions (manage expectations)
- Progress indicator
- Start when parent is ready

---

### Step 3: Individual Questions

Each question follows this structure:
1. **Context** - What Chitta observed
2. **Question** - What Chitta wants to know
3. **Why it matters** - Builds trust, shows purpose

#### **Example Question 1: Discrepancy Resolution**

```
┌─────────────────────────────────────────────────────┐
│  Progress: ●●○○○ (2 of 5)                           │
│                                                      │
│  📹 In the interview, you mentioned that Yoni       │
│     "never looks at me when I talk to him."         │
│                                                      │
│  👀 But in the home play video, I noticed Yoni      │
│     made eye contact with you several times and     │
│     even initiated eye contact to show you          │
│     something he was excited about.                 │
│                                                      │
│  ❓ Can you help me understand when eye contact is  │
│     easier vs. harder for Yoni?                     │
│                                                      │
│  For example, does it vary by:                      │
│  • Who he's with (family vs. strangers)?            │
│  • The activity (play vs. conversation)?            │
│  • His emotional state?                             │
│                                                      │
│  ┌─────────────────────────────────────────────┐   │
│  │  [Your answer here...]                       │   │
│  │                                              │   │
│  │                                              │   │
│  └─────────────────────────────────────────────┘   │
│                                                      │
│  💡 Why this matters: Understanding when eye        │
│     contact works vs. doesn't helps us identify     │
│     what supports Yoni and what makes it harder.    │
│                                                      │
│  [Skip this question] [Next]                        │
└─────────────────────────────────────────────────────┘
```

**Design elements:**
- **Icons** for visual structure (📹 = observation, 👀 = what Chitta saw, ❓ = question, 💡 = why it matters)
- **Non-judgmental framing:** "Help me understand" not "You said X but..."
- **Specific examples** from video (builds credibility)
- **Clear answer format** (open text box)
- **Skip option** (respect parent's autonomy)
- **Why it matters** section (builds investment)

---

#### **Example Question 2: New Finding Confirmation**

```
┌─────────────────────────────────────────────────────┐
│  Progress: ●●●○○ (3 of 5)                           │
│                                                      │
│  📹 In Video 2 (playground), I noticed something    │
│     that wasn't discussed in our interview.         │
│                                                      │
│  👂 Yoni covered his ears with his hands several    │
│     times when there was background noise (kids     │
│     shouting, playground equipment sounds).         │
│                                                      │
│     [See video clip 📺]                             │
│                                                      │
│  ❓ Have you noticed this pattern at other times?   │
│                                                      │
│  ○ Yes, I see this often                            │
│  ○ Yes, occasionally                                │
│  ○ No, that was unusual                             │
│  ○ I'm not sure / haven't noticed                   │
│                                                      │
│  ┌─────────────────────────────────────────────┐   │
│  │  If yes, can you describe when this happens?│   │
│  │  (sounds, places, situations)                │   │
│  │                                              │   │
│  └─────────────────────────────────────────────┘   │
│                                                      │
│  💡 Why this matters: Sensory sensitivities can     │
│     affect comfort in social situations and help    │
│     us recommend appropriate supports.              │
│                                                      │
│  [Skip] [Next]                                      │
└─────────────────────────────────────────────────────┘
```

**Design elements:**
- **Video clip reference** (let parent review the moment)
- **Multiple choice + elaboration** (easier than pure open text)
- **"I'm not sure" option** (validates uncertainty)
- **Conditional follow-up** (appears if parent says "yes")

---

#### **Example Question 3: Pervasiveness Assessment**

```
┌─────────────────────────────────────────────────────┐
│  Progress: ●●●●○ (4 of 5)                           │
│                                                      │
│  📹 In the playground video, I observed that Yoni   │
│     played alone for most of the time and didn't    │
│     approach other children, even when they were    │
│     nearby playing.                                 │
│                                                      │
│  🤔 This matches what you shared in the interview   │
│     about preschool. I want to understand the       │
│     full picture.                                   │
│                                                      │
│  ❓ Does this pattern happen:                       │
│                                                      │
│  • With familiar children (cousins, neighbors)?     │
│    ○ Always  ○ Sometimes  ○ Rarely  ○ Never         │
│                                                      │
│  • In structured activities (class, organized       │
│    playgroups)?                                     │
│    ○ Always  ○ Sometimes  ○ Rarely  ○ Never         │
│                                                      │
│  • At birthday parties or family gatherings?        │
│    ○ Always  ○ Sometimes  ○ Rarely  ○ Never         │
│                                                      │
│  ┌─────────────────────────────────────────────┐   │
│  │  Any additional observations about Yoni's    │   │
│  │  peer interactions? (optional)               │   │
│  └─────────────────────────────────────────────┘   │
│                                                      │
│  💡 Why this matters: Understanding whether this    │
│     happens everywhere or in specific situations    │
│     helps us tailor our guidance to Yoni's needs.   │
│                                                      │
│  [Skip] [Next]                                      │
└─────────────────────────────────────────────────────┘
```

**Design elements:**
- **Matrix question format** (multiple contexts, single behavior)
- **Rating scale** (Always/Sometimes/Rarely/Never)
- **Optional elaboration** (for parents who want to add more)
- **Acknowledges confirmation** ("This matches what you shared")

---

#### **Example Question 4: Context/Frequency**

```
┌─────────────────────────────────────────────────────┐
│  Progress: ●●●●● (5 of 5) - Last one!               │
│                                                      │
│  📹 In the puzzle video, Yoni worked on the puzzle  │
│     for 6 minutes with good focus, asked for help   │
│     when stuck, and stayed calm even when it was    │
│     challenging. I was impressed!                   │
│                                                      │
│  ❓ To understand if this represents his typical    │
│     attention:                                      │
│                                                      │
│  1. Would you say what you saw in the video is:    │
│     ○ Better than usual (he had a great day)        │
│     ○ Typical for him                               │
│     ○ Worse than usual (he was having a hard day)   │
│                                                      │
│  2. How does he do with challenging tasks in        │
│     general (homework, learning new skills)?        │
│                                                      │
│  ┌─────────────────────────────────────────────┐   │
│  │  [Your answer here...]                       │   │
│  │                                              │   │
│  └─────────────────────────────────────────────┘   │
│                                                      │
│  💡 Why this matters: Knowing if the video captured │
│     his typical ability helps us understand his     │
│     true attention patterns and strengths.          │
│                                                      │
│  [Skip] [Finish]                                    │
└─────────────────────────────────────────────────────┘
```

**Design elements:**
- **Celebrates progress** ("Last one!")
- **Starts with positive observation** ("I was impressed!")
- **Calibration question** (was this typical?)
- **Finish button** (instead of "Next")

---

### Step 4: Completion & Thank You

```
┌─────────────────────────────────────────────────────┐
│  ✅ Thank you!                                      │
│                                                      │
│  Your answers are incredibly helpful. I now have    │
│  a much clearer picture of Yoni's unique strengths  │
│  and challenges.                                     │
│                                                      │
│  I'm updating my analysis with this new             │
│  information...                                     │
│                                                      │
│  ⏱️ Your personalized reports will be ready in     │
│     about 10-15 minutes. I'll notify you when       │
│     they're done.                                   │
│                                                      │
│  [View my videos] [Return to dashboard]            │
└─────────────────────────────────────────────────────┘
```

**Design considerations:**
- **Gratitude** (parent invested time)
- **Value affirmation** ("incredibly helpful")
- **Set expectation** (reports ready in 10-15 min)
- **Give parent something to do** while waiting

---

### Step 5: Updated Analysis Complete

```
┌─────────────────────────────────────────────────────┐
│  🎉 Your personalized reports are ready!           │
│                                                      │
│  Thanks to your clarifications, I have a much more  │
│  complete understanding of Yoni. Your insights      │
│  helped me:                                         │
│                                                      │
│  ✓ Understand when eye contact is easier vs.       │
│    harder for him                                   │
│  ✓ Recognize his sensory sensitivities              │
│  ✓ Confirm patterns across different settings       │
│  ✓ Appreciate his strong puzzle-solving skills      │
│                                                      │
│  [Read Parent Guide] [View Professional Report]    │
└─────────────────────────────────────────────────────┘
```

**Design considerations:**
- **Show value of clarifications** (specific examples)
- **Preview key insights** (builds anticipation)
- **Call to action** (read reports)

---

## Design Principles

### 1. **Conversational Tone**
- Use "I" and "you" (Chitta and parent relationship)
- Avoid clinical jargon
- Friendly, warm, empathetic

### 2. **Transparency**
- Show what Chitta observed (with timestamps/clips)
- Explain why each question matters
- Show progress (X of Y questions)

### 3. **Respect Parent's Time**
- Keep to 3-7 questions max
- Allow skip/defer options
- Set time expectations upfront

### 4. **Non-Judgmental**
- Frame discrepancies as "help me understand" not "you were wrong"
- Validate parent's observations
- Celebrate child's strengths

### 5. **Visual Structure**
- Use icons for sections (📹 👀 ❓ 💡)
- Progress indicators
- Clear answer formats (text boxes, multiple choice, ratings)

### 6. **Mobile-Friendly**
- Parents often use phones
- Large tap targets
- Short questions per screen
- Save progress (can come back later)

---

## Question Type Templates

### Template 1: Discrepancy Resolution

```
[Context Icon] In the interview, you mentioned [parent statement].
[Observation Icon] In the video, I observed [what video showed].
[Question Icon] Can you help me understand [specific clarification]?
[Value Icon] Why this matters: [clinical significance in plain language]
```

### Template 2: New Finding

```
[Context Icon] In Video X, I noticed [behavior].
[Question Icon] Have you seen this at other times?
○ Options
[Follow-up box if yes]
[Value Icon] Why this matters: [clinical significance]
```

### Template 3: Pervasiveness

```
[Context Icon] In the video, I observed [behavior].
[Question Icon] Does this happen in [context A, B, C]?
[Rating scales or checkboxes]
[Optional elaboration]
[Value Icon] Why this matters: [clinical significance]
```

### Template 4: Frequency/Context

```
[Context Icon] In the video, I saw [behavior].
[Question Icon] Is what we saw:
○ Typical
○ Better than usual
○ Worse than usual
[Follow-up]: Describe typical [behavior] pattern
[Value Icon] Why this matters: [clinical significance]
```

---

## Technical Implementation Notes

### State Management

```javascript
{
  clarificationSession: {
    sessionId: "CQ_XXX",
    childId: "CHILD_123",
    totalQuestions: 5,
    currentQuestion: 2,
    answers: [
      { questionId: "CQ_001", answer: "...", answeredAt: "..." },
      // ...
    ],
    status: "in_progress" | "completed" | "deferred",
    canResume: true
  }
}
```

### Question Rendering

```javascript
function renderQuestion(question) {
  return {
    context: renderContext(question.observation_reference),
    questionText: question.question_text_for_parent,
    answerWidget: getWidgetForType(question.expected_answer_type),
    whyItMatters: question.why_this_matters_clinically_plain_language,
    videoClip: question.observation_reference.timestamp ?
      getVideoClip(question.observation_reference.video_id,
                   question.observation_reference.timestamp) : null
  };
}
```

### Progress Saving

- Auto-save each answer
- Allow parent to exit and resume
- Send reminder if not completed within 24 hours
- Don't block report generation indefinitely (skip after 48 hours?)

---

## Edge Cases & Handling

### Case 1: Parent Skips All Questions

**What to do:**
- Proceed with original integration analysis
- Note in metadata: "Clarification offered, parent declined"
- Don't penalize or make parent feel bad
- Reports generated without clarifications

---

### Case 2: Parent Gives Contradictory Answers

**What to do:**
- Don't try to "catch" contradictions in real-time
- Let clarification integration prompt handle interpretation
- May flag for follow-up in consultation

---

### Case 3: Parent Asks Chitta Questions

**What to do:**
- Acknowledge: "Great question! Let me finish gathering info first"
- Defer to report discussion phase
- Capture question for follow-up

---

### Case 4: Parent Gets Emotional/Overwhelmed

**Indicators:**
- Very long, emotional answers
- Signs of distress in text

**What to do:**
- After completion, offer: "I sense this is a lot. Would you like to schedule a time to talk through the findings together?"
- Ensure empathetic, supportive language in reports
- Flag for human clinician review if available

---

## Accessibility Considerations

### Language
- Offer questions in parent's preferred language (Hebrew, English, Arabic, Russian, etc.)
- Use simple, clear language (avoid jargon)

### Literacy
- Provide audio option (Chitta reads questions)
- Voice input for answers

### Visual Impairment
- Screen reader compatible
- High contrast mode
- Large text option

### Attention/Cognitive
- One question per screen (not overwhelming)
- Clear progress indicator
- Ability to save and resume

---

## Success Metrics

### Quantitative
- **Completion rate:** % of parents who complete clarification questions
- **Time to complete:** Median time from start to finish
- **Skip rate:** % of questions skipped
- **Answer quality:** Length and informativeness of answers

### Qualitative
- **Parent feedback:** Post-completion survey
  - "Was this helpful?"
  - "Did you feel heard?"
  - "Were questions clear?"
- **Clinical value:** Do clarifications meaningfully improve analysis? (analyst review)

---

## Future Enhancements

### 1. **Adaptive Questioning**
- If parent's answer reveals new concern, ask targeted follow-up
- Dynamic question generation based on previous answers

### 2. **Video Highlighting**
- Show parent exactly what Chitta saw (highlight child in frame, timestamp)
- Side-by-side: video clip + question

### 3. **Collaborative Viewing**
- Parent and Chitta watch video together
- Chitta asks questions in real-time as video plays

### 4. **Parent-Initiated Clarifications**
- Let parent flag moments in videos they want to explain
- "I want to tell you what was happening here..."

---

## Example Full Session (Parent's Perspective)

**Sarah's Experience:**

**10:00 AM - Notification:**
"Chitta has reviewed your videos!"
*Sarah clicks: "Yes, let's do it"*

**10:01 AM - Question 1:**
Chitta asks about eye contact discrepancy.
Sarah types: "Oh, eye contact is fine when we're playing, but when I'm trying to teach him something or talk seriously, he looks away. I guess I focused on the hard parts in the interview."
*Sarah feels understood - Chitta isn't saying she was wrong*

**10:03 AM - Question 2:**
Chitta asks about ear covering.
Sarah selects: "Yes, I see this often"
Describes: "Vacuum cleaner, hand dryers, music at parties. He hates loud sounds."
*Sarah realizes: "I thought that was just pickiness, but maybe it's bigger?"*

**10:06 AM - Question 3:**
Chitta asks about peer interaction across contexts.
Sarah checks boxes: Always alone with unfamiliar kids, Sometimes alone with cousins, Rarely alone in structured activities.
*Sarah starts seeing patterns she hadn't noticed before*

**10:10 AM - Question 4:**
Chitta asks if puzzle video was typical attention.
Sarah selects: "Better than usual"
Explains: "Puzzles are his favorite. With homework or anything he doesn't like, he's up every 30 seconds."
*Sarah appreciates that Chitta wants to know the full picture*

**10:13 AM - Question 5:**
Chitta asks about sensory issues with other senses.
Sarah describes: "Now that you mention it, he refuses certain clothes, is very picky about food textures..."
*Sarah is starting to connect dots*

**10:15 AM - Complete:**
"Thank you! Reports ready in 10-15 minutes."
*Sarah feels heard, collaborative, hopeful*

**10:28 AM - Reports Ready:**
"Your clarifications helped me understand when eye contact works vs. doesn't, his sensory sensitivities, patterns across settings, and his puzzle strengths!"
*Sarah feels validated - her input mattered*

**Result:** Reports are more accurate. Sarah feels like a partner, not a data source. Recommendations are tailored to Yoni's specific patterns.

---

**The clarification loop transforms video analysis from "here's what we found" to "let's understand your child together."**
