"""
Consultation Service - Universal handler for consultation questions

Powered by Graphiti semantic search (or mock for now).
Handles ANY consultation question type:
- Questions about generated artifacts/reports
- Questions about uploaded documents (when implemented)
- Questions about previous conversations
- Questions about patterns over time

Wu Wei principle: Use Graphiti's existing power instead of building special handlers.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .llm.base import Message, BaseLLMProvider
from .llm.factory import create_llm_provider
from .mock_graphiti import MockGraphiti
from .interview_service import get_interview_service

logger = logging.getLogger(__name__)


class ConsultationService:
    """
    Universal consultation service powered by Graphiti/knowledge graph.

    Works for ANY question:
    - "What did you mean by 'sensory seeking' in the report?"
    - "What did the psychologist write about attention?"
    - "How has speech improved over time?"
    - "What strategies worked for meltdowns?"

    ONE handler, works for all question types.
    Wu Wei: The power is already in Graphiti - we just use it fully.
    """

    def __init__(
        self,
        graphiti: Optional[MockGraphiti] = None,
        llm_provider: Optional[BaseLLMProvider] = None
    ):
        """
        Initialize consultation service.

        Args:
            graphiti: Graphiti instance (or mock)
            llm_provider: LLM provider for generating responses
        """
        self.graphiti = graphiti or MockGraphiti()
        self.llm = llm_provider or create_llm_provider()
        self.interview_service = get_interview_service()

        logger.info("ConsultationService initialized (universal handler)")

    async def handle_consultation(
        self,
        family_id: str,
        question: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Universal consultation handler.

        Args:
            family_id: Family identifier
            question: User's consultation question
            conversation_history: Recent conversation context (optional)

        Returns:
            Dict with:
                - response: Natural Hebrew response
                - sources_used: Summary of what sources were referenced
                - timestamp: When consultation occurred
        """
        logger.info(f"📚 Consultation question for family {family_id}: {question[:50]}...")

        # 1. Get current session state for context
        session = self.interview_service.get_or_create_session(family_id)
        data = session.extracted_data

        # 2. Retrieve relevant context using Graphiti search
        # For now with mock, we'll get conversation history and artifacts
        context_results = await self._retrieve_context(family_id, question, session)

        # 3. Format context for LLM
        formatted_context = self._format_context_for_llm(context_results, data)

        # 4. Build system prompt with context
        system_prompt = self._build_consultation_prompt(formatted_context, data)

        # 5. Generate consultation response
        messages = [Message(role="system", content=system_prompt)]

        # Add recent conversation history for continuity
        if conversation_history:
            for turn in conversation_history[-6:]:  # Last 3 exchanges
                messages.append(Message(
                    role=turn.get("role", "user"),
                    content=turn.get("content", "")
                ))

        # Add current question
        messages.append(Message(role="user", content=question))

        # Call LLM
        try:
            llm_response = await self.llm.chat(
                messages=messages,
                functions=None,
                temperature=0.7,
                max_tokens=2000
            )

            response_text = llm_response.content

            logger.info(f"✅ Consultation response generated ({len(response_text)} chars)")

            # 6. Save consultation as conversation turn (for future context)
            self.interview_service.add_conversation_turn(
                family_id,
                role="user",
                content=question
            )
            self.interview_service.add_conversation_turn(
                family_id,
                role="assistant",
                content=response_text
            )

            return {
                "response": response_text,
                "sources_used": self._summarize_sources(context_results),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Consultation failed: {e}", exc_info=True)
            return {
                "response": "מצטערת, נתקלתי בבעיה טכנית בעת חיפוש התשובה. בואי ננסה שוב.",
                "sources_used": {},
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }

    async def _retrieve_context(
        self,
        family_id: str,
        question: str,
        session: Any
    ) -> Dict[str, Any]:
        """
        Retrieve relevant context using Graphiti search (or mock equivalent).

        In production: Use Graphiti's semantic search
        For now: Use mock Graphiti query + session artifacts

        Args:
            family_id: Family identifier
            question: User's question
            session: Current interview session

        Returns:
            Dict with relevant context from various sources
        """
        # Get conversation history (recent turns)
        history = self.interview_service.get_conversation_history(
            family_id,
            last_n=40  # Last 20 exchanges
        )

        # Get artifacts (reports, guidelines, etc.)
        artifacts = {}
        for artifact_name, artifact in session.artifacts.items():
            artifacts[artifact_name] = {
                "type": artifact.type,
                "content": artifact.content,
                "created_at": artifact.created_at.isoformat() if hasattr(artifact.created_at, 'isoformat') else str(artifact.created_at)
            }

        # Get extracted data
        extracted_data = {
            "child_name": session.extracted_data.child_name,
            "age": session.extracted_data.age,
            "concerns": session.extracted_data.primary_concerns,
            "concern_details": session.extracted_data.concern_details,
            "strengths": session.extracted_data.strengths,
            "developmental_history": session.extracted_data.developmental_history,
            "family_context": session.extracted_data.family_context,
            "daily_routines": session.extracted_data.daily_routines,
            "parent_goals": session.extracted_data.parent_goals
        }

        return {
            "conversation_history": history,
            "artifacts": artifacts,
            "extracted_data": extracted_data,
            "session_stats": {
                "completeness": session.completeness,
                "message_count": len(history),
                "artifacts_count": len(artifacts)
            }
        }

    def _format_context_for_llm(
        self,
        context_results: Dict[str, Any],
        data: Any
    ) -> str:
        """
        Format retrieved context for LLM consumption - CONCISE version.

        Args:
            context_results: Retrieved context from Graphiti/mock
            data: Current extracted data

        Returns:
            Formatted context string for LLM prompt (brief summaries only)
        """
        sections = []

        # 1. Artifacts (reports, guidelines, etc.) - BRIEF summaries only
        if context_results.get("artifacts"):
            artifacts_section = ["## 📋 Reports & Documents (Brief Summary)\n"]
            for name, artifact in context_results["artifacts"].items():
                # Include only brief content preview (200 chars max)
                content = artifact.get("content", {})
                if isinstance(content, dict):
                    # Show only summary if available
                    if "summary" in content:
                        summary_preview = content['summary'][:200]
                        artifacts_section.append(f"**{name}:** {summary_preview}")
                    elif "sections" in content:
                        # Take first section's first 200 chars
                        first_section = next(iter(content.get("sections", {}).values()), "")
                        if isinstance(first_section, str):
                            artifacts_section.append(f"**{name}:** {first_section[:200]}")
                else:
                    artifacts_section.append(f"**{name}:** {str(content)[:200]}")

            sections.append("\n".join(artifacts_section))

        # 2. Extracted data (structured information) - BRIEF snippets
        extracted = context_results.get("extracted_data", {})
        if extracted.get("concern_details") or extracted.get("strengths"):
            data_section = ["## 📝 Key Information from Conversations\n"]

            if extracted.get("concern_details"):
                data_section.append(f"**Concerns:** {extracted['concern_details'][:200]}...")

            if extracted.get("strengths"):
                data_section.append(f"**Strengths:** {extracted['strengths'][:200]}...")

            sections.append("\n".join(data_section))

        # 3. Recent conversation - Only last 5 exchanges
        history = context_results.get("conversation_history", [])
        if history:
            history_section = ["## 💬 Recent Conversation (Last 5 Exchanges)\n"]
            # Take last 5 exchanges only (not 10)
            for turn in history[-5:]:
                role_icon = "👤" if turn["role"] == "user" else "🤖"
                content_preview = turn["content"][:100]  # Shorter preview
                history_section.append(f"{role_icon} {content_preview}...")

            sections.append("\n".join(history_section))

        if not sections:
            return "אין מידע זמין עדיין - השיחה רק התחילה."

        # Add reminder at the end
        context_text = "\n\n".join(sections)
        context_text += "\n\n**Remember: Use this to inform your answer, but keep response BRIEF (2-3 sentences).**"

        return context_text

    def _build_consultation_prompt(
        self,
        formatted_context: str,
        data: Any
    ) -> str:
        """
        Build system prompt for consultation with injected context.

        This is "the beauty and strength of Chitta": Parent can ask ANY question about
        child development, and we use BOTH:
        - LLM's huge developmental knowledge
        - Specific child context from conversations/artifacts

        Args:
            formatted_context: Formatted knowledge/context
            data: Current extracted data

        Returns:
            System prompt string
        """
        child_name = data.child_name or "הילד/ה"

        return f"""אתה Chitta (צ'יטה) - מדריכה מומחית להתפתחות ילדים בישראל.

ההורה שואל שאלת ייעוץ על {child_name}. יש לך גישה להיסטוריה מלאה מהשיחות והדוחות.

**הקשר רלוונטי על {child_name}:**

{formatted_context}

---

## 🚨 CRITICAL - CONVERSATION STYLE

**את מדברת עם הורה מודאג/ת, לא כותבת דו״ח מקצועי!**

**ABSOLUTE RULES:**
1. **Maximum 2-3 sentences** - Like texting a friend, not writing an article
2. **Direct answer** - Get straight to the point
3. **Warm and natural** - Hebrew conversation style, not formal clinical language
4. **No exhaustive lists** - One key point is enough

**הנחיות למענה:**

1. **תשובה קצרה וחמה** - 2-3 משפטים מקסימום
   - תני מענה ישיר לשאלה בלי התארכויות
   - דברי כמו חברה, לא כמו מומחית שכותבת דוח

2. **השתמשי בהקשר - אבל תמצת**
   - אם יש תצפית רלוונטית - הזכר במשפט אחד
   - אם יש דפוס - תאר בקצרה בלי פירוט מלא
   - אל תצטט תאריכים ושעות - זה מרגיש רובוטי

3. **אם אין מידע מספיק:**
   - תגידי זאת בפשטות: "לא זוכרת שדיברנו על זה - רוצה לשתף?"
   - אל תסבירי למה אין לך מידע, פשוט תשאלי

4. **סגנון שיחה, לא דו״ח:**
   - ✅ CORRECT: "מהשיחות שלנו נראה ש..."
   - ❌ WRONG: "על פי הנתונים שנאספו ביום X..."
   - ✅ CORRECT: "זה משתפר!"
   - ❌ WRONG: "ניתן לראות מגמת שיפור לאורך זמן בהתבסס על..."

**דוגמאות:**

❌ WRONG (200 מילים - סגנון דוח):
"על סמך הדוח שיצרתי ניתן לראות שהתייחסתי למספר היבטים התפתחותיים. מבחינת החיפוש החושי, זה מתייחס לנטייה של הילד לחפש גירויים חושיים בצורה אקטיבית - למשל, להסתובב הרבה, לגעת בדברים, או לחפש תנועה. בשיחה שלנו ביום 12/11 בשעה 14:30 ציינת ש'הוא רץ ומטפס כל הזמן'..."

✅ CORRECT (30 מילים - סגנון שיחה):
"חיפוש חושי זה כשהילד מחפש תחושות - כמו להסתובב, לקפץ, לגעת בהכל. {child_name} נראה כזה - זוכרת ששיתפת שהוא רץ ומטפס הרבה."

**זכרי: 2-3 משפטים מקסימום! תשובה קצרה, חמה, לעניין.**
"""

    def _summarize_sources(self, context_results: Dict[str, Any]) -> Dict[str, int]:
        """
        Summarize which sources were used in consultation.

        Args:
            context_results: Retrieved context

        Returns:
            Dict with counts of different source types
        """
        return {
            "artifacts_used": len(context_results.get("artifacts", {})),
            "conversation_turns_used": len(context_results.get("conversation_history", [])),
            "has_extracted_data": bool(context_results.get("extracted_data")),
            "completeness": context_results.get("session_stats", {}).get("completeness", 0.0)
        }


# Singleton instance
_consultation_service: Optional[ConsultationService] = None


def get_consultation_service() -> ConsultationService:
    """
    Get global ConsultationService instance (singleton pattern).

    Returns:
        ConsultationService instance
    """
    global _consultation_service

    if _consultation_service is None:
        _consultation_service = ConsultationService()

    return _consultation_service
