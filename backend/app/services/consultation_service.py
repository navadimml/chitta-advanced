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
        Format retrieved context for LLM consumption.

        Args:
            context_results: Retrieved context from Graphiti/mock
            data: Current extracted data

        Returns:
            Formatted context string for LLM prompt
        """
        sections = []

        # 1. Artifacts (reports, guidelines, etc.)
        if context_results.get("artifacts"):
            artifacts_section = ["## 📋 Generated Reports & Artifacts\n"]
            for name, artifact in context_results["artifacts"].items():
                artifacts_section.append(f"### {name}")
                artifacts_section.append(f"Created: {artifact['created_at']}")

                # Include relevant parts of artifact content
                content = artifact.get("content", {})
                if isinstance(content, dict):
                    # Show summary or key sections
                    if "summary" in content:
                        artifacts_section.append(f"Summary: {content['summary']}")
                    if "sections" in content:
                        for section_name, section_content in content.get("sections", {}).items():
                            artifacts_section.append(f"\n**{section_name}:**")
                            if isinstance(section_content, str):
                                artifacts_section.append(section_content[:500])  # Limit length
                            else:
                                artifacts_section.append(str(section_content)[:500])
                else:
                    artifacts_section.append(str(content)[:500])

                artifacts_section.append("")  # Empty line between artifacts

            sections.append("\n".join(artifacts_section))

        # 2. Extracted data (structured information)
        extracted = context_results.get("extracted_data", {})
        if extracted.get("concern_details") or extracted.get("strengths"):
            data_section = ["## 📝 Information from Conversations\n"]

            if extracted.get("concern_details"):
                data_section.append("**Concerns discussed:**")
                data_section.append(extracted["concern_details"][:1000])
                data_section.append("")

            if extracted.get("strengths"):
                data_section.append("**Strengths mentioned:**")
                data_section.append(extracted["strengths"][:500])
                data_section.append("")

            if extracted.get("developmental_history"):
                data_section.append("**Developmental history:**")
                data_section.append(extracted["developmental_history"][:500])
                data_section.append("")

            sections.append("\n".join(data_section))

        # 3. Recent conversation (for temporal questions like "did X improve?")
        history = context_results.get("conversation_history", [])
        if history:
            history_section = ["## 💬 Recent Conversation Highlights\n"]
            # Take last 10 meaningful exchanges
            for turn in history[-10:]:
                role_icon = "👤" if turn["role"] == "user" else "🤖"
                content_preview = turn["content"][:200]
                history_section.append(f"{role_icon} {content_preview}...")

            sections.append("\n".join(history_section))

        if not sections:
            return "אין מידע זמין עדיין - השיחה רק התחילה."

        return "\n\n".join(sections)

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

זוהי שיחת ייעוץ - **זה היופי והכוח של צ'יטה**:
ההורה יכול/ה לשאול אותך כל שאלה על התפתחות ילדים, ואת משתמשת:
1. **הידע העצום שלך** כמומחית להתפתחות ילדים
2. **ההקשר הספציפי** על {child_name} מהשיחות והדוחות

**יש לך גישה להיסטוריה מלאה:**
- שיחות שקיימתם
- דוחות וניתוחים שיצרת
- מידע מובנה שנאסף
- (בעתיד: מסמכים שהועלו, וידאו, יומן)

**הקשר רלוונטי על {child_name}:**

{formatted_context}

---

**הנחיות למענה - התאימי לסוג השאלה:**

**A. אם שואלים שאלה התפתחותית כללית** (למשל: "מה זה חיפוש חושי?", "איך יודעים שיש ADHD?"):
   - השתמשי בידע המקצועי העצום שלך
   - הסבירי את הנושא בצורה ברורה ונגישה
   - **ואז חברי לילד הספציפי:** תני דוגמאות מהתצפיות על {child_name}
   - זה מה שמייחד אותך - תשובה מקצועית + אישית!

**B. אם שואלים על דוח/ניתוח שכתבת** (למשל: "למה כתבת שיש לו חיפוש חושי?"):
   - הסבירי מה התכוונת ולמה
   - **תני דוגמאות מהשיחות** שהובילו למסקנה
   - הראי את הדפוס/ההיגיון מאחורי הממצא
   - השתמשי בציטוטים מהשיחות כשמתאים

**C. אם שואלים על התקדמות לאורך זמן** (למשל: "האם הדיבור שלו השתפר?"):
   - הראי את המגמה עם דוגמאות ספציפיות
   - השווי ציטוטים מהשיחות במועדים שונים
   - ציין תאריכים כדי להראות התקדמות

**D. אם שואלים מה עובד/לא עובד** (למשל: "איך עזרתי לו בעבר?"):
   - חפשי ברישומי היומן והשיחות
   - תני דוגמאות מה נוסה ומה היתה התוצאה
   - הצעי המלצות מבוססות על מה שנראה עובד

**כללי תמיד:**
- **שלבי ידע כללי + הקשר ספציפי** - זה מה שעושה אותך ייחודית!
- אם אין מידע מספיק על {child_name}, תגידי זאת בכנות והסבירי בכלליות
- תני עצות מעשיות מבוססות על החוזקות של {child_name}
- אם לא בטוחה, שאלי שאלות הבהרה

**סגנון:**
- דברי בעברית טבעית, חמה, תומכת ומקצועית
- השתמשי בשם של {child_name} כשמתאים
- תני תשובות מפורטות עם דוגמאות
- היי מומחית אמיתית - אל תפחדי להראות את הידע שלך!

**זכרי:** זו שיחת ייעוץ מקצועית ואישית. היופי שלך הוא לשלב ידע רחב עם הקשר אישי.
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
