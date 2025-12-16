"""
Prompt Formatting Utilities

Helper functions for building prompts.
NO intent detection here - that happens in Phase 1 LLM.

IMPORTANT: Prompts are in ENGLISH for better LLM alignment.
User-facing text (responses) should be in Hebrew.
"""

from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .curiosity import Curiosity
    from .models import Understanding, Exploration, PerceptionResult, ToolCall, Crystal


# Type icons for visual display
TYPE_ICONS = {
    "discovery": "🔍",
    "question": "❓",
    "hypothesis": "💡",
    "pattern": "🔗",
}

# Hebrew domain names for user-facing content
DOMAIN_NAMES_HE = {
    "motor": "מוטורי",
    "social": "חברתי",
    "emotional": "רגשי",
    "cognitive": "קוגניטיבי",
    "language": "שפה",
    "sensory": "חושי",
    "regulation": "ויסות",
    "essence": "מהות",
    "strengths": "חוזקות",
    "context": "הקשר",
    "concerns": "דאגות",
    "general": "כללי",
}


def format_understanding(understanding: Optional["Understanding"]) -> str:
    """
    Format understanding for prompt.

    Provides context about what we know about the child.
    Returns English for LLM prompt context.
    """
    if not understanding:
        return "Still getting to know this child."

    if not understanding.observations:
        return "Still getting to know this child."

    sections = []

    # Essence (if crystallized)
    if understanding.essence and understanding.essence.narrative:
        sections.append(f"**Who they are**: {understanding.essence.narrative}")

    # Key observations by domain
    domains: dict = {}
    for observation in understanding.observations:
        domain = observation.domain or "general"
        if domain not in domains:
            domains[domain] = []
        domains[domain].append(observation.content)

    for domain, observations in domains.items():
        sections.append(f"**{domain}**: {'; '.join(observations[:3])}")

    # Patterns
    if understanding.patterns:
        pattern_texts = [p.description for p in understanding.patterns[:3]]
        sections.append(f"**Patterns**: {'; '.join(pattern_texts)}")

    # Developmental milestones (timeline)
    if understanding.milestones:
        milestone_texts = []
        for m in sorted(understanding.milestones, key=lambda x: x.age_months or 999)[:5]:
            age_str = ""
            if m.age_months:
                years = m.age_months // 12
                months = m.age_months % 12
                if years > 0 and months > 0:
                    age_str = f"at {years}y{months}m"
                elif years > 0:
                    age_str = f"at {years}y"
                else:
                    age_str = f"at {months}m"
            elif m.age_description:
                age_str = m.age_description
            type_marker = {"achievement": "✓", "concern": "⚠", "regression": "↓", "birth": "◯"}.get(m.milestone_type, "·")
            milestone_texts.append(f"{type_marker} {m.description}" + (f" ({age_str})" if age_str else ""))
        sections.append(f"**Milestones**: {'; '.join(milestone_texts)}")

    return "\n".join(sections) if sections else "Building understanding..."


def format_curiosities(curiosities: List["Curiosity"]) -> str:
    """
    Format curiosities for prompt with visual pull bars.

    Shows what Darshan is curious about right now.
    Returns English for LLM prompt context.
    """
    if not curiosities:
        return "Open to discover who this child is."

    lines = []

    for c in curiosities[:5]:
        # Visual pull bar
        filled = int(c.pull * 10)
        empty = 10 - filled
        bar = "█" * filled + "░" * empty
        icon = TYPE_ICONS.get(c.type, "")
        percent = int(c.pull * 100)

        lines.append(f"- {icon} {c.focus} [{bar}] {percent}%")

        # Type-specific details
        if c.type == "hypothesis" and c.theory:
            cert_percent = int(c.certainty * 100)
            lines.append(f"  Theory: {c.theory} (confidence: {cert_percent}%)")
            if c.video_appropriate:
                lines.append("  Video appropriate: Yes")
        elif c.type == "question" and c.question:
            lines.append(f"  Question: {c.question}")
        elif c.type == "pattern" and c.domains_involved:
            domains_text = ", ".join(c.domains_involved)
            lines.append(f"  Domains: {domains_text}")

    return "\n".join(lines)


def format_explorations(explorations: List["Exploration"]) -> str:
    """
    Format active explorations for prompt.

    Shows what explorations are currently active.
    Returns English for LLM prompt context.
    """
    active = [e for e in explorations if e.status == "active"]

    if not active:
        return "No active explorations."

    lines = []

    for e in active[:3]:
        type_icon = TYPE_ICONS.get(e.curiosity_type, "")
        lines.append(f"- [{type_icon} {e.curiosity_type}] {e.focus} (id: {e.id})")

        if e.curiosity_type == "hypothesis":
            lines.append(f"  Testing: {e.theory}")
            conf_percent = int((e.confidence or 0.5) * 100)
            lines.append(f"  Confidence: {conf_percent}%")
            if e.video_appropriate:
                lines.append("  Video appropriate: Yes")
        elif e.curiosity_type == "question":
            lines.append(f"  Question: {e.question}")

        evidence_count = len(e.evidence)
        lines.append(f"  Evidence collected: {evidence_count} pieces")

    return "\n".join(lines)


def format_perception_summary(perception: "PerceptionResult") -> str:
    """
    Format what was perceived in Phase 1 for Phase 2 context.

    This tells the response LLM what we just learned.
    Returns English for LLM prompt context.
    """
    if not perception.tool_calls:
        return "No specific perceptions this turn."

    lines = []

    for tc in perception.tool_calls:
        if tc.name == "capture_story":
            summary = tc.args.get("summary", "story captured")
            lines.append(f"📖 Captured story: {summary}")
            reveals = tc.args.get("reveals", [])
            if reveals:
                reveals_text = ", ".join(reveals[:3])
                lines.append(f"   Reveals: {reveals_text}")

        elif tc.name == "notice":
            observation = tc.args.get("observation", "observation")
            lines.append(f"👁 Noticed: {observation}")

        elif tc.name == "wonder":
            about = tc.args.get("about", "something")
            wonder_type = tc.args.get("type", "question")
            type_icon = TYPE_ICONS.get(wonder_type, "")
            lines.append(f"💭 New curiosity {type_icon}: {about}")

        elif tc.name == "add_evidence":
            lines.append("📝 Evidence added to active exploration")

        elif tc.name == "spawn_exploration":
            focus = tc.args.get("focus", "exploration")
            lines.append(f"🔬 Starting new exploration: {focus}")

    return "\n".join(lines) if lines else "Processing naturally."


def format_open_questions(questions: List[str]) -> str:
    """
    Format open questions for display.
    Returns English for LLM prompt context.
    """
    if not questions:
        return ""

    lines = ["**Open Questions:**"]
    for q in questions[:5]:
        lines.append(f"- {q}")

    return "\n".join(lines)


def format_stories_summary(stories: list) -> str:
    """
    Format stories summary for synthesis context.
    Returns English for LLM prompt context.
    """
    if not stories:
        return "No stories captured yet."

    lines = []
    for story in stories[:5]:
        lines.append(f"- {story.summary}")
        if story.reveals:
            reveals_text = ", ".join(story.reveals[:3])
            lines.append(f"  Reveals: {reveals_text}")

    return "\n".join(lines)


def format_turn_guidance(
    captured_story: bool = False,
    spawned_curiosity: bool = False,
    added_evidence: bool = False,
    perceived_intent: str = "conversational",
    clinical_gaps: list = None,
) -> str:
    """
    Compute turn-specific guidance based on what was extracted.

    NOT keyword matching - this is based on what the LLM
    actually understood and extracted in Phase 1.

    Clinical gaps are surfaced as SOFT hints - opportunities to
    naturally weave in questions, not rigid agenda items.

    Returns English for LLM alignment.
    """
    clinical_gaps = clinical_gaps or []
    # Summary/share request - guide to ChildSpace
    if perceived_intent == "summary_request":
        return """
## TURN GUIDANCE: SUMMARY/SHARE REQUEST

The parent wants a summary or to share information about their child.
IMPORTANT: Summaries are created in the ChildSpace, not in chat.

Guide them warmly:
- Acknowledge their request
- Explain that everything you've learned is organized in the child's Space
- Tell them to tap on the child's avatar (the circle with their initial)
- In the "שיתוף" (Share) tab, they can create customized summaries for different experts
- The system will generate a professional summary tailored for the specific expert they choose

Example response:
"אשמח לעזור! כל מה שלמדתי על [שם הילד] מסודר במרחב שלו.
לחצי על העיגול עם האות שלו למעלה, ובחרי בלשונית 'שיתוף'.
שם תוכלי ליצור סיכום מותאם לכל מומחה - רופא ילדים, גננת, או כל איש מקצוע אחר."

Do NOT try to create a summary in the chat.
"""

    if captured_story:
        return """
## TURN GUIDANCE: STORY RECEIVED

You just captured a meaningful story. This is GOLD.
- Reflect back what you heard and what it reveals about the child
- Honor the significance - don't rush past it
- Let the parent see their child through new eyes
- Only then, bridge forward naturally

**Do NOT**: Immediately pivot to questions. Miss what it reveals.
"""

    if added_evidence:
        return """
## TURN GUIDANCE: EVIDENCE ADDED

You just added evidence to an active exploration.
- Acknowledge what was shared
- If the exploration is progressing well, share that insight
- Consider if we're close to understanding
"""

    if spawned_curiosity:
        return """
## TURN GUIDANCE: NEW CURIOSITY

Something sparked your curiosity about this child.
- Follow that thread naturally
- Don't make the conversation feel like an interrogation
"""

    if perceived_intent == "question":
        return """
## TURN GUIDANCE: QUESTION ASKED

The parent asked a question.
- Answer their question first, directly and helpfully
- Use your developmental psychology expertise
- Then bridge naturally to continue understanding
"""

    if perceived_intent == "emotional":
        return """
## TURN GUIDANCE: EMOTION EXPRESSED

The parent is expressing feelings.
- Hold space. Acknowledge what they're feeling.
- You're an expert, but also a human presence.
- Don't rush to problem-solve.
"""

    base_guidance = """
## TURN GUIDANCE: NATURAL RESPONSE

Respond naturally to what was shared.
- Follow the flow of conversation
- One question at a time, if any
- Let curiosity guide, not agenda
"""

    # Add clinical gap hints if we have significant gaps
    # These are SOFT suggestions - opportunities, not requirements
    if clinical_gaps:
        gap_hints = _format_clinical_gap_hints(clinical_gaps)
        if gap_hints:
            base_guidance += gap_hints

    return base_guidance


def _format_clinical_gap_hints(clinical_gaps: list) -> str:
    """
    Format clinical gaps as soft conversation hints.

    These are NOT checklist items. They're opportunities to naturally
    weave in useful questions when the moment feels right.
    """
    if not clinical_gaps:
        return ""

    # Only include critical and important gaps
    relevant_gaps = [g for g in clinical_gaps if g.priority.value in ("critical", "important")]
    if not relevant_gaps:
        return ""

    # Group by priority
    critical = [g for g in relevant_gaps if g.priority.value == "critical"]
    important = [g for g in relevant_gaps if g.priority.value == "important"]

    lines = ["\n## CLINICAL CONTEXT (soft hints for natural weaving)\n"]
    lines.append("If the moment feels natural, these topics would deepen our understanding:\n")

    if critical:
        lines.append("\n**Would be especially helpful:**")
        for gap in critical[:3]:  # Max 3
            lines.append(f"- {gap.parent_description}")
            lines.append(f"  (Natural question: \"{gap.parent_question}\")")

    if important:
        lines.append("\n**Also useful when opportunity arises:**")
        for gap in important[:2]:  # Max 2
            lines.append(f"- {gap.parent_description}")

    lines.append("\n*These are NOT agenda items. Respond to what the parent shared first.*")
    return "\n".join(lines)


def build_identity_section() -> str:
    """
    Build the identity section for system prompts.

    Defines who Chitta is. English for LLM alignment.
    """
    return """
# IDENTITY

You are Chitta - an expert developmental psychologist (ages 0.5-18 years).

## WHO YOU ARE
- An expert guide with deep knowledge in child development
- Voice: Warm, professional, natural Hebrew
- Say "שמתי לב ש..." NOT "המערכת זיהתה..."

## YOUR PRINCIPLES
- Curiosity drives exploration, not checklists
- Stories are GOLD - honor what was shared
- One question at a time, if any
- Follow the flow, don't force agenda

## CHILDSPACE - WHERE ARTIFACTS LIVE
The parent can access a "ChildSpace" by tapping on the child's avatar (the circle with initial).
This is where HOLISTIC artifacts live - things you've learned, organized for them.

**When a parent asks for a summary, report, or to share information:**
DO NOT try to create a summary in the chat. Instead, guide them warmly:
- Tell them everything is organized in the child's Space (המרחב)
- They tap the avatar at the top → open the "שיתוף" (Share) tab
- There they can create customized summaries for different experts
- The system generates professional summaries tailored for specific professionals

Example response to "תעשי לי סיכום":
"אשמח! כל מה שלמדתי על [שם הילד] מסודר במרחב שלו.
לחצי על העיגול למעלה ובחרי בלשונית 'שיתוף' - שם תוכלי ליצור סיכום מותאם לכל מומחה."

## LANGUAGE
- You MUST respond in natural Hebrew
- Use simple, warm language
- Be professional but human
"""


def build_perception_tools_description() -> str:
    """
    Build the tools description for perception phase.
    English for LLM alignment.
    """
    return """
## TOOLS AVAILABLE

Use these tools to perceive and record what you notice:

- **notice**: Record an observation about the child (general facts, behaviors, concerns)
- **record_milestone**: Record developmental milestones - use when parent mentions WHEN something happened:
  - "Started walking at 14 months" → record_milestone(domain="motor", milestone_type="achievement", age_months=14)
  - "First words around age 1" → record_milestone(domain="language", milestone_type="achievement", age_months=12)
  - "Lost words at 18 months" → record_milestone(domain="language", milestone_type="regression", age_months=18)
  - Birth/pregnancy: use domain="birth_history", NO age_months needed:
    - "C-section" / "Natural birth" → milestone_type="birth" (the birth moment)
    - "Born at 36 weeks" / "Difficult pregnancy" → milestone_type="concern" (pregnancy events)
- **wonder**: Spawn a new curiosity (discovery/question/hypothesis/pattern)
- **capture_story**: When a meaningful story is shared - capture what it reveals
- **add_evidence**: Add evidence to active exploration
- **spawn_exploration**: Start focused investigation when curiosity pulls strongly

**CRITICAL**: When parent mentions age/timing of developmental events, use record_milestone NOT notice!

RESPOND WITH TOOL CALLS ONLY. No text response in this phase.
"""


def build_response_language_instruction() -> str:
    """
    Build the language instruction for response phase.
    """
    return """
## RESPONSE LANGUAGE - CRITICAL RULES

**Be a supportive friend, NOT a professional or robot:**

**EMOTIONAL PRESENCE - Make parent feel HEARD:**
- When parent shares something hard or emotional, don't ignore it
- Acknowledge briefly but genuinely, then continue naturally
- DON'T say generic phrases like "אני מבינה את הרגשות שלך" or "זו חוויה מורכבת"
- DO respond like a friend would: short, real, then move forward together

**THE PRINCIPLE (not specific phrases to copy):**
The key is brief, genuine acknowledgment in natural spoken Hebrew - the way a friend
would respond before continuing the conversation. Use YOUR OWN varied phrasing each time.
Every response should feel fresh and specific to what was shared.

**Example of the PRINCIPLE (these are illustrations, NOT templates to repeat):**
- Parent shares something hard → brief empathetic response + natural follow-up
- The exact words should VARY each time - never use the same phrase repeatedly
- What matters is the FEEL: warm, real, then moving forward together

**NEVER DO THESE:**
❌ Echo/parrot what parent said
❌ Label things as important ("זה מידע משמעותי")
❌ Use clinical terms (התפתחות שפתית, אנרגיה התפתחותית)
❌ Move robotically to next question ("כדי להמשיך לאסוף...")
❌ Be telegraphic - one word answers or cold/abrupt responses
❌ Ignore emotional content and jump straight to questions
❌ Repeat the same empathetic phrases over and over

**INSTEAD:**
✅ Brief, genuine acknowledgment + natural follow-up
✅ Simple everyday Hebrew words
✅ Be warm and curious like a friend
✅ Show you're WITH the parent, not interviewing them
✅ VARY your language naturally - conversation should flow, not feel scripted
"""


def format_crystal(crystal: Optional["Crystal"]) -> str:
    """
    Format Crystal (holistic understanding) for conversation context.

    This is the KEY CONTEXT that helps the LLM understand the child holistically,
    not just as a collection of facts. The Crystal contains:
    - Essence narrative (who this child is)
    - Patterns (cross-domain connections)
    - Intervention pathways (how strengths can address concerns)

    Returns English for LLM alignment.
    """
    if not crystal:
        return "No crystallized understanding yet - still building picture."

    sections = []

    # Essence narrative - the most important part
    if crystal.essence_narrative:
        sections.append(f"**Who this child is**: {crystal.essence_narrative}")

    # Temperament and core qualities
    if crystal.temperament:
        sections.append(f"**Temperament**: {', '.join(crystal.temperament)}")
    if crystal.core_qualities:
        sections.append(f"**Core qualities**: {', '.join(crystal.core_qualities)}")

    # Patterns - cross-domain connections
    if crystal.patterns:
        pattern_lines = []
        for p in crystal.patterns[:4]:
            domains = ", ".join(p.domains_involved) if p.domains_involved else "general"
            pattern_lines.append(f"- {p.description} (crosses: {domains})")
        sections.append("**Patterns noticed**:\n" + "\n".join(pattern_lines))

    # Intervention pathways - the practical wisdom
    if crystal.intervention_pathways:
        pathway_lines = []
        for ip in crystal.intervention_pathways[:3]:
            pathway_lines.append(f"- {ip.hook} → can help with: {ip.concern}")
            if ip.suggestion:
                pathway_lines.append(f"  Try: {ip.suggestion}")
        sections.append("**Ways to reach this child**:\n" + "\n".join(pathway_lines))

    # Open questions
    if crystal.open_questions:
        questions = [f"- {q}" for q in crystal.open_questions[:3]]
        sections.append("**Still wondering**:\n" + "\n".join(questions))

    return "\n\n".join(sections) if sections else "Building holistic understanding..."
