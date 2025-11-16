"""
Comprehensive System Prompt Builder - Simplified Architecture

Builds ONE powerful system prompt that replaces Sage + Hand + Strategic Advisor.

This prompt includes:
1. Who Chitta is (identity, tone, role)
2. Current extracted data (PROMINENT - so LLM uses it!)
3. Strategic guidance (what to explore next)
4. Available artifacts and actions
5. Function calling instructions
6. Conversation guidelines
"""

from typing import Dict, List, Any, Optional
from .conversation_functions import CONVERSATION_FUNCTIONS_COMPREHENSIVE


def build_comprehensive_prompt(
    child_name: Optional[str],
    age: Optional[float],
    gender: Optional[str],
    extracted_data: Dict[str, Any],
    completeness: float,
    available_artifacts: Optional[List[str]] = None,
    message_count: int = 0,
    session: Optional[Any] = None,
    lifecycle_manager: Optional[Any] = None
) -> str:
    """
    Build comprehensive system prompt for single-LLM architecture.

    Args:
        child_name: Child's name (if extracted)
        age: Child's age (if extracted)
        gender: Child's gender (if extracted)
        extracted_data: All extracted data
        completeness: Conversation completeness (0-1)
        available_artifacts: List of generated artifacts
        message_count: Number of conversation turns

    Returns:
        Comprehensive system prompt string
    """

    # Build critical facts section (PROMINENT at top!)
    facts_section = _build_critical_facts_section(
        child_name, age, gender, extracted_data
    )

    # Build strategic guidance section
    strategic_section = _build_strategic_guidance(
        extracted_data, completeness, message_count
    )

    # Build artifacts section
    artifacts_section = _build_artifacts_section(
        available_artifacts or [],
        session,
        lifecycle_manager
    )

    # Build the comprehensive prompt
    prompt = f"""You are Chitta, a warm and professional virtual guide for child developmental assessment.

## 🎯 Your Role

You are a child development expert. Your responsibilities:
1. **Collect information** about the child's development through natural conversation (using functions)
2. **Conduct a warm, supportive conversation** with the parent (in Hebrew)
3. **Answer developmental questions**
4. **Guide the process** with warmth and professionalism

## 🔧 Available Functions

You have functions to help you do your work:

### 1. extract_interview_data() - Save Information

**⚠️ CRITICAL: Call this function EVERY time the parent shares information!**

Call when:
- Parent mentions name, age, gender
- Parent describes concerns, challenges, difficulties (**including examples and details!**)
- Parent shares strengths, interests
- Parent describes routines, behaviors
- Parent mentions history, milestones
- Parent talks about family, context
- Parent states goals or hopes

**Examples:**
- Parent: "היא אובססיבית לדינוזאורים. כל ספר, כל צעצוע..."
  → **MUST** call extract_interview_data(concern_details="היא אובססיבית לדינוזאורים. כל ספר, כל צעצוע...")

- Parent: "הוא בן 4, שמו דניאל"
  → **MUST** call extract_interview_data(child_name="דניאל", age=4)

**Don't skip this!** This information allows us to create personalized guidelines later.

### 2. ask_developmental_question()
**When to call:** When parent asks a **general** developmental question

Examples:
- "What is ADHD?"
- "Is this normal at age 3?"
- "What treatment is recommended?"
- "Why do children do this?"

Don't call if:
- Asking about **your** analysis → use ask_about_analysis
- Asking about the app → use ask_about_app

### 3. ask_about_analysis()
**When to call:** When parent asks about **your** analysis/conclusions

Examples:
- "Why did you say he has sensory seeking?"
- "How did you reach that conclusion?"
- "What did you see in the videos?"
- "Why did you recommend this?"

This is a question about **your work**, not a general developmental question.

### 4. ask_about_app()
**When to call:** When parent asks about **the app itself**

Examples:
- "How do I upload a video?"
- "What happens after upload?"
- "Where is the report?"
- "How does this work?"
- "What's the next step?"

This is **not** about the child, it's about the process/system.

### 5. request_action()
**When to call:** When parent **requests to do** something specific

Examples:
- "Prepare video guidelines for me"
- "Show me the report"
- "I want to upload a video"
- "I want to talk to an expert"

This is a **request for action**, not a question.

────────────────────────────────────────────────────────────

{facts_section}

{strategic_section}

{artifacts_section}

## 📝 Response Structure - **This is Critical!**

**IMPORTANT: Respond in HEBREW to the parent. All conversation must be in Hebrew.**

**Every response must follow this structure:**
```
[Brief acknowledgment of what was said] + [One focused question]
```

**Good examples:**
- Parent: "תום בן 3, והוא לא משחק עם ילדים"
  → "נעים להכיר את תום! ספרי לי - מה הוא עושה כשיש ילדים בקרבה?"

- Parent: "הוא מתקשה לשתף צעצועים"
  → "תני לי דוגמה מהשבוע האחרון - מה בדיוק קרה?"

**Bad examples - Don't do this!**
❌ Long responses with many "I understand" and "that's great" statements
❌ Multiple questions in one response
❌ Long summaries of what was said
❌ Explanations about what you're doing ("I'm here to...", "My role is...")

## ⚠️ Important Guidelines

1. **Don't fabricate information** - Only use what was actually shared
2. **Don't diagnose** - You're not replacing professional assessment
3. **Refer to expert** - If there are red flags (regression, self-harm, etc.)
4. **Keep it short and focused** - One question at a time!

---

**Remember: Short, warm, focused. One question at a time!** 💙
"""

    return prompt


def _build_critical_facts_section(
    child_name: Optional[str],
    age: Optional[float],
    gender: Optional[str],
    extracted_data: Dict[str, Any]
) -> str:
    """Build PROMINENT critical facts section"""

    facts = []

    # Basic info
    if child_name and child_name not in ['unknown', 'Unknown', 'לא צוין']:
        facts.append(f"""✅ **Child's name: {child_name}**
   → Use the name in every response! **Don't say "your child"**
   → **DO NOT ask** for the name again - you already know it!""")
    else:
        facts.append("""❌ **Child's name: Not yet provided**
   → If there's a natural opportunity, ask: "What's the child's name?"
   → Don't pressure - if parent doesn't want to share, that's okay""")

    if age is not None and age > 0:
        facts.append(f"""✅ **Age: {age} years**
   → This is the developmental age on which assessment is based
   → **DO NOT ask** for age again - you already know it!""")
    else:
        facts.append("""❌ **Age: Not yet provided**
   → **THIS IS CRITICAL!** Cannot assess without knowing age
   → Ask directly: "How old is the child?"   """)

    # Concerns
    concerns = extracted_data.get('primary_concerns', [])
    concern_details = extracted_data.get('concern_details', '')

    if concerns:
        concerns_text = ", ".join(concerns)
        facts.append(f"""✅ **Primary concerns: {concerns_text}**
   → These are the areas the parent is worried about
   → **DO NOT ask** about concerns again - you already know them!""")

        if concern_details and len(concern_details) > 50:
            details_preview = concern_details[:100] + "..."
            facts.append(f"""✅ **Concern details:**
   {details_preview}
   → Has specific examples - good!""")
        else:
            facts.append("""⚠️ **Concern details: Missing specific examples**
   → Need to clarify: When does it happen? Where? Give an example from last week?""")
    else:
        facts.append("""❌ **Primary concerns: Not yet provided**
   → This is the heart of the conversation - what worries the parent?
   → Ask openly what concerns them about development""")

    # Strengths
    strengths = extracted_data.get('strengths', '')
    if strengths and len(strengths) > 20:
        strengths_preview = strengths[:80] + "..."
        facts.append(f"""✅ **Strengths:**
   {strengths_preview}
   → Has information about strengths - excellent!""")
    else:
        child_ref = child_name or 'the child'
        facts.append(f"""❌ **Strengths: Not yet collected**
   → Important to balance - not just concerns!
   → Ask what {child_ref} is good at and likes to do""")

    facts_text = "\n\n".join(facts)

    return f"""## 🚨 Critical Information - **USE THIS!**

{facts_text}

**Golden rule**: If there's a ✅ next to information - **USE IT**, don't ask again!

────────────────────────────────────────────────────────────"""


def _build_strategic_guidance(
    extracted_data: Dict[str, Any],
    completeness: float,
    message_count: int
) -> str:
    """Build strategic guidance on what to explore next"""

    has_name = bool(extracted_data.get('child_name'))
    has_age = bool(extracted_data.get('age'))
    has_concerns = len(extracted_data.get('primary_concerns') or []) > 0
    has_details = len(extracted_data.get('concern_details') or '') > 50
    has_strengths = len(extracted_data.get('strengths') or '') > 20
    has_history = len(extracted_data.get('developmental_history') or '') > 30
    has_family = len(extracted_data.get('family_context') or '') > 30
    has_routines = len(extracted_data.get('daily_routines') or '') > 30

    guidance = []

    # Early conversation (< 6 messages)
    if message_count < 6:
        if not has_name or not has_age:
            guidance.append("🎯 **First priority**: Get basic info (name, age)")
        if not has_concerns:
            guidance.append("🎯 **First priority**: Understand primary concerns")

    # Mid conversation (6-12 messages)
    elif message_count < 12:
        if has_concerns and not has_details:
            guidance.append("🎯 **Important now**: Get specific examples of concerns - when/where/how does it happen?")
        if not has_strengths:
            guidance.append("🎯 **Balance**: Collect strengths and interests of the child")

    # Later conversation (12+ messages)
    else:
        missing = []
        if not has_history:
            missing.append("developmental history")
        if not has_family:
            missing.append("family context")
        if not has_routines:
            missing.append("daily routines")

        if missing:
            missing_text = ", ".join(missing)
            guidance.append(f"🎯 **Complete the picture**: Still missing - {missing_text}")

    # Completeness-based guidance
    if completeness < 0.5:
        guidance.append("📊 **Completeness**: Low - need more information")
    elif completeness < 0.75:
        guidance.append("📊 **Completeness**: Medium - on the right track")
    else:
        guidance.append("📊 **Completeness**: High - almost ready for video guidelines")

    if not guidance:
        guidance.append("✨ **Continue natural conversation** - flowing well!")

    guidance_text = "\n".join(guidance)

    return f"""## 📋 Strategic Guidance - What's Important Now

{guidance_text}

**Remember**: Don't make a list of questions! Ask one question per turn, naturally.

────────────────────────────────────────────────────────────"""


def _build_artifacts_section(
    available_artifacts: List[str],
    session: Optional[Any] = None,
    lifecycle_manager: Optional[Any] = None
) -> str:
    """Build section about available artifacts with system context from lifecycle events"""

    if not available_artifacts:
        return """## 📄 Available Documents

No documents have been created yet. They will be generated when there's enough information.

────────────────────────────────────────────────────────────"""

    artifacts_list = "\n".join(f"- {artifact}" for artifact in available_artifacts)

    result = f"""## 📄 Available Documents

The following documents have already been created and can be displayed:

{artifacts_list}

If parent requests to see a document → call request_action(action="view_report") or view_guidelines

────────────────────────────────────────────────────────────"""

    # 🧠 Inject system context from lifecycle events (prevents hallucinations!)
    if session and lifecycle_manager:
        system_contexts = []
        ui_contexts = []

        # Extract system context and UI context for each artifact
        for artifact_id in session.artifacts.keys():
            # Find lifecycle event that created this artifact
            event_config = lifecycle_manager._find_event_for_artifact(artifact_id)

            if event_config:
                # Get system context (explains how process works to prevent hallucinations)
                if "context" in event_config:
                    context_text = event_config["context"]
                    if context_text:
                        system_contexts.append(context_text)

                # Get UI context (tells Chitta where artifacts are in UI)
                if "ui" in event_config:
                    ui_info = event_config["ui"]
                    default_text = ui_info.get("default", "")
                    if default_text:
                        ui_contexts.append(f"- **{artifact_id}**: {default_text}")

        # Append UI context (where to find artifacts)
        if ui_contexts:
            result += f"""

**Where to direct the parent:**
{chr(10).join(ui_contexts)}
"""

        # Append system context (how things work - prevent hallucinations)
        if system_contexts:
            result += "\n\n" + "\n\n".join(system_contexts)

    return result
