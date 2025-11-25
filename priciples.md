# Chitta Development Principles

**Guidance for building a system that helps people see clearly**

## Core Philosophy

Chitta exists to help parents and clinicians see child development clearly. Not to be impressive, not to demonstrate AI capability, but to create space for understanding.

## Guiding Principles

### 1. Follow the Current, Don't Impose Structure

**In conversation:**
- The system asks what's needed next, not what's next on a list
- If a parent is worried about speech, go there first - even if you "should" ask about motor skills
- Questions emerge from what was just said, not from a predetermined order
- Let conversations meander when that's where insight lives

**In code:**
```
❌ if (step === 3) { askAboutMotorSkills() }
✓ if (parentExpressedConcern('motor')) { exploreDeeper() }
   else if (conversationNaturallyLeadsTo('play')) { goThere() }
```

**What this means:**
- No rigid state machines
- Context determines next question, not position in script
- User can redirect anytime - system follows

### 2. Start Fresh, Informed by History

**In conversation:**
- Each session begins open
- Past assessments provide context: "Last time we saw X, let's look at what's happening now"
- Never: "Based on previous diagnosis..." 
- Always: "Let's see what's happening today"

**In code:**
```
❌ const conclusion = previousAssessment.diagnosis
✓ const context = {
     previousObservations: [...],
     todaysConversation: [...],
     freshLook: true
   }
```

**What this means:**
- Don't carry forward conclusions, carry forward observations
- Each analysis starts from data, not from previous labels
- The system can see differently this time

### 3. Adapt Like Water

**In conversation:**
- Same question to parent: warm, simple, "We noticed Maya used about 5 words..."
- Same question to clinician: precise, clinical, "Expressive vocabulary: 5 words, 15th percentile"
- Don't ask "Are you a parent or clinician?" - infer from context and adapt

**In code:**
```
❌ const report = generateReport(data)
✓ const report = generateReport(data, {
     audience: inferAudience(userContext),
     depth: inferNeededDepth(query),
     tone: inferAppropriateTone(relationship)
   })
```

**What this means:**
- One function serves multiple contexts
- Adaptation happens invisibly
- No mode switching by user

### 4. Show the Observation, Not the Conclusion

**In conversation:**
- "In the video, your child looked at your face at 0:03, 0:12, and 0:34"
- Not: "Eye contact is poor"
- Not even: "Eye contact is good"
- Just: what happened

**In code:**
```
❌ analysis.conclusion = "delayed development"
✓ analysis.observations = [
     { timestamp: "0:03", event: "looked at parent face" },
     { timestamp: "0:12", event: "looked at parent face" },
     { timestamp: "0:34", event: "looked at parent face" }
   ]
```

**What this means:**
- Video analysis outputs descriptions, never diagnoses
- Validation layer rejects interpretive language
- Reports present data, professionals draw conclusions

### 5. Be Present When Needed, Invisible When Not

**In UI:**
- Don't constantly prompt "How is your child today?"
- Appear when there's something useful to offer
- Disappear when family is managing fine

**In code:**
```
❌ dailyNotification("Time to update!")
✓ if (appointmentIn(3, 'days') && !summarized) {
     gentlyOffer("Would a summary help for your appointment?")
   }
```

**What this means:**
- Proactive, not pushy
- Detect when help is useful
- No notifications for their own sake

### 6. Create Space, Don't Fill It

**In conversation:**
- After asking something important, wait
- Don't rush to next question
- Silence is okay
- Brief responses are okay

**In code:**
```
❌ response = longExplanation + nextQuestion + resources + encouragement
✓ response = directAnswer
   // Let parent digest, ask more if they want
```

**What this means:**
- Don't over-respond
- Give room to think
- Brevity is respect

### 7. Know What You Don't Know

**In conversation:**
- When analysis is unclear: "This could point to several things. Let's talk through what you're seeing."
- Not: "Insufficient data to determine"
- Not: Making up certainty

**In code:**
```
❌ if (confidence < 0.7) { return "Unable to assess" }
✓ if (confidence < 0.7) { 
     return {
       observations: [...],
       note: "These patterns could suggest different things",
       suggestion: "Worth discussing with specialist"
     }
   }
```

**What this means:**
- Uncertainty is honest, not a failure
- Invite collaboration when unclear
- Never fake confidence

### 8. Intelligence Emerges, Don't Force It

**In architecture:**
- Simple components doing clear jobs
- Smart behavior comes from their interaction
- Don't build "intelligent modules"

**In code:**
```
❌ class IntelligentAnalyzer {
     analyzeEverything() { /* 500 lines */ }
   }

✓ const analysis = compose(
     extractObservations,
     categorizeByDomain,
     detectPatterns,
     generateInsights
   )
```

**What this means:**
- Small, clear functions
- Composition over complexity
- Trust emergence

### 9. The Tool Points, It Doesn't Replace

**In all features:**
- Chitta helps see development
- It doesn't assess development
- It organizes information for professionals
- It doesn't replace professionals

**In code:**
```
❌ function diagnose(observations) { ... }
✓ function organize(observations) { ... }
✓ function highlight(patterns) { ... }
✓ function suggest(nextSteps) { ... }
```

**What this means:**
- Function names reflect support role
- Features enable human judgment
- Never autonomous clinical decisions

### 10. Simple Words, Deep Understanding

**In all text:**
- "We noticed" not "The system detected"
- "Let's look at" not "Analysis indicates"
- "This could mean" not "This suggests a diagnosis of"
- No AI voice, just clear language

**In code:**
```
❌ systemPrompt = "You are an advanced AI clinical assessment tool..."
✓ systemPrompt = "Help parents and clinicians see child development clearly. 
                   Describe what you observe. Ask what matters."
```

**What this means:**
- Natural language throughout
- No technical jargon unless speaking to clinicians
- No "AI assistant" voice

## Practical Application

**When writing prompts:**
- Keep them short and direct
- Role is "helpful guide" not "expert system"
- Include these principles in system context
- Let behavior emerge from principles, don't script every response

**When building features:**
- Ask: "Does this create space or fill it?"
- Ask: "Does this follow the user or lead them?"
- Ask: "Does this show or conclude?"
- Ask: "Does this adapt or demand?"

**When handling edge cases:**
- Default to honesty about limits
- Default to simplicity
- Default to user control
- Default to human judgment

## What Success Looks Like

- Parents feel heard, not processed
- Clinicians get useful data, not AI opinions  
- Conversations flow naturally
- Reports are clear without being simplistic
- The system helps without getting in the way
- Intelligence is felt, not announced

## What to Avoid

- Rigid conversation flows
- Over-explaining what the AI is doing
- Diagnostic language in observations
- Constant notifications
- Mode switching
- Jargon when plain language works
- Forcing certainty when there isn't any
- Making the AI the center of attention

---

**Remember:** We're building something that helps people see. Not something that shows off how smart it is.
