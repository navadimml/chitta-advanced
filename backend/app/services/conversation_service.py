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
from .prerequisite_service import get_prerequisite_service, PrerequisiteService
from .knowledge_service import get_knowledge_service, KnowledgeService
from ..prompts.interview_prompt import build_interview_prompt
from ..prompts.interview_prompt_lite import build_interview_prompt_lite
from ..prompts.interview_functions import INTERVIEW_FUNCTIONS
from ..prompts.interview_functions_lite import INTERVIEW_FUNCTIONS_LITE
from ..prompts.prerequisites import Action
from ..prompts.intent_types import IntentCategory

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
        interview_service: Optional[InterviewService] = None,
        prerequisite_service: Optional[PrerequisiteService] = None,
        knowledge_service: Optional[KnowledgeService] = None
    ):
        self.llm = llm_provider or create_llm_provider()
        self.interview_service = interview_service or get_interview_service()
        self.prerequisite_service = prerequisite_service or get_prerequisite_service()
        self.knowledge_service = knowledge_service or get_knowledge_service()

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

        # 2. CHECK FOR DIRECT FAQ MATCH FIRST (tangents, off-topic, etc.)
        # This handles things like creative writing requests, internal instructions requests
        # without even going to the LLM
        context = {
            "child_name": data.child_name,
            "completeness": session.completeness,
            "video_count": 0,  # TODO: Get from actual video count
            "reports_available": False  # TODO: Get from actual report status
        }

        direct_answer = self.knowledge_service.get_direct_answer(user_message, context)
        if direct_answer:
            logger.info(f"✓ Direct FAQ answer found - returning without LLM call")
            return {
                "response": direct_answer,
                "function_calls": [],
                "completeness": session.completeness,
                "extracted_data": data.to_dict(),
                "context_cards": self._generate_context_cards(session),
                "stats": {
                    "intent": "faq_direct_answer",
                    "faq_matched": True
                }
            }

        # 3. TIER 2: LLM-BASED INTENT CLASSIFICATION
        # Use semantic understanding to detect user intent
        # This replaces the primitive string matching with proper confidence scoring
        intent_detected = None
        prerequisite_check = None
        injected_knowledge = None

        try:
            # Call Tier 2 LLM intent classifier
            detected_intent = await self.knowledge_service.detect_intent_llm(
                user_message=user_message,
                llm_provider=self.llm,
                context={
                    "child_name": data.child_name,
                    "completeness": session.completeness,
                    "video_count": 0,  # TODO: Get from actual video count
                    "reports_available": False  # TODO: Get from actual report status
                }
            )

            logger.info(
                f"✓ Intent detected (Tier 2): category={detected_intent.category.value}, "
                f"confidence={detected_intent.confidence:.2f}"
            )

            # Handle different intent categories
            if detected_intent.category == IntentCategory.ACTION_REQUEST:
                # User wants to perform a specific action
                intent_detected = detected_intent.specific_action
                logger.info(f"✓ Action request: {intent_detected}")

                # PREREQUISITE CHECK - Is this action currently feasible?
                prerequisite_context = {
                    "completeness": session.completeness,
                    "child_name": data.child_name,
                    "video_count": 0,  # TODO: Get from actual video storage
                    "analysis_complete": False,  # TODO: Get from actual analysis status
                    "reports_available": False  # TODO: Get from actual report status
                }

                prerequisite_check = self.prerequisite_service.check_action_feasible(
                    intent_detected,
                    prerequisite_context
                )

                logger.info(
                    f"Prerequisite check: feasible={prerequisite_check.feasible}, "
                    f"missing={prerequisite_check.missing_prerequisites}"
                )

            elif detected_intent.category == IntentCategory.INFORMATION_REQUEST:
                # User wants information about the app/process
                logger.info(f"✓ Information request: {detected_intent.information_type}")

                # Get knowledge to inject into prompt
                knowledge_context = {
                    "child_name": data.child_name,
                    "completeness": session.completeness,
                    "video_count": 0,
                    "reports_available": False
                }

                injected_knowledge = self.knowledge_service.get_knowledge_for_prompt(
                    detected_intent.information_type,
                    knowledge_context
                )
                logger.info(f"Injecting domain knowledge about {detected_intent.information_type}")

            elif detected_intent.category == IntentCategory.TANGENT:
                # Off-topic request - should have been caught by FAQ, but handle gracefully
                logger.info(f"✓ Tangent detected by Tier 2 (FAQ didn't catch it)")
                # The LLM conversation will handle this naturally

            elif detected_intent.category == IntentCategory.PAUSE_EXIT:
                # User wants to pause/exit
                logger.info(f"✓ Pause/Exit intent detected")
                # The LLM conversation will handle this naturally

            # DATA_COLLECTION falls through to normal conversation flow

        except Exception as e:
            logger.warning(f"Tier 2 intent classification failed: {e} - continuing with normal flow")
            intent_detected = None
            prerequisite_check = None

        # 4. Determine which functions to use (for extraction call later)
        model_name = getattr(self.llm, 'model_name', 'unknown')
        use_lite = self.interview_service.should_use_lite_mode(family_id, model_name)

        if use_lite:
            functions = INTERVIEW_FUNCTIONS_LITE
            logger.debug(f"Using LITE functions for {family_id}")
        else:
            functions = INTERVIEW_FUNCTIONS
            logger.debug(f"Using FULL functions for {family_id}")

        # 5. Build CONTEXTUAL conversation prompt
        # This includes prerequisite information so LLM can respond appropriately

        # Base prompt
        base_prompt = f"""You are Chitta (צ'יטה) - a warm, empathetic developmental specialist conducting an interview with a parent in Hebrew.

Your job: Have a natural, flowing conversation to understand the child's development.

Current context:
- Child: {data.child_name or "unknown"} (age: {data.age or "unknown"}, gender: {data.gender or "unknown"})
- Concerns mentioned so far: {", ".join(data.primary_concerns) if data.primary_concerns else "none yet"}
- Interview completeness: {session.completeness:.0%}
- Summary: {self.interview_service.get_context_summary(family_id)}

Conversation guidelines:
1. Be warm and natural - speak like a caring friend
2. Ask ONE clear question at a time
3. Build on what the parent shares
4. Show you're listening through thoughtful follow-ups
5. Focus on gathering rich information about the child

Interview flow (follow naturally, don't announce stages):
- Start: Ask child's name and age if unknown
- Strengths first: "במה הילד/ה אוהב/ת לעסוק?" (brief)
- Main concerns: "מה הביא אותך אלינו? מה מדאיג אותך?" (detailed - examples, context, frequency, impact)
- Additional areas: Development history, family context, daily routines, parent goals

Keep the conversation natural and flowing. Just talk - don't mention any technical processes."""

        # Add prerequisite context if action was detected
        if prerequisite_check:
            if prerequisite_check.feasible:
                # Action IS possible - let LLM know they can facilitate it
                base_prompt += f"""

## ⚠️ IMPORTANT: User Action Request

The user wants to: **{prerequisite_check.action.value}**

✅ This action IS currently possible! The prerequisites are met.

Your response should:
1. Acknowledge their request positively
2. Help them with what they want
3. If interview not fully complete and action is view_report: Ask if there's anything else they want to share first

Example: "בהחלט! יש לי מספיק מידע כדי להתחיל. לפני שאסכם - יש עוד משהו חשוב שלא דיברנו עליו?"
"""
            else:
                # Action is NOT possible yet - explain warmly
                base_prompt += f"""

## ⚠️ IMPORTANT: User Action Request (Not Yet Possible)

The user wants to: **{prerequisite_check.action.value}**

❌ This action is NOT yet possible. Missing: {prerequisite_check.missing_prerequisites}

Your response should:
1. Use this explanation (personalized for them):
   "{prerequisite_check.explanation_to_user}"

2. Then guide back to completing what's needed
3. Be warm and encouraging - never make them feel blocked

The explanation above is already in Hebrew and personalized - USE IT or adapt it naturally.
"""

        # Add injected knowledge if information request detected
        if injected_knowledge:
            base_prompt += f"\n\n{injected_knowledge}"

        system_prompt = base_prompt

        # 6. Build conversation messages
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

        # 7. Call LLM - TWO SEPARATE CALLS to ensure we always get text
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

            # Use ONLY function calls from extraction response
            # CRITICAL: Do NOT append extraction_response.content to llm_response.content
            # The extraction content is just for the model, not for the user
            llm_response.function_calls = extraction_response.function_calls

            logger.info(
                f"Extraction found: {len(extraction_response.function_calls)} function calls"
            )

            # Debug: Log if extraction returned unexpected text
            if extraction_response.content and extraction_response.content.strip():
                logger.debug(f"Extraction response text (not shown to user): {extraction_response.content[:100]}")

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
            # Build subtitle - don't show "0 תחומי התפתחות"
            if data.primary_concerns:
                concerns_count = len(data.primary_concerns)
                concerns_text = "תחום התפתחות אחד" if concerns_count == 1 else f"{concerns_count} תחומי התפתחות"
                subtitle = f"גיל {data.age}, {concerns_text}"
            else:
                # No concerns yet - just show age
                subtitle = f"גיל {data.age}"

            cards.append({
                "title": f"פרופיל: {data.child_name}",
                "subtitle": subtitle,
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

    def _generate_fallback_response(
        self,
        function_calls: List[Any],
        current_data: Any
    ) -> str:
        """
        Generate an appropriate Hebrew response when LLM returns empty text

        This is a fallback for when the model makes function calls but doesn't
        include conversational text (a known issue with some models).

        Args:
            function_calls: The function calls made by the LLM
            current_data: Current extracted data

        Returns:
            Appropriate Hebrew response based on what was extracted
        """
        for func_call in function_calls:
            if func_call.name == "extract_interview_data":
                args = func_call.arguments

                # Check what was extracted and respond accordingly
                if args.get("child_name") and args.get("age"):
                    name = args.get("child_name")
                    age = args.get("age")
                    return f"נעים להכיר את {name}! ספרי לי עוד על {name} - במה הוא/היא אוהב/ת לעסוק?"

                elif args.get("child_name"):
                    name = args.get("child_name")
                    return f"נעים להכיר, {name}! בן כמה הוא/היא?"

                elif args.get("age"):
                    return "תודה! ספרי לי קצת עוד - מה מעניין אותך בעיקר בהתפתחות של הילד/ה?"

                elif args.get("primary_concerns") or args.get("concern_details"):
                    return "הבנתי. זה חשוב שדיברנו על זה. ספרי לי עוד - איך זה משפיע על היום יום?"

                elif args.get("strengths"):
                    return "נהדר! חשוב לי לדעת גם על החוזקות. מה עוד מתקדם יפה?"

                elif args.get("developmental_history"):
                    return "תודה על השיתוף. זה עוזר לי להבין את התמונה המלאה."

                # Generic response for any other extraction
                return "הבנתי, תודה! ספרי לי עוד קצת."

            elif func_call.name == "user_wants_action":
                action = func_call.arguments.get("action")

                # Get child reference for personalized responses
                child_ref = current_data.child_name if (current_data and current_data.child_name) else "הילד/ה"

                # Handle report request
                if action == "view_report":
                    return f"אני רוצה לעזור לך עם דוח מקיף! אבל כדי לייצר ממצאים משמעותיים אני צריכה להכיר את {child_ref} טוב יותר. בואי נמשיך עוד קצת והדוח יהיה הרבה יותר מותאם."

                # Handle video upload request
                elif action == "upload_video":
                    return "נהדר שאת מוכנה להעלות סרטון! קודם בואי נסיים את השיחה כדי שאוכל ליצור לך הנחיות צילום מותאמות אישית."

                # Handle video guidelines request
                elif action == "view_video_guidelines":
                    return "אני אכין לך הנחיות צילום מותאמות ברגע שנסיים את השיחה. בואי נמשיך עוד קצת."

                # Generic action response
                else:
                    return "הבנתי את הבקשה. בואי קודם נסיים את השיחה ואז נטפל בזה."

        # Default fallback if we can't determine what was extracted
        if current_data and current_data.child_name:
            return "הבנתי. ספרי לי עוד."
        else:
            return "שלום! אני כאן כדי להכיר את המשפחה שלך. ספרי לי על הילד/ה שלך."

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
