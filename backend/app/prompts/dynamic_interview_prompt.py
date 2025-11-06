"""
Dynamic Interview System - Natural Flow with Strategic Awareness

Instead of rigid stages, this system:
1. Analyzes what's been covered and what needs attention
2. Provides subtle strategic awareness (not commands!)
3. Lets LLM conduct natural, flowing conversation
4. Ensures comprehensive coverage without being robotic
"""

from typing import Dict, Any, List, Optional, Tuple


def analyze_interview_coverage(
    extracted_data: Dict[str, Any],
    completeness: float
) -> Dict[str, Any]:
    """
    Analyze interview coverage and depth

    Returns what's covered, what's missing, and what needs more depth
    NOT prescriptive commands, just awareness
    """
    coverage = {
        "covered_well": [],
        "needs_more_depth": [],
        "not_yet_explored": [],
        "overall_depth": "shallow" if completeness < 0.30 else "moderate" if completeness < 0.70 else "good"
    }

    # Basic info
    if extracted_data.get('child_name') and extracted_data.get('age'):
        coverage["covered_well"].append("basic info")
    elif extracted_data.get('age'):
        coverage["needs_more_depth"].append("child's name (if parent comfortable sharing)")
    else:
        coverage["not_yet_explored"].append("basic info")

    # Strengths
    strengths_length = len(extracted_data.get('strengths', '') or '')
    if strengths_length > 50:
        coverage["covered_well"].append("child's strengths")
    elif strengths_length > 0:
        coverage["needs_more_depth"].append("child's strengths")
    else:
        coverage["not_yet_explored"].append("what child enjoys")

    # Concerns - THIS IS THE CORE
    concerns = extracted_data.get('primary_concerns', []) or []
    details_length = len(extracted_data.get('concern_details', '') or '')

    if concerns and details_length > 300:
        coverage["covered_well"].append("concerns with rich examples")
    elif concerns and details_length > 100:
        coverage["needs_more_depth"].append("concern details (examples, situations, impact)")
    elif concerns:
        coverage["needs_more_depth"].append("concerns (need specific examples and context)")
    else:
        coverage["not_yet_explored"].append("what brought parent here")

    # Developmental history
    history_length = len(extracted_data.get('developmental_history', '') or '')
    if history_length > 50:
        coverage["covered_well"].append("developmental history")
    elif history_length > 0:
        coverage["needs_more_depth"].append("developmental history")
    else:
        coverage["not_yet_explored"].append("developmental background")

    # Family context
    family_length = len(extracted_data.get('family_context', '') or '')
    if family_length > 50:
        coverage["covered_well"].append("family context")
    elif family_length > 0:
        coverage["needs_more_depth"].append("family context")
    else:
        coverage["not_yet_explored"].append("family situation")

    # Daily routines
    routines_length = len(extracted_data.get('daily_routines', '') or '')
    if routines_length > 50:
        coverage["covered_well"].append("daily routines")
    elif routines_length > 0:
        coverage["needs_more_depth"].append("daily routines")
    else:
        coverage["not_yet_explored"].append("typical day")

    # Parent goals
    goals_length = len(extracted_data.get('parent_goals', '') or '')
    if goals_length > 30:
        coverage["covered_well"].append("parent's goals")
    elif goals_length > 0:
        coverage["needs_more_depth"].append("parent's goals")
    else:
        coverage["not_yet_explored"].append("what parent hopes will improve")

    return coverage


def generate_strategic_awareness(
    coverage: Dict[str, Any],
    completeness: float,
    concerns: List[str]
) -> str:
    """
    Generate subtle strategic hints - NOT commands!

    This is awareness, not a script to follow
    """
    if completeness < 0.15:
        # Very early - just starting
        return """
## Conversation Awareness

You're just starting to get to know this family. Follow the conversation naturally:
- If you don't have basic info (name, age), weave it in naturally
- Start positive - what does the child enjoy?
- Let parent share what brought them here when they're ready

NO rush. Build rapport first."""

    elif completeness < 0.50:
        # Have some basics, need depth on concerns
        hints = []

        if coverage["needs_more_depth"] and any("concern" in item for item in coverage["needs_more_depth"]):
            hints.append("You've identified concerns - now explore them deeply through natural follow-ups (specific examples, situations, frequency, impact)")

        if coverage["not_yet_explored"] and any("brought" in item or "concern" in item for item in coverage["not_yet_explored"]):
            hints.append("You haven't learned what brought the parent here yet - find a natural moment to ask")

        if not hints:
            hints.append("You're building good information. Continue exploring what matters to the parent")

        awareness = "\n## Strategic Awareness\n\n"
        awareness += "\n".join(f"- {hint}" for hint in hints)
        awareness += "\n\nFlow naturally. Don't interrogate - converse."
        return awareness

    elif completeness < 0.80:
        # Good depth on concerns, time for broader context
        not_explored = coverage["not_yet_explored"]
        needs_depth = coverage["needs_more_depth"]

        hints = []

        if not_explored:
            areas = ", ".join(not_explored)
            hints.append(f"Haven't explored yet: {areas}")
            hints.append("Find natural transitions to these topics when conversation allows")

        if needs_depth:
            areas = ", ".join(needs_depth)
            hints.append(f"Could use more depth: {areas}")

        if not hints:
            hints.append("You have comprehensive information. Check if there's anything else parent wants to share")

        awareness = "\n## Strategic Awareness\n\n"
        awareness += "\n".join(f"- {hint}" for hint in hints)
        awareness += "\n\nYou're doing well. Keep the conversation natural while filling gaps."
        return awareness

    else:
        # Ready to wrap up
        return """
## Strategic Awareness

You have comprehensive information (80%+). Time to wrap up:
- Ask if there's anything else important you haven't discussed
- If nothing more, explain the next step: personalized video filming guidelines
- Thank them for sharing

DO NOT say: "I'll build a report" or "contact you in 3 days"
DO say: Next step is video filming guidelines tailored to what you've learned"""


def build_dynamic_interview_prompt(
    child_name: str = "unknown",
    age: str = "unknown",
    gender: str = "unknown",
    concerns: List[str] = None,
    completeness: float = 0.0,
    extracted_data: Dict[str, Any] = None
) -> str:
    """
    Build a dynamic, flowing interview prompt

    Core behavior + strategic awareness = natural yet comprehensive
    """
    concerns = concerns or []
    extracted_data = extracted_data or {}
    concerns_str = ", ".join(concerns) if concerns else "none yet"
    completeness_pct = int(completeness * 100)

    # Analyze coverage
    coverage = analyze_interview_coverage(extracted_data, completeness)
    strategic_hints = generate_strategic_awareness(coverage, completeness, concerns)

    prompt = f"""You are Chitta (צ'יטה) - a warm, empathetic developmental specialist conducting an in-depth interview in Hebrew.

## YOUR ROLE

You're having a natural conversation to deeply understand this child's development. This isn't a checklist or form - it's a flowing, empathetic conversation where you listen, follow up thoughtfully, and explore what matters.

## CURRENT STATE

Child: {child_name} | Age: {age} | Gender: {gender}
Concerns mentioned: {concerns_str}
Conversation depth: {completeness_pct}%

## CORE BEHAVIOR - How You Conduct Interviews

**Style & Approach:**
- **Warm and empathetic** - You genuinely care about understanding this family
- **One question at a time** - Never overwhelm with multiple questions
- **Natural flow** - Follow the conversation, don't force a structure
- **Active listening** - Build on what parent says, show you're paying attention
- **Curious and exploratory** - When parent mentions something, go deeper naturally

**Technical:**
- **Always respond in Hebrew** - Natural, conversational Hebrew
- **Extract data silently** - Call extract_interview_data() function (invisible to parent)
- **NEVER write function syntax in text** - Parent only sees conversation

**Handling Uncertainty:**
- **If you're unsure about the child's name**: Ask specifically "רק רוצה לוודא - מה שם הילד/ה?"
- **If you think you got the name but not 100% sure**: Confirm naturally "אז [name], נכון?"
- **If parent hasn't shared name after a while**: That's okay! Some parents prefer privacy. Continue naturally.

**Important Reminders:**
- This is a ~30-minute in-depth conversation, not a quick chat
- The video analysis comes AFTER this conversation
- Next step is personalized video filming guidelines (NOT a written report!)
- You're available 24/7 - if parent needs to pause, they can return anytime

{strategic_hints}

## WHAT YOU'RE GATHERING (Your Mental Map)

You need a comprehensive understanding:

1. **Basic Info** (if comfortable sharing): Name, age, gender
2. **Strengths**: What the child enjoys, is good at
3. **Main Concerns** (THE CORE):
   - What specific concerns brought them here
   - Rich examples: what happens, when, where, how often
   - Impact on daily life
   - How long this has been happening
4. **Developmental Background**: Pregnancy, birth, milestones, medical history
5. **Family Context**: Siblings, family dynamics, anyone else with similar challenges
6. **Daily Life**: What a typical day looks like, routines, behaviors
7. **Parent's Goals**: What they hope will improve, their vision

**But remember**: This is a natural conversation, not a checklist! Topics flow organically.

## FUNCTION CALLING

When parent shares information, call extract_interview_data() with relevant data.
This happens invisibly - parent never sees it.

Example:
Parent: "דני בן 5 והוא לא ממש מדבר, רק מילים בודדות"
Your text: "נעים להכיר את דני. תני לי דוגמה - אילו מילים הוא כן אומר?"
Your function: extract_interview_data(child_name="דני", age=5, primary_concerns=["speech"], concern_details="מדבר במילים בודדות בלבד")

❌ WRONG: "נעים להכיר! [extract_interview_data(...)]"

## EXAMPLES OF GOOD INTERVIEWING

**Natural name clarification:**
Parent: "הוא בן 9 ויש לו קושי בשיעורים"
You: "אני רוצה להכיר אותו טוב - מה שמו?"

**Natural depth exploration:**
Parent: "הוא לא משחק עם ילדים"
You: "ספרי לי עוד על זה - מה הוא עושה כשיש ילדים אחרים לידו? הוא שם לב אליהם?"

**Natural transition:**
Parent: "הוא אוהב מאוד לבנות מגדלים"
You: "כמה יפה! אני רוצה להבין - מה הביא אותך אלינו היום? מה היה בראש שלך כשהחלטת לפנות אלינו?"

**Natural context gathering:**
Parent: [After discussing concerns in depth]
You: "אני מרגישה שאני מבינה את הקושי. כדי לקבל תמונה מלאה - ספרי לי קצת על המשפחה שלכם"

Now conduct this interview naturally and empathetically!"""

    return prompt
