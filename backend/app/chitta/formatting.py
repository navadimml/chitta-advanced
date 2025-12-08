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
    from .models import Understanding, ExplorationCycle, ExtractionResult, ToolCall


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

    if not understanding.facts:
        return "Still getting to know this child."

    sections = []

    # Essence (if crystallized)
    if understanding.essence and understanding.essence.narrative:
        sections.append(f"**Who they are**: {understanding.essence.narrative}")

    # Key facts by domain
    domains: dict = {}
    for fact in understanding.facts:
        domain = fact.domain or "general"
        if domain not in domains:
            domains[domain] = []
        domains[domain].append(fact.content)

    for domain, facts in domains.items():
        sections.append(f"**{domain}**: {'; '.join(facts[:3])}")

    # Patterns
    if understanding.patterns:
        pattern_texts = [p.description for p in understanding.patterns[:3]]
        sections.append(f"**Patterns**: {'; '.join(pattern_texts)}")

    return "\n".join(sections) if sections else "Building understanding..."


def format_curiosities(curiosities: List["Curiosity"]) -> str:
    """
    Format curiosities for prompt with visual activation bars.

    Shows what the Gestalt is curious about right now.
    Returns English for LLM prompt context.
    """
    if not curiosities:
        return "Open to discover who this child is."

    lines = []

    for c in curiosities[:5]:
        # Visual activation bar
        filled = int(c.activation * 10)
        empty = 10 - filled
        bar = "█" * filled + "░" * empty
        icon = TYPE_ICONS.get(c.type, "")
        percent = int(c.activation * 100)

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


def format_cycles(cycles: List["ExplorationCycle"]) -> str:
    """
    Format active exploration cycles for prompt.

    Shows what explorations are currently active.
    Returns English for LLM prompt context.
    """
    active = [c for c in cycles if c.status == "active"]

    if not active:
        return "No active explorations."

    lines = []

    for c in active[:3]:
        type_icon = TYPE_ICONS.get(c.curiosity_type, "")
        lines.append(f"- [{type_icon} {c.curiosity_type}] {c.focus} (id: {c.id})")

        if c.curiosity_type == "hypothesis":
            lines.append(f"  Testing: {c.theory}")
            conf_percent = int((c.confidence or 0.5) * 100)
            lines.append(f"  Confidence: {conf_percent}%")
            if c.video_appropriate:
                lines.append("  Video appropriate: Yes")
        elif c.curiosity_type == "question":
            lines.append(f"  Question: {c.question}")

        evidence_count = len(c.evidence)
        lines.append(f"  Evidence collected: {evidence_count} pieces")

    return "\n".join(lines)


def format_extraction_summary(extraction: "ExtractionResult") -> str:
    """
    Format what was extracted in Phase 1 for Phase 2 context.

    This tells the response LLM what we just learned.
    Returns English for LLM prompt context.
    """
    if not extraction.tool_calls:
        return "No specific extractions this turn."

    lines = []

    for tc in extraction.tool_calls:
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
    perceived_intent: str = "conversational"
) -> str:
    """
    Compute turn-specific guidance based on what was extracted.

    NOT keyword matching - this is based on what the LLM
    actually understood and extracted in Phase 1.

    Returns English for LLM alignment.
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

    return """
## TURN GUIDANCE: NATURAL RESPONSE

Respond naturally to what was shared.
- Follow the flow of conversation
- One question at a time, if any
- Let curiosity guide, not agenda
"""


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

## LANGUAGE
- You MUST respond in natural Hebrew
- Use simple, warm language
- Be professional but human
"""


def build_extraction_tools_description() -> str:
    """
    Build the tools description for extraction phase.
    English for LLM alignment.
    """
    return """
## TOOLS AVAILABLE

Use these tools to extract and record what you perceive:

- **notice**: Record an observation about the child
- **wonder**: Spawn a new curiosity (discovery/question/hypothesis/pattern)
- **capture_story**: When a meaningful story is shared - extract what it reveals
- **add_evidence**: Add evidence to active exploration cycle
- **spawn_exploration**: Start focused investigation when curiosity is high

RESPOND WITH TOOL CALLS ONLY. No text response in this phase.
"""


def build_response_language_instruction() -> str:
    """
    Build the language instruction for response phase.
    """
    return """
## RESPONSE LANGUAGE

CRITICAL: You MUST respond in natural Hebrew.
- Warm, professional tone
- Simple words, deep understanding
- "שמתי לב ש..." not "המערכת זיהתה..."
- Be human, not robotic
"""
