"""
Sage Service - The Interpretive Reasoning Layer

The Sage sees clearly what is. It interprets the user's message in context,
understanding what they mean, what they need, and what emotional state they're in.

This is Wu Wei: Natural interpretation without forcing into rigid categories.
The Sage describes what's happening, the Hand decides what to do about it.

Separation of concerns:
- Sage = "What does this mean?" (interpretation)
- Hand = "What do we do about it?" (action)
"""

import logging
from typing import Dict, List, Optional
from .llm.factory import create_llm_provider
from .llm.base import Message

logger = logging.getLogger(__name__)


class SageWisdom:
    """
    The Sage's interpretation of what the user means and needs.

    This is natural language wisdom, not rigid categories.
    """
    def __init__(
        self,
        interpretation: str,
        suggested_approach: str,
        emotional_state: Optional[str] = None,
        confidence: float = 1.0
    ):
        self.interpretation = interpretation
        self.suggested_approach = suggested_approach
        self.emotional_state = emotional_state
        self.confidence = confidence

    def __str__(self):
        return self.interpretation


class SageService:
    """
    The Sage - interprets what the user means and needs naturally

    Wu Wei approach: Understand the situation deeply without forcing
    into rigid categories. Provide wisdom that the Hand can act on.
    """

    def __init__(self, llm_provider=None):
        """Initialize Sage service with LLM provider"""
        self.llm = llm_provider or create_llm_provider()
        logger.info("SageService initialized - The Sage is ready to interpret")

    async def interpret(
        self,
        user_message: str,
        recent_conversation: Optional[List[Dict]] = None,
        child_context: Optional[Dict] = None,
        available_artifacts: Optional[List[str]] = None,
        session_state: Optional[Dict] = None
    ) -> SageWisdom:
        """
        The Sage interprets what the user means and needs.

        This is the core of Wu Wei: Natural understanding without forcing
        into categories. The Sage sees what is and describes it clearly.

        Args:
            user_message: What the user just said
            recent_conversation: Recent dialogue for context
            child_context: Child information (name, age, concerns)
            available_artifacts: What reports/documents exist
            session_state: Current state (completeness, etc.)

        Returns:
            SageWisdom with natural interpretation and suggested approach
        """
        # Build rich contextual picture for the Sage
        context_picture = self._build_context_picture(
            recent_conversation,
            child_context,
            available_artifacts,
            session_state
        )

        sage_prompt = f"""You are the Sage - you see clearly what is happening in conversations.

**Your role:** Interpret what the parent means and needs. Don't categorize - understand naturally.

**The situation:**

{context_picture}

**Parent just said:** "{user_message}"

---

**Your interpretation should consider:**

1. **What are they doing right now?**
   - Are they responding to something Chitta said?
   - Are they asking a new question?
   - Are they sharing an observation or concern?
   - Are they expressing emotion or needing validation?
   - Are they requesting something specific?

2. **What do they need?**
   - Do they need to share information (and have it captured)?
   - Do they need expert knowledge or guidance?
   - Do they need to understand something Chitta said?
   - Do they need something delivered (report, guidelines)?
   - Do they need to know about the app/process?

3. **What's their emotional state?**
   - Are they engaged and flowing naturally?
   - Are they confused or frustrated?
   - Are they excited or worried about their child?
   - Are they seeking reassurance?

4. **What would serve them best?**
   - What kind of response would help them most right now?
   - What context does Chitta need to respond well?
   - Should extraction happen? Should we consult artifacts?

---

**Provide your wisdom in this structure:**

**Interpretation:** [2-3 clear sentences describing what's happening and what they mean]

**Suggested approach:** [1-2 sentences on how to best serve this parent right now]

**Emotional state:** [One word or short phrase: engaged, curious, worried, confused, frustrated, etc.]

---

**Examples of good interpretation:**

Example 1:
Recent: Chitta asked "ספרי לי על הדיבור של יוני"
Parent: "תודה ששאלת. אני שמחה שאת רואה את זה. הוא מדבר רק כמה מילים בודדות"

**Interpretation:** The parent is responding warmly to Chitta's direct question about speech. They appreciate being asked and are opening up about their child's limited vocabulary. This is natural sharing in the flow of conversation - they're providing important developmental information that should be captured.

**Suggested approach:** Continue the natural dialogue flow, acknowledge their sharing, capture the speech information, and gently explore more if appropriate. This is conversation mode - keep it flowing and human.

**Emotional state:** Engaged, relieved to be heard

Example 2:
Context: Chitta said "נשמע שיוני מחפש גירוי חושי במערכת הווסטיבולרית"
Parent: "מה זה חיפוש חושי?"

**Interpretation:** The parent encountered unfamiliar professional terminology ("sensory seeking") and wants to understand what it means. This is a genuine question seeking developmental knowledge, not a continuation of sharing information. They need expert explanation of the concept, preferably connected to their child's specific behaviors so it becomes real and useful.

**Suggested approach:** Provide expert explanation of sensory seeking combined with examples from Yoni's behaviors. Use Chitta's developmental expertise + Yoni's specific context to make it personal and actionable. This is consultation mode.

**Emotional state:** Curious, wanting to learn

Example 3:
Context: No artifacts yet, conversation in progress. Chitta just said "נשמע שיש לו קושי בתפקודים ניהוליים"
Parent: "למה אמרת שזה תפקודים ניהוליים?"

**Interpretation:** The parent is seeking clarification about something Chitta just said in the current dialogue. They're not consulting a formal report (none exists yet), they're asking Chitta to explain her reasoning in real-time. This is the parent trying to understand Chitta's thinking, which helps build trust and keep the conversation flowing naturally.

**Suggested approach:** Chitta should explain her reasoning naturally, referring back to what the parent shared that led to this observation. Keep the conversation flowing while clarifying. This is still conversation mode - extraction can continue.

**Emotional state:** Curious, engaged

Example 4:
Context: Artifacts exist: baseline_parent_report, video_guidelines
Parent: "תן לי את הדוח"

**Interpretation:** Clear, direct request for a specific artifact. The parent knows what they want and is asking for it to be delivered. No confusion, no need for interpretation - they want to view their report.

**Suggested approach:** Execute the action - deliver the report. This is straightforward action mode.

**Emotional state:** Focused, task-oriented

---

**Now interpret this parent's message with the same natural clarity:**
"""

        try:
            response = await self.llm.chat(
                messages=[
                    Message(role="system", content=sage_prompt),
                    Message(role="user", content=f"Parent said: {user_message}")
                ],
                functions=None,
                temperature=0.3,  # Some creativity but grounded
                max_tokens=500
            )

            # Parse the Sage's wisdom
            wisdom_text = response.content.strip()

            # Extract sections
            interpretation = self._extract_section(wisdom_text, "Interpretation:")
            suggested_approach = self._extract_section(wisdom_text, "Suggested approach:")
            emotional_state = self._extract_section(wisdom_text, "Emotional state:")

            wisdom = SageWisdom(
                interpretation=interpretation or wisdom_text,
                suggested_approach=suggested_approach or "Respond naturally to their needs",
                emotional_state=emotional_state or "engaged",
                confidence=0.9
            )

            logger.info(f"✨ Sage's wisdom: {wisdom.interpretation[:100]}...")

            return wisdom

        except Exception as e:
            logger.error(f"Sage interpretation failed: {e}")
            # Fallback wisdom
            return SageWisdom(
                interpretation="The parent is engaging in conversation about their child. Respond naturally and continue the dialogue.",
                suggested_approach="Continue natural conversation flow, capturing information as appropriate.",
                emotional_state="engaged",
                confidence=0.5
            )

    def _build_context_picture(
        self,
        recent_conversation: Optional[List[Dict]],
        child_context: Optional[Dict],
        available_artifacts: Optional[List[str]],
        session_state: Optional[Dict]
    ) -> str:
        """Build a rich contextual picture for the Sage to understand the situation"""
        picture_parts = []

        # Recent dialogue
        if recent_conversation and len(recent_conversation) > 0:
            picture_parts.append("**Recent conversation:**")
            for turn in recent_conversation[-4:]:  # Last 2 exchanges
                role_name = "Chitta" if turn.get("role") == "assistant" else "Parent"
                content = turn.get("content", "")[:200]
                picture_parts.append(f"  {role_name}: {content}...")
        else:
            picture_parts.append("**Recent conversation:** Just starting, no prior exchanges yet")

        # Available artifacts
        if available_artifacts and len(available_artifacts) > 0:
            picture_parts.append(f"\n**Available artifacts/reports:** {', '.join(available_artifacts)}")
        else:
            picture_parts.append("\n**Available artifacts/reports:** None yet (still gathering information)")

        # Child context
        if child_context and child_context.get("child_name"):
            name = child_context.get("child_name", "")
            age = child_context.get("age", "unknown age")
            concerns = child_context.get("primary_concerns", [])
            concerns_text = ", ".join(concerns) if concerns else "not yet discussed"
            picture_parts.append(f"\n**Child:** {name}, {age} years old, concerns: {concerns_text}")
        else:
            picture_parts.append("\n**Child:** Information still being gathered")

        # Session state
        if session_state:
            completeness = session_state.get("completeness", 0.0)
            picture_parts.append(f"\n**Progress:** Interview {int(completeness * 100)}% complete")

        return "\n".join(picture_parts)

    def _extract_section(self, text: str, section_marker: str) -> Optional[str]:
        """Extract a specific section from the Sage's response"""
        if section_marker not in text:
            return None

        # Find the section
        start = text.index(section_marker) + len(section_marker)

        # Find the end (next section marker or end of text)
        end = len(text)
        for marker in ["**Interpretation:**", "**Suggested approach:**", "**Emotional state:**"]:
            if marker != section_marker and marker in text[start:]:
                marker_pos = text.index(marker, start)
                end = min(end, marker_pos)

        section_text = text[start:end].strip()

        # Remove markdown bold markers if present
        section_text = section_text.replace("**", "")

        return section_text if section_text else None


# Singleton instance
_sage_service = None


def get_sage_service() -> SageService:
    """Get or create singleton Sage service instance"""
    global _sage_service
    if _sage_service is None:
        _sage_service = SageService()
    return _sage_service
