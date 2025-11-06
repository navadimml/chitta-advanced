"""
Conversation Service - Orchestrates LLM conversations with function calling

This service:
1. Manages conversation flow with LLM
2. Processes function calls (data extraction, actions, completeness)
3. Updates interview state based on LLM responses
4. Generates appropriate system prompts
5. Returns responses with updated context
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from .llm.base import Message, BaseLLMProvider
from .llm.factory import create_llm_provider
from .interview_service import get_interview_service, InterviewService
from ..prompts.interview_prompt import build_interview_prompt
from ..prompts.interview_prompt_lite import build_interview_prompt_lite
from ..prompts.interview_functions import INTERVIEW_FUNCTIONS
from ..prompts.interview_functions_lite import INTERVIEW_FUNCTIONS_LITE

logger = logging.getLogger(__name__)


class ConversationService:
    """
    Manages LLM conversations with continuous extraction

    This is the main orchestrator that connects:
    - LLM Provider (Gemini/Claude/etc)
    - Interview Service (state management)
    - Function calling (data extraction)
    """

    def __init__(
        self,
        llm_provider: Optional[BaseLLMProvider] = None,
        interview_service: Optional[InterviewService] = None
    ):
        self.llm = llm_provider or create_llm_provider()
        self.interview_service = interview_service or get_interview_service()

        logger.info(f"ConversationService initialized with {self.llm.get_provider_name()}")

    async def process_message(
        self,
        family_id: str,
        user_message: str,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Process a user message and return LLM response with updated state

        Args:
            family_id: Unique family identifier
            user_message: The user's message
            temperature: LLM sampling temperature

        Returns:
            Dict with:
                - response: LLM's text response
                - function_calls: List of function calls made (if any)
                - completeness: Updated interview completeness (0-100)
                - extracted_data: Summary of extracted data
                - context_cards: UI context cards to show
        """
        logger.info(f"Processing message for family {family_id}: {user_message[:50]}...")

        # 1. Get current interview state
        session = self.interview_service.get_or_create_session(family_id)
        data = session.extracted_data

        # 2. Determine which prompt and functions to use
        model_name = getattr(self.llm, 'model_name', 'unknown')
        use_lite = self.interview_service.should_use_lite_mode(family_id, model_name)

        if use_lite:
            system_prompt = build_interview_prompt_lite(
                child_name=data.child_name or "unknown",
                age=str(data.age) if data.age else "unknown",
                gender=data.gender or "unknown",
                concerns=data.primary_concerns,
                completeness=session.completeness,
                context_summary=self.interview_service.get_context_summary(family_id)
            )
            functions = INTERVIEW_FUNCTIONS_LITE
            logger.debug(f"Using LITE mode for {family_id}")
        else:
            system_prompt = build_interview_prompt(
                child_name=data.child_name or "unknown",
                age=str(data.age) if data.age else "unknown",
                gender=data.gender or "unknown",
                concerns=data.primary_concerns,
                completeness=session.completeness,
                context_summary=self.interview_service.get_context_summary(family_id)
            )
            functions = INTERVIEW_FUNCTIONS
            logger.debug(f"Using FULL mode for {family_id}")

        # 3. Build conversation messages
        messages = [Message(role="system", content=system_prompt)]

        # Add recent conversation history (last 10 turns)
        history = self.interview_service.get_conversation_history(
            family_id,
            last_n=20  # Last 10 exchanges (user + assistant)
        )

        for turn in history:
            messages.append(Message(
                role=turn["role"],
                content=turn["content"]
            ))

        # Add current user message
        messages.append(Message(role="user", content=user_message))

        # 4. Call LLM - TWO SEPARATE CALLS to ensure we always get text
        #
        # CRITICAL: Gemini returns empty text when functions are provided.
        # Solution: Split into two calls:
        #   Call 1 (Conversation): Get natural Hebrew response WITHOUT functions
        #   Call 2 (Extraction): Extract structured data from the conversation
        #
        # This ensures parents always see a response, and data extraction happens separately.

        try:
            # CALL 1: Get conversational response (NO functions)
            # This ensures we ALWAYS get Hebrew text back
            llm_response = await self.llm.chat(
                messages=messages,
                functions=None,  # ← NO FUNCTIONS = Always get text
                temperature=temperature,
                max_tokens=2000
            )

            logger.info(
                f"Conversation response: {len(llm_response.content)} chars"
            )

            # Ensure we got a response
            if not llm_response.content.strip():
                logger.error("❌ LLM returned empty response even without functions!")
                llm_response.content = "סליחה, יש לי בעיה טכנית. בואי ננסה שוב."

            # CALL 2: Extract structured data from conversation
            # Create dedicated extraction context
            extraction_system = """You are a data extraction assistant. Your job is to extract structured information from conversations.

Given the latest conversation turn, identify and extract:
- Child information (name, age, gender)
- Concerns mentioned
- Strengths described
- Context shared
- Action requests

Call the appropriate functions to save this data. Extract everything you can from what the parent said."""

            extraction_messages = [
                Message(role="system", content=extraction_system),
                Message(role="user", content=f"Parent: {user_message}"),
                Message(role="assistant", content=f"Response: {llm_response.content}"),
                Message(role="user", content="Extract all relevant data from this conversation turn.")
            ]

            extraction_response = await self.llm.chat(
                messages=extraction_messages,
                functions=functions,  # ← NOW with functions for extraction
                temperature=0.1,  # Very low temp for deterministic extraction
                max_tokens=500
            )

            # Use function calls from extraction response
            llm_response.function_calls = extraction_response.function_calls

            logger.info(
                f"Extraction found: {len(extraction_response.function_calls)} function calls"
            )

        except Exception as e:
            logger.error(f"LLM call failed: {e}", exc_info=True)
            return {
                "response": "מצטערת, נתקלתי בבעיה טכנית. בואי ננסה שוב.",
                "function_calls": [],
                "completeness": session.completeness * 100,
                "extracted_data": {},
                "context_cards": [],
                "error": str(e)
            }

        # 5. Process function calls
        extraction_summary = {}
        action_requested = None
        completeness_check = None

        for func_call in llm_response.function_calls:
            if func_call.name == "extract_interview_data":
                # Update extracted data
                updated_data = self.interview_service.update_extracted_data(
                    family_id,
                    func_call.arguments
                )
                extraction_summary = func_call.arguments
                logger.info(f"Extracted data: {list(extraction_summary.keys())}")

            elif func_call.name == "user_wants_action":
                action_requested = func_call.arguments.get("action")
                logger.info(f"User wants action: {action_requested}")

            elif func_call.name == "check_interview_completeness":
                completeness_check = func_call.arguments
                logger.info(f"Completeness check: {completeness_check}")

        # 6. Save conversation turn
        self.interview_service.add_conversation_turn(
            family_id,
            role="user",
            content=user_message
        )
        self.interview_service.add_conversation_turn(
            family_id,
            role="assistant",
            content=llm_response.content
        )

        # 7. Get updated session state
        session = self.interview_service.get_or_create_session(family_id)
        completeness_pct = session.completeness * 100

        # 8. Generate context cards based on state
        context_cards = self._generate_context_cards(
            family_id,
            session.completeness,
            action_requested,
            completeness_check
        )

        # 9. Check if video guidelines should be generated
        if (session.completeness >= 0.80 and
            not session.video_guidelines_generated and
            completeness_check and
            completeness_check.get("ready_to_complete")):

            # Mark as generated (actual generation would happen here)
            self.interview_service.mark_video_guidelines_generated(family_id)

            # Add video upload card
            context_cards.append({
                "title": "הנחיות צילום מוכנות",
                "subtitle": "מותאמות במיוחד עבור הצרכים שסיפרת לי",
                "icon": "video",
                "status": "new",
                "action": "view_video_guidelines"
            })

        # 10. Return comprehensive response
        return {
            "response": llm_response.content,
            "function_calls": [
                {"name": fc.name, "arguments": fc.arguments}
                for fc in llm_response.function_calls
            ],
            "completeness": completeness_pct,
            "extracted_data": extraction_summary,
            "context_cards": context_cards,
            "stats": self.interview_service.get_session_stats(family_id)
        }

    def _generate_context_cards(
        self,
        family_id: str,
        completeness: float,
        action_requested: Optional[str],
        completeness_check: Optional[Dict]
    ) -> List[Dict[str, Any]]:
        """
        Generate context cards based on interview state

        Cards show current status and available actions
        """
        cards = []
        session = self.interview_service.get_or_create_session(family_id)
        data = session.extracted_data

        # Interview progress card (always shown)
        progress_status = "pending" if completeness < 0.5 else "processing" if completeness < 0.8 else "completed"
        cards.append({
            "title": "שיחת ההיכרות",
            "subtitle": f"התקדמות: {completeness:.0%}",
            "icon": "message-circle",
            "status": progress_status,
            "progress": completeness * 100
        })

        # Child profile card (if we have basic info)
        if data.child_name and data.age:
            cards.append({
                "title": f"פרופיל: {data.child_name}",
                "subtitle": f"גיל {data.age}, {len(data.primary_concerns)} תחומי התפתחות",
                "icon": "user",
                "status": "active"
            })

        # Concerns card (if mentioned)
        if data.primary_concerns:
            concerns_hebrew = self._translate_concerns(data.primary_concerns)
            cards.append({
                "title": "נושאים שעלו",
                "subtitle": ", ".join(concerns_hebrew[:3]),
                "icon": "alert-circle",
                "status": "active"
            })

        # Video guidelines card (if ready)
        if completeness >= 0.80:
            cards.append({
                "title": "העלאת סרטון",
                "subtitle": "מוכן לשלב הבא",
                "icon": "video",
                "status": "action",
                "action": "upload_video"
            })

        # Urgent flags card (if any)
        if data.urgent_flags:
            cards.append({
                "title": "דורש תשומת לב",
                "subtitle": "נושאים שחשוב לטפל בהם",
                "icon": "alert-triangle",
                "status": "urgent"
            })

        return cards

    def _translate_concerns(self, concerns: List[str]) -> List[str]:
        """Translate concern categories to Hebrew"""
        translations = {
            "speech": "דיבור",
            "social": "חברתי",
            "attention": "קשב",
            "motor": "מוטורי",
            "sensory": "חושי",
            "emotional": "רגשי",
            "behavioral": "התנהגות",
            "learning": "למידה",
            "sleep": "שינה",
            "eating": "אכילה",
            "other": "אחר"
        }
        return [translations.get(c, c) for c in concerns]

    async def get_session_summary(self, family_id: str) -> Dict[str, Any]:
        """Get a summary of the current session state"""
        stats = self.interview_service.get_session_stats(family_id)
        session = self.interview_service.get_or_create_session(family_id)

        return {
            **stats,
            "context_summary": self.interview_service.get_context_summary(family_id),
            "recent_messages": self.interview_service.get_conversation_history(
                family_id,
                last_n=6
            )
        }


# Singleton instance
_conversation_service = None

def get_conversation_service() -> ConversationService:
    """Get singleton ConversationService instance"""
    global _conversation_service
    if _conversation_service is None:
        _conversation_service = ConversationService()
    return _conversation_service
